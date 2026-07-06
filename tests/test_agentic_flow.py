import asyncio
import pytest
from services.agent.graph import get_fashion_graph
from services.api.core.database import init_db

@pytest.mark.asyncio
async def test_graph_compilation():
    graph = get_fashion_graph()
    assert graph is not None

@pytest.mark.asyncio
async def test_graph_run_missing_avatar():
    await init_db()
    graph = get_fashion_graph()
    result = await graph.ainvoke({
        "user_id": "test_user",
        "session_id": "test_session",
        "message": "Design a red silk lehenga for me. finalize.",
        "language": "en",
        "image_b64": None
    })
    
    assert result["intent"] == "design_request" or result["intent"] == "general"
    
if __name__ == "__main__":
    asyncio.run(test_graph_compilation())
    print("Graph compiled successfully.")
