-- Project 4 – Marrowick Health Analytics (CCGC 5506, Humber, Fall 2026)
-- Group H: Qawiyy A. Rabiu (N10038749), Saheedat O. Abbas (N10038753)
-- File: sql/01_access_views.sql – Role-scoped Athena views (fallback for Lake Formation, which the Learner Lab blocks)
-- Run in Athena with database = marrowick_curated. Run each statement on its own.

-- Clinic analyst (Brambleton / clinic-a): OWN tenant rows only; free-text notes hidden.
-- patient_ref kept: a clinic needs its own pseudonymous patient IDs for care follow-up.
CREATE OR REPLACE VIEW view_clinic_a_analyst AS
SELECT encounter_id, tenant_id, encounter_date, encounter_type, diagnosis_code,
       patient_ref, clinician_id, billing_amount
FROM marrowick_curated_004716017211
WHERE tenant_id = 'clinic-a';

-- Corporate analyst: ALL tenants, but no PII-bearing columns
-- (notes_field = free text that leaked PII; patient_ref = would allow cross-clinic linkage).
CREATE OR REPLACE VIEW view_corporate_analyst AS
SELECT encounter_id, tenant_id, encounter_date, encounter_type, diagnosis_code,
       clinician_id, billing_amount
FROM marrowick_curated_004716017211;
