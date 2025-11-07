import os
import time
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from .state import MASState
from .agents import (
    agent_repo_analyzer,
    agent_metadata,
    agent_content_improver,
    agent_reviewer,
)


def build_graph():
    """Build the LangGraph state machine with 4 agents."""
    graph = StateGraph(MASState)

    graph.add_node("analyze_repo", agent_repo_analyzer)
    graph.add_node("metadata", agent_metadata)
    graph.add_node("improve_content", agent_content_improver)
    graph.add_node("review", agent_reviewer)

    graph.set_entry_point("analyze_repo")
    graph.add_edge("analyze_repo", "metadata")
    graph.add_edge("metadata", "improve_content")
    graph.add_edge("improve_content", "review")
    graph.add_edge("review", END)

    return graph.compile()


def run_pipeline(repo_url: str) -> MASState:
    """Run the multi-agent pipeline and return the final state."""
    app = build_graph()
    initial: MASState = {"repo_url": repo_url}
    return app.invoke(initial)


def _guess_repo_name(repo_url: str) -> str:
    """
    Try to extract a stable repository name from common GitHub URL patterns.
    Examples:
      https://github.com/user/repo                -> repo
      https://github.com/user/repo/               -> repo
      https://github.com/user/repo/tree/main      -> repo
      https://github.com/user/repo/blob/main/README.md -> repo
    """
    url = (repo_url or "").strip().rstrip("/")
    parts = [p for p in url.split("/") if p]
    if not parts:
        return "repo"

    # Typical positions:
    # ... github.com / user / repo / (optional: tree|blob / branch / ...)
    # We look for 'tree' or 'blob' markers to step back.
    if "tree" in parts:
        idx = parts.index("tree")
        if idx >= 1:
            return parts[idx - 1]  # repo
    if "blob" in parts:
        idx = parts.index("blob")
        if idx >= 1:
            return parts[idx - 1]  # repo

    # Otherwise, take the last path component as repo
    return parts[-1]


if __name__ == "__main__":
    import argparse

    load_dotenv()

    parser = argparse.ArgumentParser(description="Multi-Agent Publication Assistant")
    parser.add_argument("--repo", required=True, help="GitHub repo URL")
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Also write a brief analysis report.txt (sections, keywords, raw suggestions)",
    )
    args = parser.parse_args()

    # Run pipeline
    result = run_pipeline(args.repo)

    # Prepare outputs directory & filenames
    os.makedirs("outputs", exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    repo_name = _guess_repo_name(args.repo)

    recommend_path = f"outputs/{repo_name}_recommendations_{timestamp}.txt"
    report_path = f"outputs/{repo_name}_report_{timestamp}.txt"

    # Final recommendations text
    final_text = result.get("final_output", "") or ""

    # Write recommendations (always)
    with open(recommend_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    # Print to console as well
    print("\n--- FINAL RECOMMENDATIONS ---\n")
    print(final_text)
    print(f"\nSaved recommendations to: {recommend_path}")

    # Optionally write detailed report (sections, keywords, raw blocks)
    if args.save_report:
        sections = result.get("sections") or []
        keywords = result.get("keywords") or []
        meta_raw = (result.get("metadata_suggestions") or {}).get("raw", [])
        content_raw = (result.get("content_suggestions") or {}).get("raw", "")

        # Normalize to list for meta_raw
        if not isinstance(meta_raw, list):
            meta_raw = [meta_raw]

        report_lines = []
        report_lines.append("=== Multi-Agent Publication Assistant — Analysis Report ===")
        report_lines.append(f"Repo URL: {result.get('repo_url', 'N/A')}")
        report_lines.append("")
        report_lines.append(f"Sections found ({len(sections)}):")
        for s in sections:
            report_lines.append(f"  - {s}")
        report_lines.append("")
        report_lines.append("Top keywords:")
        for kw in keywords[:20]:
            report_lines.append(f"  - {kw}")
        report_lines.append("")
        report_lines.append("Raw metadata suggestions (LLM):")
        for block in meta_raw:
            report_lines.append(f"  {block}")
        report_lines.append("")
        report_lines.append("Raw content suggestions (LLM, truncated to 1200 chars):")
        report_lines.append((content_raw or "")[:1200])

        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write("\n".join(report_lines))

        print(f"Saved report to: {report_path}")