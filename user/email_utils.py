from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_verification_code(email, code):
    """
    Send a verification code to the user's email.
    
    Args:
        email (str): Recipient email address
        code (str): 6-digit verification code
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "Your Login Verification Code"
    message = f"""
Hello,

Your verification code is: {code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
AirplaneDJ Team
    """.strip()
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #0b57d0;">Login Verification Code</h2>
            <p>Hello,</p>
            <p>Your verification code is:</p>
            <div style="background: #f6f8fa; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #0b57d0;">{code}</span>
            </div>
            <p style="color: #666; font-size: 14px;">This code will expire in 10 minutes.</p>
            <p style="color: #666; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px;">Best regards,<br>AirplaneDJ Team</p>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Verification code sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification code to {email}: {str(e)}")
        return False
