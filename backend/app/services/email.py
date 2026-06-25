from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_verification_email(recipient_email: str, verification_token: str) -> bool:
    if not settings.SMTP_HOST:
        return False

    message = EmailMessage()
    message["Subject"] = "Verify your Digital Campus account"
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "no-reply@digital-campus.local"
    message["To"] = recipient_email
    message.set_content(
        "Use this verification token to activate your account:\n\n"
        f"{verification_token}\n\n"
        "POST it to /auth/verify to complete registration."
    )

    if settings.SMTP_USE_TLS:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
    else:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)

    return True