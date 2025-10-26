from typing import Dict, List
import re
from nlp_regex import extract_capitalized_names, pick_top_counts, normalize_names
from utils.preprocess import preprocess_tweet

PRESENT_TRIG = re.compile(r"\b(present(?:s|ed|ing)?|introduc(?:e|es|ed|ing))\b", re.IGNORECASE)

def _mentions_award(text: str, award: str) -> bool:
    return award.lower() in text.lower()

def extract_presenters_by_award(tweets: List[dict], awards: List[str]) -> Dict[str, List[str]]:
    out = {}
    for a in awards:
        cand = []
        cands_all = []
        for tw in tweets:
            txt = preprocess_tweet(tw).get("text", "")
            if not _mentions_award(txt, a):
                continue
            if PRESENT_TRIG.search(txt):
                names = extract_capitalized_names(txt)
                if names:
                    cand.extend(normalize_names(names))
            cands_all.extend(normalize_names(extract_capitalized_names(txt)))
        out[a] = pick_top_counts(cand, k=3)
        out[a + "_candidates"] = pick_top_counts(cands_all, k=8)
    return out
