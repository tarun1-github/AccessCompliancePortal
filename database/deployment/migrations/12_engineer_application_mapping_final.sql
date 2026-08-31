USE [CPDB];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

/*
    FINAL ENGINEER -> LEVEL -> APPLICATION MAPPING
    Development branch only.

    Source matrix supplied by portal owner.

    Active applications represented below: 32 unique entries.
    Decommissioned applications intentionally excluded:
        - Intrado
        - CONFLUENCE

    Level interpretation:
        L1 -> Tier 1
        L2 -> Tier 2
        L3 -> Tier 3
        IM / QM / TL -> IM & Above

    Existing access rows are preserved when they remain eligible.
    Missing eligible rows are added.
    Ineligible current rows are removed only after an explicit backup.

    IMPORTANT:
        Run this script ONLY. Do not run the earlier mapping scripts 10/11.
*/

BEGIN TRY
    BEGIN TRANSACTION;

    /* ============================================================
       1. APPLICATION -> TIER MAPPING MASTER
       ============================================================ */

    IF OBJECT_ID(N'dbo.ac_application_tier_access', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ac_application_tier_access
        (
            id INT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_AC_APPLICATION_TIER_ACCESS PRIMARY KEY,
            application_id INT NOT NULL,
            display_name VARCHAR(200) NOT NULL,
            tier1_access BIT NOT NULL
                CONSTRAINT DF_AC_APP_TIER_T1 DEFAULT(0),
            tier2_access BIT NOT NULL
                CONSTRAINT DF_AC_APP_TIER_T2 DEFAULT(0),
            tier3_access BIT NOT NULL
                CONSTRAINT DF_AC_APP_TIER_T3 DEFAULT(0),
            im_above_access BIT NOT NULL
                CONSTRAINT DF_AC_APP_TIER_IM DEFAULT(0),
            active BIT NOT NULL
                CONSTRAINT DF_AC_APP_TIER_ACTIVE DEFAULT(1),
            source_label VARCHAR(200) NULL,
            created_at DATETIME2 NOT NULL
                CONSTRAINT DF_AC_APP_TIER_CREATED DEFAULT(GETDATE()),
            updated_at DATETIME2 NOT NULL
                CONSTRAINT DF_AC_APP_TIER_UPDATED DEFAULT(GETDATE()),
            CONSTRAINT UQ_AC_APPLICATION_TIER_ACCESS_APPLICATION
                UNIQUE(application_id)
        );
    END;

    /* ============================================================
       2. SAFE BACKUP OF EXISTING ACCESS DATA
       ============================================================ */

    IF OBJECT_ID(N'dbo.ac_engineer_application_access_mapping_backup_v3', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ac_engineer_application_access_mapping_backup_v3
        (
            backup_id BIGINT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_AC_EAA_MAPPING_BACKUP_V3 PRIMARY KEY,
            source_id INT NOT NULL,
            engineer_id INT NULL,
            application_id INT NULL,
            access_status VARCHAR(30) NULL,
            verification_status VARCHAR(30) NULL,
            last_verified_date DATETIME2 NULL,
            remarks VARCHAR(2000) NULL,
            updated_at DATETIME2 NULL,
            arm_ticket VARCHAR(100) NULL,
            ticket_status VARCHAR(30) NULL,
            next_reminder_date DATETIME2 NULL,
            last_email_sent_at DATETIME2 NULL,
            email_count INT NULL,
            backup_at DATETIME2 NOT NULL
        );
    END;

    INSERT INTO dbo.ac_engineer_application_access_mapping_backup_v3
    (
        source_id,
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
        FROM dbo.ac_engineer_application_access_mapping_backup_v3 AS b
        WHERE b.source_id = a.id
    );

    /* ============================================================
       3. EXACT ACTIVE MATRIX
       ============================================================ */

    DECLARE @Catalog TABLE
    (
        source_label VARCHAR(200) NOT NULL,
        application_name VARCHAR(200) NOT NULL,
        display_name VARCHAR(200) NOT NULL,
        tier1_access BIT NOT NULL,
        tier2_access BIT NOT NULL,
        tier3_access BIT NOT NULL,
        im_above_access BIT NOT NULL
    );

    INSERT INTO @Catalog
    (
        source_label,
        application_name,
        display_name,
        tier1_access,
        tier2_access,
        tier3_access,
        im_above_access
    )
    VALUES
    ('Bank Email', 'Bank Email', 'Bank Email', 1,1,1,1),
    ('HVD Desktop Access', 'HVD Desktop Access', 'HVD Desktop Access', 1,1,1,1),
    ('BOFA', 'BOFA', 'BOFA', 1,1,1,1),
    ('AUTHENTICATOR', 'Authenticator', 'AUTHENTICATOR', 1,1,1,1),
    ('SKYPE', 'Skype', 'SKYPE', 1,1,1,1),
    ('MATTER MOST', 'MatterMost', 'MATTER MOST', 1,1,1,1),
    ('ELEVATED ID', 'Elevated ID', 'ELEVATED ID', 1,1,1,1),
    ('V-CENTER', 'Vsphere', 'V-CENTER', 1,1,1,1),
    ('EV SITE SEARCH', 'EV SITE SEARCH', 'EV SITE SEARCH', 1,1,1,1),
    ('UCAT - Moved to (CWM)', 'UCAT', 'UCAT - Moved to (CWM)', 1,1,1,1),
    ('RTI Inventory', 'RTI Inventory', 'RTI Inventory', 1,1,1,1),
    ('Inventory Dashboard', 'Inventory Dashboard', 'Inventory Dashboard', 1,1,1,1),
    ('MLFC', 'MLFC', 'MLFC', 1,1,1,1),
    ('HPNA', 'HPNA', 'HPNA', 1,1,1,1),
    ('TOOLS SERVER', 'Tool servers', 'TOOLS SERVER', 1,1,1,1),
    ('CWM', 'CWM', 'CWM', 1,1,1,1),
    ('NDC.WHITELIST', 'NDC', 'NDC.WHITELIST', 1,1,1,1),
    ('ECSL_Splunk_cisco_AP', 'ECSL_Splunk_cisco_AP', 'ECSL_Splunk_cisco_AP', 1,1,1,1),
    ('BPA', 'BPA', 'BPA', 1,1,1,1),
    ('VENAFI', 'VENAFI', 'VENAFI', 0,0,1,0),
    ('NETSCOUT/SONUS', 'Netscout', 'NETSCOUT/SONUS', 1,1,1,1),
    ('IPMF', 'IPMF', 'IPMF', 0,1,1,1),
    ('Windows or Linux Servers, ciscosup,pbciscop', 'Windows or Linux Servers, ciscosup,pbciscop', 'Windows or Linux Servers, ciscosup,pbciscop', 1,1,1,1),
    ('CUCM', 'Add and Revoke Access to CUCM/CUC', 'CUCM', 1,1,1,1),
    ('TACAS', 'TACAS', 'TACAS', 1,1,1,1),
    ('EPAM - AD Group', 'EPAM - AD Group', 'EPAM - AD Group', 1,1,1,1),
    ('2nd HVD', '2nd HVD', '2nd HVD', 1,1,1,1),
    ('TTSM REMEDY', 'TTSM REMEDY', 'TTSM REMEDY', 1,1,1,1),
    ('CMSP', 'CMSP', 'CMSP', 1,1,1,1),
    ('MEDT - New Whitelisting', 'MEDT - New Whitelisting', 'MEDT - New Whitelisting', 1,1,1,1),
    ('WebEx Control Hub/Softphone', 'WebEx Control Hub/Softphone', 'WebEx Control Hub/Softphone', 1,1,1,0),
    ('Horizon - Replaces Confluence', 'Horizon - Replaces Confluence', 'Horizon - Replaces Confluence', 0,0,0,1);

    /* ============================================================
       4. ADD ONLY MISSING APPLICATION MASTER ROWS
       ============================================================ */

    INSERT INTO dbo.ac_applications
    (
        name,
        description,
        active
    )
    SELECT
        c.application_name,
        'Application from engineer access tier matrix',
        1
    FROM @Catalog c
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ac_applications a
        WHERE LOWER(LTRIM(RTRIM(a.name))) = LOWER(LTRIM(RTRIM(c.application_name)))
    );

    /* ============================================================
       5. SYNCHRONIZE TIER MATRIX
       ============================================================ */

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
        ON LOWER(LTRIM(RTRIM(a.name))) = LOWER(LTRIM(RTRIM(c.application_name)));

    INSERT INTO dbo.ac_application_tier_access
    (
        application_id,
        display_name,
        tier1_access,
        tier2_access,
        tier3_access,
        im_above_access,
        active,
        source_label
    )
    SELECT
        a.id,
        c.display_name,
        c.tier1_access,
        c.tier2_access,
        c.tier3_access,
        c.im_above_access,
        1,
        c.source_label
    FROM @Catalog c
    INNER JOIN dbo.ac_applications a
        ON LOWER(LTRIM(RTRIM(a.name))) = LOWER(LTRIM(RTRIM(c.application_name)))
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ac_application_tier_access m
        WHERE m.application_id = a.id
    );

    /* ============================================================
       6. DEACTIVATE MAPPINGS NOT IN THE CURRENT MATRIX
       This excludes old/decommissioned mappings from future use.
       ============================================================ */

    UPDATE m
       SET m.active = 0,
           m.updated_at = SYSDATETIME()
    FROM dbo.ac_application_tier_access m
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM @Catalog c
        INNER JOIN dbo.ac_applications a
            ON LOWER(LTRIM(RTRIM(a.name))) = LOWER(LTRIM(RTRIM(c.application_name)))
        WHERE a.id = m.application_id
    );

    /* ============================================================
       7. ENGINEER LEVELS FROM SUPPLIED ENGINEER MATRIX
       ============================================================ */

    DECLARE @EngineerLevels TABLE
    (
        alias VARCHAR(100) NOT NULL,
        level_code VARCHAR(20) NOT NULL
    );

    INSERT INTO @EngineerLevels(alias, level_code)
    VALUES
    ('aksharma','L2'),
    ('nibsingh','L2'),
    ('nsharma','L2'),
    ('sagarwal','L2'),
    ('asaxena','L2'),
    ('ptariyal','QM'),
    ('dgarg','L1'),
    ('msavad','L1'),
    ('mpasha','L1'),
    ('rkhanna','IM'),
    ('ttaneja','L3'),
    ('vbhat','L3'),
    ('krohan','L3'),
    ('snambiar','IM'),
    ('nitsingh','L2'),
    ('sahmad','L2'),
    ('jsharma','L2'),
    ('vsehrawat','L2'),
    ('abhatt','L2'),
    ('csharma','QM'),
    ('usachdev','L1'),
    ('karamjeet','L1'),
    ('mkumar','L1'),
    ('asingh','IM'),
    ('ayadav','L3'),
    ('mshaik','L3'),
    ('pkumari','L3'),
    ('bmiller','L2'),
    ('mpearson','L2'),
    ('mwilmers','L2'),
    ('mtikhov','L3'),
    ('dludington','TL'),
    ('jhagenburg','IM'),
    ('rhamlett','IM'),
    ('chaskins','IM'),
    ('hchaudhary','L2'),
    ('lsimte','L2'),
    ('arsharma','L2'),
    ('abhardwaj','L2'),
    ('msingh','L1'),
    ('vdutt','L1'),
    ('hmudgal','L1'),
    ('dkundu','L1'),
    ('spandey','QM'),
    ('kmurugesan','L3'),
    ('iahmad','L3'),
    ('sbhadola','IM');

    UPDATE e
       SET e.level = x.level_code
    FROM dbo.ac_engineers e
    INNER JOIN @EngineerLevels x
        ON LOWER(LTRIM(RTRIM(e.alias))) = LOWER(x.alias);

    /* ============================================================
       8. REMOVE CURRENT ACCESS WHICH IS NOT ELIGIBLE
       ============================================================ */

    DELETE a
    FROM dbo.ac_engineer_application_access a
    INNER JOIN dbo.ac_engineers e
        ON e.id = a.engineer_id
    LEFT JOIN dbo.ac_application_tier_access m
        ON m.application_id = a.application_id
       AND m.active = 1
    WHERE
        e.active = 0
        OR UPPER(ISNULL(e.role,'USER')) = 'SUPERVISOR'
        OR m.application_id IS NULL
        OR CASE UPPER(LTRIM(RTRIM(ISNULL(e.level,''))))
            WHEN 'L1' THEN m.tier1_access
            WHEN 'L2' THEN m.tier2_access
            WHEN 'L3' THEN m.tier3_access
            WHEN 'IM' THEN m.im_above_access
            WHEN 'QM' THEN m.im_above_access
            WHEN 'TL' THEN m.im_above_access
            ELSE 0
          END = 0;

    /* ============================================================
       9. ADD MISSING ELIGIBLE ACCESS
       ============================================================ */

    INSERT INTO dbo.ac_engineer_application_access
    (
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
        email_count
    )
    SELECT
        e.id,
        m.application_id,
        'Required',
        'Pending',
        NULL,
        NULL,
        GETDATE(),
        NULL,
        'Not Started',
        NULL,
        NULL,
        0
    FROM dbo.ac_engineers e
    CROSS JOIN dbo.ac_application_tier_access m
    WHERE
        e.active = 1
        AND UPPER(ISNULL(e.role,'USER')) <> 'SUPERVISOR'
        AND m.active = 1
        AND CASE UPPER(LTRIM(RTRIM(ISNULL(e.level,''))))
            WHEN 'L1' THEN m.tier1_access
            WHEN 'L2' THEN m.tier2_access
            WHEN 'L3' THEN m.tier3_access
            WHEN 'IM' THEN m.im_above_access
            WHEN 'QM' THEN m.im_above_access
            WHEN 'TL' THEN m.im_above_access
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
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

