# EigoKit Backend API

FastAPI backend server for the EigoKit English learning platform.

## Prerequisites

- Python 3.11 or 3.12 (recommended)
  - Python 3.13 may have compatibility issues with some packages
  - If using Python 3.13, you may need to install build tools: `brew install rust` (macOS) or install Rust compiler
- Supabase account and project

## Setup

0. Virtual Environment Setup:

**If using pyenv (recommended):**
```bash
# Install Python 3.12.0 if not already installed
pyenv install 3.12.0

# Set Python version for this project
pyenv local 3.12.0

# Verify Python version
python --version  # Should show Python 3.12.0

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**If not using pyenv:**
```bash
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

1. Install dependencies (choose one method):

**Method 1: Using the installation script (recommended):**
```bash
./install.sh
```

**Method 2: Manual installation:**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Troubleshooting Python 3.13 build errors:**

If you encounter `Failed building wheel for pydantic-core` on Python 3.13:

- **Option 1 (Recommended):** Use Python 3.11 or 3.12:
  
  **If using pyenv:**
  ```bash
  pyenv local 3.12.0  # or 3.11.x
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
  
  **If not using pyenv:**
  ```bash
  python3.12 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

- **Option 2:** Install Rust compiler (required for building pydantic-core from source):
  ```bash
  # macOS
  brew install rust
  
  # Linux/Windows
  # Visit https://rustup.rs/ and follow installation instructions
  
  # Then retry installation
  pip install -r requirements.txt
  ```

- **Option 3:** Try installing with upgraded build tools:
  ```bash
  pip install --upgrade pip setuptools wheel maturin
  pip install -r requirements.txt
  ```

2. Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

3. Fill in your credentials in `.env`:
   - Copy `.env.example` to `.env` and fill in the values
   - See `.env.example` for detailed explanations of all variables
   - **Required**: Supabase credentials (PROJECT_URL, ANON_KEY, SERVICE_ROLE_KEY)
   - **Optional**: Email service credentials (RESEND_API_KEY, RESEND_FROM_EMAIL) for invitations
   - **Optional**: Frontend base URLs for password reset redirects (used for Supabase password reset links)
   
   Quick reference:
   ```
   SUPABASE_PROJECT_URL=https://your-project-ref.supabase.co
   SUPABASE_ANON_KEY=your_publishable_key_here
   SUPABASE_SERVICE_ROLE_KEY=your_secret_key_here
   RESEND_API_KEY=re_your_api_key_here  # Optional - for invitations
   RESEND_FROM_EMAIL=onboarding@resend.dev  # Optional

   # Optional: Frontend base URLs for password reset redirects
   # These are base URLs only (no paths). The backend will append /auth/reset-password automatically.
   # Use the appropriate frontend base URL for each role:
   FRONTEND_ADMINS_URL=http://localhost:5173  # Platform admin frontend base URL
   FRONTEND_SCHOOLS_URL=http://localhost:5174  # School admin frontend base URL
   FRONTEND_TEACHERS_URL=http://localhost:5175  # Teacher frontend base URL
   ```

4. Set up your Supabase database schema:
   
   a. Open your Supabase project dashboard
   b. Go to the SQL Editor
   c. Run `schema.sql` first to create all tables
   d. **If you ran schema.sql before the users table was added**, run `migration_add_users_table.sql` to add the users table
   e. **If you have an existing database**, run `migration_add_school_locations.sql` to add school locations support (see `MIGRATION_GUIDE_SCHOOL_LOCATIONS.md` for details)
   f. (Optional) Run `seed.sql` to populate with mock data for testing
   
   The schema includes:
   - `users` (managed by Supabase Auth)
   - `schools`
   - `school_locations` (multiple locations per school)
   - `teachers`
   - `classes` (can be assigned to locations)
   - `students`
   - `vocabulary`
   - `grammar`
   - `survey_questions`
   - `survey_responses`
   - `game_sessions`
   - `payments`
   - `themes`
   - `feature_flags`

## Running Locally

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI) will be available at `http://localhost:8000/docs`

### Generating OpenAPI Specification

To generate the OpenAPI YAML file:

```bash
python generate_openapi.py
```

This will create `openapi.yaml` in the root directory with the complete API specification. The file can be used for:
- API documentation
- Client SDK generation
- API testing tools
- Importing into API management platforms

## Running Tests

The backend includes unit tests using `pytest`. Test dependencies are included in `requirements.txt`.

**⚠️ IMPORTANT:** Always run tests from within the virtual environment. Running tests outside the venv will cause import errors.

```bash
# 1. Navigate to the backend directory
cd eigokit_backend

# 2. Activate the virtual environment (REQUIRED)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Verify you're using the venv Python
which python  # Should show: .../eigokit_backend/.venv/bin/python

# 4. Install test dependencies (if not already installed)
pip install -r requirements.txt

# 5. Run tests
pytest
```

