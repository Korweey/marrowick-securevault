-- Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
-- Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
-- File: sql/02_access_tests.sql – Access-separation tests (actually attempt the restricted queries)

-- T0 baseline (admin, base table): expect 615 rows, 3 tenants
SELECT tenant_id, count(*) AS rows FROM marrowick_curated_004716017211 GROUP BY tenant_id ORDER BY tenant_id;

-- T1 clinic analyst sees only own tenant: expect ONE row -> clinic-a | 191
SELECT tenant_id, count(*) AS rows FROM view_clinic_a_analyst GROUP BY tenant_id;

-- T2 clinic analyst tries another tenant's rows: expect 0 rows
SELECT * FROM view_clinic_a_analyst WHERE tenant_id = 'clinic-b' LIMIT 10;

-- T3 clinic analyst tries the free-text PII column: expect error COLUMN_NOT_FOUND
SELECT notes_field FROM view_clinic_a_analyst LIMIT 5;

-- T4 corporate analyst sees all tenants: expect clinic-a 191, clinic-b 243, clinic-c 181
SELECT tenant_id, count(*) AS rows FROM view_corporate_analyst GROUP BY tenant_id ORDER BY tenant_id;

-- T5 corporate analyst tries PII columns: expect error COLUMN_NOT_FOUND (both)
SELECT notes_field FROM view_corporate_analyst LIMIT 5;
SELECT patient_ref FROM view_corporate_analyst LIMIT 5;
