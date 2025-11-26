from fastapi import APIRouter, HTTPException, Depends, Form, Query
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


@router.post("/teacher/accept-invitation")
async def accept_teacher_invitation(
    token: str = Query(..., description="Invitation token from email"),
    password: str = Form(...),
    name: Optional[str] = Form(None)
):
    """Accept a teacher invitation and create account"""
    from datetime import datetime
    
    # Find teacher by invitation token
    teacher_result = supabase_admin.table("teachers").select("*").eq("invitation_token", token).single().execute()
    
    if not teacher_result.data:
        raise HTTPException(status_code=404, detail="Invalid invitation token")
    
    teacher = teacher_result.data
    
    # Check if invitation is expired
    if teacher.get("invitation_expires_at"):
        expires_at = datetime.fromisoformat(teacher["invitation_expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
            raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Check if already accepted
    if teacher.get("invitation_status") == "accepted":
        raise HTTPException(status_code=400, detail="Invitation has already been accepted")
    
    # Create auth user
    try:
        response = supabase.auth.sign_up({
            "email": teacher["email"],
            "password": password
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Failed to create user account")
        
        user_id = response.user.id
        
        # Create user record with role
        supabase_admin.table("users").insert({
            "id": user_id,
            "email": teacher["email"],
            "role": "teacher",
            "school_id": teacher["school_id"]
        }).execute()
        
        # Update teacher record: link to auth user and mark as accepted
        # Note: We can't change the primary key, so we'll keep the original teacher.id
        # but link it to the user via a separate field if needed, or just mark as accepted
        update_data = {
            "invitation_status": "accepted",
        }
        if name and name != teacher["name"]:
            update_data["name"] = name
        
        # If teacher table has a user_id field, link it. Otherwise, the email match is sufficient
        supabase_admin.table("teachers").update(update_data).eq("id", teacher["id"]).execute()
        
        # Also update the teacher record to link with auth user if there's a user_id field
        # For now, we rely on email matching between teachers and users tables
        
        return {
            "message": "Invitation accepted successfully",
            "access_token": response.session.access_token if response.session else None,
            "user_id": user_id,
            "email_confirmation_required": True if not response.session else False
        }
    except Exception as e:
        # If user already exists, try to sign in instead
        if "already registered" in str(e).lower() or "already exists" in str(e).lower():
            try:
                signin_response = supabase.auth.sign_in_with_password({
                    "email": teacher["email"],
                    "password": password
                })
                # Update invitation status
                supabase_admin.table("teachers").update({
                    "invitation_status": "accepted"
                }).eq("id", teacher["id"]).execute()
                
                return {
                    "message": "Account already exists. Signed in successfully.",
                    "access_token": signin_response.session.access_token,
                    "user_id": signin_response.user.id
                }
            except:
                raise HTTPException(status_code=400, detail="Account exists but password is incorrect")
        raise HTTPException(status_code=400, detail=f"Failed to accept invitation: {str(e)}")


@router.post("/teacher/signup")
async def signup_teacher(email: str, password: str, name: str, school_id: str):
    """Teacher sign-up (legacy - use accept-invitation instead)"""
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

