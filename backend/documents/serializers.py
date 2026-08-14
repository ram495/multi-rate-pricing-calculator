from rest_framework import serializers

from .calculations import (
    DiscountExceedsSubtotalError,
    LineInput,
    calculate_document,
    calculate_line,
)
from .models import Document, LineItem


class DocumentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["title", "customer", "issue_date"]
        # status is never client-settable — only the finalize endpoint changes it.


class LineItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = [
            "id",
            "description",
            "quantity",
            "unit_price",
            "discount_type",
            "discount_value",
            "tax_percent",
            "sort_order",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        def current(field, default=None):
            if field in attrs:
                return attrs[field]
            if self.instance is not None:
                return getattr(self.instance, field)
            return default

        quantity = current("quantity")
        unit_price = current("unit_price")
        discount_type = current("discount_type", LineItem.DiscountType.NONE)
        discount_value = current("discount_value")
        tax_percent = current("tax_percent")

        if discount_type == LineItem.DiscountType.PERCENT:
            if discount_value is None or not (0 <= discount_value <= 100):
                raise serializers.ValidationError(
                    {"discount_value": 'Percent discount is required and must be between 0 and 100 when discount_type is "percent".'}
                )
        elif discount_type == LineItem.DiscountType.FIXED:
            if discount_value is None or discount_value < 0:
                raise serializers.ValidationError(
                    {"discount_value": 'A discount amount ≥ 0 is required when discount_type is "fixed".'}
                )
        elif discount_value not in (None, 0):
            raise serializers.ValidationError(
                {"discount_value": 'discount_value must be empty when discount_type is "none".'}
            )

        if tax_percent is not None and not (0 <= tax_percent <= 100):
            raise serializers.ValidationError(
                {"tax_percent": "Tax percent must be between 0 and 100."}
            )

        # Reuse the calc module itself for the "fixed discount can't exceed
        # the line subtotal" rule, so that constraint lives in one place.
        try:
            calculate_line(
                LineInput(
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    tax_percent=tax_percent,
                )
            )
        except DiscountExceedsSubtotalError as exc:
            raise serializers.ValidationError({"discount_value": str(exc)})

        return attrs


def document_to_dict(document: Document) -> dict:
    """The single place a document's totals are computed for API output —
    reused by every endpoint that returns a document, so the calc module is
    always the source of truth and nothing is read from a stored total."""
    lines = list(document.lines.all())
    line_inputs = [
        LineInput(
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_type=line.discount_type,
            discount_value=line.discount_value,
            tax_percent=line.tax_percent,
        )
        for line in lines
    ]
    result = calculate_document(line_inputs)

    line_payload = [
        {
            "id": line.id,
            "description": line.description,
            "quantity": line.quantity,
            "unit_price": line.unit_price,
            "discount_type": line.discount_type,
            "discount_value": line.discount_value,
            "tax_percent": line.tax_percent,
            "sort_order": line.sort_order,
            "subtotal": computed.subtotal,
            "discount_amount": computed.discount_amount,
            "after_discount": computed.after_discount,
            "tax_amount": computed.tax_amount,
            "total": computed.total,
        }
        for line, computed in zip(lines, result.lines)
    ]

    return {
        "id": document.id,
        "title": document.title,
        "customer": document.customer,
        "issue_date": document.issue_date,
        "status": document.status,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "lines": line_payload,
        "subtotal": result.subtotal,
        "total_discount": result.total_discount,
        "total_tax": result.total_tax,
        "grand_total": result.grand_total,
    }
