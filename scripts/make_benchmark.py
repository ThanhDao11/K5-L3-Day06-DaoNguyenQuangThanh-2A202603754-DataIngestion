"""Build candidate benchmark questions (35 dev / 15 test)."""
import json
import os

with open("starter/data/extracted_pages.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

# Build map from page number to text
page_text = {p["page"]: p["text"] for p in pages}

# 50 candidate questions across the book
# Each entry: (id, split, qtype, question, expected_answer, gold_page, quote_anchor, filter_dict)
raw_specs = [
    # --- PROLOGUE (Page 11) ---
    ("q01", "dev", "direct", "Why did the lake weep in the story of Narcissus?", "Because each time Narcissus knelt on the bank, the lake could see its own beauty reflected in his eyes.", 11, "I weep for Narcissus, but I never noticed", None),
    ("q02", "dev", "filter_test", "Whose mythological story did the alchemist read in the book from the caravan?", "The story of Narcissus.", 11, "Leafing through the pages, he found a story about Narcissus", {"part": "Prologue"}),

    # --- PART ONE (Pages 14 - 44) ---
    ("q03", "dev", "direct", "What kind of tree was growing on the spot where the sacristy once stood?", "An enormous sycamore tree.", 14, "an enormous sycamore had grown on the spot where the sacristy", None),
    ("q04", "dev", "direct", "What profession did the father of the girl Santiago planned to visit hold?", "He was the proprietor of a dry goods shop.", 15, "the merchant was the proprietor of a dry goods shop", None),
    ("q05", "dev", "direct", "What career had Santiago's parents originally wished for him to follow?", "A Catholic priest.", 17, "His parents had wanted him to become a priest", None),
    ("q06", "dev", "paraphrase", "What fundamental desire made Santiago choose shepherding over the priesthood?", "His desire to travel and see the world.", 17, "he had had a desire to know the world", None),
    ("q07", "dev", "direct", "In Santiago's dream, who takes him by the hand and transports him to the pyramids?", "A child.", 21, "a child appeared and began to play with the sheep", None),
    ("q08", "dev", "direct", "What fraction of the treasure did the Gypsy woman ask for interpreting the dream?", "One-tenth of the treasure.", 22, "If you find your treasure, I want one-tenth of it", None),
    ("q09", "dev", "direct", "Where had Santiago obtained the heavy book he was reading in Tarifa?", "He borrowed it from a priest in the seminary.", 23, "It was a book he had borrowed from a priest in the seminary", None),
    ("q10", "dev", "direct", "According to Melchizedek, what is the world's greatest lie?", "That we lose control of our lives and they become controlled by fate.", 25, "at a certain point in our lives, we lose control of what", None),
    ("q11", "dev", "direct", "What title and city did the old man claim when introducing himself to Santiago?", "King of Salem.", 26, "I am the King of Salem", None),
    ("q12", "dev", "conditional", "What payment did Melchizedek demand from Santiago to help him find his treasure?", "One-tenth of his flock of sheep.", 26, "give me one-tenth of your sheep, I will tell you", None),
    ("q13", "dev", "paraphrase", "How does Melchizedek define a Personal Legend?", "It is what a person has always wanted to accomplish in life.", 28, "It’s what you have always wanted to accomplish", None),
    ("q14", "dev", "direct", "What force appears negative but prepares one's spirit and will to realize their destiny?", "A mysterious force that prepares spirit and will.", 28, "prepares your spirit and your will", None),
    ("q15", "dev", "direct", "What is the Mediterranean wind called that brought the Moors and scent of the desert?", "The levanter.", 32, "people called it the levanter", None),
    ("q16", "dev", "filter_test", "What are the names of the two divination stones Melchizedek gave to Santiago?", "Urim and Thummim.", 35, "They are called Urim and Thummim", {"part": "Part One"}),
    ("q17", "dev", "direct", "What meanings do the black and white divination stones carry?", "The black stone means yes, and the white stone means no.", 35, "The black signifies ‘yes,’ and the white ‘no.’", None),
    ("q18", "dev", "paraphrase", "What is the secret of happiness according to the wise man's story of the spoons?", "To see the marvels of the world without spilling the drops of oil on the spoon.", 37, "never to forget the drops of oil on the spoon", None),
    ("q19", "dev", "direct", "What object in a shop window distracted Santiago when his money was stolen in Tangier?", "An ornate sword with an embossed silver scabbard.", 40, "distracted by the sword, which had an embossed silver scabbard", None),
    ("q20", "dev", "paraphrase", "What universal realization did Santiago have after observing the candy merchant?", "That there exists a universal language that does not depend on words.", 42, "language that doesn’t depend on words", None),
    ("q21", "dev", "filter_test", "Why did the crystal merchant offer food to Santiago after the boy cleaned his wares?", "Because Muslim law (the Koran) obligates feeding a hungry person.", 44, "The Koran requires me to feed a hungry person", {"part": "Part One"}),
    ("q22", "dev", "filter_test", "What goal did Santiago state for taking a job at the crystal shop at the end of Part One?", "He needed money to buy some sheep.", 44, "I need money to buy some sheep", {"part": "Part One"}),

    # --- PART TWO (Pages 46 - 123) ---
    ("q23", "dev", "direct", "What is the fifth obligation of every Muslim according to the crystal merchant?", "A pilgrimage to the holy city of Mecca.", 48, "fifth obligation of every Muslim is a pilgrimage", None),
    ("q24", "dev", "conditional", "Why was the crystal merchant reluctant to make his pilgrimage to Mecca?", "He feared that realizing his dream would leave him with no purpose to go on living.", 48, "afraid that if my dream is realized, I’ll have no reason", None),
    ("q25", "dev", "direct", "What innovative proposal did Santiago make to increase crystal shop sales?", "Serving hot tea in crystal glasses to customers climbing the hill.", 51, "We could sell tea in crystal glasses", None),
    ("q26", "dev", "filter_test", "How long did Santiago work for the crystal merchant before resuming his journey?", "Eleven months and nine days.", 53, "eleven months and nine days", {"part": "Part Two"}),
    ("q27", "dev", "direct", "What heavy luggage was the Englishman surrounded by while preparing for the caravan?", "Trunks filled with books on alchemy.", 56, "surrounded by trunks of books", None),
    ("q28", "dev", "direct", "What was the Englishman's primary motive for joining the desert caravan?", "To find and learn from a true alchemist living at the Al-Fayoum oasis.", 58, "search of a true alchemist", None),
    ("q29", "dev", "direct", "In what compass direction did the desert caravan journey each morning?", "Toward the east.", 61, "The caravan moved toward the east", None),
    ("q30", "dev", "filter_test", "What is the liquid component of the Master Work called, and what does it do?", "The Elixir of Life; it cures illnesses and prevents aging.", 67, "liquid part of the Master Work was called the Elixir of Life", {"part": "Part Two"}),
    ("q31", "dev", "direct", "What is the solid component of the Master Work called in alchemy?", "The Philosopher's Stone.", 67, "solid part was called the Philosopher’s Stone", None),
    ("q32", "dev", "direct", "On what legendary artifact was the Master Work of alchemy originally inscribed?", "The Emerald Tablet.", 68, "The Emerald Tablet, upon which the most important text", None),
    ("q33", "dev", "conditional", "Why were fires strictly forbidden in the caravan camps at night?", "To avoid attracting the attention of warring desert tribes.", 71, "Fires were forbidden at night, so as not to attract", None),
    ("q34", "dev", "filter_test", "Why was the Al-Fayoum oasis considered a neutral sanctuary during desert wars?", "Because it accommodated women and children, and desert custom made it neutral.", 74, "oasis was an area of neutrality", {"part": "Part Two"}),
    ("q35", "dev", "direct", "What was the name of the desert woman Santiago met at the oasis well?", "Fatima.", 79, "Her name was Fatima", None),

    # --- TEST SET (15 questions) ---
    ("q36", "test", "direct", "What omen did Santiago observe when watching two hawks in the desert sky?", "One hawk attacked the other, revealing an omen of an army attacking the oasis.", 83, "one of the hawks made a flashing dive through the sky", None),
    ("q37", "test", "direct", "To whom did Santiago report his prophetic vision of the attack on the oasis?", "To the tribal chieftains and elders of the oasis.", 85, "told them of the vision he had had, and of the two hawks", None),
    ("q38", "test", "conditional", "What severe consequence did the chieftains promise if no enemy appeared at the oasis?", "Santiago would be executed with one of the unused weapons.", 87, "if none of them are used, at least one of them will be used on you", None),
    ("q39", "test", "direct", "Who confronted Santiago on horseback with a falcon on his shoulder after the meeting?", "The Alchemist.", 89, "horseman dressed in black, with a falcon perched on his left shoulder", None),
    ("q40", "test", "conditional", "What test did the Alchemist assign to Santiago during their nocturnal desert ride?", "To demonstrate where life exists in the desert.", 93, "Show me where there is life in the desert", None),
    ("q41", "test", "paraphrase", "Why did the Alchemist advise Santiago to constantly listen to his heart?", "Because wherever his heart is, that is where his treasure will be.", 98, "wherever your heart is, that is where you will find your treasure", None),
    ("q42", "test", "direct", "What did the Alchemist carry openly in his bag that tribal guards thought was a joke?", "The Philosopher's Stone and the Elixir of Life.", 101, "the Philosopher’s Stone and the Elixir of Life", None),
    ("q43", "test", "filter_test", "What miraculous feat did the Alchemist claim Santiago could accomplish in three days?", "Transform himself into the wind.", 105, "going to transform himself into the wind", {"part": "Part Two"}),
    ("q44", "test", "direct", "Which natural element did Santiago speak to first when attempting to become the wind?", "The desert.", 107, "spoke to the desert", None),
    ("q45", "test", "direct", "Which celestial body did Santiago converse with after the desert and the wind?", "The sun.", 110, "turned to the sun", None),
    ("q46", "test", "direct", "At the Coptic monastery, what base metal did the Alchemist transmute into gold?", "Lead.", 114, "melted the lead in an iron pan", None),
    ("q47", "test", "direct", "Into how many pieces did the Alchemist divide the disk of gold at the monastery?", "Four pieces.", 115, "divided the gold into four parts", None),
    ("q48", "test", "direct", "What creature crawled through the sand near the pyramids as an omen to start digging?", "A scarab beetle.", 120, "a scarab beetle scuttled through the sand", None),
    ("q49", "test", "conditional", "What dream did the bandit leader reveal that disclosed the real location of the treasure?", "A recurring dream about a ruined church in Spain with a sycamore tree in the sacristy.", 123, "dreamed that I should travel to the fields of Spain and look for a ruined church", None),
    ("q50", "test", "filter_test", "Where did Santiago return to dig up his chest of Spanish gold coins in the Epilogue?", "Under the sycamore tree in the abandoned church in Spain.", 124, "abandoned church just as night was falling. The sycamore was still there", {"part": "Epilogue"}),
]

# Build verified questions
verified = []
for spec in raw_specs:
    qid, split, qtype, q, a, page, anchor, fdict = spec
    txt = page_text.get(page, "")
    
    # Locate anchor in page text
    idx = txt.lower().find(anchor.lower())
    if idx == -1:
        # fallback search
        words = anchor.split()[:3]
        short_anchor = " ".join(words)
        idx = txt.lower().find(short_anchor.lower())
    
    if idx != -1:
        start = max(0, idx - 40)
        end = min(len(txt), idx + len(anchor) + 80)
        snippet = " ".join(txt[start:end].split())
    else:
        snippet = anchor

    verified.append({
        "id": qid,
        "split": split,
        "type": qtype,
        "question": q,
        "expected_answer": a,
        "gold_source_id": "the-alchemist",
        "gold_page": page,
        "evidence_quote": snippet,
        "filter": fdict
    })

os.makedirs("benchmark", exist_ok=True)
out_path = "benchmark/candidate_questions_50.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(verified, f, indent=2, ensure_ascii=False)

dev_cnt = sum(1 for q in verified if q["split"] == "dev")
test_cnt = sum(1 for q in verified if q["split"] == "test")
filter_cnt = sum(1 for q in verified if q["filter"] is not None)
print(f"Generated {len(verified)} questions: {dev_cnt} dev, {test_cnt} test, {filter_cnt} with metadata filter.")
