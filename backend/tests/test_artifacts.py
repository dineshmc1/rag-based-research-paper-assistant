
import pytest
from unittest.mock import MagicMock, patch
import json
from app.agents.graph import grade_documents
from app.agents.state import AgentState
from langchain_core.documents import Document

def test_grade_documents_with_artifact():
    # Mock state
    state = {
        "messages": [],
        "documents": [],
        "artifacts": []
    }
    
    # Mock tool output with artifact
    tool_output = {
        "text_summary": "Plot generated",
        "artifact": {
            "type": "image",
            "path": "/static/test.png",
            "name": "test.png"
        }
    }
    
    # Run grade_documents with this input as "docs" (simulating tool output)
    # Note: In the real graph, grade_documents receives state, but extracting "docs" happens inside.
    # Wait, grade_documents grabs last_message which is a ToolMessage.
    # But in the code: `docs = last_message.content`
    
    # Let's verify the logic inside grade_documents directly by mocking the grading result "yes"
    # and passing the JSON string as docs.
    
    json_docs = json.dumps(tool_output)
    
    # We need to mock retrieval_grader to return "yes"
    with patch("app.agents.graph.retrieval_grader.invoke") as mock_grader:
        mock_grader.return_value = MagicMock(binary_score="yes")
        
        # We need to simulate the state passed to grade_documents
        # construct a mock message
        mock_msg = MagicMock()
        mock_msg.tool_call_id = "123"
        mock_msg.content = json_docs
        
        state["messages"] = [MagicMock(content="question"), mock_msg]
        
        result = grade_documents(state)
        
        # Verify result
        assert result["is_relevant"] is True
        assert len(result["documents"]) == 1
        assert "artifact" in result["documents"][0].metadata
        assert result["documents"][0].metadata["artifact"]["path"] == "/static/test.png"
        assert result["artifacts"][0]["path"] == "/static/test.png"

if __name__ == "__main__":
    test_grade_documents_with_artifact()
    print("Test passed!")
