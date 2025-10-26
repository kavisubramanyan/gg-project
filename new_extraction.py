# new_extraction.py
import re
import json
import spacy
import ftfy
from unidecode import unidecode
from langdetect import detect, DetectorFactory
from collections import defaultdict, Counter

# Ensure reproducible language detection
DetectorFactory.seed = 0

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# ----------------------------
# Award categories
# ----------------------------
AWARD_NAMES = ['cecil b. demille award',
                   'best motion picture drama',
                   'best performance by an actress in a motion picture - drama',
                   'best performance by an actor in a motion picture - drama',
                   'best motion picture - comedy or musical',
                   'best performance by an actress in a motion picture - comedy or musical',
                   'best performance by an actor in a motion picture - comedy or musical',
                   'best animated feature film',
                   'best foreign language film',
                   'best performance by an actress in a supporting role in a motion picture',
                   'best performance by an actor in a supporting role in a motion picture',
                   'best director - motion picture',
                   'best screenplay - motion picture',
                   'best original score - motion picture',
                   'best original song - motion picture',
                   'best television series - drama',
                   'best performance by an actress in a television series - drama',
                   'best performance by an actor in a television series - drama',
                   'best television series - comedy or musical',
                   'best performance by an actress in a television series - comedy or musical',
                   'best performance by an actor in a television series - comedy or musical',
                   'best mini-series or motion picture made for television',
                   'best performance by an actress in a mini-series or motion picture made for television',
                   'best performance by an actor in a mini-series or motion picture made for television',
                   'best performance by an actress in a supporting role in a series, mini-series or motion picture made for television',
                   'best performance by an actor in a supporting role in a series, mini-series or motion picture made for television']


# ----------------------------
# Helpers
# ----------------------------
def extract_mentions_hashtags(text):
    mentions = re.findall(r"@(\w+)", text)
    hashtags = re.findall(r"#(\w+)", text)
    return mentions, hashtags

def normalize_mentions_hashtags(text):
    mentions, hashtags = extract_mentions_hashtags(text)
    for tag in mentions + hashtags:
        readable = tag.replace("_", " ").title()
        text = text.replace(f"@{tag}", readable)
        text = text.replace(f"#{tag}", readable)
    text = re.sub(r"\bGoldenglobes\b", "Golden Globes", text, flags=re.IGNORECASE)
    return text

def clean_tweet(tweet_obj):
    """Cleans text, normalizes mentions, and extracts metadata."""
    text = tweet_obj.get("text", "")
    if not text:
        return None

    # Fix encoding
    text = ftfy.fix_text(text)
    text = unidecode(text)

    # Detect language
    try:
        lang = detect(text)
    except:
        lang = "unknown"

    # Identify retweets and remove links
    is_retweet = bool(re.match(r"^RT @", text))
    text = re.sub(r"^RT\s+@\w+:?", "", text)
    text = re.sub(r"http\S+|www.\S+", "", text)

    # Normalize
    text = normalize_mentions_hashtags(text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = " ".join(text.split())

    mentions, hashtags = extract_mentions_hashtags(text)

    return {
        "id": tweet_obj.get("id"),
        "timestamp": tweet_obj.get("timestamp_ms"),
        "language": lang,
        "is_retweet": is_retweet,
        "clean_text": text,
        "mentions": mentions,
        "hashtags": hashtags
    }

def extract_people(text):
    """Extract PERSON names from text using spaCy."""
    doc = nlp(text)
    invalid = {
       "Golden Globes", "Globes", "Golden", "Golden Globes Best",
        "Awards", "NBC", "Tonight", "Best", "Golden Globe Awards"
    }
    names = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            if len(name) > 2 and name not in invalid:
                names.append(name)
    return names

def extract_award_mentions(text):
    """Detect likely award mentions in a tweet."""
    matches = []
    text_lower = text.lower()
    for award in AWARD_NAMES:
        award_lower = award.lower()
        words = [w for w in re.split(r"[-\s]", award_lower) if len(w) > 2]
        overlap = sum(1 for w in words if w in text_lower)
        if overlap >= 3:
            matches.append(award)
    return matches

BUZZWORDS = [
    "win", "winner", "nominee", "nominated", "host", "present", "speech",
    "dress", "redcarpet", "snubbed", "best", "performance"
]

def extract_buzzwords(text):
    """Pull buzzwords that signal event context."""
    words = re.findall(r"\b\w+\b", text.lower())
    return [w for w in words if w in BUZZWORDS]

# ----------------------------
# Main Aggregation
# ----------------------------
def aggregate_results(raw_tweet_data):
    """Run cleaning + entity extraction and return structured insights."""
    tweets = [clean_tweet(t) for t in raw_tweet_data if "text" in t]
    tweets = [t for t in tweets if t]

    for t in tweets:
        t["people"] = extract_people(t["clean_text"])
        t["awards"] = extract_award_mentions(t["clean_text"])
        t["buzzwords"] = extract_buzzwords(t["clean_text"])

    # Hosts
    host_tweets = [t for t in tweets if any(b in t["buzzwords"] for b in ["host", "hosting", "hosted"])]
    host_counts = Counter(p for t in host_tweets for p in t["people"] if not t["is_retweet"])
    hosts = [name for name, _ in host_counts.most_common(3)]

    # Award → mentions
    award_to_people = defaultdict(list)
    for t in tweets:
        for award in t["awards"]:
            award_to_people[award].extend(t["people"])

    # Winners
    winners = {
        award: Counter(people).most_common(1)[0][0]
        for award, people in award_to_people.items()
        if people
    }

    # Presenters
    presenters = defaultdict(list)
    for t in tweets:
        if "present" in t["buzzwords"]:
            for award in t["awards"]:
                presenters[award].extend(t["people"])
    presenter_results = {a: [p for p, _ in Counter(p_list).most_common(2)] for a, p_list in presenters.items()}

    # Nominees
    nominees = defaultdict(list)
    for t in tweets:
        if any(b in t["buzzwords"] for b in ["nominee", "nominated"]):
            for award in t["awards"]:
                nominees[award].extend(t["people"])
    nominee_results = {a: [p for p, _ in Counter(p_list).most_common(5)] for a, p_list in nominees.items()}

    return {
    "hosts": list(dict.fromkeys(hosts)),
    "winners": {a: w for a, w in winners.items()},
    "presenters": {a: list(dict.fromkeys(p)) for a, p in presenter_results.items()},
    "nominees": {a: list(dict.fromkeys(n)) for a, n in nominee_results.items()},
    "awards": list(set(winners.keys()) | set(presenter_results.keys()) | set(nominee_results.keys()))
    }
