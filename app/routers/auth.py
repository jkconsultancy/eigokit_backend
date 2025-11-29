from fastapi import APIRouter, HTTPException, Depends, Form, Query
from app.database import supabase, supabase_admin
from app.config import settings
from app.models import StudentRegistration, StudentSignIn
from app.auth import get_current_user
from app.services.icon_password import get_icons_by_ids, generate_school_password_icons
from typing import Optional

router = APIRouter()


@router.get("/schools")
async def get_schools():
    """Get list of all schools for student login selection"""
    try:
        schools = supabase.table("schools").select("id, name, password_icons").execute()
    except Exception as e:
        # Check if the error is about missing column
        error_msg = str(e).lower()
        if "password_icons" in error_msg and ("does not exist" in error_msg or "column" in error_msg):
            raise HTTPException(
                status_code=500,
                detail="Database migration required: password_icons column missing. Please run migrations/002_add_school_password_icons.sql"
            )
        raise
    
    # For each school, ensure it has password icons set, and return icon details
    result = []
    for school in schools.data or []:
        password_icon_ids = school.get("password_icons")
        
        # If school doesn't have password icons, generate them
        if not password_icon_ids or len(password_icon_ids) != 9:
            password_icon_ids = generate_school_password_icons()
            # Save to database
            try:
                supabase_admin.table("schools").update({"password_icons": password_icon_ids}).eq("id", school["id"]).execute()
            except Exception as e:
                error_msg = str(e).lower()
                if "password_icons" in error_msg and ("does not exist" in error_msg or "column" in error_msg):
                    raise HTTPException(
                        status_code=500,
                        detail="Database migration required: password_icons column missing. Please run migrations/002_add_school_password_icons.sql"
                    )
                raise
        
        # Get icon details
        icons = get_icons_by_ids(password_icon_ids)
        
        result.append({
            "id": school["id"],
            "name": school["name"],
            "password_icons": password_icon_ids,
            "icons": icons
        })
    
    return {"schools": result}


@router.get("/schools/{school_id}/password-icons")
async def get_school_password_icons(school_id: str):
    """Get password icons for a specific school"""
    try:
        school = supabase.table("schools").select("id, name, password_icons").eq("id", school_id).single().execute()
    except Exception as e:
        # Check if the error is about missing column
        error_msg = str(e).lower()
        if "password_icons" in error_msg and ("does not exist" in error_msg or "column" in error_msg):
            raise HTTPException(
                status_code=500,
                detail="Database migration required: password_icons column missing. Please run migrations/002_add_school_password_icons.sql"
            )
        raise
    
    if not school.data:
        raise HTTPException(status_code=404, detail="School not found")
    
    password_icon_ids = school.data.get("password_icons")
    
    # If school doesn't have password icons, generate them
    if not password_icon_ids or len(password_icon_ids) != 9:
        password_icon_ids = generate_school_password_icons()
        # Save to database
        try:
            supabase_admin.table("schools").update({"password_icons": password_icon_ids}).eq("id", school_id).execute()
        except Exception as e:
            error_msg = str(e).lower()
            if "password_icons" in error_msg and ("does not exist" in error_msg or "column" in error_msg):
                raise HTTPException(
                    status_code=500,
                    detail="Database migration required: password_icons column missing. Please run migrations/002_add_school_password_icons.sql"
                )
            raise
    
    # Get icon details
    icons = get_icons_by_ids(password_icon_ids)
    
    return {
        "school_id": school_id,
        "school_name": school.data["name"],
        "password_icons": password_icon_ids,
        "icons": icons
    }


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
async def signin_student(signin: StudentSignIn, school_id: str = Query(..., description="School ID for authentication")):
    """Student sign-in with icon-based authentication (icon sequence only, no name required)"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate icon sequence length
    if len(signin.icon_sequence) != 5:
        raise HTTPException(status_code=400, detail="Icon sequence must contain exactly 5 icons")
    
    # Find student by icon sequence and school
    # Get classes for the school first
    classes = supabase.table("classes").select("id").eq("school_id", school_id).execute()
    class_ids = [c["id"] for c in classes.data] if classes.data else []
    
    if not class_ids:
        raise HTTPException(status_code=401, detail="No classes found for this school")
    
    # Find all students in those classes
    students = supabase.table("students").select("id, icon_sequence, class_id, name").in_("class_id", class_ids).execute()
    
    if not students.data:
        raise HTTPException(status_code=401, detail="No students found")
    
    # Check icon sequence (order matters)
    # Normalize input sequence to list of integers
    input_sequence = [int(x) for x in signin.icon_sequence]
    
    # Find student with matching icon sequence
    for student in students.data:
        db_sequence = student.get("icon_sequence")
        
        # Handle different data types from database
        if db_sequence is None:
            continue
        
        # Convert to list of integers if needed
        if isinstance(db_sequence, list):
            db_sequence = [int(x) for x in db_sequence]
        else:
            # If it's a string or other type, try to convert
            try:
                db_sequence = [int(x) for x in db_sequence]
            except:
                logger.warning(f"Could not convert icon_sequence for student {student['id']}: {db_sequence}")
                continue
        
        # Compare sequences (order matters!)
        if db_sequence == input_sequence:
            logger.info(f"Student {student['id']} ({student.get('name', 'Unknown')}) signed in successfully")
            return {
                "student_id": student["id"],
                "class_id": student["class_id"],
                "student_name": student.get("name", ""),
                "message": "Sign-in successful"
            }
        else:
            # Log for debugging
            logger.debug(f"Sequence mismatch for student {student['id']}: DB={db_sequence}, Input={input_sequence}")
    
    raise HTTPException(status_code=401, detail="Invalid icon sequence")


@router.post("/teacher/signin")
async def signin_teacher(email: str, password: str):
    """Teacher sign-in with email/password"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # Look up the teacher profile by email to get the teachers.id used as FK
        # Use maybe_single() to avoid errors when no record exists
        teacher_row = supabase_admin.table("teachers").select("id").eq("email", email).maybe_single().execute()
        
        # Check if teacher_row is None or if data is missing
        if not teacher_row or not teacher_row.data:
            # Teacher exists in Auth but not in teachers table
            # This can happen if teacher was created directly in Auth or record was deleted
            import logging
            logging.warning(f"Teacher with email {email} exists in Auth but not in teachers table")
            raise HTTPException(
                status_code=403,
                detail="Teacher profile not found. Please contact your school administrator to set up your account."
            )

        return {
            "access_token": response.session.access_token,
            "user": response.user,
            "teacher_id": teacher_row.data["id"],
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like 403 for teacher not found)
        raise
    except Exception as e:
        # Log the actual error for debugging
        error_msg = str(e).lower()
        # Provide more specific error messages
        if "invalid login credentials" in error_msg or "invalid" in error_msg and "password" in error_msg:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        elif "email not confirmed" in error_msg or "confirm" in error_msg:
            raise HTTPException(
                status_code=403,
                detail="Please check your email and confirm your account before signing in."
            )
        else:
            # Log unexpected errors but don't expose details to client
            import logging
            logging.error(f"Teacher sign-in error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/teacher/invitation-status")
