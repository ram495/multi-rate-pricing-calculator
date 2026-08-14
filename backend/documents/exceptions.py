from rest_framework.exceptions import APIException


class DocumentFinalizedError(APIException):
    status_code = 409
    default_detail = "This document is finalized and cannot be edited."
    default_code = "document_finalized"


def assert_draft(document):
    """Single place the immutability rule lives — call this from every
    endpoint that mutates a document or its line items."""
    if not document.is_draft:
        raise DocumentFinalizedError()
