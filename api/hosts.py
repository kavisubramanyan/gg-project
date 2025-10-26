import json
import re
from collections import Counter
from typing import Dict, Iterable, List
from utils.typesys import clean_person_candidate
from utils.extraction import is_english

HOST_KEYWORDS = [
    "host",
    "hosting",
    "hosts",
    "hosted",
    "emcee",
    "mc",
    "monologue",
    "opening monologue",
]

HOST_RE = re.compile(r"\\b(?:host|hosts|hosting|hosted|emcee|mc|monologue)\\b", re.IGNORECASE)

import sys

def get_nlp():
    main_module = sys.modules.get('__main__')
    return main_module._spacy_nlp


def compute_hosts(tweets: Iterable[dict]) -> List[str]:
    person_counts: Counter = Counter()

    for tw in tweets:
        raw = tw.get("text", "")
        if not raw:
            continue
        if not is_english(raw):
            continue
        ltext = raw.lower()
        if "host" not in ltext:
            continue
        if "next year" in ltext:
            continue

        added = False
        nlp = get_nlp()
        if nlp is not None:
            try:
                doc = nlp(raw)
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        name = clean_person_candidate(ent.text)
                        if name:
                            person_counts[name] += 1
                            added = True
            except Exception:
                pass

        if not added:
            for m in re.finditer(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})\b", raw):
                name = clean_person_candidate(m.group(1))
                if name:
                    person_counts[name] += 1

    if not person_counts:
        return []

    return [name for name, _ in person_counts.most_common(2)]


def compute_hosts_from_file(tweets_path: str) -> List[str]:
    with open(tweets_path, "r") as f:
        data = json.load(f)
    return compute_hosts(data)


__all__ = [
    "compute_hosts",
    "compute_hosts_from_file",
]


