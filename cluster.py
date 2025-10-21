# clustering.py
# Python 3.10+
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Iterable
import re
import unicodedata
from difflib import SequenceMatcher
from collections import defaultdict

# ---------- Roles we support ----------
DEFAULT_ROLE_KEYS = {"winner", "nominee", "presenter", "host"}

# Words we strip if they’re obvious noise around entities
NOISE_TOKENS = {
    "rt", "golden", "globes", "globesphilly", "redcarpet", "red", "carpet",
    "bestdressed", "stylechat", "scriptchat", "eredcarpet", "e", "page",
    "wins", "won", "winner", "nominee", "nominated", "present",
    "presented", "presenting", "host", "hosts", "hosted"
}

# ---------- Data structures ----------
@dataclass
class Evidence:
    text: Optional[str] = None
    confidence: int = 1
    award_hint: Optional[str] = None

@dataclass
class Cluster:
    role: str
    canonical: str
    aliases: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)

    def total_confidence(self) -> int:
        return sum(e.confidence for e in self.evidence)

# ---------- Normalization helpers ----------
WS_RE = re.compile(r"\s+")
QUOTES_RE = re.compile(r"[\"“”‘’]+")
PUNCT_EDGE_RE = re.compile(r"^[^\w@#]+|[^\w]+$")
AT_HASH_RE = re.compile(r"[@#]")  # later removed/space
HASHTAG_SPLIT_RE = re.compile(r"#?([A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+)")

def _strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

def _split_hashtags_and_handles(s: str) -> str:
    out = []
    for tok in s.split():
        if tok.startswith("#"):
            parts = HASHTAG_SPLIT_RE.findall(tok)
            flat = " ".join(p[0] if isinstance(p, tuple) else p for p in parts)
            out.append(flat or tok[1:])
        elif tok.startswith("@"):
            out.append(tok[1:])  # drop '@', keep token for name recovery
        else:
            out.append(tok)
    return " ".join(out)

def _basic_clean(s: str) -> str:
    s = _strip_accents(s)
    s = _split_hashtags_and_handles(s)
    s = QUOTES_RE.sub("", s)
    s = PUNCT_EDGE_RE.sub("", s.strip())
    s = AT_HASH_RE.sub(" ", s)
    s = WS_RE.sub(" ", s).strip()
    return s

def _normalize_for_match(raw: str) -> Tuple[str, List[str]]:
    s = _basic_clean(raw)
    low = s.lower()
    toks = [t for t in re.findall(r"[a-z0-9][a-z0-9\-']*", low) if t]
    toks = [t for t in toks if t not in NOISE_TOKENS]
    if not toks:
        toks = [w for w in re.findall(r"[a-z0-9]+", low)]
    return " ".join(toks), toks

def _title_case(s: str) -> str:
    return " ".join(w.capitalize() if not w.isupper() else w for w in re.findall(r"[A-Za-z0-9\-']+", s))

# ---------- Name/alias utilities ----------
def _name_parts(s: str) -> Tuple[List[str], Optional[str], Optional[str]]:
    """Return (tokens, first, last) from a display string."""
    s = _basic_clean(s)
    toks = [t for t in re.findall(r"[A-Za-z][A-Za-z\-']*", s)]
    if not toks:
        return [], None, None
    return toks, toks[0], toks[-1]

def _is_personish(s: str) -> bool:
    toks, first, last = _name_parts(s)
    # Person-like if has at least 2 tokens and most tokens start uppercase
    if len(toks) >= 2:
        cap = sum(1 for t in toks if t[0].isupper())
        return cap / len(toks) >= 0.6
    return False

