import os, smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from fastapi import HTTPException

DEFAULT_FROM = "evaccessverification@cisco.com"

def base_url():
    return os.getenv("PORTAL_BASE_URL", "https://evaccesscheck.cisco.com").rstrip("/")

def verification_url(engineer):
    return f"{base_url()}/{engineer.alias}"

def build_message(engineer, days):
    url = verification_url(engineer)
    subject = f"Action Required: Complete Application Access Verification within {days} days"
    html = f'''<!doctype html><html><body style="margin:0;background:#eef2ff;font-family:Arial,sans-serif;padding:28px">
    <div style="max-width:680px;margin:auto;background:#fff;border-radius:22px;overflow:hidden;box-shadow:0 16px 35px rgba(31,41,55,.2)">
      <div style="padding:28px;background:linear-gradient(135deg,#2563eb,#7c3aed,#ec4899);color:#fff"><h1 style="margin:0">🛡️ Access Verification</h1><p>Please help us keep application access accurate and compliant.</p></div>
      <div style="padding:32px;color:#172033"><p>Hello <b>{engineer.name}</b>,</p><p>Please test every application assigned to you and confirm whether your access is working. This verification should be completed within <b>{days} days</b>.</p>
      <p style="text-align:center;margin:32px 0"><a href="{url}" style="display:inline-block;padding:17px 34px;border-radius:14px;background:linear-gradient(135deg,#22c55e,#06b6d4,#2563eb);color:#fff;text-decoration:none;font-weight:bold;font-size:17px;box-shadow:0 7px 0 #0f766e,0 14px 24px rgba(37,99,235,.35)">🔐 VERIFY ACCESS NOW</a></p>
      <p style="font-size:13px;color:#64748b">Your personal verification page: {url}</p></div></div></body></html>'''
    return subject, html

def send_verification(engineer, days, cc=None):
    if not engineer.email:
        return False, "Engineer has no email address"
    subject, html = build_message(engineer, days)
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        return False, "SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME and SMTP_PASSWORD."
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv("MAIL_FROM", DEFAULT_FROM)
    msg["To"] = engineer.email
    if cc: msg["Cc"] = cc
    msg.set_content(f"Please verify your access: {verification_url(engineer)}")
    msg.add_alternative(html, subtype="html")
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(smtp_host, port, timeout=30) as s:
        if os.getenv("SMTP_STARTTLS", "true").lower() == "true": s.starttls()
        if os.getenv("SMTP_USERNAME"): s.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD", ""))
        s.send_message(msg)
    return True, f"Sent to {engineer.email}" 
