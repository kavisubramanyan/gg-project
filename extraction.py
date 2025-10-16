import re
from inflection import humanize, underscore
import json
import spacy
import ftfy
from unidecode import unidecode
from langdetect import detect, DetectorFactory, detect_langs
DetectorFactory.seed = 0
import datetime
# detect_langs detects the most probable langiages and prob.

nlp = spacy.load("en_core_web_sm")

##### get the data 
with open("sample_text.json", "r", encoding="utf-8") as f:
    raw_tweet_data = json.load(f)

AWARD_NAMES = [
    "best screenplay - motion picture",
    "best director - motion picture",
    "best performance by an actress in a television series - comedy or musical",
    "best foreign language film",
    "best performance by an actor in a supporting role in a motion picture",
    "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television",
    "best motion picture - comedy or musical",
    "best performance by an actress in a motion picture - comedy or musical",
    "best mini-series or motion picture made for television",
    "best original score - motion picture",
    "best performance by an actress in a television series - drama",
    "best performance by an actress in a motion picture - drama",
    "cecil b. demille award",
    "best performance by an actor in a motion picture - comedy or musical",
    "best motion picture - drama",
    "best performance by an actor in a supporting role in a series, mini-series or motion picture made for television",
    "best performance by an actress in a supporting role in a motion picture",
    "best television series - drama",
    "best performance by an actor in a mini-series or motion picture made for television",
    "best performance by an actress in a mini-series or motion picture made for television",
    "best animated feature film",
    "best original song - motion picture",
    "best performance by an actor in a motion picture - drama",
    "best television series - comedy or musical",
    "best performance by an actor in a television series - drama",
    "best performance by an actor in a television series - comedy or musical"
]


##### get the list of tweets, tweet_id, and timestamps
tweets = []
tweet_id = []
timestamp = []

for t in raw_tweet_data:
    tweets.append(t.get("text"))
    tweet_id.append(t.get("id"))
    timestamp.append(t.get("timestamp_ms"))


def hashtags_usernames(tweet):
    usernames = re.findall(r"@(\w+)", tweet)
    hashtags = re.findall(r"#(\w+)", tweet)

    for part_list in [usernames, hashtags]:
        for part in part_list:
            snake_name = part if "_" in part else underscore(part)
            readable = humanize(snake_name)
            tweet = tweet.replace(f"@{part}", readable)
            tweet = tweet.replace(f"#{part}", readable)

    # this hard codes the goldenglobes ahshatag to be parsed
    ### do we need to do this for other instances?
    tweet = re.sub(r"\bGoldenglobes\b", "Golden globes", tweet, flags=re.IGNORECASE)
    return tweet


##### clean up the tweets before we try to use spacy
def clean_tweets(tweet):
    # fix text encoding issues (from slides)
    tweet = ftfy.fix_text(tweet)
    # fixes unicode to ascii (from slides)
    tweet = unidecode(tweet)
    # we can remove the URls
    tweet = re.sub(r"http\S+", "", tweet)
    # # we can remove the hashtag icon
    # tweet = re.sub(r"#", "", tweet)
    # # and also the @s and mentions
    # tweet = re.sub(r"@\w+", "", tweet)
    
    # do this instead 
    tweet = hashtags_usernames(tweet)

    # we can remove ":"
    tweet = re.sub(r":", "", tweet)
    # # remove retweets
    # tweet = re.sub(r"\bRT\b", "", tweet)
    # we can remove emojis and the ascii symbols
    tweet = re.sub(r"[^\x00-\x7F]+", " ", tweet)
    # check for spaces?
    # substitue all whitespaces
    tweet = " ".join(tweet.split())
    # code to keep tabs/newline characters
    tweet = re.sub(' +', ' ', tweet)

    # # ensure in english - moved to extract people
    # try:
    #     if detect(tweet) != "en":
    #         return ""
    # except:
    #     return ""

    return tweet


########### this is the cleaned tweet text 
cleaned_tweets = []
for tweet in tweets:
    cleaned_tweets.append(clean_tweets(tweet))


