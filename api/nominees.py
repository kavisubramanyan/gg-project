from typing import Dict, List
import json
from collections import Counter, defaultdict

from utils.aggregation import compute_nominees as _compute_nominees
from utils.extraction import extract_nominee_counts


def compute_nominees(tweets: List[dict]) -> Dict[str, List[str]]:
    return _compute_nominees(tweets)


def compute_nominees_from_file(tweets_path: str) -> Dict[str, List[str]]:
    with open(tweets_path, "r") as f:
        data = json.load(f)
    return _compute_nominees(data)


__all__ = [
    "compute_nominees",
    "compute_nominees_from_file",
]


