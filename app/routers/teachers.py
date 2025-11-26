from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase
from app.models import SurveyQuestion, Vocabulary, Grammar
from app.auth import get_current_user
from typing import List

router = APIRouter()


@router.get("/{teacher_id}/students")
async def get_teacher_students(teacher_id: str):
    """Get all students for a teacher"""
    # Get teacher's classes
    classes = supabase.table("classes").select("id").eq("teacher_id", teacher_id).execute()
    class_ids = [c["id"] for c in classes.data]
    
    # Get students from those classes
    students = supabase.table("students").select("*").in_("class_id", class_ids).execute()
    return {"students": students.data}


@router.post("/{teacher_id}/students")
async def add_student(teacher_id: str, name: str, class_id: str):
    """Add a new student to a class"""
    # Verify teacher owns the class
    class_check = supabase.table("classes").select("teacher_id").eq("id", class_id).single().execute()
    if not class_check.data or class_check.data["teacher_id"] != teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized for this class")
    
    student_data = {
        "name": name,
        "class_id": class_id,
        "registration_status": "pending"
    }
    
    result = supabase.table("students").insert(student_data).execute()
    return {"student_id": result.data[0]["id"], "message": "Student added"}


@router.put("/students/{student_id}")
async def update_student(student_id: str, name: str = None, class_id: str = None):
    """Update student information"""
    update_data = {}
    if name:
        update_data["name"] = name
    if class_id:
        update_data["class_id"] = class_id
    
    supabase.table("students").update(update_data).eq("id", student_id).execute()
    return {"message": "Student updated"}


@router.delete("/students/{student_id}")
async def delete_student(student_id: str):
    """Remove student from class"""
    supabase.table("students").delete().eq("id", student_id).execute()
    return {"message": "Student removed"}


@router.post("/{teacher_id}/reset-auth/{student_id}")
async def reset_student_auth(teacher_id: str, student_id: str):
    """Reset student authentication"""
    # Verify teacher has access to this student
    student = supabase.table("students").select("class_id").eq("id", student_id).single().execute()
    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    class_check = supabase.table("classes").select("teacher_id").eq("id", student.data["class_id"]).single().execute()
    if class_check.data["teacher_id"] != teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Clear icon sequence to force re-registration
    supabase.table("students").update({"icon_sequence": None, "registration_status": "pending"}).eq("id", student_id).execute()
    return {"message": "Student authentication reset"}


@router.post("/{teacher_id}/vocabulary")
async def add_vocabulary(teacher_id: str, vocab: Vocabulary):
    """Add vocabulary to class or student"""
    vocab_data = {
        "teacher_id": teacher_id,
        "class_id": vocab.class_id,
        "student_id": vocab.student_id,
        "english_word": vocab.english_word,
        "japanese_word": vocab.japanese_word,
        "example_sentence": vocab.example_sentence,
        "audio_url": vocab.audio_url,
        "is_current_lesson": vocab.is_current_lesson,
        "scheduled_date": vocab.scheduled_date.isoformat() if vocab.scheduled_date else None
    }
    
    result = supabase.table("vocabulary").insert(vocab_data).execute()
    return {"vocab_id": result.data[0]["id"], "message": "Vocabulary added"}


@router.post("/{teacher_id}/grammar")
async def add_grammar(teacher_id: str, grammar: Grammar):
    """Add grammar rule to class or student"""
    grammar_data = {
        "teacher_id": teacher_id,
        "class_id": grammar.class_id,
        "student_id": grammar.student_id,
        "rule_name": grammar.rule_name,
        "rule_description": grammar.rule_description,
        "examples": grammar.examples,
        "is_current_lesson": grammar.is_current_lesson,
        "scheduled_date": grammar.scheduled_date.isoformat() if grammar.scheduled_date else None
    }
    
    result = supabase.table("grammar").insert(grammar_data).execute()
    return {"grammar_id": result.data[0]["id"], "message": "Grammar added"}


@router.get("/{teacher_id}/vocabulary")
async def get_vocabulary(teacher_id: str, class_id: str = None):
    """Get vocabulary for teacher"""
    query = supabase.table("vocabulary").select("*").eq("teacher_id", teacher_id)
    if class_id:
        query = query.eq("class_id", class_id)
    
    result = query.execute()
    return {"vocabulary": result.data}


@router.get("/{teacher_id}/grammar")
async def get_grammar(teacher_id: str, class_id: str = None):
    """Get grammar for teacher"""
    query = supabase.table("grammar").select("*").eq("teacher_id", teacher_id)
    if class_id:
        query = query.eq("class_id", class_id)
    
    result = query.execute()
    return {"grammar": result.data}


@router.post("/{teacher_id}/survey-questions")
async def create_survey_question(teacher_id: str, question: SurveyQuestion):
    """Create a survey question"""
    question_data = {
        "teacher_id": teacher_id,
        "class_id": question.class_id,
        "question_type": question.question_type.value,
        "question_text": question.question_text,
        "question_text_jp": question.question_text_jp,
        "options": question.options
    }
    
    result = supabase.table("survey_questions").insert(question_data).execute()
    return {"question_id": result.data[0]["id"], "message": "Question created"}


@router.get("/{teacher_id}/survey-questions")
async def get_survey_questions(teacher_id: str, class_id: str = None):
    """Get survey questions for teacher"""
    query = supabase.table("survey_questions").select("*").eq("teacher_id", teacher_id)
    if class_id:
        query = query.eq("class_id", class_id)
    
    result = query.execute()
    return {"questions": result.data}


@router.get("/{teacher_id}/dashboard")
async def get_teacher_dashboard(teacher_id: str):
    """Get teacher dashboard metrics"""
    # Get classes
    classes = supabase.table("classes").select("id, name").eq("teacher_id", teacher_id).execute()
    
    # Get students
    class_ids = [c["id"] for c in classes.data]
    students = supabase.table("students").select("id").in_("class_id", class_ids).execute()
    student_ids = [s["id"] for s in students.data]
    
    # Get survey responses
    surveys = supabase.table("survey_responses").select("*").in_("student_id", student_ids).execute()
    
    # Get game sessions
    games = supabase.table("game_sessions").select("*").in_("student_id", student_ids).execute()
    
    # Calculate metrics
    survey_completion_rate = len(surveys.data) / max(len(students.data), 1) * 100 if students.data else 0
    
    return {
        "class_metrics": {
            "total_classes": len(classes.data),
            "total_students": len(students.data),
            "survey_completion_rate": survey_completion_rate,
            "average_game_score": sum([g.get("score", 0) for g in games.data]) / max(len(games.data), 1) if games.data else 0
        },
        "student_metrics": students.data,
        "survey_responses": surveys.data,
        "game_sessions": games.data
    }

