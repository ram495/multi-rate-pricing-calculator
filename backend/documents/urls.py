from django.urls import path

from .views import (
    DocumentDetailView,
    DocumentFinalizeView,
    DocumentListCreateView,
    LineItemDetailView,
    LineItemListCreateView,
    ReportSummaryView,
)

urlpatterns = [
    path("documents/", DocumentListCreateView.as_view(), name="document-list-create"),
    path("documents/<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
    path(
        "documents/<int:document_id>/finalize/",
        DocumentFinalizeView.as_view(),
        name="document-finalize",
    ),
    path(
        "documents/<int:document_id>/lines/",
        LineItemListCreateView.as_view(),
        name="line-list-create",
    ),
    path(
        "documents/<int:document_id>/lines/<int:pk>/",
        LineItemDetailView.as_view(),
        name="line-detail",
    ),
    path("reports/summary/", ReportSummaryView.as_view(), name="report-summary"),
]
