from __future__ import annotations
from typing import List, Optional
import re
import textwrap
import time

import requests
import yake
from markdown_it import MarkdownIt

from .logging_utils import get_logger

logger = get_logger(__name__)

# -------------------------------------------------------------------
# GitHub constants (you already had these, we keep + reuse them)
# -------------------------------------------------------------------
GITHUB_API_README = "https://api.github.com/repos/{owner}/{repo}/readme"
RAW_README = "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"


# -------------------------------------------------------------------
# Validation & Safety Helpers
# -------------------------------------------------------------------
def validate_repo_url(url: str) -> bool:
    """
    Basic validation for GitHub repo URLs.
    Accepts: https://github.com/owner/repo
    """
    if not url:
        return False
    url = url.strip()
    pattern = r"^https://github\.com/[^/]+/[^/]+/?$"
    return bool(re.match(pattern, url))


def sanitize_text(text: str, max_len: int = 4000) -> str:
    """
    Light guardrail: trim very long outputs and normalize whitespace.
    """
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text


# -------------------------------------------------------------------
# Your original helpers (now with logging)
# -------------------------------------------------------------------
def fetch_readme_via_api(repo_url: str, timeout: int = 10) -> Optional[str]:
    """
    Try the GitHub API (returns raw content when requested).
    repo_url examples:
        https://github.com/owner/repo
        git@github.com:owner/repo.git
    """
    try:
        parts = repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1].replace(".git", "")
    except Exception as e:
        logger.error(f"Failed to parse repo URL '{repo_url}': {e}")
        return None

    url = GITHUB_API_README.format(owner=owner, repo=repo)
    headers = {"Accept": "application/vnd.github.v3.raw"}

    try:
        logger.info(f"Fetching README via GitHub API: {url}")
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200 and resp.text.strip():
            return resp.text
    except Exception as e:
        logger.warning(f"GitHub API fetch failed, will try raw URLs: {e}")

    # fallback: direct raw README on main and master
    for branch in ("main", "master"):
        raw_url = RAW_README.format(owner=owner, repo=repo, branch=branch)
        try:
            logger.info(f"Trying raw README at: {raw_url}")
            r2 = requests.get(raw_url, timeout=timeout)
            if r2.status_code == 200 and r2.text.strip():
                return r2.text
        except Exception as e:
            logger.warning(f"Raw README fetch failed for branch {branch}: {e}")
            continue

    logger.error(f"Unable to fetch README for repo: {repo_url}")
    return None


def safe_call(func, *args, tries: int = 3, base_delay: float = 1.0, **kwargs):
    """
    Generic retry helper with exponential backoff.
    """
    last_err = None
    delay = base_delay
    for _ in range(tries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_err = e
            logger.warning(f"safe_call retry after error: {e}")
            time.sleep(delay)
            delay *= 2
    logger.error(f"safe_call exhausted retries, last error: {last_err}")
    raise last_err


# -------------------------------------------------------------------
# High-level README fetch wrapper (used by app.py & UI)
# -------------------------------------------------------------------
def fetch_repo_readme(repo_url: str, timeout: int = 10) -> str:
    """
    Validates the URL, then uses your API+raw fallback approach with retries.
    Raises a clear error if README cannot be retrieved.
    """
    if not validate_repo_url(repo_url):
        raise ValueError("Invalid GitHub repo URL. Expected https://github.com/owner/repo")

    logger.info(f"Fetching README for repo: {repo_url}")
    content = safe_call(fetch_readme_via_api, repo_url, timeout=timeout)

    if not content or not content.strip():
        raise RuntimeError("README content is empty or could not be retrieved.")

    return content.strip()


# -------------------------------------------------------------------
# Keyword Extraction
# -------------------------------------------------------------------
def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """
    Simple YAKE-based keyword extraction from README / repo text.
    """
    text = text or ""
    if not text.strip():
        return []

    kw_extractor = yake.KeywordExtractor(top=top_k, stopwords=None)
    keywords = kw_extractor.extract_keywords(text)
    # YAKE returns list of (keyword, score); we only need keyword string
    return [k for k, _ in keywords]


# -------------------------------------------------------------------
# Markdown → Plain Text
# -------------------------------------------------------------------
def markdown_to_text(md: str) -> str:
    """
    Convert README markdown to plain text for LLM consumption.
    """
    if not md:
        return ""
    md = md.strip()
    parser = MarkdownIt()
    tokens = parser.parse(md)
    lines: List[str] = []
    for t in tokens:
        if t.type == "inline" and t.content:
            lines.append(t.content)
    out = "\n".join(lines)
    return textwrap.dedent(out).strip()