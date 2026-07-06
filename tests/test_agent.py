import pytest

from services.agent.master import classify_intent
from services.agent.graph import run_graph


def test_classify_design_intent():
    assert classify_intent("I need a red saree for wedding") == "design_request"


@pytest.mark.asyncio
async def test_agent_offline_fallback(app):
    result = await run_graph("hello", user_id="test-user", session_id="test-session", language="te")
    assert "reply" in result
    assert result["intent"] == "greeting"
