"""Read and normalize source data dynamically driven by manifest.json."""
import json
import re
import unicodedata
from pathlib import Path
import pypdf
from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without discarding paragraph structure.

    Converts characters to NFC standard, handles line breaks, and preserves
    double-newlines for semantic paragraph chunking.
    """
    if not text:
        return ""

    # Normalize Unicode to NFC
    text = unicodedata.normalize("NFC", text)

    # Standardize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Clean horizontal whitespace per line
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Collapse excessive newlines (> 2) down to 2 to preserve paragraph boundaries
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def load_pdf(
    path: Path | str,
    manifest_path: Path | str | None = None,
    document_id: str | None = None,
    source: str | None = None
) -> list[DocumentPage]:
    """Extract pages dynamically driven by manifest.json as the Single Source of Truth.

    Loads the valid page list and all custom metadata fields directly from the manifest.
    Falls back gracefully if manifest is not present, without hardcoded book-specific values.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found at: {path}")

    # Resolve manifest path dynamically
    manifest_data = None
    if manifest_path:
        m_path = Path(manifest_path)
        if m_path.exists():
            with open(m_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
    else:
        candidate_manifests = [
            path.parent / "manifest.json",
            path.parent.parent / "data" / "manifest.json",
            path.parent.parent.parent / "data" / "manifest.json"
        ]
        for cand in candidate_manifests:
            if cand.exists():
                with open(cand, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                break

    # Build page configuration map from manifest
    valid_page_map: dict[int, dict] = {}
    if manifest_data:
        document_id = document_id or manifest_data.get("source_id", path.stem.lower())
        source = source or manifest_data.get("source_path_or_url", str(path))
        if "pages" in manifest_data:
            for p_info in manifest_data["pages"]:
                p_num = p_info["page"]
                # Extract all metadata attributes defined in the page entry
                meta = {
                    k: v
                    for k, v in p_info.items()
                    if k not in ("page", "character_count", "raw_character_count")
                }
                # Normalize section/part compatibility
                if "section" in p_info and "part" not in meta:
                    meta["part"] = p_info["section"]
                valid_page_map[p_num] = meta
    else:
        document_id = document_id or path.stem.lower()
        source = source or str(path)

    reader = pypdf.PdfReader(str(path))
    valid_pages: list[DocumentPage] = []
    empty_pages_logged: list[int] = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1

        # If manifest defined valid pages, filter by manifest!
        if valid_page_map and page_num not in valid_page_map:
            continue

        raw_text = page.extract_text() or ""
        normalized = normalize_text(raw_text)

        if not normalized:
            empty_pages_logged.append(page_num)
            continue

        page_meta = valid_page_map.get(page_num, {})

        valid_pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=page_num,
                text=normalized,
                metadata=dict(page_meta)
            )
        )

    return valid_pages
