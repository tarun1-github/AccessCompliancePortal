USE [CPDB];
GO

/* Remove the old constraint before converting its legacy status values. */
IF EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_ac_eaa_ticket_status'
      AND parent_object_id = OBJECT_ID(N'dbo.ac_engineer_application_access')
)
    ALTER TABLE dbo.ac_engineer_application_access
    DROP CONSTRAINT CK_ac_eaa_ticket_status;
GO

/* Convert legacy ARM statuses to the supervisor request-status workflow. */
UPDATE dbo.ac_engineer_application_access
SET ticket_status = CASE ticket_status
    WHEN 'Request Not Initiated' THEN 'Not Started'
    WHEN 'Not Required' THEN 'Not Started'
    WHEN 'Approval Pending' THEN 'Pending Approval'
    WHEN 'Pending' THEN 'Pending Approval'
    ELSE ticket_status
END;
GO

ALTER TABLE dbo.ac_engineer_application_access
ADD CONSTRAINT CK_ac_eaa_ticket_status
CHECK (ticket_status IN ('Not Started', 'In Progress', 'Pending Approval', 'Completed'));
GO

DECLARE @default_constraint sysname;
SELECT @default_constraint = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c
    ON c.object_id = dc.parent_object_id
   AND c.column_id = dc.parent_column_id
WHERE dc.parent_object_id = OBJECT_ID(N'dbo.ac_engineer_application_access')
  AND c.name = N'ticket_status';

IF @default_constraint IS NOT NULL
    EXEC(N'ALTER TABLE dbo.ac_engineer_application_access DROP CONSTRAINT [' + @default_constraint + N']');
GO

ALTER TABLE dbo.ac_engineer_application_access
ADD CONSTRAINT DF_ac_eaa_ticket_status
DEFAULT ('Not Started') FOR ticket_status;
GO
