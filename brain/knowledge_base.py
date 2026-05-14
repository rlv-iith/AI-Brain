"""
Loads every .md file from the knowledge/ tree and returns them as text chunks.
Add or edit Markdown files in knowledge/ — no code change needed.
"""

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


def load_chunks() -> list[dict]:
    """
    Returns list of { text, source, category } dicts.
    Each .md file becomes one chunk (split further in rag.py if needed).
    """
    chunks = []
    for md_file in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        rel = md_file.relative_to(KNOWLEDGE_DIR)
        category = rel.parts[0] if len(rel.parts) > 1 else "general"
        chunks.append({
            "text": text,
            "source": str(rel),
            "category": category,
        })
    return chunks
