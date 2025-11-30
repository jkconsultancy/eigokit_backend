from fastapi import APIRouter, Depends, HTTPException, Form, Query
from app.database import supabase, supabase_admin
from app.models import Payment, ThemeConfig
from app.auth import get_current_user, require_role
from app.models import UserRole
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter()


def check_school_access(user_id: str, school_id: str) -> bool:
    """Helper function to check if user has access to a school (school_admin or platform_admin)"""
    try:
        # Check if user has platform_admin role (can access any school)
        platform_admin_role = supabase_admin.table("user_roles").select("expires_at").eq("user_id", user_id).eq("role", "platform_admin").is_("school_id", "null").eq("is_active", True).maybe_single().execute()
        
        if platform_admin_role and platform_admin_role.data:
            expires_at = platform_admin_role.data.get("expires_at")
            if expires_at is None:
                return True
            try:
                if isinstance(expires_at, str):
                    if expires_at.endswith('Z'):
                        expires_at = expires_at[:-1] + '+00:00'
                    exp_dt = datetime.fromisoformat(expires_at)
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                else:
                    exp_dt = expires_at
                if exp_dt > datetime.now(timezone.utc):
                    return True
            except:
                pass
        
        # Check if user has school_admin role for this specific school
        school_admin_role = supabase_admin.table("user_roles").select("expires_at").eq("user_id", user_id).eq("role", "school_admin").eq("school_id", school_id).eq("is_active", True).maybe_single().execute()
        
        if school_admin_role and school_admin_role.data:
            expires_at = school_admin_role.data.get("expires_at")
            if expires_at is None:
                return True
            try:
                if isinstance(expires_at, str):
                    if expires_at.endswith('Z'):
                        expires_at = expires_at[:-1] + '+00:00'
                    exp_dt = datetime.fromisoformat(expires_at)
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                else:
                    exp_dt = expires_at
                if exp_dt > datetime.now(timezone.utc):
                    return True
            except:
                pass
    except Exception as e:
        # Log error but don't fail - return False to deny access
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking school access for user {user_id}, school {school_id}: {str(e)}")
    
    return False


@router.get("/{school_id}/teachers")
async def get_school_teachers(school_id: str):
    """Get all teachers for a school"""
    # Get teacher_schools relationships for this school
    teacher_schools = supabase_admin.table("teacher_schools").select("*").eq("school_id", school_id).execute()
    
    if not teacher_schools.data:
        return {"teachers": []}
    
    # Get all teacher IDs
    teacher_ids = [ts["teacher_id"] for ts in teacher_schools.data]
    
    # Get teacher details
    teachers_data = supabase_admin.table("teachers").select("*").in_("id", teacher_ids).execute()
    
    # Create a map of teacher_id -> teacher data
    teachers_map = {t["id"]: t for t in teachers_data.data}
    
    # Merge teacher_schools data with teacher data
    teachers = []
    for ts in teacher_schools.data:
        teacher_id = ts["teacher_id"]
        teacher = teachers_map.get(teacher_id)
        
        # Skip if teacher record doesn't exist (data integrity issue)
        if not teacher:
            continue
        
        # Merge teacher data with teacher_schools invitation data
        merged_teacher = {
            **teacher,  # All teacher fields (id, name, email, etc.)
            "teacher_school_id": ts.get("id"),  # The teacher_schools relationship ID
            "invitation_status": ts.get("invitation_status"),  # Key field: pending, accepted, expired
            "invitation_token": ts.get("invitation_token"),
            "invitation_sent_at": ts.get("invitation_sent_at"),
            "invitation_expires_at": ts.get("invitation_expires_at"),
            "is_active": ts.get("is_active", True)  # Default to True for backward compatibility
        }
        teachers.append(merged_teacher)
    
    return {"teachers": teachers}


@router.get("/{school_id}/students/available-icon-sequence")
async def get_available_icon_sequence(school_id: str, student_name: str = Query(..., description="Student name to generate unique icon sequence for")):
    """Get an available icon sequence for a student name (not used by other students with same name)"""
    import random
    
    if not student_name or not student_name.strip():
        # Generate random sequence if no name provided
        sequence = sorted(random.sample(range(1, 25), 4))
        return {"icon_sequence": sequence, "icons": sequence}
    
    # Get all classes for school
    classes = supabase_admin.table("classes").select("id").eq("school_id", school_id).execute()
    class_ids = [c["id"] for c in classes.data]
    
    used_sequences = set()
    
    if class_ids:
        # Get all students with the same name in this school
        students = supabase_admin.table("students").select("icon_sequence").in_("class_id", class_ids).eq("name", student_name.strip()).execute()
        
        for student in students.data:
            if student.get("icon_sequence") and isinstance(student["icon_sequence"], list) and len(student["icon_sequence"]) == 4:
                # Normalize sequence (sort) for comparison since order matters but we want to avoid duplicates
                # Actually, order DOES matter, so we keep the original order
                seq_tuple = tuple(student["icon_sequence"])
                used_sequences.add(seq_tuple)
    
    # Generate random sequences until we find one not in use
    # Note: Order matters for authentication, so we preserve the random order
    max_attempts = 1000  # Increased attempts since we're checking exact sequence matches
    for _ in range(max_attempts):
        # Generate 4 unique random numbers between 1-24 (order matters!)
        sequence = random.sample(range(1, 25), 4)
        seq_tuple = tuple(sequence)
        if seq_tuple not in used_sequences:
            return {"icon_sequence": sequence, "icons": sequence}
    
    # If we can't find a unique one after many attempts, return a random one anyway
    # (in practice, with 24 icons and 4 positions, there are 24*23*22*21 = 255,024 possible sequences)
    sequence = random.sample(range(1, 25), 4)
    return {"icon_sequence": sequence, "icons": sequence}


@router.get("/{school_id}/students")
async def get_school_students(school_id: str):
    """Get all students for a school with class information"""
    # Get classes for school
    classes = supabase_admin.table("classes").select("id, name").eq("school_id", school_id).execute()
    class_ids = [c["id"] for c in classes.data]
    
    if not class_ids:
        return {"students": []}
    
    # Get students with class info
    students = supabase_admin.table("students").select("*, classes(name)").in_("class_id", class_ids).execute()
    return {"students": students.data}


