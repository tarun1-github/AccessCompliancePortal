USE [CPDB];
GO

/*
============================================================
Migration : 002_forgot_password
Purpose   : Add password reset functionality
Table     : dbo.ac_engineers

Reset token is temporary and expires.
============================================================
*/


/* Password reset token */

IF COL_LENGTH(
    'dbo.ac_engineers',
    'password_reset_token'
) IS NULL
BEGIN

    ALTER TABLE dbo.ac_engineers
    ADD password_reset_token NVARCHAR(255) NULL;

    PRINT 'Added password_reset_token';

END
ELSE
BEGIN

    PRINT 'password_reset_token already exists';

END
GO


/* Password reset token expiry */

IF COL_LENGTH(
    'dbo.ac_engineers',
    'password_reset_expires_at'
) IS NULL
BEGIN

    ALTER TABLE dbo.ac_engineers
    ADD password_reset_expires_at DATETIME2 NULL;

    PRINT 'Added password_reset_expires_at';

END
ELSE
BEGIN

    PRINT 'password_reset_expires_at already exists';

END
GO


/*
Create a filtered unique index.

Only non-NULL reset tokens need to be unique.
Multiple users can have NULL reset tokens.
*/

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name =
        'UX_ac_engineers_password_reset_token'
      AND object_id =
        OBJECT_ID('dbo.ac_engineers')
)
BEGIN

    CREATE UNIQUE NONCLUSTERED INDEX
        UX_ac_engineers_password_reset_token
    ON dbo.ac_engineers
        (password_reset_token)
    WHERE password_reset_token IS NOT NULL;

    PRINT 'Created password reset token index';

END
ELSE
BEGIN

    PRINT 'Password reset token index already exists';

END
GO


PRINT '============================================================';
PRINT '002_forgot_password completed';
PRINT '============================================================';
GO



IF COL_LENGTH('dbo.ac_engineers', 'password_reset_token') IS NULL
BEGIN
    ALTER TABLE dbo.ac_engineers
    ADD password_reset_token VARCHAR(255) NULL;
END
GO

IF COL_LENGTH('dbo.ac_engineers', 'password_reset_expires_at') IS NULL
BEGIN
    ALTER TABLE dbo.ac_engineers
    ADD password_reset_expires_at DATETIME2 NULL;
END
GO

