USE [CPDB];
GO

-- LAB ONLY
-- Resets vbhat so the first-time password setup flow can be tested.

UPDATE dbo.ac_engineers
SET
    password_hash = NULL,
    password_set_at = NULL,
    must_set_password = 1,
    verification_token = 'LAB-SETUP-VBHAT-001'
WHERE alias = 'vbhat';
GO