-- EigoKit Database Schema
-- Run this SQL in your Supabase SQL Editor to create all required tables
-- Run this BEFORE running seed.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SCHOOLS
-- ============================================================================
CREATE TABLE IF NOT EXISTS schools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    contact_info VARCHAR(255),
    account_status VARCHAR(50) DEFAULT 'trial',
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- USERS (for role management - links to Supabase Auth users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL DEFAULT 'teacher',
    school_id UUID REFERENCES schools(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_school_id ON users(school_id);

-- ============================================================================
-- TEACHERS
-- ============================================================================
CREATE TABLE IF NOT EXISTS teachers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    -- Teacher invitation fields (for email-based invitations)
    invitation_token VARCHAR(255) UNIQUE,
    invitation_sent_at TIMESTAMP WITH TIME ZONE,
    invitation_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'accepted', 'expired'
    invitation_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teachers_school_id ON teachers(school_id);
CREATE INDEX IF NOT EXISTS idx_teachers_invitation_token ON teachers(invitation_token) WHERE invitation_token IS NOT NULL;

-- Add comments for invitation fields
COMMENT ON COLUMN teachers.invitation_token IS 'Unique token for teacher invitation email';
COMMENT ON COLUMN teachers.invitation_sent_at IS 'Timestamp when invitation was sent';
COMMENT ON COLUMN teachers.invitation_status IS 'Status of invitation: pending, accepted, expired';
COMMENT ON COLUMN teachers.invitation_expires_at IS 'Expiration timestamp for invitation (typically 7 days)';

-- ============================================================================
-- SCHOOL LOCATIONS
-- ============================================================================
CREATE TABLE IF NOT EXISTS school_locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(255),
    prefecture VARCHAR(255),
    postal_code VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_school_locations_school_id ON school_locations(school_id);

-- ============================================================================
-- CLASSES
-- ============================================================================
CREATE TABLE IF NOT EXISTS classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    location_id UUID REFERENCES school_locations(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_classes_school_id ON classes(school_id);
CREATE INDEX IF NOT EXISTS idx_classes_teacher_id ON classes(teacher_id);
CREATE INDEX IF NOT EXISTS idx_classes_location_id ON classes(location_id);

-- ============================================================================
-- STUDENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    icon_sequence INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    registration_status VARCHAR(50) DEFAULT 'pending',
    streak_days INTEGER DEFAULT 0,
    badges TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_students_class_id ON students(class_id);

-- ============================================================================
-- VOCABULARY
-- ============================================================================
CREATE TABLE IF NOT EXISTS vocabulary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    english_word VARCHAR(255) NOT NULL,
    japanese_word VARCHAR(255) NOT NULL,
    example_sentence TEXT,
    audio_url VARCHAR(500),
    is_current_lesson BOOLEAN DEFAULT false,
    scheduled_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vocabulary_teacher_id ON vocabulary(teacher_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_class_id ON vocabulary(class_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_student_id ON vocabulary(student_id);

-- ============================================================================
-- GRAMMAR
-- ============================================================================
CREATE TABLE IF NOT EXISTS grammar (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    rule_description TEXT NOT NULL,
    examples TEXT[] DEFAULT ARRAY[]::TEXT[],
    is_current_lesson BOOLEAN DEFAULT false,
    scheduled_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_grammar_teacher_id ON grammar(teacher_id);
CREATE INDEX IF NOT EXISTS idx_grammar_class_id ON grammar(class_id);
CREATE INDEX IF NOT EXISTS idx_grammar_student_id ON grammar(student_id);

-- ============================================================================
-- SURVEY QUESTIONS
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    question_type VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    question_text_jp TEXT,
    options TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_survey_questions_teacher_id ON survey_questions(teacher_id);
CREATE INDEX IF NOT EXISTS idx_survey_questions_class_id ON survey_questions(class_id);

-- ============================================================================
-- SURVEY RESPONSES
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    lesson_id VARCHAR(255) NOT NULL,
    question_id UUID NOT NULL REFERENCES survey_questions(id) ON DELETE CASCADE,
    response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_survey_responses_student_id ON survey_responses(student_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_question_id ON survey_responses(question_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_lesson_id ON survey_responses(lesson_id);

-- ============================================================================
-- GAME SESSIONS
-- ============================================================================
CREATE TABLE IF NOT EXISTS game_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL,
    score INTEGER DEFAULT 0,
    content_ids UUID[] DEFAULT ARRAY[]::UUID[],
    difficulty_level INTEGER DEFAULT 1,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_game_sessions_student_id ON game_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_game_type ON game_sessions(game_type);

-- ============================================================================
-- PAYMENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'JPY',
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    billing_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    billing_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    payment_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_school_id ON payments(school_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- ============================================================================
-- THEMES
-- ============================================================================
CREATE TABLE IF NOT EXISTS themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL UNIQUE REFERENCES schools(id) ON DELETE CASCADE,
    primary_color VARCHAR(50) DEFAULT '#3B82F6',
    secondary_color VARCHAR(50) DEFAULT '#10B981',
    accent_color VARCHAR(50) DEFAULT '#F59E0B',
    font_family VARCHAR(255),
    logo_url VARCHAR(500),
    app_icon_url VARCHAR(500),
    favicon_url VARCHAR(500),
    background_color VARCHAR(50),
    button_style JSONB,
    card_style JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_themes_school_id ON themes(school_id);

-- ============================================================================
-- FEATURE FLAGS
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT false,
    expiration_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(school_id, feature_name)
);

CREATE INDEX IF NOT EXISTS idx_feature_flags_school_id ON feature_flags(school_id);
CREATE INDEX IF NOT EXISTS idx_feature_flags_feature_name ON feature_flags(feature_name);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) - Optional but recommended
-- ============================================================================
-- Enable RLS on all tables (you can customize policies based on your needs)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocabulary ENABLE ROW LEVEL SECURITY;
ALTER TABLE grammar ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;

-- Basic policies (allow all for now - customize based on your security needs)
-- In production, you should create proper policies based on user roles

-- Drop existing policies if they exist (for re-running this script)
DROP POLICY IF EXISTS "Service role can do everything" ON users;
DROP POLICY IF EXISTS "Service role can do everything" ON schools;
DROP POLICY IF EXISTS "Service role can do everything" ON school_locations;
DROP POLICY IF EXISTS "Service role can do everything" ON teachers;
DROP POLICY IF EXISTS "Service role can do everything" ON classes;
DROP POLICY IF EXISTS "Service role can do everything" ON students;
DROP POLICY IF EXISTS "Service role can do everything" ON vocabulary;
DROP POLICY IF EXISTS "Service role can do everything" ON grammar;
DROP POLICY IF EXISTS "Service role can do everything" ON survey_questions;
DROP POLICY IF EXISTS "Service role can do everything" ON survey_responses;
DROP POLICY IF EXISTS "Service role can do everything" ON game_sessions;
DROP POLICY IF EXISTS "Service role can do everything" ON payments;
DROP POLICY IF EXISTS "Service role can do everything" ON themes;
DROP POLICY IF EXISTS "Service role can do everything" ON feature_flags;

DROP POLICY IF EXISTS "Allow public read access" ON users;
DROP POLICY IF EXISTS "Allow public read access" ON schools;
DROP POLICY IF EXISTS "Allow public read access" ON school_locations;
DROP POLICY IF EXISTS "Allow public read access" ON teachers;
DROP POLICY IF EXISTS "Allow public read access" ON classes;
DROP POLICY IF EXISTS "Allow public read access" ON students;
DROP POLICY IF EXISTS "Allow public read access" ON vocabulary;
DROP POLICY IF EXISTS "Allow public read access" ON grammar;
DROP POLICY IF EXISTS "Allow public read access" ON survey_questions;
DROP POLICY IF EXISTS "Allow public read access" ON survey_responses;
DROP POLICY IF EXISTS "Allow public read access" ON game_sessions;
DROP POLICY IF EXISTS "Allow public read access" ON themes;
DROP POLICY IF EXISTS "Allow public read access" ON feature_flags;

-- Allow service role to do everything (for backend API)
CREATE POLICY "Service role can do everything" ON users
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON schools
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON school_locations
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON teachers
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON classes
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON students
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON vocabulary
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON grammar
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON survey_questions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON survey_responses
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON game_sessions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON payments
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON themes
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON feature_flags
    FOR ALL USING (auth.role() = 'service_role');

-- For development/testing, you might want to allow public access
-- Remove these in production and use proper authentication-based policies
CREATE POLICY "Allow public read access" ON schools
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON school_locations
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON teachers
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON classes
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON students
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON vocabulary
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON grammar
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON survey_questions
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON survey_responses
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON game_sessions
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON themes
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON feature_flags
    FOR SELECT USING (true);

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. Run this schema.sql file FIRST before running seed.sql
-- 2. The RLS policies above are basic - customize them for production
-- 3. Make sure to set up proper authentication in Supabase
-- 4. Consider adding more indexes based on your query patterns
-- 5. The service_role policy allows the backend API (using service key) to access everything
-- 6. For production, implement proper role-based access control policies

