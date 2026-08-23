USE [CPDB];
GO

IF COL_LENGTH('dbo.ac_engineers','password_hash') IS NULL
    ALTER TABLE dbo.ac_engineers ADD password_hash varchar(255) NULL;
GO

IF COL_LENGTH('dbo.ac_engineers','password_set_at') IS NULL
    ALTER TABLE dbo.ac_engineers ADD password_set_at datetime2 NULL;
GO

IF COL_LENGTH('dbo.ac_engineers','must_set_password') IS NULL
BEGIN
    ALTER TABLE dbo.ac_engineers ADD must_set_password bit NOT NULL
        CONSTRAINT DF_ac_engineers_must_set_password DEFAULT (1);
END
GO

IF COL_LENGTH('dbo.ac_engineers','last_login_at') IS NULL
    ALTER TABLE dbo.ac_engineers ADD last_login_at datetime2 NULL;
GO
