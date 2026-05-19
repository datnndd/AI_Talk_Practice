import smtplib
from email.message import EmailMessage
import logging
import socket
from app.core.config import settings

logger = logging.getLogger(__name__)

def _mask_email(value: str | None) -> str | None:
    if not value or "@" not in value:
        return value
    name, domain = value.split("@", 1)
    if len(name) <= 2:
        return f"{name[:1]}***@{domain}"
    return f"{name[:2]}***@{domain}"

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

    logger.info(
        "SMTP config: server=%s port=%s user=%s from=%s to=%s",
        settings.smtp_server,
        settings.smtp_port,
        _mask_email(settings.smtp_user),
        _mask_email(settings.smtp_from_email),
        _mask_email(to_email),
    )

    try:
        addresses = socket.getaddrinfo(settings.smtp_server, settings.smtp_port, type=socket.SOCK_STREAM)
        resolved_ips = sorted({address[4][0] for address in addresses})
        logger.info("SMTP DNS resolved: server=%s ips=%s", settings.smtp_server, resolved_ips)
    except socket.gaierror:
        logger.exception("SMTP DNS lookup failed: server=%s", settings.smtp_server)
        raise

    server = None
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = to_email

        # Depending on port, use starttls or ssl
        if settings.smtp_port in [465]:
            logger.info("SMTP connecting with SSL: server=%s port=%s", settings.smtp_server, settings.smtp_port)
            server = smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port)
        else:
            logger.info("SMTP connecting: server=%s port=%s", settings.smtp_server, settings.smtp_port)
            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
            logger.info("SMTP starting TLS")
            server.starttls()
            
        if settings.smtp_user and settings.smtp_password:
            logger.info("SMTP logging in: user=%s", _mask_email(settings.smtp_user))
            server.login(settings.smtp_user, settings.smtp_password)
            
        logger.info("SMTP sending message: to=%s subject=%s", _mask_email(to_email), subject)
        server.send_message(msg)
        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.exception(f"Failed to send email to {to_email}: {e}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                logger.debug("SMTP quit failed", exc_info=True)

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
