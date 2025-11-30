# Admin Role System

## Overview

The EigoKit platform uses a multi-role based access control (RBAC) system to determine user permissions. Roles are stored in the `user_roles` table, allowing users to have multiple roles simultaneously (e.g., platform_admin AND teacher). This system is linked to Supabase Auth users.

## User Roles

1. **Platform Admin** (`platform_admin`)
   - Full access to all platform features
   - Can manage all schools, payments, and feature flags
   - Access: `/api/platform/*` endpoints

2. **School Admin** (`school_admin`)
   - Manages their own school
   - Can manage teachers, students, classes, payments, and branding
   - Access: `/api/schools/*` endpoints (filtered to their school)

3. **Teacher** (`teacher`)
   - Manages their classes and students
   - Can create content, surveys, and view dashboards
   - Access: `/api/teachers/*` endpoints (filtered to their classes)

4. **Student** (`student`)
   - Uses icon-based authentication (no password)
   - Access: `/api/students/*` endpoints (filtered to their own data)

## How Roles Are Determined

### Database Structure

The `user_roles` table manages roles, allowing users to have multiple roles:

```sql
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'platform_admin', 'school_admin', 'teacher', 'student'
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE, -- NULL for platform-level roles
    is_active BOOLEAN DEFAULT true,
    granted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Optional expiration for temporary roles
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_user_role_school UNIQUE(user_id, role, school_id),
    CONSTRAINT platform_admin_no_school CHECK (
        (role = 'platform_admin' AND school_id IS NULL) OR 
        (role != 'platform_admin')
    )
);
```

### Role Assignment Flow

1. **Platform Admin**:
   - Create user in Supabase Auth (Dashboard > Authentication > Users)
   - Insert record in `users` table (id, email only)
   - Insert record in `user_roles` table with `role = 'platform_admin'` and `school_id = NULL`

2. **School Admin**:
   - Create user in Supabase Auth
   - Insert record in `users` table (id, email only)
   - Insert record in `user_roles` table with `role = 'school_admin'` and `school_id = <school_uuid>`

3. **Teacher**:
   - Created via `/api/auth/teacher/signup` endpoint
   - Automatically assigned `role = 'teacher'` and `school_id` in `user_roles` table

4. **Student**:
   - No Supabase Auth user needed
   - Uses icon-based authentication
   - Stored in `students` table only

### Authentication Flow

1. User signs in via Supabase Auth (email/password)
2. Backend receives JWT token
3. `get_current_user()` extracts user ID from token
4. `require_role()` checks `user_roles` table for active, non-expired roles
5. Access granted/denied based on role(s)

## Setting Up Platform Admin

### Step 1: Create Auth User

1. Go to Supabase Dashboard > Authentication > Users
2. Click "Add User"
3. Enter email and password (e.g., `admin@eigokit.com`)
4. Copy the user's UUID

### Step 2: Create User Record

Run this SQL in Supabase SQL Editor:

```sql
-- Create user record (without role - that goes in user_roles)
INSERT INTO users (id, email, created_at) 
VALUES ('YOUR_USER_UUID_HERE', 'admin@eigokit.com', NOW())
ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;

-- Create platform_admin role in user_roles table
INSERT INTO user_roles (user_id, role, school_id, is_active, granted_at)
VALUES ('YOUR_USER_UUID_HERE', 'platform_admin', NULL, true, NOW())
ON CONFLICT (user_id, role, school_id) DO UPDATE SET is_active = true, expires_at = NULL;
```

### Step 3: Sign In

Use the Platform Admin app to sign in with the email/password you created.

## API Endpoint Protection

All platform admin endpoints are protected with:

```python
@router.get("/endpoint")
async def endpoint(user = Depends(require_role([UserRole.PLATFORM_ADMIN]))):
    # Only platform admins can access
    ...
```

The `require_role()` dependency:
1. Verifies JWT token
2. Looks up user in `user_roles` table for active, non-expired roles
3. Checks if any role matches allowed roles
4. Returns 403 if no matching role found

## Troubleshooting

### "Network Error" in Frontend

- **Backend not running**: Start with `uvicorn app.main:app --reload`
- **Wrong API URL**: Check `.env` file has correct `VITE_API_URL`
- **CORS issue**: Backend CORS is configured to allow all origins (check `app/main.py`)

### "Access denied" or 403 Error

- User doesn't have required role in `user_roles` table
- Check user's roles: 
  ```sql
  SELECT ur.*, u.email 
  FROM user_roles ur 
  JOIN users u ON ur.user_id = u.id 
  WHERE u.email = 'user@example.com' AND ur.is_active = true;
  ```
- Add role if needed: 
  ```sql
  INSERT INTO user_roles (user_id, role, school_id, is_active, granted_at)
  SELECT id, 'platform_admin', NULL, true, NOW()
  FROM users WHERE email = 'user@example.com'
  ON CONFLICT (user_id, role, school_id) DO UPDATE SET is_active = true;
  ```

### "Invalid credentials" Error

- User doesn't exist in Supabase Auth
- Password is incorrect
- User exists in Auth but not in `users` table (create record)

