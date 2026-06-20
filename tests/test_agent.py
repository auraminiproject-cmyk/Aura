import pytest

from services.agent.master import classify_intent, run_fashion_agent


def test_classify_design_intent():
    assert classify_intent("I need a red saree for wedding") == "design_request"


@pytest.mark.asyncio
async def test_agent_offline_fallback():
    result = await run_fashion_agent("hello", language="te")
    assert "reply" in result
    assert result["intent"] == "greeting"
