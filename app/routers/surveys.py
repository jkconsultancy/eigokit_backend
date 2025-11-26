from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.models import SurveyResponse

router = APIRouter()


@router.get("/questions/{class_id}")
async def get_survey_questions_for_class(class_id: str):
    """Get survey questions for a class"""
    questions = supabase.table("survey_questions").select("*").eq("class_id", class_id).execute()
    return {"questions": questions.data}


@router.post("/responses")
async def submit_survey_response(response: SurveyResponse):
    """Submit a survey response"""
    response_data = {
        "student_id": response.student_id,
        "lesson_id": response.lesson_id,
        "question_id": response.question_id,
        "response": response.response
    }
    
    result = supabase.table("survey_responses").insert(response_data).execute()
    return {"response_id": result.data[0]["id"], "message": "Response submitted"}


@router.get("/responses/{student_id}")
async def get_student_responses(student_id: str):
    """Get survey responses for a student"""
    responses = supabase.table("survey_responses").select("*").eq("student_id", student_id).execute()
    return {"responses": responses.data}

