from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    supabase_project_url: str  # Project URL from Supabase dashboard
    supabase_anon_key: str  # Anon/Public key (API key listed as anon public)
    supabase_service_role_key: str  # Service Role key (secret key)
    supabase_jwt_secret: Optional[str] = None  # JWT Signing Key (optional, for custom JWT verification)
    database_url: Optional[str] = None  # Optional direct database connection URL
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

