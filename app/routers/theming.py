from fastapi import APIRouter
from app.database import supabase

router = APIRouter()


@router.get("/{school_id}")
async def get_theme(school_id: str):
    """Get theme configuration"""
    theme = supabase.table("themes").select("*").eq("school_id", school_id).single().execute()
    if not theme.data:
        return {
            "school_id": school_id,
            "primary_color": "#3B82F6",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B"
        }
    return theme.data

