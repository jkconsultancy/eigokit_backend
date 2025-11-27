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

    # Frontend base URLs for each app (used to construct password reset redirect URLs)
    frontend_admins_url: Optional[str] = None  # Platform admin frontend base URL
    frontend_schools_url: Optional[str] = None  # School admin frontend base URL
    frontend_teachers_url: Optional[str] = None  # Teacher frontend base URL

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env (like deprecated RESEND_FORWARDING_URL)


settings = Settings()

