import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


def _activity_url(activity_name: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}"


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities_returns_activities(client):
    # Arrange
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert isinstance(activities["Chess Club"]["participants"], list)


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    signup_response = client.post(
        f"{_activity_url(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert signup_response.status_code == 200
    assert email in signup_response.json()["message"]

    activities_response = client.get("/activities")
    assert activities_response.status_code == 200
    activities = activities_response.json()
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    email = "duplicate@student.local"

    # Act
    first_response = client.post(
        f"{_activity_url(activity_name)}/signup",
        params={"email": email},
    )
    second_response = client.post(
        f"{_activity_url(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student is already signed up for this activity"


def test_remove_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    delete_response = client.delete(
        f"{_activity_url(activity_name)}/participants",
        params={"email": email},
    )

    # Assert
    assert delete_response.status_code == 200
    assert email in delete_response.json()["message"]

    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity_name]["participants"]


def test_remove_missing_participant_returns_404(client):
    # Arrange
    activity_name = "Chess Club"
    missing_email = "missing@student.local"

    # Act
    delete_response = client.delete(
        f"{_activity_url(activity_name)}/participants",
        params={"email": missing_email},
    )

    # Assert
    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Participant not found"
