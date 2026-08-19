"""Email notification service.

When SMTP_HOST is not configured, emails are logged to stdout so the app
can be demoed locally without real SMTP credentials.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email.

    Falls back to a stdout log entry if SMTP_HOST is not set — never raises.
    """
    if not settings.SMTP_HOST:
        _log_to_stdout(to, subject, body)
        return

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to

        port = settings.SMTP_PORT or 587
        with smtplib.SMTP(settings.SMTP_HOST, port) as smtp:
            if settings.SMTP_USER:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
            logger.info("Email sent to %s: %s", to, subject)

    except Exception as exc:  # noqa: BLE001
        # Log but never crash the request — notification failure is non-fatal.
        logger.error("Failed to send email to %s: %s", to, exc)
        _log_to_stdout(to, subject, body)


def _log_to_stdout(to: str, subject: str, body: str) -> None:
    print(
        f"\n{'='*60}\n"
        f"[EMAIL] To: {to}\n"
        f"[EMAIL] Subject: {subject}\n"
        f"[EMAIL] Body:\n{body}\n"
        f"{'='*60}\n"
    )
