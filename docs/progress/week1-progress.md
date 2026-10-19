<!--
Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
File: docs/progress/week1-progress.md – Week 1 progress log with evidence
-->

# Week 1 – Multi-tenant design, encryption & access control

**Milestone (from brief):** Encrypted, tenant-separated data landed; demonstrated tenant/role access separation; CloudTrail enabled.

| Part | Scope | Status | Date |
|---|---|---|---|
| Design | Architecture diagram | ✅ Drafted (awaiting team sign-off) | Oct 12 |
| A | KMS key, encrypted buckets, tenant folders, data landed | ✅ Complete | Oct 18 |
| B | CloudTrail + bucket policies (+ enforcement test) | ✅ Complete | Oct 18 |
| B2 | Lake Formation roles (needs Glue table) | ⏳ Next session | – |

---

## Environment
| Item | Value |
|---|---|
| AWS account | `004716017211` (AWS Academy Learner Lab) |
| Region | `us-east-1` (N. Virginia) |
| Console role | `voclabs` · Pipeline role: `LabRole` |

---

## Design – Architecture diagram
- File: [`architecture/Marrowick_Architecture.drawio`](../../architecture/Marrowick_Architecture.drawio) (editable) and [preview PNG](../../architecture/Marrowick_Architecture_preview.png)
- Flow: clinic CSVs → S3 raw (per-clinic prefixes, SSE-KMS) → Glue crawler → Step Functions PII gate (Lambda regex scan → Choice → curated or quarantine + SNS) → Lake Formation (row/column filters) → Athena → analysts. CloudTrail + CloudWatch in the background for audit.

---

## Part A – Encryption at rest & tenant-separated storage

### A1. Data preparation
- The supplied CSVs contain an answer-key column `_seeded_pii_for_grading_only`. Per the dataset README it must never reach the pipeline, so it was **removed** before upload.
- Upload files: [`data/raw/`](../../data/raw/) – clinic-a (191 rows), clinic-b (243 rows), clinic-c (181 rows).
- Answer key kept separately for testing the PII gate: [`tests/seeded_pii_answer_key.csv`](../../tests/seeded_pii_answer_key.csv) – **14 seeded PII rows** (A=4, B=6, C=4).

### A2. Customer-managed KMS key
| Setting | Value |
|---|---|
| Alias | `marrowick-data-key` |
| ARN | `arn:aws:kms:us-east-1:004716017211:key/22bce328-0375-4cd6-a3cf-6df93b007a2b` |
| Type / usage | Symmetric · Encrypt and decrypt · Single-Region |
| Key administrator | `voclabs` (human operator) |
| Key users | `LabRole` (pipeline) + `voclabs` |
| Rotation | Automatic, every 365 days (next: Oct 18, 2027) |
| Policy file | [`iam/kms-key-policy.json`](../../iam/kms-key-policy.json) |

**Key policy justification**
1. *Enable IAM User Permissions* (account root, `kms:*`) – AWS default; lets IAM policies also grant key access and prevents the key from becoming unmanageable. It does **not** give anyone direct data access.
2. *Key Administrators* (`voclabs`) – can manage, rotate, disable or schedule deletion, but this statement grants no Encrypt/Decrypt.
3. *Use of the key* (`LabRole`, `voclabs`) – Encrypt/Decrypt/GenerateDataKey for the pipeline and operator.
4. *Persistent resources* – grants only when `kms:GrantIsForAWSResource = true` (S3, Glue integrations).
→ **Separation of duties:** the pipeline role can use the key but cannot disable or delete it.

**Rotation impact:** AWS keeps prior key material, so objects encrypted before a rotation remain decryptable without re-encryption; new objects use the new material.

Evidence:
- ![KMS general config & policy](../../evidence/week1/02_kms_key_general_config_and_policy.png)
- ![Rotation enabled](../../evidence/week1/03_kms_key_rotation_enabled.png)

### A3. Three zone buckets (all identical security settings)
| Bucket | Purpose |
|---|---|
| `marrowick-raw-004716017211` | Landing zone – unchecked clinic uploads |
| `marrowick-quarantine-004716017211` | Batches that fail the PII gate |
| `marrowick-curated-004716017211` | Trusted zone – only gate-approved data; the only zone analysts query |

Settings: General purpose · ACLs disabled · **Block all public access ON** · Versioning disabled · **SSE-KMS with `marrowick-data-key`** · **Bucket Key enabled**.

Evidence: ![Three buckets](../../evidence/week1/04_s3_three_buckets_created.png)

### A4. Tenant separation (per-clinic prefixes)
Each bucket has `clinic-a/`, `clinic-b/`, `clinic-c/`. Raw holds one CSV per clinic; curated and quarantine start empty (filled by the Week 2 gate).

### A5. Encryption verified on every landed object
All three raw objects show **SSE-KMS**, key ARN ending `…6df93b007a2b`, Bucket Key **Enabled**.

- ![clinic-a](../../evidence/week1/05_raw_clinic-a_object_sse-kms.png)
- ![clinic-b](../../evidence/week1/06_raw_clinic-b_object_sse-kms.png)
- ![clinic-c](../../evidence/week1/07_raw_clinic-c_object_sse-kms.png)
- ![curated folders empty](../../evidence/week1/08_curated_bucket_empty_clinic_folders.png)

---

