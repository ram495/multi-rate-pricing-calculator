from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        FINALIZED = "finalized", "Finalized"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents"
    )
    title = models.CharField(max_length=255)
    customer = models.CharField(max_length=255)
    issue_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.customer})"

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT


class LineItem(models.Model):
    class DiscountType(models.TextChoices):
        NONE = "none", "None"
        FIXED = "fixed", "Fixed amount"
        PERCENT = "percent", "Percent"

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="lines"
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    discount_type = models.CharField(
        max_length=10, choices=DiscountType.choices, default=DiscountType.NONE
    )
    discount_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    tax_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.description} x{self.quantity}"
