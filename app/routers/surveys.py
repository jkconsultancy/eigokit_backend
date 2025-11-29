from fastapi import APIRouter, HTTPException
from app.database import supabase, supabase_admin
from app.models import SurveyResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/questions/{class_id}")
async def get_survey_questions_for_class(class_id: str):
    """Get survey questions for a class (includes class-specific and global surveys)"""
    # Get class-specific questions
    class_questions_result = supabase_admin.table("survey_questions").select("*").eq("class_id", class_id).execute()
    class_questions = class_questions_result.data or []
    
    # Get global questions (class_id IS NULL - available to all classes)
    global_questions_result = supabase_admin.table("survey_questions").select("*").is_("class_id", None).execute()
    global_questions = global_questions_result.data or []
    
    # Combine and deduplicate by id
    questions_dict = {}
    for q in class_questions:
        questions_dict[q["id"]] = q
    for q in global_questions:
        if q["id"] not in questions_dict:
            questions_dict[q["id"]] = q
    
    return {"questions": list(questions_dict.values())}


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


@router.get("/open/{student_id}")
async def get_open_surveys(student_id: str):
    """Get count of open (uncompleted) surveys for a student"""
    try:
        # Get student's class_id
        student_result = supabase_admin.table("students").select("class_id").eq("id", student_id).single().execute()
        
        if not student_result.data:
            raise HTTPException(status_code=404, detail="Student not found")
        
        class_id = student_result.data.get("class_id")
        
        # Get all survey questions for the student's class
        class_question_ids = []
        if class_id:
            class_questions_result = supabase_admin.table("survey_questions").select("id").eq("class_id", class_id).execute()
            class_question_ids = [q["id"] for q in (class_questions_result.data or [])]
        
        # Get global survey questions (class_id IS NULL - available to all classes)
        global_questions_result = supabase_admin.table("survey_questions").select("id").is_("class_id", None).execute()
        global_question_ids = [q["id"] for q in (global_questions_result.data or [])]
        
        # Combine and deduplicate
        all_question_ids = list(set(class_question_ids + global_question_ids))
        
        if not all_question_ids:
            return {"count": 0, "has_open_surveys": False}
        
        # Get all survey responses for this student
        responses_result = supabase_admin.table("survey_responses").select("question_id").eq("student_id", student_id).execute()
        answered_question_ids = set([r["question_id"] for r in (responses_result.data or [])])
        
        # Find questions that haven't been answered
        open_question_ids = [qid for qid in all_question_ids if qid not in answered_question_ids]
        
        return {
            "count": len(open_question_ids),
            "has_open_surveys": len(open_question_ids) > 0,
            "open_question_ids": open_question_ids
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting open surveys for student {student_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get open surveys")

