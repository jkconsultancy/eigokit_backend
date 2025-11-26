from fastapi import APIRouter
from app.database import supabase

router = APIRouter()


@router.get("/{school_id}")
async def get_theme(school_id: str):
    """Get theme configuration for a school.

    If the school_id is a placeholder (e.g. 'default') or invalid for the
    UUID column in the database, return a safe default theme instead of
    letting the database raise a 22P02 error.
    """

    # Handle placeholder / non-UUID IDs gracefully
    # Some frontend code uses 'default' when there is no real school_id yet.
    if school_id == "default":
        return {
            "school_id": school_id,
            "primary_color": "#3B82F6",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B",
        }

    try:
        theme = (
            supabase.table("themes")
            .select("*")
            .eq("school_id", school_id)
            .single()
            .execute()
        )
    except Exception:
        # If Supabase/Postgres rejects the ID (e.g. invalid UUID syntax),
        # fall back to a default theme instead of crashing the request.
        return {
            "school_id": school_id,
            "primary_color": "#3B82F6",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B",
        }

    if not theme.data:
        return {
            "school_id": school_id,
            "primary_color": "#3B82F6",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B",
        }

    return theme.data

