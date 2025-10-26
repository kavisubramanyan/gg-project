from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
AWARDS_DIR = BASE_DIR / "data" / "hardcoded_awards"

def load_hardcoded_awards(year: int) -> List[str]:
    """Load the course-provided hard-coded awards list for a given year.

    Expected file path: data/hardcoded_awards/awards_<year>.txt
    One award per line, exact strings as provided by the course.
    Lines starting with '#' are treated as comments.

    Returns:
        List[str]: ordered list of award names.
    """
    path = AWARDS_DIR / f"awards_{year}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Missing hard-coded awards list: {path}. "
                                "Ask the TA for the official list and paste it here.")
    awards = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        awards.append(line)
    return awards
