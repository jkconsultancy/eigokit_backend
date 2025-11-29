from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    SCHOOL_ADMIN = "school_admin"
    PLATFORM_ADMIN = "platform_admin"


class StudentRegistration(BaseModel):
    name: str
    icon_sequence: List[int]  # 5 icon IDs in order
    class_id: str


class StudentSignIn(BaseModel):
    icon_sequence: List[int]  # 5 icon IDs in order


class SurveyQuestionType(str, Enum):
    EMOJI_SCALE = "emoji_scale"
    MULTIPLE_CHOICE = "multiple_choice"
    YES_NO = "yes_no"
    SHORT_ANSWER = "short_answer"
    AUDIO = "audio"


class SurveyQuestion(BaseModel):
    id: Optional[str] = None
    teacher_id: Optional[str] = None  # Optional because it comes from URL path in some endpoints
    class_id: Optional[str] = None
    question_type: SurveyQuestionType
    question_text: str
    question_text_jp: Optional[str] = None
    options: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class SurveyResponse(BaseModel):
    id: Optional[str] = None
    student_id: str
    lesson_id: str
    question_id: str
    response: Any  # Can be string, number, or dict
    created_at: Optional[datetime] = None


class Vocabulary(BaseModel):
    id: Optional[str] = None
    teacher_id: Optional[str] = None
    class_id: Optional[str] = None
    student_id: Optional[str] = None
    english_word: str
    japanese_word: str
    example_sentence: Optional[str] = None
    audio_url: Optional[str] = None
    is_current_lesson: bool = False
    scheduled_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


class Grammar(BaseModel):
    id: Optional[str] = None
    teacher_id: Optional[str] = None
    class_id: Optional[str] = None
    student_id: Optional[str] = None
    rule_name: str
    rule_description: str
    examples: List[str]
    is_current_lesson: bool = False
    scheduled_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


class GameType(str, Enum):
    WORD_MATCH_RUSH = "word_match_rush"
    SENTENCE_BUILDER = "sentence_builder"
    PRONUNCIATION_ADVENTURE = "pronunciation_adventure"


class GameSession(BaseModel):
    id: Optional[str] = None
    student_id: str
    game_type: GameType
    score: int
    content_ids: List[str]  # vocab/grammar IDs used
    difficulty_level: int
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class StudentProgress(BaseModel):
    student_id: str
    vocabulary_progress: float
    grammar_progress: float
    streak_days: int
    total_points: int
    badges: List[str]


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    OVERDUE = "overdue"
    REFUNDED = "refunded"


class Payment(BaseModel):
    id: Optional[str] = None
    school_id: str
    amount: float
    currency: str = "JPY"
    payment_method: PaymentMethod
    status: PaymentStatus
    billing_period_start: datetime
    billing_period_end: datetime
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class ThemeConfig(BaseModel):
    school_id: str
    primary_color: str
    secondary_color: str
    accent_color: str
    font_family: Optional[str] = None
    logo_url: Optional[str] = None
    app_icon_url: Optional[str] = None
    favicon_url: Optional[str] = None
    background_color: Optional[str] = None
    button_style: Optional[Dict[str, Any]] = None
    card_style: Optional[Dict[str, Any]] = None


class FeatureFlag(BaseModel):
    school_id: str
    feature_name: str
    enabled: bool
    expiration_date: Optional[datetime] = None

