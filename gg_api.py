"""
Autograder API — reads standardized JSON outputs.
Do NOT modify function names or docstrings. Only fill in the logic as needed.
"""

from __future__ import annotations
import json, os
from functools import lru_cache
from typing import Dict, List, Any

DEFAULT_OUT_DIR = os.environ.get("GG_OUT_DIR", "output")

@lru_cache(maxsize=None)
def _load_results(year: int) -> Dict[str, Any]:
    # Allow override via env var GG_RESULTS_JSON to point to any single file
    override = os.environ.get("GG_RESULTS_JSON")
    if override and os.path.isfile(override):
        with open(override, "r", encoding="utf-8") as f:
            return json.load(f)

    # Otherwise, default to output/results_<year>.json
    fp = os.path.join(DEFAULT_OUT_DIR, f"results_{year}.json")
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)

def get_hosts(year: int) -> str:
    """
    Return the host as a string.
    """
    data = _load_results(year)
    return data.get("host", "")

def get_awards(year: int) -> List[str]:
    """
    Return the list of extracted award names (not the hard-coded list).
    """
    data = _load_results(year)
    return data.get("awards", [])

def get_nominees(year: int) -> Dict[str, List[str]]:
    """
    Return a mapping: hard-coded award name -> list of nominees.
    """
    data = _load_results(year)
    result = {}
    for award in data.get("hard_coded_awards", []):
        block = data.get(award, {})
        result[award] = block.get("nominees", [])
    return result

def get_winner(year: int) -> Dict[str, str]:
    """
    Return a mapping: hard-coded award name -> winner string.
    """
    data = _load_results(year)
    result = {}
    for award in data.get("hard_coded_awards", []):
        block = data.get(award, {})
        result[award] = block.get("winner", "")
    return result

def get_presenters(year: int) -> Dict[str, List[str]]:
    """
    Return a mapping: hard-coded award name -> list of presenters.
    """
    data = _load_results(year)
    result = {}
    for award in data.get("hard_coded_awards", []):
        block = data.get(award, {})
        result[award] = block.get("presenters", [])
    return result
