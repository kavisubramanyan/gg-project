import json
import argparse
from pathlib import Path
from tqdm import tqdm

from utils.io import read_tweets, write_json, write_text
from extract_hosts import extract_host_and_candidates
from extract_awards import extract_awards_list
from extract_presenters import extract_presenters_by_award
from extract_nominees import extract_nominees_by_award
from extract_winners import extract_winners_by_award
from extras_fashion import compute_best_worst_dressed

from hardcoded_awards import load_hardcoded_awards

def build(year: int, in_path: Path, out_path: Path):
    tweets = read_tweets(in_path)

    # --- Minimum tasks ---
    host, host_candidates = extract_host_and_candidates(tweets)
    awards = extract_awards_list(tweets)  # your extracted list (cannot hardcode beyond the word "Best")

    presenters = extract_presenters_by_award(tweets, HARDCODED_AWARDS)
    nominees   = extract_nominees_by_award(tweets, HARDCODED_AWARDS)
    winners    = extract_winners_by_award(tweets, HARDCODED_AWARDS)

    out = {
        "host": host,
        "host_candidates": host_candidates,
        "awards": awards,
        "hard_coded_awards": HARDCODED_AWARDS,
    }
    # attach per-award blocks
    for a in HARDCODED_AWARDS:
        out[a] = {
            "presenters": presenters.get(a, []),
            "presenters_candidates": presenters.get(a + "_candidates", []),
            "nominees": nominees.get(a, []),
            "nominee_candidates": nominees.get(a + "_candidates", []),
            "winner": winners.get(a, ""),
            "winner_candidates": winners.get(a + "_candidates", []),
        }

    # --- Additional goals (optional) ---
    # out["best_dressed"] = ...
    # out["worst_dressed"] = ...
    # out["most_controversially_dressed"] = ...

    write_json(out_path, out)

def build_report(year: int, in_path: Path, out_report_path: Path):
    # Convert the JSON to a human-readable report
    res_path = Path("output") / f"results_{year}.json"
    data = json.loads(Path(res_path).read_text(encoding="utf-8"))

    lines = []
    lines.append(f'Host: "{data.get("host","")}"')
    lines.append('Host Candidates: ' + ", ".join(f'"{x}"' for x in data.get("host_candidates", [])))
    lines.append("")
    lines.append("Awards: " + ", ".join(f'"{x}"' for x in data.get("awards", [])))
    lines.append("")
    for a in data.get("hard_coded_awards", []):
        block = data.get(a, {})
        lines.append(f'Award: "{a}"')
        lines.append("Presenters: " + ", ".join(f'"{x}"' for x in block.get("presenters", [])))
        lines.append("Presenters Candidates: " + ", ".join(f'"{x}"' for x in block.get("presenters_candidates", [])))
        lines.append("Nominees: " + ", ".join(f'"{x}"' for x in block.get("nominees", [])))
        lines.append("Nominee Candidates: " + ", ".join(f'"{x}"' for x in block.get("nominee_candidates", [])))
        lines.append(f'Winner: "{block.get("winner","")}"')
        lines.append("Winner Candidates: " + ", ".join(f'"{x}"' for x in block.get("winner_candidates", [])))
        lines.append("")
    # Optional extras
    for k in ["best_dressed", "worst_dressed", "most_controversially_dressed"]:
        if k in data:
            pretty = k.replace("_", " ").title()
            lines.append(f'{pretty}: "{data[k]}"')
    write_text(out_report_path, "\n".join(lines))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--in", dest="infile", type=Path, help="path to raw gg<year>.json", required=False)
    ap.add_argument("--out", dest="outfile", type=Path, help="path to results_<year>.json", required=False)
    ap.add_argument("--out-report", dest="out_report", type=Path, help="path to report_<year>.txt", required=False)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    if args.report_only:
        assert args.year, "--year required"
        build_report(args.year, args.infile, args.out_report)
        return

    assert args.infile and args.outfile, "--in and --out required"
    build(args.year, args.infile, args.outfile)

if __name__ == "__main__":
    main()