def _gen_alias_candidates(canonical: str) -> List[str]:
    """Generate likely aliases automatically from the canonical form."""
    toks, first, last = _name_parts(canonical)
    al = set()
    disp = _title_case(canonical)
    al.add(disp)
    if _is_personish(canonical) and first and last:
        # common person aliases
        al.add(f"{first} {last}")
        al.add(last)                 # last-name only
        al.add(f"{first[0]}. {last}") if first else None
        # middle name/initial collapses (already implicit via first last)
    else:
        # work/title-like: strip leading 'The', collapse punctuation variants
        if toks and toks[0].lower() == "the":
            al.add(" ".join(toks[1:]))
    # deaccented + lower alias for matching
    al.add(_strip_accents(disp))
    al.add(disp.lower())
    return [a for a in al if a]

# ---------- Similarity ----------
def _token_jaccard(a_toks: List[str], b_toks: List[str]) -> float:
    if not a_toks and not b_toks:
        return 0.0
    A, B = set(a_toks), set(b_toks)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)

def _string_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def name_similarity(a_raw: str, b_raw: str) -> float:
    anorm, atoks = _normalize_for_match(a_raw)
    bnorm, btoks = _normalize_for_match(b_raw)
    jac = _token_jaccard(atoks, btoks)
    rat = _string_ratio(anorm, bnorm)
    return 0.6 * rat + 0.4 * jac

# ---------- Ticket iterator ----------
def _iter_candidates_from_tickets(
    tickets: List[Dict], valid_roles: Iterable[str] = DEFAULT_ROLE_KEYS
) -> Iterable[Tuple[str, str, Evidence]]:
    for t in tickets:
        conf = int(t.get("confidence", 1))
        for name, role, hint in t.get("names-cat", []):
            if not isinstance(name, str) or not name.strip():
                continue
            if role not in valid_roles and role is not None:
                continue
            yield name, (role or "nominee"), Evidence(text=name, confidence=conf, award_hint=hint)

# ---------- Core clustering with automatic alias discovery ----------
def cluster_candidates(
    tickets: List[Dict],
    sim_threshold: float = 0.88,
    alias_hit_threshold: float = 0.90,
    roles: Iterable[str] = DEFAULT_ROLE_KEYS
) -> Dict[str, List[Cluster]]:
    """
    Build clusters per role (winner/nominee/presenter/host) with automatic alias discovery.
    Returns: { role: [Cluster, ...], ... }
    """
    clusters_by_role: Dict[str, List[Cluster]] = {r: [] for r in roles}

    # alias index: role -> normalized key -> cluster
    alias_index: Dict[str, Dict[str, Cluster]] = {r: {} for r in roles}

    def _index_alias(role: str, surface: str, cluster: Cluster):
        # index multiple normalizations for robust future matches
        surf_clean = _basic_clean(surface)
        k1, toks = _normalize_for_match(surf_clean)
        keys = {k1, surf_clean.lower()}
        for a in _gen_alias_candidates(surface):
            k, _ = _normalize_for_match(a)
            keys.add(k)
            keys.add(a.lower())
        for k in keys:
            if k:
                alias_index[role][k] = cluster

    for raw_name, role, ev in _iter_candidates_from_tickets(tickets, roles):
        # quick normalized key for alias lookup
        base_norm, _ = _normalize_for_match(raw_name)
        # 1) alias index hit
        hit_cluster = alias_index[role].get(base_norm)
        if not hit_cluster:
            # 2) try looser alias keys (lowercased form)
            hit_cluster = alias_index[role].get(_basic_clean(raw_name).lower())

        placed = False
        if hit_cluster:
            hit_cluster.aliases.append(raw_name)
            hit_cluster.evidence.append(ev)
            placed = True
        else:
            # 3) similarity to existing clusters (canonical or aliases)
            best_sim, best_cluster = 0.0, None
            for cl in clusters_by_role[role]:
                s1 = name_similarity(raw_name, cl.canonical)
                s2 = max([name_similarity(raw_name, a) for a in cl.aliases] or [0.0])
                s = max(s1, s2)
                if s > best_sim:
                    best_sim, best_cluster = s, cl

            # 3a) person-style rule: last name match + first initial match
            if best_sim < sim_threshold and _is_personish(best_cluster.canonical if best_cluster else ""):
                cand_toks, c_first, c_last = _name_parts(raw_name)
                cl_toks, cl_first, cl_last = _name_parts(best_cluster.canonical) if best_cluster else ([], None, None)
                if c_last and cl_last and c_last.lower() == cl_last.lower():
                    if not c_first or not cl_first or c_first[0].lower() == cl_first[0].lower():
                        best_sim = alias_hit_threshold
            # 4) attach or create
            if best_cluster and best_sim >= sim_threshold:
                best_cluster.aliases.append(raw_name)
                best_cluster.evidence.append(ev)
                placed = True
                # index this new alias for future matches
                _index_alias(role, raw_name, best_cluster)

        if not placed:
            # make a new cluster and index its aliases
            canonical = _choose_canonical_auto([raw_name])
            cl = Cluster(role=role, canonical=canonical, aliases=[raw_name], evidence=[ev])
            clusters_by_role[role].append(cl)
            # index canonical + generated aliases
            _index_alias(role, canonical, cl)
            for a in _gen_alias_candidates(canonical):
                _index_alias(role, a, cl)
            # also index the raw surface
            _index_alias(role, raw_name, cl)

    # final tidy per cluster
    for role, cls in clusters_by_role.items():
        for cl in cls:
            # clean canonical
            cl.canonical = _choose_canonical_auto([cl.canonical, *cl.aliases])
            # dedupe aliases
            seen = set()
            unique = []
            for a in cl.aliases:
                key = _basic_clean(a).lower()
                if key not in seen:
                    unique.append(a)
                    seen.add(key)
            cl.aliases = unique

    return clusters_by_role

