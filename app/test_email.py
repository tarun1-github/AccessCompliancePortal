import os
import smtplib
from pathlib import Path
from email.message import EmailMessage

from dotenv import load_dotenv


# ============================================================
# LOAD PROJECT .ENV
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(
    PROJECT_ROOT / ".env",
    override=True
)


# ============================================================
# SMTP CONFIGURATION
# ============================================================

MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_TO = os.getenv("MAIL_TO") or MAIL_FROM

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

SMTP_STARTTLS = (
    os.getenv("SMTP_STARTTLS", "true").lower() == "true"
)


# ============================================================
# DISPLAY CONFIGURATION
# ============================================================

print()
print("SMTP Configuration")
print("-------------------")
print("MAIL_FROM       :", MAIL_FROM)
print("MAIL_TO         :", MAIL_TO)
print("SMTP_HOST       :", SMTP_HOST)
print("SMTP_PORT       :", SMTP_PORT)
print("SMTP_STARTTLS   :", SMTP_STARTTLS)
print("SMTP_USERNAME   :", SMTP_USERNAME)
print(
    "SMTP_PASSWORD   :",
    "Configured" if SMTP_PASSWORD else "NOT CONFIGURED"
)
print()


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not MAIL_FROM:
    raise ValueError(
        "MAIL_FROM is not configured in .env"
    )

if not MAIL_TO:
    raise ValueError(
        "MAIL_TO is not configured in .env"
    )

if not SMTP_HOST:
    raise ValueError(
        "SMTP_HOST is not configured in .env"
    )

if not SMTP_USERNAME:
    raise ValueError(
        "SMTP_USERNAME is not configured in .env"
    )

if not SMTP_PASSWORD:
    raise ValueError(
        "SMTP_PASSWORD is not configured in .env"
    )


# ============================================================
# CREATE EMAIL
# ============================================================

msg = EmailMessage()

msg["From"] = MAIL_FROM
msg["To"] = MAIL_TO
msg["Subject"] = "Access Compliance Portal - SMTP Test"

msg.set_content(
    """Hello,

This is a test email from the Access Compliance Portal.

SMTP connectivity and authentication test.

Regards,
Access Compliance Portal
"""
)


# ============================================================
# SEND EMAIL
# ============================================================

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

        # ----------------------------------------------------
        # SMTP AUTHENTICATION
        # ----------------------------------------------------

        print("Authenticating SMTP account...")

        smtp.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        print("SMTP authentication successful")

        # ----------------------------------------------------
        # SEND
        # ----------------------------------------------------

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

    print(
        type(e).__name__,
        ":",
        str(e)
    )