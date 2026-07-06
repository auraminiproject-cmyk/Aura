"""Specialized agents for the Aura Agentic Workflow."""

from typing import Any
import base64
import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.core.database import SessionLocal
from services.api.core.models import BodyProfile, User, Session, Conversation
from services.agent.master import classify_intent, extract_params_llm, extract_params_heuristic
from services.agent.llm import complete
from services.agent.schemas import DesignParams
from services.vision.virtual_tryon import try_on_with_spaces

logger = logging.getLogger(__name__)

async def _get_profile(user_id: str, profile_name: str | None = None) -> BodyProfile | None:
    async with SessionLocal() as db:
        stmt = select(BodyProfile).where(BodyProfile.user_id == user_id)
        if profile_name:
            stmt = stmt.where(BodyProfile.profile_name == profile_name)
        else:
            stmt = stmt.where(BodyProfile.profile_type == "primary")
        result = await db.execute(stmt.order_by(BodyProfile.created_at.desc()).limit(1))
        return result.scalars().first()

class MemoryAgent:
    """Handles retrieval and update of session state and conversation history."""
    @staticmethod
    async def retrieve_state(session_id: str, user_id: str) -> dict[str, Any]:
        async with SessionLocal() as db:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalars().first()
            if not session:
                return {}
            
            # Fetch last few messages for context
            conv_result = await db.execute(
                select(Conversation).where(Conversation.session_id == session_id).order_by(Conversation.created_at.asc())
            )
            history = [{"role": c.role, "content": c.content} for c in conv_result.scalars().all()[-10:]]
            
            return {
                "status": session.status,
                "context": session.context_json or {},
                "history": history
            }
            
    @staticmethod
    async def update_state(session_id: str, context: dict[str, Any], status: str = "active"):
        async with SessionLocal() as db:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalars().first()
            if session:
                session.context_json = context
                session.status = status
                await db.commit()

class PlannerAgent:
    """Orchestrates the strategic goal based on memory, intent, and user profile."""
    @staticmethod
    def determine_plan(intent: str, context: dict[str, Any], message: str) -> str:
        # Check if we need to resolve measurements (profile missing or user asked for another person)
        if intent == "design_request":
            if not context.get("profile_resolved", False):
                return "RESOLVE_PROFILE"
            if not context.get("design_params_complete", False):
                return "GATHER_REQUIREMENTS"
            return "PROPOSE_OUTFIT"
        if intent in ("product_search", "tailoring", "wardrobe"):
            return "FINALIZE"
        
        # If user explicitly asks to finalize or we reached a natural end
        if "finalize" in message.lower() or "done" in message.lower() or "looks good" in message.lower():
            return "FINALIZE"
            
        return "GENERAL_CHAT"

class BodyAnalysisAgent:
    """Handles Gender, Pose, Body Shape, and Measurement Validation."""
    @staticmethod
    async def process_profile(message: str, user_id: str, context: dict[str, Any]) -> dict[str, Any]:
        profile_name = context.get("target_profile_name")
        
        # If LLM sees user wants to design for someone else (e.g. "for my sister")
        system_prompt = "Does the user want to design for themselves or someone else? Respond with ONLY 'self' or the name/relation (e.g. 'sister', 'john'). Message: " + message
        try:
            target = await complete(system_prompt, temperature=0.0)
            target = target.strip().lower()
            if target != "self" and target != "":
                profile_name = target
        except Exception:
            pass

        profile = await _get_profile(user_id, profile_name)
        
        if not profile:
            # Need to ask user for gender and measurements
            return {
                "profile_resolved": False,
                "target_profile_name": profile_name,
                "missing_info": "gender_and_measurements"
            }
            
        return {
            "profile_resolved": True,
            "target_profile_name": profile_name,
            "gender": profile.gender,
            "measurements": profile.measurements,
            "avatar_image_url": profile.avatar_image_url
        }

class StylingAgent:
    """Retrieves fashion knowledge and reasons about styling."""
    @staticmethod
    async def reason(message: str, params: DesignParams, profile_data: dict[str, Any], history: list[dict[str, Any]]) -> str:
        gender = profile_data.get("gender", "neutral")
        system = f"You are an expert Indian fashion stylist for a {gender} client. Offer brief, culturally accurate styling advice based on their measurements. Keep your response STRICTLY under 400 characters for text-to-speech compatibility."
        user_prompt = f"Message: {message}\nParams: {params.model_dump_json()}\nHistory: {json.dumps(history)}"
        return await complete(user_prompt, system=system, temperature=0.7)

class TryOnAgent:
    """Handles virtual try-on with strict constraints (no fallback to fake images)."""
    @staticmethod
    async def apply_garment(person_image_bytes: bytes | None, garment_image_bytes: bytes) -> bytes:
        if not person_image_bytes:
            raise ValueError("Avatar missing. User must upload a photo.")
            
        logger.info("[TryOnAgent] Sending images to real Virtual Try-On space")
        
        # We retry a few times to be robust against HF space failures
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await try_on_with_spaces(person_image_bytes, garment_image_bytes)
                if result and len(result) > 1000:
                    return result
            except Exception as e:
                logger.warning(f"Try-on attempt {attempt+1} failed: {e}")
                
        raise RuntimeError("Virtual Try-On service unavailable after retries.")

class WardrobeAgent:
    """Handles saving finalized outfits and composite images to the user's wardrobe."""
    @staticmethod
    async def save_to_wardrobe(user_id: str, outfit_data: dict, composite_b64: str | None) -> str:
        # In a real app we'd upload the composite_b64 to a storage bucket and save the URL.
        # Here we just save the metadata and base64 directly or a placeholder URL.
        image_url = outfit_data.get("image_url", "")
        if composite_b64:
            image_url = f"data:image/jpeg;base64,{composite_b64[:30]}..." # Mock URL for DB size limits
            
        async with SessionLocal() as db:
            from services.api.core.models import WardrobeItem
            import uuid
            item = WardrobeItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=outfit_data.get("name", "Generated Outfit"),
                image_url=image_url,
                category="outfit",
                metadata_json=outfit_data
            )
            db.add(item)
            await db.commit()
            return item.id
