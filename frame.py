import typesys
from extraction import clean_tweets, extract_people, tweet_data
from Levenshtein import distance as levenshtein_distance
import re
from collections import Counter

#HYPERPARAMETERS
MAX_LEVENSHTEIN_DISTANCE = 10  # Tighter tolerance for better accuracy
WINDOW_SIZE = 100  # Larger window to catch more context
trainsize = len(tweet_data)

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
    for end in range(3, min(15, len(words)+1)):
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
    PRIORITY ORDER: host > presenter > winner > nominee
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
    
    # CRITICAL: Presenter keywords - removed "award" to avoid false positives
    # Key patterns: "X presents", "X and Y present", "presented by X"
    presenter_kw = re.compile(
        r"\b(present|presents|presented|presenting|presenter|presenters|"
        r"introduce|introduces|introduced|introducing|handed out|hands out|"
        r"gave out|gives out|giving out)\b", 
        re.IGNORECASE
    )
    
    # Additional strong presenter patterns
    present_nominees_pattern = re.compile(
        r"present(?:s|ed|ing)?\s+(?:the\s+)?(?:nominees|award)", 
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

        # Check for host keywords FIRST (special case, no award needed)
        if host_kw.search(window_lower):
            return "host", None

        # Find any phrase starting with 'Best' (case insensitive) within this window
        best_matches = list(re.finditer(r"[Bb]est [A-Za-z0-9 &'()-]{2,80}", window_orig))
        
        # Also look for Cecil B. DeMille
        cecil_matches = list(re.finditer(r"[Cc]ecil [Bb]\.\s*[Dd]e[Mm]ille", window_orig))
        
        all_award_matches = best_matches + cecil_matches
        
        for award_match in all_award_matches:
            if award_match in cecil_matches:
                nomination = "Cecil B DeMille Award for Lifetime Achievement in Motion Pictures"
            else:
                nomination = find_best_award(award_match.group(0))
            
            if not nomination:
                continue
            
            # Calculate confidence score based on keyword proximity to name
            name_pos = start - win_start
            award_pos = award_match.start() - win_start
            
            # Check PRESENTER keywords with HIGHEST priority
            # Key insight: presenters come BEFORE the award name
            # Pattern: "Name present(s) the award" or "Name and Name present the nominees for Award"
            presenter_matches = list(presenter_kw.finditer(window_lower))
            present_nominees_matches = list(present_nominees_pattern.finditer(window_lower))
            
            if presenter_matches or present_nominees_matches:
                all_presenter_indicators = presenter_matches + present_nominees_matches
                
                for pmatch in all_presenter_indicators:
                    presenter_word_pos = pmatch.start()
                    
                    # Check if pattern is: Name ... present ... Award
                    # Name should come before "present", and "present" should come before award
                    if name_pos < presenter_word_pos < award_pos:
                        # This is the classic presenter pattern
                        distance_name_to_present = presenter_word_pos - name_pos
                        distance_present_to_award = award_pos - pmatch.end()
                        
                        # Close proximity check
                        if distance_name_to_present < 50 and distance_present_to_award < 50:
                            confidence = 20  # Very high confidence
                            
                            # Bonus for "present the nominees" pattern
                            if pmatch in present_nominees_matches:
                                confidence += 5
                            
                            if confidence > highest_confidence:
                                highest_confidence = confidence
                                best_category = "presenter"
                                best_nomination = nomination
                    
                    # Also check reverse pattern: "Award presented by Name"
                    elif award_pos < presenter_word_pos < name_pos:
                        distance_award_to_present = presenter_word_pos - award_pos
                        distance_present_to_name = name_pos - pmatch.end()
                        
                        if distance_award_to_present < 50 and distance_present_to_name < 30:
                            confidence = 18
                            if confidence > highest_confidence:
                                highest_confidence = confidence
                                best_category = "presenter"
                                best_nomination = nomination
            
            # Check winner keywords (lower priority than presenter)
            winner_matches = list(winner_kw.finditer(window_lower))
            if winner_matches and highest_confidence < 15:  # Only if no strong presenter signal
                # Winners usually have keyword AFTER name or very close
                min_dist = min(abs(match.start() - name_pos) for match in winner_matches)
                if min_dist < 50:
                    confidence = 10 - (min_dist / 10)
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_category = "winner"
                        best_nomination = nomination
            
            # Check nominee keywords (lowest priority)
            nominee_matches = list(nominee_kw.finditer(window_lower))
            if nominee_matches and highest_confidence < 10:  # Only if no strong winner/presenter signal
                min_dist = min(abs(match.start() - name_pos) for match in nominee_matches)
                if min_dist < 50:
                    confidence = 8 - (min_dist / 10)
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_category = "nominee"
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
                ticket["confidence"] += 4  # Higher weight for presenters
            elif cat == "host":
                ticket["confidence"] += 2
            
            if nomination is not None:
                ticket["confidence"] += 2
            
            seen_combinations.add(sig)

        # Only keep tickets with meaningful confidence
        if ticket["confidence"] >= 1:
            tickets.append(ticket)

    print(f"\nExtracted {len(tickets)} high-confidence tickets")
    return tickets

# print(get_tickets(tweet_data))