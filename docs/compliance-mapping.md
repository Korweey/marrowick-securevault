<!--
Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
File: docs/compliance-mapping.md – Controls mapped to PIPEDA fair information principles
-->

# Compliance mapping – PIPEDA-style (simplified)

**Scope statement.** This maps the technical controls we built to the ten fair information principles in Schedule 1 of Canada's *Personal Information Protection and Electronic Documents Act* (PIPEDA). It is a **learning exercise on synthetic data**, not a compliance certification or legal opinion. Health data in Ontario would also fall under **PHIPA**, which is out of scope here.

## Implemented controls → principles
| # | PIPEDA principle | Control implemented | Evidence | Strength |
|---|---|---|---|---|
| 4.1 | **Accountability** | Named owners in README; CloudTrail records *who* did every action; log-file validation detects tampering | Week 1 B1; audit Q1/Q2 | Partial – technical, no formal privacy officer |
| 4.4 | **Limiting collection** | Regex PII gate blocks identifiers (health card, SIN, email, address) from reaching analytics; answer-key column removed before ingestion | Week 2 D (14/14 caught) | Strong (for known patterns) |
| 4.5 | **Limiting use, disclosure and retention** | Tenant separation by prefix; clinic analysts see only their own clinic's rows; corporate analysts see no PII columns | Access tests T1–T5b (7/7) | Strong in tests; views are bypassable without Lake Formation (see limitations) |
| 4.5 | (retention) | Raw kept as immutable record of submissions; quarantine isolates blocked batches | Week 2 C | Partial – no lifecycle/expiry rules |
| 4.6 | **Accuracy** | Gate is all-or-nothing per batch; steward remediation creates a new `_v2` object, original preserved; row counts reconciled (615 in = 615 catalogued) | Week 2 D, Glue table | Partial |
| 4.7 | **Safeguards** | SSE-KMS with customer-managed key + annual rotation; bucket policies deny non-TLS, non-KMS and wrong-key uploads; public access blocked; SNS alert on gate failure; least-privilege role designs | Week 1 A2–A5, B2–B3 (SSE-S3 upload denied) | **Strong** – the core of this project |
| 4.8 | **Openness** | Architecture, policies and runbook documented in repo | README, diagram | Partial |
| 4.10 | **Challenging compliance** | Audit queries can show exactly who accessed a tenant's data in response to a complaint | Audit Q1 | Partial |
| — | *Breach of security safeguards* (s.10.1) | Incident-response runbook includes the "real risk of significant harm" assessment, OPC reporting, individual notification and 24-month record keeping | `docs/incident-response-runbook.md` | Process only (untested) |

## Not covered / out of scope
| Principle / area | Why not covered |
|---|---|
| 4.2 **Identifying purposes** | Requires business/legal documentation of why each field is collected – organisational, not technical |
| 4.3 **Consent** | Consent is obtained by clinics at point of care; our platform receives de-identified data and has no consent records |
| 4.9 **Individual access** | No process for a patient to request their records; `patient_ref` is pseudonymous and re-identification is deliberately not possible here |
| Retention & deletion | No S3 lifecycle rules or deletion schedule; would be added for production |
| Unstructured PII the regex cannot see | Names without an identifier pattern, misspellings, scanned images – Amazon Macie or an ML classifier (e.g. Comprehend Medical) would be needed |
| Formal governance | No privacy impact assessment, data-sharing agreements with clinics, staff training or third-party audit |
| PHIPA (Ontario) | Health-specific obligations (health information custodian duties, logging requirements) not assessed |
| Lake Formation enforcement | Designed but not deployable in the Learner Lab; Athena views used instead |
