USE [CPDB];
GO

/*
============================================================
Migration: 001_phase2_authentication
Purpose  : Add Phase 2A local authentication fields
Table    : dbo.ac_engineers

Safe to run multiple times.
Existing columns will not be modified.
============================================================
*/


/* ============================================================
   password_hash
   Stores the PBKDF2 password hash.
   Passwords are NEVER stored in plain text.
   ============================================================ */

IF COL_LENGTH(
    'dbo.ac_engineers',
    'password_hash'
) IS NULL
BEGIN

    ALTER TABLE dbo.ac_engineers
    ADD password_hash NVARCHAR(255) NULL;

    PRINT 'Added password_hash';

END
ELSE
BEGIN

    PRINT 'password_hash already exists';

END
GO


/* ============================================================
   password_set_at
   Stores when the engineer first/set their password.
   ============================================================ */

IF COL_LENGTH(
    'dbo.ac_engineers',
    'password_set_at'
) IS NULL
BEGIN

    ALTER TABLE dbo.ac_engineers
    ADD password_set_at DATETIME2 NULL;

    PRINT 'Added password_set_at';

END
ELSE
BEGIN

    PRINT 'password_set_at already exists';

END
GO


/* ============================================================
   must_set_password
   1 = engineer must set password
   0 = password has been configured
   ============================================================ */

IF COL_LENGTH(
    'dbo.ac_engineers',
    'must_set_password'
) IS NULL
BEGIN

    ALTER TABLE dbo.ac_engineers
    ADD must_set_password BIT NOT NULL
        CONSTRAINT DF_ac_engineers_must_set_password
        DEFAULT (1);

    PRINT 'Added must_set_password';

END
ELSE
BEGIN

    PRINT 'must_set_password already exists';

END
GO


/* ============================================================
   last_login_at
   Stores the last successful login timestamp.
   ============================================================ */

IF COL_LENGTH(
    'dbo.ac_engineers',
    'last_login_at'
) IS NULL
BEGIN

    ALTER TABLE dbo.ac_engineers
    ADD last_login_at DATETIME2 NULL;

    PRINT 'Added last_login_at';

END
ELSE
BEGIN

    PRINT 'last_login_at already exists';

END
GO


/* ============================================================
   VERIFICATION
   ============================================================ */

SELECT
    name AS column_name,
    system_type_name,
    is_nullable
FROM sys.dm_exec_describe_first_result_set(
    N'
    SELECT
        password_hash,
        password_set_at,
        must_set_password,
        last_login_at
    FROM dbo.ac_engineers
    ',
    NULL,
    0
);

GO

PRINT '============================================================';
PRINT '001_phase2_authentication completed successfully';
PRINT '============================================================';
GO