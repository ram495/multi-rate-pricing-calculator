import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="lifecycle@test.com", password="testpass123")


@pytest.fixture
def client(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def draft_document(client):
    resp = client.post(
        "/api/documents/",
        {"title": "Test doc", "customer": "Test customer", "issue_date": "2026-01-01"},
        format="json",
    )
    assert resp.status_code == 201
    return resp.data


@pytest.fixture
def line_on_document(client, draft_document):
    resp = client.post(
        f"/api/documents/{draft_document['id']}/lines/",
        {
            "description": "Widget",
            "quantity": "1",
            "unit_price": "100.00",
            "discount_type": "none",
        },
        format="json",
    )
    assert resp.status_code == 201
    return resp.data["lines"][0]
