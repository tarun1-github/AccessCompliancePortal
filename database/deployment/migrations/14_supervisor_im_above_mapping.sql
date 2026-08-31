USE [CPDB];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

/*
    Supervisor application mapping

    Requirement:
      Supervisors must receive the IM & Above application set,
      regardless of the supervisor's stored engineer level.

    Existing verification / ARM values are preserved.
    Missing supervisor application rows are inserted as:
      access_status        = Required
      verification_status  = Pending
      ticket_status        = Not Started

    This migration does not change application master data.
*/

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.ac_application_tier_access', N'U') IS NULL
    BEGIN
        THROW 51001, 'ac_application_tier_access does not exist. Run migration 13 first.', 1;
    END;

    /* ========================================================
       1. Remove supervisor assignments that are not IM & Above.
          This keeps supervisor access aligned with the matrix.
          Application master rows are never deleted.
       ======================================================== */
    DELETE eaa
    FROM dbo.ac_engineer_application_access AS eaa
    INNER JOIN dbo.ac_engineers AS e
        ON e.id = eaa.engineer_id
    LEFT JOIN dbo.ac_application_tier_access AS map
        ON map.application_id = eaa.application_id
       AND map.active = 1
    WHERE
        e.active = 1
        AND UPPER(ISNULL(e.role,'')) = 'SUPERVISOR'
        AND (
            map.application_id IS NULL
            OR map.im_above_access = 0
        );

    /* ========================================================
       2. Add every IM & Above application for every active
          supervisor.
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
    FROM dbo.ac_engineers AS e
    CROSS JOIN dbo.ac_application_tier_access AS map
    WHERE
        e.active = 1
        AND UPPER(ISNULL(e.role,'')) = 'SUPERVISOR'
        AND map.active = 1
        AND map.im_above_access = 1
        AND NOT EXISTS
        (
            SELECT 1
            FROM dbo.ac_engineer_application_access AS existing_row
            WHERE existing_row.engineer_id = e.id
              AND existing_row.application_id = map.application_id
        );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO

/* Validation: supervisor -> IM & Above application count */
SELECT
    e.name,
    e.alias,
    e.level,
    COUNT(a.id) AS application_count
FROM dbo.ac_engineers AS e
LEFT JOIN dbo.ac_engineer_application_access AS a
    ON a.engineer_id = e.id
LEFT JOIN dbo.ac_application_tier_access AS map
    ON map.application_id = a.application_id
   AND map.active = 1
WHERE
    e.active = 1
    AND UPPER(ISNULL(e.role,'')) = 'SUPERVISOR'
    AND map.im_above_access = 1
GROUP BY
    e.name,
    e.alias,
    e.level
ORDER BY
    e.name;
GO
