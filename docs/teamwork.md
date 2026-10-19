<!--
Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
File: docs/teamwork.md – Team technical report: design rationale, trade-offs, lessons learned, contributions
-->

# Team Technical Report – Marrowick Health Analytics (SecureVault)

**Group H:** Qawiyy A. Rabiu (N10038749) · Saheedat O. Abbas (N10038753)
**Course:** CCGC 5506 Mid-Term, Project 4 · Humber Polytechnic · Fall 2026
**Status:** Internal team report (optional submission)

> Items marked _[confirm]_ are for both members to complete together before this report is shared, so that it accurately records who did what.

---

## 1. Purpose and scope
Marrowick Health Analytics receives encounter and billing data from three clinic partners into a shared analytics platform. Our workstream was not to build analytics, but to build and **prove** the guardrails around it: encryption at rest, separation between clinics and between analyst roles, an auditable trail, and an automated gate that stops personal information from reaching the analytics layer.

All data is synthetic. The three clinic files (615 encounters in total) contain 14 deliberately seeded PII rows – names with health-card numbers, SIN-formatted numbers, emails and full contact cards in a free-text `notes_field`.

## 2. Architecture summary
| Layer | Service | Key decision |
|---|---|---|
| Storage | Three S3 buckets – **raw**, **quarantine**, **curated** – each with `clinic-a/`, `clinic-b/`, `clinic-c/` prefixes | Zone = trust level; prefix = tenant |
| Encryption | One customer-managed KMS key, SSE-KMS + Bucket Key, annual rotation | Key policy separates key *administration* (human) from key *use* (pipeline) |
| Enforcement | Bucket policies: TLS-only, KMS-only uploads, our key only, per-tenant tag rules | A deny in a bucket policy overrides any IAM allow |
| PII gate | Step Functions → Lambda regex scan → Choice → quarantine + SNS, or promote | All-or-nothing per batch, as the brief requires |
| Catalog & query | Glue crawler on curated only → Athena | Blocked data can never be catalogued |
| Access separation | Athena views per role (Lake Formation design documented) | See §4.3 |
| Audit | CloudTrail (management + scoped S3 data events) → Athena | Partition projection, no crawler needed |

## 3. Results
| Requirement | Outcome |
|---|---|
| Encrypted, tenant-separated data | All objects verified SSE-KMS with our key; upload requesting SSE-S3 **denied** by bucket policy |
| PII gate blocks seeded data end-to-end | All 3 raw batches **quarantined** with SNS alerts; 3 steward-redacted batches **promoted**; **14/14 seeded rows detected, 0 false positives** (precision and recall 1.00) |
| Clinic analyst cannot see other tenants or PII columns | Restricted queries returned **0 rows** or **COLUMN_NOT_FOUND** – 7/7 tests passed |
| Two audit questions answered | Three answered: who accessed curated clinic-c data; which calls changed bucket security; which denied calls indicate probing |

## 4. Design rationale and trade-offs

### 4.1 Bucket-per-zone, prefix-per-tenant
**Chosen:** three buckets (by trust level) with per-clinic prefixes.
**Rejected:** one bucket per clinic per zone (nine buckets) – stronger physical isolation, but nine policies and encryption settings to keep in sync, and more places to misconfigure. Our layout lets one bucket policy express the zone's rules and per-prefix statements express tenant rules. The trade-off is logical rather than physical tenant isolation, which the brief accepts ("logically, and where possible physically").

### 4.2 Encryption choices
- **SSE-KMS over DSSE-KMS:** dual-layer encryption costs more per request and does not support S3 Bucket Keys; it adds no meaningful protection for this threat model.
- **Bucket Key enabled:** reduces KMS requests (and cost) by issuing a short-lived bucket-level key instead of calling KMS for every object.
- **CloudTrail logs not encrypted with the data key:** doing so would require granting the CloudTrail service use of the key that protects health data. Logs use S3-managed encryption instead, with log-file validation to detect tampering.
- **Key rotation:** enabled annually. Previous key material is retained, so existing objects remain readable without re-encryption.

### 4.3 Access separation: Lake Formation vs Athena views
The intended design uses Lake Formation data cells filters (row filter `tenant_id = 'clinic-a'`, column exclusions) granted to dedicated analyst roles. In the Learner Lab, the console role is denied `lakeformation:GetDataLakeSettings`, so no administrator or grant could be created.

We implemented the same restrictions as Athena views and tested them by actually attempting the forbidden queries. **This is a weaker control:** a view limits what a query *through the view* returns, but any principal with base-table or S3 access can bypass it. Lake Formation enforces the filter on the table itself for every engine. Our design pairs the filters with an explicit IAM deny on direct S3 access, closing that gap in production. We chose to state this limitation openly rather than present views as equivalent.

**Why `patient_ref` is visible to the clinic analyst but not the corporate analyst:** a clinic needs its own pseudonymous patient IDs for follow-up care; a cross-clinic analyst with those IDs could link one patient's visits across clinics.

### 4.4 The PII gate
- **Regex over Macie as the gate:** regex is deterministic, fast, free, and testable offline against the answer key. Macie is better at discovering unknown sensitive data but runs as a scheduled job and is a discovery layer, not an inline gate. We documented Macie as the complementary layer.
- **Leak-safe scanner:** the Lambda returns and logs only the *type* and *location* of each finding, never the matched value. The SNS alert therefore contains encounter IDs and counts only – the alerting channel cannot itself leak PII, which is also why the topic did not need KMS encryption.
- **Skipped columns:** structured pseudonymous IDs (`patient_ref`, `encounter_id`, `clinician_id`) are excluded from scanning by design; SIN-like patterns would otherwise risk matching them.
- **Remediation model:** raw is never modified. A data steward redacts the flagged rows and resubmits as a new `_v2` object. The original stays in raw and quarantine as the audit record of what the clinic actually sent.
- **Trade-off:** all-or-nothing gating means one bad row blocks 190 good ones. Row-level quarantine would be more efficient but harder to audit and was not what the brief specified.

