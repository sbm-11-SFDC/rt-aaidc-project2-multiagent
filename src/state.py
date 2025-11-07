from typing import TypedDict, List, Optional, Dict

class MASState(TypedDict, total=False):
    repo_url: str
    readme_text: str
    sections: List[str]
    keywords: List[str]
    metadata_suggestions: Dict[str, List[str]]
    content_suggestions: Dict[str, str]
    review_notes: str
    final_output: str