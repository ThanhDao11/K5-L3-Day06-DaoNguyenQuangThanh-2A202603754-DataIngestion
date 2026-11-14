"""Re-balance and stratify the 20 benchmark questions across the whole book."""
import json
import csv
import os

with open("starter/data/extracted_pages.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

page_map = {p["page"]: " ".join(p["text"].split()) for p in pages}

# Stratified Dev set (15 questions spanning Prologue, Part One, Part Two, Epilogue)
dev_specs = [
    {
        "type": "filter_test",
        "question": "Whose mythological story did the alchemist read in the book found in the caravan?",
        "expected_answer": "The story of Narcissus.",
        "gold_page": 11,
        "anchor": "found a story about Narcissus",
        "filter": {"part": "Prologue"}
    },
    {
        "type": "direct",
        "question": "What kind of tree was growing in the ruins of the sacristy where Santiago slept with his sheep?",
        "expected_answer": "An enormous sycamore tree.",
        "gold_page": 14,
        "anchor": "an enormous sycamore had grown on the spot where the sacristy",
        "filter": None
    },
    {
        "type": "direct",
        "question": "What profession had Santiago's parents originally wished for him to follow?",
        "expected_answer": "A Catholic priest.",
        "gold_page": 17,
        "anchor": "His parents had wanted him to become a priest",
        "filter": None
    },
    {
        "type": "paraphrase",
        "question": "What primary desire motivated Santiago to wander as a shepherd instead of serving in the clergy?",
        "expected_answer": "His purpose and desire in life was to travel and know the world.",
        "gold_page": 17,
        "anchor": "His purpose in life was to travel, and, after two years of walking the Andalusian terrain",
        "filter": None
    },
    {
        "type": "direct",
        "question": "In Santiago's recurring dream, who takes him by the hands and transports him to the Egyptian pyramids?",
        "expected_answer": "A child.",
        "gold_page": 21,
        "anchor": "the child took me by both hands and transported me to the Egyptian pyramids",
        "filter": None
    },
    {
        "type": "direct",
        "question": "What payment did the Gypsy woman demand for interpreting Santiago's dream?",
        "expected_answer": "One-tenth of the treasure.",
        "gold_page": 22,
        "anchor": "I want one-tenth of the treasure, if you find it",
        "filter": None
    },
    {
        "type": "conditional",
        "question": "What payment did Melchizedek demand from Santiago to tell him how to find the hidden treasure?",
        "expected_answer": "One-tenth of his flock of sheep.",
        "gold_page": 26,
        "anchor": "Give me one-tenth of your sheep",
        "filter": None
    },
    {
        "type": "direct",
        "question": "What Mediterranean wind brought the Moors and the scent of the desert into Andalusia?",
        "expected_answer": "The levanter.",
        "gold_page": 30,
        "anchor": "people called it the levanter, because on it the Moors had come",
        "filter": None
    },
    {
        "type": "paraphrase",
        "question": "What is the secret of happiness according to the wise man's story of the oil spoons?",
        "expected_answer": "To see all marvels of the world without forgetting the drops of oil on the spoon.",
        "gold_page": 34,
        "anchor": "The secret of happiness is to see all the marvels of the world, and never to forget the drops of oil on the spoon",
        "filter": None
    },
    {
        "type": "filter_test",
        "question": "Why did the crystal merchant offer food to Santiago after the boy cleaned his display glasses?",
        "expected_answer": "Because Muslim law (the Koran) requires feeding a hungry person.",
        "gold_page": 44,
        "anchor": "The Koran requires me to feed a hungry person",
        "filter": {"part": "Part One"}
    },
    {
        "type": "conditional",
        "question": "Why was the crystal merchant afraid to make his pilgrimage to Mecca?",
        "expected_answer": "He feared that once his dream was fulfilled, he would have no reason left to live.",
        "gold_page": 48,
        "anchor": "I’m afraid that if my dream is realized, I’ll have no reason to go on living",
        "filter": None
    },
    {
        "type": "direct",
        "question": "What business innovation did Santiago propose to increase sales in the crystal shop?",
        "expected_answer": "Selling hot tea in crystal glasses to customers climbing the hill.",
        "gold_page": 51,
        "anchor": "sell tea in the crystal glasses",
        "filter": None
    },
    {
        "type": "direct",
        "question": "What is the liquid portion of the Master Work called, and what are its properties?",
        "expected_answer": "The Elixir of Life; it cures all illnesses and keeps the alchemist from aging.",
        "gold_page": 66,
        "anchor": "liquid part of the Master Work was called the Elixir of Life",
        "filter": None
    },
    {
        "type": "direct",
        "question": "What was the name of the desert woman Santiago met and fell in love with at the oasis well?",
        "expected_answer": "Fatima.",
        "gold_page": 75,
        "anchor": "What’s your name?” he asked. “Fatima,” the girl said",
        "filter": None
    },
    {
        "type": "filter_test",
        "question": "Where did Santiago return to dig for his chest of Spanish gold coins in the Epilogue?",
        "expected_answer": "At the abandoned church in Spain under the roots of the sycamore tree.",
        "gold_page": 124,
        "anchor": "small, abandoned church just as night was falling. The sycamore was still there in the sacristy",
        "filter": {"part": "Epilogue"}
    }
]

# Stratified Test set (5 questions distributed across early, mid, and late parts)
test_specs = [
    {
        "type": "direct",
        "question": "According to Melchizedek, what is the world's greatest lie?",
        "expected_answer": "That at a certain point, we lose control of our lives and they become controlled by fate.",
        "gold_page": 24,
        "anchor": "at a certain point in our lives, we lose control of what’s happening to us, and our lives become controlled by fate. That’s the world’s greatest lie",
        "filter": None
    },
    {
        "type": "filter_test",
        "question": "What are the names of the two divination stones Melchizedek gave to Santiago?",
        "expected_answer": "Urim and Thummim.",
        "gold_page": 32,
        "anchor": "They are called Urim and Thummim. The black signifies ‘yes,’ and the white ‘no.’",
        "filter": {"part": "Part One"}
    },
    {
        "type": "conditional",
        "question": "Why were desert oases considered neutral territory during tribal wars?",
        "expected_answer": "Because the majority of inhabitants were women and children, making them safe places of refuge.",
        "gold_page": 71,
        "anchor": "oases were always considered to be neutral territories, because the majority of the inhabitants were women and children",
        "filter": None
    },
    {
        "type": "conditional",
        "question": "What severe penalty did the oasis chieftains promise Santiago if no enemies attacked the oasis?",
        "expected_answer": "Santiago would be executed with one of the unused weapons.",
        "gold_page": 85,
        "anchor": "If at least one of them hasn’t been used by the end of the day tomorrow, one will be used on you",
        "filter": None
    },
    {
        "type": "filter_test",
        "question": "What miraculous feat did the Alchemist claim Santiago could perform within three days?",
        "expected_answer": "Transform himself into the wind.",
        "gold_page": 107,
        "anchor": "He is going to transform himself into the wind, just to demonstrate his powers",
        "filter": {"part": "Part Two"}
    }
]

final_records = []

# Process Dev (q01 - q15)
for idx, q in enumerate(dev_specs, start=1):
    qid = f"q{idx:02d}"
    p = q["gold_page"]
    anchor = q["anchor"]
    txt = page_map.get(p, "")
    
    clean_txt = txt.replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "")
    clean_anchor = anchor.replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "")
    
    idx_pos = clean_txt.lower().find(clean_anchor.lower())
    if idx_pos == -1:
        snippet = anchor
    else:
        start = max(0, idx_pos - 10)
        end = min(len(txt), idx_pos + len(anchor) + 20)
        snippet = txt[start:end].strip()
        
    final_records.append({
        "id": qid,
        "split": "dev",
        "type": q["type"],
        "question": q["question"],
        "expected_answer": q["expected_answer"],
        "gold_source_id": "the-alchemist",
        "gold_page": p,
        "evidence_quote": snippet,
        "filter": q["filter"]
    })