def _choose_canonical_auto(variants: List[str]) -> str:
    """
    Pick a canonical form from observed variants:
    - prefer person-like full names; else longest tokenized title
    - then longest by length
    - title-case as display
    """
    if not variants:
        return ""
    # score by (is_personish, token_count, length)
    scored = []
    for v in variants:
        toks, _, _ = _name_parts(v)
        scored.append((1 if _is_personish(v) else 0, len(toks), len(v), v))
    scored.sort(reverse=True)
    chosen = scored[0][3]
    return _title_case(chosen)

# ---------- Optional: ranking helper ----------
def rank_clusters_by_confidence(
    clustered: Dict[str, List[Cluster]]
) -> Dict[str, List[Tuple[str, int, List[str]]]]:
    out: Dict[str, List[Tuple[str, int, List[str]]]] = {}
    for role, cls in clustered.items():
        rows = [(cl.canonical, cl.total_confidence(), cl.aliases) for cl in cls]
        rows.sort(key=lambda r: (-r[1], -len(r[2]), r[0]))
        out[role] = rows
    return out

# ---------- Example manual test ----------
if __name__ == "__main__":
    tickets = [
        {'names-cat': [('Tina Fey', 'presenter', None)], 'confidence': 1},
        {'names-cat': [('christoph waltz', 'winner', None), ('P3rla david Golden', 'winner', None)], 'confidence': 2},
        {'names-cat': [('Christoph Waltz WINS', 'winner', None), ('Mikeand', 'winner', None)], 'confidence': 2},
        {'names-cat': [('Christoph Waltz', 'nominee', 'Best Supporting Actor goes to Christoph Waltz in')], 'confidence': 2},
        {'names-cat': [('Django', 'winner', 'Best supporting actor Golden globes')], 'confidence': 4},
        {'names-cat': [('Amy Poehler', 'host', None), ('Amy', 'host', None)], 'confidence': 1},
        {'names-cat': [('#SofiaVergara', 'presenter', None), ('@kerrywashington', 'presenter', None)], 'confidence': 1},
        {'names-cat': [('Leonardo Dicaprio', 'nominee', None), ('Leo', 'nominee', None)], 'confidence': 1},
    ]
    clusters = cluster_candidates(tickets)
    from pprint import pprint
    pprint(rank_clusters_by_confidence(clusters))
