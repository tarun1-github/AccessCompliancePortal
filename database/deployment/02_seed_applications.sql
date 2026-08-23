USE [CPDB];
GO
SET IDENTITY_INSERT dbo.ac_applications ON;
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=3) INSERT dbo.ac_applications(id,name,description,active) VALUES(3,N'NG2 Splunk',N'NG2 Splunk access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=4) INSERT dbo.ac_applications(id,name,description,active) VALUES(4,N'MatterMost',N'MatterMost collaboration application',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=5) INSERT dbo.ac_applications(id,name,description,active) VALUES(5,N'Add and Revoke Access to CUCM/CUC',N'CUCM and Unity Connection access management',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=6) INSERT dbo.ac_applications(id,name,description,active) VALUES(6,N'Splunk access',N'Splunk access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=7) INSERT dbo.ac_applications(id,name,description,active) VALUES(7,N'Remedy-CRQ Approval for T3s',N'Remedy CRQ approval for T3 engineers',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=8) INSERT dbo.ac_applications(id,name,description,active) VALUES(8,N'CWM',N'CWM access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=9) INSERT dbo.ac_applications(id,name,description,active) VALUES(9,N'Wx Softphone',N'Wx Softphone access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=10) INSERT dbo.ac_applications(id,name,description,active) VALUES(10,N'NDC',N'NDC access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=11) INSERT dbo.ac_applications(id,name,description,active) VALUES(11,N'HPNA',N'HPNA access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=12) INSERT dbo.ac_applications(id,name,description,active) VALUES(12,N'Netscout',N'Netscout access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=13) INSERT dbo.ac_applications(id,name,description,active) VALUES(13,N'Vsphere',N'vSphere access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=14) INSERT dbo.ac_applications(id,name,description,active) VALUES(14,N'Control Hub',N'Control Hub access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=15) INSERT dbo.ac_applications(id,name,description,active) VALUES(15,N'Tool servers',N'Tool server access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=16) INSERT dbo.ac_applications(id,name,description,active) VALUES(16,N'ECSL',N'ECSL access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=17) INSERT dbo.ac_applications(id,name,description,active) VALUES(17,N'Ansible horizon',N'Ansible Horizon access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=18) INSERT dbo.ac_applications(id,name,description,active) VALUES(18,N'UCAT',N'UCAT access',1);
IF NOT EXISTS(SELECT 1 FROM dbo.ac_applications WHERE id=19) INSERT dbo.ac_applications(id,name,description,active) VALUES(19,N'CDR Dashboard',N'CDR Dashboard access',1);
SET IDENTITY_INSERT dbo.ac_applications OFF;
GO
