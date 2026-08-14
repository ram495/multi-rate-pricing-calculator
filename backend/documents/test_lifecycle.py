"""API-level tests for the draft/finalized lifecycle guard.

documents/test_calculations.py covers the calc module; this file covers the
thing that actually enforces immutability over HTTP — assert_draft(), wired
into every mutating endpoint (documents/exceptions.py, documents/views.py).
"""

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


@pytest.mark.django_db
class TestDraftIsEditable:
    def test_can_add_line(self, client, draft_document):
        resp = client.post(
            f"/api/documents/{draft_document['id']}/lines/",
            {"description": "Line", "quantity": "1", "unit_price": "10.00", "discount_type": "none"},
            format="json",
        )
        assert resp.status_code == 201

    def test_can_edit_line(self, client, draft_document, line_on_document):
        resp = client.patch(
            f"/api/documents/{draft_document['id']}/lines/{line_on_document['id']}/",
            {"description": "Updated"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["lines"][0]["description"] == "Updated"

    def test_can_delete_line(self, client, draft_document, line_on_document):
        resp = client.delete(f"/api/documents/{draft_document['id']}/lines/{line_on_document['id']}/")
        assert resp.status_code == 200
        assert resp.data["lines"] == []

    def test_can_edit_metadata(self, client, draft_document):
        resp = client.patch(
            f"/api/documents/{draft_document['id']}/", {"title": "Renamed"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["title"] == "Renamed"


@pytest.mark.django_db
class TestFinalize:
    def test_requires_at_least_one_line(self, client, draft_document):
        resp = client.post(f"/api/documents/{draft_document['id']}/finalize/")
        assert resp.status_code == 400

    def test_succeeds_with_a_line(self, client, draft_document, line_on_document):
        resp = client.post(f"/api/documents/{draft_document['id']}/finalize/")
        assert resp.status_code == 200
        assert resp.data["status"] == "finalized"

    def test_refinalizing_is_rejected(self, client, draft_document, line_on_document):
        client.post(f"/api/documents/{draft_document['id']}/finalize/")
        resp = client.post(f"/api/documents/{draft_document['id']}/finalize/")
        assert resp.status_code == 409


@pytest.mark.django_db
class TestFinalizedIsImmutable:
    @pytest.fixture(autouse=True)
    def _finalize(self, client, draft_document, line_on_document):
        resp = client.post(f"/api/documents/{draft_document['id']}/finalize/")
        assert resp.status_code == 200
        self.document_id = draft_document["id"]
        self.line_id = line_on_document["id"]

    def test_metadata_edit_rejected(self, client):
        resp = client.patch(f"/api/documents/{self.document_id}/", {"title": "x"}, format="json")
        assert resp.status_code == 409
        assert resp.data["detail"] == "This document is finalized and cannot be edited."

    def test_document_delete_rejected(self, client):
        resp = client.delete(f"/api/documents/{self.document_id}/")
        assert resp.status_code == 409

    def test_add_line_rejected(self, client):
        resp = client.post(
            f"/api/documents/{self.document_id}/lines/",
            {"description": "New", "quantity": "1", "unit_price": "1.00", "discount_type": "none"},
            format="json",
        )
        assert resp.status_code == 409

    def test_edit_line_rejected(self, client):
        resp = client.patch(
            f"/api/documents/{self.document_id}/lines/{self.line_id}/",
            {"description": "changed"},
            format="json",
        )
        assert resp.status_code == 409

    def test_delete_line_rejected(self, client):
        resp = client.delete(f"/api/documents/{self.document_id}/lines/{self.line_id}/")
        assert resp.status_code == 409