###### looking at the clean text
# print(cleaned_tweets)

##### now we can use nlp for specific functions
def extract_people(tweet):
    # # ensure in english
    try:
        if detect(tweet) != "en":
            return []
    except:
        pass
    
    doc = nlp(tweet)
    people = []

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # removes weird spacing
            name = ent.text.strip()
            # Filters to remove false positives
            if (# helps remove shorter names 
                len(name) > 2     
                # helps remove anything that is in all caps                             
                and not name.isupper()     
                # we can remove words we see arent names                  
                and not any(word.lower() in ["rt", "fab", "golden", "miu"] for word in name.split())):
                people.append(name)

    # take off the colon
    people = [re.sub(r"'s$", "", p) for p in people]

    return people 


##### helps test the extract_people works:
# for clean_tweet in cleaned_tweets:
#     people = extract_people(clean_tweet)
#     if people:
#         print(people)


##### gets award names in each tweet
def extract_award_names(tweet):
    instances_of_awards = []
    text = nlp(tweet.lower())
    tokens = {token.lemma_ for token in text if not token.is_stop}
    
    for award in AWARD_NAMES:
        # fixes the dashes - might need
        award_lower = award.replace("–", "-").replace("—", "-")
        award_txt = nlp(award_lower)
        award_words = [
            word.lemma_ for word in award_txt 
            if word.is_alpha and word.text not in {"by", "an", "in", "a", "the", "of"}
        ]
        # check how many words from the award are found in the tweet
        matching = sum(1 for w in award_words if w in tokens)

        # helps shorter awards still match
        if matching >= 3 or (len(award_words) <= 5 and matching >= 2):
            instances_of_awards.append(award)
    return instances_of_awards

# ##### helps test the extract_award_names works:
# for clean_tweet in cleaned_tweets:
#     awards = extract_award_names(AWARD_NAMES, clean_tweet)
#     print(awards)



##### gets buzzwords in each tweet
BUZZWORDS = ["win", "winner", "won", "nominee", "nominated", "award", "awards", "best" "performance", "role", "actor", "actress", "director",
    "film", "movie", "show", "series", "screenplay", "amazing", "deserved", "snubbed", "robbed", "proud",
    "stunning", "brilliant", "incredible", "iconic", "powerful", "speech", "redcarpet", "dress", "host", "presenter",
    "stage", "moment", "applause", "crowd", "look", "congrats", "celebrate", "party", "cheers"]


def extract_buzzwords (tweet):
    found_buzzwords = []
    # gets clean words
    words = re.findall(r'\b\w+\b', tweet.lower()) 
    for word in words:
        if word in BUZZWORDS:
            found_buzzwords.append(word)
    return found_buzzwords

# for clean_tweet in cleaned_tweets:
#     buzz = extract_buzzwords(BUZZWORDS, clean_tweet)
#     print(buzz)


####### class of each tweet
class Tweet:
    def __init__(self, tweets, cleaned_tweet, tweet_id, timestamp):
        self.text = cleaned_tweet
        self.tweet_id = tweet_id
        self.timestamp = timestamp

        # extracted info
        self.people = extract_people(cleaned_tweet)
        self.awards = extract_award_names(cleaned_tweet)
        self.buzzwords = extract_buzzwords(cleaned_tweet)
        self.hashtags = re.findall(r"#(\w+)", tweets)

tweet_objects = []
for i in range(len(tweets)):
    raw = tweets[i]
    cleaned = cleaned_tweets[i]
    tw = Tweet(raw, cleaned, tweet_id[i], timestamp[i])
    tweet_objects.append(tw)



for t in tweet_objects:
    print("=" * 60)
    print(f"Tweet ID: {t.tweet_id}")
    print(f"Timestamp: {t.timestamp}")
    print(f"Text: {t.text}")
    print(f"People: {t.people if t.people else 'None'}")
    print(f"Awards: {t.awards if t.awards else 'None'}")
    print(f"Buzzwords: {t.buzzwords if t.buzzwords else 'None'}")
    print(f"Hashtags: {t.hashtags if t.hashtags else 'None'}")

