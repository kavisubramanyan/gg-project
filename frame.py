import typesys
from extraction import clean_tweets, extract_people, tweet_data

print("Number of tweets:", len(tweet_data))

# Create ceremony
ceremony = typesys.AwardCeremony(name="Golden Globes", year=2013)

# Extract all people from all tweets
entity_id = 1
for tweet in tweet_data:
    cleaned = clean_tweets(tweet.get("text", ""))
    people = extract_people(cleaned)
    # Just create Person objects, don't assign them anywhere
    for person_name in people:
        person = typesys.Person(id=entity_id, name=person_name)
        entity_id += 1

print(f"Processed {entity_id - 1} person entities")
print(ceremony)