from fastapi import APIRouter, HTTPException
from app.database import supabase, supabase_admin
from app.models import SurveyResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/questions/{class_id}")
async def get_survey_questions_for_class(class_id: str):
    """Get survey questions for a class"""
    questions = supabase.table("survey_questions").select("*").eq("class_id", class_id).execute()
    return {"questions": questions.data}


@router.post("/responses")
async def submit_survey_response(response: SurveyResponse):
    """Submit a survey response"""
    try:
        response_data = {
            "student_id": response.student_id,
            "lesson_id": response.lesson_id,
            "question_id": response.question_id,
            "response": response.response
        }
        
        # Use supabase_admin to bypass RLS policies for insert
        result = supabase_admin.table("survey_responses").insert(response_data).execute()
        
        if not result.data:
            logger.error(f"Failed to insert survey response: {response_data}")
            raise HTTPException(status_code=500, detail="Failed to submit survey response")
        
        logger.info(f"Survey response submitted: student_id={response.student_id}, question_id={response.question_id}")
        return {"response_id": result.data[0]["id"], "message": "Response submitted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting survey response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while submitting the survey response")


@router.get("/responses/{student_id}")
async def get_student_responses(student_id: str):
    """Get survey responses for a student"""
    responses = supabase.table("survey_responses").select("*").eq("student_id", student_id).execute()
    return {"responses": responses.data}

