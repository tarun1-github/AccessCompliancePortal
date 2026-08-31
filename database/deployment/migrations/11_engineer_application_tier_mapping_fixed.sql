USE [CPDB];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

/*
 FIX for migration 10:
 The previous backup used SELECT a.* INTO, which copied the identity
 property of ac_engineer_application_access.id. A subsequent INSERT
 therefore failed with SQL Server error 8101.

 This version uses an explicit backup schema where id is NOT IDENTITY.
 Do NOT run migration 10 again. Run this migration instead.
*/

BEGIN TRY
    BEGIN TRANSACTION;

    /* ========================================================
       1. Application -> engineer tier matrix
       ======================================================== */
    IF OBJECT_ID(N'dbo.ac_application_tier_access', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ac_application_tier_access
        (
            id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_AC_APPLICATION_TIER_ACCESS PRIMARY KEY,
            application_id INT NOT NULL,
            display_name NVARCHAR(200) NOT NULL,
            tier1_access BIT NOT NULL CONSTRAINT DF_AC_APP_TIER_T1 DEFAULT(0),
            tier2_access BIT NOT NULL CONSTRAINT DF_AC_APP_TIER_T2 DEFAULT(0),
            tier3_access BIT NOT NULL CONSTRAINT DF_AC_APP_TIER_T3 DEFAULT(0),
            im_above_access BIT NOT NULL CONSTRAINT DF_AC_APP_TIER_IM DEFAULT(0),
            active BIT NOT NULL CONSTRAINT DF_AC_APP_TIER_ACTIVE DEFAULT(1),
            source_label NVARCHAR(200) NULL,
            created_at DATETIME2 NOT NULL CONSTRAINT DF_AC_APP_TIER_CREATED DEFAULT(GETDATE()),
            updated_at DATETIME2 NOT NULL CONSTRAINT DF_AC_APP_TIER_UPDATED DEFAULT(GETDATE()),
            CONSTRAINT UQ_AC_APPLICATION_TIER_ACCESS_APPLICATION UNIQUE(application_id)
        );
    END;

    /* ========================================================
       2. Safe backup. id is deliberately NOT IDENTITY.
       ======================================================== */
    IF OBJECT_ID(N'dbo.ac_engineer_application_access_mapping_backup_v2', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ac_engineer_application_access_mapping_backup_v2
        (
            id INT NOT NULL,
            engineer_id INT NULL,
            application_id INT NULL,
            access_status NVARCHAR(50) NULL,
            verification_status NVARCHAR(50) NULL,
            last_verified_date DATETIME2 NULL,
            remarks NVARCHAR(200) NULL,
            updated_at DATETIME2 NULL,
            arm_ticket NVARCHAR(100) NULL,
            ticket_status NVARCHAR(30) NULL,
            next_reminder_date DATETIME2 NULL,
            last_email_sent_at DATETIME2 NULL,
            email_count INT NULL,
            backup_at DATETIME2 NOT NULL
        );
        CREATE INDEX IX_AC_ACCESS_BACKUP_V2_ID
            ON dbo.ac_engineer_application_access_mapping_backup_v2(id);
    END;

    INSERT INTO dbo.ac_engineer_application_access_mapping_backup_v2
    (
        id,
        engineer_id,
        application_id,
        access_status,
        verification_status,
        last_verified_date,
        remarks,
        updated_at,
        arm_ticket,
        ticket_status,
        next_reminder_date,
        last_email_sent_at,
        email_count,
        backup_at
    )
    SELECT
        a.id,
        a.engineer_id,
        a.application_id,
        a.access_status,
        a.verification_status,
        a.last_verified_date,
        a.remarks,
        a.updated_at,
        a.arm_ticket,
        a.ticket_status,
        a.next_reminder_date,
        a.last_email_sent_at,
        a.email_count,
        SYSDATETIME()
    FROM dbo.ac_engineer_application_access AS a
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ac_engineer_application_access_mapping_backup_v2 AS b
        WHERE b.id = a.id
    );

    /* ========================================================
       3. Source application matrix
       ======================================================== */
    DECLARE @Catalog TABLE
    (
        source_label NVARCHAR(200) NOT NULL,
        target_application_name NVARCHAR(200) NOT NULL,
        display_name NVARCHAR(200) NOT NULL,
        tier1_access BIT NOT NULL,
        tier2_access BIT NOT NULL,
        tier3_access BIT NOT NULL,
        im_above_access BIT NOT NULL
    );

    INSERT INTO @Catalog
    (source_label,target_application_name,display_name,tier1_access,tier2_access,tier3_access,im_above_access)
    VALUES
    (N'Bank Email',N'Bank Email',N'Bank Email',1,1,1,1),
    (N'HVD Desktop Access',N'HVD Desktop Access',N'HVD Desktop Access',1,1,1,1),
    (N'BOFA',N'BOFA',N'BOFA',1,1,1,1),
    (N'AUTHENTICATOR',N'Authenticator',N'AUTHENTICATOR',1,1,1,1),
    (N'SKYPE',N'Skype',N'SKYPE',1,1,1,1),
    (N'MATTER MOST',N'MatterMost',N'MATTER MOST',1,1,1,1),
    (N'ELEVATED ID',N'Elevated ID',N'ELEVATED ID',1,1,1,1),
    (N'V-CENTER',N'Vsphere',N'V-CENTER',1,1,1,1),
    (N'EV SITE',N'EV SITE',N'EV SITE',1,1,1,1),
    (N'UCAT - Moved to (CWM)',N'UCAT',N'UCAT',1,1,1,1),
    (N'RTI Inventory',N'RTI Inventory',N'RTI Inventory',1,1,1,1),
    (N'Inventory Dashboard',N'Inventory Dashboard',N'Inventory Dashboard',1,1,1,1),
    (N'MLFC',N'MLFC',N'MLFC',1,1,1,1),
    (N'HPNA',N'HPNA',N'HPNA',1,1,1,1),
    (N'TOOLS SERVER',N'Tool servers',N'TOOLS SERVER',1,1,1,1),
    (N'CWM',N'CWM',N'CWM',1,1,1,1),
    (N'NDC.WHITELIS',N'NDC',N'NDC.WHITELIS',1,1,1,1),
    (N'ECSL_Splunk_cisco_AP',N'ECSL_Splunk_cisco_AP',N'ECSL_Splunk_cisco_AP',1,1,1,1),
    (N'BPA',N'BPA',N'BPA',1,1,1,1),
    (N'VENAFI',N'VENAFI',N'VENAFI',0,0,1,1),
    (N'NETSCOUT/SONUS',N'Netscout',N'NETSCOUT/SONUS',0,0,1,1),
    (N'IPMF',N'IPMF',N'IPMF',0,1,1,1),
    (N'Windows or Linux Servers',N'Windows or Linux Servers',N'Windows or Linux Servers',0,1,1,1),
    (N'CUCM',N'Add and Revoke Access to CUCM/CUC',N'CUCM',1,1,1,1),
    (N'TACAS',N'TACAS',N'TACAS',1,1,1,1),
    (N'EPAM - AD Group',N'EPAM - AD Group',N'EPAM - AD Group',1,1,1,1),
    (N'TTSM REMEDY',N'TTSM REMEDY',N'TTSM REMEDY',1,1,1,1),
    (N'CMSPR',N'CMSPR',N'CMSPR',1,1,1,1),
    (N'MEDT - New Whitelisting',N'MEDT - New Whitelisting',N'MEDT - New Whitelisting',1,1,1,1),
    (N'WebEx Control Hub / Softphone',N'WebEx Control Hub / Softphone',N'WebEx Control Hub / Softphone',1,1,1,0),
    (N'Horizon - New Confluence',N'Ansible horizon',N'Horizon - New Confluence',0,0,0,1);

    /* ========================================================
       4. Application catalog
       ======================================================== */
    INSERT INTO dbo.ac_applications(name,description,active)
    SELECT c.target_application_name,
           N'Application from engineer tier access matrix',
           1
    FROM @Catalog c
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.ac_applications a
        WHERE a.name = c.target_application_name
    );

    /* ========================================================
       5. Upsert mapping
       ======================================================== */
    UPDATE m
       SET m.display_name = c.display_name,
           m.tier1_access = c.tier1_access,
           m.tier2_access = c.tier2_access,
           m.tier3_access = c.tier3_access,
           m.im_above_access = c.im_above_access,
           m.source_label = c.source_label,
           m.active = 1,
           m.updated_at = SYSDATETIME()
    FROM dbo.ac_application_tier_access m
    INNER JOIN dbo.ac_applications a
        ON a.id = m.application_id
    INNER JOIN @Catalog c
        ON c.target_application_name = a.name;

    INSERT INTO dbo.ac_application_tier_access
    (
        application_id,display_name,tier1_access,tier2_access,tier3_access,
        im_above_access,active,source_label
    )
    SELECT
        a.id,c.display_name,c.tier1_access,c.tier2_access,c.tier3_access,
        c.im_above_access,1,c.source_label
    FROM @Catalog c
    INNER JOIN dbo.ac_applications a
        ON a.name = c.target_application_name
    WHERE NOT EXISTS
    (
        SELECT 1 FROM dbo.ac_application_tier_access m
        WHERE m.application_id = a.id
    );

    /* ========================================================
       6. Engineer levels
       ======================================================== */
    DECLARE @EngineerLevels TABLE
    (
        alias NVARCHAR(100) NOT NULL,
        level_code NVARCHAR(50) NOT NULL
    );

    INSERT INTO @EngineerLevels(alias,level_code) VALUES
    (N'aksharma',N'L2'),(N'nibsingh',N'L2'),(N'nsharma',N'L2'),(N'sagarwal',N'L2'),(N'asaxena',N'L2'),
    (N'ptariyal',N'QM'),(N'dgarg',N'L1'),(N'msavad',N'L1'),(N'mpasha',N'L1'),(N'rkhanna',N'IM'),
    (N'ttaneja',N'L3'),(N'vbhat',N'L3'),(N'krohan',N'L3'),(N'snambiar',N'IM'),(N'nitsingh',N'L2'),
    (N'sahmad',N'L2'),(N'jsharma',N'L2'),(N'vsehrawat',N'L2'),(N'abhatt',N'L2'),(N'csharma',N'QM'),
    (N'usachdev',N'L1'),(N'karamjeet',N'L1'),(N'mkumar',N'L1'),(N'asingh',N'IM'),(N'ayadav',N'L3'),
    (N'mshaik',N'L3'),(N'pkumari',N'L3'),(N'bmiller',N'L2'),(N'mpearson',N'L2'),(N'mwilmers',N'L2'),
    (N'mtikhov',N'L3'),(N'dludington',N'TL'),(N'jhagenburg',N'IM'),(N'rhamlett',N'IM'),(N'chaskins',N'IM'),
    (N'hchaudhary',N'L2'),(N'lsimte',N'L2'),(N'arsharma',N'L2'),(N'abhardwaj',N'L2'),(N'msingh',N'L1'),
    (N'vdutt',N'L1'),(N'hmudgal',N'L1'),(N'dkundu',N'L1'),(N'spandey',N'QM'),(N'kmurugesan',N'L3'),
    (N'iahmad',N'L3'),(N'sbhadola',N'IM');

    UPDATE e
       SET e.level = x.level_code
    FROM dbo.ac_engineers e
    INNER JOIN @EngineerLevels x
        ON LOWER(LTRIM(RTRIM(e.alias))) = LOWER(x.alias);

    /* ========================================================
       7. Remove assignments not allowed by the matrix
       ======================================================== */
    DELETE a
    FROM dbo.ac_engineer_application_access a
    INNER JOIN dbo.ac_engineers e
        ON e.id = a.engineer_id
    LEFT JOIN dbo.ac_application_tier_access m
        ON m.application_id = a.application_id
       AND m.active = 1
    WHERE
        e.active = 0
        OR UPPER(ISNULL(e.role,N'USER')) = N'SUPERVISOR'
        OR m.application_id IS NULL
        OR CASE UPPER(LTRIM(RTRIM(ISNULL(e.level,N''))))
            WHEN N'L1' THEN m.tier1_access
            WHEN N'L2' THEN m.tier2_access
            WHEN N'L3' THEN m.tier3_access
            WHEN N'IM' THEN m.im_above_access
            WHEN N'QM' THEN m.im_above_access
            WHEN N'TL' THEN m.im_above_access
            ELSE 0
           END = 0;

    /* ========================================================
       8. Add missing assignments
       ======================================================== */
    INSERT INTO dbo.ac_engineer_application_access
    (
        engineer_id,application_id,access_status,verification_status,
        last_verified_date,remarks,updated_at,arm_ticket,ticket_status,
        next_reminder_date,last_email_sent_at,email_count
    )
    SELECT
        e.id,m.application_id,N'Required',N'Pending',NULL,NULL,GETDATE(),NULL,
        N'Not Required',NULL,NULL,0
    FROM dbo.ac_engineers e
    CROSS JOIN dbo.ac_application_tier_access m
    WHERE
        e.active = 1
        AND UPPER(ISNULL(e.role,N'USER')) <> N'SUPERVISOR'
        AND m.active = 1
        AND CASE UPPER(LTRIM(RTRIM(ISNULL(e.level,N''))))
            WHEN N'L1' THEN m.tier1_access
            WHEN N'L2' THEN m.tier2_access
            WHEN N'L3' THEN m.tier3_access
            WHEN N'IM' THEN m.im_above_access
            WHEN N'QM' THEN m.im_above_access
            WHEN N'TL' THEN m.im_above_access
            ELSE 0
            END = 1
        AND NOT EXISTS
        (
            SELECT 1
            FROM dbo.ac_engineer_application_access x
            WHERE x.engineer_id = e.id
              AND x.application_id = m.application_id
        );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

/* ============================================================
   VALIDATION
   ============================================================ */
SELECT
    e.name,
    e.alias,
    e.level,
    COUNT(a.id) AS application_count
FROM dbo.ac_engineers e
LEFT JOIN dbo.ac_engineer_application_access a
    ON a.engineer_id = e.id
WHERE e.active = 1
  AND UPPER(ISNULL(e.role,N'USER')) <> N'SUPERVISOR'
GROUP BY e.name,e.alias,e.level
ORDER BY e.name;

SELECT
    m.display_name,
    m.tier1_access,
    m.tier2_access,
    m.tier3_access,
    m.im_above_access,
    COUNT(a.id) AS assigned_rows
FROM dbo.ac_application_tier_access m
LEFT JOIN dbo.ac_engineer_application_access a
    ON a.application_id = m.application_id
WHERE m.active = 1
GROUP BY m.display_name,m.tier1_access,m.tier2_access,m.tier3_access,m.im_above_access
ORDER BY m.display_name;
GO
