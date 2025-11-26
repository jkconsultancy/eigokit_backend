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

3. Fill in your Supabase credentials in `.env`:
```
# Get these from your Supabase project dashboard: https://app.supabase.com/project/_/settings/api
SUPABASE_PROJECT_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_publishable_key_here  # "Publishable key" in Project Settings > API keys
SUPABASE_SERVICE_ROLE_KEY=your_secret_key_here  # "Secret key" in Project Settings > API keys
SUPABASE_JWT_SECRET=your_jwt_signing_key_here  # Optional - found in Project Settings > API > JWT Settings
ENVIRONMENT=development
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
- AWS/GCP/Azure

Make sure to set environment variables in your deployment platform.

## Database Setup Files

- **schema.sql**: Creates all required database tables, indexes, and basic RLS policies
- **migration_add_users_table.sql**: Migration script to add the users table (run this if you set up the database before the users table was added)
- **migration_add_school_locations.sql**: Migration script to add school locations support (run this if you have an existing database - see `MIGRATION_GUIDE_SCHOOL_LOCATIONS.md`)
- **seed.sql**: Populates the database with mock data for testing (3 schools, 4 teachers, 13 students, etc.)
- **MIGRATION_GUIDE_SCHOOL_LOCATIONS.md**: Detailed guide for migrating existing databases to support school locations

**Important**: 
1. Run `schema.sql` first to create all tables
2. If you get an error about the `users` table not existing, run `migration_add_users_table.sql`
3. If you have an existing database and want to add school locations support, run `migration_add_school_locations.sql` (see `MIGRATION_GUIDE_SCHOOL_LOCATIONS.md`)
4. Then run `seed.sql` to populate with mock data

**Note**: The `users` table links to Supabase Auth's `auth.users` table. Make sure you have created at least one user in Supabase Auth before inserting into the `users` table.

