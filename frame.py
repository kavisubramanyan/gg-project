import typesys
from extraction import clean_tweets, extract_people, tweet_data
from Levenshtein import distance as levenshtein_distance
import re
from collections import Counter

#HYPERPARAMETERS
MAX_LEVENSHTEIN_DISTANCE = 10  # Tighter tolerance for better accuracy
WINDOW_SIZE = 80  # Larger window to catch more context
trainsize = 80000

print("Number of tweets:", len(tweet_data))

AWARD_NAMES = [
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
    "Best Supporting Actor in a Television Series",
    "Best Supporting Actress in a Television Series",
    "Best Stand Up Comedy Performance Television",
    "Carol Burnett Award for Lifetime Achievement in Television"
]

# Pre-compute award variations for faster matching
AWARD_KEYWORDS = {}
for award in AWARD_NAMES:
    words = award.lower().split()
    # Store key phrases from each award
    AWARD_KEYWORDS[award] = {
        'full': award.lower(),
        'words': set(words),
        'bigrams': set([f"{words[i]} {words[i+1]}" for i in range(len(words)-1)])
    }


def find_best_award(window_text, max_distance=MAX_LEVENSHTEIN_DISTANCE):
    """
    Given a text window starting with 'Best', find the closest award name.
    Optimized with early filtering and better matching.
    """
    # Clean the window text
    window_text = re.sub(r'["""]', '', window_text)
    window_text = re.sub(r'\s+', ' ', window_text).strip()
    window_lower = window_text.lower()
    
    best_match = None
    best_distance = float('inf')
    words = window_text.split()
    
    # Quick filter: if window doesn't contain common award words, skip
    award_indicators = {'actor', 'actress', 'picture', 'motion', 'series', 'television', 
                        'drama', 'comedy', 'musical', 'director', 'screenplay', 'song',
                        'score', 'foreign', 'animated', 'supporting', 'demille', 'cecil'}
    window_words = set(window_lower.split())
    if not window_words.intersection(award_indicators):
        return None
    
    # Try windows of different sizes (optimize range)
    for end in range(3, min(12, len(words)+1)):
        candidate = " ".join(words[:end])
        candidate_lower = candidate.lower()
        
        # Skip very short candidates
        if len(candidate) < 10:
            continue
        
        # Pre-filter awards that share keywords
        candidate_words = set(candidate_lower.split())
        potential_awards = []
        
        for award in AWARD_NAMES:
            # Quick overlap check
            if len(AWARD_KEYWORDS[award]['words'].intersection(candidate_words)) >= 2:
                potential_awards.append(award)
        
        # If no potential matches, continue
        if not potential_awards:
            continue
        
        # Find closest among potential awards
        for award in potential_awards:
            dist = levenshtein_distance(award.lower(), candidate_lower)
            if dist < best_distance:
                best_distance = dist
                best_match = award
    
    # Special cases for common patterns
    if best_match == "Best Song Motion Picture" and best_distance > 4:
        return None
    
    # Stricter for short matches
    if best_match and len(best_match.split()) <= 3 and best_distance > 6:
        return None
    
    # Return the best match if within tolerance
    if best_distance <= max_distance and len(" ".join(words[:2])) >= 8:
        return best_match
    return None


