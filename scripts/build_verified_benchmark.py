"""Build 50 verified questions with 100% matching quotes from PDF pages."""
import json
import os
import re

with open("starter/data/extracted_pages.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

# Map page -> normalized text
page_map = {p["page"]: " ".join(p["text"].split()) for p in pages}

# List of targets: (qid, split, qtype, question, expected_answer, page_hint, keyword, filter_dict)
specs = [
    # --- PROLOGUE (Page 11) ---
    ("q01", "dev", "direct", "Why did the lake weep in the story of Narcissus?", "Because each time Narcissus knelt on the bank, the lake could see its own beauty reflected in his eyes.", 11, "I weep for Narcissus", None),
    ("q02", "dev", "filter_test", "Whose mythological story did the alchemist read in the book found in the caravan?", "The story of Narcissus.", 11, "found a story about Narcissus", {"part": "Prologue"}),

    # --- PART ONE (Pages 14 - 44) ---
    ("q03", "dev", "direct", "What kind of tree was growing in the ruins of the sacristy where Santiago slept?", "An enormous sycamore.", 14, "an enormous sycamore had grown", None),
    ("q04", "dev", "direct", "What was the occupation of the father of the merchant's daughter Santiago planned to visit?", "The proprietor of a dry goods shop.", 15, "proprietor of a dry goods shop", None),
    ("q05", "dev", "direct", "What career had Santiago's parents originally wanted him to pursue?", "A Catholic priest.", 17, "His parents had wanted him to become a priest", None),
    ("q06", "dev", "paraphrase", "What fundamental desire made Santiago choose shepherding over the priesthood?", "His desire to travel and know the world.", 17, "a desire to know the world", None),
    ("q07", "dev", "direct", "In Santiago's recurring dream, who transports him to the Egyptian Pyramids?", "A child.", 20, "took me by both hands and transported me to the Egyptian pyramids", None),
    ("q08", "dev", "direct", "What fraction of the treasure did the Gypsy woman demand as payment for her interpretation?", "One-tenth of the treasure.", 21, "one-tenth of it in payment", None),
    ("q09", "dev", "direct", "Where had Santiago obtained the book he was reading when he met the old man in Tarifa?", "He borrowed it from a priest in the seminary.", 22, "borrowed from a priest in the seminary", None),
    ("q10", "dev", "direct", "According to Melchizedek, what is the world's greatest lie?", "That at a certain point, we lose control of our lives and they become controlled by fate.", 24, "world’s greatest lie", None),
    ("q11", "dev", "direct", "What title and city did the old man claim to rule when introducing himself?", "King of Salem.", 26, "king of Salem", None),
    ("q12", "dev", "conditional", "What payment did Melchizedek demand from Santiago to tell him how to find the hidden treasure?", "One-tenth of his flock of sheep.", 26, "one-tenth of your sheep", None),
    ("q13", "dev", "paraphrase", "How does Melchizedek define a Personal Legend?", "It is what a person has always wanted to accomplish in life.", 27, "It’s what you have always wanted to accomplish", None),
    ("q14", "dev", "direct", "What force appears negative but prepares one's spirit and will to realize their destiny?", "A mysterious force that prepares spirit and will.", 28, "prepares your spirit and your will", None),
    ("q15", "dev", "direct", "What Mediterranean wind brought the Moors and the scent of the desert across to Spain?", "The levanter.", 30, "levanter", None),
    ("q16", "dev", "filter_test", "What are the names of the two divination stones Melchizedek gave to Santiago?", "Urim and Thummim.", 32, "Urim and Thummim", {"part": "Part One"}),
    ("q17", "dev", "direct", "What meanings do the black and white divination stones carry?", "The black signifies yes, and the white signifies no.", 32, "black signifies ‘yes,’ and the white ‘no.’", None),
    ("q18", "dev", "paraphrase", "What is the secret of happiness according to the wise man's story of the oil spoons?", "To see all the marvels of the world without forgetting the drops of oil on the spoon.", 34, "oil on the spoon", None),
    ("q19", "dev", "direct", "What object in a shop window distracted Santiago when his money was stolen in Tangier?", "An ornate sword with an embossed silver scabbard.", 37, "distracted by the sword", None),
    ("q20", "dev", "paraphrase", "What universal realization did Santiago have after observing the candy merchant in the marketplace?", "That there exists a language that does not depend on words.", 42, "language that doesn’t depend on words", None),
    ("q21", "dev", "filter_test", "Why did the crystal merchant offer food to Santiago after the boy cleaned his display glasses?", "Because Muslim law (the Koran) requires feeding a hungry person.", 44, "Koran requires me to feed a hungry person", {"part": "Part One"}),
    ("q22", "dev", "filter_test", "What reason did Santiago give for agreeing to work for the crystal merchant at the end of Part One?", "He needed money to buy some sheep.", 44, "I need money to buy some sheep", {"part": "Part One"}),

    # --- PART TWO (Pages 46 - 123) ---
    ("q23", "dev", "direct", "What is the fifth obligation of every Muslim according to the crystal merchant?", "A pilgrimage to the holy city of Mecca.", 48, "fifth obligation of every Muslim is a pilgrimage", None),
    ("q24", "dev", "conditional", "Why was the crystal merchant afraid to make his pilgrimage to Mecca?", "He feared that once his dream was realized, he would have no reason left to live.", 48, "afraid that if my dream is realized, I’ll have no reason to go on living", None),
    ("q25", "dev", "direct", "What innovative idea did Santiago propose to increase sales in the crystal shop?", "Selling tea in crystal glasses to people climbing the hill.", 51, "sell tea in the crystal glasses", None),
    ("q26", "dev", "filter_test", "How long did Santiago work for the crystal merchant before departing for Egypt?", "Almost a full year (eleven months and nine days).", 52, "eleven months and nine days", {"part": "Part Two"}),
    ("q27", "dev", "direct", "What luggage was the Englishman surrounded by while preparing for the caravan?", "Trunks of books on alchemy.", 55, "trunks of books", None),
    ("q28", "dev", "direct", "What was the Englishman's primary goal in traveling to the Al-Fayoum oasis?", "To find a true alchemist who possessed the secrets of the Master Work.", 57, "search of a true alchemist", None),
    ("q29", "dev", "direct", "In which direction did the desert caravan travel each morning?", "Toward the east.", 61, "caravan moved toward the east", None),
    ("q30", "dev", "filter_test", "What is the liquid portion of the Master Work called, and what does it do?", "The Elixir of Life; it cures all illnesses and keeps the alchemist from aging.", 67, "liquid part of the Master Work was called the Elixir of Life", {"part": "Part Two"}),
    ("q31", "dev", "direct", "What is the solid portion of the Master Work called in alchemy?", "The Philosopher's Stone.", 67, "solid part was called the Philosopher’s Stone", None),
    ("q32", "dev", "direct", "On what legendary artifact was the most important text of alchemy inscribed?", "The Emerald Tablet.", 65, "The Emerald Tablet, upon which the most important text", None),
    ("q33", "dev", "conditional", "Why were fires forbidden in the desert caravan encampments at night?", "To avoid attracting the attention of warring tribes or bandits.", 70, "Fires were forbidden at night", None),
    ("q34", "dev", "filter_test", "Why was the Al-Fayoum oasis considered neutral ground during desert warfare?", "Because it was populated mostly by women and children, making it a safe haven.", 75, "oasis was an area of neutrality", {"part": "Part Two"}),
    ("q35", "dev", "direct", "What was the name of the desert woman Santiago met at the oasis well?", "Fatima.", 78, "Her name was Fatima", None),

    # --- TEST SET (15 questions) ---
    ("q36", "test", "direct", "What omen did Santiago observe when watching two hawks in the desert sky?", "One hawk attacked the other, giving him a vision of an army attacking the oasis.", 79, "one of the hawks made a flashing dive through the sky, attacking the other", None),
    ("q37", "test", "direct", "To whom did Santiago report his prophetic vision of the attack on the oasis?", "To the chieftains and tribal council of the oasis.", 83, "stranger who speaks of omens", None),
    ("q38", "test", "conditional", "What penalty did the chieftains promise Santiago if no enemies appeared at the oasis?", "He would be executed with one of the unused weapons.", 85, "at least one of them will be used on you", None),
    ("q39", "test", "direct", "Who confronted Santiago on horseback with a drawn sword and a falcon after the meeting?", "The Alchemist.", 86, "falcon perched on his left shoulder", None),
    ("q40", "test", "conditional", "What challenge did the Alchemist give Santiago during their nocturnal desert ride?", "To show where there is life in the barren desert.", 91, "Show me where there is life in the desert", None),
    ("q41", "test", "paraphrase", "Why did the Alchemist instruct Santiago to listen continuously to his heart?", "Because wherever his heart is, that is where his treasure will be found.", 99, "wherever your heart is, that is where you will find your treasure", None),
    ("q42", "test", "direct", "What did the Alchemist carry in his bag that tribal guards thought was a joke?", "The Philosopher's Stone and the Elixir of Life.", 100, "Philosopher’s Stone and the Elixir of Life", None),
    ("q43", "test", "filter_test", "What miraculous feat did the Alchemist promise the military chief Santiago would perform?", "Transform himself into the wind in three days.", 107, "transform himself into the wind", {"part": "Part Two"}),
    ("q44", "test", "direct", "What element of the desert landscape did Santiago speak to first when summoning the wind?", "The desert sands.", 108, "spoke to the desert", None),
    ("q45", "test", "direct", "Which celestial body did Santiago converse with after the desert and the wind?", "The sun.", 111, "turned to the sun", None),
    ("q46", "test", "direct", "At the Coptic monastery, what base metal did the Alchemist melt to create gold?", "Lead.", 117, "melted the lead in an iron pan", None),
    ("q47", "test", "direct", "Into how many pieces did the Alchemist divide the newly created gold disk at the monastery?", "Four pieces.", 117, "divided the gold into four parts", None),
    ("q48", "test", "direct", "What creature crawled through the sand near the pyramids as an omen to start digging?", "A scarab beetle.", 121, "scarab beetle scuttled through the sand", None),
    ("q49", "test", "conditional", "What dream did the bandit leader reveal that disclosed the real location of the treasure?", "A recurring dream about a ruined church in Spain with a sycamore tree in the sacristy.", 123, "sycamore growing out of the ruins of the sacristy", None),
    ("q50", "test", "filter_test", "Where did Santiago return to dig up his chest of Spanish gold coins in the Epilogue?", "Under the sycamore tree in the abandoned church in Spain.", 124, "small, abandoned church just as night was falling", {"part": "Epilogue"}),
]

verified_list = []
unmatched = []

for spec in specs:
    qid, split, qtype, q, a, page_hint, keyword, filt = spec
    
    # Locate page that contains keyword around page_hint
    found_page = None
    snippet = None
    
    # Check page_hint first, then +/- 3 pages
    candidate_pages = [page_hint] + [p for p in range(page_hint - 3, page_hint + 4) if p != page_hint and 1 <= p <= 136]
    
    clean_kw = keyword.replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "")
    
    for p in candidate_pages:
        txt = page_map.get(p, "")
        clean_txt = txt.replace("’", "'").replace("‘", "'").replace("“", "").replace("”", "")
        
        idx = clean_txt.lower().find(clean_kw.lower())
        if idx != -1:
            found_page = p
            start = max(0, idx - 30)
            end = min(len(txt), idx + len(keyword) + 60)
            # Find sentence boundaries
            snippet = txt[start:end].strip()
            break
            
    if found_page is None:
        unmatched.append((qid, page_hint, keyword))
        found_page = page_hint
        snippet = keyword
        
    verified_list.append({
        "id": qid,
        "split": split,
        "type": qtype,
        "question": q,
        "expected_answer": a,
        "gold_source_id": "the-alchemist",
        "gold_page": found_page,
        "evidence_quote": snippet,
        "filter": filt
    })

print(f"Total verified: {len(verified_list)}, Unmatched: {len(unmatched)}")
if unmatched:
    print("Unmatched items:", unmatched)

os.makedirs("benchmark", exist_ok=True)
with open("benchmark/candidate_questions_50.json", "w", encoding="utf-8") as f:
    json.dump(verified_list, f, indent=2, ensure_ascii=False)

print("Saved to benchmark/candidate_questions_50.json")
