from typing import Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from pathlib import Path

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

async def send_reset_password_email(email_to: str, token: str):
    """
    Send reset password email with token
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email_to],
        body=f"""
        Hello,
        
        You have requested to reset your password. Please click the link below to reset it:
        
        {reset_url}
        
        If you did not request this, please ignore this email.
        
        Best regards,
        Your App Team
        """,
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message) 