### 4.5 Audit design
CloudTrail data events were scoped with a custom selector to the three tenant buckets. Logging all S3 data events would also log writes to the CloudTrail bucket itself – a feedback loop that adds cost and noise. **Insights** events (extra cost, needs a multi-day baseline) and **network activity** events (no VPC endpoints in the design) were considered and rejected.

## 5. Data quality and governance measures
- Answer-key column removed before ingestion, so the pipeline never sees the grading labels.
- Row counts reconciled end-to-end: 191 + 243 + 181 = 615 rows uploaded, scanned, promoted and catalogued.
- Offline unit test (`tests/test_pii_scan.py`) measures precision and recall against the answer key before every deployment.
- Live alert contents cross-checked against the answer key: the 14 encounter IDs in the three emails match exactly.
- Every build step captured as evidence, with problems logged and resolved in the weekly progress logs.

## 6. Cost and performance
Every component is serverless and pay-per-use, as the Learner Lab budget requires:

| Component | Cost driver | Our usage |
|---|---|---|
| S3 | Storage + requests | ~70 KB data – negligible |
| KMS | ~US$1/month per key + requests | Bucket Key cuts request volume |
| Lambda | Per invocation + duration | 6 runs, < 1 s each |
| Step Functions (Standard) | Per state transition | 6 executions × 4–6 transitions |
| Athena | Per data scanned | Queries scanned ~69 KB (curated) and ~316 KB (CloudTrail) |
| CloudTrail | First management trail free; data events per event | Scoped to 3 buckets |

**Always-on alternatives avoided:** an EMR cluster or OpenSearch domain for scanning/audit would cost tens of dollars per day even when idle; Lambda + Athena cost fractions of a cent for the same work at this scale.

## 7. Learner Lab constraints and honesty
| Constraint | What we did |
|---|---|
| IAM role/user creation blocked | All services ran as LabRole; one least-privilege policy per role written as design-only JSON (`iam/roles/`) |
| Lake Formation blocked | Athena-view fallback, tested; full LF design documented |
| No tagged principals | Bucket-policy tenant statements deployed but untestable – stated as such |

The controls that **were** enforced regardless of IAM are the KMS key policy, the bucket policies (tested) and the gate logic itself.

## 8. Lessons learned
1. **Enable CloudTrail first.** It records only from the moment it is turned on; audit questions need history.
2. **Verify every console default.** The bucket form defaulted to versioning on; the KMS wizard lost role selections across paginated lists; the CloudTrail "Log all events" template ignored the selector name. Each needed an explicit check.
3. **A test that passes for the wrong reason is worse than no test.** Our first "upload with SSE-S3" test succeeded because the override was never applied. Checking the resulting object's encryption revealed it.
4. **Conventions are not controls.** Early in setup, unscanned files were uploaded to the curated bucket by mistake. Zone boundaries must be enforced by policy and by the gate, not by naming.
5. **Check service availability in the first session.** Discovering the Lake Formation block late forced a redesign of the access layer.
6. **Raw audit data is noisy.** Background console calls produced many AccessDenied events; filtering to security-relevant services made the real signal – repeated Lake Formation probing – stand out.

## 9. Future work
- Deploy Lake Formation filters and per-role IAM policies in a non-restricted account.
- Add Amazon Macie scheduled discovery and reconcile its findings with the regex gate.
- CloudWatch dashboard and alarms for gate failures and AccessDenied spikes.
- Partial masking of health-card numbers for corporate analysts (e.g. `****-***-244`).
- S3 lifecycle rules for retention and deletion.

## 10. Team organization and contributions
**How we worked:** We split the work along the brief's three phases, recorded design decisions in a shared progress note, and filed evidence by week so either member can explain any step.

| Member | Role | Responsibility |
|---|---|---|
| Qawiyy A. Rabiu | **Cloud Security Engineer (Build & Deployment)** | Developed the code (with AI-assisted drafting) and deployed every component in AWS |
| Saheedat O. Abbas | **Security Test & Compliance Analyst** | Ran the control tests and analyzed the results against the requirements |

| Deliverable | Qawiyy A. Rabiu | Saheedat O. Abbas |
|---|---|---|
| Architecture diagram | Drafted | Confirmed & Approved |
| KMS key, S3 zones, bucket policies, CloudTrail | Built & deployed | Ran enforcement test (SSE-S3 upload denied) |
| PII gate – Lambda, Step Functions, SNS | Developed & deployed | Ran gate tests; analysed 14/14 detection vs answer key |
| Glue catalog and Athena access views | Built & deployed | Ran access tests T0–T5b and analysed results |
| CloudTrail audit queries | Wrote queries / audit table | Ran Q1–Q3 and interpreted findings |
| IAM least-privilege policy set | Drafted | Confirmed |
| Compliance mapping | Confirmed | Mapped |
| Incident-response runbook | Confirmed | Tested Scenarios |
| README / GitHub repository | Set up & pushed | Confirmed |
| Screen recordings and demo | Collective | Collective |

**Tools used:** AWS Academy Learner Lab, draw.io, GitHub, and an AI assistant (Claude) for guidance, drafting code, and documentation. All AI-drafted material was reviewed, run and edited by the team.
