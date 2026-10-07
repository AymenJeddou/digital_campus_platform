from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(recipient_email: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Never raises: a mail failure is logged and
    reported as False so the caller's request still succeeds (the user can
    ask for a resend)."""
    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST not set; email to %s not sent (%s).", recipient_email, subject)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "no-reply@digital-campus.local"
    message["To"] = recipient_email
    message.set_content(body)

    smtp_cls = smtplib.SMTP if settings.SMTP_USE_TLS else smtplib.SMTP_SSL
    try:
        with smtp_cls(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
    except (smtplib.SMTPException, OSError):
        logger.exception("Failed to send email to %s (%s).", recipient_email, subject)
        return False
    return True


def send_verification_email(recipient_email: str, verification_token: str) -> bool:
    link = f"{settings.FRONTEND_URL}/verify?token={quote(verification_token)}"
    return _send(
        recipient_email,
        "Confirme ton adresse — Digital Campus FSB",
        "Bienvenue sur Digital Campus.\n\n"
        f"Pour activer ton compte, ouvre ce lien (valable 30 minutes) :\n{link}\n\n"
        "Si tu n'as pas créé de compte, ignore ce message.",
    )


def send_password_reset_email(recipient_email: str, reset_token: str) -> bool:
    link = f"{settings.FRONTEND_URL}/reset-password?token={quote(reset_token)}"
    return _send(
        recipient_email,
        "Réinitialisation du mot de passe — Digital Campus FSB",
        f"Pour choisir un nouveau mot de passe, ouvre ce lien (valable 30 minutes) :\n{link}\n\n"
        "Si tu n'as rien demandé, ignore ce message : ton mot de passe reste inchangé.",
    )
