# Submission checklist – Group H, Project 4 (due Friday, October 23, 2026)

**Repository:** https://github.com/Korweey/marrowick-securevault (public)<br>
**Team:** Qawiyy A. Rabiu (N10038749) – Cloud Security Engineer (Build & Deployment) · Saheedat O. Abbas (N10038753) – Security Test & Compliance Analyst

| # | Required artifact | Where it is |
|---|---|---|
| 1 | Architecture diagram (every AWS service, direction of data flow) | `architecture/Marrowick_Architecture.drawio` and `architecture/Marrowick_Architecture_preview.png` |
| 2 | Repository with all code and SQL + README to reproduce from a fresh Learner Lab | `src/lambda/`, `src/stepfunctions/`, `sql/`, `iam/`, `tests/`; rebuild steps in `README.md` |
| 3 | Written technical report (1,500–2,500 words) | `docs/teamwork.md` (about 1,900 words: §4 design and trade-offs, §5 data quality and governance, §6 cost and performance, §8 lessons learned) |
| 4 | Evidence of a working pipeline + sample query results | `evidence/week3/group-h-marrowick-demo.mp4` (6 min, resubmitted Oct 23); screenshots in `evidence/` (table below); test sign-off in `docs/progress/week3-progress.md` |
| 5 | 8-minute team presentation + 2 min Q&A | Delivered live in class; slides in `presentation/` |

## Evidence by pipeline stage
| Stage | Screenshots |
|---|---|
| Encryption and storage | `evidence/week1/02–09` |
| Encryption enforcement (SSE-S3 upload denied) | `evidence/week1/13–20` |
| Audit trail setup | `evidence/week1/10–12` |
| PII gate – blocked + SNS alerts | `evidence/week2/06–18` |
| PII gate – redacted batches promoted | `evidence/week2/19–30` |
| Glue catalog and Athena views | `evidence/week2/31–39` |
| Access tests T0–T5b (query results) | `evidence/week2/40–46` |
| Audit queries Q1–Q3 (query results) | `evidence/week2/47–54` |
| Scanner accuracy 14/14 | `evidence/week3/01` |
| Problems hit and fixed | `evidence/week1/issues/`, `evidence/week2/issues/` |

## Note on Infrastructure-as-Code
The environment was built in the AWS console of the Learner Lab. Every resource's configuration is kept in this repository as code: KMS key and bucket policies (`iam/*.json`), the Step Functions definition, the Lambda source and all SQL. The README's 12 rebuild steps recreate it from a fresh Learner Lab session. IAM roles and Lake Formation permissions are design-only because the Learner Lab blocks them.
