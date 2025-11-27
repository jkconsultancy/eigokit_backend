-- EigoKit Database Seed Data
-- Run this SQL in your Supabase SQL Editor to populate the database with mock data
-- 
-- IMPORTANT: Before running this seed file:
-- 1. Create a platform admin user in Supabase Auth (Authentication > Users > Add User)
-- 2. Note the user's UUID from Supabase Auth
-- 3. Update the PLATFORM_ADMIN_USER_ID below with that UUID
-- 4. Or manually insert the user record after creating the auth user

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PLATFORM ADMIN USER
-- ============================================================================
-- NOTE: Replace 'YOUR_PLATFORM_ADMIN_AUTH_USER_ID' with the actual UUID from Supabase Auth
-- To create a platform admin:
-- 1. Go to Supabase Dashboard > Authentication > Users > Add User
-- 2. Create user with email/password (e.g., admin@eigokit.com)
-- 3. Copy the user's UUID
-- 4. Replace the UUID below and uncomment the INSERT statement
--
-- INSERT INTO users (id, email, role, created_at) VALUES
-- ('YOUR_PLATFORM_ADMIN_AUTH_USER_ID', 'admin@eigokit.com', 'platform_admin', NOW())
-- ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SCHOOLS
-- ============================================================================
INSERT INTO schools (id, name, contact_info, account_status, subscription_tier, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Tokyo English Academy', 'contact@tokyoenglish.ac.jp', 'active', 'premium', NOW()),
('550e8400-e29b-41d4-a716-446655440002', 'Osaka Kids English', 'info@osakakids.jp', 'active', 'standard', NOW()),
('550e8400-e29b-41d4-a716-446655440003', 'Yokohama Learning Center', 'hello@yokohamalearning.jp', 'trial', 'basic', NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- TEACHERS
-- ============================================================================
-- Note: Teachers are now stored without school_id (multi-school support)
-- School associations are managed via the teacher_schools junction table
INSERT INTO teachers (id, name, email, created_at) VALUES
('660e8400-e29b-41d4-a716-446655440001', 'Sarah Johnson', 'sarah.johnson@tokyoenglish.ac.jp', NOW()),
('660e8400-e29b-41d4-a716-446655440002', 'Michael Chen', 'michael.chen@tokyoenglish.ac.jp', NOW()),
('660e8400-e29b-41d4-a716-446655440003', 'Emma Williams', 'emma.williams@osakakids.jp', NOW()),
('660e8400-e29b-41d4-a716-446655440004', 'David Tanaka', 'david.tanaka@yokohamalearning.jp', NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- TEACHER SCHOOLS (Junction Table)
-- ============================================================================
-- Links teachers to schools, enabling multi-school support
-- Note: For seed data, we're creating accepted relationships without invitation tokens
-- In production, teachers should be added via the School Admin app, which will
-- automatically generate invitation tokens and send invitation emails
-- Example: Sarah Johnson works at Tokyo English Academy (and could work at other schools too)
INSERT INTO teacher_schools (id, teacher_id, school_id, invitation_status, created_at) VALUES
('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'accepted', NOW()),
('770e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'accepted', NOW()),
('770e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440002', 'accepted', NOW()),
('770e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440003', 'accepted', NOW()),
-- Example: Sarah Johnson also works at Osaka Kids English (multi-school support)
('770e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', 'accepted', NOW())
ON CONFLICT (teacher_id, school_id) DO NOTHING;

-- ============================================================================
-- CLASSES
-- ============================================================================
INSERT INTO classes (id, name, school_id, teacher_id, created_at) VALUES
('770e8400-e29b-41d4-a716-446655440001', 'Beginner Class A', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', NOW()),
('770e8400-e29b-41d4-a716-446655440002', 'Intermediate Class B', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', NOW()),
('770e8400-e29b-41d4-a716-446655440003', 'Advanced Class C', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', NOW()),
('770e8400-e29b-41d4-a716-446655440004', 'Kids Class 1', '550e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440003', NOW()),
('770e8400-e29b-41d4-a716-446655440005', 'Kids Class 2', '550e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440003', NOW()),
('770e8400-e29b-41d4-a716-446655440006', 'Trial Class', '550e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440004', NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- STUDENTS
-- ============================================================================
INSERT INTO students (id, name, class_id, icon_sequence, registration_status, streak_days, badges, created_at) VALUES
-- Class 1 students
('880e8400-e29b-41d4-a716-446655440001', 'Yuki Tanaka', '770e8400-e29b-41d4-a716-446655440001', ARRAY[1, 5, 9, 13], 'registered', 5, ARRAY['first_week', 'vocab_master'], NOW()),
('880e8400-e29b-41d4-a716-446655440002', 'Hiroshi Suzuki', '770e8400-e29b-41d4-a716-446655440001', ARRAY[2, 6, 10, 14], 'registered', 3, ARRAY['first_week'], NOW()),
('880e8400-e29b-41d4-a716-446655440003', 'Sakura Yamamoto', '770e8400-e29b-41d4-a716-446655440001', ARRAY[3, 7, 11, 15], 'registered', 7, ARRAY['first_week', 'streak_king'], NOW()),
('880e8400-e29b-41d4-a716-446655440004', 'Kenji Watanabe', '770e8400-e29b-41d4-a716-446655440001', ARRAY[4, 8, 12, 16], 'pending', 0, ARRAY[]::text[], NOW()),

-- Class 2 students
('880e8400-e29b-41d4-a716-446655440005', 'Mei Sato', '770e8400-e29b-41d4-a716-446655440002', ARRAY[1, 6, 11, 16], 'registered', 10, ARRAY['first_week', 'vocab_master', 'streak_king'], NOW()),
('880e8400-e29b-41d4-a716-446655440006', 'Riku Nakamura', '770e8400-e29b-41d4-a716-446655440002', ARRAY[2, 7, 12, 17], 'registered', 4, ARRAY['first_week'], NOW()),
('880e8400-e29b-41d4-a716-446655440007', 'Aoi Kobayashi', '770e8400-e29b-41d4-a716-446655440002', ARRAY[3, 8, 13, 18], 'registered', 6, ARRAY['first_week', 'grammar_guru'], NOW()),

-- Class 3 students
('880e8400-e29b-41d4-a716-446655440008', 'Ren Ito', '770e8400-e29b-41d4-a716-446655440003', ARRAY[4, 9, 14, 19], 'registered', 12, ARRAY['first_week', 'vocab_master', 'grammar_guru', 'streak_king'], NOW()),
('880e8400-e29b-41d4-a716-446655440009', 'Mio Kato', '770e8400-e29b-41d4-a716-446655440003', ARRAY[5, 10, 15, 20], 'registered', 8, ARRAY['first_week', 'vocab_master'], NOW()),

-- Class 4 students (Osaka)
('880e8400-e29b-41d4-a716-446655440010', 'Taro Yamada', '770e8400-e29b-41d4-a716-446655440004', ARRAY[1, 7, 13, 19], 'registered', 2, ARRAY['first_week'], NOW()),
('880e8400-e29b-41d4-a716-446655440011', 'Hanako Saito', '770e8400-e29b-41d4-a716-446655440004', ARRAY[2, 8, 14, 20], 'registered', 1, ARRAY['first_week'], NOW()),

-- Class 5 students (Osaka)
('880e8400-e29b-41d4-a716-446655440012', 'Jiro Matsumoto', '770e8400-e29b-41d4-a716-446655440005', ARRAY[3, 9, 15, 21], 'registered', 0, ARRAY[]::text[], NOW()),
('880e8400-e29b-41d4-a716-446655440013', 'Akari Fujita', '770e8400-e29b-41d4-a716-446655440005', ARRAY[4, 10, 16, 22], 'pending', 0, ARRAY[]::text[], NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- VOCABULARY
-- ============================================================================
INSERT INTO vocabulary (id, teacher_id, class_id, student_id, english_word, japanese_word, example_sentence, audio_url, is_current_lesson, scheduled_date, created_at) VALUES
-- Class 1 vocabulary
('990e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', NULL, 'apple', 'りんご', 'I like to eat an apple.', NULL, true, NOW(), NOW()),
('990e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', NULL, 'banana', 'バナナ', 'The banana is yellow.', NULL, true, NOW(), NOW()),
('990e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', NULL, 'orange', 'オレンジ', 'I have an orange for lunch.', NULL, false, NOW() - INTERVAL '7 days', NOW()),
('990e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', NULL, 'cat', 'ねこ', 'The cat is sleeping.', NULL, true, NOW(), NOW()),
('990e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', NULL, 'dog', 'いぬ', 'My dog is very friendly.', NULL, true, NOW(), NOW()),

-- Class 2 vocabulary
('990e8400-e29b-41d4-a716-446655440006', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', NULL, 'book', 'ほん', 'I read a book every day.', NULL, true, NOW(), NOW()),
('990e8400-e29b-41d4-a716-446655440007', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', NULL, 'pencil', 'えんぴつ', 'Can I borrow your pencil?', NULL, true, NOW(), NOW()),
('990e8400-e29b-41d4-a716-446655440008', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', NULL, 'school', 'がっこう', 'I go to school by bus.', NULL, false, NOW() - INTERVAL '3 days', NOW()),

-- Class 3 vocabulary (advanced)
('990e8400-e29b-41d4-a716-446655440009', '660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', NULL, 'beautiful', '美しい', 'The sunset is beautiful.', NULL, true, NOW(), NOW()),
('990e8400-e29b-41d4-a716-446655440010', '660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', NULL, 'adventure', '冒険', 'Life is an adventure.', NULL, true, NOW(), NOW()),

-- Student-specific vocabulary
('990e8400-e29b-41d4-a716-446655440011', '660e8400-e29b-41d4-a716-446655440001', NULL, '880e8400-e29b-41d4-a716-446655440001', 'elephant', 'ぞう', 'The elephant is very big.', NULL, false, NOW(), NOW()),
('990e8400-e29b-41d4-a716-446655440012', '660e8400-e29b-41d4-a716-446655440001', NULL, '880e8400-e29b-41d4-a716-446655440002', 'tiger', 'とら', 'The tiger is orange and black.', NULL, false, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- GRAMMAR
-- ============================================================================
INSERT INTO grammar (id, teacher_id, class_id, student_id, rule_name, rule_description, examples, is_current_lesson, scheduled_date, created_at) VALUES
-- Class 1 grammar
('aa0e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', NULL, 'Simple Present', 'Use simple present for habits and facts', ARRAY['I play soccer.', 'She likes ice cream.', 'They go to school.'], true, NOW(), NOW()),
('aa0e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', NULL, 'Articles: a/an', 'Use "a" before consonants, "an" before vowels', ARRAY['a cat', 'an apple', 'a book', 'an orange'], true, NOW(), NOW()),

-- Class 2 grammar
('aa0e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', NULL, 'Present Continuous', 'Use for actions happening now', ARRAY['I am reading.', 'She is playing.', 'They are studying.'], true, NOW(), NOW()),
('aa0e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', NULL, 'Plural Nouns', 'Add -s or -es to make nouns plural', ARRAY['cat → cats', 'box → boxes', 'child → children'], false, NOW() - INTERVAL '5 days', NOW()),

-- Class 3 grammar (advanced)
('aa0e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', NULL, 'Past Perfect', 'Use for actions completed before another past action', ARRAY['I had finished my homework before dinner.', 'She had left when I arrived.'], true, NOW(), NOW()),
('aa0e8400-e29b-41d4-a716-446655440006', '660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', NULL, 'Conditional Sentences', 'If + past simple, would + verb', ARRAY['If I had time, I would travel.', 'If it rained, we would stay home.'], false, NOW() - INTERVAL '2 days', NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SURVEY QUESTIONS
-- ============================================================================
INSERT INTO survey_questions (id, teacher_id, class_id, question_type, question_text, question_text_jp, options, created_at) VALUES
-- Class 1 questions
('bb0e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 'emoji_scale', 'How did you feel about today''s lesson?', '今日のレッスンはどうでしたか？', NULL, NOW()),
('bb0e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 'multiple_choice', 'Which word was the most difficult?', 'どの単語が一番難しかったですか？', ARRAY['apple', 'banana', 'orange', 'cat', 'dog'], NOW()),
('bb0e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 'yes_no', 'Did you understand the grammar lesson?', '文法のレッスンは理解できましたか？', NULL, NOW()),
('bb0e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 'short_answer', 'What did you learn today?', '今日は何を学びましたか？', NULL, NOW()),

-- Class 2 questions
('bb0e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 'emoji_scale', 'How confident do you feel with the new vocabulary?', '新しい単語にどのくらい自信がありますか？', NULL, NOW()),
('bb0e8400-e29b-41d4-a716-446655440006', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 'yes_no', 'Would you like more practice with this topic?', 'このトピックをもっと練習したいですか？', NULL, NOW()),

-- Class 3 questions
('bb0e8400-e29b-41d4-a716-446655440007', '660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', 'emoji_scale', 'Rate your enjoyment of today''s lesson', '今日のレッスンの楽しさを評価してください', NULL, NOW()),
('bb0e8400-e29b-41d4-a716-446655440008', '660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', 'short_answer', 'What grammar rule was most challenging?', 'どの文法ルールが最も難しかったですか？', NULL, NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SURVEY RESPONSES
-- ============================================================================
INSERT INTO survey_responses (id, student_id, lesson_id, question_id, response, created_at) VALUES
-- Student 1 responses
('cc0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 'lesson_001', 'bb0e8400-e29b-41d4-a716-446655440001', '4', NOW() - INTERVAL '1 day'),
('cc0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440001', 'lesson_001', 'bb0e8400-e29b-41d4-a716-446655440002', 'orange', NOW() - INTERVAL '1 day'),
('cc0e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440001', 'lesson_001', 'bb0e8400-e29b-41d4-a716-446655440003', 'yes', NOW() - INTERVAL '1 day'),

-- Student 2 responses
('cc0e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440002', 'lesson_001', 'bb0e8400-e29b-41d4-a716-446655440001', '3', NOW() - INTERVAL '1 day'),
('cc0e8400-e29b-41d4-a716-446655440005', '880e8400-e29b-41d4-a716-446655440002', 'lesson_001', 'bb0e8400-e29b-41d4-a716-446655440002', 'banana', NOW() - INTERVAL '1 day'),

-- Student 3 responses
('cc0e8400-e29b-41d4-a716-446655440006', '880e8400-e29b-41d4-a716-446655440003', 'lesson_001', 'bb0e8400-e29b-41d4-a716-446655440001', '5', NOW() - INTERVAL '1 day'),
('cc0e8400-e29b-41d4-a716-446655440007', '880e8400-e29b-41d4-a716-446655440003', 'lesson_001', 'bb0e8400-e29b-41d4-a716-446655440003', 'yes', NOW() - INTERVAL '1 day'),

-- Student 5 responses (Class 2)
('cc0e8400-e29b-41d4-a716-446655440008', '880e8400-e29b-41d4-a716-446655440005', 'lesson_002', 'bb0e8400-e29b-41d4-a716-446655440005', '4', NOW() - INTERVAL '2 days'),
('cc0e8400-e29b-41d4-a716-446655440009', '880e8400-e29b-41d4-a716-446655440005', 'lesson_002', 'bb0e8400-e29b-41d4-a716-446655440006', 'yes', NOW() - INTERVAL '2 days')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- GAME SESSIONS
-- ============================================================================
INSERT INTO game_sessions (id, student_id, game_type, score, content_ids, difficulty_level, completed_at, created_at) VALUES
-- Student 1 game sessions
('dd0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 'word_match_rush', 850, ARRAY['990e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440002'], 1, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
('dd0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440001', 'sentence_builder', 920, ARRAY['aa0e8400-e29b-41d4-a716-446655440001'], 1, NOW() - INTERVAL '12 hours', NOW() - INTERVAL '12 hours'),
('dd0e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440001', 'pronunciation_adventure', 780, ARRAY['990e8400-e29b-41d4-a716-446655440004', '990e8400-e29b-41d4-a716-446655440005'], 1, NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours'),

-- Student 2 game sessions
('dd0e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440002', 'word_match_rush', 650, ARRAY['990e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440002'], 1, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),
('dd0e8400-e29b-41d4-a716-446655440005', '880e8400-e29b-41d4-a716-446655440002', 'sentence_builder', 720, ARRAY['aa0e8400-e29b-41d4-a716-446655440001'], 1, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),

-- Student 3 game sessions
('dd0e8400-e29b-41d4-a716-446655440006', '880e8400-e29b-41d4-a716-446655440003', 'word_match_rush', 950, ARRAY['990e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440003'], 2, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
('dd0e8400-e29b-41d4-a716-446655440007', '880e8400-e29b-41d4-a716-446655440003', 'pronunciation_adventure', 880, ARRAY['990e8400-e29b-41d4-a716-446655440004', '990e8400-e29b-41d4-a716-446655440005'], 1, NOW() - INTERVAL '8 hours', NOW() - INTERVAL '8 hours'),

-- Student 5 game sessions (Class 2)
('dd0e8400-e29b-41d4-a716-446655440008', '880e8400-e29b-41d4-a716-446655440005', 'word_match_rush', 1000, ARRAY['990e8400-e29b-41d4-a716-446655440006', '990e8400-e29b-41d4-a716-446655440007'], 2, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days'),
('dd0e8400-e29b-41d4-a716-446655440009', '880e8400-e29b-41d4-a716-446655440005', 'sentence_builder', 980, ARRAY['aa0e8400-e29b-41d4-a716-446655440003'], 2, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),

-- Student 8 game sessions (Class 3 - advanced)
('dd0e8400-e29b-41d4-a716-446655440010', '880e8400-e29b-41d4-a716-446655440008', 'word_match_rush', 1100, ARRAY['990e8400-e29b-41d4-a716-446655440009', '990e8400-e29b-41d4-a716-446655440010'], 3, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
('dd0e8400-e29b-41d4-a716-446655440011', '880e8400-e29b-41d4-a716-446655440008', 'sentence_builder', 1050, ARRAY['aa0e8400-e29b-41d4-a716-446655440005'], 3, NOW() - INTERVAL '5 hours', NOW() - INTERVAL '5 hours')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- PAYMENTS
-- ============================================================================
INSERT INTO payments (id, school_id, amount, currency, payment_method, status, billing_period_start, billing_period_end, payment_date, notes, created_at) VALUES
-- Tokyo English Academy payments
('ee0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 50000.00, 'JPY', 'credit_card', 'paid', NOW() - INTERVAL '30 days', NOW(), NOW() - INTERVAL '30 days', 'Monthly subscription', NOW() - INTERVAL '30 days'),
('ee0e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 50000.00, 'JPY', 'credit_card', 'paid', NOW(), NOW() + INTERVAL '30 days', NOW(), 'Monthly subscription - current period', NOW()),

-- Osaka Kids English payments
('ee0e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440002', 30000.00, 'JPY', 'bank_account', 'paid', NOW() - INTERVAL '30 days', NOW(), NOW() - INTERVAL '30 days', 'Standard plan', NOW() - INTERVAL '30 days'),
('ee0e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', 30000.00, 'JPY', 'bank_account', 'pending', NOW(), NOW() + INTERVAL '30 days', NULL, 'Standard plan - pending payment', NOW()),

-- Yokohama Learning Center (trial)
('ee0e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440003', 0.00, 'JPY', 'credit_card', 'paid', NOW() - INTERVAL '7 days', NOW() + INTERVAL '23 days', NOW() - INTERVAL '7 days', 'Trial period - free', NOW() - INTERVAL '7 days')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- THEMES
-- ============================================================================
INSERT INTO themes (id, school_id, primary_color, secondary_color, accent_color, font_family, logo_url, app_icon_url, favicon_url, background_color, button_style, card_style, created_at) VALUES
-- Tokyo English Academy theme
('ff0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', '#2563EB', '#10B981', '#F59E0B', 'Inter, sans-serif', 'https://example.com/logos/tokyo-english.png', NULL, NULL, '#F9FAFB', '{"borderRadius": "8px", "padding": "12px 24px"}', '{"boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "borderRadius": "12px"}', NOW()),

-- Osaka Kids English theme
('ff0e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', '#7C3AED', '#EC4899', '#FBBF24', 'Roboto, sans-serif', 'https://example.com/logos/osaka-kids.png', NULL, NULL, '#FFF7ED', '{"borderRadius": "12px", "padding": "14px 28px"}', '{"boxShadow": "0 4px 6px rgba(0,0,0,0.1)", "borderRadius": "16px"}', NOW()),

-- Yokohama Learning Center theme (default)
('ff0e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', '#3B82F6', '#10B981', '#F59E0B', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- FEATURE FLAGS
-- ============================================================================
INSERT INTO feature_flags (id, school_id, feature_name, enabled, expiration_date, created_at) VALUES
-- Tokyo English Academy features
('110e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'custom_theming', true, NULL, NOW()),
('110e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'advanced_analytics', true, NULL, NOW()),
('110e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'bulk_import', true, NULL, NOW()),
('110e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'api_access', true, NULL, NOW()),

-- Osaka Kids English features
('110e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 'custom_theming', true, NULL, NOW()),
('110e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 'advanced_analytics', false, NULL, NOW()),
('110e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440002', 'bulk_import', true, NULL, NOW()),

-- Yokohama Learning Center features (trial - limited)
('110e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440003', 'custom_theming', false, NULL, NOW()),
('110e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440003', 'advanced_analytics', false, NULL, NOW()),
('110e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440003', 'bulk_import', false, NULL, NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- This seed file creates:
-- - 3 Schools (Tokyo, Osaka, Yokohama)
-- - 4 Teachers (with multi-school support)
-- - 5 Teacher-School relationships (Sarah Johnson works at 2 schools)
-- - 6 Classes
-- - 13 Students (with various registration statuses and progress)
-- - 12 Vocabulary items (class-level and student-specific)
-- - 6 Grammar rules
-- - 8 Survey questions
-- - 10 Survey responses
-- - 11 Game sessions
-- - 5 Payment records
-- - 3 Theme configurations
-- - 10 Feature flags

-- Note: Make sure your Supabase tables are created with the correct schema
-- before running this seed file. The tables should match the schema described
-- in the backend README.md file.

