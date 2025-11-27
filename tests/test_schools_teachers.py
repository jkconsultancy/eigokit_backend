"""
Tests for school teacher management endpoints
"""
import pytest
# Note: client fixture is provided by conftest.py


def test_get_school_teachers_empty(client, mocker):
    """Test getting teachers for a school with no teachers"""
    mock_supabase = mocker.patch('app.routers.schools.supabase_admin')
    mock_table = mocker.MagicMock()
    mock_supabase.table.return_value = mock_table
    
    # Mock empty teacher_schools response
    mock_table.select.return_value.eq.return_value.execute.return_value.data = []
    
    response = client.get("/api/schools/test-school-id/teachers")
    
    assert response.status_code == 200
    assert response.json() == {"teachers": []}
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.eq.assert_called_once_with("school_id", "test-school-id")


def test_get_school_teachers_with_accepted_teacher(client, mocker):
    """Test getting teachers including one with accepted invitation status"""
    mock_supabase = mocker.patch('app.routers.schools.supabase_admin')
    mock_table = mocker.MagicMock()
    mock_supabase.table.return_value = mock_table
    
    # Mock teacher_schools response
    teacher_schools_data = [
        {
            "id": "ts-1",
            "teacher_id": "teacher-1",
            "school_id": "school-1",
            "invitation_status": "accepted",
            "invitation_token": None,
            "invitation_sent_at": "2024-01-01T00:00:00Z",
            "invitation_expires_at": None
        }
    ]
    
    # Mock teachers response
    teachers_data = [
        {
            "id": "teacher-1",
            "name": "John Doe",
            "email": "john@example.com"
        }
    ]
    
    # Setup mocks for two table calls
    mock_table1 = mocker.MagicMock()
    mock_table2 = mocker.MagicMock()
    
    def table_side_effect(table_name):
        if table_name == "teacher_schools":
            mock_table1.select.return_value.eq.return_value.execute.return_value.data = teacher_schools_data
            return mock_table1
        elif table_name == "teachers":
            mock_table2.select.return_value.in_.return_value.execute.return_value.data = teachers_data
            return mock_table2
    
    mock_supabase.table.side_effect = table_side_effect
    
    response = client.get("/api/schools/school-1/teachers")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["teachers"]) == 1
    teacher = data["teachers"][0]
    assert teacher["id"] == "teacher-1"
    assert teacher["name"] == "John Doe"
    assert teacher["email"] == "john@example.com"
    assert teacher["invitation_status"] == "accepted"
    assert teacher["teacher_school_id"] == "ts-1"


def test_get_school_teachers_with_pending_teacher(client, mocker):
    """Test getting teachers including one with pending invitation status"""
    mock_supabase = mocker.patch('app.routers.schools.supabase_admin')
    
    teacher_schools_data = [
        {
            "id": "ts-2",
            "teacher_id": "teacher-2",
            "school_id": "school-1",
            "invitation_status": "pending",
            "invitation_token": "token-123",
            "invitation_sent_at": "2024-01-01T00:00:00Z",
            "invitation_expires_at": "2024-01-08T00:00:00Z"
        }
    ]
    
    teachers_data = [
        {
            "id": "teacher-2",
            "name": "Jane Smith",
            "email": "jane@example.com"
        }
    ]
    
    mock_table1 = mocker.MagicMock()
    mock_table2 = mocker.MagicMock()
    
    def table_side_effect(table_name):
        if table_name == "teacher_schools":
            mock_table1.select.return_value.eq.return_value.execute.return_value.data = teacher_schools_data
            return mock_table1
        elif table_name == "teachers":
            mock_table2.select.return_value.in_.return_value.execute.return_value.data = teachers_data
            return mock_table2
    
    mock_supabase.table.side_effect = table_side_effect
    
    response = client.get("/api/schools/school-1/teachers")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["teachers"]) == 1
    teacher = data["teachers"][0]
    assert teacher["invitation_status"] == "pending"
    assert teacher["invitation_token"] == "token-123"


def test_get_school_teachers_skips_missing_teacher(client, mocker):
    """Test that teachers without a teacher record are skipped"""
    mock_supabase = mocker.patch('app.routers.schools.supabase_admin')
    
    # teacher_schools has a relationship but teacher record doesn't exist
    teacher_schools_data = [
        {
            "id": "ts-3",
            "teacher_id": "missing-teacher",
            "school_id": "school-1",
            "invitation_status": "pending"
        }
    ]
    
    # No teachers returned (teacher record missing)
    teachers_data = []
    
    mock_table1 = mocker.MagicMock()
    mock_table2 = mocker.MagicMock()
    
    def table_side_effect(table_name):
        if table_name == "teacher_schools":
            mock_table1.select.return_value.eq.return_value.execute.return_value.data = teacher_schools_data
            return mock_table1
        elif table_name == "teachers":
            mock_table2.select.return_value.in_.return_value.execute.return_value.data = teachers_data
            return mock_table2
    
    mock_supabase.table.side_effect = table_side_effect
    
    response = client.get("/api/schools/school-1/teachers")
    
    assert response.status_code == 200
    data = response.json()
    # Should skip the missing teacher and return empty list
    assert len(data["teachers"]) == 0

