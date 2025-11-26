from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase
from app.models import StudentProgress, GameSession, GameType
from app.auth import get_current_user

router = APIRouter()


@router.get("/{student_id}/progress")
async def get_student_progress(student_id: str):
    """Get student progress dashboard data"""
    # Get student data
    student = supabase.table("students").select("*").eq("id", student_id).single().execute()
    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Calculate progress from game sessions and surveys
    game_sessions = supabase.table("game_sessions").select("*").eq("student_id", student_id).execute()
    surveys = supabase.table("survey_responses").select("*").eq("student_id", student_id).execute()
    
    # Calculate vocabulary and grammar progress
    vocab_progress = 0.0
    grammar_progress = 0.0
    total_points = sum([g.get("score", 0) for g in game_sessions.data])
    
    # Get streak
    streak = student.data.get("streak_days", 0)
    
    # Get badges
    badges = student.data.get("badges", [])
    
    progress = StudentProgress(
        student_id=student_id,
        vocabulary_progress=vocab_progress,
        grammar_progress=grammar_progress,
        streak_days=streak,
        total_points=total_points,
        badges=badges
    )
    
    return progress


@router.get("/{student_id}/leaderboard")
async def get_student_leaderboard_position(student_id: str):
    """Get student's position in class leaderboard"""
    student = supabase.table("students").select("class_id").eq("id", student_id).single().execute()
    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    class_id = student.data["class_id"]
    
    # Get all students in class with their points
    students = supabase.table("students").select("id, name").eq("class_id", class_id).execute()
    
    # Calculate points for each student
    student_points = []
    for s in students.data:
        games = supabase.table("game_sessions").select("score").eq("student_id", s["id"]).execute()
        total_points = sum([g.get("score", 0) for g in games.data])
        student_points.append({"student_id": s["id"], "name": s["name"], "points": total_points})
    
    # Sort by points
    student_points.sort(key=lambda x: x["points"], reverse=True)
    
    # Find current student's position
    position = next((i + 1 for i, s in enumerate(student_points) if s["student_id"] == student_id), None)
    
    return {
        "position": position,
        "total_students": len(student_points),
        "categories": {
            "vocabulary": position,  # Simplified
            "grammar": position,
            "game_points": position
        }
    }


@router.post("/{student_id}/game-session")
async def create_game_session(student_id: str, session: GameSession):
    """Record a game session"""
    session_data = {
        "student_id": student_id,
        "game_type": session.game_type.value,
        "score": session.score,
        "content_ids": session.content_ids,
        "difficulty_level": session.difficulty_level
    }
    
    result = supabase.table("game_sessions").insert(session_data).execute()
    return {"session_id": result.data[0]["id"], "message": "Game session recorded"}

