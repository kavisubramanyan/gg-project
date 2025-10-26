import re
from typing import Dict, List, Optional, Set, Tuple

from ftfy import fix_text
from unidecode import unidecode

from constants import WINNER_VERBS, AWARD_NAMES, URL_PATTERN, USER_PATTERN, MULTISPACE_PATTERN, HASHTAG_PATTERN, QUOTED_SPAN_PATTERN, PERSON_LIKE_PATTERN, AWARD_ALIASES

URL_RE = re.compile(URL_PATTERN, re.IGNORECASE)
USER_RE = re.compile(USER_PATTERN, re.IGNORECASE)
MULTISPACE_RE = re.compile(MULTISPACE_PATTERN, re.MULTILINE)


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    fixed = fix_text(str(text))
    ascii_text = unidecode(fixed)
    no_urls = URL_RE.sub(" ", ascii_text)
    no_users = USER_RE.sub(" ", no_urls)
    lowered = no_users.lower()
    cleaned = re.sub(r"[^a-z0-9#'\s]", " ", lowered)
    cleaned = re.sub(r"(\w)\1{2,}", r"\1\1", cleaned)
    return MULTISPACE_RE.sub(" ", cleaned).strip()


def extract_hashtags(text: str) -> List[str]:
    return [ht[1:] for ht in re.findall(HASHTAG_PATTERN, text or "")]


def titleish_spans(raw_text: str) -> List[str]:
    if not raw_text:
        return []
    spans: List[str] = []
    for m in re.finditer(QUOTED_SPAN_PATTERN, raw_text):
        spans.append(m.group(1).strip())
    tokens = raw_text.split()
    buf: List[str] = []
    for tok in tokens:
        if tok[:1].isupper() and re.search(r"[A-Za-z]", tok):
            buf.append(tok.strip(".,!?:;"))
        else:
            if len(buf) >= 2:
                spans.append(" ".join(buf))
            buf = []
    if len(buf) >= 2:
        spans.append(" ".join(buf))
    seen = set()
    uniq: List[str] = []
    for s in spans:
        key = s.lower().strip()
        if key and key not in seen:
            uniq.append(s.strip())
            seen.add(key)
    return uniq


def normalize_hashtag_token(token: str) -> str:
    if not token:
        return ""
    t = token.strip("#")
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", t)
    if parts:
        return " ".join(parts)
    return t


try:
    from imdb import IMDb
except Exception:
    IMDb = None 

_ia = None


def _get_ia():
    global _ia
    if _ia is None and IMDb is not None:
        try:
            _ia = IMDb()
        except Exception:
            _ia = None
    return _ia


def normalize_title(title: str) -> Optional[str]:
    ia = _get_ia()
    if ia is None or not title:
        return None
    try:
        results = ia.search_movie(title)
        if results:
            best = results[0]
            name = best.get('title') or best.get('long imdb title')
            if name:
                return str(name)
    except Exception:
        return None
    return None

WINNER_PAT = re.compile(r"(" + r"|".join([re.escape(w) for w in WINNER_VERBS]) + r")", re.IGNORECASE)


__all__ = [
    "normalize_text",
    "extract_hashtags",
    "titleish_spans",
    "normalize_hashtag_token",
    "normalize_title",
    "WINNER_PAT",
]


ALIASES: Dict[str, List[str]] = AWARD_ALIASES


def build_award_patterns() -> List[Tuple[str, re.Pattern]]:
    patterns: List[Tuple[str, re.Pattern]] = []
    for canon in AWARD_NAMES:
        words = canon.split()
        flex = r"\s*[-:]*\s*".join(map(re.escape, words))
        patterns.append((canon, re.compile(flex, re.IGNORECASE)))
        for alias in ALIASES.get(canon, []):
            awords = alias.split()
            aflex = r"\s*[-:]*\s*".join(map(re.escape, awords))
            patterns.append((canon, re.compile(aflex, re.IGNORECASE)))
    return patterns


AWARD_PATTERNS = build_award_patterns()


def match_award(text: str) -> str:
    for canon, pat in AWARD_PATTERNS:
        if pat.search(text):
            return canon
    return ""


