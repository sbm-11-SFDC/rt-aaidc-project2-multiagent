from src.tools import validate_repo_url, sanitize_text

def test_validate_repo_url_valid():
    assert validate_repo_url("https://github.com/owner/repo")

def test_validate_repo_url_invalid():
    assert not validate_repo_url("https://google.com/owner/repo")
    assert not validate_repo_url("")

def test_sanitize_text_truncation():
    txt = "a" * 5000
    out = sanitize_text(txt, max_len=1000)
    assert len(out) <= 1000
    assert out.endswith("...")