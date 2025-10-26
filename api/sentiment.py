import json
from typing import Dict, List

from utils.frame import normalize_text

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
except Exception:
    nltk = None
    SentimentIntensityAnalyzer = None


def get_sentiment_analyzer():
    if SentimentIntensityAnalyzer is None:
        return None
    try:
        return SentimentIntensityAnalyzer()
    except Exception:
        try:
            import nltk as _n
            _n.download('vader_lexicon', quiet=True)
            return SentimentIntensityAnalyzer()
        except Exception:
            return None


def label_sentiment(text: str) -> str:
    sia = get_sentiment_analyzer()
    if sia is None:
        t = normalize_text(text)
        if any(w in t for w in ["love", "great", "amazing", "awesome", "best"]):
            return "positive"
        if any(w in t for w in ["hate", "worst", "terrible", "awful", "meh"]):
            return "negative"
        return "neutral"
    scores = sia.polarity_scores(text)
    comp = scores.get('compound', 0.0)
    if comp > 0.05:
        return "positive"
    if comp < -0.05:
        return "negative"
    return "neutral"


def analyze_group(tweets: List[dict], names: List[str]) -> Dict[str, str]:
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    example = {"positive": "", "negative": "", "neutral": ""}
    lower_names = [n.lower() for n in names if n]
    for tw in tweets:
        raw = tw.get("text", "")
        if not raw:
            continue
        n = normalize_text(raw)
        if any(name and name in n for name in lower_names):
            lab = label_sentiment(raw)
            counts[lab] += 1
            if not example[lab]:
                example[lab] = raw.strip().replace("\n", " ")[:160]
    top = max(counts.items(), key=lambda x: x[1])[0] if any(counts.values()) else "neutral"
    return {"label": top, "example": example[top]}


MAX_TWEETS_FOR_SENTIMENT = 12000


def compute_sentiments_from_file(tweets_file: str, winners: Dict[str, str], presenters: Dict[str, List[str]]) -> Dict[str, Dict[str, str]]:
    try:
        with open(tweets_file, "r") as f:
            tweets = json.load(f)
    except Exception:
        tweets = []
    if len(tweets) > MAX_TWEETS_FOR_SENTIMENT:
        tweets = tweets[:MAX_TWEETS_FOR_SENTIMENT]

    winner_names = [w for w in winners.values() if isinstance(w, str) and w]
    presenter_names: List[str] = []
    for lst in presenters.values():
        if isinstance(lst, list):
            presenter_names.extend([p for p in lst if isinstance(p, str) and p])

    return {
        "winners": analyze_group(tweets, winner_names),
        "presenters": analyze_group(tweets, presenter_names),
    }


__all__ = [
    "compute_sentiments_from_file",
]


def compute_per_entity_sentiments_from_file(tweets_file: str, winners: Dict[str, str], presenters: Dict[str, List[str]]) -> Dict[str, Dict[str, Dict[str, str]]]:
    try:
        with open(tweets_file, "r") as f:
            tweets = json.load(f)
    except Exception:
        tweets = []
    if len(tweets) > MAX_TWEETS_FOR_SENTIMENT:
        tweets = tweets[:MAX_TWEETS_FOR_SENTIMENT]

    norm_texts: List[str] = [normalize_text(tw.get("text", "")) for tw in tweets]

    # Initialize structures
    per_winner_counts: Dict[str, Dict[str, int]] = {}
    per_winner_example: Dict[str, Dict[str, str]] = {}
    per_presenter_counts: Dict[str, Dict[str, int]] = {}
    per_presenter_example: Dict[str, Dict[str, str]] = {}

    for award, winner in winners.items():
        per_winner_counts[award] = {"positive": 0, "negative": 0, "neutral": 0}
        per_winner_example[award] = {"positive": "", "negative": "", "neutral": ""}
    for award in presenters.keys():
        per_presenter_counts[award] = {"positive": 0, "negative": 0, "neutral": 0}
        per_presenter_example[award] = {"positive": "", "negative": "", "neutral": ""}

    # Single pass over tweets
    for tw, ntext in zip(tweets, norm_texts):
        raw = tw.get("text", "")
        if not raw:
            continue
        lab = None

        # Winners: check each award's winner name
        for award, winner in winners.items():
            if isinstance(winner, str) and winner:
                if winner.lower() in ntext:
                    if lab is None:
                        lab = label_sentiment(raw)
                    per_winner_counts[award][lab] += 1
                    if not per_winner_example[award][lab]:
                        per_winner_example[award][lab] = raw.strip().replace("\n", " ")[:160]

        # Presenters: check each award's presenters
        for award, plist in presenters.items():
            if not isinstance(plist, list) or not plist:
                continue
            found = False
            for p in plist:
                if isinstance(p, str) and p and p.lower() in ntext:
                    found = True
                    break
            if found:
                if lab is None:
                    lab = label_sentiment(raw)
                per_presenter_counts[award][lab] += 1
                if not per_presenter_example[award][lab]:
                    per_presenter_example[award][lab] = raw.strip().replace("\n", " ")[:160]

    # Reduce to label + example per award
    per_winner: Dict[str, Dict[str, str]] = {}
    for award, counts in per_winner_counts.items():
        label = max(counts.items(), key=lambda x: x[1])[0] if any(counts.values()) else "neutral"
        per_winner[award] = {"label": label, "example": per_winner_example[award][label]}

    per_presenter: Dict[str, Dict[str, str]] = {}
    for award, counts in per_presenter_counts.items():
        label = max(counts.items(), key=lambda x: x[1])[0] if any(counts.values()) else "neutral"
        per_presenter[award] = {"label": label, "example": per_presenter_example[award][label]}

    return {
        "winners": per_winner,
        "presenters": per_presenter,
    }


__all__.append("compute_per_entity_sentiments_from_file")


