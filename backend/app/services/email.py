from email.message import EmailMessage
import smtplib
from app.core.config import settings

def send_email(to_email: str, subject: str, html: str) -> bool:
    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password or not settings.smtp_from_email:
        if settings.environment == "development":
            print(f"[DEV EMAIL] To={to_email} Subject={subject}\n{html}")
            return False
        raise RuntimeError("SMTP email settings are not configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email
    msg.set_content("Please use an HTML-capable email client to view this message.")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)
    return True
