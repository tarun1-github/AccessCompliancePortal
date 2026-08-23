USE [CPDB];
GO

/*
============================================================
Migration : 001_phase2_authentication
Purpose   : Add Phase 2A local authentication fields
Table     : dbo.ac_engineers

Safe to run multiple times.
============================================================
*/


/* password_hash */

IF COL_LENGTH('dbo.ac_engineers', 'password_hash') IS NULL
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


/* password_set_at */

IF COL_LENGTH('dbo.ac_engineers', 'password_set_at') IS NULL
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


/* must_set_password */

IF COL_LENGTH('dbo.ac_engineers', 'must_set_password') IS NULL
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


/* last_login_at */

IF COL_LENGTH('dbo.ac_engineers', 'last_login_at') IS NULL
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


PRINT '============================================================';
PRINT '001_phase2_authentication completed';
PRINT '============================================================';
GO