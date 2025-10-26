from typing import Dict, List, Tuple

from .extraction import extract_winner_counts, extract_nominee_counts, load_tweets


def postprocess_pick(award: str, top_keys: List[Tuple[str, int]]) -> str:
    if not top_keys:
        return ""
    key, _ = top_keys[0]
    tokens = key.split()
    if 1 < len(tokens) <= 4:
        return " ".join(t.capitalize() for t in tokens)
    return " ".join(w.capitalize() if len(w) > 2 else w for w in tokens)


class WinnerAggregator:
    @staticmethod
    def compute_winners(tweets: List[dict]) -> Dict[str, str]:
        counts = extract_winner_counts(tweets)
        winners: Dict[str, str] = {}
        for award, counter in counts.items():
            pruned = [(k, c) for k, c in counter.items() if c >= 2]
            pruned.sort(key=lambda x: (-x[1], x[0]))
            pick = postprocess_pick(award, pruned or counter.most_common(5))
            if pick:
                winners[award] = pick
        return winners


def compute_winners(tweets: List[dict]) -> Dict[str, str]:
    return WinnerAggregator.compute_winners(tweets)


def compute_winners_from_file(tweets_path: str) -> Dict[str, str]:
    data = load_tweets(tweets_path)
    return WinnerAggregator.compute_winners(data)


class NomineeAggregator:
    @staticmethod
    def compute_nominees(tweets: List[dict]) -> Dict[str, List[str]]:
        counts = extract_nominee_counts(tweets)
        winners = WinnerAggregator.compute_winners(tweets)
        nominees: Dict[str, List[str]] = {}
        for award, counter in counts.items():
            pruned = [(k, c) for k, c in counter.items() if c >= 2]
            pruned.sort(key=lambda x: (-x[1], x[0]))
            top_nominees = [k for k, c in pruned[:5]]
            winner = winners.get(award, "")
            if winner and winner in top_nominees:
                top_nominees.remove(winner)
            nominees[award] = top_nominees
        return nominees


def compute_nominees(tweets: List[dict]) -> Dict[str, List[str]]:
    return NomineeAggregator.compute_nominees(tweets)


def compute_nominees_from_file(tweets_path: str) -> Dict[str, List[str]]:
    data = load_tweets(tweets_path)
    return NomineeAggregator.compute_nominees(data)


