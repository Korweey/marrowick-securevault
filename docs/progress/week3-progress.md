<!--
Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
File: docs/progress/week3-progress.md – Week 3 progress log
-->

# Week 3 – Compliance mapping, IAM docs & final delivery

**Milestone (from brief):** Full governance package; live demo of the PII gate catching a bad record. Due October 23.

**Technical report:** the 1,500–2,500-word written report is one of the five required artifacts. `docs/teamwork.md` (about 1,900 words) is our technical report.

| Item | File | Status | Date |
|---|---|---|---|
| IAM least-privilege policy set + deployability annotations | `iam/README.md`, `iam/roles/*.json` | ✅ Final | Oct 18 |
| Compliance mapping (PIPEDA-style) + not-covered section | `docs/compliance-mapping.md` | ✅ Final | Oct 18 |
| Incident-response runbook | `docs/incident-response-runbook.md` | ✅ Final | Oct 18 |
| Architecture diagram updated (Athena views enforced, LF design-only) | `architecture/` | ✅ | Oct 18 |
| README (GitHub front page + reproduction guide) | `README.md` | ✅ Final | Oct 22 |
| Team technical report (teamwork) | `docs/teamwork.md` | ✅ Final, contributions confirmed by both members | Oct 22 |
| GitHub repository (public, both members contributing) | https://github.com/Korweey/marrowick-securevault | ✅ | Oct 18–22 |
| Screen recording of each stage | `evidence/week3/group-h-marrowick-demo.mp4` (6½ min, Git LFS) | ✅ | Oct 22 |
| Presentation slides | `presentation/Marrowick_SecureVault_Group_H_Presentation.pptx` | ✅ | Oct 22 |
| Submission checklist | `SUBMISSION.md` | ✅ | Oct 22 |

## Issues encountered & resolutions
| # | Issue | Impact | Resolution | Evidence |
|---|---|---|---|---|

## Test sign-off: Security Test & Compliance Analyst (Saheedat O. Abbas)

I reran or reviewed every control test against the requirements in the brief. A test passes when the restricted action is refused or the restricted data never comes back.

### Encryption enforcement (evidence/week1)
| Test | Expected | Result | Evidence | Status |
|---|---|---|---|---|
| Upload requesting SSE-S3 override | Denied by bucket policy | Access denied | 19, 20 | Pass |
| Upload with bucket default | Succeeds, encrypted with project KMS key | SSE-KMS with marrowick key ARN | 17, 18 | Pass |
| Raw objects for all three clinics | SSE-KMS with project key | Verified on clinic-a, b and c | 05, 06, 07 | Pass |

### PII gate (evidence/week2)
| Test | Expected | Result | Evidence | Status |
|---|---|---|---|---|
| Gate tests 1 to 3: raw clinic-a, b, c | Blocked, quarantined, SNS alert, curated untouched | All three blocked with alerts | 08 to 18 | Pass |
| Gate tests 4 to 6: steward-redacted batches | Promoted to curated, no alert | All three promoted | 19 to 30 | Pass |
| Alert content | Encounter IDs and finding types only, no PII values | No PII values in any of the three emails | 07, 17, 18 | Pass |

Detection accuracy, rerun on Oct 21 with `python3 tests/test_pii_scan.py` against the answer key (evidence/week3/01):

| Clinic | Rows | Flagged | Seeded |
|---|---|---|---|
| clinic-a | 191 | 4 | 4 |
| clinic-b | 243 | 6 | 6 |
| clinic-c | 181 | 4 | 4 |

TP = 14, FP = 0, FN = 0. Precision 1.00, recall 1.00. The 14 encounter IDs in the three alert emails match the answer key exactly.

### Access separation (evidence/week2, Athena views)
| Test | Role | Attempt | Result | Evidence | Status |
|---|---|---|---|---|---|
| T0 | Baseline | Count all rows | 615 | 40 | Pass |
| T1 | Clinic analyst | Count rows by clinic | Only clinic-a, 191 rows | 41 | Pass |
| T2 | Clinic analyst | Rows where clinic = clinic-b | 0 rows | 42 | Pass |
| T3 | Clinic analyst | Select notes_field | COLUMN_NOT_FOUND | 43 | Pass |
| T4 | Corporate analyst | Count rows by clinic | 191 / 243 / 181 | 44 | Pass |
| T5a | Corporate analyst | Select notes_field | COLUMN_NOT_FOUND | 45 | Pass |
| T5b | Corporate analyst | Select patient_ref | COLUMN_NOT_FOUND | 46 | Pass |

Result: 7 of 7 passed.

### Audit questions (evidence/week2)
| Question | Finding | Evidence |
|---|---|---|
| Q1 Who accessed curated clinic-c data? | Pipeline copy, Glue crawler, then 3 analyst queries, each with identity and time | 51 |
| Q2 Who changed bucket security? | 4 bucket policy changes and 1 encryption change, with identity and time | 52 |
| Q3 Any probing of security services? | Burst of denied Lake Formation calls within 5 minutes, flagged for review | 53, 54 |

### Analyst notes and limitations
1. Access separation uses Athena views because Lake Formation is blocked in the Learner Lab. Views are weaker: a principal with base table or S3 access can bypass them. The Lake Formation filter design is documented for production.
2. The regex gate would miss a name with no identifier, a phone number, a misspelt format or a scanned image. Macie is the documented discovery layer.
3. Per tenant bucket policy rules are deployed but could not be tested, because the lab does not allow tagged principals.
4. CloudTrail times are in UTC.

**Sign-off:** All tested controls met the brief's requirements within the Learner Lab limits above. Saheedat O. Abbas, Oct 21, 2026.