/* ============================================================
   VALIDATION 1 - ENGINEER COUNTS
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
  AND UPPER(ISNULL(e.role,'USER')) <> 'SUPERVISOR'
GROUP BY
    e.name,
    e.alias,
    e.level
ORDER BY
    e.name;
GO

/* ============================================================
   VALIDATION 2 - CURRENT MATRIX
   ============================================================ */
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
GROUP BY
    m.display_name,
    m.tier1_access,
    m.tier2_access,
    m.tier3_access,
    m.im_above_access
ORDER BY
    m.display_name;
GO

/* ============================================================
   VALIDATION 3 - APPLICATION COUNT BY LEVEL
   ============================================================ */
SELECT
    e.level,
    COUNT(DISTINCT e.id) AS engineer_count,
    COUNT(a.id) AS total_assignments,
    CASE
        WHEN COUNT(DISTINCT e.id) = 0 THEN 0
        ELSE COUNT(a.id) / COUNT(DISTINCT e.id)
    END AS avg_assignments_per_engineer
FROM dbo.ac_engineers e
LEFT JOIN dbo.ac_engineer_application_access a
    ON a.engineer_id = e.id
WHERE e.active = 1
  AND UPPER(ISNULL(e.role,'USER')) <> 'SUPERVISOR'
GROUP BY e.level
ORDER BY
    CASE e.level
        WHEN 'L1' THEN 1
        WHEN 'L2' THEN 2
        WHEN 'L3' THEN 3
        WHEN 'IM' THEN 4
        WHEN 'QM' THEN 5
        WHEN 'TL' THEN 6
        ELSE 99
    END;
GO
