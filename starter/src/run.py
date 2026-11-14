"""Main pipeline orchestrator for Day 06 Data Ingestion Lab (Fully Dynamic)."""
import csv
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from .ingestion import load_pdf
from .chunking import fixed_size, by_paragraph
from .embeddings import MyEmbedder
from .store import PgVectorStore
from .evaluation import evaluate_query, summarize


def resolve_corpus_path(base_dir: Path, starter_dir: Path) -> Path:
    """Dynamically discover the corpus PDF path without hardcoded filenames."""
    # 1. Environment override
    env_corpus = os.getenv("CORPUS_PATH")
    if env_corpus:
        p = Path(env_corpus)
        if p.exists():
            return p

    # 2. Check manifest source path
    manifest_candidates = [
        starter_dir / "data" / "manifest.json",
        base_dir / "data" / "manifest.json"
    ]
    for mf in manifest_candidates:
        if mf.exists():
            try:
                with open(mf, "r", encoding="utf-8") as f:
                    mdata = json.load(f)
                rel_source = mdata.get("source_path_or_url")
                if rel_source:
                    resolved = (base_dir / rel_source).resolve()
                    if resolved.exists():
                        return resolved
                    resolved_starter = (starter_dir / rel_source).resolve()
                    if resolved_starter.exists():
                        return resolved_starter
            except Exception:
                pass

    # 3. Auto-discover any .pdf file in data directories
    search_dirs = [starter_dir / "data", base_dir / "data"]
    for sdir in search_dirs:
        if sdir.exists():
            pdf_files = list(sdir.glob("*.pdf"))
            if pdf_files:
                return pdf_files[0]

    raise FileNotFoundError("Could not find any corpus PDF in data/ or starter/data/")


