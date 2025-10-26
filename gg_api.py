# '''Version 0.5'''

from collections import defaultdict
import json
from typing import Dict

from api.winners import compute_winners_from_file
from api.hosts import compute_hosts_from_file
from api.presenters import compute_presenters_from_file
from api.nominees import compute_nominees_from_file
from constants import YEAR, AWARD_NAMES
from api.awards import compute_awards_from_file
from api.sentiment import compute_sentiments_from_file, compute_per_entity_sentiments_from_file


def ensure_pre_ceremony():
    import sys
    main_module = sys.modules.get('__main__')
    if not hasattr(main_module, '_spacy_nlp'):
        pre_ceremony()

def get_hosts(year):
    '''Returns the host(s) of the Golden Globes ceremony for the given year.
    
    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")
    
    Returns:
        list: A list of strings containing the host names. 
              Example: ["Seth Meyers"] or ["Tina Fey", "Amy Poehler"]
    
    Note:
        - Do NOT change the name of this function or what it returns
        - The function should return a list even if there's only one host
    '''
    ensure_pre_ceremony()

    try:
        with open(f"cache/hosts_{year}.json", "r") as f:
            hosts = json.load(f)
            if isinstance(hosts, list):
                return hosts
    except Exception:
        pass

    print("Computing hosts...")
    try:
        hosts = compute_hosts_from_file(f"gg{year}.json")
        with open(f"cache/hosts_{year}.json", "w") as f:
            json.dump(hosts, f)
    except Exception:
        hosts = []
    return hosts


def get_awards(year):
    '''Returns the list of award categories for the Golden Globes ceremony.
    
    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")
    
    Returns:
        list: A list of strings containing award category names.
              Example: ["Best Motion Picture - Drama", "Best Motion Picture - Musical or Comedy", 
                       "Best Performance by an Actor in a Motion Picture - Drama"]
    
    Note:
        - Do NOT change the name of this function or what it returns
        - Award names should be extracted from tweets, not hardcoded
        - The only hardcoded part allowed is the word "Best"
    '''
    ensure_pre_ceremony()
    
    try:
        with open(f"cache/awards_{year}.json", "r") as f:
            awards = json.load(f)
            if isinstance(awards, list):
                return awards
    except Exception:
        pass

    print("Computing awards...")
    try:
        awards = compute_awards_from_file(f"gg{year}.json")
        with open(f"cache/awards_{year}.json", "w") as f:
            json.dump(awards, f)
    except Exception as e:
        print(f"Error computing awards: {e}")
        awards = []
    return awards


def get_nominees(year):
    '''Returns the nominees for each award category.
    
    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")
    
    Returns:
        dict: A dictionary where keys are award category names and values are 
              lists of nominee strings.
              Example: {
                  "Best Motion Picture - Drama": [
                      "Three Billboards Outside Ebbing, Missouri",
                      "Call Me by Your Name", 
                      "Dunkirk",
                      "The Post",
                      "The Shape of Water"
                  ],
                  "Best Motion Picture - Musical or Comedy": [
                      "Lady Bird",
                      "The Disaster Artist",
                      "Get Out",
                      "The Greatest Showman",
                      "I, Tonya"
                  ]
              }
    
    Note:
        - Do NOT change the name of this function or what it returns
        - Use the hardcoded award names as keys (from the global AWARD_NAMES list)
        - Each value should be a list of strings, even if there's only one nominee
    '''
    ensure_pre_ceremony()

    try:
        with open(f"cache/nominees_{year}.json", "r") as f:
            nominees = json.load(f)
            if isinstance(nominees, dict):
                return nominees
    except Exception:
        pass

    print("Computing nominees...")
    try:
        nominees = compute_nominees_from_file(f"gg{year}.json")
        completed = {name: nominees.get(name, []) for name in AWARD_NAMES}
        with open(f"cache/nominees_{year}.json", "w") as f:
            json.dump(completed, f)
        return completed
    except Exception as e:
        print(f"Error computing nominees: {e}")
        empty_completed = {name: [] for name in AWARD_NAMES}
        return empty_completed


