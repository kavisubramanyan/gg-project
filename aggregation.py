#assume that inputs are well-formed like the following
""" {
  "type": "person" | "movie" | "award",
  "canonical": "anne hathaway",
  "aliases": {"anne hathaway","hathaway"},
  "evidence": [
    {
      "tweet_id": 290620657799159809,     # optional but helpful
      "user": "_NicoleEdwards",           # screen_name or user id
      "kind": "WIN" or "NOM" or "MENTION",
      "weight": 1|2|3,                    # pattern specificity from extractor
      "hedged": False,                    # True if prediction/hope/snark
      "clean_bonus": 1.1,                 # e.g., short/noisy tweet bonus
      "ts": 1358124338000,                # timestamp_ms (optional)
      "text": "Anne Hathaway has got me living. #GoldenGlobes"
    },
    ...
  ]
} """




# aggregation.py
from collections import defaultdict, Counter
from math import exp

class AggregationConfig:
    """
    Tunable weights and options (safe defaults).
    """
    # evidence weights
    BASE_WIN = 2.0       # base score boost if hit.kind == "WIN"
    BASE_NOM = 1.0       # base score boost if hit.kind == "NOM"
    RT_DUP_PENALTY = 0.5 # multiply if many duplicate texts (RT-like)
    USER_CAP = 3         # max contributions counted per single user
    STRICT_HIT_BONUS = 0.2  # per strict (weight>=3) hit
    DISTINCT_USER_BONUS = 0.05  # per distinct user
    ALIAS_BONUS = 0.03   # per alias (reflects alias consolidation strength)

    # penalties
    HEDGED_ZERO_OUT = True     # ignore hedged hits entirely
    LONG_TWEET_PENALTY = 0.9   # multiply when clean_bonus < 1.0 (already encoded)
    
    # constraints
    ENFORCE_WINNER_IN_NOMINEES = True

    # softmax temperature for confidence
    CONF_TEMPERATURE = 1.0

def _softmax(xs, T=1.0):
    if not xs: 
        return []
    m = max(xs)
    exps = [exp((x - m)/max(T, 1e-6)) for x in xs]
    s = sum(exps)
    return [v/s for v in exps]

def _score_hit(hit, cfg: AggregationConfig):
    if cfg.HEDGED_ZERO_OUT and hit.get("hedged"):
        return 0.0
    base = cfg.BASE_WIN if hit.get("kind") == "WIN" else (cfg.BASE_NOM if hit.get("kind") == "NOM" else 0.5)
    spec = hit.get("weight", 1)           # 1..3 from extractor
    clean = hit.get("clean_bonus", 1.0)   # ~0.9..1.2
    return base * spec * clean

def _dedupe_like_rts(evidence_list):
    """
    Group by normalized text; return a dict text->count to detect echo/RTs.
    """
    norm = lambda s: ' '.join((s or '').lower().split())
    bag = Counter(norm(h.get("text","")) for h in evidence_list if h.get("text"))
    return bag

def _apply_user_cap(evidence_list, cap):
    """
    Limit per-user impact to avoid spam; keep only top-scoring 'cap' hits per user.
    """
    by_user = defaultdict(list)
    for h in evidence_list:
        by_user[h.get("user","?")].append(h)
    pruned = []
    for u, hits in by_user.items():
        # keep up to cap; no scoring yet, so sort by (weight, clean_bonus) proxy
        hits.sort(key=lambda k: (k.get("weight",1), k.get("clean_bonus",1.0)), reverse=True)
        pruned.extend(hits[:cap])
    return pruned

