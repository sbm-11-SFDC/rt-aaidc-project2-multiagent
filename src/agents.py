import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from .state import MASState
from .tools import fetch_repo_readme, extract_keywords, lint_readme_sections

load_dotenv()
_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def _ask_llm(prompt: str) -> str:
    resp = _llm.invoke([HumanMessage(content=prompt)])
    return getattr(resp, "content", str(resp))

def agent_repo_analyzer(state: MASState) -> MASState:
    readme = fetch_repo_readme(state["repo_url"])
    sections = lint_readme_sections(readme)
    kw = extract_keywords(readme)
    state.update({"readme_text": readme, "sections": sections, "keywords": kw})
    return state

def agent_metadata(state: MASState) -> MASState:
    text = state.get("readme_text", "")
    kw = state.get("keywords", [])
    prompt = f"""
Suggest 6–10 tags and 2–4 categories for this GitHub AI project.

README:
{text[:1200]}
KEYWORDS: {kw[:20]}
"""
    out = _ask_llm(prompt)
    state["metadata_suggestions"] = {"raw": out}
    return state

def agent_content_improver(state: MASState) -> MASState:
    text = state.get("readme_text", "")
    sections = state.get("sections", [])
    prompt = f"""
Improve the project title, summary, and list missing recommended README sections.
Return a concise list.

CURRENT SECTIONS: {sections}
README:
{text[:1200]}
"""
    out = _ask_llm(prompt)
    state["content_suggestions"] = {"raw": out}
    return state

def agent_reviewer(state: MASState) -> MASState:
    prompt = f"""
Combine metadata_suggestions and content_suggestions into a single final plan:
1) Improved title
2) Short summary (3–5 sentences)
3) Suggested tags (6–10)
4) Suggested categories (2–4)
5) Checklist of missing sections

METADATA: {state.get("metadata_suggestions")}
CONTENT: {state.get("content_suggestions")}
"""
    final = _ask_llm(prompt)
    state["final_output"] = final
    return state