def get_winner(year):
    '''Returns the winner for each award category.
    
    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")
    
    Returns:
        dict: A dictionary where keys are award category names and values are 
              single winner strings.
              Example: {
                  "Best Motion Picture - Drama": "Three Billboards Outside Ebbing, Missouri",
                  "Best Motion Picture - Musical or Comedy": "Lady Bird",
                  "Best Performance by an Actor in a Motion Picture - Drama": "Gary Oldman"
              }
    
    Note:
        - Do NOT change the name of this function or what it returns
        - Use the hardcoded award names as keys (from the global AWARD_NAMES list)
        - Each value should be a single string (the winner's name)
    '''
    ensure_pre_ceremony()
    
    winners: Dict[str, str] = {}
    try:
        with open(f"cache/winners_{year}.json", "r") as f:
            winners = json.load(f)
    except Exception:
        print("Computing winners...")
        winners = compute_winners_from_file(f"gg{year}.json")
        completed = {name: winners.get(name, "") for name in AWARD_NAMES}
        with open(f"cache/winners_{year}.json", "w") as f:
            json.dump(completed, f)
        return completed

    completed = {name: winners.get(name, "") for name in AWARD_NAMES}
    return completed


def get_presenters(year):
    '''Returns the presenters for each award category.
    
    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")
    
    Returns:
        dict: A dictionary where keys are award category names and values are 
              lists of presenter strings.
              Example: {
                  "Best Motion Picture - Drama": ["Barbra Streisand"],
                  "Best Motion Picture - Musical or Comedy": ["Alicia Vikander", "Michael Keaton"],
                  "Best Performance by an Actor in a Motion Picture - Drama": ["Emma Stone"]
              }
    
    Note:
        - Do NOT change the name of this function or what it returns
        - Use the hardcoded award names as keys (from the global AWARD_NAMES list)
        - Each value should be a list of strings, even if there's only one presenter
    '''
    ensure_pre_ceremony()
    
    try:
        with open(f"cache/presenters_{year}.json", "r") as f:
            presenters = json.load(f)
            if isinstance(presenters, dict):
                completed = {name: presenters.get(name, []) for name in AWARD_NAMES}
                return completed
    except Exception:
        pass
    
    print("Computing presenters...")
    try:
        presenters = compute_presenters_from_file(f"gg{year}.json")
    except Exception as e:
        print(f"Error computing presenters: {e}")
        presenters = defaultdict(list)
    
    completed = {name: presenters.get(name, []) for name in AWARD_NAMES}
    
    with open(f"cache/presenters_{year}.json", "w") as f:
        json.dump(completed, f)
    
    return completed


