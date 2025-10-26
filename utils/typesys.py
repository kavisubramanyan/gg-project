from .frame import entity_labels
from typing import List


def expected_labels_for_award(award_name: str) -> List[str]:
    a = award_name.lower()
    if "actor" in a or "actress" in a or "demille" in a:
        return ["PERSON"]
    if "television series" in a or "series" in a:
        return ["WORK_OF_ART", "ORG", "EVENT"]
    if "motion picture" in a or "film" in a or "song" in a or "score" in a:
        return ["WORK_OF_ART"]
    return []


def clean_person_candidate(name: str) -> str:
    tokens = name.split()
    if len(tokens) < 2 or len(tokens) > 4:
        return ""
    return " ".join(t.capitalize() for t in tokens)


def clean_work_candidate(title: str) -> str:
    tokens = title.split()
    if tokens and tokens[0].lower() in {"the", "a", "an"}:
        tokens = tokens[1:]
    if len(tokens) == 0 or len(tokens) > 6:
        return ""
    return " ".join(w.capitalize() if len(w) > 2 else w for w in tokens)


def award_expects_person(award_name: str) -> bool:
    return "PERSON" in expected_labels_for_award(award_name)


class TypeSystem:
    @staticmethod
    def expected_labels_for_award(award_name: str) -> List[str]:
        return expected_labels_for_award(award_name)

    @staticmethod
    def award_expects_person(award_name: str) -> bool:
        return award_expects_person(award_name)

    @staticmethod
    def clean_person_candidate(name: str) -> str:
        return clean_person_candidate(name)

    @staticmethod
    def clean_work_candidate(title: str) -> str:
        return clean_work_candidate(title)

    @staticmethod
    def candidate_is_valid_for_award(award_name: str, candidate_text: str) -> bool:
        labels = entity_labels(candidate_text)
        expects = expected_labels_for_award(award_name)
        return not expects or any(lbl in labels for lbl in expects)


__all__ = [
    "expected_labels_for_award",
    "clean_person_candidate",
    "clean_work_candidate",
    "award_expects_person",
    "candidate_is_valid_for_award",
]


