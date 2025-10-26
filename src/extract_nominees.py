from typing import Dict, List
import re
from nlp_regex import extract_capitalized_names, pick_top_counts, normalize_names
from utils.preprocess import preprocess_tweet

NOM_TRIG = re.compile(r"\b(nominee[s]?|nominated|nominations?)\b", re.IGNORECASE)

def _mentions_award(text: str, award: str) -> bool:
    return award.lower() in text.lower()

def extract_nominees_by_award(tweets: List[dict], awards: List[str]) -> Dict[str, List[str]]:
    out = {}
    for a in awards:
        nom_exact = []
        nom_candidates_all = []
        for tw in tweets:
            txt = preprocess_tweet(tw).get("text", "")
            if not _mentions_award(txt, a):
                continue
            if NOM_TRIG.search(txt):
                names = extract_capitalized_names(txt)
                nom_exact.extend(normalize_names(names))
            nom_candidates_all.extend(normalize_names(extract_capitalized_names(txt)))
        out[a] = pick_top_counts(nom_exact, k=5)
        out[a + "_candidates"] = pick_top_counts(nom_candidates_all, k=12)
    return out
