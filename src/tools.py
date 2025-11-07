import re
import requests
from typing import List

# Try YAKE; fall back to a simple extractor if unavailable
try:
    import yake  # type: ignore
    _HAS_YAKE = True
except Exception:
    _HAS_YAKE = False

def _simple_keywords(text: str, top_k: int = 15) -> List[str]:
    text = (text or "").lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", text)
    stop = {
        "the","and","for","with","that","this","from","your","you","are",
        "was","were","have","has","had","use","using","used","into","only",
        "can","will","about","into","when","then","them","they","their",
        "project","readme","code","file","files","data","based","also"
    }
    freq = {}
    for w in words:
        if w in stop:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_k]]

def extract_keywords(text: str, top_k: int = 15) -> List[str]:
    if _HAS_YAKE:
        kw_extractor = yake.KeywordExtractor(top=top_k, stopwords=None)
        pairs = kw_extractor.extract_keywords(text or "")
        seen, out = set(), []
        for w, _ in pairs:
            if len(w.split()) <= 4 and len(w) > 2:
                k = w.lower()
                if k not in seen:
                    seen.add(k)
                    out.append(w)
        return out
    # fallback
    return _simple_keywords(text, top_k)

def _guess_raw_readme_url(repo_url: str) -> str:
    repo_url = repo_url.rstrip("/")
    parts = repo_url.split("/")
    if len(parts) >= 5 and parts[-2] == "tree":
        user, repo, _, branch = parts[-4], parts[-3], parts[-2], parts[-1]
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/README.md"
    if len(parts) >= 5 and parts[-2] == "blob":
        user, repo, _, branch = parts[-5], parts[-4], parts[-3], parts[-2]
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/README.md"
    user, repo = parts[-2], parts[-1]
    return f"https://raw.githubusercontent.com/{user}/{repo}/main/README.md"

def fetch_repo_readme(repo_url: str) -> str:
    for branch in ["main", "master"]:
        raw = _guess_raw_readme_url(repo_url).replace("/main/", f"/{branch}/")
        r = requests.get(raw, timeout=15)
        if r.ok and r.text.strip():
            return r.text
    raise RuntimeError("Could not fetch README.md (check URL/visibility)")

def lint_readme_sections(text: str) -> List[str]:
    headings = re.findall(r"^(#{1,6})\s+(.*)$", text or "", flags=re.MULTILINE)
    return [h[1].strip() for h in headings]