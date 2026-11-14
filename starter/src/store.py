"""Store and search vectors using PostgreSQL + pgvector."""
import json
from typing import Any
import psycopg
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int = 1536) -> None:
        """Initialize PostgreSQL connection settings and validate dimensions."""
        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        """Create extension, chunks table, and metadata/vector indices."""
        with psycopg.connect(self.database_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS chunks (
                        id TEXT NOT NULL,
                        strategy VARCHAR(10) NOT NULL,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        page INT NOT NULL,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({self.dimensions}) NOT NULL,
                        PRIMARY KEY (strategy, id)
                    );
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_strategy ON chunks (strategy);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING gin (metadata);")

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Clean existing strategy records and insert chunks with vectors.

        Guarantees idempotent re-ingestion without duplicate chunk accumulation.
        """
        if len(chunks) != len(vectors):
            raise ValueError(f"Chunk count ({len(chunks)}) does not match vector count ({len(vectors)})")

        if not chunks:
            return

        with psycopg.connect(self.database_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Remove obsolete records for this strategy
                cur.execute("DELETE FROM chunks WHERE strategy = %s;", (strategy,))

                insert_sql = """
                    INSERT INTO chunks (id, strategy, document_id, source, page, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector);
                """

                rows = []
                for chunk, vec in zip(chunks, vectors):
                    vec_str = f"[{','.join(str(x) for x in vec)}]"
                    meta_str = json.dumps(chunk.metadata, ensure_ascii=False)
                    rows.append((
                        chunk.chunk_id,
                        strategy,
                        chunk.document_id,
                        chunk.source,
                        chunk.page,
                        chunk.text,
                        meta_str,
                        vec_str
                    ))

                cur.executemany(insert_sql, rows)

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Perform cosine similarity vector search with optional metadata filtering.

        Returns list of hits sorted by descending cosine similarity.
        """
        vec_str = f"[{','.join(str(x) for x in query_vector)}]"

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                if filters:
                    filter_str = json.dumps(filters, ensure_ascii=False)
                    query_sql = """
                        SELECT id, document_id, source, page, text, metadata,
                               1 - (embedding <=> %s::vector) AS score
                        FROM chunks
                        WHERE strategy = %s
                          AND metadata @> %s::jsonb
                        ORDER BY embedding <=> %s::vector ASC
                        LIMIT %s;
                    """
                    cur.execute(query_sql, (vec_str, strategy, filter_str, vec_str, top_k))
                else:
                    query_sql = """
                        SELECT id, document_id, source, page, text, metadata,
                               1 - (embedding <=> %s::vector) AS score
                        FROM chunks
                        WHERE strategy = %s
                        ORDER BY embedding <=> %s::vector ASC
                        LIMIT %s;
                    """
                    cur.execute(query_sql, (vec_str, strategy, vec_str, top_k))

                results = []
                for row in cur.fetchall():
                    results.append({
                        "id": row[0],
                        "document_id": row[1],
                        "source": row[2],
                        "page": row[3],
                        "text": row[4],
                        "metadata": row[5],
                        "score": float(row[6])
                    })

                return results