@router.post("/{school_id}/students")
async def add_student(
    school_id: str,
    name: str = Form(...),
    class_id: str = Form(...),
    icon_sequence: Optional[str] = Form(None),
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Add a new student to a class"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify class belongs to school
    class_check = supabase_admin.table("classes").select("id").eq("id", class_id).eq("school_id", school_id).single().execute()
    if not class_check.data:
        raise HTTPException(status_code=404, detail="Class not found")
    
    student_data = {
        "name": name,
        "class_id": class_id,
        "registration_status": "pending"
    }
    
    # Parse icon_sequence if provided (comma-separated string)
    if icon_sequence:
        try:
            icon_array = [int(x.strip()) for x in icon_sequence.split(',')]
            student_data["icon_sequence"] = icon_array
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid icon_sequence format. Use comma-separated integers.")
    
    result = supabase_admin.table("students").insert(student_data).execute()
    return {"student_id": result.data[0]["id"], "message": "Student added", "student": result.data[0]}


@router.put("/{school_id}/students/{student_id}")
async def update_student(
    school_id: str,
    student_id: str,
    name: Optional[str] = Form(None),
    class_id: Optional[str] = Form(None),
    icon_sequence: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Update a student"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify student belongs to school
    student_check = supabase_admin.table("students").select("class_id").eq("id", student_id).single().execute()
    if not student_check.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify class belongs to school if class_id is being updated
    if class_id:
        class_check = supabase_admin.table("classes").select("id").eq("id", class_id).eq("school_id", school_id).single().execute()
        if not class_check.data:
            raise HTTPException(status_code=404, detail="Class not found")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if class_id is not None:
        update_data["class_id"] = class_id
    if icon_sequence is not None:
        if icon_sequence == "":
            update_data["icon_sequence"] = []
        else:
            try:
                icon_array = [int(x.strip()) for x in icon_sequence.split(',')]
                update_data["icon_sequence"] = icon_array
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid icon_sequence format. Use comma-separated integers.")
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true' if isinstance(is_active, str) else bool(is_active)
        update_data["is_active"] = is_active_bool
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = supabase_admin.table("students").update(update_data).eq("id", student_id).execute()
    return {"message": "Student updated", "student": result.data[0]}


@router.delete("/{school_id}/students/{student_id}")
async def delete_student(school_id: str, student_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Delete a student"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify student belongs to school
    student_check = supabase_admin.table("students").select("class_id").eq("id", student_id).single().execute()
    if not student_check.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    supabase_admin.table("students").delete().eq("id", student_id).execute()
    return {"message": "Student deleted"}


@router.get("/{school_id}/classes")
async def get_school_classes(school_id: str):
    """Get all classes for a school"""
    classes = supabase_admin.table("classes").select("*, teachers(name, email), school_locations(name)").eq("school_id", school_id).execute()
    return {"classes": classes.data}


@router.get("/{school_id}/locations")
async def get_school_locations(school_id: str):
    """Get all locations for a school"""
    locations = supabase_admin.table("school_locations").select("*").eq("school_id", school_id).order("name").execute()
    return {"locations": locations.data}


@router.post("/{school_id}/teachers")
async def add_teacher(school_id: str, name: str = Form(...), email: str = Form(...), user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Add a teacher to school and send invitation email"""
    import secrets
    from datetime import datetime, timedelta
    from app.services.email import email_service
    
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get school name for email
    school = supabase_admin.table("schools").select("name").eq("id", school_id).single().execute()
    school_name = school.data.get("name", "the school") if school.data else "the school"
    
    # Get inviter name
    inviter_data = supabase_admin.table("users").select("email").eq("id", user.user.id).single().execute()
    inviter_email = inviter_data.data.get("email", "") if inviter_data.data else ""
    
    # Generate unique invitation token
    invitation_token = secrets.token_urlsafe(32)
    invitation_expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    
    # Check if teacher already exists (by email)
    existing_teacher = supabase_admin.table("teachers").select("id").eq("email", email).maybe_single().execute()
    
    if existing_teacher.data:
        # Teacher exists, just create teacher_schools relationship
        teacher_id = existing_teacher.data["id"]
        # Check if relationship already exists
        existing_relationship = supabase_admin.table("teacher_schools").select("id").eq("teacher_id", teacher_id).eq("school_id", school_id).maybe_single().execute()
        if existing_relationship.data:
            raise HTTPException(status_code=400, detail="Teacher is already associated with this school")
    else:
        # Create new teacher record
        teacher_data = {
            "name": name,
            "email": email
        }
        result = supabase_admin.table("teachers").insert(teacher_data).execute()
        teacher_id = result.data[0]["id"]
    
    # Create teacher_schools relationship with invitation info
    teacher_school_data = {
        "teacher_id": teacher_id,
        "school_id": school_id,
        "invitation_token": invitation_token,
        "invitation_sent_at": datetime.utcnow().isoformat(),
        "invitation_status": "pending",
        "invitation_expires_at": invitation_expires_at
    }
    teacher_school_result = supabase_admin.table("teacher_schools").insert(teacher_school_data).execute()
    
    # Send invitation email (non-blocking - don't fail if email fails)
    try:
        email_sent = email_service.send_teacher_invitation(
            teacher_email=email,
            teacher_name=name,
            school_name=school_name,
            invitation_token=invitation_token,
            inviter_name=inviter_email
        )
        if not email_sent:
            # Log warning but don't fail the request
            print(f"Warning: Failed to send invitation email to {email}, but teacher was created")
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error sending invitation email to {email}: {str(e)}")
    
    # Get teacher data for response
    teacher_result = supabase_admin.table("teachers").select("*").eq("id", teacher_id).single().execute()
    
    return {
        "teacher_id": teacher_id,
        "message": "Teacher added and invitation email sent",
        "teacher": teacher_result.data[0],
        "invitation_sent": True
    }


@router.post("/{school_id}/teachers/{teacher_id}/resend-invitation")
async def resend_teacher_invitation(school_id: str, teacher_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Resend invitation email to a teacher"""
    import secrets
    from datetime import datetime, timedelta
    from app.services.email import email_service
    
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get teacher_schools relationship
    teacher_school_result = supabase_admin.table("teacher_schools").select("*, teachers(*)").eq("teacher_id", teacher_id).eq("school_id", school_id).single().execute()
    if not teacher_school_result.data:
        raise HTTPException(status_code=404, detail="Teacher not found for this school")
    
    teacher_school = teacher_school_result.data
    teacher = teacher_school.get("teachers", {})
    
    # Get school name for email
    school = supabase_admin.table("schools").select("name").eq("id", school_id).single().execute()
    school_name = school.data.get("name", "the school") if school.data else "the school"
    
    # Get inviter name
    inviter_data = supabase_admin.table("users").select("email").eq("id", user.user.id).single().execute()
    inviter_email = inviter_data.data.get("email", "") if inviter_data.data else ""
    
    # Generate new invitation token
    invitation_token = secrets.token_urlsafe(32)
    invitation_expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    
    # Update teacher_schools with new invitation token
    supabase_admin.table("teacher_schools").update({
        "invitation_token": invitation_token,
        "invitation_sent_at": datetime.utcnow().isoformat(),
        "invitation_status": "pending",
        "invitation_expires_at": invitation_expires_at
    }).eq("teacher_id", teacher_id).eq("school_id", school_id).execute()
    
    # Send invitation email
    try:
        email_sent = email_service.send_teacher_invitation(
            teacher_email=teacher["email"],
            teacher_name=teacher["name"],
            school_name=school_name,
            invitation_token=invitation_token,
            inviter_name=inviter_email
        )
        if not email_sent:
            # Check if email service is configured
            if not email_service.resend:
                return {
                    "message": "Invitation token updated, but email service is not configured. Please set RESEND_API_KEY in your .env file.",
                    "invitation_sent": False,
                    "error": "email_service_not_configured"
                }
            return {
                "message": "Invitation token updated, but email failed to send. Please check your email service configuration.",
                "invitation_sent": False,
                "error": "email_send_failed"
            }
        return {
            "message": "Invitation email resent successfully",
            "invitation_sent": True,
            "invitation_token": invitation_token  # Include token for manual sharing if needed
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Error resending invitation email to {teacher['email']}: {error_msg}")
        return {
            "message": f"Invitation token updated, but email failed to send: {error_msg}",
            "invitation_sent": False,
            "error": "email_exception",
            "error_details": error_msg
        }


@router.put("/{school_id}/teachers/{teacher_id}")
async def update_teacher(school_id: str, teacher_id: str, name: Optional[str] = Form(None), email: Optional[str] = Form(None), is_active: Optional[str] = Form(None), user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Update a teacher"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify teacher belongs to school
    teacher_school_check = supabase_admin.table("teacher_schools").select("id").eq("teacher_id", teacher_id).eq("school_id", school_id).single().execute()
    if not teacher_school_check.data:
        raise HTTPException(status_code=404, detail="Teacher not found for this school")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if email is not None:
        update_data["email"] = email
    
    # Update teacher record (affects all schools)
    if update_data:
        result = supabase_admin.table("teachers").update(update_data).eq("id", teacher_id).execute()
    
    # Update is_active in teacher_schools (per-school status)
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true' if isinstance(is_active, str) else bool(is_active)
        supabase_admin.table("teacher_schools").update({"is_active": is_active_bool}).eq("teacher_id", teacher_id).eq("school_id", school_id).execute()
    
    if not update_data and is_active is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Get updated teacher data
    teacher_result = supabase_admin.table("teachers").select("*").eq("id", teacher_id).single().execute()
    teacher_school_result = supabase_admin.table("teacher_schools").select("*").eq("teacher_id", teacher_id).eq("school_id", school_id).single().execute()
    
    merged_teacher = {
        **teacher_result.data[0],
        "teacher_school_id": teacher_school_result.data[0].get("id"),
        "is_active": teacher_school_result.data[0].get("is_active", True),
        "invitation_status": teacher_school_result.data[0].get("invitation_status")
    }
    
    return {"message": "Teacher updated", "teacher": merged_teacher}


@router.delete("/{school_id}/teachers/{teacher_id}")
async def delete_teacher(school_id: str, teacher_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Delete a teacher"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify teacher belongs to school
    teacher_school_check = supabase_admin.table("teacher_schools").select("id").eq("teacher_id", teacher_id).eq("school_id", school_id).single().execute()
    if not teacher_school_check.data:
        raise HTTPException(status_code=404, detail="Teacher not found for this school")
    
    # Remove teacher from this school (delete teacher_schools relationship)
    # Note: This doesn't delete the teacher record, just removes them from this school
    supabase_admin.table("teacher_schools").delete().eq("teacher_id", teacher_id).eq("school_id", school_id).execute()
    return {"message": "Teacher removed from school"}


@router.post("/{school_id}/classes")
async def add_class(school_id: str, name: str = Form(...), teacher_id: str = Form(...), location_id: Optional[str] = Form(None), user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Add a class to school"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify teacher belongs to school
    teacher_school_check = supabase_admin.table("teacher_schools").select("teacher_id").eq("teacher_id", teacher_id).eq("school_id", school_id).single().execute()
    if not teacher_school_check.data:
        raise HTTPException(status_code=404, detail="Teacher not found for this school")
    
    # Verify location belongs to school if provided
    if location_id:
        location_check = supabase_admin.table("school_locations").select("id").eq("id", location_id).eq("school_id", school_id).single().execute()
        if not location_check.data:
            raise HTTPException(status_code=404, detail="Location not found")
    
    class_data = {
        "name": name,
        "school_id": school_id,
        "teacher_id": teacher_id
    }
    if location_id:
        class_data["location_id"] = location_id
    
    result = supabase_admin.table("classes").insert(class_data).execute()
    return {"class_id": result.data[0]["id"], "message": "Class added", "class": result.data[0]}


@router.put("/{school_id}/classes/{class_id}")
async def update_class(school_id: str, class_id: str, name: Optional[str] = Form(None), teacher_id: Optional[str] = Form(None), location_id: Optional[str] = Form(None), is_active: Optional[str] = Form(None), user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Update a class"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify class belongs to school
    class_check = supabase_admin.table("classes").select("id").eq("id", class_id).eq("school_id", school_id).single().execute()
    if not class_check.data:
        raise HTTPException(status_code=404, detail="Class not found")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if teacher_id is not None:
        # Verify teacher belongs to school
        teacher_school_check = supabase_admin.table("teacher_schools").select("teacher_id").eq("teacher_id", teacher_id).eq("school_id", school_id).single().execute()
        if not teacher_school_check.data:
            raise HTTPException(status_code=404, detail="Teacher not found for this school")
        update_data["teacher_id"] = teacher_id
    if location_id is not None:
        if location_id == "":
            update_data["location_id"] = None
        else:
            # Verify location belongs to school
            location_check = supabase_admin.table("school_locations").select("id").eq("id", location_id).eq("school_id", school_id).single().execute()
            if not location_check.data:
                raise HTTPException(status_code=404, detail="Location not found")
            update_data["location_id"] = location_id
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true' if isinstance(is_active, str) else bool(is_active)
        update_data["is_active"] = is_active_bool
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = supabase_admin.table("classes").update(update_data).eq("id", class_id).execute()
    return {"message": "Class updated", "class": result.data[0]}


@router.delete("/{school_id}/classes/{class_id}")
async def delete_class(school_id: str, class_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Delete a class"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify class belongs to school
    class_check = supabase_admin.table("classes").select("id").eq("id", class_id).eq("school_id", school_id).single().execute()
    if not class_check.data:
        raise HTTPException(status_code=404, detail="Class not found")
    
    supabase_admin.table("classes").delete().eq("id", class_id).execute()
    return {"message": "Class deleted"}


@router.post("/{school_id}/payments")
async def create_payment(school_id: str, payment: Payment):
    """Create a payment record"""
    payment_data = {
        "school_id": school_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "payment_method": payment.payment_method.value,
        "status": payment.status.value,
        "billing_period_start": payment.billing_period_start.isoformat(),
        "billing_period_end": payment.billing_period_end.isoformat(),
        "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
        "notes": payment.notes
    }
    
    result = supabase.table("payments").insert(payment_data).execute()
    return {"payment_id": result.data[0]["id"], "message": "Payment created"}


@router.get("/{school_id}/payments")
async def get_payments(school_id: str):
    """Get payment history for school"""
    payments = supabase.table("payments").select("*").eq("school_id", school_id).order("created_at", desc=True).execute()
    return {"payments": payments.data}


@router.get("/{school_id}/payments/status")
async def get_payment_status(school_id: str):
    """Get current payment/subscription status"""
    # Get most recent payment
    payments = supabase.table("payments").select("*").eq("school_id", school_id).order("created_at", desc=True).limit(1).execute()
    
    if not payments.data:
        return {"status": "no_payment", "message": "No payment records found"}
    
    latest = payments.data[0]
    return {
        "status": latest["status"],
        "billing_period_start": latest["billing_period_start"],
        "billing_period_end": latest["billing_period_end"],
        "amount": latest["amount"]
    }


@router.get("/{school_id}/theme")
async def get_theme(school_id: str):
    """Get theme configuration for school"""
    theme = supabase.table("themes").select("*").eq("school_id", school_id).single().execute()
    if not theme.data:
        # Return default theme
        return {
            "school_id": school_id,
            "primary_color": "#3B82F6",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B"
        }
    return theme.data


@router.post("/{school_id}/theme")
async def update_theme(school_id: str, theme: ThemeConfig):
    """Update theme configuration for school"""
    theme_data = {
        "school_id": school_id,
        "primary_color": theme.primary_color,
        "secondary_color": theme.secondary_color,
        "accent_color": theme.accent_color,
        "font_family": theme.font_family,
        "logo_url": theme.logo_url,
        "app_icon_url": theme.app_icon_url,
        "favicon_url": theme.favicon_url,
        "background_color": theme.background_color,
        "button_style": theme.button_style,
        "card_style": theme.card_style
    }
    
    # Check if theme exists
    existing = supabase.table("themes").select("id").eq("school_id", school_id).execute()
    if existing.data:
        supabase.table("themes").update(theme_data).eq("school_id", school_id).execute()
        return {"message": "Theme updated"}
    else:
        result = supabase.table("themes").insert(theme_data).execute()
        return {"message": "Theme created", "theme_id": result.data[0]["id"]}


@router.post("/{school_id}/locations")
async def create_location(
    school_id: str,
    name: str = Form(...),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    prefecture: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    is_active: str = Form("true"),
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Create a new school location"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Convert is_active string to boolean
    is_active_bool = is_active.lower() in ('true', '1', 'yes', 'on') if isinstance(is_active, str) else bool(is_active)
    
    location_data = {
        "school_id": school_id,
        "name": name,
        "is_active": is_active_bool
    }
    if address:
        location_data["address"] = address
    if city:
        location_data["city"] = city
    if prefecture:
        location_data["prefecture"] = prefecture
    if postal_code:
        location_data["postal_code"] = postal_code
    if phone:
        location_data["phone"] = phone
    if email:
        location_data["email"] = email
    
    result = supabase_admin.table("school_locations").insert(location_data).execute()
    return {"location_id": result.data[0]["id"], "message": "Location created", "location": result.data[0]}


@router.put("/{school_id}/locations/{location_id}")
async def update_location(
    school_id: str,
    location_id: str,
    name: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    prefecture: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Update a school location"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify location belongs to school
    location_check = supabase_admin.table("school_locations").select("id").eq("id", location_id).eq("school_id", school_id).single().execute()
    if not location_check.data:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if address is not None:
        update_data["address"] = address
    if city is not None:
        update_data["city"] = city
    if prefecture is not None:
        update_data["prefecture"] = prefecture
    if postal_code is not None:
        update_data["postal_code"] = postal_code
    if phone is not None:
        update_data["phone"] = phone
    if email is not None:
        update_data["email"] = email
    if is_active is not None:
        # Convert is_active string to boolean
        is_active_bool = is_active.lower() in ('true', '1', 'yes', 'on') if isinstance(is_active, str) else bool(is_active)
        update_data["is_active"] = is_active_bool
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = supabase_admin.table("school_locations").update(update_data).eq("id", location_id).execute()
    return {"message": "Location updated", "location": result.data[0]}


@router.delete("/{school_id}/locations/{location_id}")
async def delete_location(school_id: str, location_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Delete a school location"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify location belongs to school
    location_check = supabase_admin.table("school_locations").select("id").eq("id", location_id).eq("school_id", school_id).single().execute()
    if not location_check.data:
        raise HTTPException(status_code=404, detail="Location not found")
    
    supabase_admin.table("school_locations").delete().eq("id", location_id).execute()
    return {"message": "Location deleted"}


@router.get("/{school_id}/dashboard")
async def get_school_dashboard(school_id: str):
    """Get school dashboard metrics with preview data"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Try to get active counts (if is_active column exists)
        try:
            active_teachers = supabase_admin.table("teacher_schools").select("teacher_id").eq("school_id", school_id).eq("is_active", True).execute()
            active_classes = supabase_admin.table("classes").select("id").eq("school_id", school_id).eq("is_active", True).execute()
            active_class_ids = [c["id"] for c in active_classes.data] if active_classes.data else []
            if active_class_ids:
                active_students = supabase_admin.table("students").select("id").in_("class_id", active_class_ids).eq("is_active", True).execute()
            else:
                active_students = type('Response', (), {'data': []})()
            active_locations = supabase_admin.table("school_locations").select("id").eq("school_id", school_id).eq("is_active", True).execute()
            
            # Get preview data (limit to 5 items each)
            try:
                preview_locations = supabase_admin.table("school_locations").select(
                    "id, name, city, prefecture"
                ).eq("school_id", school_id).eq("is_active", True).limit(5).execute()
            except Exception:
                # Fallback if is_active doesn't exist
                preview_locations = supabase_admin.table("school_locations").select(
                    "id, name, city, prefecture"
                ).eq("school_id", school_id).limit(5).execute()
            
            try:
                preview_classes = supabase_admin.table("classes").select(
                    "id, name, teacher_id, location_id, teachers(name, email), school_locations(name)"
                ).eq("school_id", school_id).eq("is_active", True).limit(5).execute()
            except Exception:
                # Fallback if is_active doesn't exist
                preview_classes = supabase_admin.table("classes").select(
                    "id, name, teacher_id, location_id, teachers(name, email), school_locations(name)"
                ).eq("school_id", school_id).limit(5).execute()
            
            # Get class IDs for students query
            preview_class_ids = [c["id"] for c in preview_classes.data] if preview_classes.data else []
            preview_students = type('Response', (), {'data': []})()
            if preview_class_ids:
                try:
                    preview_students = supabase_admin.table("students").select(
                        "id, name, class_id, classes(name)"
                    ).in_("class_id", preview_class_ids).eq("is_active", True).limit(5).execute()
                except Exception:
                    # Fallback if is_active doesn't exist
                    preview_students = supabase_admin.table("students").select(
                        "id, name, class_id, classes(name)"
                    ).in_("class_id", preview_class_ids).limit(5).execute()
            
        except Exception as e:
            # Fallback: if is_active column doesn't exist, get all (treat all as active)
            logger.warning(f"is_active column may not exist, falling back to all records: {str(e)}")
            active_teachers = supabase_admin.table("teacher_schools").select("teacher_id").eq("school_id", school_id).execute()
            active_classes = supabase_admin.table("classes").select("id").eq("school_id", school_id).execute()
            active_class_ids = [c["id"] for c in active_classes.data] if active_classes.data else []
            if active_class_ids:
                active_students = supabase_admin.table("students").select("id").in_("class_id", active_class_ids).execute()
            else:
                active_students = type('Response', (), {'data': []})()
            active_locations = supabase_admin.table("school_locations").select("id").eq("school_id", school_id).execute()
            
            # Get preview data without is_active filter
            preview_locations = supabase_admin.table("school_locations").select(
                "id, name, city, prefecture"
            ).eq("school_id", school_id).limit(5).execute()
            
            preview_classes = supabase_admin.table("classes").select(
                "id, name, teacher_id, location_id, teachers(name, email), school_locations(name)"
            ).eq("school_id", school_id).limit(5).execute()
            
            preview_class_ids = [c["id"] for c in preview_classes.data] if preview_classes.data else []
            preview_students = type('Response', (), {'data': []})()
            if preview_class_ids:
                preview_students = supabase_admin.table("students").select(
                    "id, name, class_id, classes(name)"
                ).in_("class_id", preview_class_ids).limit(5).execute()
        
        return {
            "school_level": {
                "active_students": len(getattr(active_students, 'data', [])),
                "active_locations": len(getattr(active_locations, 'data', [])),
                "active_teachers": len(getattr(active_teachers, 'data', [])),
                "active_classes": len(getattr(active_classes, 'data', []))
            },
            "previews": {
                "locations": getattr(preview_locations, 'data', []) or [],
                "classes": getattr(preview_classes, 'data', []) or [],
                "students": getattr(preview_students, 'data', []) or []
            }
        }
    except Exception as e:
        # Log the error and return a safe default
        logger.error(f"Error getting dashboard metrics: {str(e)}", exc_info=True)
        # Return zeros as fallback
        return {
            "school_level": {
                "active_students": 0,
                "active_locations": 0,
                "active_teachers": 0,
                "active_classes": 0
            },
            "previews": {
                "locations": [],
                "classes": [],
                "students": []
            }
        }


@router.get("/{school_id}")
async def get_school(school_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Get school information"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    school = supabase_admin.table("schools").select("*").eq("id", school_id).single().execute()
    if not school.data:
        raise HTTPException(status_code=404, detail="School not found")
    
    return {"school": school.data}


@router.put("/{school_id}")
async def update_school(
    school_id: str,
    name: Optional[str] = Form(None),
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Update school information"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = supabase_admin.table("schools").update(update_data).eq("id", school_id).execute()
    return {"message": "School updated", "school": result.data[0]}


@router.get("/{school_id}/admins")
async def get_school_admins(school_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Get all school admins for a school, including pending invitations"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all users with school_admin role for this school using user_roles table
    user_roles_result = supabase_admin.table("user_roles").select("user_id, granted_at").eq("role", "school_admin").eq("school_id", school_id).eq("is_active", True).order("granted_at").execute()
    
    # Get user details for these admins
    user_ids = [ur["user_id"] for ur in user_roles_result.data]
    users_result = supabase_admin.table("users").select("id, email, created_at, is_active").in_("id", user_ids).execute() if user_ids else type('obj', (object,), {'data': []})()
    
    # Create a map of user_id -> granted_at for sorting
    granted_at_map = {ur["user_id"]: ur["granted_at"] for ur in user_roles_result.data}
    
    # Get all pending invitations for this school
    pending_invitations_result = supabase_admin.table("school_admin_invitations").select("*").eq("school_id", school_id).eq("invitation_status", "pending").order("created_at", desc=True).execute()
    
    # Create a set of emails that already have user accounts
    accepted_admin_emails = {user_record["email"] for user_record in users_result.data}
    
    # Build list of accepted admins with granted_at from user_roles
    admins = []
    for user_record in users_result.data:
        user_id = user_record["id"]
        granted_at = granted_at_map.get(user_id, user_record.get("created_at"))
        # Get invitation information (most recent first)
        try:
            invitation_result = supabase_admin.table("school_admin_invitations").select("*").eq("email", user_record["email"]).eq("school_id", school_id).order("created_at", desc=True).limit(1).execute()
            
            name = None
            invitation_status = None
            invitation_expires_at = None
            
            if invitation_result.data and len(invitation_result.data) > 0:
                invitation = invitation_result.data[0]
                name = invitation.get("name")
                invitation_status = invitation.get("invitation_status")
                invitation_expires_at = invitation.get("invitation_expires_at")
        except Exception:
            # If query fails, just continue without invitation data
            name = None
            invitation_status = None
            invitation_expires_at = None
        
        admin_data = {
            "id": user_record["id"],
            "email": user_record["email"],
            "name": name,
            "created_at": user_record["created_at"],
            "invitation_status": invitation_status or "accepted",  # Default to accepted if no invitation record
            "invitation_expires_at": invitation_expires_at,
            "is_active": user_record.get("is_active", True)  # Default to True for backward compatibility
        }
        admins.append(admin_data)
    
    # Add pending invitations that don't have user accounts yet
    for invitation in pending_invitations_result.data:
        invitation_email = invitation.get("email")
        # Only include if this email doesn't already have a user account
        if invitation_email not in accepted_admin_emails:
            admin_data = {
                "id": None,  # No user account yet
                "email": invitation_email,
                "name": invitation.get("name"),
                "created_at": invitation.get("created_at"),
                "invitation_status": "pending",
                "invitation_expires_at": invitation.get("invitation_expires_at"),
                "invitation_id": invitation.get("id")  # Store invitation ID for resend/delete operations
            }
            admins.append(admin_data)
    
    return {"admins": admins}


@router.post("/{school_id}/admins/invite")
async def invite_school_admin(
    school_id: str,
    email: str = Form(...),
    name: str = Form(...),
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Invite a new school admin to the school"""
    import secrets
    from datetime import datetime, timedelta
    from app.services.email import email_service
    
    # Verify user's school_id matches
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get user email for later use
    user_data = supabase_admin.table("users").select("email").eq("id", user.user.id).single().execute()
    
    # Get school name for email
    school = supabase_admin.table("schools").select("name").eq("id", school_id).single().execute()
    school_name = school.data.get("name", "the school") if school.data else "the school"
    
    # Get inviter email
    inviter_email = user_data.data.get("email", "")
    
    # Check if there's already a pending invitation for this email and school
    try:
        existing_invitation_result = supabase_admin.table("school_admin_invitations").select("*").eq("email", email).eq("school_id", school_id).eq("invitation_status", "pending").execute()
        
        if existing_invitation_result.data and len(existing_invitation_result.data) > 0:
            existing_invitation = existing_invitation_result.data[0]
            # Check if invitation is still valid (not expired)
            if existing_invitation.get("invitation_expires_at"):
                expires_at = datetime.fromisoformat(existing_invitation["invitation_expires_at"].replace("Z", "+00:00"))
                if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) <= expires_at:
                    raise HTTPException(status_code=400, detail="An invitation has already been sent to this email. Please wait for it to expire or resend the invitation.")
    except HTTPException:
        raise
    except Exception:
        # If query fails, continue (don't block invitation creation)
        pass
    
    # Check if user already exists and is already a school admin for this school using user_roles table
    existing_user = supabase_admin.table("users").select("id").eq("email", email).maybe_single().execute()
    
    if existing_user.data:
        user_id = existing_user.data["id"]
        # Check if user already has school_admin role for this school
        existing_role = supabase_admin.table("user_roles").select("id, expires_at").eq("user_id", user_id).eq("role", "school_admin").eq("school_id", school_id).eq("is_active", True).maybe_single().execute()
        
        if existing_role.data:
            # Check if role is not expired
            expires_at = existing_role.data.get("expires_at")
            if expires_at is None:
                raise HTTPException(status_code=400, detail="User is already a school admin for this school")
            else:
                try:
                    if isinstance(expires_at, str):
                        if expires_at.endswith('Z'):
                            expires_at = expires_at[:-1] + '+00:00'
                        exp_dt = datetime.fromisoformat(expires_at)
                        if exp_dt.tzinfo is None:
                            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    else:
                        exp_dt = expires_at
                    if exp_dt > datetime.now(timezone.utc):
                        raise HTTPException(status_code=400, detail="User is already a school admin for this school")
                except:
                    pass  # If expired or parsing fails, allow invitation
        
        # Check if user is school admin for another school
        other_school_role = supabase_admin.table("user_roles").select("school_id").eq("user_id", user_id).eq("role", "school_admin").eq("is_active", True).neq("school_id", school_id).maybe_single().execute()
        if other_school_role.data:
            raise HTTPException(status_code=400, detail="User is already a school admin for another school")
    
    # Generate invitation token
    invitation_token = secrets.token_urlsafe(32)
    invitation_expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    
    # Store invitation in database
    invitation_data = {
        "school_id": school_id,
        "email": email,
        "name": name,
        "invitation_token": invitation_token,
        "invitation_sent_at": datetime.utcnow().isoformat(),
        "invitation_status": "pending",
        "invitation_expires_at": invitation_expires_at,
        "invited_by": user.user.id
    }
    
    # Insert invitation record
    invitation_result = supabase_admin.table("school_admin_invitations").insert(invitation_data).execute()
    
    if not invitation_result.data:
        raise HTTPException(status_code=500, detail="Failed to create invitation record")
    
    # Send invitation email
    try:
        # Build invitation URL
        from app.config import settings
        import os
        frontend_url = (
            getattr(settings, "frontend_schools_url", None)
            or os.getenv("FRONTEND_SCHOOLS_URL")
            or os.getenv("frontend_schools_url")
        )
        
        if frontend_url:
            base_url = frontend_url.rstrip('/')
            invitation_url = f"{base_url}/register?token={invitation_token}&school_id={school_id}"
        else:
            invitation_url = f"#token={invitation_token}&school_id={school_id}"
        
        inviter_text = f" by {inviter_email}" if inviter_email else ""
        subject = f"Invitation to administer {school_name} on EigoKit"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #3B82F6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #3B82F6; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>EigoKit School Admin Invitation</h1>
                </div>
                <div class="content">
                    <p>Hello {name},</p>
                    <p>You have been invited{inviter_text} to administer <strong>{school_name}</strong> on EigoKit.</p>
                    <p>EigoKit is an English learning platform that helps schools manage students, teachers, and classes.</p>
                    <p style="text-align: center;">
                        <a href="{invitation_url}" class="button">Accept Invitation</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #6b7280; font-size: 14px;">{invitation_url}</p>
                    <p>This invitation link will expire in 7 days.</p>
                    <p>If you didn't expect this invitation, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© EigoKit - English Learning Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {name},
        
        You have been invited{inviter_text} to administer {school_name} on EigoKit.
        
        EigoKit is an English learning platform that helps schools manage students, teachers, and classes.
        
        Accept your invitation by clicking this link:
        {invitation_url}
        
        This invitation link will expire in 7 days.
        
        If you didn't expect this invitation, you can safely ignore this email.
        
        © EigoKit - English Learning Platform
        """
        
        if email_service.resend:
            emails = email_service.resend.Emails()
            params = {
                "from": email_service.from_email,
                "to": [email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
            }
            emails.send(params)
            print(f"School admin invitation email sent to {email}")
        else:
            print(f"Email service not available. Would send invitation to {email}")
            print(f"Invitation URL: {invitation_url}")
            print(f"Token: {invitation_token}")
    except Exception as e:
        error_msg = str(e)
        print(f"Error sending invitation email to {email}: {error_msg}")
        # Don't fail the request if email fails
    
    return {
        "message": "Invitation sent successfully",
        "email": email,
        "invitation_id": invitation_result.data[0]["id"],
        "invitation_token": invitation_token  # Include for manual sharing if needed
    }


@router.put("/{school_id}/admins/{admin_id}")
async def update_school_admin(
    school_id: str,
    admin_id: str,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    is_active: Optional[str] = Form(None),
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Update a school admin's information"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify admin has school_admin role for this school using user_roles table
    admin_role = supabase_admin.table("user_roles").select("id, expires_at").eq("user_id", admin_id).eq("role", "school_admin").eq("school_id", school_id).eq("is_active", True).maybe_single().execute()
    if not admin_role.data:
        raise HTTPException(status_code=404, detail="Admin not found for this school")
    
    # Check if role is expired
    expires_at = admin_role.data.get("expires_at")
    if expires_at is not None:
        try:
            if isinstance(expires_at, str):
                if expires_at.endswith('Z'):
                    expires_at = expires_at[:-1] + '+00:00'
                exp_dt = datetime.fromisoformat(expires_at)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            else:
                exp_dt = expires_at
            if exp_dt <= datetime.now(timezone.utc):
                raise HTTPException(status_code=404, detail="Admin role has expired")
        except:
            pass
    
    # Get admin email for validation
    admin_check = supabase_admin.table("users").select("email").eq("id", admin_id).single().execute()
    
    # Don't allow updating email if it would conflict with another user
    if email and email != admin_check.data.get("email"):
        existing_user = supabase_admin.table("users").select("id").eq("email", email).maybe_single().execute()
        if existing_user.data and existing_user.data.get("id") != admin_id:
            raise HTTPException(status_code=400, detail="Email is already in use by another user")
    
    update_data = {}
    # Update user email if provided
    if email:
        update_data["email"] = email
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true' if isinstance(is_active, str) else bool(is_active)
        update_data["is_active"] = is_active_bool
    
    if update_data:
        supabase_admin.table("users").update(update_data).eq("id", admin_id).execute()
    
    # Update invitation record with new name if provided
    if name:
        # Update the most recent invitation for this admin
        invitation_result = supabase_admin.table("school_admin_invitations").select("id").eq("email", admin_check.data.get("email")).eq("school_id", school_id).order("created_at", desc=True).limit(1).execute()
        if invitation_result.data and len(invitation_result.data) > 0:
            supabase_admin.table("school_admin_invitations").update({"name": name}).eq("id", invitation_result.data[0]["id"]).execute()
    
    if not update_data and not name:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    return {"message": "Admin updated successfully"}


@router.delete("/{school_id}/admins/{admin_id}")
async def delete_school_admin(
    school_id: str,
    admin_id: str,
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Remove a school admin from the school, or delete a pending invitation"""
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if admin_id is a UUID (user ID) or invitation ID
    # First, try to find it as a user ID with school_admin role for this school
    admin_role = supabase_admin.table("user_roles").select("id").eq("user_id", admin_id).eq("role", "school_admin").eq("school_id", school_id).eq("is_active", True).maybe_single().execute()
    
    if admin_role.data:
        # It's an existing user - remove their school_admin role for this school
        # Don't allow deleting yourself
        if admin_id == user.user.id:
            raise HTTPException(status_code=400, detail="You cannot remove yourself from the school")
        
        # Deactivate the school_admin role for this school
        supabase_admin.table("user_roles").update({
            "is_active": False,
            "updated_at": datetime.now().isoformat()
        }).eq("user_id", admin_id).eq("role", "school_admin").eq("school_id", school_id).execute()
        
        return {"message": "Admin removed from school successfully"}
    else:
        # Check if it's a pending invitation ID
        invitation_check = supabase_admin.table("school_admin_invitations").select("id").eq("id", admin_id).eq("school_id", school_id).eq("invitation_status", "pending").maybe_single().execute()
        
        if invitation_check.data:
            # Delete the pending invitation
            supabase_admin.table("school_admin_invitations").delete().eq("id", admin_id).execute()
            return {"message": "Pending invitation deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Admin or invitation not found for this school")


@router.post("/{school_id}/admins/{admin_id}/resend-invitation")
async def resend_school_admin_invitation(
    school_id: str,
    admin_id: str,
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Resend invitation email to a school admin or pending invitation"""
    import secrets
    from datetime import datetime, timedelta
    from app.services.email import email_service
    
    # Verify user's school_id matches
    # Verify user has access to this school (school_admin or platform_admin)
    if not check_school_access(user.user.id, school_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get user email for later use
    user_data = supabase_admin.table("users").select("email").eq("id", user.user.id).single().execute()
    
    # Check if admin_id is a user ID or invitation ID
    # Check if user has school_admin role for this school
    admin_role = supabase_admin.table("user_roles").select("id").eq("user_id", admin_id).eq("role", "school_admin").eq("school_id", school_id).eq("is_active", True).maybe_single().execute()
    
    if admin_role.data:
        # Get admin email
        admin_check = supabase_admin.table("users").select("email").eq("id", admin_id).single().execute()
    
    if admin_check.data:
        # It's an existing user - get their email and find invitation
        admin_email = admin_check.data.get("email")
        invitation_result = supabase_admin.table("school_admin_invitations").select("*").eq("email", admin_email).eq("school_id", school_id).order("created_at", desc=True).limit(1).execute()
    else:
        # Check if it's a pending invitation ID
        invitation_result = supabase_admin.table("school_admin_invitations").select("*").eq("id", admin_id).eq("school_id", school_id).eq("invitation_status", "pending").execute()
    
    if not invitation_result.data or len(invitation_result.data) == 0:
        raise HTTPException(status_code=404, detail="No invitation found for this admin")
    
    invitation = invitation_result.data[0]
    admin_email = invitation.get("email")
    
    # Get school name
    school = supabase_admin.table("schools").select("name").eq("id", school_id).single().execute()
    school_name = school.data.get("name", "the school") if school.data else "the school"
    
    # Generate new invitation token
    invitation_token = secrets.token_urlsafe(32)
    invitation_expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    
    # Update invitation
    supabase_admin.table("school_admin_invitations").update({
        "invitation_token": invitation_token,
        "invitation_sent_at": datetime.utcnow().isoformat(),
        "invitation_status": "pending",
        "invitation_expires_at": invitation_expires_at
    }).eq("id", invitation["id"]).execute()
    
    # Send invitation email
    try:
        from app.config import settings
        import os
        frontend_url = (
            getattr(settings, "frontend_schools_url", None)
            or os.getenv("FRONTEND_SCHOOLS_URL")
            or os.getenv("frontend_schools_url")
        )
        
        if frontend_url:
            base_url = frontend_url.rstrip('/')
            invitation_url = f"{base_url}/register?token={invitation_token}&school_id={school_id}"
        else:
            invitation_url = f"#token={invitation_token}&school_id={school_id}"
        
        inviter_email = user_data.data.get("email", "")
        inviter_text = f" by {inviter_email}" if inviter_email else ""
        subject = f"Invitation to administer {school_name} on EigoKit"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #3B82F6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #3B82F6; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>EigoKit School Admin Invitation</h1>
                </div>
                <div class="content">
                    <p>Hello {invitation.get('name', 'there')},</p>
                    <p>You have been invited{inviter_text} to administer <strong>{school_name}</strong> on EigoKit.</p>
                    <p>EigoKit is an English learning platform that helps schools manage students, teachers, and classes.</p>
                    <p style="text-align: center;">
                        <a href="{invitation_url}" class="button">Accept Invitation</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #6b7280; font-size: 14px;">{invitation_url}</p>
                    <p>This invitation link will expire in 7 days.</p>
                    <p>If you didn't expect this invitation, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© EigoKit - English Learning Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello {invitation.get('name', 'there')},
        
        You have been invited{inviter_text} to administer {school_name} on EigoKit.
        
        EigoKit is an English learning platform that helps schools manage students, teachers, and classes.
        
        Accept your invitation by clicking this link:
        {invitation_url}
        
        This invitation link will expire in 7 days.
        
        If you didn't expect this invitation, you can safely ignore this email.
        
        © EigoKit - English Learning Platform
        """
        
        if email_service.resend:
            emails = email_service.resend.Emails()
            params = {
                "from": email_service.from_email,
                "to": [admin_email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
            }
            emails.send(params)
            print(f"School admin invitation email resent to {admin_email}")
            return {
                "message": "Invitation email resent successfully",
                "invitation_sent": True,
                "invitation_token": invitation_token
            }
        else:
            print(f"Email service not available. Would resend invitation to {admin_email}")
            return {
                "message": "Invitation token updated, but email service is not configured",
                "invitation_sent": False,
                "invitation_token": invitation_token
            }
    except Exception as e:
        error_msg = str(e)
        print(f"Error resending invitation email to {admin_email}: {error_msg}")
        return {
            "message": f"Invitation token updated, but email failed to send: {error_msg}",
            "invitation_sent": False,
            "error": "email_exception",
            "error_details": error_msg
        }

