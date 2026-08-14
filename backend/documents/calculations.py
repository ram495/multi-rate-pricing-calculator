"""Pure pricing calculation logic — no Django/DB/HTTP dependency.

Rounding policy: round to the nearest cent (ROUND_HALF_UP) after each derived
step (subtotal, discount amount, tax amount), not just at the end. This keeps
every intermediate number the same as what a user would see on screen, and is
what the assignment's worked example assumes.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

TWO_PLACES = Decimal("0.01")

DISCOUNT_NONE = "none"
DISCOUNT_FIXED = "fixed"
DISCOUNT_PERCENT = "percent"


class DiscountExceedsSubtotalError(ValueError):
    """Raised when a fixed discount is larger than the line it applies to."""


def round_money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class LineInput:
    quantity: Decimal
    unit_price: Decimal
    discount_type: str = DISCOUNT_NONE
    discount_value: Optional[Decimal] = None
    tax_percent: Optional[Decimal] = None


@dataclass(frozen=True)
class LineResult:
    subtotal: Decimal
    discount_amount: Decimal
    after_discount: Decimal
    tax_amount: Decimal
    total: Decimal


@dataclass(frozen=True)
class DocumentResult:
    lines: List[LineResult] = field(default_factory=list)
    subtotal: Decimal = Decimal("0.00")
    total_discount: Decimal = Decimal("0.00")
    total_tax: Decimal = Decimal("0.00")
    grand_total: Decimal = Decimal("0.00")


def calculate_line(line: LineInput) -> LineResult:
    subtotal = round_money(line.quantity * line.unit_price)

    if line.discount_type == DISCOUNT_FIXED:
        discount_amount = round_money(line.discount_value or Decimal("0"))
        if discount_amount > subtotal:
            raise DiscountExceedsSubtotalError(
                f"Fixed discount ({discount_amount}) cannot exceed the line "
                f"subtotal ({subtotal})."
            )
    elif line.discount_type == DISCOUNT_PERCENT:
        percent = line.discount_value or Decimal("0")
        discount_amount = round_money(subtotal * percent / Decimal("100"))
    else:
        discount_amount = Decimal("0.00")

    after_discount = subtotal - discount_amount

    if line.tax_percent:
        tax_amount = round_money(after_discount * line.tax_percent / Decimal("100"))
    else:
        tax_amount = Decimal("0.00")

    total = after_discount + tax_amount

    return LineResult(
        subtotal=subtotal,
        discount_amount=discount_amount,
        after_discount=after_discount,
        tax_amount=tax_amount,
        total=total,
    )


def calculate_document(lines: List[LineInput]) -> DocumentResult:
    results = [calculate_line(line) for line in lines]
    return DocumentResult(
        lines=results,
        subtotal=sum((r.subtotal for r in results), Decimal("0.00")),
        total_discount=sum((r.discount_amount for r in results), Decimal("0.00")),
        total_tax=sum((r.tax_amount for r in results), Decimal("0.00")),
        grand_total=sum((r.total for r in results), Decimal("0.00")),
    )