## Issues encountered & resolutions
| # | Issue | Impact | Resolution | Evidence |
|---|---|---|---|---|
| 1 | KMS create-key wizard lost role selections across paginated role lists (admin/user roles ended up swapped, then missing). | LabRole would have been unable to decrypt data in Week 2; no separation of duties. | Pasted the final key policy directly into the policy editor; verified 4 statements on review. | Policy file in repo |
| 2 | Automatic rotation is **off** by default on new keys. | Missed bonus / weaker key hygiene. | Enabled 365-day rotation. | ![](../../evidence/week1/issues/issue1_rotation_initially_disabled.png) |
| 3 | Bucket form defaulted to **Versioning: Enable** and **DSSE-KMS** was selected. | DSSE-KMS costs more and does not support Bucket Keys; versioning adds cost and complicates cleanup. | Switched to SSE-KMS + Bucket Key, versioning disabled; verified on objects. | ![](../../evidence/week1/issues/issue2_bucket_form_dsse-kms_and_versioning.png) |
| 5 | CloudTrail data-event selectors used the "Log all events" template; the selector *name* was only a label, so every bucket (incl. the log bucket itself) was logged 3×. | Recursive logging, cost, noisy audit. | Single Custom selector: `resources.ARN startsWith` the three tenant buckets. | ![](../../evidence/week1/issues/issue5_cloudtrail_data_events_log_all.png) |
| 6 | First SSE-S3 test upload "succeeded" – the override was never applied (object showed SSE-KMS). | False test result. | Repeated with Properties → Specify key → Override → SSE-S3 explicitly selected; upload then **failed with Access Denied**. | ![](../../evidence/week1/19_test1_sse-s3_override_requested.png) |
| 4 | Clinic CSVs (containing seeded PII) were first uploaded to the **curated** bucket instead of raw. | Unscanned PII sat in the trusted zone – exactly what the gate must prevent. | Deleted from curated, re-uploaded to raw, confirmed curated folders empty. **Lesson:** zone boundaries need enforcement (bucket policies in Part B, PII gate in Week 2), not just naming convention. | ![](../../evidence/week1/issues/issue3_files_wrongly_in_curated_clinic-a.png) |

---

## Part B – Audit trail & bucket policies

### B1. CloudTrail
| Setting | Value |
|---|---|
| Trail | `marrowick-audit-trail` (multi-Region, logging ON) |
| Log bucket | `aws-cloudtrail-logs-004716017211-36c99747` (SSE-S3 – KMS for logs deliberately not used to avoid widening the data-key policy to the CloudTrail service) |
| Log file validation | Enabled (tamper detection) |
| Management events | All (Read + Write) → audit Q2 (bucket policy changes) |
| Data events | One Custom selector `marrowick-tenant-buckets`: S3 objects where `resources.ARN` starts with raw/quarantine/curated bucket ARNs → audit Q1 (object access) |
| Rejected options | Insights events (extra cost, needs multi-day baseline), Network activity events (no VPC endpoints in design), CloudWatch Logs delivery (cost; Athena on S3 suffices) |

- ![Trail logging](../../evidence/week1/10_cloudtrail_trail_logging_on.png)
- ![Storage & validation](../../evidence/week1/11_cloudtrail_storage_and_validation.png)
- ![Scoped data events](../../evidence/week1/12_cloudtrail_data_events_scoped_to_tenant_buckets.png)

### B2. Bucket policies (one per zone)
Files: [`iam/bucket-policy-raw.json`](../../iam/bucket-policy-raw.json), [`-quarantine`](../../iam/bucket-policy-quarantine.json), [`-curated`](../../iam/bucket-policy-curated.json)

| Statement | Effect | Status |
|---|---|---|
| DenyInsecureTransport | Blocks non-HTTPS requests | ✅ Enforced |
| DenyNonKmsEncryptionHeader | Blocks uploads requesting non-KMS encryption | ✅ Enforced & **tested** |
| DenyWrongKmsKey | Blocks uploads naming any other KMS key | ✅ Enforced |
| TenantIsolationClinicA/B/C | Denies a principal tagged `tenant=clinic-x` access to other clinics' prefixes | ⚠️ Deployed, **design-ready only** – Learner Lab blocks creating tagged per-clinic roles, so no principal carries the tag yet. Tenant separation is demonstrated via Lake Formation instead. |

- ![raw](../../evidence/week1/13_bucket_policy_raw.png) · ![quarantine](../../evidence/week1/14_bucket_policy_quarantine.png) · ![curated](../../evidence/week1/15_bucket_policy_curated.png)
- Side effect: each save produced a `PutBucketPolicy` CloudTrail event – source data for audit Q2.

### B3. Enforcement test
| Test | Request | Expected | Actual |
|---|---|---|---|
| 1 | Upload `test-sse-s3.txt` to raw/clinic-a/ with **SSE-S3 override** | Denied | ✅ **Failed – Access denied** |
| 2 | Same file, bucket default encryption | Allowed, SSE-KMS | ✅ Succeeded, SSE-KMS with `marrowick-data-key` |

- ![SSE-S3 requested](../../evidence/week1/19_test1_sse-s3_override_requested.png)
- ![Access denied](../../evidence/week1/20_test1_sse-s3_upload_access_denied.png)
- ![Default upload OK](../../evidence/week1/17_test2_default_kms_upload_succeeded.png) · ![Encrypted with our key](../../evidence/week1/18_test2_object_encrypted_with_marrowick_key.png)
- Test file deleted afterwards.

### B4. Lake Formation (next session)
- [ ] Glue crawler → catalog table over curated zone
- [ ] Register curated location; clinic-analyst row filter (`tenant_id`); corporate-analyst column exclusion (`notes_field`, `patient_ref`)
- [ ] Evidence that the restricted queries are actually blocked

## Cost note
KMS key ≈ US$1/month (prorated) + requests (reduced by Bucket Key); S3 storage for ~70 KB is negligible.
