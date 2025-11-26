"""
Email service for sending teacher invitations and other notifications.

This module uses Resend (https://resend.com) for email delivery.
Alternative services you can use:
- SendGrid (https://sendgrid.com) - Popular, reliable, good free tier
- Mailgun (https://www.mailgun.com) - Developer-friendly
- AWS SES (https://aws.amazon.com/ses/) - Cost-effective at scale
- Supabase Edge Functions with email service - If using Supabase infrastructure

Setup instructions for Resend:
1. Sign up at https://resend.com
2. Get your API key from the dashboard
3. Add RESEND_API_KEY to your .env file
4. Verify your domain (or use Resend's test domain for development)
"""
import os
from typing import Optional
from app.config import settings

# Load environment variables from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on pydantic-settings

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    print("Warning: resend package not installed. Email functionality will be disabled.")


class EmailService:
    """Email service for sending notifications"""
    
    def __init__(self):
        # Use settings object as primary source (it loads from .env automatically via pydantic-settings)
        # Fall back to os.getenv() for direct environment variable access
        self.resend_api_key = (
            getattr(settings, "resend_api_key", None) or
            os.getenv("RESEND_API_KEY") or
            os.getenv("resend_api_key")
        )
        self.from_email = (
            getattr(settings, "resend_from_email", None) or
            os.getenv("RESEND_FROM_EMAIL") or
            os.getenv("resend_from_email") or
            "onboarding@resend.dev"
        )
        # Base URL used in email links (teacher app / frontend)
        # Prefer RESEND_FORWARDING_URL / settings.resend_forwarding_url, but fall back to legacy APP_URL if present
        self.forward_url = (
            getattr(settings, "resend_forwarding_url", None)
            or os.getenv("RESEND_FORWARDING_URL")
            or os.getenv("resend_forwarding_url")
            or os.getenv("APP_URL")  # legacy name, kept for backward compatibility
            or os.getenv("app_url")
            or "http://localhost:5173"
        )
        
        # Debug output
        if not RESEND_AVAILABLE:
            print("Warning: resend package not installed. Run: pip install resend")
        elif not self.resend_api_key:
            print("Warning: Email service not configured. Set RESEND_API_KEY in .env to enable emails.")
            print(f"Debug: settings.resend_api_key = {getattr(settings, 'resend_api_key', None)}")
            print(f"Debug: os.getenv('RESEND_API_KEY') = {os.getenv('RESEND_API_KEY')}")
        else:
            # Only print success message if key is set (to avoid cluttering logs)
            if self.resend_api_key:
                print(f"Email service configured. From: {self.from_email}, Forward URL: {self.forward_url}")
        
        if RESEND_AVAILABLE and self.resend_api_key:
            try:
                # New resend SDK (v2.x) uses module-level API key
                resend.api_key = self.resend_api_key
                self.resend = resend  # Store the module reference
            except Exception as e:
                print(f"Error initializing Resend client: {str(e)}")
                self.resend = None
        else:
            self.resend = None
    
    def send_teacher_invitation(
        self,
        teacher_email: str,
        teacher_name: str,
        school_name: str,
        invitation_token: str,
        inviter_name: Optional[str] = None
    ) -> bool:
        """
        Send an invitation email to a teacher
        
        Args:
            teacher_email: Email address of the teacher
            teacher_name: Name of the teacher
            school_name: Name of the school
            invitation_token: Unique token for the invitation
            inviter_name: Name of the person who sent the invitation (optional)
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.resend:
            print(f"Email service not available. Would send invitation to {teacher_email}")
            return False
        
        # Build invitation URL using the configured forwarding URL (e.g. teacher app)
        invitation_url = f"{self.forward_url}/teacher/accept-invitation?token={invitation_token}"
        
        # Email content
        inviter_text = f" by {inviter_name}" if inviter_name else ""
        subject = f"Invitation to join {school_name} on EigoKit"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3B82F6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background-color: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                .button:hover {{ background-color: #2563EB; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>EigoKit Teacher Invitation</h1>
                </div>
                <div class="content">
                    <p>Hello {teacher_name},</p>
                    <p>You have been invited{inviter_text} to join <strong>{school_name}</strong> as a teacher on EigoKit.</p>
                    <p>EigoKit is an English learning platform that helps you manage your students, track their progress, and deliver engaging lessons.</p>
                    <p style="text-align: center;">
                        <a href="{invitation_url}" class="button">Accept Invitation</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #6b7280; font-size: 14px;">{invitation_url}</p>
                    <p>This invitation link will expire in 7 days.</p>
                    <p>If you didn't expect this invitation, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© EigoKit - English Learning Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {teacher_name},
        
        You have been invited{inviter_text} to join {school_name} as a teacher on EigoKit.
        
        EigoKit is an English learning platform that helps you manage your students, track their progress, and deliver engaging lessons.
        
        Accept your invitation by clicking this link:
        {invitation_url}
        
        This invitation link will expire in 7 days.
        
        If you didn't expect this invitation, you can safely ignore this email.
        
        © EigoKit - English Learning Platform
        """
        
        try:
            # New resend SDK (v2.x) API - use Emails class
            emails = self.resend.Emails()
            params = {
                "from": self.from_email,
                "to": [teacher_email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
            }
            
            email = emails.send(params)
            print(f"Teacher invitation email sent to {teacher_email}: {email}")
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to send email to {teacher_email}: {error_msg}")
            # Re-raise to provide more context to the caller
            raise Exception(f"Email send failed: {error_msg}")


# Global email service instance
email_service = EmailService()

