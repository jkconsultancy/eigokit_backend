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
                print(f"Email service configured. From: {self.from_email}")
        
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
    
    def _get_frontend_url_for_role(self, role: str, inviter_role: Optional[str] = None) -> Optional[str]:
        """
        Get the frontend base URL for a given role based on invitation routing rules.
        
        Routing rules:
        - Teachers: Always use FRONTEND_TEACHERS_URL (regardless of who invites them)
        - School Admins: Use FRONTEND_SCHOOLS_URL
          - When invited by Platform Admin: Use FRONTEND_SCHOOLS_URL
          - When invited by School Admin (team member): Use FRONTEND_SCHOOLS_URL
        - Platform Admins: Use FRONTEND_ADMINS_URL
          - When invited by Platform Admin (team member): Use FRONTEND_ADMINS_URL
        
        Args:
            role: The role being invited ('teacher', 'school_admin', 'platform_admin')
            inviter_role: The role of the person sending the invitation (optional, for future use)
        
        Returns:
            The frontend base URL for the role, or None if not configured
        """
        if role == "teacher":
            # Teachers always go to teacher frontend, regardless of who invites them
            return (
                getattr(settings, "frontend_teachers_url", None)
                or os.getenv("FRONTEND_TEACHERS_URL")
                or os.getenv("frontend_teachers_url")
            )
        elif role == "school_admin":
            # School admins always go to school admin frontend
            return (
                getattr(settings, "frontend_schools_url", None)
                or os.getenv("FRONTEND_SCHOOLS_URL")
                or os.getenv("frontend_schools_url")
            )
        elif role == "platform_admin":
            # Platform admins always go to platform admin frontend
            return (
                getattr(settings, "frontend_admins_url", None)
                or os.getenv("FRONTEND_ADMINS_URL")
                or os.getenv("frontend_admins_url")
            )
        return None
    
    def send_teacher_invitation(
        self,
        teacher_email: str,
        teacher_name: str,
        school_name: str,
        invitation_token: str,
        inviter_name: Optional[str] = None
    ) -> bool:
        """
        Send an invitation email to a teacher.
        Teachers are always invited to the teacher frontend (FRONTEND_TEACHERS_URL).
        
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
        
        # Teachers are always invited to the teacher frontend
        frontend_url = self._get_frontend_url_for_role("teacher")
        if not frontend_url:
            print(f"Warning: FRONTEND_TEACHERS_URL not configured. Cannot send invitation to {teacher_email}")
            return False
        
        # Build invitation URL using the teacher frontend URL
        base_url = frontend_url.rstrip('/')
        invitation_url = f"{base_url}/teacher/accept-invitation?token={invitation_token}"
        
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

