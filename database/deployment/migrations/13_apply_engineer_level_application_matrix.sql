USE [CPDB];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

/* ============================================================
   Engineer Level -> Application Matrix

   Source: supplied Access Requirements matrix screenshots.

   Active matrix rows: 31 unique applications.
   Decommissioned rows intentionally excluded:
       Intrado
       CONFLUENCE

   Tier rules:
       L1  -> Tier 1
       L2  -> Tier 2
       L3  -> Tier 3
       IM  -> IM & Above
       QM  -> IM & Above
       TL  -> IM & Above

   Existing verification / ARM values are preserved for rows that
   remain eligible. New rows are created as Pending / Not Started.

   This script only changes engineer/application assignments and
   the application master names needed to align the portal with the
   supplied matrix. It does NOT remove application master records
   that are no longer assigned.
   ============================================================ */

BEGIN TRY
    BEGIN TRANSACTION;

    /* ========================================================
       1. Mapping table
       ======================================================== */
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

    /* ========================================================
       2. Matrix source
       ======================================================== */
    DECLARE @Matrix TABLE
    (
        matrix_name VARCHAR(200) NOT NULL,
        tier1 BIT NOT NULL,
        tier2 BIT NOT NULL,
        tier3 BIT NOT NULL,
        im_above BIT NOT NULL
    );

    INSERT INTO @Matrix(matrix_name,tier1,tier2,tier3,im_above)
    VALUES
        ('Bank Email',1,1,1,1),
        ('HVD Desktop Access',1,1,1,1),
        ('BOFA',1,1,1,1),
        ('AUTHENTICATOR',1,1,1,1),
        ('SKYPE',1,1,1,1),
        ('MATTER MOST',1,1,1,1),
        ('ELEVATED ID',1,1,1,1),
        ('V-CENTER',1,1,1,1),
        ('EV SITE SEARCH',1,1,1,1),
        ('UCAT - Moved to (CWM)',1,1,1,1),
        ('RTC Inventory',1,1,1,1),
        ('Inventory Dashboard',1,1,1,1),
        ('MLFC',1,1,1,1),
        ('HPNA',1,1,1,1),
        ('TOOLS SERVER',1,1,1,1),
        ('CWM',1,1,1,1),
        ('NDC.WHITELIS',1,1,1,1),
        ('ECSL_Splunk_cisco_AP',1,1,1,1),
        ('BPA',1,1,1,1),
        ('VENAFI',0,0,1,0),
        ('NETSCOUT/SONUS',1,1,1,1),
        ('IPMF',0,1,1,1),
        ('Windows or Linux Servers, ciscopub,pbciscop',1,1,1,1),
        ('CUCM',1,1,1,1),
        ('TACAS',1,1,1,1),
        ('EPAM - AD Group',1,1,1,1),
        ('TTSM REMEDY',1,1,1,1),
        ('CMSPR',1,1,1,1),
        ('MEDT - New Whitelisting',1,1,1,1),
        ('WebEx Control Hub/Softphone',1,1,1,0),
        ('Horizon - New Confluence',0,0,0,1);

    /* ========================================================
       3. Normalize known existing application names.

       These are naming-only changes. Existing application IDs and
       engineer/application references are retained.
       ======================================================== */
    UPDATE a
       SET a.name = v.matrix_name
    FROM dbo.ac_applications a
    INNER JOIN
    (
        VALUES
            ('MatterMost','MATTER MOST'),
            ('Vsphere','V-CENTER'),
            ('Tool servers','TOOLS SERVER'),
            ('Netscout','NETSCOUT/SONUS'),
            ('UCAT','UCAT - Moved to (CWM)'),
            ('Add and Revoke Access to CUCM/CUC','CUCM'),
            ('WebEx Control Hub / Softphone','WebEx Control Hub/Softphone'),
            ('Ansible horizon','Horizon - New Confluence'),
            ('Windows or Linux Servers','Windows or Linux Servers, ciscopub,pbciscop')
    ) v(old_name,matrix_name)
      ON a.name = v.old_name
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ac_applications x
        WHERE x.name = v.matrix_name
          AND x.id <> a.id
    );

    /* ========================================================
       4. Add all matrix applications that do not yet exist.
       ======================================================== */
    INSERT INTO dbo.ac_applications(name,description,active)
    SELECT
        m.matrix_name,
        'Application from Access Requirements tier matrix',
        1
    FROM @Matrix m
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ac_applications a
        WHERE a.name = m.matrix_name
    );

    /* ========================================================
       5. Upsert matrix mapping.
       ======================================================== */
    UPDATE x
       SET x.display_name = m.matrix_name,
           x.tier1_access = m.tier1,
           x.tier2_access = m.tier2,
           x.tier3_access = m.tier3,
           x.im_above_access = m.im_above,
           x.source_label = m.matrix_name,
           x.active = 1,
           x.updated_at = SYSDATETIME()
    FROM dbo.ac_application_tier_access x
    INNER JOIN dbo.ac_applications a
        ON a.id = x.application_id
    INNER JOIN @Matrix m
        ON m.matrix_name = a.name;

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
        m.matrix_name,
        m.tier1,
        m.tier2,
        m.tier3,
        m.im_above,
        1,
        m.matrix_name
    FROM dbo.ac_applications a
    INNER JOIN @Matrix m
        ON m.matrix_name = a.name
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ac_application_tier_access x
        WHERE x.application_id = a.id
    );

    /* ========================================================
       6. Deactivate any mapping that is not part of the current
          matrix. It remains in the DB for history, but cannot be
          assigned by this matrix.
       ======================================================== */
    UPDATE x
       SET x.active = 0,
           x.updated_at = SYSDATETIME()
    FROM dbo.ac_application_tier_access x
    INNER JOIN dbo.ac_applications a
        ON a.id = x.application_id
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM @Matrix m
        WHERE m.matrix_name = a.name
    );

    /* ========================================================
       7. Remove existing engineer assignments that are not
          allowed by the matrix.

          This removes only the assignment row. Application master
          records are preserved. Eligible rows retain their current
          verification / ARM history.
       ======================================================== */
    DELETE eaa
    FROM dbo.ac_engineer_application_access eaa
    INNER JOIN dbo.ac_engineers e
        ON e.id = eaa.engineer_id
    LEFT JOIN dbo.ac_application_tier_access map
        ON map.application_id = eaa.application_id
       AND map.active = 1
    WHERE
        e.active = 0
        OR UPPER(ISNULL(e.role,'')) = 'SUPERVISOR'
        OR map.application_id IS NULL
        OR
        CASE UPPER(LTRIM(RTRIM(ISNULL(e.level,''))))
            WHEN 'L1' THEN map.tier1_access
            WHEN 'L2' THEN map.tier2_access
            WHEN 'L3' THEN map.tier3_access
            WHEN 'IM' THEN map.im_above_access
            WHEN 'QM' THEN map.im_above_access
            WHEN 'TL' THEN map.im_above_access
            ELSE 0
        END = 0;

    /* ========================================================
       8. Add missing eligible engineer assignments.
       ======================================================== */
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
        map.application_id,
        'Required',
        'Pending',
        NULL,
        NULL,
        SYSDATETIME(),
        NULL,
        'Not Started',
        NULL,
        NULL,
        0
    FROM dbo.ac_engineers e
    CROSS JOIN dbo.ac_application_tier_access map
    WHERE
        e.active = 1
        AND UPPER(ISNULL(e.role,'')) <> 'SUPERVISOR'
        AND map.active = 1
        AND
        CASE UPPER(LTRIM(RTRIM(ISNULL(e.level,''))))
            WHEN 'L1' THEN map.tier1_access
            WHEN 'L2' THEN map.tier2_access
            WHEN 'L3' THEN map.tier3_access
            WHEN 'IM' THEN map.im_above_access
            WHEN 'QM' THEN map.im_above_access
            WHEN 'TL' THEN map.im_above_access
            ELSE 0
        END = 1
        AND NOT EXISTS
        (
            SELECT 1
            FROM dbo.ac_engineer_application_access x
            WHERE x.engineer_id = e.id
              AND x.application_id = map.application_id
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
   VALIDATION 1: engineer -> level -> count
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
  AND UPPER(ISNULL(e.role,'')) <> 'SUPERVISOR'
GROUP BY e.name,e.alias,e.level
ORDER BY e.name;

/* ============================================================
   VALIDATION 2: exact assignments for sample engineers
   ============================================================ */
SELECT
    e.name,
    e.alias,
    e.level,
    a.name AS application_name
FROM dbo.ac_engineers e
INNER JOIN dbo.ac_engineer_application_access x
    ON x.engineer_id = e.id
INNER JOIN dbo.ac_applications a
    ON a.id = x.application_id
WHERE e.alias IN ('dgarg','mkumar','ttaneja','vbhat')
ORDER BY e.alias,a.name;
GO
