USE [CPDB];
GO
SET IDENTITY_INSERT dbo.ac_portal_settings ON;
IF NOT EXISTS(SELECT 1 FROM dbo.ac_portal_settings WHERE id=1) INSERT dbo.ac_portal_settings(id,setting_key,setting_value,description,updated_at,updated_by) VALUES(1,N'reminder_days',N'20',N'Number of days between access verification reminder emails',N'2026-08-22 00:42:57.5870525',N'supervisor_alias');
SET IDENTITY_INSERT dbo.ac_portal_settings OFF;
GO
