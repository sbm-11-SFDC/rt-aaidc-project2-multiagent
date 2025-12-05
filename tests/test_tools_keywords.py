from src.tools import extract_keywords

def test_extract_keywords_basic():
    text = "This project builds a multi-agent system using LangGraph and Gemini."
    kws = extract_keywords(text, top_k=5)
    assert isinstance(kws, list)
    assert len(kws) > 0