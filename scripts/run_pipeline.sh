#!/usr/bin/env bash
set -euo pipefail

YEAR=${1:-2013}
INFILE=${2:-data/raw/gg${YEAR}.json}
OUTJSON=${3:-output/results_${YEAR}.json}
OUTREPORT=${4:-output/report_${YEAR}.txt}

echo "[run_pipeline] year=${YEAR} in=${INFILE} out=${OUTJSON}"

python src/build_dataset.py --year "${YEAR}" --in "${INFILE}" --out "${OUTJSON}"

# also produce a human-readable report for convenience
python src/build_dataset.py --year "${YEAR}" --in "${INFILE}" --out-report "${OUTREPORT}" --report-only

echo "[run_pipeline] done."