def coarse_match_award(text: str) -> str:
    t = text.lower()
    
    if "actor" in t and ("motion picture" in t or "film" in t) and "drama" in t and "support" not in t:
        if "comedy" in t or "musical" in t:
            return "best performance by an actor in a motion picture - comedy or musical"
        else:
            return "best performance by an actor in a motion picture - drama"
    if "actress" in t and ("motion picture" in t or "film" in t) and "drama" in t and "support" not in t:
        if "comedy" in t or "musical" in t:
            return "best performance by an actress in a motion picture - comedy or musical"
        else:
            return "best performance by an actress in a motion picture - drama"
    if "supporting" in t and "actor" in t and ("motion picture" in t or "film" in t):
        return "best performance by an actor in a supporting role in a motion picture"
    if "supporting" in t and "actress" in t and ("motion picture" in t or "film" in t):
        return "best performance by an actress in a supporting role in a motion picture"
    if "supporting" in t and "actor" in t and ("tv" in t or "television" in t or "series" in t):
        return "best performance by an actor in a supporting role in a series, mini-series or motion picture made for television"
    if "supporting" in t and "actress" in t and ("tv" in t or "television" in t or "series" in t):
        return "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television"
    if ("mini" in t or "miniseries" in t or "limited" in t) and "actor" in t:
        return "best performance by an actor in a mini-series or motion picture made for television"
    if ("mini" in t or "miniseries" in t or "limited" in t) and "actress" in t:
        return "best performance by an actress in a mini-series or motion picture made for television"
    if "actor" in t and ("tv" in t or "television" in t or "series" in t) and ("comedy" in t or "musical" in t):
        return "best performance by an actor in a television series - comedy or musical"
    if "actor" in t and ("tv" in t or "television" in t or "series" in t) and "drama" in t:
        return "best performance by an actor in a television series - drama"
    if "actress" in t and ("tv" in t or "television" in t or "series" in t) and ("comedy" in t or "musical" in t):
        return "best performance by an actress in a television series - comedy or musical"
    if "actress" in t and ("tv" in t or "television" in t or "series" in t) and "drama" in t:
        return "best performance by an actress in a television series - drama"
    if ("tv" in t or "television" in t or "series" in t) and ("comedy" in t or "musical" in t):
        return "best television series - comedy or musical"
    if ("tv" in t or "television" in t or "series" in t) and "drama" in t:
        return "best television series - drama"
    
    return ""

import sys

def _get_nlp():
    main_module = sys.modules.get('__main__')
    return main_module._spacy_nlp

_NLP = None

PERSON_LIKE_RE = re.compile(PERSON_LIKE_PATTERN)


def guess_person_like(text: str) -> bool:
    return bool(PERSON_LIKE_RE.match(text.strip()))


def entity_labels(text: str) -> Set[str]:
    labels: Set[str] = set()
    if not text:
        return labels
    nlp = _get_nlp()
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                labels.add(ent.label_)
            return labels
        except Exception:
            pass
    if guess_person_like(text):
        labels.add("PERSON")
    if any(w in text.lower() for w in [" of ", " the ", ":", "'s", " and "]):
        labels.add("WORK_OF_ART")
    return labels


class Normalizer:
    @staticmethod
    def normalize_text(text: str) -> str:
        if text is None:
            return ""
        fixed = fix_text(str(text))
        ascii_text = unidecode(fixed)
        no_urls = URL_RE.sub(" ", ascii_text)
        no_users = USER_RE.sub(" ", no_urls)
        lowered = no_users.lower()
        cleaned = re.sub(r"[^a-z0-9#'\s]", " ", lowered)
        cleaned = re.sub(r"(\w)\1{2,}", r"\1\1", cleaned)
        return MULTISPACE_RE.sub(" ", cleaned).strip()

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        return [ht[1:] for ht in re.findall(HASHTAG_PATTERN, text or "")]

    @staticmethod
    def titleish_spans(raw_text: str) -> List[str]:
        if not raw_text:
            return []
        spans: List[str] = []
        for m in re.finditer(QUOTED_SPAN_PATTERN, raw_text):
            spans.append(m.group(1).strip())
        tokens = raw_text.split()
        buf: List[str] = []
        for tok in tokens:
            if tok[:1].isupper() and re.search(r"[A-Za-z]", tok):
                buf.append(tok.strip(".,!?:;"))
            else:
                if len(buf) >= 2:
                    spans.append(" ".join(buf))
                buf = []
        if len(buf) >= 2:
            spans.append(" ".join(buf))
        seen = set()
        uniq: List[str] = []
        for s in spans:
            key = s.lower().strip()
            if key and key not in seen:
                uniq.append(s.strip())
                seen.add(key)
        return uniq

    @staticmethod
    def normalize_hashtag_token(token: str) -> str:
        if not token:
            return ""
        t = token.strip("#")
        parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", t)
        if parts:
            return " ".join(parts)
        return t


