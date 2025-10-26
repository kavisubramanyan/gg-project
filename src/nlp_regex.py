import re
from typing import List, Iterable

# Basic person/movie-like chunk: sequences of capitalized tokens, allowing internal punctuation/hyphen.
NAME_CHUNK_LOOSE = r"(?:[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z\.\-]+){0,3})"

# Common stopwords to trim from award tails
_AWARD_STOP = re.compile(r"[\s\-\:\;\|\(\)\[\]\"“”‘’]+$")

def normalize_award_fragment(s: str) -> str:
    s = s.strip()
    s = _AWARD_STOP.sub("", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s

def extract_best_award_phrases(text: str, max_len: int = 80) -> List[str]:
    """Find phrases starting with 'Best' up to punctuation/emoji/URL/hashtag boundaries."""
    pat = re.compile(r"\bBest[^\n#@]+?(?=(?:[.!?]|http[s]?://|\s#[A-Za-z0-9_]|$))", re.IGNORECASE)
    out = []
    for m in pat.finditer(text):
        frag = m.group(0).strip()
        if len(frag) <= max_len and len(frag) >= 10:
            out.append(normalize_award_fragment(frag))
    return out

def extract_capitalized_names(text: str) -> List[str]:
    """Very simple name extractor based on capitalization."""
    text = re.sub(r"(?:https?://\S+|@\w+|#\w+)", " ", text)
    chunks = re.findall(NAME_CHUNK_LOOSE, text)
    cleaned = []
    for c in chunks:
        c = c.strip()
        if len(c) < 3:
            continue
        if c.lower() in {"best", "golden globes"}:
            continue
        cleaned.append(c)
    return cleaned

def pick_top_counts(items: Iterable[str], k: int = 3) -> List[str]:
    from collections import Counter
    c = Counter([i.strip() for i in items if i and i.strip()])
    return [x for x,_ in c.most_common(k)]


def normalize_names(names):
    try:
        from utils.aliases import canonicalize
    except Exception:
        def canonicalize(x):
            return x
    out = []
    for n in names:
        out.append(canonicalize(n))
    return out
