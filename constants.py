YEAR = "2013"
AWARD_NAMES = [
    "best motion picture - drama",
    "best motion picture - comedy or musical",
    "best performance by an actor in a motion picture - drama",
    "best performance by an actress in a motion picture - drama",
    "best performance by an actor in a motion picture - comedy or musical",
    "best performance by an actress in a motion picture - comedy or musical",
    "best performance by an actor in a supporting role in a motion picture",
    "best performance by an actress in a supporting role in a motion picture",
    "best director - motion picture",
    "best screenplay - motion picture",
    "best original score - motion picture",
    "best original song - motion picture",
    "best animated feature film",
    "best foreign language film",
    "best television series - drama",
    "best television series - comedy or musical",
    "best mini-series or motion picture made for television",
    "best performance by an actor in a television series - drama",
    "best performance by an actress in a television series - drama",
    "best performance by an actor in a television series - comedy or musical",
    "best performance by an actress in a television series - comedy or musical",
    "best performance by an actor in a mini-series or motion picture made for television",
    "best performance by an actress in a mini-series or motion picture made for television",
    "best performance by an actor in a supporting role in a series, mini-series or motion picture made for television",
    "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television",
    "cecil b. demille award",
]

WINNER_VERBS = [
    "wins", "won", "winner", "takes", "took", "goes to", "goes-to",
    "accepts", "accepted", "congrats", "congratulations", "awarded", "award goes to",
    "best goes to", "picks up", "takes home", "snags", "grabs", "nabs",
]

URL_PATTERN = r"https?://\S+|www\.\S+"
USER_PATTERN = r"@\w+"
MULTISPACE_PATTERN = r"\s+"
HASHTAG_PATTERN = r"#\w+"
QUOTED_SPAN_PATTERN = r'"([^"\n]{2,})' + r'"'
PERSON_LIKE_PATTERN = r"^(?:[A-Z][a-z]+\s){1,3}[A-Z][a-z]+$"

AWARD_ALIASES = {
    "best motion picture - drama": ["best picture drama", "best motion picture drama", "best film drama"],
    "best motion picture - comedy or musical": ["best picture musical", "best picture comedy", "best motion picture musical", "best motion picture comedy"],
    "best director - motion picture": ["best director"],
    "best screenplay - motion picture": ["best screenplay"],
    "best original score - motion picture": ["best score"],
    "best original song - motion picture": ["best song"],
    "best animated feature film": ["best animated film", "best animated feature"],
    "best foreign language film": ["best foreign film"],
    "best television series - drama": ["best tv series drama", "best tv drama"],
    "best television series - comedy or musical": ["best tv series comedy", "best tv comedy", "best tv musical"],
    "best mini-series or motion picture made for television": ["best miniseries", "best tv movie", "best limited series"],
    "best performance by an actor in a motion picture - drama": ["best actor drama", "actor drama"],
    "best performance by an actress in a motion picture - drama": ["best actress drama", "actress drama"],
    "best performance by an actor in a motion picture - comedy or musical": ["best actor comedy", "actor musical", "actor comedy"],
    "best performance by an actress in a motion picture - comedy or musical": ["best actress comedy", "actress musical", "actress comedy"],
    "best performance by an actor in a supporting role in a motion picture": ["best supporting actor"],
    "best performance by an actress in a supporting role in a motion picture": ["best supporting actress"],
    "best performance by an actor in a television series - drama": ["best actor tv drama"],
    "best performance by an actress in a television series - drama": ["best actress tv drama"],
    "best performance by an actor in a television series - comedy or musical": ["best actor tv comedy", "best actor tv musical"],
    "best performance by an actress in a television series - comedy or musical": ["best actress tv comedy", "best actress tv musical"],
    "best performance by an actor in a mini-series or motion picture made for television": ["best actor miniseries", "best actor tv movie", "best actor limited series"],
    "best performance by an actress in a mini-series or motion picture made for television": ["best actress miniseries", "best actress tv movie", "best actress limited series"],
    "best performance by an actor in a supporting role in a series, mini-series or motion picture made for television": ["best supporting actor tv"],
    "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television": ["best supporting actress tv"],
    "cecil b. demille award": ["cecil b demille", "lifetime achievement"],
}

BAD_TOKENS = {"he's", "she's", "it's", "that's", "let's", "here's", "there's", "rt"}
PERSON_BAN = {"tv", "television", "film", "movie", "series"}
GEN_NOISE = {"congrats", "congratulations", "massive", "cast", "crew", "win", "wins", "winner"}


