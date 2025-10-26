import argparse, json
from pymongo import MongoClient
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--in", dest="infile", type=Path, required=True)
    ap.add_argument("--uri", type=str, default="mongodb://localhost:27017")
    ap.add_argument("--db", type=str, default="gg_project")
    ap.add_argument("--coll", type=str, default=None, help="defaults to tweets_<year>")
    args = ap.parse_args()

    coll_name = args.coll or f"tweets_{args.year}"
    client = MongoClient(args.uri)
    db = client[args.db]
    coll = db[coll_name]
    coll.drop()

    data = json.loads(args.infile.read_text(encoding="utf-8"))
    if isinstance(data, list):
        if data:
            coll.insert_many(data)
    else:
        raise ValueError("Expected list of tweet-like objects")

    print(f"Inserted {coll.count_documents({})} documents into {args.db}.{coll_name}")

if __name__ == "__main__":
    main()
