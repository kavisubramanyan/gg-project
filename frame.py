import typesys
from extraction import clean_tweets, extract_people, tweet_data
import re

print("Number of tweets:", len(tweet_data))
def extract_category(name, text):
    lower_text = text.lower()
    # Patterns for winner
    winner_patterns = [
        rf"{re.escape(name.lower())} (won|is the winner|takes home|receives|awarded)",
        rf"{re.escape(name.lower())} (wins|won the|takes the)"
    ]
    # Patterns for nominee
    nominee_patterns = [
        rf"{re.escape(name.lower())} (nominated|nominee|up for|shortlisted)"
    ]
    # Patterns for presenter
    presenter_patterns = [
        rf"{re.escape(name.lower())} (presents|presenting|hosted)"
    ]

    for pat in winner_patterns:
        if re.search(pat, lower_text):
            return "winner"
    for pat in nominee_patterns:
        if re.search(pat, lower_text):
            return "nominee"
    for pat in presenter_patterns:
        if re.search(pat, lower_text):
            return "presenter"

    return None

def get_tickets(tweet_data):
    tickets = []

    for tweet in tweet_data:
        cleaned = clean_tweets(tweet.get("text", ""))
        people = extract_people(cleaned)  # names only

        ticket = {
            "names-cat": [],
            "confidence": 0
        }

        for name in people:
            cat = extract_category(name, cleaned)
            #print(f"Extracted category for {name}: {cat}")
            ticket["names-cat"].append((name, cat))
            if cat is not None:
                ticket["confidence"] += 1

        if ticket["confidence"] > 0:
            tickets.append(ticket)

    print("Generated tickets:", tickets)
    return tickets