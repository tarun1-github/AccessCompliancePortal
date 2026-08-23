# CPDB Database Deployment

Generated from the supplied CPDB LAB metadata snapshot.

## Included tables
- dbo.ac_applications
- dbo.ac_audit_log
- dbo.ac_engineer_application_access
- dbo.ac_engineers
- dbo.ac_notification_log
- dbo.ac_portal_settings

## Excluded tables
- dbo.Employee
- dbo.GatewayStatus
- dbo.HR
- dbo.Phones
- dbo.SalesOrder

## Deployment order
1. 01_schema.sql
2. 02_seed_applications.sql
3. 03_seed_engineers.sql
4. 04_seed_access.sql
5. 05_seed_settings.sql

The audit log is created but not seeded because the supplied report contains only a 20-row audit sample.
The notification log is created but not seeded because the supplied report contains zero notification rows.

## Security
LAB verification_token values are intentionally not copied into the deployment package.
The source report shows this column is nullable.

## Metadata limitation
The supplied report contains index names but not the indexed column lists for the non-unique IX_* indexes.
Those indexes are therefore not recreated until exact index-column metadata is exported.
