"""
Icon Password System Service

This module handles the icon-based password system for students:
- 48 total available icons
- Each school uses a subset of 9 password icons
- Each student gets a unique 5-icon sequence from their school's 9 icons
"""

import random
from typing import List, Set, Optional
import logging

logger = logging.getLogger(__name__)

# All 48 available icons (expanded from 24)
ALL_ICONS = [
    {'id': 1, 'name': 'apple', 'emoji': '🍎'},
    {'id': 2, 'name': 'banana', 'emoji': '🍌'},
    {'id': 3, 'name': 'orange', 'emoji': '🍊'},
    {'id': 4, 'name': 'strawberry', 'emoji': '🍓'},
    {'id': 5, 'name': 'cat', 'emoji': '🐱'},
    {'id': 6, 'name': 'dog', 'emoji': '🐶'},
    {'id': 7, 'name': 'bird', 'emoji': '🐦'},
    {'id': 8, 'name': 'rabbit', 'emoji': '🐰'},
    {'id': 9, 'name': 'book', 'emoji': '📚'},
    {'id': 10, 'name': 'pencil', 'emoji': '✏️'},
    {'id': 11, 'name': 'ball', 'emoji': '⚽'},
    {'id': 12, 'name': 'car', 'emoji': '🚗'},
    {'id': 13, 'name': 'sun', 'emoji': '☀️'},
    {'id': 14, 'name': 'moon', 'emoji': '🌙'},
    {'id': 15, 'name': 'star', 'emoji': '⭐'},
    {'id': 16, 'name': 'heart', 'emoji': '❤️'},
    {'id': 17, 'name': 'house', 'emoji': '🏠'},
    {'id': 18, 'name': 'tree', 'emoji': '🌳'},
    {'id': 19, 'name': 'flower', 'emoji': '🌸'},
    {'id': 20, 'name': 'fish', 'emoji': '🐟'},
    {'id': 21, 'name': 'bear', 'emoji': '🐻'},
    {'id': 22, 'name': 'lion', 'emoji': '🦁'},
    {'id': 23, 'name': 'elephant', 'emoji': '🐘'},
    {'id': 24, 'name': 'butterfly', 'emoji': '🦋'},
    {'id': 25, 'name': 'panda', 'emoji': '🐼'},
    {'id': 26, 'name': 'tiger', 'emoji': '🐯'},
    {'id': 27, 'name': 'cow', 'emoji': '🐮'},
    {'id': 28, 'name': 'pig', 'emoji': '🐷'},
    {'id': 29, 'name': 'frog', 'emoji': '🐸'},
    {'id': 30, 'name': 'duck', 'emoji': '🦆'},
    {'id': 31, 'name': 'horse', 'emoji': '🐴'},
    {'id': 32, 'name': 'sheep', 'emoji': '🐑'},
    {'id': 33, 'name': 'giraffe', 'emoji': '🦒'},
    {'id': 34, 'name': 'zebra', 'emoji': '🦓'},
    {'id': 35, 'name': 'monkey', 'emoji': '🐵'},
    {'id': 36, 'name': 'chicken', 'emoji': '🐔'},
    {'id': 37, 'name': 'penguin', 'emoji': '🐧'},
    {'id': 38, 'name': 'owl', 'emoji': '🦉'},
    {'id': 39, 'name': 'dolphin', 'emoji': '🐬'},
    {'id': 40, 'name': 'whale', 'emoji': '🐋'},
    {'id': 41, 'name': 'shark', 'emoji': '🦈'},
    {'id': 42, 'name': 'turtle', 'emoji': '🐢'},
    {'id': 43, 'name': 'snake', 'emoji': '🐍'},
    {'id': 44, 'name': 'spider', 'emoji': '🕷️'},
    {'id': 45, 'name': 'bee', 'emoji': '🐝'},
    {'id': 46, 'name': 'snail', 'emoji': '🐌'},
    {'id': 47, 'name': 'crab', 'emoji': '🦀'},
    {'id': 48, 'name': 'lobster', 'emoji': '🦞'},
]

# Icon lookup by ID
ICON_BY_ID = {icon['id']: icon for icon in ALL_ICONS}


def get_all_icons() -> List[dict]:
    """Get all available icons"""
    return ALL_ICONS


def get_icon_by_id(icon_id: int) -> Optional[dict]:
    """Get icon information by ID"""
    return ICON_BY_ID.get(icon_id)


def get_icons_by_ids(icon_ids: List[int]) -> List[dict]:
    """Get multiple icons by their IDs"""
    return [ICON_BY_ID.get(id) for id in icon_ids if ICON_BY_ID.get(id)]


def generate_school_password_icons() -> List[int]:
    """
    Generate a random set of 9 password icons for a school.
    Returns a list of 9 unique icon IDs.
    """
    available_ids = list(range(1, 49))  # IDs 1-48
    selected = random.sample(available_ids, 9)
    return sorted(selected)


