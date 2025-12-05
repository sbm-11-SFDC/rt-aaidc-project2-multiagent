# src/app.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from . import tools
from .agents import repo_analyzer, tag_recommender, content_improver, reviewer
from .state import MASState
from .logging_utils import get_logger

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger("app")

load_dotenv()


# ------------------------------
# Human-in-the-loop helpers
# ------------------------------
def ask_human_choice(prompt_text: str) -> str:
    """
    Ask the human to choose: yes / no / edit
    (Human-in-the-loop control point for CLI usage)
    """
    while True:
        choice = input(prompt_text + " (yes / no / edit) > ").strip().lower()
        if choice in ("yes", "y"):
            return "yes"
        if choice in ("no", "n"):
            return "no"
        if choice == "edit":
            return "edit"
        print("Please enter 'yes', 'no' or 'edit'.")


def get_multiline_input(prompt_header: str) -> str:
    """
    Collect multi-line human input until a blank line is entered.
    Used when the human wants to edit intermediate outputs.
    """
    print(prompt_header)
    print("(Enter your edited text. Finish by entering a blank line on its own.)")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()


# ------------------------------
# Core pipeline (used by CLI + tests + UI)
# ------------------------------
def _run_review_core(
    repo_url: str,
    human_feedback: Optional[str] = "",
    model_name: str = "gemini-2.5-flash",
    interactive: bool = True,
    timeout_sec: int = 10,  # kept for signature symmetry; not used in tests
) -> dict:
    """
    Core multi-agent review pipeline.

    - Fetches README
    - Runs Repo Analyzer, Tag Recommender, Content Improver, Reviewer
    - Optionally injects human feedback (HITL)
    - Writes outputs to outputs/ and returns a result dict
    """
    logger.info(f"Starting pipeline for repo: {repo_url}")
    state = MASState()

    print(f"\nFetching README for: {repo_url} ...")
    try:
        # IMPORTANT: call through tools.safe_call and tools.fetch_repo_readme
        # so pytest monkeypatch on tools.fetch_repo_readme works.
        # NOTE: we DO NOT pass timeout=... here to avoid kwarg mismatch
        readme = tools.safe_call(
            tools.fetch_repo_readme,
            repo_url,
            tries=3,
            base_delay=1.0,
        )
    except Exception as e:
        logger.error("Error fetching README", exc_info=True)
        return {
            "error": f"Error fetching README: {e}",
            "recommendations_path": None,
            "report": "",
            "report_path": None,
            "keywords": [],
        }

    if not readme or not readme.strip():
        msg = "README content is empty or could not be retrieved."
        logger.error(msg)
        return {
            "error": msg,
            "recommendations_path": None,
            "report": "",
            "report_path": None,
            "keywords": [],
        }

    # Store the raw README in state
    state.set("readme_raw", readme)

    # -----------------------------
    # Stage 1: Repo Analyzer
    # -----------------------------
    print("\n=== Repo Analyzer ===")
    analysis = repo_analyzer(readme)
    state.set("analyzer", analysis)

    print("\nAnalyzer summary:")
    print(analysis.get("summary"))
    if analysis.get("suggestions"):
        print("\nSuggestions:")
        for s in analysis["suggestions"]:
            print(" -", s)

    if interactive:
        choice = ask_human_choice("\nProceed to Tag Recommender?")
        if choice == "no":
            print("Pipeline stopped by user.")
            return {"final_recommendations": "", "keywords": []}
        if choice == "edit":
            edited = get_multiline_input(
                "Edit README excerpt (this will be used by next agents):"
            )
            if edited:
                readme = edited
                state.set("readme_edited_stage1", True)
                state.set("readme_after_analyzer_edit", edited)
                print("Edited README saved for next steps.")
    else:
        print("Non-interactive mode: continuing...")

    # -----------------------------
    # Stage 2: Tag Recommender
    # -----------------------------
    print("\n=== Tag Recommender ===")
    tags_out = tag_recommender(readme)
    state.set("tags", tags_out)

    keywords = tags_out.get("tags", [])
    if keywords:
        print("Suggested tags:", ", ".join(keywords))
    else:
        print("No tags extracted.")

    if interactive:
        choice = ask_human_choice(
            "Proceed to Content Improver (title/intro suggestions)?"
        )
        if choice == "no":
            print("Pipeline stopped by user.")
            return {"final_recommendations": "", "keywords": keywords}
        if choice == "edit":
            edited = get_multiline_input(
                "Edit content (title/intro) to use next:"
            )
            if edited:
                readme = edited
                state.set("readme_edited_stage2", True)
                state.set("readme_after_tags_edit", edited)
                print("Edited content saved for next steps.")

    # -----------------------------
    # Stage 3: Content Improver
    # -----------------------------
    print("\n=== Content Improver ===")
    improvements = content_improver(readme)
    state.set("improvements", improvements)

    print("Suggested Title:", improvements.get("suggested_title"))
    print("Suggested Intro (preview):", improvements.get("suggested_intro"))

    if interactive:
        choice = ask_human_choice("Proceed to final Reviewer?")
        if choice == "no":
            print("Pipeline stopped by user.")
            return {"final_recommendations": "", "keywords": keywords}
        if choice == "edit":
            edited = get_multiline_input(
                "Edit improved intro/title to use in final report:"
            )
            if edited:
                improvements["suggested_intro"] = edited
                state.set("improvements", improvements)
                state.set("intro_edited_stage3", True)
                print("Edited intro saved.")

    # Store human feedback (HITL) in state
    if human_feedback:
        state.set("human_feedback", human_feedback)

    # -----------------------------
    # Stage 4: Reviewer (aggregation)
    # -----------------------------
    print("\n=== Reviewer: Synthesizing final report ===")
    report_out = reviewer(state.to_dict())
    report_text = report_out.get("report", "No report produced.")

    # ✅ Ensure human feedback is appended to the final recommendations
    if human_feedback:
        report_text = f"{report_text}\n\n[Human feedback]\n{human_feedback}"

    # Save outputs with timestamped filenames
    ts = str(int(__import__("time").time()))
    rec_f = OUTPUTS_DIR / f"recommendations_{ts}.txt"
    rpt_f = OUTPUTS_DIR / f"report_{ts}.txt"

    with open(rec_f, "w", encoding="utf-8") as fh:
        fh.write("Recommendations (auto-generated state)\n\n")
        fh.write(json.dumps(state.to_dict(), indent=2))

    with open(rpt_f, "w", encoding="utf-8") as fh:
        fh.write(report_text)

    print("\n--- Final Report ---\n")
    print(report_text)
    print(f"\nSaved recommendations to: {rec_f}")
    print(f"Saved final report to: {rpt_f}")

    logger.info(
        "Pipeline complete. Outputs written to %s and %s",
        rec_f,
        rpt_f,
    )

    return {
        "final_recommendations": report_text,
        "recommendations_path": str(rec_f),
        "report": report_text,
        "report_path": str(rpt_f),
        "keywords": keywords,
    }


# ------------------------------
# Public API used by tests & UI
# ------------------------------
def run_review_workflow(
    repo_url: str,
    human_feedback: Optional[str] = "",
    model_name: str = "gemini-2.5-flash",
    timeout_sec: int = 10,
) -> dict:
    """
    Thin wrapper used by tests and Streamlit UI.
    Always runs in non-interactive mode (no CLI prompts).
    """
    return _run_review_core(
        repo_url=repo_url,
        human_feedback=human_feedback,
        model_name=model_name,
        interactive=False,
        timeout_sec=timeout_sec,
    )


# ------------------------------
# CLI entrypoint
# ------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Publication Reviewer CLI",
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="GitHub repo URL to analyze",
        required=True,
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Run pipeline without human prompts",
    )
    parser.add_argument(
        "--human-feedback",
        type=str,
        default="",
        help="Optional human reviewer notes to append in the final report.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP timeout seconds (reserved for future use).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="LLM model name (for future extensions).",
    )

    args = parser.parse_args()

    _run_review_core(
        repo_url=args.repo,
        human_feedback=args.human_feedback,
        model_name=args.model,
        interactive=not args.no_interactive,
        timeout_sec=args.timeout,
    )


if __name__ == "__main__":
    main()