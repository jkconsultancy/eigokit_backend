from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase
from app.models import UserRole

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from Supabase JWT token"""
    try:
        token = credentials.credentials
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


def require_role(allowed_roles: List[UserRole], school_id: str = None):
    """Dependency factory to check if user has required role
    
    Args:
        allowed_roles: List of roles that are allowed to access the endpoint
        school_id: Optional school_id for school-scoped roles. If None, checks for platform-level roles.
    """
    async def role_checker(user = Depends(get_current_user)):
        from datetime import datetime, timezone
        
        allowed_role_values = [r.value for r in allowed_roles]
        user_id = user.user.id
        
        # Check user_roles table (multi-role system)
        # First check if user has platform_admin role (can access anything)
        if UserRole.PLATFORM_ADMIN in allowed_roles:
            platform_admin_check = supabase.table("user_roles").select("expires_at").eq("user_id", user_id).eq("role", "platform_admin").is_("school_id", "null").eq("is_active", True).execute()
            
            if platform_admin_check.data:
                now = datetime.now(timezone.utc)
                for role in platform_admin_check.data:
                    expires_at = role.get("expires_at")
                    if expires_at is None:
                        return user  # Active role with no expiration
                    # Check if not expired
                    try:
                        if isinstance(expires_at, str):
                            if expires_at.endswith('Z'):
                                expires_at = expires_at[:-1] + '+00:00'
                            exp_dt = datetime.fromisoformat(expires_at)
                            if exp_dt.tzinfo is None:
                                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                        else:
                            exp_dt = expires_at
                        if exp_dt > now:
                            return user  # Active non-expired role
                    except:
                        pass  # If parsing fails, skip this role
        
        # Check for other allowed roles
        # For school-scoped roles (school_admin, teacher), we need to check if user has the role
        # even if school_id is not specified (endpoint will verify school_id separately)
        # For platform-level roles (platform_admin), only check roles without school_id
        
        # Determine which roles are school-scoped vs platform-level
        school_scoped_roles = [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]
        platform_level_roles = [UserRole.PLATFORM_ADMIN]
        
        allowed_school_scoped = [r for r in allowed_roles if r in school_scoped_roles]
        allowed_platform_level = [r for r in allowed_roles if r in platform_level_roles]
        
        # Check school-scoped roles (can have any school_id or null)
        if allowed_school_scoped:
            school_scoped_values = [r.value for r in allowed_school_scoped]
            if school_id:
                # Check for role with specific school_id or platform admin
                query = supabase.table("user_roles").select("role, school_id, expires_at").eq("user_id", user_id).in_("role", school_scoped_values).eq("is_active", True).or_(f"school_id.eq.{school_id},school_id.is.null")
            else:
                # Check for role with any school_id (endpoint will verify school_id separately)
                query = supabase.table("user_roles").select("role, school_id, expires_at").eq("user_id", user_id).in_("role", school_scoped_values).eq("is_active", True)
            
            roles_result = query.execute()
            
            # Filter out expired roles
            if roles_result.data:
                now = datetime.now(timezone.utc)
                for role in roles_result.data:
                    expires_at = role.get("expires_at")
                    if expires_at is None:
                        return user  # Active role with no expiration
                    # Check if not expired
                    try:
                        if isinstance(expires_at, str):
                            if expires_at.endswith('Z'):
                                expires_at = expires_at[:-1] + '+00:00'
                            exp_dt = datetime.fromisoformat(expires_at)
                            if exp_dt.tzinfo is None:
                                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                        else:
                            exp_dt = expires_at
                        if exp_dt > now:
                            return user  # Active non-expired role
                    except:
                        pass  # If parsing fails, skip this role
        
        # Check platform-level roles (only roles without school_id)
        if allowed_platform_level:
            platform_values = [r.value for r in allowed_platform_level]
            query = supabase.table("user_roles").select("role, school_id, expires_at").eq("user_id", user_id).in_("role", platform_values).eq("is_active", True).is_("school_id", "null")
            roles_result = query.execute()
            
            # Filter out expired roles
            if roles_result.data:
                now = datetime.now(timezone.utc)
                for role in roles_result.data:
                    expires_at = role.get("expires_at")
                    if expires_at is None:
                        return user  # Active role with no expiration
                    # Check if not expired
                    try:
                        if isinstance(expires_at, str):
                            if expires_at.endswith('Z'):
                                expires_at = expires_at[:-1] + '+00:00'
                            exp_dt = datetime.fromisoformat(expires_at)
                            if exp_dt.tzinfo is None:
                                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                        else:
                            exp_dt = expires_at
                        if exp_dt > now:
                            return user  # Active non-expired role
                    except:
                        pass  # If parsing fails, skip this role
        
        # Filter out expired roles
        if roles_result.data:
            now = datetime.now(timezone.utc)
            for role in roles_result.data:
                expires_at = role.get("expires_at")
                if expires_at is None:
                    return user  # Active role with no expiration
                # Check if not expired
                try:
                    if isinstance(expires_at, str):
                        if expires_at.endswith('Z'):
                            expires_at = expires_at[:-1] + '+00:00'
                        exp_dt = datetime.fromisoformat(expires_at)
                        if exp_dt.tzinfo is None:
                            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    else:
                        exp_dt = expires_at
                    if exp_dt > now:
                        return user  # Active non-expired role
                except:
                    pass  # If parsing fails, skip this role
        
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return role_checker

