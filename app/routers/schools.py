from fastapi import APIRouter, Depends, HTTPException, Form, Query
from app.database import supabase, supabase_admin
from app.models import Payment, ThemeConfig
from app.auth import get_current_user, require_role
from app.models import UserRole
from typing import List, Optional

router = APIRouter()


@router.get("/{school_id}/teachers")
async def get_school_teachers(school_id: str):
    """Get all teachers for a school"""
    teachers = supabase.table("teachers").select("*").eq("school_id", school_id).execute()
    return {"teachers": teachers.data}


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
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
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
    user = Depends(require_role([UserRole.SCHOOL_ADMIN]))
):
    """Update a student"""
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
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
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = supabase_admin.table("students").update(update_data).eq("id", student_id).execute()
    return {"message": "Student updated", "student": result.data[0]}


@router.delete("/{school_id}/students/{student_id}")
async def delete_student(school_id: str, student_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Delete a student"""
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
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
    classes = supabase.table("classes").select("*, teachers(name, email), school_locations(name)").eq("school_id", school_id).execute()
    return {"classes": classes.data}


@router.get("/{school_id}/locations")
async def get_school_locations(school_id: str):
    """Get all locations for a school"""
    locations = supabase_admin.table("school_locations").select("*").eq("school_id", school_id).order("name").execute()
    return {"locations": locations.data}


@router.post("/{school_id}/teachers")
async def add_teacher(school_id: str, name: str = Form(...), email: str = Form(...), user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Add a teacher to school"""
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    teacher_data = {
        "name": name,
        "email": email,
        "school_id": school_id
    }
    
    result = supabase_admin.table("teachers").insert(teacher_data).execute()
    return {"teacher_id": result.data[0]["id"], "message": "Teacher added", "teacher": result.data[0]}


@router.put("/{school_id}/teachers/{teacher_id}")
async def update_teacher(school_id: str, teacher_id: str, name: Optional[str] = Form(None), email: Optional[str] = Form(None), user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Update a teacher"""
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify teacher belongs to school
    teacher_check = supabase_admin.table("teachers").select("id").eq("id", teacher_id).eq("school_id", school_id).single().execute()
    if not teacher_check.data:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if email is not None:
        update_data["email"] = email
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = supabase_admin.table("teachers").update(update_data).eq("id", teacher_id).execute()
    return {"message": "Teacher updated", "teacher": result.data[0]}


@router.delete("/{school_id}/teachers/{teacher_id}")
async def delete_teacher(school_id: str, teacher_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Delete a teacher"""
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify teacher belongs to school
    teacher_check = supabase_admin.table("teachers").select("id").eq("id", teacher_id).eq("school_id", school_id).single().execute()
    if not teacher_check.data:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    supabase_admin.table("teachers").delete().eq("id", teacher_id).execute()
    return {"message": "Teacher deleted"}


@router.post("/{school_id}/classes")
async def add_class(school_id: str, name: str = Form(...), teacher_id: str = Form(...), location_id: Optional[str] = Form(None), user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Add a class to school"""
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify teacher belongs to school
    teacher_check = supabase_admin.table("teachers").select("id").eq("id", teacher_id).eq("school_id", school_id).single().execute()
    if not teacher_check.data:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
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
async def update_class(school_id: str, class_id: str, name: Optional[str] = Form(None), teacher_id: Optional[str] = Form(None), location_id: Optional[str] = Form(None), user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Update a class"""
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
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
        teacher_check = supabase_admin.table("teachers").select("id").eq("id", teacher_id).eq("school_id", school_id).single().execute()
        if not teacher_check.data:
            raise HTTPException(status_code=404, detail="Teacher not found")
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
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = supabase_admin.table("classes").update(update_data).eq("id", class_id).execute()
    return {"message": "Class updated", "class": result.data[0]}


@router.delete("/{school_id}/classes/{class_id}")
async def delete_class(school_id: str, class_id: str, user = Depends(require_role([UserRole.SCHOOL_ADMIN]))):
    """Delete a class"""
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
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
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
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
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
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
    # Verify user's school_id matches
    user_data = supabase_admin.table("users").select("school_id").eq("id", user.user.id).single().execute()
    if not user_data.data or user_data.data.get("school_id") != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify location belongs to school
    location_check = supabase_admin.table("school_locations").select("id").eq("id", location_id).eq("school_id", school_id).single().execute()
    if not location_check.data:
        raise HTTPException(status_code=404, detail="Location not found")
    
    supabase_admin.table("school_locations").delete().eq("id", location_id).execute()
    return {"message": "Location deleted"}


@router.get("/{school_id}/dashboard")
async def get_school_dashboard(school_id: str):
    """Get school dashboard metrics"""
    # Get counts
    teachers = supabase.table("teachers").select("id").eq("school_id", school_id).execute()
    classes = supabase.table("classes").select("id").eq("school_id", school_id).execute()
    class_ids = [c["id"] for c in classes.data]
    students = supabase.table("students").select("id").in_("class_id", class_ids).execute()
    
    # Get survey completion
    student_ids = [s["id"] for s in students.data]
    surveys = supabase.table("survey_responses").select("id").in_("student_id", student_ids).execute()
    
    # Get game engagement
    games = supabase.table("game_sessions").select("id").in_("student_id", student_ids).execute()
    
    return {
        "school_level": {
            "active_students": len(students.data),
            "survey_completion_rate": len(surveys.data) / max(len(students.data), 1) * 100 if students.data else 0,
            "game_engagement": len(games.data)
        },
        "teacher_level": {
            "total_teachers": len(teachers.data),
            "teachers": teachers.data
        },
        "class_level": {
            "total_classes": len(classes.data),
            "classes": classes.data
        }
    }

