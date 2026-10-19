<!--
Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
File: iam/README.md – IAM least-privilege policy set with deployability annotations
-->

# IAM least-privilege policy set

## Why this is mostly design-only
The AWS Academy Learner Lab provides one pre-built role (**LabRole**) for services and one console role (**voclabs**), and **blocks IAM role and user creation** (evidence: `evidence/week2/issues/issue2_sfn_cannot_create_iam_role.png`). Every service in the pipeline therefore ran as LabRole, which has far broader permissions than any single component needs.

To get as close to least privilege as the lab allows, we (1) **deployed** the resource-based policies the console *does* allow (KMS key policy, S3 bucket policies), and (2) **designed** one identity policy per role below, scoped to the exact actions and ARNs that role used in our tested pipeline. The pipeline policies are derived from what Step Functions' console listed as required when it tried to auto-create a role (lambda:InvokeFunction, s3:GetObject/PutObject, sns:Publish).

## Deployment status
| File | Applies to | Status | Notes |
|---|---|---|---|
| `kms-key-policy.json` | KMS key `marrowick-data-key` | ✅ **Deployed** | Admin = voclabs, users = LabRole + voclabs (separation of duties) |
| `bucket-policy-raw.json` / `-quarantine` / `-curated` | 3 tenant buckets | ✅ **Deployed** | TLS-only, KMS-only uploads, our key only – **tested** (SSE-S3 upload denied) |
| ↳ `TenantIsolationClinicA/B/C` statements | same | ⚠️ **Deployed, untestable** | Require principals tagged `tenant=clinic-x`; lab cannot create tagged roles |
| `roles/clinic-a-analyst.policy.json` | Clinic analyst role | 📐 **Design-only** | IAM role creation blocked |
| `roles/corporate-analyst.policy.json` | Corporate analyst role | 📐 **Design-only** | IAM role creation blocked |
| `roles/pii-scan-lambda.policy.json` + `.trust.json` | Lambda execution role | 📐 **Design-only** | Ran as LabRole instead |
| `roles/pii-gate-stepfunctions.policy.json` + `.trust.json` | Step Functions role | 📐 **Design-only** | Ran as LabRole instead |
| `roles/curated-crawler.policy.json` + `.trust.json` | Glue crawler role | 📐 **Design-only** | Ran as LabRole instead |
| `../lakeformation/permission-matrix.md` | Lake Formation grants & filters | 📐 **Design-only** | voclabs denied `lakeformation:GetDataLakeSettings` |

## Statement-by-statement intent

### Analyst roles (`clinic-a-analyst`, `corporate-analyst`)
| Sid | Purpose |
|---|---|
| RunQueriesInOwnWorkgroupOnly | Athena only in a dedicated workgroup (`marrowick-clinic-a` / `marrowick-corporate`), so query history, cost and result location are separated per role |
| WriteOwnQueryResultsOnly | Results bucket access limited to that workgroup's prefix |
| LakeFormationVendedCredentials | Data is read through Lake Formation-vended temporary credentials, which apply the row/column filters |
| ReadCatalogForCuratedDbOnly | Catalog metadata for the curated database only – never raw/quarantine/audit |
| **DenyDirectS3AccessToTenantData** | Explicit deny on all tenant buckets. Analysts can only see data *through* Lake Formation filters; this closes the bypass that makes our Athena-view fallback weaker |
| DenyAuditDatabase (clinic) | Clinic analysts cannot read the CloudTrail audit table |

Row/column scoping (clinic-a rows only; no `notes_field`; corporate also no `patient_ref`) is **not** expressed in IAM – IAM cannot filter rows. It is enforced by the Lake Formation data cells filters in `lakeformation/permission-matrix.md`.

### Pipeline roles
| Role | Can | Cannot |
|---|---|---|
| pii-scan-lambda | Read **raw** objects; decrypt with the data key **only via S3**; write its own logs | Write anywhere; read curated/quarantine; call KMS directly |
| pii-gate-stepfunctions | Invoke **only** `marrowick-pii-scan`; read raw; write quarantine **or** curated; publish to **one** SNS topic | Delete objects; modify raw; read curated; administer the key |
| curated-crawler | Read **curated** only; create/update tables in `marrowick_curated` only | See raw/quarantine (so PII that was blocked can never be catalogued) |

`kms:ViaService = s3.us-east-1.amazonaws.com` means a stolen role credential cannot call `kms:Decrypt` directly on arbitrary ciphertext – only S3 can use the key on the role's behalf.

## Residual risk (honest statement)
Because LabRole was used everywhere, in *this deployment* the Lambda could technically have written to curated, and the analyst-equivalent queries ran with admin-level permissions. Controls that **were** enforced regardless of IAM: the bucket policies (deny wins over any IAM allow), the KMS key policy, and the gate logic itself. The design-only policies above are what we would deploy in a production account.