async def get_teacher_invitation_status(
    token: str = Query(..., description="Invitation token from email")
):
    """Check invitation status and whether user already exists"""
    from datetime import datetime
    
    # Find teacher_schools relationship by invitation token
    teacher_school_result = supabase_admin.table("teacher_schools").select("*, teachers(*)").eq("invitation_token", token).maybe_single().execute()
    
    if not teacher_school_result.data:
        raise HTTPException(status_code=404, detail="Invalid invitation token")
    
    teacher_school = teacher_school_result.data
    teacher = teacher_school.get("teachers", {})
    school_id = teacher_school.get("school_id")
    
    # Check if invitation is expired
    if teacher_school.get("invitation_expires_at"):
        expires_at = datetime.fromisoformat(teacher_school["invitation_expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
            raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Check if already accepted
    if teacher_school.get("invitation_status") == "accepted":
        raise HTTPException(status_code=400, detail="Invitation has already been accepted")
    
    # Check if user exists in Supabase Auth by attempting to get user by email
    # Note: Supabase doesn't have a direct "check if user exists" API, so we'll try to sign in
    # with a dummy password to see if the account exists (this is a common pattern)
    user_exists = False
    try:
        # Try to get user - Supabase Admin API can check if user exists
        # We'll use a different approach: check if there's a user record in our users table
        user_check = supabase_admin.table("users").select("id").eq("email", teacher.get("email")).maybe_single().execute()
        user_exists = user_check.data is not None
    except:
        # If we can't check, assume user doesn't exist
        user_exists = False
    
    # Check if teacher already has a record for this school (the current relationship)
    teacher_exists_for_school = True  # We already found the relationship
    
    return {
        "email": teacher.get("email"),
        "name": teacher.get("name"),
        "school_id": school_id,
        "user_exists": user_exists,
        "teacher_exists_for_school": teacher_exists_for_school,
        "requires_registration": not user_exists,
        "requires_signin": user_exists
    }


@router.post("/teacher/accept-invitation")
async def accept_teacher_invitation(
    token: str = Query(..., description="Invitation token from email"),
    password: str = Form(...),
    confirm_password: Optional[str] = Form(None),
    name: Optional[str] = Form(None)
):
    """
    Accept a teacher invitation.
    
    If user exists: Just sign in (no password confirmation needed).
    If user is new: Register with password confirmation.
    """
    from datetime import datetime
    
    # Find teacher_schools relationship by invitation token
    teacher_school_result = supabase_admin.table("teacher_schools").select("*, teachers(*)").eq("invitation_token", token).maybe_single().execute()
    
    if not teacher_school_result.data:
        raise HTTPException(status_code=404, detail="Invalid invitation token")
    
    teacher_school = teacher_school_result.data
    teacher = teacher_school.get("teachers", {})
    teacher_id = teacher.get("id")
    school_id = teacher_school.get("school_id")
    
    # Check if invitation is expired
    if teacher_school.get("invitation_expires_at"):
        expires_at = datetime.fromisoformat(teacher_school["invitation_expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
            raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Check if already accepted
    if teacher_school.get("invitation_status") == "accepted":
        raise HTTPException(status_code=400, detail="Invitation has already been accepted")
    
    # Check if user exists
    user_check = supabase_admin.table("users").select("id").eq("email", teacher.get("email")).maybe_single().execute()
    user_exists = user_check.data is not None
    
    if user_exists:
        # User exists - just sign them in and associate with school
        try:
            signin_response = supabase.auth.sign_in_with_password({
                "email": teacher.get("email"),
                "password": password
            })
            
            user_id = signin_response.user.id
            
            # Update the teacher_schools relationship to mark invitation as accepted
            supabase_admin.table("teacher_schools").update({
                "invitation_status": "accepted"
            }).eq("teacher_id", teacher_id).eq("school_id", school_id).execute()
            
            # Update teacher name if provided
            if name and name != teacher.get("name"):
                supabase_admin.table("teachers").update({"name": name}).eq("id", teacher_id).execute()
            
            return {
                "message": "Invitation accepted successfully. You are now signed in.",
                "access_token": signin_response.session.access_token,
                "teacher_id": teacher_id,
                "user_id": user_id
            }
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg and "password" in error_msg:
                raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")
            raise HTTPException(status_code=401, detail="Sign in failed. Please check your password.")
    else:
        # New user - register with password confirmation
        if not confirm_password:
            raise HTTPException(status_code=400, detail="Password confirmation is required for new accounts")
        
        if password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
        try:
            # Create auth user
            response = supabase.auth.sign_up({
                "email": teacher.get("email"),
                "password": password
            })
            
            if not response.user:
                raise HTTPException(status_code=400, detail="Failed to create user account")
            
            user_id = response.user.id
            
            # Create user record with role
            supabase_admin.table("users").insert({
                "id": user_id,
                "email": teacher.get("email"),
                "role": "teacher",
                "school_id": school_id
            }).execute()
            
            # Update teacher_schools relationship: mark as accepted
            supabase_admin.table("teacher_schools").update({
                "invitation_status": "accepted"
            }).eq("teacher_id", teacher_id).eq("school_id", school_id).execute()
            
            # Update teacher name if provided
            if name and name != teacher.get("name"):
                supabase_admin.table("teachers").update({"name": name}).eq("id", teacher_id).execute()
            
            return {
                "message": "Account created and invitation accepted successfully",
                "access_token": response.session.access_token if response.session else None,
                "teacher_id": teacher_id,
                "user_id": user_id,
                "email_confirmation_required": True if not response.session else False
            }
        except Exception as e:
            error_msg = str(e).lower()
            if "already registered" in error_msg or "already exists" in error_msg:
                # Race condition - user was created between check and creation
                # Try to sign in instead
                try:
                    signin_response = supabase.auth.sign_in_with_password({
                        "email": teacher.get("email"),
                        "password": password
                    })
                    # Update the invitation record
                    supabase_admin.table("teacher_schools").update({
                        "invitation_status": "accepted"
                    }).eq("teacher_id", teacher_id).eq("school_id", school_id).execute()
                    
                    if name:
                        supabase_admin.table("teachers").update({"name": name}).eq("id", teacher_id).execute()
                    
                    return {
                        "message": "Account already exists. Signed in successfully.",
                        "access_token": signin_response.session.access_token,
                        "teacher_id": teacher_id,
                        "user_id": signin_response.user.id
                    }
                except:
                    raise HTTPException(status_code=400, detail="Account exists but password is incorrect")
            raise HTTPException(status_code=400, detail=f"Failed to create account: {str(e)}")


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


@router.post("/password-reset-request")
async def password_reset_request(
    email: str = Form(...),
    app: str = Form(..., description="App requesting reset: 'platform_admin' | 'school_admin' | 'teacher'"),
):
    """
    Request a password reset email for any Supabase-authenticated account.

    This works for:
    - Platform admins
    - School admins
    - Teachers

    Students use icon-based sign-in and do not have passwords; they should ask a teacher
    to reset their registration instead.
    """
    # Choose redirect URL based on which app is requesting the reset
    # Append /auth/reset-password to the base frontend URL
    redirect_url = None
    if app == "platform_admin":
        if settings.frontend_admins_url:
            redirect_url = f"{settings.frontend_admins_url.rstrip('/')}/auth/reset-password"
    elif app == "school_admin":
        if settings.frontend_schools_url:
            redirect_url = f"{settings.frontend_schools_url.rstrip('/')}/auth/reset-password"
    elif app == "teacher":
        if settings.frontend_teachers_url:
            redirect_url = f"{settings.frontend_teachers_url.rstrip('/')}/auth/reset-password"

    # Fallback: if no specific URL set, let Supabase use its configured default
    options = {"redirect_to": redirect_url} if redirect_url else None

    try:
        if options:
            supabase.auth.reset_password_for_email(email, options=options)
        else:
            supabase.auth.reset_password_for_email(email)
    except Exception:
        # Don't leak whether the email exists
        raise HTTPException(
            status_code=400,
            detail="Unable to process password reset request. Please try again later.",
        )

    return {
        "message": "If an account with that email exists, a password reset email has been sent."
    }

