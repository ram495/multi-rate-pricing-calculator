"""Stretch goal: duplicate a finalized document into a new draft."""

import pytest

# user/client/draft_document/line_on_document fixtures come from conftest.py


@pytest.mark.django_db
class TestDuplicate:
    def test_duplicates_a_finalized_document_into_a_new_draft(
        self, client, draft_document, line_on_document
    ):
        finalize_resp = client.post(f"/api/documents/{draft_document['id']}/finalize/")
        assert finalize_resp.status_code == 200

        resp = client.post(f"/api/documents/{draft_document['id']}/duplicate/")
        assert resp.status_code == 201

        copy = resp.data
        assert copy["id"] != draft_document["id"]
        assert copy["status"] == "draft"
        assert copy["title"] == "Test doc (copy)"
        assert copy["customer"] == draft_document["customer"]
        assert copy["issue_date"] == draft_document["issue_date"]
        assert len(copy["lines"]) == 1
        assert copy["lines"][0]["description"] == "Widget"
        assert copy["grand_total"] == 100
        assert copy["grand_total"] == finalize_resp.data["grand_total"]

    def test_copy_is_independently_editable(self, client, draft_document, line_on_document):
        client.post(f"/api/documents/{draft_document['id']}/finalize/")
        copy = client.post(f"/api/documents/{draft_document['id']}/duplicate/").data

        resp = client.patch(
            f"/api/documents/{copy['id']}/", {"title": "Edited copy"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["title"] == "Edited copy"

        # original is untouched and still finalized
        original = client.get(f"/api/documents/{draft_document['id']}/").data
        assert original["title"] == "Test doc"
        assert original["status"] == "finalized"

    def test_source_document_is_unaffected(self, client, draft_document, line_on_document):
        client.post(f"/api/documents/{draft_document['id']}/finalize/")
        client.post(f"/api/documents/{draft_document['id']}/duplicate/")

        original = client.get(f"/api/documents/{draft_document['id']}/").data
        assert len(original["lines"]) == 1
        assert original["status"] == "finalized"

    def test_duplicating_a_draft_is_rejected(self, client, draft_document, line_on_document):
        resp = client.post(f"/api/documents/{draft_document['id']}/duplicate/")
        assert resp.status_code == 400
