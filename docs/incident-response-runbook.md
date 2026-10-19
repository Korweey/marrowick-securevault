<!--
Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
File: docs/incident-response-runbook.md – Response steps for PII-gate or access-control failure
-->

# Incident-response runbook

**Owner:** Platform security/governance workstream (Group H) · **Severity scale:** SEV-1 PII exposed to an unauthorised person · SEV-2 PII in curated but no confirmed access · SEV-3 control degraded, no PII exposed

## Scenarios covered
| ID | Scenario | Typical trigger |
|---|---|---|
| IR-1 | **PII reached the curated zone** (gate false negative) | Analyst/steward spots PII; Macie finding; spot-check query |
| IR-2 | **Gate did not alert** (SNS failed or workflow skipped) | Quarantine object with no matching email; failed execution |
| IR-3 | **Access control failed** – an analyst saw another tenant's rows or a PII column | Test failure; user report; audit Q1 shows unexpected principal |
| IR-4 | **Security setting changed** – bucket policy, encryption or key policy altered/deleted | Audit Q2 shows unexpected `PutBucketPolicy`/`DeleteBucketPolicy`; KMS key disabled |

## Phase 1 – Detect & triage (0–30 min)
1. Record time, reporter, what was seen. Open an incident log (who/what/when for every action below).
2. Assign severity (above). SEV-1/2 → notify team lead and privacy contact immediately.
3. Identify scope: which tenant(s), which object key(s), which encounter IDs.
   ```sql
   -- Which batches were promoted, and when (Step Functions copies into curated)
   SELECT eventtime, useridentity.arn, json_extract_scalar(requestparameters,'$.key') AS key
   FROM marrowick_audit.cloudtrail_logs
   WHERE eventsource='s3.amazonaws.com' AND eventname='CopyObject'
     AND json_extract_scalar(requestparameters,'$.bucketName')='marrowick-curated-004716017211'
   ORDER BY eventtime DESC;
   ```

## Phase 2 – Contain (30–60 min)
| Scenario | Containment action |
|---|---|
| IR-1 | Move the offending object from curated → quarantine (copy, then delete from curated). Temporarily `DROP VIEW` / revoke analyst access to the affected table. Pause new runs of `marrowick-pii-gate`. |
| IR-2 | Pause the gate. Check SNS subscription is **Confirmed**; check the failed execution's step for the error. Manually notify the team. |
| IR-3 | Revoke the analyst's access (drop/replace the view; in production revoke the Lake Formation grant). Preserve the query ID and results location as evidence. |
| IR-4 | Re-apply the known-good policy from the repo (`iam/bucket-policy-*.json`, `iam/kms-key-policy.json`). If the KMS key was scheduled for deletion, **cancel deletion** immediately. |

## Phase 3 – Investigate (same day)
1. **Who accessed the exposed data?**
   ```sql
   SELECT eventtime, useridentity.arn AS who, useridentity.invokedby AS via, eventname,
          json_extract_scalar(requestparameters,'$.key') AS key
   FROM marrowick_audit.cloudtrail_logs
   WHERE json_extract_scalar(requestparameters,'$.bucketName')='marrowick-curated-004716017211'
     AND json_extract_scalar(requestparameters,'$.key') LIKE 'clinic-x/%'   -- affected tenant
   ORDER BY eventtime;
   ```
2. **Who changed security settings?** Run audit Q2 (`sql/03_cloudtrail_audit.sql`).
3. **Any probing?** Run Q3b (denied calls on security/data services).
4. Root cause: new PII format the regex misses? Gate bypassed (file written to curated directly)? View definition changed? Policy edited?

## Phase 4 – Eradicate & recover (1–3 days)
- IR-1: add the missed pattern to `PATTERNS` in `src/lambda/pii_scan.py`; add the case to `tests/test_pii_scan.py`; re-run the test (must stay 100% recall); redeploy; re-scan **all** curated objects; have the data steward redact and resubmit as `_v2`.
- IR-2: fix the subscription/permission; add a CloudWatch alarm on `ExecutionsFailed` for the state machine.
- IR-3: correct the view/filter; re-run access tests T0–T5b and attach results.
- IR-4: restore policy; rotate any credentials of the principal that made the change.
- Re-enable the gate and analyst access only after tests pass.

## Phase 5 – Notify (PIPEDA breach of security safeguards)
1. Assess **real risk of significant harm (RROSH)**: sensitivity (health data = high) × probability of misuse (who saw it, was it copied?).
2. If RROSH: report to the **Office of the Privacy Commissioner of Canada** and notify affected individuals (via the clinic partner) **as soon as feasible**; notify any organisation that can reduce the harm.
3. Notify the affected **clinic partner** in all SEV-1/SEV-2 cases regardless of RROSH (contractual duty).
4. **Keep a record of every breach for 24 months**, even if not reportable.
5. Note: Ontario health data would additionally trigger **PHIPA** notification duties.

## Phase 6 – Post-incident review (within 1 week)
- Blameless write-up: timeline, root cause, what worked, what didn't.
- Update this runbook and the compliance mapping.
- Add a regression test for the failure.

## Tabletop exercise (bonus)
Simulate IR-1 live: upload a file containing a **new** PII format (e.g. a phone number) that the current regex does not match → it is promoted to curated → walk the class through Phases 1–6 using the queries above.