# Process Test (q16 - q20)
for idx, q in enumerate(test_specs, start=16):
    qid = f"q{idx:02d}"
    p = q["gold_page"]
    anchor = q["anchor"]
    txt = page_map.get(p, "")
    
    clean_txt = txt.replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "")
    clean_anchor = anchor.replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "")
    
    idx_pos = clean_txt.lower().find(clean_anchor.lower())
    if idx_pos == -1:
        snippet = anchor
    else:
        start = max(0, idx_pos - 10)
        end = min(len(txt), idx_pos + len(anchor) + 20)
        snippet = txt[start:end].strip()
        
    final_records.append({
        "id": qid,
        "split": "test",
        "type": q["type"],
        "question": q["question"],
        "expected_answer": q["expected_answer"],
        "gold_source_id": "the-alchemist",
        "gold_page": p,
        "evidence_quote": snippet,
        "filter": q["filter"]
    })

print(f"Total compiled questions: {len(final_records)}")
dev_pages = [q["gold_page"] for q in final_records if q["split"] == "dev"]
test_pages = [q["gold_page"] for q in final_records if q["split"] == "test"]
print("Dev pages distribution:", dev_pages)
print("Test pages distribution:", test_pages)

# Save to benchmark/
os.makedirs("benchmark", exist_ok=True)
with open("benchmark/questions.json", "w", encoding="utf-8") as f:
    json.dump(final_records, f, indent=2, ensure_ascii=False)

with open("benchmark/questions.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "split", "type", "question", "expected_answer", "gold_source_id", "gold_page", "evidence_quote", "filter"])
    for r in final_records:
        writer.writerow([
            r["id"],
            r["split"],
            r["type"],
            r["question"],
            r["expected_answer"],
            r["gold_source_id"],
            r["gold_page"],
            r["evidence_quote"],
            json.dumps(r["filter"]) if r["filter"] else ""
        ])

# Also save to starter/benchmark/
os.makedirs("starter/benchmark", exist_ok=True)
with open("starter/benchmark/questions.json", "w", encoding="utf-8") as f:
    json.dump(final_records, f, indent=2, ensure_ascii=False)
with open("starter/benchmark/questions.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "split", "type", "question", "expected_answer", "gold_source_id", "gold_page", "evidence_quote", "filter"])
    for r in final_records:
        writer.writerow([
            r["id"],
            r["split"],
            r["type"],
            r["question"],
            r["expected_answer"],
            r["gold_source_id"],
            r["gold_page"],
            r["evidence_quote"],
            json.dumps(r["filter"]) if r["filter"] else ""
        ])

print("Saved successfully to both benchmark/ and starter/benchmark/ directories.")
