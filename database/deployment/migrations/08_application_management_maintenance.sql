USE [CPDB];
GO

/* =========================================================================
   MIGRATION / MAINTENANCE SCRIPT: 08_application_management_maintenance.sql
   Description:
     Helper operations and stored patterns for Application Governance:
     - Global application provisioning across active engineers
     - Application global deactivation
     - Individual engineer application assignment / removal
     - Audit trail recording for application management actions
   ========================================================================= */

-- 1. Verify schema constraints on verification and request ticket statuses
IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_ac_eaa_ticket_status'
      AND parent_object_id = OBJECT_ID(N'dbo.ac_engineer_application_access')
)
BEGIN
    ALTER TABLE dbo.ac_engineer_application_access
    ADD CONSTRAINT CK_ac_eaa_ticket_status
    CHECK (ticket_status IN ('Not Started', 'In Progress', 'Pending Approval', 'Completed'));
END
GO

-- 2. Helpful Query: List all active applications and total engineers assigned
/*
SELECT 
    a.id AS application_id,
    a.name AS application_name,
    a.description,
    a.active,
    COUNT(eaa.engineer_id) AS assigned_engineers_count
FROM dbo.ac_applications a
LEFT JOIN dbo.ac_engineer_application_access eaa ON eaa.application_id = a.id
GROUP BY a.id, a.name, a.description, a.active
ORDER BY a.name;
*/
GO

-- 3. Procedure Pattern: Assign an application to all active non-supervisor engineers
-- (Used by the portal backend upon application registration)
/*
DECLARE @NewAppName NVARCHAR(200) = N'Citrix';
DECLARE @NewAppDescription NVARCHAR(500) = N'Remote Citrix Virtual Access';
DECLARE @DefaultAccessStatus NVARCHAR(50) = N'Required';
DECLARE @SupervisorAlias NVARCHAR(100) = N'ttaneja';

DECLARE @AppId INT;

-- Insert or activate application
IF EXISTS (SELECT 1 FROM dbo.ac_applications WHERE LOWER(name) = LOWER(@NewAppName))
BEGIN
    UPDATE dbo.ac_applications
    SET active = 1, description = ISNULL(@NewAppDescription, description)
    WHERE LOWER(name) = LOWER(@NewAppName);

    SELECT @AppId = id FROM dbo.ac_applications WHERE LOWER(name) = LOWER(@NewAppName);
END
ELSE
BEGIN
    INSERT INTO dbo.ac_applications (name, description, active)
    VALUES (@NewAppName, @NewAppDescription, 1);

    SET @AppId = SCOPE_IDENTITY();
END

-- Assign to all active engineers who do not currently have this application assigned
INSERT INTO dbo.ac_engineer_application_access (engineer_id, application_id, access_status, verification_status, ticket_status)
SELECT e.id, @AppId, @DefaultAccessStatus, N'Pending', N'Not Started'
FROM dbo.ac_engineers e
WHERE e.active = 1 
  AND ISNULL(UPPER(e.role), N'USER') <> N'SUPERVISOR'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.ac_engineer_application_access x
      WHERE x.engineer_id = e.id AND x.application_id = @AppId
  );

-- Log in audit table
INSERT INTO dbo.ac_audit_log (application_id, action, new_status, remarks, performed_by, created_at)
VALUES (@AppId, N'APPLICATION_CREATED_FOR_ALL_ENGINEERS', @NewAppName, N'Assigned via database migration script', @SupervisorAlias, GETUTCDATE());
*/
GO

-- 4. Procedure Pattern: Remove/Deactivate an application for all engineers
/*
DECLARE @DeactivateAppName NVARCHAR(200) = N'Citrix';
DECLARE @DeactivateSupervisor NVARCHAR(100) = N'ttaneja';
DECLARE @DeactivateAppId INT;

SELECT @DeactivateAppId = id FROM dbo.ac_applications WHERE LOWER(name) = LOWER(@DeactivateAppName);

IF @DeactivateAppId IS NOT NULL
BEGIN
    UPDATE dbo.ac_applications SET active = 0 WHERE id = @DeactivateAppId;

    INSERT INTO dbo.ac_audit_log (application_id, action, old_status, remarks, performed_by, created_at)
    VALUES (@DeactivateAppId, N'APPLICATION_REMOVED_FOR_ALL_ENGINEERS', @DeactivateAppName, N'Deactivated application via SQL', @DeactivateSupervisor, GETUTCDATE());
END
*/
GO

-- 5. Procedure Pattern: Remove an application from a specific engineer only
/*
DECLARE @TargetEngineerAlias NVARCHAR(100) = N'vbhat';
DECLARE @RemoveAppName NVARCHAR(200) = N'Splunk access';
DECLARE @ActingSupervisor NVARCHAR(100) = N'ttaneja';

DECLARE @TargetEngId INT;
DECLARE @TargetAppId INT;

SELECT @TargetEngId = id FROM dbo.ac_engineers WHERE alias = @TargetEngineerAlias;
SELECT @TargetAppId = id FROM dbo.ac_applications WHERE LOWER(name) = LOWER(@RemoveAppName);

IF @TargetEngId IS NOT NULL AND @TargetAppId IS NOT NULL
BEGIN
    DELETE FROM dbo.ac_engineer_application_access
    WHERE engineer_id = @TargetEngId AND application_id = @TargetAppId;

    INSERT INTO dbo.ac_audit_log (engineer_id, application_id, action, remarks, performed_by, created_at)
    VALUES (@TargetEngId, @TargetAppId, N'APPLICATION_REMOVED_FROM_ENGINEER', N'Removed for single engineer via SQL', @ActingSupervisor, GETUTCDATE());
END
*/
GO
