from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from app.database import supabase, supabase_admin
from app.models import StudentProgress, GameSession, GameType
from app.auth import get_current_user
from app.config import settings
import httpx
import asyncio
import logging
from difflib import SequenceMatcher

router = APIRouter()
logger = logging.getLogger(__name__)


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
    
    # Include student name in response
    progress_dict = progress.dict()
    progress_dict["student_name"] = student.data.get("name", "")
    
    return progress_dict


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
async def create_game_session(student_id: str, session: dict = Body(...)):
    """
    Record a game session.

    Uses a plain dict instead of Pydantic model to be more forgiving about
    the payload coming from the frontend games.
    """
    try:
        game_type_raw = session.get("game_type")
        try:
            game_type = GameType(game_type_raw).value
        except Exception:
            logger.error(f"Invalid game_type received: {game_type_raw}")
            raise HTTPException(status_code=422, detail="Invalid game_type for game session")

        score = int(session.get("score", 0))
        content_ids = session.get("content_ids") or []
        difficulty_level = int(session.get("difficulty_level", 1))

        if not isinstance(content_ids, list):
            content_ids = [content_ids]

        session_data = {
            "student_id": student_id,
            "game_type": game_type,
            "score": score,
            "content_ids": content_ids,
            "difficulty_level": difficulty_level,
        }

        # Use admin client to bypass RLS when recording sessions
        result = supabase_admin.table("game_sessions").insert(session_data).execute()
        return {"session_id": result.data[0]["id"], "message": "Game session recorded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording game session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record game session")


@router.post("/{student_id}/pronunciation-eval")
async def evaluate_pronunciation(
    student_id: str,
    audio: UploadFile = File(...),
    reference_text: str = Form(...),
):
    """
    Evaluate a student's pronunciation using AssemblyAI.

    - Accepts an audio file (short recording) and the target English text.
    - Uploads audio to AssemblyAI, gets a transcript, and compares it to the reference.
    - Returns a simple 0–100 similarity score plus raw transcript for debugging.
    """
    api_key = (
        getattr(settings, "assemblyai_api_key", None)
        or settings.__dict__.get("ASSEMBLYAI_API_KEY")
    )

    if not api_key:
        logger.error("ASSEMBLYAI_API_KEY is not configured")
        raise HTTPException(
            status_code=500,
            detail="Pronunciation service is not configured on the server.",
        )

    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        headers = {"authorization": api_key}

        async with httpx.AsyncClient(timeout=60) as client:
            # 1) Upload audio
            upload_resp = await client.post(
                "https://api.assemblyai.com/v2/upload", content=audio_bytes, headers=headers
            )
            upload_resp.raise_for_status()
            upload_url = upload_resp.json().get("upload_url")

            if not upload_url:
                logger.error("AssemblyAI upload failed: no upload_url in response")
                raise HTTPException(
                    status_code=502, detail="Failed to upload audio for pronunciation check."
                )

            # 2) Request transcription
            transcript_req = {
                "audio_url": upload_url,
                "language_code": "en_us",
                # Bias recognition toward the expected phrase
                "word_boost": [reference_text],
                "boost_param": "high",
            }

            transcribe_resp = await client.post(
                "https://api.assemblyai.com/v2/transcript",
                json=transcript_req,
                headers=headers,
            )
            transcribe_resp.raise_for_status()
            transcript_id = transcribe_resp.json().get("id")

            if not transcript_id:
                logger.error("AssemblyAI transcription creation failed: no id in response")
                raise HTTPException(
                    status_code=502, detail="Failed to start pronunciation analysis."
                )

            # 3) Poll for completion
            status = "queued"
            transcript_text = ""
            for _ in range(20):  # up to ~20 seconds
                poll_resp = await client.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers=headers,
                )
                poll_resp.raise_for_status()
                data = poll_resp.json()
                status = data.get("status")

                if status == "completed":
                    transcript_text = (data.get("text") or "").strip()
                    break
                if status in {"error", "failed"}:
                    logger.error(f"AssemblyAI transcription error: {data}")
                    raise HTTPException(
                        status_code=502,
                        detail="Pronunciation service reported an error while processing audio.",
                    )

                await asyncio.sleep(1)

            if status != "completed":
                logger.error(f"AssemblyAI transcription timeout, last status={status}")
                raise HTTPException(
                    status_code=504,
                    detail="Pronunciation service took too long to respond.",
                )

            # 4) Simple similarity scoring between transcript and reference
            ref = reference_text.lower().strip()
            hyp = transcript_text.lower().strip()
            similarity = SequenceMatcher(None, ref, hyp).ratio()
            score = round(similarity * 100, 2)

            return {
                "student_id": student_id,
                "reference_text": reference_text,
                "transcript": transcript_text,
                "similarity_score": score,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during pronunciation evaluation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to evaluate pronunciation. Please try again later.",
        )

