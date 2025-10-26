from typing import Dict

# Simple alias canonicalization for popular entities; extend as needed.
ALIAS_MAP: Dict[str, str] = {
    "JLo": "Jennifer Lopez",
    "J.Lo": "Jennifer Lopez",
    "J-LO": "Jennifer Lopez",
    "J LO": "Jennifer Lopez",
    "Leo DiCaprio": "Leonardo DiCaprio",
    "Leondardo DiCaprio": "Leonardo DiCaprio",
    "DiCaprio": "Leonardo DiCaprio",
    "Sofia Vergara": "Sofía Vergara",  # preserve accent optional
    "Hugh Jackman": "Hugh Jackman",
    "Anne Hathaway": "Anne Hathaway",
    "Kerry Washington": "Kerry Washington",
    "Ben Affleck": "Ben Affleck",
    "George Clooney": "George Clooney",
    "Nicole Kidman": "Nicole Kidman",
    "Helen Mirren": "Helen Mirren",
    "Jennifer Lawrence": "Jennifer Lawrence",
    "Adele": "Adele",
}

def canonicalize(name: str) -> str:
    return ALIAS_MAP.get(name, name)
