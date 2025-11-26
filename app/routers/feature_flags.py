from fastapi import APIRouter
from app.database import supabase

router = APIRouter()


@router.get("/{school_id}/{feature_name}")
async def check_feature(school_id: str, feature_name: str):
    """Check if a feature is enabled for a school"""
    feature = supabase.table("feature_flags").select("*").eq("school_id", school_id).eq("feature_name", feature_name).single().execute()
    if not feature.data:
        return {"enabled": False}
    return {"enabled": feature.data.get("enabled", False)}

