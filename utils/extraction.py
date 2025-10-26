import json
import re
from collections import Counter, defaultdict
from typing import Dict, Iterable, List

from .frame import (
    WINNER_PAT,
    normalize_text,
    titleish_spans,
    extract_hashtags,
    normalize_hashtag_token,
    normalize_title,
    match_award,
    coarse_match_award,
    entity_labels,
)
from .typesys import expected_labels_for_award
from constants import AWARD_NAMES, BAD_TOKENS, PERSON_BAN, GEN_NOISE


class TweetExtractor:
    @staticmethod
    def is_english(text: str) -> bool:
        if not text:
            return False
        ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(1, len(text))
        return ascii_ratio > 0.9 and (" " in text)


    @staticmethod
    def candidate_spans(raw_text: str, norm_text: str) -> List[str]:
        spans: List[str] = []
        spans.extend(titleish_spans(raw_text))
        for ht in extract_hashtags(norm_text):
            spans.append(normalize_hashtag_token(ht))
        toks = norm_text.split()
        joined = " ".join(toks)
        for m in WINNER_PAT.finditer(joined):
            char_idx = m.start()
            prefix = joined[:char_idx]
            i = len(prefix.split())
            left = max(0, i - 6)
            right = min(len(toks), i + 7)
            window = " ".join(toks[left:right])
            spans.append(window)
        dedup: List[str] = []
        seen = set()
        for s in spans:
            key = normalize_text(s)
            if key and key not in seen:
                seen.add(key)
                dedup.append(s.strip())
        return dedup


    @staticmethod
    def is_noise_candidate(span: str) -> bool:
        l = span.lower()
        noise = [
            "golden globes", "golden globe", "red carpet", "best dressed", "after party", "commercial",
            "rt", "live", "episode", "season", "trailer", "premiere"
        ]
        if any(n in l for n in noise):
            return True
        if len(l) < 3:
            return True
        return False


    BAD_TOKENS = BAD_TOKENS
    PERSON_BAN = PERSON_BAN
    GEN_NOISE = GEN_NOISE


    @staticmethod
    def clean_span_for_award(award: str, span: str) -> str:
        s = span.strip().strip('"').strip()
        s = s.replace("\u2019", "'")
        if s.endswith("'s"):
            s = s[:-2].strip()
        tokens = [t for t in s.split() if t.lower() not in BAD_TOKENS]
        if not tokens:
            return ""
        s = " ".join(tokens)
        if any(w in s.lower() for w in GEN_NOISE):
            return ""
        labels = entity_labels(s)
        expect = expected_labels_for_award(award)
        if "PERSON" in expect or (expect and expect == ["PERSON"]):
            toks = [t for t in s.split() if t.lower() not in PERSON_BAN]
            s = " ".join(toks)
            toks = s.split()
            if len(toks) < 2 or len(toks) > 4:
                return ""
            s = " ".join(t.capitalize() for t in toks)
        else:
            toks = s.split()
            if toks and toks[0].lower() in {"the", "a", "an"}:
                toks = toks[1:]
            if len(toks) == 0 or len(toks) > 6:
                return ""
            s = " ".join(w.capitalize() if len(w) > 2 else w for w in toks)
        return s.strip()


    @staticmethod
    def extract_winner_counts(tweets: Iterable[dict]) -> Dict[str, Counter]:
        award_to_counts: Dict[str, Counter] = {a: Counter() for a in AWARD_NAMES}
        for tw in tweets:
            raw = tw.get("text", "")
            if not raw:
                continue
            if not TweetExtractor.is_english(raw):
                continue
            norm = normalize_text(raw)
            if not WINNER_PAT.search(norm):
                continue
            award = match_award(norm) or coarse_match_award(norm)
            if not award:
                continue
            spans = TweetExtractor.candidate_spans(raw, norm)
            expect = expected_labels_for_award(award)
            matched_any = False
            for s in spans:
                if TweetExtractor.is_noise_candidate(s):
                    continue
                cleaned = TweetExtractor.clean_span_for_award(award, s)
                if not cleaned:
                    continue
                key = normalize_text(cleaned)
                if not key:
                    continue
                if any(w in key for w in ["best", "award", "golden", "globe", "wins", "winner", "goes to", "takes", "accepted", "accepts", "won", "takes home"]):
                    continue
                labels = entity_labels(cleaned)
                if expect:
                    if any(lbl in labels for lbl in expect):
                        weight = 3
                        matched_any = True
                        if 'WORK_OF_ART' in labels:
                            fixed = normalize_title(cleaned)
                            if fixed:
                                key = normalize_text(fixed)
                        award_to_counts[award][key] += weight
                else:
                    award_to_counts[award][key] += 1
            if expect and not matched_any:
                for s in spans:
                    if TweetExtractor.is_noise_candidate(s):
                        continue
                    cleaned = TweetExtractor.clean_span_for_award(award, s)
                    if not cleaned:
                        continue
                    key = normalize_text(cleaned)
                    if not key:
                        continue
                    if any(w in key for w in ["best", "award", "golden", "globe", "wins", "winner", "goes to", "takes", "accepted", "accepts", "won", "takes home"]):
                        continue
                    award_to_counts[award][key] += 1
        return award_to_counts

    @staticmethod
    def extract_nominee_counts(tweets: Iterable[dict]) -> Dict[str, Counter]:
        award_to_counts = defaultdict(Counter)
        for tweet in tweets:
            if not TweetExtractor.is_english(tweet.get("text", "")):
                continue
            raw = tweet["text"]
            norm = normalize_text(raw)
            if not norm:
                continue
            if WINNER_PAT.search(norm):
                continue
            award = match_award(norm) or coarse_match_award(norm)
            if not award:
                continue
            spans = TweetExtractor.candidate_spans(raw, norm)
            expect = expected_labels_for_award(award)
            for s in spans:
                if TweetExtractor.is_noise_candidate(s):
                    continue
                cleaned = TweetExtractor.clean_span_for_award(award, s)
                if not cleaned:
                    continue
                key = normalize_text(cleaned)
                if not key:
                    continue
                if any(w in key for w in ["best", "award", "golden", "globe", "wins", "winner", "goes to", "takes", "accepted", "accepts", "won", "takes home"]):
                    continue
                labels = entity_labels(cleaned)
                if expect:
                    if any(lbl in labels for lbl in expect):
                        weight = 2
                        if 'WORK_OF_ART' in labels:
                            fixed = normalize_title(cleaned)
                            if fixed:
                                key = normalize_text(fixed)
                        award_to_counts[award][key] += weight
                else:
                    award_to_counts[award][key] += 1
        return award_to_counts

    @staticmethod
    def load_tweets(path: str) -> List[dict]:
        with open(path, "r") as f:
            return json.load(f)


def is_english(text: str) -> bool:
    return TweetExtractor.is_english(text)


def candidate_spans(raw_text: str, norm_text: str) -> List[str]:
    return TweetExtractor.candidate_spans(raw_text, norm_text)


def is_noise_candidate(span: str) -> bool:
    return TweetExtractor.is_noise_candidate(span)


def clean_span_for_award(award: str, span: str) -> str:
    return TweetExtractor.clean_span_for_award(award, span)


def extract_winner_counts(tweets: Iterable[dict]) -> Dict[str, Counter]:
    return TweetExtractor.extract_winner_counts(tweets)


def load_tweets(path: str) -> List[dict]:
    return TweetExtractor.load_tweets(path)


def extract_nominee_counts(tweets: Iterable[dict]) -> Dict[str, Counter]:
    return TweetExtractor.extract_nominee_counts(tweets)


