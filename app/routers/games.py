from fastapi import APIRouter, HTTPException
from app.database import supabase_admin
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/available")
async def get_available_games():
    """Get list of available games"""
    return {
        "games": [
            {
                "id": "word_match_rush",
                "name": "Word Match Rush",
                "description": "Match English words to pictures or Japanese equivalents"
            },
            {
                "id": "sentence_builder",
                "name": "Sentence Builder Blocks",
                "description": "Drag-and-drop tiles to build sentences"
            },
            {
                "id": "pronunciation_adventure",
                "name": "Pronunciation Adventure",
                "description": "Speak words and get pronunciation feedback"
            }
        ]
    }


@router.get("/config/{student_id}")
async def get_game_config(student_id: str):
    """Get game configuration for a student"""
    try:
        # Get student info including class_id
        student_result = supabase_admin.table("students").select("id, class_id").eq("id", student_id).single().execute()
        
        if not student_result.data:
            raise HTTPException(status_code=404, detail="Student not found")
        
        class_id = student_result.data.get("class_id")
        
        # Get vocabulary: student-specific OR class-level OR available to all (class_id IS NULL)
        # Fetch both separately and combine (Supabase Python client doesn't support OR directly)
        vocab_student_result = supabase_admin.table("vocabulary").select("*").eq("student_id", student_id).execute()
        vocab_student = vocab_student_result.data or []
        
        vocab_class = []
        if class_id:
            vocab_class_result = supabase_admin.table("vocabulary").select("*").eq("class_id", class_id).execute()
            vocab_class = vocab_class_result.data or []
        
        # Get vocabulary available to all classes (class_id IS NULL and student_id IS NULL)
        vocab_all_result = supabase_admin.table("vocabulary").select("*").is_("class_id", None).is_("student_id", None).execute()
        vocab_all = vocab_all_result.data or []
        
        # Combine and deduplicate by id
        vocab_dict = {}
        for item in vocab_student:
            vocab_dict[item["id"]] = item
        for item in vocab_class:
            if item["id"] not in vocab_dict:
                vocab_dict[item["id"]] = item
        for item in vocab_all:
            if item["id"] not in vocab_dict:
                vocab_dict[item["id"]] = item
        vocab_data = list(vocab_dict.values())
        
        # Get grammar: student-specific OR class-level OR available to all (class_id IS NULL)
        grammar_student_result = supabase_admin.table("grammar").select("*").eq("student_id", student_id).execute()
        grammar_student = grammar_student_result.data or []
        
        grammar_class = []
        if class_id:
            grammar_class_result = supabase_admin.table("grammar").select("*").eq("class_id", class_id).execute()
            grammar_class = grammar_class_result.data or []
        
        # Get grammar available to all classes (class_id IS NULL and student_id IS NULL)
        grammar_all_result = supabase_admin.table("grammar").select("*").is_("class_id", None).is_("student_id", None).execute()
        grammar_all = grammar_all_result.data or []
        
        # Combine and deduplicate by id
        grammar_dict = {}
        for item in grammar_student:
            grammar_dict[item["id"]] = item
        for item in grammar_class:
            if item["id"] not in grammar_dict:
                grammar_dict[item["id"]] = item
        for item in grammar_all:
            if item["id"] not in grammar_dict:
                grammar_dict[item["id"]] = item
        grammar_data = list(grammar_dict.values())
        
        # Get survey responses for problem areas (optional)
        try:
            responses = supabase_admin.table("survey_responses").select("*").eq("student_id", student_id).execute()
            problem_areas = []  # Would be calculated from survey responses
        except Exception as e:
            logger.warning(f"Could not fetch survey responses: {str(e)}")
            problem_areas = []
        
        return {
            "vocabulary": vocab_data,
            "grammar": grammar_data,
            "problem_areas": problem_areas
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game config for student {student_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get game configuration")

