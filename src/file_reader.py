"""
File reader module — reads content from various file formats.
"""

import os
from pathlib import Path


def read_file(file_path: str) -> str:
    """Read content from a file based on its extension."""
    ext = Path(file_path).suffix.lower()

    if ext == ".md" or ext == ".txt":
        return _read_text(file_path)
    elif ext == ".docx":
        return _read_docx(file_path)
    elif ext == ".pdf":
        return _read_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _read_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _read_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def _read_pdf(file_path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n\n".join(text_parts)


_KNOWN_SENSITIVITIES = {"public", "internal", "private"}
_FILE_EXT_PATTERNS = {".md", ".txt", ".docx", ".pdf"}


def _looks_like_filename(s: str) -> bool:
    """A path component that has a known file extension is a file, not a directory."""
    return any(s.lower().endswith(ext) for ext in _FILE_EXT_PATTERNS)


def extract_metadata_from_path(file_path: str, base_dir: str) -> dict:
    """
    Extract metadata from the file's position in the directory structure.

    Expected structure:
        knowledge-base/{sensitivity}/{category}/{content_type}/filename.md

    Example:
        knowledge-base/public/leadership/frameworks/delegation-101.md
        -> sensitivity=public, category=leadership, content_type=framework

    Strict rules (post phase 1.5 hygiene fix):
      - A path component that looks like a filename (has .md/.txt/.docx/.pdf
        extension) is NEVER used as metadata. This prevents the historical bug
        where files placed at the KB root (no subdirs) had their filename leak
        into 'sensitivity' / 'category'.
      - sensitivity is only set from path if parts[0] is one of the known levels.
      - 'category' is only set from a real subdirectory, never from a filename.
        If it cannot be derived, the key is left ABSENT — the caller (ingest.py)
        must then rely on frontmatter, or fail loudly via _validate_required_metadata.
    """
    rel_path = os.path.relpath(file_path, base_dir)
    parts = Path(rel_path).parts

    # Only directory components count as metadata sources — never the filename
    dir_parts = [p for p in parts if not _looks_like_filename(p)]

    metadata: dict = {
        "source": os.path.basename(file_path),
        "tags": [],
    }

    if len(dir_parts) >= 1 and dir_parts[0].lower() in _KNOWN_SENSITIVITIES:
        metadata["sensitivity"] = dir_parts[0].lower()

    if len(dir_parts) >= 2:
        metadata["category"] = dir_parts[1]

    if len(dir_parts) >= 3:
        content_type_map = {
            "frameworks": "framework",
            "how-to": "how-to",
            "checklists": "checklist",
            "case-studies": "case-study",
            "principles": "princíp",
            "stories": "príbeh",
            "analyses": "analýza",
        }
        folder_name = dir_parts[2]
        metadata["content_type"] = content_type_map.get(folder_name, folder_name)

    return metadata


def extract_yaml_frontmatter(text: str) -> tuple[dict, str]:
    """
    Extract YAML frontmatter from markdown files.
    Returns (metadata_dict, content_without_frontmatter).

    Expected format:
        ---
        category: leadership
        content_type: framework
        tags: [delegation, management]
        audience: founder
        ---
        Actual content here...
    """
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    try:
        import yaml
        frontmatter = yaml.safe_load(parts[1])
        content = parts[2].strip()
        return frontmatter if frontmatter else {}, content
    except Exception:
        return {}, text