def extract_category_and_nomination(name, text):
    """
    Return (category, nomination) for a given person and tweet text.
    Enhanced with better keyword detection and context awareness.
    """
    lower_text = text.lower()
    
    # Enhanced keyword patterns with more variations
    winner_kw = re.compile(
        r"\b(won|wins|winner|winning|takes|took|takes home|goes to|went to|"
        r"receives|received|awarded|gets|got|congrats|congratulations|"
        r"victory|victorious|champion)\b", 
        re.IGNORECASE
    )
    
    nominee_kw = re.compile(
        r"\b(nominated|nominee|nominees|nomination|nominations|up for|"
        r"shortlisted|contender|contenders|in the running|competing for)\b", 
        re.IGNORECASE
    )
    
    presenter_kw = re.compile(
        r"\b(presents|presented|presenting|presenter|presenters|"
        r"introduce|introduced|introducing|handed out|gave|giving)\b", 
        re.IGNORECASE
    )
    
    host_kw = re.compile(
        r"\b(host|hosts|hosted|hosting|co-host|cohost|emcee|emceeing)\b",
        re.IGNORECASE
    )

    try:
        name_re = re.compile(r"\b" + re.escape(name.lower()) + r"\b")
    except re.error:
        return None, None

    # Track all matches and their contexts
    best_category = None
    best_nomination = None
    highest_confidence = 0
    
    # Search for the name in the text
    for m in name_re.finditer(lower_text):
        start, end = m.start(), m.end()
        win_start = max(0, start - WINDOW_SIZE)
        win_end = min(len(lower_text), end + WINDOW_SIZE)
        window_lower = lower_text[win_start:win_end]
        window_orig = text[win_start:win_end]

        # Find any phrase starting with 'Best' (case insensitive) within this window
        best_matches = re.finditer(r"[Bb]est [A-Za-z0-9 &'()-]{2,80}", window_orig)
        
        for best_match in best_matches:
            nomination = find_best_award(best_match.group(0))
            
            if not nomination:
                continue
            
            # Calculate confidence score based on keyword proximity to name
            name_pos = start - win_start
            confidence = 0
            
            # Check for host keywords first (special case)
            if host_kw.search(window_lower):
                return "host", None
            
            # Check winner keywords
            winner_matches = list(winner_kw.finditer(window_lower))
            if winner_matches:
                # Find closest winner keyword to name
                min_dist = min(abs(match.start() - name_pos) for match in winner_matches)
                if min_dist < 50:  # Close to name
                    confidence = 10 - (min_dist / 10)  # Closer = higher confidence
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_category = "winner"
                        best_nomination = nomination
            
            # Check nominee keywords
            nominee_matches = list(nominee_kw.finditer(window_lower))
            if nominee_matches:
                min_dist = min(abs(match.start() - name_pos) for match in nominee_matches)
                if min_dist < 50:
                    confidence = 8 - (min_dist / 10)
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_category = "nominee"
                        best_nomination = nomination
            
            # Check presenter keywords
            presenter_matches = list(presenter_kw.finditer(window_lower))
            if presenter_matches:
                min_dist = min(abs(match.start() - name_pos) for match in presenter_matches)
                if min_dist < 50:
                    confidence = 6 - (min_dist / 10)
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_category = "presenter"
                        best_nomination = nomination
            
            # Default to winner if we found nomination but no keywords
            # (most tweets announce winners without explicit "won" keyword)
            if nomination and highest_confidence == 0:
                confidence = 3
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_category = "winner"
                    best_nomination = nomination

    return best_category, best_nomination


from tqdm import tqdm
def get_tickets(tweet_data):
    """
    Extract structured tickets from tweet data.
    Enhanced with deduplication and confidence scoring.
    """
    tickets = []
    seen_combinations = set()  # Avoid duplicate tickets

    for tweet in tqdm(tweet_data[:trainsize], desc="Processing tweets"):
        cleaned = clean_tweets(tweet.get("text", ""))
        
        # Skip empty tweets
        if not cleaned or len(cleaned) < 10:
            continue
        
        people = extract_people(cleaned)
        
        # Skip tweets with no people or too many people (likely noise)
        if not people or len(people) > 10:
            continue

        ticket = {"names-cat": [], "confidence": 0}

        for name in people:
            cat, nomination = extract_category_and_nomination(name, cleaned)
            
            # Create signature for deduplication
            sig = (name.lower(), cat, nomination)
            if sig in seen_combinations:
                continue
            
            ticket["names-cat"].append((name, cat, nomination))
            
            # Weight confidence by category type
            if cat == "winner":
                ticket["confidence"] += 3
            elif cat == "nominee":
                ticket["confidence"] += 2
            elif cat == "presenter":
                ticket["confidence"] += 1
            elif cat == "host":
                ticket["confidence"] += 2
            
            if nomination is not None:
                ticket["confidence"] += 2
            
            seen_combinations.add(sig)

        # Only keep tickets with meaningful confidence
        if ticket["confidence"] >= 2:
            tickets.append(ticket)

    print(f"\nExtracted {len(tickets)} high-confidence tickets")
    return tickets

# print(get_tickets(tweet_data))