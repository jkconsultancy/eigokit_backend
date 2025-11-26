from fastapi import APIRouter, HTTPException, Depends, Form
from app.database import supabase, supabase_admin
from app.models import StudentRegistration, StudentSignIn
from app.auth import get_current_user
from typing import Optional

router = APIRouter()


@router.post("/student/register")
async def register_student(registration: StudentRegistration):
    """Register a new student with icon-based authentication"""
    # Verify student exists in class
    class_check = supabase.table("classes").select("id, teacher_id").eq("id", registration.class_id).single().execute()
    if not class_check.data:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if student already exists
    existing = supabase.table("students").select("id").eq("name", registration.name).eq("class_id", registration.class_id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Student already registered")
    
    # Create student record
    student_data = {
        "name": registration.name,
        "class_id": registration.class_id,
        "icon_sequence": registration.icon_sequence,
        "registration_status": "registered"
    }
    
    result = supabase.table("students").insert(student_data).execute()
    return {"student_id": result.data[0]["id"], "message": "Registration successful"}


@router.post("/student/signin")
async def signin_student(signin: StudentSignIn):
    """Student sign-in with icon-based authentication"""
    # Find student by name
    students = supabase.table("students").select("id, icon_sequence, class_id").eq("name", signin.name).execute()
    
    if not students.data:
        raise HTTPException(status_code=401, detail="Student not found")
    
    # Check icon sequence
    for student in students.data:
        if student["icon_sequence"] == signin.icon_sequence:
            # Generate session token (simplified - in production use proper JWT)
            # For now, return student ID
            return {
                "student_id": student["id"],
                "class_id": student["class_id"],
                "message": "Sign-in successful"
            }
    
    raise HTTPException(status_code=401, detail="Invalid icon sequence")


@router.post("/teacher/signin")
async def signin_teacher(email: str, password: str):
    """Teacher sign-in with email/password"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return {
            "access_token": response.session.access_token,
            "user": response.user
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/teacher/signup")
async def signup_teacher(email: str, password: str, name: str, school_id: str):
    """Teacher sign-up"""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        # Create user record with role
        supabase.table("users").insert({
            "id": response.user.id,
            "email": email,
            "role": "teacher",
            "school_id": school_id
        }).execute()
        
        # Create teacher record
        supabase.table("teachers").insert({
            "id": response.user.id,
            "name": name,
            "school_id": school_id,
            "email": email
        }).execute()
        
        return {"message": "Teacher registered successfully", "user_id": response.user.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/platform-admin/signin")
async def signin_platform_admin(email: str, password: str):
    """Platform admin sign-in"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Verify user is platform admin
        user_data = supabase.table("users").select("role").eq("id", response.user.id).single().execute()
        if not user_data.data or user_data.data.get("role") != "platform_admin":
            raise HTTPException(status_code=403, detail="Access denied. Platform admin role required.")
        
        return {
            "access_token": response.session.access_token,
            "user": response.user
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/school-admin/signup")
async def signup_school_admin(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    school_name: str = Form(...),
    contact_info: Optional[str] = Form(None)
):
    """School admin sign-up - creates both school and admin user"""
    try:
        # Create auth user
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Create school record (use admin client to bypass RLS)
        from app.database import supabase_admin
        school_data = {
            "name": school_name,
            "contact_info": contact_info,
            "account_status": "trial",
            "subscription_tier": "basic"
        }
        school_result = supabase_admin.table("schools").insert(school_data).execute()
        school_id = school_result.data[0]["id"]
        
        # Create user record with role
        supabase_admin.table("users").insert({
            "id": response.user.id,
            "email": email,
            "role": "school_admin",
            "school_id": school_id
        }).execute()
        
        # Create school_admin record (if this table exists)
        # For now, we'll just use the users table with role
        
        # Check if email confirmation is required
        email_confirmed = response.user.email_confirmed_at is not None
        has_session = response.session is not None
        
        return {
            "message": "School and admin registered successfully",
            "user_id": response.user.id,
            "school_id": school_id,
            "access_token": response.session.access_token if has_session else None,
            "email_confirmation_required": not email_confirmed,
            "email": response.user.email
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


@router.post("/school-admin/signin")
async def signin_school_admin(email: str = Form(...), password: str = Form(...)):
    """School admin sign-in"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Verify user is school admin
        user_data = supabase.table("users").select("role, school_id").eq("id", response.user.id).single().execute()
        if not user_data.data or user_data.data.get("role") != "school_admin":
            raise HTTPException(status_code=403, detail="Access denied. School admin role required.")
        
        return {
            "access_token": response.session.access_token,
            "user": response.user,
            "school_id": user_data.data.get("school_id")
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        # Check if error is related to email confirmation
        if "email not confirmed" in error_msg or "confirm" in error_msg or "verification" in error_msg:
            raise HTTPException(
                status_code=403, 
                detail="Please check your email and confirm your account before signing in. A confirmation email has been sent to your email address."
            )
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.get("/me")
async def get_current_user_info(user = Depends(get_current_user)):
    """Get current authenticated user info"""
    return {"user": user.user}

