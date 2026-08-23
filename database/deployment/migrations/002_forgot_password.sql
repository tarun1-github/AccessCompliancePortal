USE [CPDB];
GO

IF COL_LENGTH('dbo.ac_engineers', 'password_reset_token') IS NULL
BEGIN
    ALTER TABLE dbo.ac_engineers
    ADD password_reset_token NVARCHAR(255) NULL;
END
GO

IF COL_LENGTH('dbo.ac_engineers', 'password_reset_expires_at') IS NULL
BEGIN
    ALTER TABLE dbo.ac_engineers
    ADD password_reset_expires_at DATETIME2 NULL;
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_ac_engineers_password_reset_token'
      AND object_id = OBJECT_ID('dbo.ac_engineers')
)
BEGIN
    CREATE UNIQUE INDEX UX_ac_engineers_password_reset_token
    ON dbo.ac_engineers(password_reset_token)
    WHERE password_reset_token IS NOT NULL;
END
GO