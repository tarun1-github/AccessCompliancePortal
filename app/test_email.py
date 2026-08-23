import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# ------------------------------------------------------------
# Load .env
# ------------------------------------------------------------

load_dotenv()

MAIL_FROM = os.getenv("MAIL_FROM")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() == "true"

# For the first test, send to yourself
MAIL_TO = MAIL_FROM

# ------------------------------------------------------------
# Validate configuration
# ------------------------------------------------------------

print("SMTP Configuration")
print("-------------------")
print("MAIL_FROM       :", MAIL_FROM)
print("SMTP_HOST       :", SMTP_HOST)
print("SMTP_PORT       :", SMTP_PORT)
print("SMTP_STARTTLS   :", SMTP_STARTTLS)
print("MAIL_TO         :", MAIL_TO)
print()

if not MAIL_FROM:
    raise ValueError("MAIL_FROM is not configured in .env")

if not SMTP_HOST:
    raise ValueError("SMTP_HOST is not configured in .env")

# ------------------------------------------------------------
# Create email
# ------------------------------------------------------------

msg = EmailMessage()

msg["From"] = MAIL_FROM
msg["To"] = MAIL_TO
msg["Subject"] = "Access Compliance Portal - SMTP Test"

msg.set_content(
    """Hello,

This is a test email from the Access Compliance Portal LAB server.

SMTP connectivity and email configuration test.

Regards,
Access Compliance Portal
"""
)

# ------------------------------------------------------------
# Send email
# ------------------------------------------------------------

try:

    print("Connecting to SMTP server...")

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=30
    ) as smtp:

        print("SMTP TCP connection successful")

        smtp.ehlo()

        if SMTP_STARTTLS:

            print("Starting STARTTLS...")

            smtp.starttls()

            smtp.ehlo()

            print("STARTTLS successful")

        print("Sending email...")

        smtp.send_message(msg)

        print()
        print("========================================")
        print("EMAIL SENT SUCCESSFULLY")
        print("========================================")

except Exception as e:

    print()
    print("========================================")
    print("EMAIL FAILED")
    print("========================================")
    print(type(e).__name__, ":", str(e))