from typing import List, Tuple
import re
from nlp_regex import extract_capitalized_names, pick_top_counts, normalize_names
from utils.preprocess import preprocess_tweet

HOST_TRIG = re.compile(r"\b(host|hosts|hosting|your hosts?)\b", re.IGNORECASE)

def extract_host_and_candidates(tweets: List[dict]) -> Tuple[str, list]:
    """Look for 'host/hosting/your hosts' contexts and collect nearby names."""
    candidates = []
    global_names = []
    for tw in tweets:
        txt = preprocess_tweet(tw).get("text", "")
        names = extract_capitalized_names(txt)
        global_names.extend(names)
        if HOST_TRIG.search(txt):
            candidates.extend(names)
    if not candidates:
        top = pick_top_counts(global_names, k=3)
        return (top[0] if top else ""), top
    top = pick_top_counts(candidates, k=5)
    return (top[0] if top else ""), top
