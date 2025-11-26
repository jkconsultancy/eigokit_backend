# Admin Role System

## Overview

The EigoKit platform uses a role-based access control (RBAC) system to determine user permissions. Roles are stored in the `users` table and linked to Supabase Auth users.

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

The `users` table links Supabase Auth users to roles:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL DEFAULT 'teacher',
    school_id UUID REFERENCES schools(id),
    ...
);
```

### Role Assignment Flow

1. **Platform Admin**:
   - Create user in Supabase Auth (Dashboard > Authentication > Users)
   - Insert record in `users` table with `role = 'platform_admin'`
   - No `school_id` needed

2. **School Admin**:
   - Create user in Supabase Auth
   - Insert record in `users` table with `role = 'school_admin'` and `school_id`

3. **Teacher**:
   - Created via `/api/auth/teacher/signup` endpoint
   - Automatically assigned `role = 'teacher'` and `school_id`

4. **Student**:
   - No Supabase Auth user needed
   - Uses icon-based authentication
   - Stored in `students` table only

### Authentication Flow

1. User signs in via Supabase Auth (email/password)
2. Backend receives JWT token
3. `get_current_user()` extracts user ID from token
4. `require_role()` checks `users` table for role
5. Access granted/denied based on role

## Setting Up Platform Admin

### Step 1: Create Auth User

1. Go to Supabase Dashboard > Authentication > Users
2. Click "Add User"
3. Enter email and password (e.g., `admin@eigokit.com`)
4. Copy the user's UUID

### Step 2: Create User Record

Run this SQL in Supabase SQL Editor:

```sql
INSERT INTO users (id, email, role, created_at) 
VALUES ('YOUR_USER_UUID_HERE', 'admin@eigokit.com', 'platform_admin', NOW())
ON CONFLICT (id) DO NOTHING;
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
2. Looks up user in `users` table
3. Checks if role matches allowed roles
4. Returns 403 if role doesn't match

## Troubleshooting

### "Network Error" in Frontend

- **Backend not running**: Start with `uvicorn app.main:app --reload`
- **Wrong API URL**: Check `.env` file has correct `VITE_API_URL`
- **CORS issue**: Backend CORS is configured to allow all origins (check `app/main.py`)

### "Access denied" or 403 Error

- User doesn't have required role in `users` table
- Check user's role: `SELECT * FROM users WHERE email = 'user@example.com';`
- Update role if needed: `UPDATE users SET role = 'platform_admin' WHERE email = 'user@example.com';`

### "Invalid credentials" Error

- User doesn't exist in Supabase Auth
- Password is incorrect
- User exists in Auth but not in `users` table (create record)

