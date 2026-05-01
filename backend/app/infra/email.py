import smtplib
from email.message import EmailMessage
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body: str) -> None:
    """Send an email using SMTP or log it if SMTP is not configured."""
    if not settings.smtp_server:
        logger.warning("SMTP not configured. Mocking email send.")
        logger.info(f"--- MOCK EMAIL ---")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body}")
        logger.info(f"------------------")
        return

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = to_email

        # Depending on port, use starttls or ssl
        if settings.smtp_port in [465]:
            server = smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port)
        else:
            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
            server.starttls()
            
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
            
        server.send_message(msg)
        server.quit()
        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")

async def send_verification_email(to_email: str, token: str) -> None:
    subject = "Verify your AI Talk Practice Account"
    link = f"{settings.frontend_url.rstrip('/')}/auth/verify?token={token}"
    body = f"Please verify your email by clicking the link: {link}"
    await send_email(to_email, subject, body)

async def send_password_reset_email(to_email: str, token: str) -> None:
    subject = "Reset your AI Talk Practice Password"
    body = f"Your password reset code is: {token}\nThis code expires in 10 minutes. If you did not request this, ignore this email."
    await send_email(to_email, subject, body)


async def send_register_otp_email(to_email: str, otp: str) -> None:
    subject = "Verify your AI Talk Practice email"
    body = f"Your registration code is: {otp}\nThis code expires in 10 minutes."
    await send_email(to_email, subject, body)
