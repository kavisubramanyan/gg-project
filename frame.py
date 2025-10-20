import typesys
from extraction import clean_tweets, extract_people, tweet_data
import re

print("Number of tweets:", len(tweet_data))


def extract_category_and_nomination(name, text):
    """
    Return (category, nomination) for a given person and tweet text.
    Category ∈ {"winner", "nominee", "presenter"} or None.
    Nomination ∈ short award phrase (e.g., "Best Actress") or None.
    """
    lower_text = text.lower()

    winner_kw = re.compile(r"\b(won|wins|is the winner|takes home|receives|awarded)\b", re.IGNORECASE)
    nominee_kw = re.compile(r"\b(nominated|nominee|up for|shortlisted)\b", re.IGNORECASE)
    presenter_kw = re.compile(r"\b(presents|presenting|hosted|host)\b", re.IGNORECASE)
    nomination_re = re.compile(r"\b(?:Best [A-Za-z0-9 &'()-]{2,60})\b", re.IGNORECASE)

    try:
        name_re = re.compile(r"\b" + re.escape(name.lower()) + r"\b")
    except re.error:
        return None, None

    for m in name_re.finditer(lower_text):
        start, end = m.start(), m.end()
        win_start = max(0, start - 60)
        win_end = min(len(lower_text), end + 60)
        window_lower = lower_text[win_start:win_end]
        window_orig = text[win_start:win_end]

        if winner_kw.search(window_lower):
            nom_m = nomination_re.search(window_orig)
            return "winner", nom_m.group(0).strip() if nom_m else None
        if nominee_kw.search(window_lower):
            nom_m = nomination_re.search(window_orig)
            return "nominee", nom_m.group(0).strip() if nom_m else None
        if presenter_kw.search(window_lower):
            nom_m = nomination_re.search(window_orig)
            return "presenter", nom_m.group(0).strip() if nom_m else None

        # heuristic: if "Best ..." is very close to name but no explicit keyword, assume nominee
        nom_m = nomination_re.search(window_orig)
        if nom_m:
            return "nominee", nom_m.group(0).strip()

    return None, None


def get_tickets(tweet_data):
    tickets = []

    for tweet in tweet_data:
        cleaned = clean_tweets(tweet.get("text", ""))
        people = extract_people(cleaned)  # names only

        ticket = {"names-cat": [], "confidence": 0}

        for name in people:
            cat, nomination = extract_category_and_nomination(name, cleaned)
            ticket["names-cat"].append((name, cat, nomination))
            if cat is not None:
                ticket["confidence"] += 1
            if nomination is not None:
                ticket["confidence"] += 1

        if ticket["confidence"] > 0:
            tickets.append(ticket)

    return tickets

print(get_tickets(tweet_data))
