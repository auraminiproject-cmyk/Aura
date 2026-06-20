"""LangGraph fashion agent — classify → extract → [vlm_analyze] → synthesize.

The VLM node is conditionally activated when the input contains an image
(image_b64 key in state).  History is threaded through for stateful conversation.
"""

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from services.agent.master import classify_intent, extract_params_heuristic, extract_params_llm
from services.agent.response_gen import synthesize_with_profile
from services.agent.schemas import AgentState, DesignParams


class GraphState(TypedDict, total=False):
    message: str
    language: str
    history: list[dict[str, Any]]
    image_b64: str | None
    intent: str
    params: dict[str, Any]
    vlm_analysis: dict[str, Any] | None
    reply: str


async def node_classify(state: GraphState) -> GraphState:
    return {**state, "intent": classify_intent(state["message"])}


async def node_extract(state: GraphState) -> GraphState:
    intent = state.get("intent", "general")
    language = state.get("language", "te")
    if intent == "design_request":
        params = await extract_params_llm(state["message"], language)
    else:
        params = extract_params_heuristic(state["message"])
    return {**state, "params": params.model_dump()}


async def node_vlm_analyze(state: GraphState) -> GraphState:
    """Run VLM analysis when an image is present in the state."""
    image_b64 = state.get("image_b64")
    if not image_b64:
        return {**state, "vlm_analysis": None}

    import base64
    from services.agent.vlm import analyze_clothing_image

    image_bytes = base64.b64decode(image_b64)
    result = await analyze_clothing_image(
        image_bytes, prompt=state.get("message", ""), language=state.get("language", "en"),
    )
    return {
        **state,
        "vlm_analysis": {
            "description": result.description,
            "tags": result.tags,
            "style_category": result.style_category,
            "color_palette": result.color_palette,
            "suggestions": result.suggestions,
            "confidence": result.confidence,
        },
    }


async def node_synthesize(state: GraphState) -> GraphState:
    params_data = state.get("params") or {}
    agent_state = AgentState(
        message=state["message"],
        language=state.get("language", "te"),
        intent=state.get("intent", "general"),  # type: ignore[arg-type]
        params=DesignParams(**{k: v for k, v in params_data.items() if k in DesignParams.model_fields}),
    )

    # Enrich synthesis prompt with VLM analysis if available
    vlm = state.get("vlm_analysis")
    if vlm and vlm.get("description"):
        agent_state.message += f"\n\n[VLM Analysis: {vlm['description']}. Tags: {', '.join(vlm.get('tags', []))}. Style: {vlm.get('style_category', '')}]"

    reply = await synthesize_with_profile(agent_state, history=state.get("history"))
    return {**state, "reply": reply}


def _route_after_classify(state: GraphState) -> str:
    """Route to VLM node if image is present, otherwise straight to extract."""
    if state.get("image_b64"):
        return "vlm_analyze"
    return "extract"


def build_fashion_graph():
    graph = StateGraph(GraphState)
    graph.add_node("classify", node_classify)
    graph.add_node("extract", node_extract)
    graph.add_node("vlm_analyze", node_vlm_analyze)
    graph.add_node("synthesize", node_synthesize)
    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        _route_after_classify,
        {"extract": "extract", "vlm_analyze": "vlm_analyze"},
    )
    graph.add_edge("vlm_analyze", "extract")
    graph.add_edge("extract", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


_fashion_graph = None


def get_fashion_graph():
    global _fashion_graph
    if _fashion_graph is None:
        _fashion_graph = build_fashion_graph()
    return _fashion_graph


async def run_graph(
    message: str,
    *,
    history: list[dict[str, Any]] | None = None,
    language: str = "te",
    image_b64: str | None = None,
) -> dict[str, Any]:
    graph = get_fashion_graph()
    result = await graph.ainvoke(
        {
            "message": message,
            "language": language,
            "history": history or [],
            "image_b64": image_b64,
        },
    )
    return {
        "reply": result.get("reply", ""),
        "intent": result.get("intent", "general"),
        "params": result.get("params", {}),
        "vlm_analysis": result.get("vlm_analysis"),
    }
