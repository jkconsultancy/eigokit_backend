from fastapi import APIRouter
from app.database import supabase

router = APIRouter()


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
    # Get student's problem areas from surveys
    responses = supabase.table("survey_responses").select("*").eq("student_id", student_id).execute()
    
    # Get vocabulary and grammar for student
    vocab = supabase.table("vocabulary").select("*").eq("student_id", student_id).execute()
    grammar = supabase.table("grammar").select("*").eq("student_id", student_id).execute()
    
    return {
        "vocabulary": vocab.data,
        "grammar": grammar.data,
        "problem_areas": []  # Would be calculated from survey responses
    }

