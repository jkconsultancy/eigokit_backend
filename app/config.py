from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    supabase_project_url: str  # Project URL from Supabase dashboard
    supabase_anon_key: str  # Anon/Public key (API key listed as anon public)
    supabase_service_role_key: str  # Service Role key (secret key)
    supabase_jwt_secret: Optional[str] = None  # JWT Signing Key (optional, for custom JWT verification)
    database_url: Optional[str] = None  # Optional direct database connection URL
    environment: str = "development"
    
    # Email service configuration (Resend)
    resend_api_key: Optional[str] = None  # Resend API key for sending emails
    resend_from_email: Optional[str] = None  # From email address (must be verified in Resend)
    # Base URL of the frontend app used in email links (e.g. teacher app)
    # Populated from RESEND_FORWARDING_URL (preferred) or APP_URL (legacy)
    resend_forwarding_url: Optional[str] = None

    # Password reset redirect URLs per app (used for Supabase password reset links)
    password_reset_redirect_url_platform_admin: Optional[str] = None
    password_reset_redirect_url_school_admin: Optional[str] = None
    password_reset_redirect_url_teacher: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

