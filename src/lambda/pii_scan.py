# Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
# Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
# File: src/lambda/pii_scan.py – Regex-based PII/PHI scanner used as the hard gate in the Step Functions workflow
"""
Input event : {"bucket": "<raw bucket>", "key": "clinic-a/clinic-a_encounters.csv"}
Output      : {"bucket", "key", "tenant", "rows_scanned", "pii_found", "flagged_rows",
               "counts": {type: n}, "findings": [{"row", "encounter_id", "field", "type"}]}
Matched values are NEVER returned or logged – only their type and location –
so the scanner itself does not leak the PII it finds.
"""
import csv
import io
import re

# Synthetic Canadian-style patterns used by the dataset
PATTERNS = {
    # e.g. "health card 7135-655-564 AB"  (4-3-3 digits + 2-letter version code)
    "health_card": re.compile(r"\b\d{4}-\d{3}-\d{3}\s?[A-Z]{2}\b"),
    # e.g. "SIN on file 173-866-654"  (3-3-3 digits, not part of a longer number)
    "sin": re.compile(r"(?<![\d-])\d{3}[- ]\d{3}[- ]\d{3}(?![\d-])"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # street address: number + name + street type, e.g. "1495 Thistle St"
    "street_address": re.compile(
        r"\b\d{1,5}\s+[A-Z][a-z]+\s+(St|Ave|Rd|Cres|Dr|Blvd|Way|Lane|Ln|Ct)\b"),
}

# Columns that are structured, pseudonymous identifiers by design (not PII)
SKIP_COLUMNS = {"encounter_id", "tenant_id", "patient_ref", "clinician_id",
                "encounter_date", "diagnosis_code", "billing_amount", "encounter_type"}


def scan_rows(rows):
    """Scan an iterable of dict rows; return findings list (no raw values)."""
    findings = []
    for i, row in enumerate(rows, start=2):  # row 1 is the header
        for col, val in row.items():
            if col in SKIP_COLUMNS or not val:
                continue
            for ptype, rx in PATTERNS.items():
                if rx.search(val):
                    findings.append({"row": i, "encounter_id": row.get("encounter_id"),
                                     "field": col, "type": ptype})
    return findings


def summarise(findings):
    counts = {}
    for f in findings:
        counts[f["type"]] = counts.get(f["type"], 0) + 1
    flagged = sorted({f["encounter_id"] for f in findings})
    return counts, flagged


def lambda_handler(event, context):
    bucket, key = event["bucket"], event["key"]
    import boto3  # imported here so the scan logic can be unit-tested offline
    body = boto3.client("s3").get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(body)))
    findings = scan_rows(rows)
    counts, flagged = summarise(findings)
    result = {
        "bucket": bucket,
        "key": key,
        "tenant": key.split("/")[0],
        "rows_scanned": len(rows),
        "pii_found": bool(findings),
        "flagged_rows": flagged,
        "counts": counts,
        "findings": findings[:50],
    }
    # Log only the summary (no PII values) to CloudWatch
    print({k: result[k] for k in ("key", "rows_scanned", "pii_found", "counts")})
    return result
