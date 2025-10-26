from typing import List
import re
from nlp_regex import extract_best_award_phrases
from utils.preprocess import preprocess_tweet

def extract_awards_list(tweets: List[dict]) -> List[str]:
    """Extract award name candidates starting with 'Best ...' using regex."""
    variants = {}
    counts = {}
    for tw in tweets:
        txt = preprocess_tweet(tw).get("text", "")
        for frag in extract_best_award_phrases(txt):
            key = re.sub(r"\s+", " ", frag.strip()).lower()
            variants.setdefault(key, frag.strip())
            counts[key] = counts.get(key, 0) + 1
    keys_sorted = sorted(counts.keys(), key=lambda k: (-counts[k], k))
    return [variants[k] for k in keys_sorted]
