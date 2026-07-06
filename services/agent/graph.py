"""Strict Agentic Execution Graph for Aura."""

from typing import Any, TypedDict
import asyncio
import base64

from langgraph.graph import END, StateGraph

from services.agent.master import classify_intent, extract_params_llm, extract_params_heuristic
from services.agent.agents import MemoryAgent, PlannerAgent, BodyAnalysisAgent, StylingAgent, TryOnAgent, WardrobeAgent
from services.agent.schemas import DesignParams
from services.vision.generate_outfit import generate_outfits
from services.retrieval.product_match import match_products
from services.agent.tailor_guide import generate_tailoring_guide
from services.api.core.models import WardrobeItem
from services.api.core.database import SessionLocal

class AgenticState(TypedDict, total=False):
    user_id: str
    session_id: str
    message: str
    language: str
    image_b64: str | None
    
    # Computed state
    history: list[dict[str, Any]]
    context: dict[str, Any]
    intent: str
    plan_goal: str
    
    # Fashion & Profile State
    profile_data: dict[str, Any]
    design_params: dict[str, Any]
    
    # Outputs
    reply: str
    outfits: list[dict[str, Any]]
    products: list[dict[str, Any]]
    tailoring_pdf_base64: str | None
    composite_image_b64: str | None
    error: str | None
    status: str

# Nodes

async def node_memory_load(state: AgenticState) -> AgenticState:
    mem = await MemoryAgent.retrieve_state(state["session_id"], state["user_id"])
    return {
        **state,
        "history": mem.get("history", []),
        "context": mem.get("context", {}),
        "status": mem.get("status", "active")
    }

async def node_intent(state: AgenticState) -> AgenticState:
    intent = classify_intent(state["message"])
    return {**state, "intent": intent}

async def node_planner(state: AgenticState) -> AgenticState:
    goal = PlannerAgent.determine_plan(state["intent"], state.get("context", {}), state["message"])
    return {**state, "plan_goal": goal}

async def node_body_analysis(state: AgenticState) -> AgenticState:
    profile_data = await BodyAnalysisAgent.process_profile(
        state["message"], state["user_id"], state.get("context", {})
    )
    # Update context with profile resolution status
    ctx = state.get("context", {})
    ctx["profile_resolved"] = profile_data.get("profile_resolved", False)
    ctx["target_profile_name"] = profile_data.get("target_profile_name")
    
    return {**state, "profile_data": profile_data, "context": ctx}

async def node_extraction(state: AgenticState) -> AgenticState:
    if state["intent"] == "design_request":
        params = await extract_params_llm(state["message"], state["language"])
    else:
        params = extract_params_heuristic(state["message"])
        
    ctx = state.get("context", {})
    # Very simplistic check for completeness
    ctx["design_params_complete"] = bool(params.occasion or params.budget_inr)
    
    return {**state, "design_params": params.model_dump(), "context": ctx}

async def node_stylist(state: AgenticState) -> AgenticState:
    params_data = state.get("design_params") or {}
    params = DesignParams(**{k: v for k, v in params_data.items() if k in DesignParams.model_fields})
    
    reply = await StylingAgent.reason(
        state["message"], params, state.get("profile_data", {}), state.get("history", [])
    )
    return {**state, "reply": reply}

async def node_outfit_gen(state: AgenticState) -> AgenticState:
    if state.get("error"): return state
    if state.get("plan_goal") not in ("PROPOSE_OUTFIT", "FINALIZE"):
        return state
        
    try:
        outfit_result = await generate_outfits(design_brief=state["message"], num_variants=1)
        variants = [v.__dict__ for v in outfit_result.variants]
        return {**state, "outfits": variants}
    except Exception as e:
        return {**state, "error": f"Outfit Generation Failed: {e}"}

async def node_tryon(state: AgenticState) -> AgenticState:
    if state.get("error"): return state
    if state.get("plan_goal") not in ("PROPOSE_OUTFIT", "FINALIZE"):
        return state
        
    outfits = state.get("outfits")
    if not outfits:
        return state
        
    profile = state.get("profile_data", {})
    avatar_url = profile.get("avatar_image_url")
    measurements = profile.get("measurements") or {}
    avatar_b64 = measurements.get("_front_photo_b64")
    
    if not avatar_url and not state.get("image_b64") and not avatar_b64:
        return {**state, "error": "Avatar missing. Please upload a full-body photo for try-on."}
        
    person_bytes = None
    if state.get("image_b64"):
        person_bytes = base64.b64decode(state["image_b64"])
    elif avatar_b64:
        person_bytes = base64.b64decode(avatar_b64)
    else:
        # In a real app we'd fetch the avatar_url bytes here.
        # For this prototype we will assume image_b64 is provided or fail.
        return {**state, "error": "Avatar missing. Please upload a full-body photo for try-on."}
        
    garment_b64 = outfits[0].get("image_url") or outfits[0].get("image_base64")
    if not garment_b64:
        return {**state, "error": "Try-On Failed: Garment image missing."}
        
    if garment_b64 and garment_b64.startswith("data:image"):
        garment_b64 = garment_b64.split(",")[1]
        
    garment_bytes = base64.b64decode(garment_b64) if garment_b64 else None
    
    if not garment_bytes:
        return {**state, "error": "Try-On Failed: Invalid garment image data."}
        
    try:
        composite = await TryOnAgent.apply_garment(person_bytes, garment_bytes)
        return {**state, "composite_image_b64": base64.b64encode(composite).decode("ascii")}
    except Exception as e:
        return {**state, "error": f"Try-On Failed: {e}"}

