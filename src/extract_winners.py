from typing import Dict
import re
from nlp_regex import extract_capitalized_names, pick_top_counts, normalize_names
from utils.preprocess import preprocess_tweet

PAT_WIN_BEFORE = re.compile(
    r"(?P<winner>[A-Z][A-Za-z0-9\.\'\-\&\s]{1,60})\s+(?:wins|won|takes|takes home)\s+(?P<award>Best[^\n#@]{5,80})",
    re.IGNORECASE
)
PAT_WIN_AFTER = re.compile(
    r"(?P<award>Best[^\n#@]{5,80})\s+(?:goes to|is awarded to|to)\s+(?P<winner>[A-Z][A-Za-z0-9\.\'\-\&\s]{1,60})",
    re.IGNORECASE
)

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def extract_winners_by_award(tweets: List[dict], awards: List[str]) -> Dict[str, str]:
    evidence = {a: [] for a in awards}
    cand_lists = {a + "_candidates": [] for a in awards}

    for tw in tweets:
        txt = preprocess_tweet(tw).get("text", "")
        for m in PAT_WIN_BEFORE.finditer(txt):
            award = _clean(m.group("award"))
            winner = _clean(m.group("winner"))
            for a in awards:
                if a.lower() in award.lower():
                    evidence[a].append(winner)
                    cand_lists[a + "_candidates"].extend(normalize_names(extract_capitalized_names(txt)))
        for m in PAT_WIN_AFTER.finditer(txt):
            award = _clean(m.group("award"))
            winner = _clean(m.group("winner"))
            for a in awards:
                if a.lower() in award.lower():
                    evidence[a].append(winner)
                    cand_lists[a + "_candidates"].extend(normalize_names(extract_capitalized_names(txt)))

    out = {}
    for a in awards:
        top = pick_top_counts(evidence.get(a, []), k=1)
        out[a] = top[0] if top else ""
        out[a + "_candidates"] = pick_top_counts(cand_lists.get(a + "_candidates", []), k=8)
    return out
