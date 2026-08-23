USE [master];
GO
IF DB_ID(N'CPDB') IS NULL
    CREATE DATABASE [CPDB];
GO
USE [CPDB];
GO

IF OBJECT_ID(N'dbo.ac_applications',N'U') IS NULL
CREATE TABLE dbo.ac_applications(
 id int IDENTITY(1,1) NOT NULL,
 name varchar(200) NOT NULL,
 description varchar(500) NULL,
 active bit NOT NULL,
 CONSTRAINT PK_AC_APPLICATIONS PRIMARY KEY CLUSTERED(id),
 CONSTRAINT UQ_AC_APPLICATIONS_NAME UNIQUE(name)
);
GO

IF OBJECT_ID(N'dbo.ac_engineers',N'U') IS NULL
CREATE TABLE dbo.ac_engineers(
 id int IDENTITY(1,1) NOT NULL,
 name varchar(150) NOT NULL,
 email varchar(200) NULL,
 level varchar(20) NOT NULL,
 rm_email varchar(200) NULL,
 active bit NOT NULL,
 created_at datetime2(7) NOT NULL,
 verification_token varchar(100) NULL,
 alias varchar(100) NULL,
 role varchar(20) NOT NULL,
 supervisor_id int NULL,
 CONSTRAINT PK_AC_ENGINEERS PRIMARY KEY CLUSTERED(id),
 CONSTRAINT UQ_ac_engineers_alias UNIQUE(alias),
 CONSTRAINT UQ_AC_ENGINEERS_NAME_LEVEL UNIQUE(name,level),
 CONSTRAINT FK_ac_engineers_supervisor FOREIGN KEY(supervisor_id) REFERENCES dbo.ac_engineers(id)
);
GO

IF OBJECT_ID(N'dbo.ac_engineer_application_access',N'U') IS NULL
CREATE TABLE dbo.ac_engineer_application_access(
 id int IDENTITY(1,1) NOT NULL,
 engineer_id int NOT NULL,
 application_id int NOT NULL,
 access_status varchar(30) NOT NULL,
 verification_status varchar(30) NOT NULL,
 last_verified_date datetime2(0) NULL,
 remarks varchar(2000) NULL,
 updated_at datetime2(7) NOT NULL,
 arm_ticket varchar(100) NULL,
 ticket_status varchar(30) NOT NULL,
 next_reminder_date datetime2(7) NULL,
 last_email_sent_at datetime2(7) NULL,
 email_count int NOT NULL,
 CONSTRAINT PK_AC_ENGINEER_APPLICATION_ACCESS PRIMARY KEY CLUSTERED(id),
 CONSTRAINT UQ_AC_ENGINEER_APPLICATION UNIQUE(engineer_id,application_id),
 CONSTRAINT FK_AC_ACCESS_ENGINEER FOREIGN KEY(engineer_id) REFERENCES dbo.ac_engineers(id),
 CONSTRAINT FK_AC_ACCESS_APPLICATION FOREIGN KEY(application_id) REFERENCES dbo.ac_applications(id)
);
GO

IF OBJECT_ID(N'dbo.ac_audit_log',N'U') IS NULL
CREATE TABLE dbo.ac_audit_log(
 id bigint IDENTITY(1,1) NOT NULL,
 engineer_id int NULL,
 application_id int NULL,
 action nvarchar(255) NULL,
 old_status nvarchar(max) NULL,
 new_status nvarchar(max) NULL,
 remarks nvarchar(max) NULL,
 performed_by nvarchar(255) NULL,
 performed_at datetime2(7) NOT NULL,
 CONSTRAINT PK_AC_AUDIT_LOG PRIMARY KEY CLUSTERED(id),
 CONSTRAINT FK_AC_AUDIT_ENGINEER FOREIGN KEY(engineer_id) REFERENCES dbo.ac_engineers(id),
 CONSTRAINT FK_AC_AUDIT_APPLICATION FOREIGN KEY(application_id) REFERENCES dbo.ac_applications(id)
);
GO

IF OBJECT_ID(N'dbo.ac_notification_log',N'U') IS NULL
CREATE TABLE dbo.ac_notification_log(
 id bigint IDENTITY(1,1) NOT NULL,
 engineer_id int NOT NULL,
 access_id int NULL,
 notification_type varchar(30) NOT NULL,
 recipient_email varchar(255) NOT NULL,
 cc_email varchar(255) NULL,
 subject varchar(500) NULL,
 sent_at datetime2(7) NULL,
 status varchar(20) NOT NULL,
 error_message varchar(max) NULL,
 created_at datetime2(7) NOT NULL,
 CONSTRAINT PK_ac_notification_log PRIMARY KEY CLUSTERED(id),
 CONSTRAINT FK_ac_notification_log_engineer FOREIGN KEY(engineer_id) REFERENCES dbo.ac_engineers(id),
 CONSTRAINT FK_ac_notification_log_access FOREIGN KEY(access_id) REFERENCES dbo.ac_engineer_application_access(id)
);
GO

IF OBJECT_ID(N'dbo.ac_portal_settings',N'U') IS NULL
CREATE TABLE dbo.ac_portal_settings(
 id int IDENTITY(1,1) NOT NULL,
 setting_key varchar(100) NOT NULL,
 setting_value varchar(500) NOT NULL,
 description varchar(500) NULL,
 updated_at datetime2(7) NOT NULL,
 updated_by varchar(255) NULL,
 CONSTRAINT PK_ac_portal_settings PRIMARY KEY CLUSTERED(id),
 CONSTRAINT UQ_ac_portal_settings_key UNIQUE(setting_key)
);
GO

IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE name=N'UX_AC_ENGINEERS_EMAIL' AND object_id=OBJECT_ID(N'dbo.ac_engineers'))
 CREATE UNIQUE INDEX UX_AC_ENGINEERS_EMAIL ON dbo.ac_engineers(email) WHERE email IS NOT NULL;
GO
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE name=N'UX_ac_engineers_verification_token' AND object_id=OBJECT_ID(N'dbo.ac_engineers'))
 CREATE UNIQUE INDEX UX_ac_engineers_verification_token ON dbo.ac_engineers(verification_token) WHERE verification_token IS NOT NULL;
GO
