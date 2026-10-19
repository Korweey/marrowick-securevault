# Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
# Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
# File: tests/test_pii_scan.py – Offline precision/recall check of the PII scanner against the answer key
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src", "lambda"))
from pii_scan import scan_rows, summarise  # noqa: E402

key = {r["encounter_id"]: r["pii_type"] for r in csv.DictReader(open(os.path.join(HERE, "seeded_pii_answer_key.csv")))}
tp = fp = 0; detected = set()
for c in "abc":
    rows = list(csv.DictReader(open(os.path.join(HERE, "..", "data", "raw", f"clinic-{c}_encounters.csv"))))
    counts, flagged = summarise(scan_rows(rows))
    print(f"clinic-{c}: rows={len(rows)} flagged={len(flagged)} counts={counts}")
    for e in flagged:
        detected.add(e)
        if e in key: tp += 1
        else: fp += 1; print("  FALSE POSITIVE:", e)
fn = [e for e in key if e not in detected]
print(f"\nTP={tp} FP={fp} FN={len(fn)}  precision={tp/(tp+fp):.2f} recall={tp/(tp+len(fn)):.2f}")
for e in fn: print("  MISSED:", e, key[e])