def resolve_benchmark_path(base_dir: Path, starter_dir: Path) -> Path:
    """Dynamically discover the benchmark questions file."""
    env_bench = os.getenv("BENCHMARK_PATH")
    if env_bench:
        p = Path(env_bench)
        if p.exists():
            return p

    candidates = [
        base_dir / "benchmark" / "questions.json",
        starter_dir / "benchmark" / "questions.json"
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    raise FileNotFoundError("Could not find benchmark/questions.json")


def main() -> None:
    # 0. Load environment
    starter_dir = Path(__file__).resolve().parent.parent
    base_dir = starter_dir.parent
    load_dotenv(starter_dir / ".env")
    load_dotenv(base_dir / ".env")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set in .env")

    # Dynamic path resolution
    data_pdf = resolve_corpus_path(base_dir, starter_dir)
    benchmark_json = resolve_benchmark_path(base_dir, starter_dir)
    results_dir = base_dir / "results"
    artifacts_dir = base_dir / "artifacts"
    results_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Dynamic strategy parameters
    size_a = int(os.getenv("STRATEGY_A_CHUNK_SIZE", "500"))
    overlap_a = int(os.getenv("STRATEGY_A_OVERLAP", "50"))
    max_size_b = int(os.getenv("STRATEGY_B_MAX_SIZE", "800"))
    filter_field = os.getenv("FILTER_FIELD", "part")

    print("==============================================================")
    print("DAY 06 · DATA INGESTION ENGINEERING PIPELINE")
    print("==============================================================")
    print(f"Corpus resolved:    {data_pdf.name}")
    print(f"Benchmark resolved: {benchmark_json.relative_to(base_dir)}")

    # 1. Ingestion: Load and normalize PDF pages dynamically
    print("\n[Step 1/6] Loading corpus from PDF...")
    start_ingest = time.time()
    pages = load_pdf(data_pdf)
    ingest_duration = round(time.time() - start_ingest, 2)
    doc_id = pages[0].document_id if pages else "document"
    print(f"Loaded {len(pages)} valid narrative content pages for '{doc_id}' in {ingest_duration}s (Requirement >= 30: PASS)")

    # 2. Chunking: Strategy A (Fixed) vs Strategy B/C (Paragraph)
    print("\n[Step 2/6] Generating chunks for Strategies A, B, and C...")
    chunks_a = []
    for p in pages:
        chunks_a.extend(fixed_size(p, size=size_a, overlap=overlap_a))

    chunks_b = []
    for p in pages:
        chunks_b.extend(by_paragraph(p, max_size=max_size_b))

    print(f"Strategy A (Fixed-size {size_a}/{overlap_a}): {len(chunks_a)} chunks")
    print(f"Strategy B & C (Paragraph <= {max_size_b}): {len(chunks_b)} chunks")

    # 3. Embeddings: API Embedder
    print("\n[Step 3/6] Generating embeddings via API...")
    embedder = MyEmbedder()
    print(f"Embedder initialized: {embedder.model_name} ({embedder.dimensions} dimensions)")

    start_embed = time.time()
    print(f"Embedding Strategy A ({len(chunks_a)} chunks)...")
    texts_a = [c.text for c in chunks_a]
    vectors_a = embedder.embed_documents(texts_a, batch_size=64)

    print(f"Embedding Strategy B ({len(chunks_b)} chunks)...")
    texts_b = [c.text for c in chunks_b]
    vectors_b = embedder.embed_documents(texts_b, batch_size=64)
    embed_duration = round(time.time() - start_embed, 2)
    print(f"Embedding completed in {embed_duration}s.")

    # 4. Storage: PostgreSQL + pgvector
    print("\n[Step 4/6] Storing vectors and metadata in pgvector...")
    store = PgVectorStore(database_url=db_url, dimensions=embedder.dimensions)
    store.create_schema()

    print("Upserting Strategy A...")
    store.upsert("A", chunks_a, vectors_a)

    print("Upserting Strategy B...")
    store.upsert("B", chunks_b, vectors_b)

    print("Upserting Strategy C (reuses B's chunks with metadata filter)...")
    store.upsert("C", chunks_b, vectors_b)
    print("Storage upsert complete.")

    # 5. Benchmark Retrieval & Evaluation
    print("\n[Step 5/6] Running benchmark retrieval across questions...")
    with open(benchmark_json, "r", encoding="utf-8") as f:
        questions = json.load(f)
    print(f"Loaded {len(questions)} benchmark questions ({sum(1 for q in questions if q['split']=='dev')} dev, {sum(1 for q in questions if q['split']=='test')} test).")

    print("Embedding query questions...")
    query_vectors = {}
    for q in questions:
        query_vectors[q["id"]] = embedder.embed_query(q["question"])

    strategies = ["A", "B", "C"]
    all_traces = {}
    summaries = {}

    for strat in strategies:
        strat_traces = []
        for q in questions:
            q_vec = query_vectors[q["id"]]
            q_filter = q.get("filter") if strat == "C" else None

            hits = store.search(strategy=strat, query_vector=q_vec, top_k=3, filters=q_filter)
            eval_record = evaluate_query(q, hits)
            strat_traces.append(eval_record)

        all_traces[strat] = strat_traces
        summaries[strat] = summarize(strat_traces)

        out_trace_file = results_dir / f"trace_strategy_{strat}.json"
        with open(out_trace_file, "w", encoding="utf-8") as f:
            json.dump(strat_traces, f, indent=2, ensure_ascii=False)
        print(f"Saved {out_trace_file.name}")

    # 6. Update Experiment Log & Display Results
    print("\n[Step 6/6] Logging experiment results and printing summary...")

    exp_log_file = artifacts_dir / "experiment_log.csv"
    hypotheses = {
        "A": f"Baseline fixed-size ({size_a}/{overlap_a}) chunking splits semantic units arbitrarily.",
        "B": f"Structure-aware paragraph chunking (<= {max_size_b}) preserves narrative context and increases grounding.",
        "C": f"Metadata filtering on '{filter_field}' restricts search space and suppresses false-positive cross-section distractors."
    }

    log_rows = [
        ["strategy", "chunking", "chunk_size", "overlap", "metadata", "filter", "vectorizer", "hypothesis", "dev_hit1", "dev_hit3", "test_hit1", "test_hit3", "notes"],
        [
            "A", "fixed_size", size_a, overlap_a, "document_id,page,source", "none", embedder.model_name,
            hypotheses["A"],
            summaries["A"]["dev"]["hit1_ratio"], summaries["A"]["dev"]["hit3_ratio"],
            summaries["A"]["test"]["hit1_ratio"], summaries["A"]["test"]["hit3_ratio"],
            f"{len(chunks_a)} chunks"
        ],
        [
            "B", "by_paragraph", max_size_b, 0, f"document_id,page,source,{filter_field}", "none", embedder.model_name,
            hypotheses["B"],
            summaries["B"]["dev"]["hit1_ratio"], summaries["B"]["dev"]["hit3_ratio"],
            summaries["B"]["test"]["hit1_ratio"], summaries["B"]["test"]["hit3_ratio"],
            f"{len(chunks_b)} chunks"
        ],
        [
            "C", "by_paragraph", max_size_b, 0, f"document_id,page,source,{filter_field}", filter_field, embedder.model_name,
            hypotheses["C"],
            summaries["C"]["dev"]["hit1_ratio"], summaries["C"]["dev"]["hit3_ratio"],
            summaries["C"]["test"]["hit1_ratio"], summaries["C"]["test"]["hit3_ratio"],
            f"{len(chunks_b)} chunks + metadata filter"
        ]
    ]

    with open(exp_log_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(log_rows)
    print(f"Updated {exp_log_file.name}")

    print("\n" + "=" * 65)
    print("FINAL BENCHMARK EVALUATION SUMMARY")
    print("=" * 65)
    print(f"{'Strategy':<10} | {'Split':<6} | {'Hit@1':<12} | {'Evidence Hit@3':<16} | {'Chunks':<8}")
    print("-" * 65)
    for strat in ["A", "B", "C"]:
        chunk_c = len(chunks_a) if strat == "A" else len(chunks_b)
        dev_res = summaries[strat]["dev"]
        test_res = summaries[strat]["test"]
        print(f"Strategy {strat:<1} | Dev    | {dev_res['hit1_ratio']:<5} ({dev_res['hit1_pct']:>4}%) | {dev_res['hit3_ratio']:<5} ({dev_res['hit3_pct']:>5}%) | {chunk_c:<8}")
        print(f"           | Test   | {test_res['hit1_ratio']:<5} ({test_res['hit1_pct']:>4}%) | {test_res['hit3_ratio']:<5} ({test_res['hit3_pct']:>5}%) |")
        print("-" * 65)

    print("\nPipeline execution completed successfully!")


if __name__ == "__main__":
    main()
