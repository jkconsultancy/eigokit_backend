"""
Pytest configuration and fixtures for EigoKit backend tests.

This file mocks Supabase and other dependencies before any test modules are imported,
preventing import errors when running tests without all production dependencies installed.
"""
import sys
import types
from unittest.mock import MagicMock

# Mock pydantic_settings module before any imports that depend on it
# This must happen before app.config is imported
# Create a proper mock class that can be used as a base class
class MockBaseSettings:
    """Mock BaseSettings class that can be subclassed."""
    def __init__(self, **kwargs):
        # Store any kwargs as attributes to mimic pydantic behavior
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Create a proper module object for pydantic_settings (not a MagicMock)
# This ensures Python's import system recognizes it as a valid module
mock_pydantic_settings = types.ModuleType('pydantic_settings')
mock_pydantic_settings.BaseSettings = MockBaseSettings
sys.modules['pydantic_settings'] = mock_pydantic_settings

# Mock supabase module before any imports that depend on it
# This must happen before app.database is imported
mock_supabase_module = MagicMock()
mock_client_instance = MagicMock()

# Create a mock create_client function
def mock_create_client(url, key):
    return mock_client_instance

mock_supabase_module.create_client = mock_create_client
mock_supabase_module.Client = MagicMock

# Inject the mock into sys.modules before any app modules are imported
# This prevents the actual supabase module from being imported
sys.modules['supabase'] = mock_supabase_module

# Mock app.config.settings to avoid needing real environment variables
# We need to do this before app.config is imported
# Create mock_settings first
mock_settings = MagicMock()
mock_settings.supabase_project_url = "https://mock.supabase.co"
mock_settings.supabase_anon_key = "mock_anon_key"
mock_settings.supabase_service_role_key = "mock_service_key"
mock_settings.supabase_jwt_secret = None
mock_settings.database_url = None
mock_settings.environment = "test"
mock_settings.resend_api_key = None
mock_settings.resend_from_email = None
mock_settings.frontend_admins_url = None
mock_settings.frontend_schools_url = None
mock_settings.frontend_teachers_url = None

# Create a mock Settings class that returns our mock_settings when instantiated
class MockSettings(MockBaseSettings):
    """Mock Settings class that returns mock_settings singleton when instantiated."""
    _instance = None
    
    def __new__(cls, **kwargs):
        # Return the same mock_settings instance every time Settings() is called
        if MockSettings._instance is None:
            MockSettings._instance = mock_settings
        return MockSettings._instance
    
    def __init__(self, **kwargs):
        # Already initialized as mock_settings, no need to do anything
        pass

# Create a mock config module that will be used when app.config is imported
mock_config_module = types.ModuleType('app.config')
mock_config_module.Settings = MockSettings
# When app.config does `settings = Settings()`, it will get our mock_settings
mock_config_module.settings = mock_settings
sys.modules['app.config'] = mock_config_module

# Create mock clients that will replace the real ones
mock_supabase_client = MagicMock()
mock_supabase_admin_client = MagicMock()

import pytest
from fastapi.testclient import TestClient

# Explicitly check for pytest-mock plugin
# The 'mocker' fixture is required by tests, so we need to ensure it's available
try:
    import pytest_mock
    pytest_mock_available = True
except ImportError:
    pytest_mock_available = False
    # Provide a helpful error message if pytest-mock is missing
    import sys
    import os
    
    # Check if we're in a venv
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    venv_hint = ""
    if not in_venv:
        venv_hint = (
            "\n\n⚠️  WARNING: You don't appear to be in a virtual environment.\n"
            "   Activate the venv first: source .venv/bin/activate\n"
        )
    
    error_msg = (
        f"\n{'='*70}\n"
        f"ERROR: pytest-mock is not installed or not available.\n"
        f"{'='*70}\n"
        f"The 'mocker' fixture is required by tests but pytest-mock is missing.\n\n"
        f"To fix this:\n"
        f"  1. Activate the virtual environment:\n"
        f"     cd eigokit_backend\n"
        f"     source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate\n"
        f"  2. Install dependencies:\n"
        f"     pip install -r requirements.txt\n"
        f"  3. Verify installation:\n"
        f"     pip list | grep pytest-mock\n"
        f"  4. Run tests:\n"
        f"     python -m pytest tests/ -v\n"
        f"{venv_hint}"
        f"{'='*70}\n"
    )
    
    # Only show error if pytest is actually running (not just importing)
    if 'pytest' in sys.modules:
        print(error_msg, file=sys.stderr)
        sys.exit(1)

@pytest.fixture(scope="session", autouse=True)
def setup_database_mocks():
    """Auto-use fixture that mocks database clients before any tests run."""
    # Patch the database module's clients
    # We need to do this before app.main is imported
    with pytest.MonkeyPatch().context() as m:
        # Import and patch the database module
        import app.database
        m.setattr(app.database, 'supabase', mock_supabase_client)
        m.setattr(app.database, 'supabase_admin', mock_supabase_admin_client)
        yield

@pytest.fixture(scope="session")
def app():
    """Fixture to provide the FastAPI app instance."""
    # Ensure database clients are mocked before importing app
    import app.database
    app.database.supabase = mock_supabase_client
    app.database.supabase_admin = mock_supabase_admin_client
    
    from app.main import app
    return app

@pytest.fixture
def client(app):
    """Fixture to provide a test client."""
    return TestClient(app)

# Optional fixtures that require pytest-mock
# These are not used by the current tests but are available for future use
# Note: These fixtures will fail if pytest-mock is not installed
# The 'mocker' fixture comes from pytest-mock plugin and must be available
if pytest_mock_available:
    @pytest.fixture
    def mock_supabase_admin(mocker):
        """Fixture to mock supabase_admin for tests. Requires pytest-mock."""
        mock = mocker.patch('app.database.supabase_admin')
        return mock

    @pytest.fixture
    def mock_supabase_client(mocker):
        """Fixture to mock supabase (anon client) for tests. Requires pytest-mock."""
        mock = mocker.patch('app.database.supabase')
        return mock
