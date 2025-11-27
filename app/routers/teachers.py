from fastapi import APIRouter, Depends, HTTPException, Form
from app.database import supabase, supabase_admin
from app.models import SurveyQuestion, Vocabulary, Grammar
from app.auth import get_current_user
from typing import List, Optional

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
async def add_student(
    teacher_id: str,
    name: str = Form(...),
    class_id: str = Form(...),
    icon_sequence: Optional[str] = Form(None),
):
    """Add a new student to a class"""
    # Verify teacher owns the class
    class_check = supabase.table("classes").select("teacher_id").eq("id", class_id).single().execute()
    if not class_check.data or class_check.data["teacher_id"] != teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized for this class")
    
    student_data = {
        "name": name,
        "class_id": class_id,
        "registration_status": "pending",
    }

    # Optional icon sequence support (same format as school admin flow)
    if icon_sequence:
        try:
            icon_array = [int(x.strip()) for x in icon_sequence.split(",")]
            student_data["icon_sequence"] = icon_array
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid icon_sequence format. Use comma-separated integers.",
            )

    result = supabase.table("students").insert(student_data).execute()
    return {"student_id": result.data[0]["id"], "message": "Student added", "student": result.data[0]}


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
        # Convert empty strings to NULL for optional UUID columns
        "class_id": vocab.class_id or None,
        "student_id": vocab.student_id or None,
        "english_word": vocab.english_word,
        "japanese_word": vocab.japanese_word,
        "example_sentence": vocab.example_sentence,
        "audio_url": vocab.audio_url,
        "is_current_lesson": vocab.is_current_lesson,
        "scheduled_date": vocab.scheduled_date.isoformat() if vocab.scheduled_date else None
    }
    
    result = supabase_admin.table("vocabulary").insert(vocab_data).execute()
    return {"vocab_id": result.data[0]["id"], "message": "Vocabulary added"}


@router.post("/{teacher_id}/grammar")
async def add_grammar(teacher_id: str, grammar: Grammar):
    """Add grammar rule to class or student"""
    grammar_data = {
        "teacher_id": teacher_id,
        # Convert empty strings to NULL for optional UUID columns
        "class_id": grammar.class_id or None,
        "student_id": grammar.student_id or None,
        "rule_name": grammar.rule_name,
        "rule_description": grammar.rule_description,
        "examples": grammar.examples,
        "is_current_lesson": grammar.is_current_lesson,
        "scheduled_date": grammar.scheduled_date.isoformat() if grammar.scheduled_date else None
    }
    
    result = supabase_admin.table("grammar").insert(grammar_data).execute()
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


@router.get("/{teacher_id}/schools")
async def get_teacher_schools(teacher_id: str):
    """Get all schools a teacher is associated with, including pending invitations"""
    from datetime import datetime
    
    # Get all teacher_schools relationships for this teacher
    teacher_schools = supabase_admin.table("teacher_schools").select("*").eq("teacher_id", teacher_id).execute()
    
    if not teacher_schools.data:
        return {"schools": [], "pending_invitations": []}
    
    # Get all school IDs
    school_ids = [ts["school_id"] for ts in teacher_schools.data]
    
    # Get school details
    schools_data = supabase_admin.table("schools").select("*").in_("id", school_ids).execute()
    
    # Create a map of school_id -> school data
    schools_map = {s["id"]: s for s in schools_data.data}
    
    schools_list = []
    pending_invitations = []
    
    for ts in teacher_schools.data:
        school_id = ts["school_id"]
        school = schools_map.get(school_id)
        
        # Skip if school record doesn't exist
        if not school:
            continue
        
        invitation_status = ts.get("invitation_status", "pending")
        invitation_expires_at = ts.get("invitation_expires_at")
        
        school_info = {
            "school_id": school.get("id"),
            "school_name": school.get("name"),
            "invitation_status": invitation_status,
            "invitation_token": ts.get("invitation_token"),
            "invitation_expires_at": invitation_expires_at,
            "invitation_sent_at": ts.get("invitation_sent_at")
        }
        
        # Check if invitation is expired
        is_expired = False
        if invitation_expires_at and invitation_status == "pending":
            try:
                expires_at = datetime.fromisoformat(invitation_expires_at.replace("Z", "+00:00"))
                if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                    is_expired = True
                    school_info["invitation_status"] = "expired"
            except:
                pass
        
        if invitation_status == "accepted":
            schools_list.append(school_info)
        elif invitation_status == "pending" and not is_expired:
            pending_invitations.append(school_info)
        elif is_expired or invitation_status == "expired":
            school_info["invitation_status"] = "expired"
            pending_invitations.append(school_info)
    
    return {
        "schools": schools_list,
        "pending_invitations": pending_invitations
    }


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


@router.get("/{teacher_id}/classes")
async def get_teacher_classes(teacher_id: str):
    """Get all classes for a teacher"""
    classes = supabase.table("classes").select("*").eq("teacher_id", teacher_id).execute()
    return {"classes": classes.data}


@router.post("/{teacher_id}/classes")
async def add_teacher_class(teacher_id: str, name: str = Form(...)):
    """Add a new class for this teacher"""
    # Look up teacher's school_id from teacher_schools (get first school they're associated with)
    # Note: For multi-school support, we may need to pass school_id as a parameter
    teacher_school = supabase_admin.table("teacher_schools").select("school_id").eq("teacher_id", teacher_id).limit(1).single().execute()
    if not teacher_school.data:
        raise HTTPException(status_code=404, detail="Teacher not found or not associated with any school")

    class_data = {
        "name": name,
        "teacher_id": teacher_id,
        "school_id": teacher_school.data["school_id"],
    }
    result = supabase_admin.table("classes").insert(class_data).execute()
    return {"class_id": result.data[0]["id"], "class": result.data[0]}


@router.put("/{teacher_id}/classes/{class_id}")
async def update_teacher_class(teacher_id: str, class_id: str, name: Optional[str] = Form(None)):
    """Update an existing class for this teacher"""
    class_check = supabase_admin.table("classes").select("teacher_id").eq("id", class_id).single().execute()
    if not class_check.data or class_check.data["teacher_id"] != teacher_id:
        raise HTTPException(status_code=404, detail="Class not found")

    update_data = {}
    if name is not None:
        update_data["name"] = name

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase_admin.table("classes").update(update_data).eq("id", class_id).execute()
    return {"message": "Class updated", "class": result.data[0]}


@router.delete("/{teacher_id}/classes/{class_id}")
async def delete_teacher_class(teacher_id: str, class_id: str):
    """Delete a class owned by this teacher"""
    class_check = supabase_admin.table("classes").select("teacher_id").eq("id", class_id).single().execute()
    if not class_check.data or class_check.data["teacher_id"] != teacher_id:
        raise HTTPException(status_code=404, detail="Class not found")

    supabase_admin.table("classes").delete().eq("id", class_id).execute()
    return {"message": "Class deleted"}


