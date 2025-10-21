import typesys
from extraction import clean_tweets, extract_people, tweet_data
from Levenshtein import distance as levenshtein_distance
import re

#HYPERPARAMETERS
MAX_LEVENSHTEIN_DISTANCE = 12  # Balanced tolerance
WINDOW_SIZE = 60

print("Number of tweets:", len(tweet_data))

AWARD_NAMES =  [
    "Best Motion Picture Drama",
    "Best Motion Picture Musical or Comedy",
    "Best Motion Picture Foreign Language",
    "Best Motion Picture Animated",
    "Best Cinematic and Box Office Achievement Motion Picture",
    "Best Director Motion Picture",
    "Best Actor in a Motion Picture Drama",
    "Best Actor in a Motion Picture Musical or Comedy",
    "Best Actress in a Motion Picture Drama",
    "Best Actress in a Motion Picture Musical or Comedy",
    "Best Supporting Actor Motion Picture",
    "Best Supporting Actress Motion Picture",
    "Best Screenplay Motion Picture",
    "Best Score Motion Picture",
    "Best Song Motion Picture",
    "Cecil B DeMille Award for Lifetime Achievement in Motion Pictures",
    "Best Television Series Drama",
    "Best Television Series Musical or Comedy",
    "Best Miniseries or Motion Picture Television",
    "Best Actor in a Television Series Drama",
    "Best Actor in a Television Series Musical or Comedy",
    "Best Actor in a Miniseries or Motion Picture Television",
    "Best Actress in a Television Series Drama",
    "Best Actress in a Television Series Musical or Comedy",
    "Best Actress in a Miniseries or Motion Picture Television",
    "Best Supporting Actor Series Miniseries or Motion Picture Made for Television",
    "Best Supporting Actress Series Miniseries or Motion Picture Made for Television",
    "Best Supporting Actor in a Television Series",  # Added simplified version
    "Best Supporting Actress in a Television Series",  # Added simplified version
    "Best Stand Up Comedy Performance Television",
    "Carol Burnett Award for Lifetime Achievement in Television"
]


def find_best_award(window_text, max_distance=MAX_LEVENSHTEIN_DISTANCE):
    """
    Given a text window starting with 'Best', find the closest award name.
    """
    # Clean the window text - remove extra punctuation
    window_text = re.sub(r'["""]', '', window_text)
    window_text = re.sub(r'\s+', ' ', window_text).strip()
    
    best_match = None
    best_distance = float('inf')
    words = window_text.split()
    
    # Try windows of different sizes
    for end in range(2, min(15, len(words)+1)):
        candidate = " ".join(words[:end])
        
        # Find closest AWARD_NAME using Levenshtein distance
        for award in AWARD_NAMES:
            dist = levenshtein_distance(award.lower(), candidate.lower())
            if dist < best_distance:
                best_distance = dist
                best_match = award
    
    # Penalize "Best Song" matches - require tighter distance
    if best_match == "Best Song Motion Picture" and best_distance > 5:
        return None
    
    # Return the best match if it's within tolerance AND candidate is at least 8 chars
    if best_distance <= max_distance and len(" ".join(words[:2])) >= 8:
        return best_match
    return None

def extract_category_and_nomination(name, text):
    """
    Return (category, nomination) for a given person and tweet text.
    Uses windowed best-phrase extraction + Levenshtein distance.
    """
    lower_text = text.lower()
    winner_kw = re.compile(r"\b(won|wins|is the winner|takes|takes home|goes to|receives|awarded)\b", re.IGNORECASE)
    nominee_kw = re.compile(r"\b(nominated|nominee|up for|shortlisted)\b", re.IGNORECASE)
    presenter_kw = re.compile(r"\b(presents|presenting|hosted|host|hosts)\b", re.IGNORECASE)

    try:
        name_re = re.compile(r"\b" + re.escape(name.lower()) + r"\b")
    except re.error:
        return None, None

    # Search for the name in the text
    for m in name_re.finditer(lower_text):
        start, end = m.start(), m.end()
        win_start = max(0, start - WINDOW_SIZE)
        win_end = min(len(lower_text), end + WINDOW_SIZE)
        window_lower = lower_text[win_start:win_end]
        window_orig = text[win_start:win_end]

        # Find any phrase starting with 'Best' (case insensitive) within this window
        best_match = re.search(r"[Bb]est [A-Za-z0-9 &'()-]{2,80}", window_orig)
        nomination = find_best_award(best_match.group(0)) if best_match else None

        # Check for winner keywords
        if winner_kw.search(window_lower) and nomination:
            return "winner", nomination
        if nominee_kw.search(window_lower) and nomination:
            return "nominee", nomination
        if presenter_kw.search(window_lower):
            return "presenter", nomination

        # Default to winner if we found a nomination (since most tweets announce winners)
        if nomination:
            return "winner", nomination

    return None, None


from tqdm import tqdm
def get_tickets(tweet_data):
    tickets = []

    for tweet in tqdm(tweet_data[:5000]):
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

        if ticket["confidence"] > 0:  # Changed from > 1 to > 0
            tickets.append(ticket)

    return tickets

print(get_tickets(tweet_data))