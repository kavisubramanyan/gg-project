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
with open("gg2013.json", "r", encoding="utf-8") as f:
    tweet_data = json.load(f)


##### get the list of tweets, tweet_id, and timestamps
tweets = []
tweet_id = []
timestamp = []

for t in tweet_data:
    tweets.append(t.get("text"))
    tweet_id.append(t.get("id"))
    timestamp.append(datetime.datetime.fromtimestamp(t.get("timestamp_ms")/1000))

#### fixing time stamp
# raw_time = example["timestamp_ms"]
# dt = datetime.datetime.fromtimestamp(raw_time/1000.0)


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

    # ensure in english
    # try:
    #     if detect(tweet) != "en":
    #         return ""
    # except:
    #     return ""

    return tweet


##### this is the plain text 
cleaned_tweets = []
for tweet in tweets:
    cleaned_tweets.append(clean_tweets(tweet))


# looking at the clean text
# print(cleaned_tweets)

##### now we can use nlp for specific functions
def extract_people(tweet):
    doc = nlp(tweet)
    # we look at nlp entities to get all the people defined
    people = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    
    # some of the people have possesive "'s" so we can remove that now
    people = [re.sub(r"'s$", "", name) for name in people]
    # return a list of people in the tweet
    return people

##### helps test the extract_people works:
# for clean_tweet in cleaned_tweets:
#     people = extract_people(clean_tweet)
#     if people:
#         print(people)