class ImdbClient:
    _ia = None

    @classmethod
    def _get_ia(cls):
        if cls._ia is None and IMDb is not None:
            try:
                cls._ia = IMDb()
            except Exception:
                cls._ia = None
        return cls._ia

    @classmethod
    def normalize_title(cls, title: str) -> Optional[str]:
        ia = cls._get_ia()
        if ia is None or not title:
            return None
        try:
            results = ia.search_movie(title)
            if results:
                best = results[0]
                name = best.get('title') or best.get('long imdb title')
                if name:
                    return str(name)
        except Exception:
            return None
        return None


class AwardSemantics:
    def __init__(self) -> None:
        self.patterns: List[Tuple[str, re.Pattern]] = []
        for canon in AWARD_NAMES:
            words = canon.split()
            flex = r"\s*[-:]*\s*".join(map(re.escape, words))
            self.patterns.append((canon, re.compile(flex, re.IGNORECASE)))
            for alias in ALIASES.get(canon, []):
                awords = alias.split()
                aflex = r"\s*[-:]*\s*".join(map(re.escape, awords))
                self.patterns.append((canon, re.compile(aflex, re.IGNORECASE)))

    def match_award(self, text: str) -> str:
        for canon, pat in self.patterns:
            if pat.search(text):
                return canon
        return ""

    def coarse_match_award(self, text: str) -> str:
        t = text.lower()
        if "supporting" in t and "actor" in t and ("tv" in t or "television" in t or "series" in t):
            return "best performance by an actor in a supporting role in a series, mini-series or motion picture made for television"
        if "supporting" in t and "actress" in t and ("tv" in t or "television" in t or "series" in t):
            return "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television"
        if ("mini" in t or "miniseries" in t or "limited" in t) and "actor" in t:
            return "best performance by an actor in a mini-series or motion picture made for television"
        if ("mini" in t or "miniseries" in t or "limited" in t) and "actress" in t:
            return "best performance by an actress in a mini-series or motion picture made for television"
        if ("tv" in t or "television" in t or "series" in t) and ("comedy" in t or "musical" in t):
            return "best television series - comedy or musical"
        if ("tv" in t or "television" in t or "series" in t) and "drama" in t:
            return "best television series - drama"
        return ""


class EntitySemantics:
    def __init__(self) -> None:
        self._nlp = None
        self._person_like_re = re.compile(PERSON_LIKE_PATTERN)

    def guess_person_like(self, text: str) -> bool:
        return bool(self._person_like_re.match(text.strip()))

    def entity_labels(self, text: str) -> Set[str]:
        labels: Set[str] = set()
        if not text:
            return labels
        nlp = _get_nlp()
        if nlp is not None:
            try:
                doc = nlp(text)
                for ent in doc.ents:
                    labels.add(ent.label_)
                return labels
            except Exception:
                pass
        if self.guess_person_like(text):
            labels.add("PERSON")
        if any(w in text.lower() for w in [" of ", " the ", ":", "'s", " and "]):
            labels.add("WORK_OF_ART")
        return labels


_AWARDS = AwardSemantics()
_ENTITY = EntitySemantics()

normalize_text = Normalizer.normalize_text
extract_hashtags = Normalizer.extract_hashtags
titleish_spans = Normalizer.titleish_spans
normalize_hashtag_token = Normalizer.normalize_hashtag_token
normalize_title = ImdbClient.normalize_title

def match_award(text: str) -> str:
    return _AWARDS.match_award(text)


def coarse_match_award(text: str) -> str:
    return _AWARDS.coarse_match_award(text)


def guess_person_like(text: str) -> bool:
    return _ENTITY.guess_person_like(text)


def entity_labels(text: str) -> Set[str]:
    return _ENTITY.entity_labels(text)