**Note:** Tests use mocks for external dependencies (Supabase, pydantic-settings) so they can run without requiring all production dependencies to be installed.

### Running All Tests

```bash
# Make sure you're in the virtual environment first!
source .venv/bin/activate

# Run all tests
pytest

# Or use python -m pytest to ensure correct Python environment
python -m pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=app --cov-report=html
```

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/test_schools_teachers.py

# Run a specific test function
pytest tests/test_schools_teachers.py::test_get_school_teachers_with_accepted_teacher

# Run tests matching a pattern
pytest -k "teacher"
```

### Test Structure

Tests are located in the `tests/` directory:
- `tests/test_schools_teachers.py` - Tests for school teacher management endpoints

### Writing New Tests

When writing new tests:
1. Create test files in the `tests/` directory
2. Use `pytest` fixtures and `pytest-mock` for mocking Supabase calls
3. Follow the existing test patterns in `test_schools_teachers.py`
4. Use descriptive test function names starting with `test_`

Example test structure:
```python
import pytest
from fastapi.testclient import TestClient

def test_endpoint_name(client, mocker):
    """Test description"""
    # Mock Supabase calls
    mock_supabase = mocker.patch('app.routers.module_name.supabase_admin')
    # ... setup mocks ...
    
    # Make request (client is provided by conftest.py fixture)
    response = client.get("/api/endpoint")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == expected_data
```

**Note:** Use the `client` fixture from `conftest.py` instead of creating `TestClient(app)` directly. This ensures all mocks are properly set up before the app is imported.

### Test Environment

Tests use mocks for Supabase database calls, so they don't require a live database connection. This makes tests:
- Fast to run
- Independent of external services
- Safe to run in CI/CD pipelines

**Note:** The `conftest.py` file automatically mocks the Supabase and pydantic-settings modules before any test imports happen. This prevents import errors when these packages aren't installed in the test environment. The mocks are set up at the module level, so all tests automatically use mocked dependencies.

**Note on deprecation warnings:** You may see a deprecation warning from `httpx` about the `app` shortcut. This is harmless and comes from httpx's internal usage. It doesn't affect test functionality and can be safely ignored. To suppress it, you can run tests with: `pytest -W ignore::DeprecationWarning`

### Troubleshooting Test Errors

#### Error: `fixture 'mocker' not found`

**Root Cause:** The `mocker` fixture is provided by the `pytest-mock` plugin. This error occurs when:
- Tests are run outside the virtual environment
- `pytest-mock` is not installed
- pytest is using a different Python environment

**Solution:**
1. **Activate the virtual environment (REQUIRED):**
   ```bash
   cd eigokit_backend
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Verify you're using the venv Python:**
   ```bash
   which python
   # Should show: .../eigokit_backend/.venv/bin/python
   ```

3. **Install test dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify pytest-mock is installed:**
   ```bash
   pip list | grep pytest-mock
   # Should show: pytest-mock 3.15.1 (or similar)
   ```

5. **Run tests using the venv Python:**
   ```bash
   python -m pytest tests/ -v
   # NOT: pytest tests/ -v (might use system pytest)
   ```

6. **Verify mocker fixture is available:**
   ```bash
   python -m pytest --fixtures tests/ | grep mocker
   # Should show: mocker -- .../pytest_mock/plugin.py
   ```

#### Other Common Errors

1. **"ModuleNotFoundError" for supabase or pydantic_settings:**
   - This should be handled by `conftest.py` mocks
   - Make sure `conftest.py` is in the `tests/` directory
   - Try running with: `python -m pytest tests/ -v` to ensure the correct Python environment is used

2. **Database connection errors:**
   - Tests use mocks, so this shouldn't happen
   - Check that `conftest.py` is properly mocking `app.database.supabase` and `app.database.supabase_admin`

3. **Clear pytest cache:**
   ```bash
   rm -rf .pytest_cache
   python -m pytest tests/ -v
   ```

#### Diagnostic Tools

Run the diagnostic script to check your environment:
```bash
python tests/check_pytest_setup.py
```

See `tests/README_TROUBLESHOOTING.md` for more detailed troubleshooting information.

## Database Schema

The backend expects the following Supabase tables:

