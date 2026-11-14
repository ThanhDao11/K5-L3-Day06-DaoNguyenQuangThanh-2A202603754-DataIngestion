"""Evaluate retrieved evidence and preserve per-query traces."""
import re
from typing import Any


def _is_evidence_hit(gold_page: int, evidence_quote: str, hit: dict[str, Any]) -> bool:
    """Check if a retrieved chunk matches the gold page and contains the evidence quote."""
    if hit.get("page") != gold_page:
        return False

    hit_text = hit.get("text", "").lower()
    clean_hit = re.sub(r"\s+", " ", hit_text)

    # Clean quote
    clean_quote = re.sub(r"\s+", " ", evidence_quote.lower().strip())
    clean_quote = clean_quote.replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "")

    # Direct substring check
    if clean_quote in clean_hit:
        return True

    # Token overlap check (if quote is long or boundary slightly shifted)
    tokens = [re.sub(r"[^\w]", "", w) for w in clean_quote.split() if len(w) > 3]
    if tokens:
        matches = sum(1 for t in tokens if t in clean_hit)
        if matches / len(tokens) >= 0.75:
            return True

    return False


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check source/page and gold evidence coverage; retain Hit@1 and Hit@3 trace."""
    gold_page = question["gold_page"]
    evidence_quote = question.get("evidence_quote", "")

    top_hits_evaluated = []
    for rank, hit in enumerate(hits[:3], start=1):
        is_hit = _is_evidence_hit(gold_page, evidence_quote, hit)
        top_hits_evaluated.append({
            "rank": rank,
            "chunk_id": hit.get("id"),
            "page": hit.get("page"),
            "score": round(hit.get("score", 0.0), 4),
            "metadata": hit.get("metadata", {}),
            "text": hit.get("text", ""),
            "is_hit": is_hit
        })

    hit_at_1 = bool(top_hits_evaluated and top_hits_evaluated[0]["is_hit"])
    hit_at_3 = any(h["is_hit"] for h in top_hits_evaluated)

    return {
        "question_id": question["id"],
        "split": question["split"],
        "type": question.get("type", "direct"),
        "question": question["question"],
        "expected_answer": question.get("expected_answer", ""),
        "gold_page": gold_page,
        "evidence_quote": evidence_quote,
        "filter": question.get("filter"),
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hits": top_hits_evaluated
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by dev/test split."""
    splits = {"dev": [], "test": [], "all": traces}
    for t in traces:
        sp = t.get("split", "dev")
        if sp in splits:
            splits[sp].append(t)

    summary: dict[str, Any] = {}

    for name, items in splits.items():
        total = len(items)
        if total == 0:
            summary[name] = {
                "total": 0,
                "hit1_count": 0,
                "hit1_rate": "N/A",
                "hit3_count": 0,
                "hit3_rate": "N/A"
            }
            continue

        h1 = sum(1 for x in items if x["hit_at_1"])
        h3 = sum(1 for x in items if x["hit_at_3"])

        summary[name] = {
            "total": total,
            "hit1_count": h1,
            "hit1_ratio": f"{h1}/{total}",
            "hit1_pct": round(h1 / total * 100, 1),
            "hit3_count": h3,
            "hit3_ratio": f"{h3}/{total}",
            "hit3_pct": round(h3 / total * 100, 1)
        }

    return summary
