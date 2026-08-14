from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import assert_draft
from .models import Document, LineItem
from .serializers import DocumentWriteSerializer, LineItemWriteSerializer, document_to_dict


class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentWriteSerializer

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        return Response([document_to_dict(d) for d in self.get_queryset()])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(owner=request.user)
        return Response(document_to_dict(document), status=status.HTTP_201_CREATED)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentWriteSerializer

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        return Response(document_to_dict(self.get_object()))

    def update(self, request, *args, **kwargs):
        document = self.get_object()
        assert_draft(document)
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(document, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(document_to_dict(document))

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        assert_draft(document)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentFinalizeView(APIView):
    def post(self, request, document_id):
        document = get_object_or_404(Document, pk=document_id, owner=request.user)
        assert_draft(document)
        if not document.lines.exists():
            return Response(
                {"detail": "Cannot finalize a document with no line items."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        document.status = Document.Status.FINALIZED
        document.save(update_fields=["status", "updated_at"])
        return Response(document_to_dict(document))


class DocumentScopedMixin:
    """Resolves the parent document (scoped to the current user) for the
    nested line-item endpoints."""

    def get_document(self):
        return get_object_or_404(
            Document, pk=self.kwargs["document_id"], owner=self.request.user
        )


class LineItemListCreateView(DocumentScopedMixin, generics.ListCreateAPIView):
    serializer_class = LineItemWriteSerializer

    def get_queryset(self):
        return LineItem.objects.filter(document_id=self.kwargs["document_id"])

    def list(self, request, *args, **kwargs):
        return Response(document_to_dict(self.get_document()))

    def create(self, request, *args, **kwargs):
        document = self.get_document()
        assert_draft(document)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(document=document)
        return Response(document_to_dict(document), status=status.HTTP_201_CREATED)


class LineItemDetailView(DocumentScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LineItemWriteSerializer

    def get_object(self):
        return get_object_or_404(
            LineItem, pk=self.kwargs["pk"], document=self.get_document()
        )

    def retrieve(self, request, *args, **kwargs):
        return Response(document_to_dict(self.get_object().document))

    def update(self, request, *args, **kwargs):
        line = self.get_object()
        assert_draft(line.document)
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(line, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(document_to_dict(line.document))

    def destroy(self, request, *args, **kwargs):
        line = self.get_object()
        assert_draft(line.document)
        document = line.document
        line.delete()
        return Response(document_to_dict(document))


class ReportSummaryView(APIView):
    def get(self, request):
        date_from_raw = request.query_params.get("date_from")
        date_to_raw = request.query_params.get("date_to")

        date_from = parse_date(date_from_raw) if date_from_raw else None
        date_to = parse_date(date_to_raw) if date_to_raw else None

        if date_from_raw and date_from is None:
            return Response(
                {"date_from": "Invalid date format, expected YYYY-MM-DD."}, status=400
            )
        if date_to_raw and date_to is None:
            return Response(
                {"date_to": "Invalid date format, expected YYYY-MM-DD."}, status=400
            )

        queryset = Document.objects.filter(owner=request.user)
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)

        document_count = 0
        sum_grand_total = Decimal("0.00")
        sum_total_tax = Decimal("0.00")
        sum_total_discount = Decimal("0.00")

        for document in queryset:
            data = document_to_dict(document)
            document_count += 1
            sum_grand_total += data["grand_total"]
            sum_total_tax += data["total_tax"]
            sum_total_discount += data["total_discount"]

        return Response(
            {
                "document_count": document_count,
                "sum_grand_total": sum_grand_total,
                "sum_total_tax": sum_total_tax,
                "sum_total_discount": sum_total_discount,
            }
        )
