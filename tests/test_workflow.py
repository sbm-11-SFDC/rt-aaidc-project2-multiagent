from src.app import run_review_workflow
import src.tools as tools


def dummy_readme() -> str:
    return """
# Dummy Project

This is a sample README for testing the multi-agent publication reviewer.
It uses Python, LangGraph, and Gemini to analyze repositories.
"""


def test_run_review_workflow_monkeypatched(monkeypatch):
    # monkeypatch the network-dependent function
    monkeypatch.setattr(tools, "fetch_repo_readme", lambda repo_url: dummy_readme())

    result = run_review_workflow(
        repo_url="https://github.com/owner/repo",
        human_feedback="Human note: focus on clarity.",
        model_name="gemini-2.5-flash",
    )

    assert "final_recommendations" in result
    assert isinstance(result["final_recommendations"], str)
    assert "Human note" in result["final_recommendations"]