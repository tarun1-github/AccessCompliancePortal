USE [CPDB];
GO

/*
    Engineer/Application Tier Mapping - development branch

    Source:
      - Tier matrix supplied for the Access Compliance Portal
      - Engineer level mapping supplied by the portal owner

    Tier interpretation:
      L1 -> Tier 1
      L2 -> Tier 2
      L3 -> Tier 3
      IM / QM / TL -> IM & Above

    Decommissioned applications from the supplied matrix are intentionally
    NOT included in the catalog below.

    IMPORTANT:
      This migration keeps a backup of the current access table before
      reconciling it. Only access rows outside the approved tier/application
      matrix are removed. Existing verification/ARM data for eligible rows
      is preserved.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    /* ========================================================
       1. Mapping master
       ======================================================== */

    IF OBJECT_ID(N'dbo.ac_application_tier_access', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.ac_application_tier_access
        (
            id INT IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_AC_APPLICATION_TIER_ACCESS PRIMARY KEY,

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

            CONSTRAINT UQ_AC_APPLICATION_TIER_ACCESS_APPLICATION
                UNIQUE(application_id)
        );
    END;

    /* ========================================================
       2. Backup existing access data once per migration run
       ======================================================== */

    IF OBJECT_ID(N'dbo.ac_engineer_application_access_mapping_backup', N'U') IS NULL
    BEGIN
        SELECT TOP (0)
            a.*,
            CAST(NULL AS DATETIME2) AS backup_at
        INTO dbo.ac_engineer_application_access_mapping_backup
        FROM dbo.ac_engineer_application_access AS a;
    END;

    INSERT INTO dbo.ac_engineer_application_access_mapping_backup
    SELECT
        a.*,
        SYSDATETIME()
    FROM dbo.ac_engineer_application_access AS a
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ac_engineer_application_access_mapping_backup AS b
        WHERE b.id = a.id
    );

    /* ========================================================
       3. Source tier matrix

       YES values are taken from the supplied screenshots.
       Decommissioned rows are omitted.
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
    (
        source_label,
        target_application_name,
        display_name,
        tier1_access,
        tier2_access,
        tier3_access,
        im_above_access
    )
    VALUES
        (N'Bank Email', N'Bank Email', N'Bank Email', 1,1,1,1),
        (N'HVD Desktop Access', N'HVD Desktop Access', N'HVD Desktop Access', 1,1,1,1),
        (N'BOFA', N'BOFA', N'BOFA', 1,1,1,1),
        (N'AUTHENTICATOR', N'Authenticator', N'AUTHENTICATOR', 1,1,1,1),
        (N'SKYPE', N'Skype', N'SKYPE', 1,1,1,1),
        (N'MATTER MOST', N'MatterMost', N'MATTER MOST', 1,1,1,1),
        (N'ELEVATED ID', N'Elevated ID', N'ELEVATED ID', 1,1,1,1),
        (N'V-CENTER', N'Vsphere', N'V-CENTER', 1,1,1,1),
        (N'EV SITE', N'EV SITE', N'EV SITE', 1,1,1,1),
        (N'UCAT - Moved to (CWM)', N'UCAT', N'UCAT', 1,1,1,1),
        (N'RTI Inventory', N'RTI Inventory', N'RTI Inventory', 1,1,1,1),
        (N'Inventory Dashboard', N'Inventory Dashboard', N'Inventory Dashboard', 1,1,1,1),
        (N'MLFC', N'MLFC', N'MLFC', 1,1,1,1),
        (N'HPNA', N'HPNA', N'HPNA', 1,1,1,1),
        (N'TOOLS SERVER', N'Tool servers', N'TOOLS SERVER', 1,1,1,1),
        (N'CWM', N'CWM', N'CWM', 1,1,1,1),
        (N'NDC.WHITELIS', N'NDC', N'NDC.WHITELIS', 1,1,1,1),
        (N'ECSL_Splunk_cisco_AP', N'ECSL_Splunk_cisco_AP', N'ECSL_Splunk_cisco_AP', 1,1,1,1),
        (N'BPA', N'BPA', N'BPA', 1,1,1,1),
        (N'VENAFI', N'VENAFI', N'VENAFI', 0,0,1,1),
        (N'NETSCOUT/SONUS', N'Netscout', N'NETSCOUT/SONUS', 0,0,1,1),
        (N'IPMF', N'IPMF', N'IPMF', 0,1,1,1),
        (N'Windows or Linux Servers', N'Windows or Linux Servers', N'Windows or Linux Servers', 0,1,1,1),
        (N'CUCM', N'Add and Revoke Access to CUCM/CUC', N'CUCM', 1,1,1,1),
        (N'TACAS', N'TACAS', N'TACAS', 1,1,1,1),
        (N'EPAM - AD Group', N'EPAM - AD Group', N'EPAM - AD Group', 1,1,1,1),
        (N'TTSM REMEDY', N'TTSM REMEDY', N'TTSM REMEDY', 1,1,1,1),
        (N'CMSPR', N'CMSPR', N'CMSPR', 1,1,1,1),
        (N'MEDT - New Whitelisting', N'MEDT - New Whitelisting', N'MEDT - New Whitelisting', 1,1,1,1),
        (N'WebEx Control Hub / Softphone', N'WebEx Control Hub / Softphone', N'WebEx Control Hub / Softphone', 1,1,1,0),
        (N'Horizon - New Confluence', N'Ansible horizon', N'Horizon - New Confluence', 0,0,0,1);

    /* ========================================================
       4. Add missing application master rows.
       Existing canonical applications are reused through the
       target_application_name aliases above.
       ======================================================== */

    INSERT INTO dbo.ac_applications
    (
        name,
        description,
        active
    )
    SELECT
        c.target_application_name,
        N'Application from engineer tier access matrix',
        1
    FROM @Catalog AS c
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ac_applications AS a
        WHERE a.name = c.target_application_name
    );

    /* ========================================================
       5. Upsert the tier matrix.
       ======================================================== */

    MERGE dbo.ac_application_tier_access AS target
    USING
    (
        SELECT
            a.id AS application_id,
            c.display_name,
            c.tier1_access,
            c.tier2_access,
            c.tier3_access,
            c.im_above_access,
            c.source_label
        FROM @Catalog AS c
        INNER JOIN dbo.ac_applications AS a
            ON a.name = c.target_application_name
    ) AS source
    ON target.application_id = source.application_id

    WHEN MATCHED THEN
        UPDATE SET
            target.display_name = source.display_name,
            target.tier1_access = source.tier1_access,
            target.tier2_access = source.tier2_access,
            target.tier3_access = source.tier3_access,
            target.im_above_access = source.im_above_access,
            target.source_label = source.source_label,
            target.active = 1,
            target.updated_at = SYSDATETIME()

    WHEN NOT MATCHED BY TARGET THEN
        INSERT
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
        VALUES
        (
            source.application_id,
            source.display_name,
            source.tier1_access,
            source.tier2_access,
            source.tier3_access,
            source.im_above_access,
            1,
            source.source_label
        );

    /* ========================================================
       6. Make the supplied engineer level list authoritative.

       IM / QM / TL are treated as IM & Above for the tier matrix.
       ======================================================== */

    DECLARE @EngineerLevels TABLE
    (
        alias NVARCHAR(100) NOT NULL,
        level_code NVARCHAR(50) NOT NULL
    );

    INSERT INTO @EngineerLevels(alias, level_code)
    VALUES
        (N'aksharma',N'L2'),
        (N'nibsingh',N'L2'),
        (N'nsharma',N'L2'),
        (N'sagarwal',N'L2'),
        (N'asaxena',N'L2'),
        (N'ptariyal',N'QM'),
        (N'dgarg',N'L1'),
        (N'msavad',N'L1'),
        (N'mpasha',N'L1'),
        (N'rkhanna',N'IM'),
        (N'ttaneja',N'L3'),
        (N'vbhat',N'L3'),
        (N'krohan',N'L3'),
        (N'snambiar',N'IM'),
        (N'nitsingh',N'L2'),
        (N'sahmad',N'L2'),
        (N'jsharma',N'L2'),
        (N'vsehrawat',N'L2'),
        (N'abhatt',N'L2'),
        (N'csharma',N'QM'),
        (N'usachdev',N'L1'),
        (N'karamjeet',N'L1'),
        (N'mkumar',N'L1'),
        (N'asingh',N'IM'),
        (N'ayadav',N'L3'),
        (N'mshaik',N'L3'),
        (N'pkumari',N'L3'),
        (N'bmiller',N'L2'),
        (N'mpearson',N'L2'),
        (N'mwilmers',N'L2'),
        (N'mtikhov',N'L3'),
        (N'dludington',N'TL'),
        (N'jhagenburg',N'IM'),
        (N'rhamlett',N'IM'),
        (N'chaskins',N'IM'),
        (N'hchaudhary',N'L2'),
        (N'lsimte',N'L2'),
        (N'arsharma',N'L2'),
        (N'abhardwaj',N'L2'),
        (N'msingh',N'L1'),
        (N'vdutt',N'L1'),
        (N'hmudgal',N'L1'),
        (N'dkundu',N'L1'),
        (N'spandey',N'QM'),
        (N'kmurugesan',N'L3'),
        (N'iahmad',N'L3'),
        (N'sbhadola',N'IM');

    UPDATE e
        SET e.level = x.level_code
    FROM dbo.ac_engineers AS e
    INNER JOIN @EngineerLevels AS x
        ON LOWER(LTRIM(RTRIM(e.alias))) = LOWER(x.alias);

    /* ========================================================
       7. Reconcile access rows.

       Only applications explicitly present in the tier matrix
       and allowed for the engineer's level remain in the access
       table. Existing eligible rows are preserved.
       ======================================================== */

    DELETE access_row
    FROM dbo.ac_engineer_application_access AS access_row
    LEFT JOIN dbo.ac_application_tier_access AS map
        ON map.application_id = access_row.application_id
       AND map.active = 1
    INNER JOIN dbo.ac_engineers AS e
        ON e.id = access_row.engineer_id
    WHERE
        map.application_id IS NULL
        OR e.active = 0
        OR UPPER(ISNULL(e.role,N'USER')) = N'SUPERVISOR'
        OR
        CASE UPPER(LTRIM(RTRIM(ISNULL(e.level,N''))))
            WHEN N'L1' THEN map.tier1_access
            WHEN N'L2' THEN map.tier2_access
            WHEN N'L3' THEN map.tier3_access
            WHEN N'IM' THEN map.im_above_access
            WHEN N'QM' THEN map.im_above_access
            WHEN N'TL' THEN map.im_above_access
            ELSE 0
        END = 0;

    /* Insert missing eligible application assignments. */
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
        N'Required',
        N'Pending',
        NULL,
        NULL,
        GETDATE(),
        NULL,
        N'Not Required',
        NULL,
        NULL,
        0
    FROM dbo.ac_engineers AS e
    CROSS JOIN dbo.ac_application_tier_access AS m
    WHERE
        e.active = 1
        AND UPPER(ISNULL(e.role,N'USER')) <> N'SUPERVISOR'
        AND m.active = 1
        AND
        CASE UPPER(LTRIM(RTRIM(ISNULL(e.level,N''))))
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
            FROM dbo.ac_engineer_application_access AS x
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
   8. Validation queries
   ============================================================ */

SELECT
    e.name,
    e.alias,
    e.level,
    COUNT(a.id) AS application_count
FROM dbo.ac_engineers AS e
LEFT JOIN dbo.ac_engineer_application_access AS a
    ON a.engineer_id = e.id
WHERE e.active = 1
  AND UPPER(ISNULL(e.role,N'USER')) <> N'SUPERVISOR'
GROUP BY
    e.name,
    e.alias,
    e.level
ORDER BY
    e.name;

SELECT
    m.display_name,
    m.tier1_access,
    m.tier2_access,
    m.tier3_access,
    m.im_above_access,
    COUNT(a.id) AS assigned_rows
FROM dbo.ac_application_tier_access AS m
LEFT JOIN dbo.ac_engineer_application_access AS a
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

/* Engineers whose level was not present in the supplied matrix. */
SELECT
    id,
    name,
    alias,
    level,
    role
FROM dbo.ac_engineers
WHERE active = 1
  AND UPPER(ISNULL(role,N'USER')) <> N'SUPERVISOR'
  AND UPPER(ISNULL(level,N'')) NOT IN (N'L1',N'L2',N'L3',N'IM',N'QM',N'TL')
ORDER BY name;
GO
