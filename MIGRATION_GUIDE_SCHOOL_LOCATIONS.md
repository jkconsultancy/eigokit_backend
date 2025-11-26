# Migration Guide: Adding School Locations Support

This guide explains how to update your existing database to support school locations.

## Overview

The update adds:
- A new `school_locations` table to store multiple locations per school
- A `location_id` column to the `classes` table to link classes to locations
- Full CRUD API endpoints for managing locations
- Frontend pages for managing teachers, locations, and classes

## Migration Steps

### Step 1: Backup Your Database

**IMPORTANT**: Always backup your database before running migrations.

In Supabase:
1. Go to Database → Backups
2. Create a manual backup or ensure automatic backups are enabled

### Step 2: Run the Migration SQL

1. Open your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `migration_add_school_locations.sql`
4. Click **Run** to execute the migration

The migration script is **idempotent** - it's safe to run multiple times. It will:
- Create the `school_locations` table if it doesn't exist
- Add the `location_id` column to `classes` if it doesn't exist
- Set up RLS policies for the new table
- Create necessary indexes

### Step 3: Verify the Migration

Run these queries to verify the migration was successful:

```sql
-- Check if school_locations table exists
SELECT * FROM school_locations LIMIT 1;

-- Check if location_id column exists in classes table
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'classes' AND column_name = 'location_id';

-- Check RLS policies
SELECT tablename, policyname 
FROM pg_policies 
WHERE tablename = 'school_locations';
```

### Step 4: Update Existing Data (Optional)

If you have existing classes and want to assign them to locations:

1. **Create locations first** (via the admin UI or SQL):
```sql
INSERT INTO school_locations (school_id, name, address, city, prefecture, is_active)
VALUES 
  ('<your-school-id>', 'Main Campus', '123 Main St', 'Tokyo', 'Tokyo', true),
  ('<your-school-id>', 'Branch Campus', '456 Branch Ave', 'Osaka', 'Osaka', true);
```

2. **Assign classes to locations**:
```sql
-- Assign all classes to a specific location
UPDATE classes 
SET location_id = '<location-id>' 
WHERE school_id = '<school-id>' AND location_id IS NULL;

-- Or assign specific classes
UPDATE classes 
SET location_id = '<location-id>' 
WHERE id = '<class-id>';
```

## For New Installations

If you're setting up a fresh database:

1. Run `schema.sql` first (this includes the school_locations table)
2. Then run `seed.sql` to populate with sample data
3. **Skip** `migration_add_school_locations.sql` (it's only for existing databases)

## API Changes

### New Endpoints

**Locations:**
- `GET /api/schools/{school_id}/locations` - List all locations
- `POST /api/schools/{school_id}/locations` - Create location
- `PUT /api/schools/{school_id}/locations/{location_id}` - Update location
- `DELETE /api/schools/{school_id}/locations/{location_id}` - Delete location

**Teachers (Enhanced):**
- `PUT /api/schools/{school_id}/teachers/{teacher_id}` - Update teacher
- `DELETE /api/schools/{school_id}/teachers/{teacher_id}` - Delete teacher

**Classes (Enhanced):**
- `PUT /api/schools/{school_id}/classes/{class_id}` - Update class (now supports location_id)
- `DELETE /api/schools/{school_id}/classes/{class_id}` - Delete class

### Updated Endpoints

**Classes:**
- `POST /api/schools/{school_id}/classes` - Now accepts optional `location_id` parameter
- `GET /api/schools/{school_id}/classes` - Now includes location information in response

## Frontend Changes

New pages added to the School Admin app:
- `/teachers` - Manage Teachers (CRUD)
- `/locations` - Manage School Locations (CRUD)
- `/classes` - Manage Classes (CRUD with location assignment)

Updated navigation in Dashboard to include links to these new pages.

## Rollback (If Needed)

If you need to rollback the migration:

```sql
-- Remove location_id from classes
ALTER TABLE classes DROP COLUMN IF EXISTS location_id;

-- Drop the school_locations table
DROP TABLE IF EXISTS school_locations CASCADE;
```

**Warning**: This will permanently delete all location data and remove location assignments from classes.

## Troubleshooting

### Error: "column location_id does not exist"
- The migration didn't complete successfully
- Re-run `migration_add_school_locations.sql`

### Error: "relation school_locations does not exist"
- The migration didn't create the table
- Check if you have proper permissions
- Re-run the migration script

### Classes showing "No location"
- This is expected for existing classes
- Assign them to locations via the UI or SQL (see Step 4)

### RLS blocking operations
- Ensure you're using the service role key in the backend
- Check that RLS policies were created correctly
- Verify the service role policy exists: `SELECT * FROM pg_policies WHERE tablename = 'school_locations';`

## Support

If you encounter issues:
1. Check the Supabase logs in the Dashboard
2. Verify all migration steps were completed
3. Ensure your backend is using the service role key for admin operations
4. Check that authentication is working correctly

## Next Steps

After migration:
1. Create at least one location for your school
2. Optionally assign existing classes to locations
3. Use the new management pages to organize your school structure
4. Create new classes with location assignments

