'''Version 0.5'''
import json
import os
from new_extraction import aggregate_results

# Year of the Golden Globes ceremony being analyzed
YEAR = "2013"

# Global variable for hardcoded award names
# This list is used by get_nominees(), get_winner(), and get_presenters() functions
# as the keys for their returned dictionaries
# Students should populate this list with the actual award categories for their year, to avoid cascading errors on outputs that depend on correctly extracting award names (e.g., nominees, presenters, winner)
AWARD_NAMES = ['cecil b. demille award',
                   'best motion picture drama',
                   'best performance by an actress in a motion picture - drama',
                   'best performance by an actor in a motion picture - drama',
                   'best motion picture - comedy or musical',
                   'best performance by an actress in a motion picture - comedy or musical',
                   'best performance by an actor in a motion picture - comedy or musical',
                   'best animated feature film',
                   'best foreign language film',
                   'best performance by an actress in a supporting role in a motion picture',
                   'best performance by an actor in a supporting role in a motion picture',
                   'best director - motion picture',
                   'best screenplay - motion picture',
                   'best original score - motion picture',
                   'best original song - motion picture',
                   'best television series - drama',
                   'best performance by an actress in a television series - drama',
                   'best performance by an actor in a television series - drama',
                   'best television series - comedy or musical',
                   'best performance by an actress in a television series - comedy or musical',
                   'best performance by an actor in a television series - comedy or musical',
                   'best mini-series or motion picture made for television',
                   'best performance by an actress in a mini-series or motion picture made for television',
                   'best performance by an actor in a mini-series or motion picture made for television',
                   'best performance by an actress in a supporting role in a series, mini-series or motion picture made for television',
                   'best performance by an actor in a supporting role in a series, mini-series or motion picture made for television']

_cached_results = None
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
    # Your code here
    global _cached_results

    with open("gg2013.json", "r", encoding="utf-8") as f:
            tweets = json.load(f)
    _cached_results = aggregate_results(tweets)
    
    return _cached_results

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
    # Your code here
    results = pre_ceremony()
    return results.get("hosts", [])

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
    return pre_ceremony().get("awards", [])

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
    # Your code here
    return pre_ceremony().get("nominees", {})

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
    # Your code here
    return pre_ceremony().get("winners", {})

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
    # Your code here
    return pre_ceremony().get("presenters", {})



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
    results = pre_ceremony()
    print(json.dumps(results, indent=2, ensure_ascii=False))

    

if __name__ == '__main__':
    main()
