import json
from collections import Counter
from typing import List

from utils.frame import normalize_text, entity_labels
from constants import WINNER_VERBS
from utils.extraction import is_english


def order(tokens: List[str]) -> List[str]:
    out = []
    i = 0
    while i < len(tokens):
        if i + 2 < len(tokens) and tokens[i+1] == 'or' and tokens[i].isalpha() and tokens[i+2].isalpha():
            w1, w2 = tokens[i], tokens[i+2]
            a, b = sorted([w1, w2])
            out.extend([a, 'or', b])
            i += 3
        else:
            out.append(tokens[i])
            i += 1
    return out


def trim(tokens: List[str]) -> List[str]:
    t = tokens[:]
    changed = True
    while changed and len(t) >= 3:
        changed = False
        for k in range(min(4, len(t)), 0, -1):
            tail = " ".join(t[-k:])
            labels = entity_labels(tail)
            if 'PERSON' in labels or 'WORK_OF_ART' in labels:
                t = t[:-k]
                if t and t[-1] in {'by', 'for'}:
                    t = t[:-1]
                changed = True
                break
    return t


def get_best_phrases(norm_text: str, max_len: int = 12) -> List[str]:
    phrases: List[str] = []
    if not norm_text:
        return phrases
    tokens = norm_text.split()
    if not tokens:
        return phrases

    boundary_words = set()
    for w in WINNER_VERBS:
        for part in w.split():
            boundary_words.add(part)

    n = len(tokens)
    i = 0
    while i < n:
        if tokens[i] != "best":
            i += 1
            continue
        j = i + 1
        taken = ["best"]
        while j < n and len(taken) < max_len:
            t = tokens[j]
            if t == "best":
                break
            if t in boundary_words:
                break
            if t.startswith('#'):
                break
            taken.append(t)
            j += 1

        if len(taken) >= 3:
            taken = order(taken)
            taken = trim(taken)
            if len(taken) >= 3:
                phrase = " ".join(taken).strip()
                phrases.append(phrase)

        i = j

    return phrases


def compute_awards(tweets: List[dict], k: int = 26) -> List[str]:

    counts = Counter()

    for tw in tweets:
        raw = tw.get("text", "")
        if not raw:
            continue
        if not is_english(raw):
            continue
        norm = normalize_text(raw)
        if not norm or "best" not in norm:
            continue

        phrases = get_best_phrases(norm)
        for p in phrases:
            counts[p] += 1

    if not counts:
        return []

    ranked = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    results: List[str] = []
    seen = set()
    for phrase, _ in ranked:
        key = phrase.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        results.append(key)
        if len(results) >= k:
            break

    return results


def compute_awards_from_file(tweets_path: str, k: int = 26) -> List[str]:
    with open(tweets_path, "r") as f:
        tweets = json.load(f)
    return compute_awards(tweets, k=k)


__all__ = [
    "compute_awards",
    "compute_awards_from_file",
]


