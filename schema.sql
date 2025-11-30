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
-- NOTE: The 'role' and 'school_id' columns are DEPRECATED and kept for backward compatibility.
-- Use the 'user_roles' table for multi-role support. These columns will be removed in a future version.
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL DEFAULT 'teacher', -- DEPRECATED: Use user_roles table instead
    school_id UUID REFERENCES schools(id) ON DELETE SET NULL, -- DEPRECATED: Use user_roles table instead
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_school_id ON users(school_id);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

COMMENT ON COLUMN users.role IS 'DEPRECATED: Use user_roles table for role management. Kept for backward compatibility.';
COMMENT ON COLUMN users.school_id IS 'DEPRECATED: Use user_roles table for school associations. Kept for backward compatibility.';

-- ============================================================================
-- USER ROLES (Junction table for multiple roles per user)
-- ============================================================================
-- Supports users having multiple roles simultaneously (e.g., platform_admin AND teacher)
-- Each role can be associated with a specific school (for school_admin, teacher) or NULL (for platform_admin)
CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'platform_admin', 'school_admin', 'teacher', 'student'
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE, -- NULL for platform-level roles
    is_active BOOLEAN DEFAULT true,
    granted_by UUID REFERENCES users(id) ON DELETE SET NULL, -- Who granted this role
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Optional expiration for temporary roles
    metadata JSONB, -- Additional role-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_user_role_school UNIQUE(user_id, role, school_id),
    CONSTRAINT platform_admin_no_school CHECK (
        (role = 'platform_admin' AND school_id IS NULL) OR 
        (role != 'platform_admin')
    )
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role);
CREATE INDEX IF NOT EXISTS idx_user_roles_school_id ON user_roles(school_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_active ON user_roles(user_id, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_user_roles_user_role ON user_roles(user_id, role, is_active);

COMMENT ON TABLE user_roles IS 'Junction table supporting multiple roles per user. Enables users to have platform_admin, school_admin, and teacher roles simultaneously.';
COMMENT ON COLUMN user_roles.role IS 'Role type: platform_admin, school_admin, teacher, or student';
COMMENT ON COLUMN user_roles.school_id IS 'School UUID for school-scoped roles (school_admin, teacher). NULL for platform_admin.';
COMMENT ON COLUMN user_roles.is_active IS 'Whether this role assignment is currently active';
COMMENT ON COLUMN user_roles.granted_by IS 'User ID who granted this role (for audit trail)';
COMMENT ON COLUMN user_roles.expires_at IS 'Optional expiration timestamp for temporary role assignments';
COMMENT ON COLUMN user_roles.metadata IS 'JSONB field for role-specific metadata (e.g., permissions, settings)';

-- ============================================================================
-- SCHOOL ADMIN INVITATIONS
-- ============================================================================
-- Stores invitation information for school admin users
CREATE TABLE IF NOT EXISTS school_admin_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    invitation_token VARCHAR(255) NOT NULL UNIQUE,
    invitation_sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invitation_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'accepted', 'expired'
    invitation_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_school_admin_invitations_school_id ON school_admin_invitations(school_id);
CREATE INDEX IF NOT EXISTS idx_school_admin_invitations_email ON school_admin_invitations(email);
CREATE INDEX IF NOT EXISTS idx_school_admin_invitations_token ON school_admin_invitations(invitation_token);
CREATE INDEX IF NOT EXISTS idx_school_admin_invitations_status ON school_admin_invitations(invitation_status);

COMMENT ON TABLE school_admin_invitations IS 'Stores invitation tokens for school admin users';
COMMENT ON COLUMN school_admin_invitations.invitation_token IS 'Unique token for school admin invitation email';
COMMENT ON COLUMN school_admin_invitations.invitation_sent_at IS 'Timestamp when invitation was sent';
COMMENT ON COLUMN school_admin_invitations.invitation_status IS 'Status of invitation: pending, accepted, expired';
COMMENT ON COLUMN school_admin_invitations.invitation_expires_at IS 'Expiration timestamp for invitation (typically 7 days)';
COMMENT ON COLUMN school_admin_invitations.invited_by IS 'User ID of the person who sent the invitation';

-- ============================================================================
-- TEACHERS
-- ============================================================================
-- Teachers table stores core teacher information (one record per teacher)
-- Teachers can work at multiple schools via the teacher_schools junction table
CREATE TABLE IF NOT EXISTS teachers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teachers_email ON teachers(email);

-- Add comments
COMMENT ON TABLE teachers IS 'Core teacher information. Teachers can work at multiple schools via teacher_schools table.';
COMMENT ON COLUMN teachers.email IS 'Unique email address for the teacher';

-- ============================================================================
-- TEACHER SCHOOLS (Junction Table)
-- ============================================================================
-- Links teachers to schools, enabling multi-school support
-- Stores invitation information per school-teacher relationship
CREATE TABLE IF NOT EXISTS teacher_schools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    -- Teacher invitation fields (for email-based invitations per school)
    invitation_token VARCHAR(255) UNIQUE,
    invitation_sent_at TIMESTAMP WITH TIME ZONE,
    invitation_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'accepted', 'expired'
    invitation_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(teacher_id, school_id) -- Prevent duplicate relationships
);

CREATE INDEX IF NOT EXISTS idx_teacher_schools_teacher_id ON teacher_schools(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_schools_school_id ON teacher_schools(school_id);
CREATE INDEX IF NOT EXISTS idx_teacher_schools_invitation_token ON teacher_schools(invitation_token) WHERE invitation_token IS NOT NULL;

-- Add comments for invitation fields
COMMENT ON TABLE teacher_schools IS 'Junction table linking teachers to schools, enabling multi-school support';
COMMENT ON COLUMN teacher_schools.invitation_token IS 'Unique token for teacher invitation email (per school)';
COMMENT ON COLUMN teacher_schools.invitation_sent_at IS 'Timestamp when invitation was sent';
COMMENT ON COLUMN teacher_schools.invitation_status IS 'Status of invitation: pending, accepted, expired';
COMMENT ON COLUMN teacher_schools.invitation_expires_at IS 'Expiration timestamp for invitation (typically 7 days)';

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
-- HELPER VIEWS
-- ============================================================================
-- View: Active user roles with school information
CREATE OR REPLACE VIEW active_user_roles AS
SELECT 
    ur.id,
    ur.user_id,
    ur.role,
    ur.school_id,
    s.name AS school_name,
    u.email,
    ur.is_active,
    ur.granted_by,
    ur.granted_at,
    ur.expires_at,
    ur.metadata,
    ur.created_at,
    ur.updated_at
FROM user_roles ur
JOIN users u ON ur.user_id = u.id
LEFT JOIN schools s ON ur.school_id = s.id
WHERE ur.is_active = true
  AND (ur.expires_at IS NULL OR ur.expires_at > NOW());

-- View: User role summary (aggregated view)
CREATE OR REPLACE VIEW user_role_summary AS
SELECT 
    u.id AS user_id,
    u.email,
    u.is_active AS user_is_active,
    ARRAY_AGG(DISTINCT ur.role) FILTER (WHERE ur.school_id IS NULL AND ur.is_active = true AND (ur.expires_at IS NULL OR ur.expires_at > NOW())) AS platform_roles,
    JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'role', ur.role,
            'school_id', ur.school_id,
            'school_name', s.name,
            'granted_at', ur.granted_at,
            'expires_at', ur.expires_at
        )
    ) FILTER (WHERE ur.school_id IS NOT NULL AND ur.is_active = true AND (ur.expires_at IS NULL OR ur.expires_at > NOW())) AS school_roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN schools s ON ur.school_id = s.id
