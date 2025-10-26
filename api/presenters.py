import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional
import nltk
from nltk.tokenize import word_tokenize

from utils.frame import normalize_text, match_award, coarse_match_award
from constants import AWARD_NAMES, YEAR
PRESENTER_KEYWORDS = [
    "present", "presents", "presented", "presenting", "presenter", "presenters",
    "introduce", "introduces", "introduced", "introducing",
    "here to present", "presenting the award", "presented by",
    "to present", "will present", "are presenting", "is presenting",
    "announce", "announces", "announcing", "announcer",
    "give", "gives", "giving",
    "presentan", "presenta", "presentando", "presentador", "presentadores"
]

PRESENTER_PATTERNS = [
    re.compile(r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:and|&)\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:present|presenting|presentan|presenta)", re.IGNORECASE),
    re.compile(r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+y\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:present|presentan|presenta)", re.IGNORECASE),
    re.compile(r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:present|presenting|presenta|presentan)", re.IGNORECASE),
    re.compile(r"presented?\s+by\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.IGNORECASE),
    re.compile(r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:and|&|y)\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+to\s+present", re.IGNORECASE),
]
class PresenterExtractor:
    
    def __init__(self):
        import sys
        self._main_module = sys.modules.get('__main__')
        self.nlp = None
    
    def getNLP(self):
        if self.nlp is None:
            self.nlp = self._main_module._spacy_nlp
        return self.nlp
    
    def is_presenter_tweet(self, text: str) -> bool:
        text_lower = text.lower()
        
        presenter_words = ['presenter', 'presenters', 'presenting', 'presented', 'presents',
                          'presentan', 'presenta', 'to present', 'will present', 'are presenting',
                          'is presenting', ' present ']
        
        return any(word in text_lower for word in presenter_words)
    
    def extract_person_names(self, text: str) -> List[str]:
        persons = []
        seen = set()
        
        try:
            doc = self.getNLP()(text)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    name = self.cleanPersonName(name)
                    if name and self.isValidPersonName(name):
                        name_key = name.lower()
                        if name_key not in seen:
                            persons.append(name)
                            seen.add(name_key)
        except Exception:
            pass
        
        for pattern in PRESENTER_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    for m in match:
                        if m:
                            name = self.cleanPersonName(m)
                            if name and self.isValidPersonName(name):
                                name_key = name.lower()
                                if name_key not in seen:
                                    persons.append(name)
                                    seen.add(name_key)
                else:
                    name = self.cleanPersonName(match)
                    if name and self.isValidPersonName(name):
                        name_key = name.lower()
                        if name_key not in seen:
                            persons.append(name)
                            seen.add(name_key)
        
        return persons
    
    
    def cleanPersonName(self, name: str) -> str:
        if not name:
            return ""
        
        name = re.sub(r'[^\w\s-]', '', name)
        name = name.strip()
        
        name = re.sub(r'\b(rt|via|by|the|and|or|with|is|are|was|were)\b', '', name, flags=re.IGNORECASE)
        name = ' '.join(name.split())
        
        if not name:
            return ""
        
        tokens = name.split()
        cleaned_tokens = []
        for t in tokens:
            if '-' in t:
                parts = t.split('-')
                t = '-'.join(p.capitalize() for p in parts)
            else:
                t = t.capitalize()
            cleaned_tokens.append(t)
        
        name = ' '.join(cleaned_tokens)
        
        return name.strip()
    
    def isValidPersonName(self, name: str) -> bool:
        if not name:
            return False
        
        tokens = name.split()
        if len(tokens) < 2 or len(tokens) > 4:
            return False
        
        if not all(t[0].isupper() or t[0].isdigit() for t in tokens if t):
            return False
        
        banned_words = [
            'golden globes', 'golden globe', 'best picture', 'best actor',
            'best actress', 'tonight show', 'red carpet',
            'twitter', 'hashtag', 'retweet', 'two children',
            'on stage', 'watch adele', 'watch', 'tonight', 'baron cohen stumbles'
        ]
        name_lower = name.lower()
        if any(banned in name_lower for banned in banned_words):
            return False
        
        if 'best' in name_lower:
            award_words = ['song', 'score', 'film', 'picture', 'animated', 'foreign', 'director', 
                          'screenplay', 'actor', 'actress', 'series', 'television', 'mini']
            if any(word in name_lower for word in award_words):
                return False
        
        single_banned = [
            'twitter', 'retweet', 'hashtag', 'goldenglobes', 'watch', 'tonight', 'stage',
            'stumbles', 'award', 'wins', 'winner'
        ]
        if any(word in name_lower.split() for word in single_banned):
            return False
        
        banned_people = ['josh groban']
        if name_lower in banned_people:
            return False
        
        non_person_indicators = ['of', 'the', 'in', 'for', 'and', 'to', 'while', 'during']
        if sum(1 for word in non_person_indicators if word in name_lower.split()) >= 2:
            return False
        
        if len(name) < 4 or len(name) > 50:
            return False
        
        spacy_valid = self.validatePersonWithSpacy(name)
        
        if spacy_valid:
            return True
        
        tokens_lower = [t.lower() for t in tokens]
        non_name_words = ['should', 'have', 'just', 'as', 'she', 'he', 'they', 'them', 'two', 'steaks', 'stunning']
        if any(word in tokens_lower for word in non_name_words):
            return False
        
        return False 
    
    def validatePersonWithSpacy(self, name: str) -> bool:
        try:
            doc = self.getNLP()(name)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return True

            if all(token.pos_ == "PROPN" for token in doc if not token.is_punct):
                return True
            
            return False
        except Exception:
            return True
    
    def validatePersonWithNLTK(self, name: str) -> bool:
        try:
            tokens = word_tokenize(name)
            pos_tags = nltk.pos_tag(tokens)
            proper_noun_count = sum(1 for _, pos in pos_tags if pos in ['NNP', 'NNPS'])
            if proper_noun_count == 0:
                return False
            
            return True
        except Exception:
            return True
    
    def match_tweet_to_award(self, text: str) -> Optional[str]:
        normalized = normalize_text(text)
        
        award = match_award(normalized)
        if award:
            return award
        
        award = coarse_match_award(normalized)
        if award:
            return award
        
        return None
    
    def extract_presenters_with_temporal(self, tweets: List[dict]) -> Dict[str, List[str]]:
        sorted_tweets = sorted(tweets, key=lambda t: t.get('timestamp_ms', 0))
        
        award_winner_times = defaultdict(list)
        
        presenter_mentions = defaultdict(lambda: defaultdict(list))
        

        winner_keywords = ['wins', 'won', 'winner', 'takes', 'goes to', 'award goes to']
        processed = 0
        total_tweets = len(sorted_tweets)
        for i, tweet in enumerate(sorted_tweets):
            text = tweet.get('text', '')
            if not text:
                continue
            

            if i > 0 and i % 20000 == 0:
                percent = (i / total_tweets) * 100
            
            normalized = normalize_text(text)
            timestamp = tweet.get('timestamp_ms', 0)
            

            if any(keyword in normalized for keyword in winner_keywords):
                award = self.match_tweet_to_award(normalized)
                if award:
                    award_winner_times[award].append(timestamp)
                    processed += 1
        

        award_median_times = {}
        for award, times in award_winner_times.items():
            if times:
                times_sorted = sorted(times)
                median_idx = len(times_sorted) // 2
                award_median_times[award] = times_sorted[median_idx]
        

        presenter_tweets_found = 0
        for i, tweet in enumerate(sorted_tweets):
            text = tweet.get('text', '')
            if not text:
                continue
            

            if i > 0 and i % 20000 == 0:
                percent = (i / total_tweets) * 100
            
            timestamp = tweet.get('timestamp_ms', 0)
            

            if not self.is_presenter_tweet(text):
                continue
            

            award = self.match_tweet_to_award(text)
            if not award:
                continue
            


            if award in award_median_times:
                if timestamp > award_median_times[award] + 7200000:
                    continue
            

            persons = self.extract_person_names(text)
            if persons:
                presenter_tweets_found += 1
                for person in persons:
                    presenter_mentions[award][person].append(timestamp)
        
        

        result = {}
        for award in AWARD_NAMES:
            if award in presenter_mentions:

                presenter_counts = Counter()
                for person, timestamps in presenter_mentions[award].items():

                    count = len(timestamps)

                    if count >= 2:
                        timestamps_sorted = sorted(timestamps)

                        for i in range(len(timestamps_sorted) - 1):
                            if timestamps_sorted[i+1] - timestamps_sorted[i] < 600000:
                                count += 0.5
                    presenter_counts[person] = count
                

                top_presenters = [name for name, _ in presenter_counts.most_common(4)]
                

                filtered = top_presenters[:2]
                

                result[award] = [name.lower() for name in filtered]
            else:
                result[award] = []
        
        return result
    
    def extract_presenters_simple(self, tweets: List[dict]) -> Dict[str, List[str]]:
        presenter_mentions = defaultdict(lambda: Counter())
        
        total_tweets = len(tweets)
        presenter_tweets_found = 0
        
        for i, tweet in enumerate(tweets):
            text = tweet.get('text', '')
            if not text:
                continue
            

            if i > 0 and i % 20000 == 0:
                percent = (i / total_tweets) * 100
            

            if not self.is_presenter_tweet(text):
                continue
            

            award = self.match_tweet_to_award(text)
            if not award:
                continue
            

            persons = self.extract_person_names(text)
            if persons:
                presenter_tweets_found += 1
                for person in persons:
                    presenter_mentions[award][person] += 1
        
        

        result = {}
        for award in AWARD_NAMES:
            if award in presenter_mentions:

                top_presenters = [name for name, count in presenter_mentions[award].most_common(2)]

                result[award] = [name.lower() for name in top_presenters]
            else:
                result[award] = []
        
        return result
    
    def extract_presenters_hybrid(self, tweets: List[dict]) -> Dict[str, List[str]]:

        temporal_result = self.extract_presenters_with_temporal(tweets)
        
        simple_result = self.extract_presenters_simple(tweets)
        

        result = {}
        for award in AWARD_NAMES:
            temporal_presenters = temporal_result.get(award, [])
            simple_presenters = simple_result.get(award, [])
            
            if temporal_presenters:

                result[award] = temporal_presenters
            elif simple_presenters:

                result[award] = simple_presenters
            else:

                result[award] = []
        
        result = self.removeWinnersFromPresenters(result)
        
        return result
    
    def removeWinnersFromPresenters(self, results: Dict[str, List[str]]) -> Dict[str, List[str]]:

        winners = self.loadWinners()
        
        if not winners:
            return results
        

        cleaned_results = {}
        removed_count = 0
        
        for award, presenters in results.items():
            if not presenters:
                cleaned_results[award] = []
                continue
            

            winner = winners.get(award, "").lower()
            
            if winner:

                cleaned_presenters = []
                for presenter in presenters:
                    if presenter not in winner and not self.namesMatch(presenter, winner):
                        cleaned_presenters.append(presenter)
                    else:
                        removed_count += 1
                
                cleaned_results[award] = cleaned_presenters
            else:
                cleaned_results[award] = presenters
        
        if removed_count > 0:
            pass
        
        return cleaned_results
    
    def namesMatch(self, name1: str, name2: str) -> bool:

        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        

        if n1 == n2:
            return True
        

        n1_normalized = n1.replace('-', ' ').replace('  ', ' ')
        n2_normalized = n2.replace('-', ' ').replace('  ', ' ')
        
        if n1_normalized == n2_normalized:
            return True
        

        if n1 in n2 or n2 in n1:
            return True
        

        if n1_normalized in n2_normalized or n2_normalized in n1_normalized:
            return True
        

        n1_parts = n1_normalized.split()
        n2_parts = n2_normalized.split()
        

        if len(n1_parts) >= 2 and len(n2_parts) >= 2:
            if n1_parts[-1] == n2_parts[-1] and n1_parts[0] == n2_parts[0]:
                return True
        
        return False
    
    def loadWinners(self) -> Dict[str, str]:
        winners = {}
        

        try:
            import json
            with open(f"winners_{YEAR}.json", "r") as f:
                winners = json.load(f)
                return winners
        except Exception:
            pass
        

        try:
            from .winners import compute_winners_from_file
            winners = compute_winners_from_file(f"gg{YEAR}.json")
            return winners
        except Exception as e:
            return {}
        
    
    def extractForSpecificAward(self, tweets: List[dict], target_award: str) -> List[str]:
        presenter_counts = Counter()
        

        for tweet in tweets:
            text = tweet.get('text', '')
            if not text:
                continue
            
            normalized = normalize_text(text)
            

            award = self.match_tweet_to_award(normalized)
            if award != target_award:
                continue
            

            if self.is_presenter_tweet(text):
                persons = self.extract_person_names(text)
                for person in persons:
                    presenter_counts[person] += 1
        

        if presenter_counts:
            return [name.lower() for name, _ in presenter_counts.most_common(2)]
        return []
def compute_presenters_from_file(tweets_file: str, use_temporal: bool = False) -> Dict[str, List[str]]:
    with open(tweets_file, 'r') as f:
        tweets = json.load(f)
    
    extractor = PresenterExtractor()
    presenters = extractor.extract_presenters_simple(tweets)
    

    presenters = extractor.removeWinnersFromPresenters(presenters)
    
    
    return presenters


__all__ = [
    "compute_presenters_from_file",
]