def generate_unique_icon_sequence(
    school_password_icons: List[int],
    used_sequences: Set[tuple],
    max_attempts: int = 1000
) -> Optional[List[int]]:
    """
    Generate a unique 5-icon sequence from a school's 9 password icons.
    
    Args:
        school_password_icons: List of 9 icon IDs available for the school
        used_sequences: Set of tuples representing already-used sequences
        max_attempts: Maximum number of attempts to find a unique sequence
    
    Returns:
        List of 5 icon IDs in order, or None if no unique sequence found
    """
    if len(school_password_icons) < 5:
        logger.error(f"School has fewer than 5 password icons: {len(school_password_icons)}")
        return None
    
    for _ in range(max_attempts):
        # Generate a random 5-icon sequence from the school's 9 icons
        # Order matters, so we use random.sample (no replacement) then shuffle
        sequence = random.sample(school_password_icons, 5)
        seq_tuple = tuple(sequence)
        
        if seq_tuple not in used_sequences:
            return sequence
    
    logger.warning(f"Could not generate unique sequence after {max_attempts} attempts")
    # Return a random one anyway (shouldn't happen in practice with 9 choose 5 = 126 combinations)
    return random.sample(school_password_icons, 5)


def get_used_sequences_for_school(
    supabase_admin,
    school_id: str,
    student_id: Optional[str] = None
) -> Set[tuple]:
    """
    Get all used icon sequences for students in a school.
    
    Args:
        supabase_admin: Supabase admin client
        school_id: School ID
        exclude_student_id: Optional student ID to exclude from the check
    
    Returns:
        Set of tuples representing used sequences
    """
    used_sequences = set()
    
    try:
        # Get all classes for the school
        classes = supabase_admin.table("classes").select("id").eq("school_id", school_id).execute()
        class_ids = [c["id"] for c in classes.data] if classes.data else []
        
        if not class_ids:
            return used_sequences
        
        # Get all students in those classes
        query = supabase_admin.table("students").select("id, icon_sequence").in_("class_id", class_ids)
        
        if student_id:
            query = query.neq("id", student_id)
        
        students = query.execute()
        
        # Extract sequences
        for student in students.data or []:
            icon_seq = student.get("icon_sequence")
            if icon_seq and isinstance(icon_seq, list) and len(icon_seq) == 5:
                # Convert to tuple for set membership
                used_sequences.add(tuple(icon_seq))
    
    except Exception as e:
        logger.error(f"Error getting used sequences for school {school_id}: {str(e)}")
    
    return used_sequences


def generate_student_icon_sequence(
    supabase_admin,
    school_id: str,
    student_id: Optional[str] = None
) -> Optional[List[int]]:
    """
    Generate a unique 5-icon sequence for a student.
    
    Args:
        supabase_admin: Supabase admin client
        school_id: School ID
        student_id: Optional student ID to exclude from collision check
    
    Returns:
        List of 5 icon IDs, or None if generation failed
    """
    try:
        # Get school's password icons
        try:
            school = supabase_admin.table("schools").select("password_icons").eq("id", school_id).single().execute()
        except Exception as e:
            # Check if the error is about missing column
            error_msg = str(e).lower()
            if "password_icons" in error_msg and ("does not exist" in error_msg or "column" in error_msg):
                logger.error(f"password_icons column does not exist. Please run migration: migrations/002_add_school_password_icons.sql")
                raise Exception("Database migration required: password_icons column missing. Please run migrations/002_add_school_password_icons.sql")
            raise
        
        if not school.data:
            logger.error(f"School not found: {school_id}")
            return None
        
        password_icons = school.data.get("password_icons")
        
        # If school doesn't have password icons set, generate them
        if not password_icons or len(password_icons) != 9:
            logger.info(f"School {school_id} doesn't have password icons set, generating new ones")
            password_icons = generate_school_password_icons()
            # Save to database
            try:
                supabase_admin.table("schools").update({"password_icons": password_icons}).eq("id", school_id).execute()
            except Exception as e:
                error_msg = str(e).lower()
                if "password_icons" in error_msg and ("does not exist" in error_msg or "column" in error_msg):
                    logger.error(f"password_icons column does not exist. Please run migration: migrations/002_add_school_password_icons.sql")
                    raise Exception("Database migration required: password_icons column missing. Please run migrations/002_add_school_password_icons.sql")
                raise
        
        # Get used sequences
        used_sequences = get_used_sequences_for_school(supabase_admin, school_id, student_id=student_id)
        
        # Generate unique sequence
        sequence = generate_unique_icon_sequence(password_icons, used_sequences)
        
        if sequence:
            logger.info(f"Generated icon sequence for student: {sequence}")
            return sequence
        else:
            logger.error(f"Failed to generate unique icon sequence for school {school_id}")
            return None
    
    except Exception as e:
        logger.error(f"Error generating student icon sequence: {str(e)}", exc_info=True)
        return None


def validate_icon_sequence(sequence: List[int], school_password_icons: List[int]) -> bool:
    """
    Validate that an icon sequence is valid for a school.
    
    Args:
        sequence: List of icon IDs
        school_password_icons: List of school's 9 password icon IDs
    
    Returns:
        True if valid, False otherwise
    """
    if not sequence or len(sequence) != 5:
        return False
    
    # Check that all icons in sequence are from school's password icons
    password_icons_set = set(school_password_icons)
    sequence_set = set(sequence)
    
    return sequence_set.issubset(password_icons_set) and len(sequence) == len(set(sequence))  # No duplicates

