
import pytest
from unittest.mock import MagicMock, patch
from app.agents.graph import plan_node, grade_generation_v_documents_and_question
from langchain_core.messages import HumanMessage

def test_plan_node_text_mode():
    state = {
        "messages": [HumanMessage(content="Calculate X")],
        "execution_mode": "text"
    }
    
    with patch("app.agents.graph.planner.invoke") as mock_planner:
        mock_planner.return_value = MagicMock(steps=["Step 1"])
        
        result = plan_node(state)
        
        # Verify planner was invoked with TEXT_MODE constraint
        args, _ = mock_planner.invoke.call_args
        objective = args[0]["objective"]
        assert "TEXT_MODE" in objective
        assert "Do NOT use the python_interpreter_tool" in objective

def test_plan_node_python_mode():
    state = {
        "messages": [HumanMessage(content="Plot X")],
        "execution_mode": "python"
    }
    
    with patch("app.agents.graph.planner.invoke") as mock_planner:
        mock_planner.return_value = MagicMock(steps=["Step 1"])
        
        result = plan_node(state)
        
        # Verify planner was invoked with PYTHON_INTERPRETER_MODE constraint
        args, _ = mock_planner.invoke.call_args
        objective = args[0]["objective"]
        assert "PYTHON_INTERPRETER_MODE" in objective
        assert "MUST use the python_interpreter_tool" in objective

def test_grade_generation_python_mode_failure():
    state = {
        "messages": [HumanMessage(content="Plot X")],
        "execution_mode": "python",
        "artifacts": [], # No artifacts!
        "retry_count": 0
    }
    
    result = grade_generation_v_documents_and_question(state)
    assert result["is_supported"] is False # Should fail

def test_grade_generation_python_mode_success():
    state = {
        "messages": [HumanMessage(content="Plot X")],
        "execution_mode": "python",
        "artifacts": [{"path": "plot.png"}], # Artifact exists
        "retry_count": 0
    }
    
    result = grade_generation_v_documents_and_question(state)
    assert result["is_supported"] is True # Should pass

if __name__ == "__main__":
    test_plan_node_text_mode()
    test_plan_node_python_mode()
    test_grade_generation_python_mode_failure()
    test_grade_generation_python_mode_success()
    print("All mode tests passed!")
