"""Embedder adapter connecting to OpenRouter (or OpenAI) embedding API."""
import os
from typing import Protocol
from dotenv import load_dotenv
from openai import OpenAI


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Production embedder using OpenRouter / OpenAI API.

    Guarantees true semantic embeddings; never silently falls back to mocks.
    Dimensions and parameters are dynamically loaded from environment or probed from API.
    """

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None
    ) -> None:
        load_dotenv()
        self.model_name = (
            model_name
            or os.getenv("EMBEDDING_MODEL")
            or "openai/text-embedding-3-small"
        )
        base_url = (
            base_url
            or os.getenv("EMBEDDING_BASE_URL")
            or os.getenv("OPENROUTER_BASE_URL")
            or "https://openrouter.ai/api/v1"
        )
        self.dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

        resolved_key = (
            api_key
            or os.getenv("OPENROUTER_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        if not resolved_key:
            raise RuntimeError(
                "Missing API key. Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env before running."
            )

        self.client = OpenAI(
            api_key=resolved_key,
            base_url=base_url
        )

    def embed_documents(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """Embed a list of documents in batches to prevent API payload overflow."""
        if not texts:
            return []

        all_vectors: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            clean_batch = [t if t.strip() else " " for t in batch]

            response = self.client.embeddings.create(
                model=self.model_name,
                input=clean_batch
            )

            # Sort by index to ensure order is strictly preserved
            sorted_data = sorted(response.data, key=lambda item: item.index)
            for item in sorted_data:
                vec = item.embedding
                if len(vec) != self.dimensions:
                    self.dimensions = len(vec)
                all_vectors.append(vec)

        return all_vectors

    def embed_query(self, question: str) -> list[float]:
        """Embed a single query string for vector similarity search."""
        if not question.strip():
            question = " "
        results = self.embed_documents([question])
        return results[0]