- **schools**: id, name, contact_info, account_status, subscription_tier
- **teachers**: id, name, email, school_id
- **classes**: id, name, school_id, teacher_id
- **students**: id, name, class_id, icon_sequence, registration_status, streak_days, badges
- **vocabulary**: id, teacher_id, class_id, student_id, english_word, japanese_word, example_sentence, audio_url, is_current_lesson, scheduled_date
- **grammar**: id, teacher_id, class_id, student_id, rule_name, rule_description, examples, is_current_lesson, scheduled_date
- **survey_questions**: id, teacher_id, class_id, question_type, question_text, question_text_jp, options
- **survey_responses**: id, student_id, lesson_id, question_id, response
- **game_sessions**: id, student_id, game_type, score, content_ids, difficulty_level
- **payments**: id, school_id, amount, currency, payment_method, status, billing_period_start, billing_period_end, payment_date, notes
- **themes**: id, school_id, primary_color, secondary_color, accent_color, font_family, logo_url, app_icon_url, favicon_url, background_color, button_style, card_style
- **feature_flags**: id, school_id, feature_name, enabled, expiration_date

## API Endpoints

- `/api/auth/*` - Authentication endpoints
- `/api/students/*` - Student-related endpoints
- `/api/teachers/*` - Teacher-related endpoints
- `/api/schools/*` - School admin endpoints
- `/api/platform/*` - Platform admin endpoints
- `/api/content/*` - Content management
- `/api/surveys/*` - Survey management
- `/api/games/*` - Game configuration
- `/api/payments/*` - Payment processing
- `/api/theming/*` - Theme configuration
- `/api/features/*` - Feature flags

## Deployment

This backend can be deployed to services like:
- Render
- Railway
- Fly.io
- Heroku
- LeapCell
- AWS/GCP/Azure

Make sure to set environment variables in your deployment platform.

### Deploying to LeapCell

1. **Create a new project** on LeapCell and connect your repository

2. **Set environment variables** in LeapCell dashboard:
   - `SUPABASE_PROJECT_URL` - Your Supabase project URL
   - `SUPABASE_ANON_KEY` - Your Supabase anonymous key
   - `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
   - `RESEND_API_KEY` - (Optional) For email invitations
   - `RESEND_FROM_EMAIL` - (Optional) Email sender address
   - `FRONTEND_ADMINS_URL` - (Optional) Platform admin frontend URL
   - `FRONTEND_SCHOOLS_URL` - (Optional) School admin frontend URL
   - `FRONTEND_TEACHERS_URL` - (Optional) Teacher frontend URL

3. **Configure the start command**:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
   ```
   
   Or if LeapCell uses a fixed port:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

4. **Set Python version** (if available):
   - Python 3.12 (recommended) or 3.11

5. **Deploy**: Push your code or trigger deployment from LeapCell dashboard

**Note**: Make sure your Supabase database schema is set up (run `schema.sql` in Supabase SQL Editor) before deploying.

## Email Service Setup

For teacher invitation emails, configure an email service (recommended: **Resend**).

**Quick Setup:**
1. Sign up at https://resend.com and get your API key
2. Add to `.env`: `RESEND_API_KEY=your_key`, `RESEND_FROM_EMAIL=onboarding@resend.dev`
3. If using a new database: `schema.sql` already includes invitation fields
4. If using an existing database: Run `migration_add_teacher_invitations.sql` to add invitation fields

See `EMAIL_SERVICE_SETUP.md` for detailed instructions and alternative services.

**Note:** Email is optional. Without it, teachers can still be created but no invitation emails will be sent.

## Database Setup Files

- **schema.sql**: Creates all required database tables, indexes, and basic RLS policies
- **migration_add_users_table.sql**: Migration script to add the users table (run this if you set up the database before the users table was added)
- **migration_add_school_locations.sql**: Migration script to add school locations support (run this if you have an existing database - see `MIGRATION_GUIDE_SCHOOL_LOCATIONS.md`)
- **migration_add_teacher_invitations.sql**: Migration script to add teacher invitation fields (only needed if you created the database before teacher invitations were added to schema.sql)
- **seed.sql**: Populates the database with mock data for testing (3 schools, 4 teachers, 13 students, etc.)
- **MIGRATION_GUIDE_SCHOOL_LOCATIONS.md**: Detailed guide for migrating existing databases to support school locations
- **EMAIL_SERVICE_SETUP.md**: Guide for setting up email service for teacher invitations

**Important**: 
1. Run `schema.sql` first to create all tables (includes teacher invitation fields)
2. If you get an error about the `users` table not existing, run `migration_add_users_table.sql`
3. If you have an existing database and want to add school locations support, run `migration_add_school_locations.sql` (see `MIGRATION_GUIDE_SCHOOL_LOCATIONS.md`)
4. If you have an existing database created before teacher invitations were added, run `migration_add_teacher_invitations.sql` to add invitation fields
5. Then run `seed.sql` to populate with mock data

**Note**: The `users` table links to Supabase Auth's `auth.users` table. Make sure you have created at least one user in Supabase Auth before inserting into the `users` table.