GROUP BY u.id, u.email, u.is_active;

COMMENT ON VIEW active_user_roles IS 'View showing all active user roles with school information';
COMMENT ON VIEW user_role_summary IS 'Aggregated view showing platform and school roles per user';

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) - Optional but recommended
-- ============================================================================
-- Enable RLS on all tables (you can customize policies based on your needs)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_schools ENABLE ROW LEVEL SECURITY;
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
DROP POLICY IF EXISTS "Service role can do everything" ON user_roles;
DROP POLICY IF EXISTS "Service role can do everything" ON schools;
DROP POLICY IF EXISTS "Service role can do everything" ON school_locations;
DROP POLICY IF EXISTS "Service role can do everything" ON teachers;
DROP POLICY IF EXISTS "Service role can do everything" ON teacher_schools;
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
DROP POLICY IF EXISTS "Allow public read access" ON user_roles;
DROP POLICY IF EXISTS "Allow public read access" ON schools;
DROP POLICY IF EXISTS "Allow public read access" ON school_locations;
DROP POLICY IF EXISTS "Allow public read access" ON teachers;
DROP POLICY IF EXISTS "Allow public read access" ON teacher_schools;
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

CREATE POLICY "Service role can do everything" ON user_roles
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON schools
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON school_locations
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON teachers
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON teacher_schools
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
CREATE POLICY "Allow public read access" ON user_roles
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON schools
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON school_locations
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON teachers
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON teacher_schools
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
-- 7. MULTI-ROLE SYSTEM: The new user_roles table supports multiple roles per user.
--    - Use user_roles table for all new role assignments
--    - The users.role and users.school_id columns are deprecated but kept for backward compatibility
--    - For existing databases, run migrations/004_migrate_to_multi_role_system.sql to migrate data
--    - See active_user_roles and user_role_summary views for easy querying

