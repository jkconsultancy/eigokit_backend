from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase, supabase_admin
from app.models import Payment, FeatureFlag, UserRole
from app.auth import get_current_user, require_role
from typing import List, Optional

router = APIRouter()


@router.get("/schools")
async def get_all_schools(user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Get all schools with key metrics"""
    # Use admin client to bypass RLS for reads (we've already verified user is platform admin)
    schools = supabase_admin.table("schools").select("*").execute()
    
    # Get metrics for each school
    for school in schools.data:
        # Get counts
        teachers = supabase_admin.table("teacher_schools").select("teacher_id").eq("school_id", school["id"]).execute()
        classes = supabase_admin.table("classes").select("id").eq("school_id", school["id"]).execute()
        class_ids = [c["id"] for c in classes.data]
        students = supabase_admin.table("students").select("id").in_("class_id", class_ids).execute()
        
        school["teacher_count"] = len(teachers.data)
        school["student_count"] = len(students.data)
        school["class_count"] = len(classes.data)
    
    return {"schools": schools.data}


@router.post("/schools")
async def create_school(name: str, contact_info: Optional[str] = None, account_status: str = "trial", subscription_tier: str = "basic", user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Create a new school"""
    school_data = {
        "name": name,
        "contact_info": contact_info,
        "account_status": account_status,
        "subscription_tier": subscription_tier
    }
    
    # Use admin client to bypass RLS (we've already verified user is platform admin)
    result = supabase_admin.table("schools").insert(school_data).execute()
    return {"school_id": result.data[0]["id"], "message": "School created successfully", "school": result.data[0]}


@router.get("/schools/{school_id}")
async def get_school_details(school_id: str, user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Get detailed information about a school"""
    school = supabase_admin.table("schools").select("*").eq("id", school_id).single().execute()
    if not school.data:
        raise HTTPException(status_code=404, detail="School not found")
    
    # Get related data
    # Join through teacher_schools to get teachers for this school
    teacher_schools = supabase_admin.table("teacher_schools").select("*, teachers(*)").eq("school_id", school_id).execute()
    teachers = [ts.get("teachers", {}) for ts in teacher_schools.data]
    classes = supabase_admin.table("classes").select("*").eq("school_id", school_id).execute()
    payments = supabase_admin.table("payments").select("*").eq("school_id", school_id).execute()
    
    return {
        "school": school.data,
        "teachers": teachers.data,
        "classes": classes.data,
        "payments": payments.data
    }


@router.put("/schools/{school_id}/status")
async def update_school_status(school_id: str, status: str, user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Update school account status"""
    allowed_statuses = ["active", "suspended", "trial"]
    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {allowed_statuses}")
    
    # Use admin client to bypass RLS
    supabase_admin.table("schools").update({"account_status": status}).eq("id", school_id).execute()
    return {"message": f"School status updated to {status}"}


@router.get("/payments")
async def get_all_payments(status: Optional[str] = None, user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Get all payments across schools"""
    query = supabase_admin.table("payments").select("*")
    if status:
        query = query.eq("status", status)
    
    payments = query.order("created_at", desc=True).execute()
    return {"payments": payments.data}


@router.post("/payments/{payment_id}/adjust")
async def adjust_payment(payment_id: str, adjustment_amount: float, notes: str, user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Adjust payment amount"""
    payment = supabase_admin.table("payments").select("*").eq("id", payment_id).single().execute()
    if not payment.data:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    new_amount = payment.data["amount"] + adjustment_amount
    supabase_admin.table("payments").update({
        "amount": new_amount,
        "notes": f"{payment.data.get('notes', '')}\nAdjustment: {notes}"
    }).eq("id", payment_id).execute()
    
    return {"message": "Payment adjusted", "new_amount": new_amount}


@router.post("/payments/{payment_id}/refund")
async def refund_payment(payment_id: str, refund_amount: Optional[float] = None, user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Issue a refund for a payment"""
    payment = supabase_admin.table("payments").select("*").eq("id", payment_id).single().execute()
    if not payment.data:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    refund_amt = refund_amount or payment.data["amount"]
    
    # Create refund record
    supabase_admin.table("payments").insert({
        "school_id": payment.data["school_id"],
        "amount": -refund_amt,
        "currency": payment.data["currency"],
        "payment_method": payment.data["payment_method"],
        "status": "refunded",
        "notes": f"Refund for payment {payment_id}"
    }).execute()
    
    return {"message": "Refund processed", "refund_amount": refund_amt}


@router.get("/features/{school_id}")
async def get_school_features(school_id: str, user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Get feature flags for a school"""
    features = supabase_admin.table("feature_flags").select("*").eq("school_id", school_id).execute()
    return {"features": features.data}


@router.post("/features/{school_id}")
async def set_feature_flag(school_id: str, feature: FeatureFlag, user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Set a feature flag for a school"""
    feature_data = {
        "school_id": school_id,
        "feature_name": feature.feature_name,
        "enabled": feature.enabled,
        "expiration_date": feature.expiration_date.isoformat() if feature.expiration_date else None
    }
    
    # Check if exists
    existing = supabase_admin.table("feature_flags").select("id").eq("school_id", school_id).eq("feature_name", feature.feature_name).execute()
    if existing.data:
        supabase_admin.table("feature_flags").update(feature_data).eq("id", existing.data[0]["id"]).execute()
        return {"message": "Feature flag updated"}
    else:
        result = supabase_admin.table("feature_flags").insert(feature_data).execute()
        return {"message": "Feature flag created", "feature_id": result.data[0]["id"]}


@router.get("/dashboard")
async def get_platform_dashboard(user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    """Get platform-wide dashboard metrics"""
    # Get all schools
    schools = supabase_admin.table("schools").select("id, account_status").execute()
    
    # Count by status
    active = len([s for s in schools.data if s.get("account_status") == "active"])
    trial = len([s for s in schools.data if s.get("account_status") == "trial"])
    suspended = len([s for s in schools.data if s.get("account_status") == "suspended"])
    
    # Get total students
    all_classes = supabase_admin.table("classes").select("id").execute()
    class_ids = [c["id"] for c in all_classes.data]
    all_students = supabase_admin.table("students").select("id").in_("class_id", class_ids).execute()
    
    # Get revenue
    payments = supabase_admin.table("payments").select("amount, status").eq("status", "paid").execute()
    total_revenue = sum([p.get("amount", 0) for p in payments.data])
    
    return {
        "platform_level": {
            "total_schools": len(schools.data),
            "active_schools": active,
            "trial_schools": trial,
            "suspended_schools": suspended,
            "total_students": len(all_students.data),
            "total_revenue": total_revenue
        }
    }

