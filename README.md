# Access Compliance Portal – v2 changes

## Added
- ARM Ticket and Ticket Status on every user/application access record.
- Ticket Status values: `Approval Pending` and `Completed`.
- Completed displays green; all non-completed ticket states display red.
- Shared remarks are validated to a maximum of 200 characters.
- Supervisor dashboard with colorful status chart and pivot-style totals.
- CSV and Excel downloads.
- Database-driven `reminder_days` setting, defaulting to 15 days.
- Email endpoints for one user or all users; each email uses the engineer's alias URL and CCs the configured supervisor email (`rm_email`).

## Important email configuration
The application can construct and send mail from `BOAaccessverification@cisco.com`, but the actual sender must be authorized by the organization's SMTP/Exchange relay. Copy `.env.example` values into the deployment configuration and set valid SMTP settings. The application will not pretend mail was sent if SMTP is missing.

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On startup, the app creates the settings table and adds the new access columns when they do not exist.