async def node_finalize(state: AgenticState) -> AgenticState:
    if state.get("error"): return state
    if state.get("plan_goal") != "FINALIZE":
        return state
        
    # Retrieve products
    params_data = state.get("design_params") or {}
    products = await match_products(
        outfit_description=state["message"],
        max_price_inr=params_data.get("budget_inr"),
        limit=5,
        threshold=0.72
    )
    
    tailoring_pdf_b64 = None
    if len(products) < 2:
        measurements = state.get("profile_data", {}).get("measurements", {"chest_cm": 88, "waist_cm": 72, "hip_cm": 96})
        pdf = await generate_tailoring_guide(
            garment_type="outfit",
            fabric="silk",
            measurements=measurements,
            occasion=params_data.get("occasion"),
        )
        tailoring_pdf_b64 = base64.b64encode(pdf).decode("ascii")
        
    # Save to Wardrobe
    outfits = state.get("outfits")
    if outfits:
        try:
            await WardrobeAgent.save_to_wardrobe(
                state["user_id"],
                outfits[0],
                state.get("composite_image_b64")
            )
        except Exception as e:
            return {**state, "error": f"Wardrobe Save Failed: {e}"}
        
    # Update status
    return {**state, "products": products, "tailoring_pdf_base64": tailoring_pdf_b64, "status": "finalized"}

async def node_memory_save(state: AgenticState) -> AgenticState:
    status = state.get("status", "active")
    if state.get("error"):
        status = "error"
    await MemoryAgent.update_state(state["session_id"], state.get("context", {}), status)
    return state


# Routing
def route_after_planner(state: AgenticState) -> str:
    goal = state.get("plan_goal")
    if goal in ("GATHER_REQUIREMENTS", "PROPOSE_OUTFIT", "FINALIZE", "RESOLVE_PROFILE"):
        return "body_analysis"
    return "stylist"

# Build Graph
def build_fashion_graph():
    graph = StateGraph(AgenticState)
    
    graph.add_node("memory_load", node_memory_load)
    graph.add_node("detect_intent", node_intent)
    graph.add_node("planner", node_planner)
    graph.add_node("body_analysis", node_body_analysis)
    graph.add_node("extraction", node_extraction)
    graph.add_node("stylist", node_stylist)
    graph.add_node("outfit_gen", node_outfit_gen)
    graph.add_node("tryon", node_tryon)
    graph.add_node("finalize", node_finalize)
    graph.add_node("memory_save", node_memory_save)
    
    graph.set_entry_point("memory_load")
    graph.add_edge("memory_load", "detect_intent")
    graph.add_edge("detect_intent", "planner")
    
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {"body_analysis": "body_analysis", "stylist": "stylist"}
    )
    
    graph.add_edge("body_analysis", "extraction")
    graph.add_edge("extraction", "stylist")
    graph.add_edge("stylist", "outfit_gen")
    graph.add_edge("outfit_gen", "tryon")
    graph.add_edge("tryon", "finalize")
    graph.add_edge("finalize", "memory_save")
    graph.add_edge("memory_save", END)
    
    return graph.compile()


_fashion_graph = None

def get_fashion_graph():
    global _fashion_graph
    if _fashion_graph is None:
        _fashion_graph = build_fashion_graph()
    return _fashion_graph

async def run_graph(
    message: str,
    user_id: str,
    session_id: str,
    language: str = "te",
    image_b64: str | None = None,
) -> dict[str, Any]:
    graph = get_fashion_graph()
    
    result = await graph.ainvoke({
        "user_id": user_id,
        "session_id": session_id,
        "message": message,
        "language": language,
        "image_b64": image_b64
    })
    
    return {
        "reply": result.get("reply", ""),
        "intent": result.get("intent", "general"),
        "params": result.get("design_params", {}),
        "outfits": result.get("outfits"),
        "products": result.get("products"),
        "tailoring_pdf_base64": result.get("tailoring_pdf_base64"),
        "composite_image_b64": result.get("composite_image_b64"),
        "error": result.get("error"),
        "status": result.get("status")
    }
