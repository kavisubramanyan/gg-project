from typing import Dict, List, Tuple
import re
from utils.preprocess import preprocess_tweet
from nlp_regex import extract_capitalized_names, normalize_names, pick_top_counts

# Fashion/topic triggers
FASHION_TRIG = re.compile(
    r"\b(dress|gown|tux|suit|red\s*carpet|redcarpet|look|wearing|outfit|style|neckline|sequins?|plunging|backless)\b",
    re.IGNORECASE
)

# Hashtag-like tokens already normalized by preprocess: e.g., "goldenglobes", "eredcarpet", "bestdressed"
BEST_TAG = re.compile(r"\b(bestdressed|slay|stunning|flawless|gorgeous|beautiful|perfection)\b", re.IGNORECASE)
WORST_TAG = re.compile(r"\b(worstdressed|fashionmess|trainwreck|disaster|ugly|terrible|awful|hideous)\b", re.IGNORECASE)

# Simple sentiment lexicons (expandable)
POS_WORDS = {
    "amazing","stunning","flawless","gorgeous","beautiful","love","lovely","iconic","perfect",
    "perfection","obsessed","incredible","impeccable","yes","wow","killing","killing it","serve","serving",
    "slay","slayed","slew","best","favorite","favourite","hot","elegant","classy","divine"
}
NEG_WORDS = {
    "worst","ugly","ugh","yikes","awful","terrible","horrible","hideous","mess","fashionmess",
    "disaster","trash","tacky","not good","nope","fail","cringe","ew","barf","gross","why"
}

def _sentiment_score(text: str) -> int:
    score = 0
    tl = text.lower()
    for w in POS_WORDS:
        if w in tl:
            score += 1
    for w in NEG_WORDS:
        if w in tl:
            score -= 1
    if BEST_TAG.search(tl):
        score += 2
    if WORST_TAG.search(tl):
        score -= 2
    # light heuristics for negation
    if "not his color" in tl or "not her color" in tl or "not their color" in tl:
        score -= 1
    return score

def compute_best_worst_dressed(tweets: List[dict], k_candidates: int = 5) -> Dict[str, object]:
    """
    Scan tweets for fashion-related mentions, score sentiment per named entity,
    and return best/worst dressed and candidate lists.
    """
    per_name_score = {}
    per_name_count = {}

    for tw in tweets:
        t = preprocess_tweet(tw).get("text", "")
        if not t:
            continue
        if not (FASHION_TRIG.search(t) or BEST_TAG.search(t) or WORST_TAG.search(t)):
            # still include obvious #bestdressed or #worstdressed lines caught by preprocess
            pass
        names = normalize_names(extract_capitalized_names(t))
        if not names:
            continue
        s = _sentiment_score(t)
        # if explicitly says "best dressed" add extra to all names present
        if "bestdressed" in t.lower():
            s += 2
        if "worstdressed" in t.lower():
            s -= 2
        for n in names:
            per_name_score[n] = per_name_score.get(n, 0) + s
            per_name_count[n] = per_name_count.get(n, 0) + 1

    # Rank by score (ties broken by count)
    ranked = sorted(per_name_score.items(), key=lambda kv: (-kv[1], -per_name_count.get(kv[0], 0), kv[0]))
    best = ranked[0][0] if ranked else ""
    # For worst, sort ascending
    ranked_worst = sorted(per_name_score.items(), key=lambda kv: (kv[1], -per_name_count.get(kv[0], 0), kv[0]))
    worst = ranked_worst[0][0] if ranked_worst else ""

    best_cands = [n for n,_ in ranked[:k_candidates]]
    worst_cands = [n for n,_ in ranked_worst[:k_candidates]]

    return {
        "best_dressed": best,
        "best_dressed_candidates": best_cands,
        "worst_dressed": worst,
        "worst_dressed_candidates": worst_cands,
    }
