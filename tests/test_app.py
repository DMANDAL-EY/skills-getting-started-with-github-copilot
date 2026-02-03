import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to known state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for intramural and inter-school games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": []
        }
    })


def test_root_redirect(client):
    """Test that root path redirects to index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Basketball Team" in data
    assert len(data["Chess Club"]["participants"]) == 2


def test_signup_for_activity(client):
    """Test signing up for an activity"""
    response = client.post(
        "/activities/Basketball Team/signup?email=john@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    updated_activities = activities_response.json()
    assert "john@mergington.edu" in updated_activities["Basketball Team"]["participants"]


def test_signup_already_registered(client):
    """Test signing up for an activity when already registered"""
    response = client.post(
        "/activities/Chess Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"]


def test_signup_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=john@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_unregister_from_activity(client):
    """Test unregistering from an activity"""
    # First verify participant is registered
    activities_before = client.get("/activities").json()
    assert "michael@mergington.edu" in activities_before["Chess Club"]["participants"]
    
    # Unregister
    response = client.delete(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered" in data["message"]
    
    # Verify participant was removed
    activities_after = client.get("/activities").json()
    assert "michael@mergington.edu" not in activities_after["Chess Club"]["participants"]


def test_unregister_not_registered(client):
    """Test unregistering from an activity when not registered"""
    response = client.delete(
        "/activities/Basketball Team/unregister?email=john@mergington.edu"
    )
    assert response.status_code == 400
    data = response.json()
    assert "not registered" in data["detail"]


def test_unregister_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent Club/unregister?email=john@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_signup_multiple_participants(client):
    """Test signing up multiple participants for the same activity"""
    # Sign up first participant
    client.post("/activities/Basketball Team/signup?email=player1@mergington.edu")
    # Sign up second participant
    client.post("/activities/Basketball Team/signup?email=player2@mergington.edu")
    
    # Verify both are registered
    activities_response = client.get("/activities")
    participants = activities_response.json()["Basketball Team"]["participants"]
    assert "player1@mergington.edu" in participants
    assert "player2@mergington.edu" in participants
    assert len(participants) == 2
