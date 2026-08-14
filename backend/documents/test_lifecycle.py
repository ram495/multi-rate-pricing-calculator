"""API-level tests for the draft/finalized lifecycle guard.

documents/test_calculations.py covers the calc module; this file covers the
thing that actually enforces immutability over HTTP — assert_draft(), wired
into every mutating endpoint (documents/exceptions.py, documents/views.py).
"""

import pytest

# user/client/draft_document/line_on_document fixtures come from conftest.py


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
class TestQuantityAndPriceValidation:
    """Stretch goal: 'reject finalize if any line has quantity <= 0 or
    negative prices'. Satisfied by construction rather than a check at
    finalize time — the model validators (MinValueValidator) make it
    impossible for such a line to be saved at all, draft or otherwise, so
    finalize can never encounter one."""

    def test_zero_quantity_rejected_at_creation(self, client, draft_document):
        resp = client.post(
            f"/api/documents/{draft_document['id']}/lines/",
            {"description": "Bad", "quantity": "0", "unit_price": "10.00", "discount_type": "none"},
            format="json",
        )
        assert resp.status_code == 400
        assert "quantity" in resp.data

    def test_negative_quantity_rejected_at_creation(self, client, draft_document):
        resp = client.post(
            f"/api/documents/{draft_document['id']}/lines/",
            {"description": "Bad", "quantity": "-1", "unit_price": "10.00", "discount_type": "none"},
            format="json",
        )
        assert resp.status_code == 400
        assert "quantity" in resp.data

    def test_negative_unit_price_rejected_at_creation(self, client, draft_document):
        resp = client.post(
            f"/api/documents/{draft_document['id']}/lines/",
            {"description": "Bad", "quantity": "1", "unit_price": "-5.00", "discount_type": "none"},
            format="json",
        )
        assert resp.status_code == 400
        assert "unit_price" in resp.data


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
