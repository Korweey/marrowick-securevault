# Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
# Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
# File: src/lambda/analyst_query.py – Test harness: runs an Athena query AS the Lambda's role (LabRole)
"""
Why this exists: the Learner Lab blocks creating IAM users/roles, so we cannot log in
as a "clinic analyst". Instead, Lake Formation permissions are granted to LabRole and
this function runs queries *as LabRole*. Whatever Lake Formation lets LabRole see is
exactly what an analyst with those grants would see.

Event: {"query": "SELECT ...", "label": "clinic-analyst test 1"}
"""
import time

import boto3

DATABASE = "marrowick_curated"
OUTPUT = "s3://marrowick-athena-results-004716017211/analyst-tests/"

athena = boto3.client("athena")


def lambda_handler(event, context):
    q = event["query"]
    qid = athena.start_query_execution(
        QueryString=q,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": OUTPUT},
        WorkGroup="primary",
    )["QueryExecutionId"]

    while True:
        st = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        if st["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)

    out = {"label": event.get("label"), "query": q, "query_id": qid, "state": st["State"]}
    if st["State"] != "SUCCEEDED":
        # A Lake Formation denial shows up here – that IS the evidence we want for blocked queries
        out["error"] = st.get("StateChangeReason")
        print(out)
        return out

    res = athena.get_query_results(QueryExecutionId=qid, MaxResults=25)["ResultSet"]
    cols = [c["Label"] for c in res["ResultSetMetadata"]["ColumnInfo"]]
    rows = [[d.get("VarCharValue") for d in r["Data"]] for r in res["Rows"][1:]]
    out.update({"columns": cols, "rows": rows, "row_count_shown": len(rows)})
    print({k: out[k] for k in ("label", "state", "columns", "row_count_shown")})
    return out