def pre_ceremony():
    '''Pre-processes and loads data for the Golden Globes analysis.
    
    This function should be called before any other functions to:
    - Load and process the tweet data from gg2013.json
    - Download required models (e.g., spaCy models)
    - Perform any initial data cleaning or preprocessing
    - Store processed data in files or database for later use
    
    This is the first function the TA will run when grading.
    
    Note:
        - Do NOT change the name of this function or what it returns
        - This function should handle all one-time setup tasks
        - Print progress messages to help with debugging
    '''
    print("Pre-ceremony...")
    
    import os
    os.makedirs("cache", exist_ok=True)
    
    print("Loading spaCy model...")
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        print("spaCy model loaded successfully")
    except OSError:
        print("Downloading spaCy model en_core_web_sm...")
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
        nlp = spacy.load("en_core_web_sm")
        print("spaCy model downloaded and loaded successfully")
    

    print("Downloading NLTK data...")
    import nltk
    nltk.download('punkt_tab', quiet=True)
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        nltk.download('averaged_perceptron_tagger', quiet=True)
    
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger_eng')
    except LookupError:
        nltk.download('averaged_perceptron_tagger_eng', quiet=True)
    try:
        nltk.data.find('sentiment/vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
    print("NLTK data downloaded successfully")
    
    import sys
    sys.modules['__main__']._spacy_nlp = nlp
    
    print("Pre-ceremony complete.")
    return


def main():
    '''Main function that orchestrates the Golden Globes analysis.
    
    This function should:
    - Call pre_ceremony() to set up the environment
    - Run the main analysis pipeline
    - Generate and save results in the required JSON format
    - Print progress messages and final results
    
    Usage:
        - Command line: python gg_api.py
        - Python interpreter: import gg_api; gg_api.main()
    
    This is the second function the TA will run when grading.
    
    Note:
        - Do NOT change the name of this function or what it returns
        - This function should coordinate all the analysis steps
        - Make sure to handle errors gracefully
    '''

    pre_ceremony()

    import os
    
    # Winners
    if os.path.exists(f"cache/winners_{YEAR}.json"):
        print("Using cached winners data...")
    else:
        print("Computing winners...")
        winners = compute_winners_from_file(f"gg{YEAR}.json")
        completed = {name: winners.get(name, "") for name in AWARD_NAMES}
        with open(f"cache/winners_{YEAR}.json", "w") as f:
            json.dump(completed, f)
        
    
    # Hosts
    if os.path.exists(f"cache/hosts_{YEAR}.json"):
        print("Using cached hosts data...")
    else:
        print("Computing hosts...")
        try:
            from api.hosts import compute_hosts_from_file as _compute_hosts_from_file
            hosts = _compute_hosts_from_file(f"gg{YEAR}.json")
            with open(f"cache/hosts_{YEAR}.json", "w") as f:
                json.dump(hosts, f)
            
        except Exception as e:
            print(f"Warning: Could not compute hosts: {e}")
    
    # Presenters
    if os.path.exists(f"cache/presenters_{YEAR}.json"):
        print("Using cached presenters data...")
    else:
        print("Computing presenters...")
        try:
            presenters = compute_presenters_from_file(f"gg{YEAR}.json")
            completed_presenters = {name: presenters.get(name, []) for name in AWARD_NAMES}
            with open(f"cache/presenters_{YEAR}.json", "w") as f:
                json.dump(completed_presenters, f)
            
        except Exception as e:
            print(f"Warning: Could not compute presenters: {e}")

    # Awards
    if os.path.exists(f"cache/awards_{YEAR}.json"):
        print("Using cached awards data...")
    else:
        print("Computing awards...")
        try:
            awards = compute_awards_from_file(f"gg{YEAR}.json")
            with open(f"cache/awards_{YEAR}.json", "w") as f:
                json.dump(awards, f)
        except Exception as e:
            print(f"Warning: Could not compute awards: {e}")

    # Nominees
    if os.path.exists(f"cache/nominees_{YEAR}.json"):
        print("Using cached nominees data...")
    else:
        print("Computing nominees...")
        try:
            nominees = compute_nominees_from_file(f"gg{YEAR}.json")
            completed_nominees = {name: nominees.get(name, []) for name in AWARD_NAMES}
            with open(f"cache/nominees_{YEAR}.json", "w") as f:
                json.dump(completed_nominees, f)
            
        except Exception as e:
            print(f"Warning: Could not compute nominees: {e}")

    generate_output_formats()

    return


def generate_output_formats():
    print("Generating output formats...")
    
    try:
        with open(f"cache/hosts_{YEAR}.json", "r") as f:
            hosts = json.load(f)
    except Exception:
        hosts = []
    host_candidates = []
    
    try:
        with open(f"cache/awards_{YEAR}.json", "r") as f:
            extracted_awards = json.load(f)
    except Exception:
        extracted_awards = []
    
    nominees = {}
    try:
        with open(f"cache/nominees_{YEAR}.json", "r") as f:
            nominees = json.load(f)
    except Exception:
        nominees = {}
    nominee_candidates = {}
    
    try:
        with open(f"cache/presenters_{YEAR}.json", "r") as f:
            presenters = json.load(f)
    except Exception:
        presenters = {}
    presenter_candidates = {}
    
    try:
        with open(f"cache/winners_{YEAR}.json", "r") as f:
            winners = json.load(f)
    except Exception:
        winners = {}
    
    sentiments = compute_sentiments_from_file(f"gg{YEAR}.json", winners, presenters)
    per_entity_sentiments = compute_per_entity_sentiments_from_file(f"gg{YEAR}.json", winners, presenters)
    winner_candidates = {}
    
    human_output = []
    
    if hosts:
        host_name = hosts[0] if hosts else "Unknown"
        human_output.append(f"Host: \"{host_name}\"")
        
    else:
        human_output.append("Host: \"Unknown\"")
    
    human_output.append("")
    
    if extracted_awards:
        awards_str = ", ".join([f'"{award}"' for award in extracted_awards])
        human_output.append(f"Awards: {awards_str}")
    else:
        human_output.append("Awards: \"award_1\", \"award_2\", \"award_3\"")
    
    human_output.append("") 
    

    for award_name in AWARD_NAMES:
        human_output.append(f"Award: \"{award_name.title()}\"")
        

        award_presenters = presenters.get(award_name, [])
        if award_presenters:
            presenter_name = award_presenters[0]
            human_output.append(f"Presenters: \"{presenter_name}\"")
        else:
            human_output.append("Presenters: \"Unknown\"")
        
        

        award_nominees = nominees.get(award_name, [])
        if award_nominees:
            nominees_str = ", ".join([f'"{nominee}"' for nominee in award_nominees])
            human_output.append(f"Nominees: {nominees_str}")
        else:
            human_output.append("Nominees: []")
        
        

        winner = winners.get(award_name, "")
        if winner:
            human_output.append(f"Winner: \"{winner}\"")
        else:
            human_output.append("Winner: \"Unknown\"")
        
        
        human_output.append("")  
        w_det = per_entity_sentiments.get("winners", {}).get(award_name, {"label": "neutral", "example": ""})
        p_det = per_entity_sentiments.get("presenters", {}).get(award_name, {"label": "neutral", "example": ""})
        human_output.append(
            f"Winner Sentiment: {w_det.get('label','neutral').title()}" +
            (f" (e.g., \"{w_det.get('example','')}\")" if w_det.get('example') else "")
        )
        human_output.append(
            f"Presenter Sentiment: {p_det.get('label','neutral').title()}" +
            (f" (e.g., \"{p_det.get('example','')}\")" if p_det.get('example') else "")
        )
        human_output.append("")
    
    w_sent = sentiments.get("winners", {"label": "neutral", "example": ""})
    p_sent = sentiments.get("presenters", {"label": "neutral", "example": ""})
    human_output.append(f"Winner Sentiment: {w_sent['label'].title()}")
    human_output.append(f"Presenter Sentiment: {p_sent['label'].title()}")
    human_output.append("")

    with open("results.txt", "w") as f:
        f.write("\n".join(human_output))
    
    json_output = {}
    
    if hosts:
        json_output["host"] = hosts[0]
    else:
        json_output["host"] = "Unknown"
    
    if extracted_awards:
        json_output["awards"] = extracted_awards
    else:
        json_output["awards"] = ["award_1", "award_2", "award_3"]
    
    for award_name in AWARD_NAMES:
        award_data = {}
        
        award_presenters = presenters.get(award_name, [])
        if award_presenters:
            award_data["presenters"] = award_presenters
        else:
            award_data["presenters"] = ["Unknown"]
        
        award_nominees = nominees.get(award_name, [])
        award_data["nominees"] = award_nominees
        
        winner = winners.get(award_name, "")
        if winner:
            award_data["winner"] = winner
        else:
            award_data["winner"] = "Unknown"
        
        json_output[award_name.title()] = award_data
    
    # Sentiment summary and per-entity details added to JSON
    json_output["sentiment"] = {
        "summary": {
            "winners": w_sent.get("label", "neutral"),
            "presenters": p_sent.get("label", "neutral"),
        },
        "winners": per_entity_sentiments.get("winners", {}),
        "presenters": per_entity_sentiments.get("presenters", {}),
    }
    
    with open("results.json", "w") as f:
        json.dump(json_output, f, indent=2)
    
    print("Outputs generated successfully.")
    print("Human-readable format saved to: results.txt")
    print("JSON format saved to: results.json")


if __name__ == '__main__':
    main()

