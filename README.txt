Golden Globes Project — Group X (Template)
==========================================

Python Version
--------------
Tested with **Python 3.10**. Please use Python 3.10 for grading/running.

Quick Start
-----------
# 1) Create a clean environment (option A: requirements.txt)
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 1b) OR (option B: environment.yml via conda/mamba)
mamba env create -f environment.yml   # or: conda env create -f environment.yml
mamba activate gg-golden-globes       # or: conda activate gg-golden-globes

# 2) (Optional) Download external NLP models/resources we use
python scripts/download_models.py

# 3) Run the pipeline (example for 2013 data placed under ./data/raw/gg2013.json)
bash scripts/run_pipeline.sh 2013

# 4) Check outputs
- Human-readable report: output/report_2013.txt
- Autograder JSON:      output/results_2013.json

GitHub Repository
-----------------
Public repo URL: <ADD YOUR PUBLIC GITHUB URL HERE>

We commit regularly. When pair programming, we note participants in the commit
message, e.g., "pair: Alice, Bob".

Autograder Integration
----------------------
We rely on the provided autograder in the central repo: 
https://github.com/simon-benigeri/gg-project

Our file `gg_api.py` implements the required functions for the autograder.
It simply **loads the JSON produced by our pipeline** (e.g. output/results_2013.json)
and returns values by key.

Environment & Dependencies
--------------------------
- Do **not** run a raw `pip freeze > requirements.txt`. Our requirements.txt lists only the necessary packages.
- If you use a different Python version locally, please still test with Python 3.10.
- If using MongoDB, ensure a local instance is running (default URI in `mongo/load_mongo.py`), then run:
  python mongo/load_mongo.py --year 2013 --in data/raw/gg2013.json

External Model Downloads
------------------------
If you use spaCy/NLTK, we include a helper:
    python scripts/download_models.py

It downloads:
- spaCy: en_core_web_sm
- NLTK: punkt, stopwords, vader_lexicon, averaged_perceptron_tagger

Required Output Formats
-----------------------
We produce **two** outputs:

1) Human-readable (output/report_<year>.txt)
   Contains host, award lists, per-award presenters/nominees/winners, plus any additional goals
   (e.g., best dressed, sentiment summaries). For award-dependent info, we use the course-provided
   hardcoded award list as the section headers, and we fill values found by the pipeline.
   (Award-name mining itself cannot hardcode more than the word "Best".)

2) Autograder JSON (output/results_<year>.json)
   Strictly the minimum tasks in standardized JSON. Example structure is in output/results_2013.json.
   The autograder calls our functions in `gg_api.py`, which read that JSON.

How to Run the Autograder Against Our Output
--------------------------------------------
Follow the steps in the central repo. Typically:
- Place our output JSON at: output/results_<year>.json
- Ensure `gg_api.py` is present in the root of this submission (zip) and in the GitHub repo.

MongoDB (Optional)
------------------
If you choose to use MongoDB, we include:
- `mongo/load_mongo.py` to ingest tweets into a collection.
- Queries are documented in comments for reproducibility.

Runtime
-------
Our pipeline completes in under 10 minutes for a single year on a typical laptop.
Heavy steps (e.g., model loading) are cached when possible.

Submission Packaging
--------------------
Before zipping, rename your top-level directory to include your group number, e.g.:
    gg-project-group1
Then zip that directory and upload to Canvas.

Files to Run
------------
Primary entry point:
    python src/build_dataset.py --year 2013 --in data/raw/gg2013.json --out output/results_2013.json

A convenience wrapper is provided:
    bash scripts/run_pipeline.sh 2013

PEP8 Imports
------------
We follow PEP8 import guidelines: stdlib, then third-party, then local imports.
See: https://www.python.org/dev/peps/pep-0008/#imports

Notes
-----
- We do **not** read gg2013answers.json in our code.
- We keep a `CITATIONS.md` noting any outside repos we looked at for ideas (not code).
