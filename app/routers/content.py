from fastapi import APIRouter
from app.database import supabase

router = APIRouter()


@router.get("/vocabulary/{student_id}")
async def get_student_vocabulary(student_id: str):
    """Get vocabulary for a student"""
    vocab = supabase.table("vocabulary").select("*").eq("student_id", student_id).execute()
    return {"vocabulary": vocab.data}


@router.get("/grammar/{student_id}")
async def get_student_grammar(student_id: str):
    """Get grammar for a student"""
    grammar = supabase.table("grammar").select("*").eq("student_id", student_id).execute()
    return {"grammar": grammar.data}

