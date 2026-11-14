"""Implement fixed-size and structure-aware chunking."""
import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split text into overlapping character windows and retain page metadata.

    Strategy A baseline chunking.
    """
    text = page.text.strip()
    if not text:
        return []

    if len(text) <= size:
        return [
            Chunk(
                chunk_id=f"{page.document_id}_p{page.page}_f01",
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=text,
                metadata=dict(page.metadata)
            )
        ]

    chunks: list[Chunk] = []
    step = max(1, size - overlap)
    start = 0
    chunk_idx = 1

    while start < len(text):
        end = min(len(text), start + size)
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(
                Chunk(
                    chunk_id=f"{page.document_id}_p{page.page}_f{chunk_idx:02d}",
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=chunk_text,
                    metadata=dict(page.metadata)
                )
            )
            chunk_idx += 1

        if end >= len(text):
            break
        start += step

    return chunks


def by_paragraph(page: DocumentPage, max_size: int = 800) -> list[Chunk]:
    """Group natural paragraphs and split oversized paragraphs gracefully.

    Strategy B & C structure-aware chunking for high coherence.
    """
    text = page.text.strip()
    if not text:
        return []

    # Split on double newlines to find natural paragraph boundaries
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[Chunk] = []
    current_paras: list[str] = []
    current_length = 0
    chunk_idx = 1

    def flush_current() -> None:
        nonlocal chunk_idx, current_paras, current_length
        if not current_paras:
            return
        combined_text = "\n\n".join(current_paras).strip()
        if combined_text:
            chunks.append(
                Chunk(
                    chunk_id=f"{page.document_id}_p{page.page}_p{chunk_idx:02d}",
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=combined_text,
                    metadata=dict(page.metadata)
                )
            )
            chunk_idx += 1
        current_paras = []
        current_length = 0

    for para in paragraphs:
        # If a single paragraph is larger than max_size, split by sentence
        if len(para) > max_size:
            flush_current()
            # Split paragraph by sentences
            sentences = re.split(r"(?<=[.!?]) +", para)
            sent_accum: list[str] = []
            sent_len = 0
            for sent in sentences:
                if sent_len + len(sent) > max_size and sent_accum:
                    chunks.append(
                        Chunk(
                            chunk_id=f"{page.document_id}_p{page.page}_p{chunk_idx:02d}",
                            document_id=page.document_id,
                            source=page.source,
                            page=page.page,
                            text=" ".join(sent_accum).strip(),
                            metadata=dict(page.metadata)
                        )
                    )
                    chunk_idx += 1
                    sent_accum = [sent]
                    sent_len = len(sent)
                else:
                    sent_accum.append(sent)
                    sent_len += len(sent) + 1
            if sent_accum:
                chunks.append(
                    Chunk(
                        chunk_id=f"{page.document_id}_p{page.page}_p{chunk_idx:02d}",
                        document_id=page.document_id,
                        source=page.source,
                        page=page.page,
                        text=" ".join(sent_accum).strip(),
                        metadata=dict(page.metadata)
                    )
                )
                chunk_idx += 1
        else:
            # Check if adding this paragraph exceeds max_size
            added_len = len(para) + (2 if current_paras else 0)
            if current_length + added_len > max_size and current_paras:
                flush_current()
            current_paras.append(para)
            current_length += added_len

    flush_current()
    return chunks
