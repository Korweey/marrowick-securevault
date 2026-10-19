<!--
Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
File: lakeformation/permission-matrix.md – Lake Formation permission matrix (DESIGN-ONLY in Learner Lab)
-->

# Lake Formation permission matrix

**Status: design-only.** In the Learner Lab, the console role `voclabs` is denied
`lakeformation:GetDataLakeSettings` (see `evidence/week2/issues/issue4_lakeformation_access_denied.png`),
so no data-lake administrator can be registered and no Lake Formation grants can be made.
The same restrictions were implemented and **tested** with role-scoped Athena views
(`sql/01_access_views.sql`, `sql/02_access_tests.sql`).

| Principal (production) | Resource | Permission | Row filter | Columns |
|---|---|---|---|---|
| `role/marrowick-clinic-a-analyst` | `marrowick_curated.marrowick_curated_004716017211` | SELECT via data cells filter `clinic_a_only` | `tenant_id = 'clinic-a'` | all **except** `notes_field` |
| `role/marrowick-clinic-b-analyst` | same | SELECT via `clinic_b_only` | `tenant_id = 'clinic-b'` | all except `notes_field` |
| `role/marrowick-clinic-c-analyst` | same | SELECT via `clinic_c_only` | `tenant_id = 'clinic-c'` | all except `notes_field` |
| `role/marrowick-corporate-analyst` | same | SELECT via `corporate_no_pii` | `TRUE` (all rows) | all **except** `notes_field`, `patient_ref` |
| `role/LabRole` (pipeline) | database `marrowick_curated` | CREATE_TABLE, ALTER (crawler only) | – | – |
| `IAMAllowedPrincipals` | the table | **revoked** | – | – |

## Data cells filters (CLI, for a non-restricted account)
```bash
aws lakeformation create-data-cells-filter --table-data '{
  "TableCatalogId":"004716017211","DatabaseName":"marrowick_curated",
  "TableName":"marrowick_curated_004716017211","Name":"clinic_a_only",
  "RowFilter":{"FilterExpression":"tenant_id = '\''clinic-a'\''"},
  "ColumnWildcard":{"ExcludedColumnNames":["notes_field"]}}'

aws lakeformation create-data-cells-filter --table-data '{
  "TableCatalogId":"004716017211","DatabaseName":"marrowick_curated",
  "TableName":"marrowick_curated_004716017211","Name":"corporate_no_pii",
  "RowFilter":{"AllRowsWildcard":{}},
  "ColumnWildcard":{"ExcludedColumnNames":["notes_field","patient_ref"]}}'

aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=arn:aws:iam::004716017211:role/marrowick-clinic-a-analyst \
  --permissions SELECT \
  --resource '{"DataCellsFilter":{"TableCatalogId":"004716017211","DatabaseName":"marrowick_curated",
              "TableName":"marrowick_curated_004716017211","Name":"clinic_a_only"}}'
```

## Why views are a weaker substitute (honest limitation)
A view restricts what a query *through the view* returns, but any principal that can read the
base table (or the S3 objects) can bypass it. Lake Formation enforces the filter on the table
itself for every engine. In production, analysts would be granted the filters above and **no**
direct access to the base table or curated bucket.
