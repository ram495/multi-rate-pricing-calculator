from decimal import Decimal

import pytest

from documents.calculations import (
    DISCOUNT_FIXED,
    DISCOUNT_NONE,
    DISCOUNT_PERCENT,
    DiscountExceedsSubtotalError,
    LineInput,
    calculate_document,
    calculate_line,
    round_money,
)


def test_round_money_half_up():
    # ROUND_HALF_UP, not Python's default banker's rounding (ROUND_HALF_EVEN):
    # 2.005 -> 2.01 (HALF_EVEN would give 2.00, since 0 is even)
    assert round_money(Decimal("2.005")) == Decimal("2.01")
    assert round_money(Decimal("0.125")) == Decimal("0.13")


def test_assignment_sample_document():
    """Exact numbers from the assignment's worked example."""
    widget_a = LineInput(
        quantity=Decimal("2"),
        unit_price=Decimal("100.00"),
        discount_type=DISCOUNT_PERCENT,
        discount_value=Decimal("10"),
        tax_percent=Decimal("5"),
    )
    widget_b = LineInput(
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        discount_type=DISCOUNT_NONE,
        tax_percent=Decimal("5"),
    )
    service_fee = LineInput(
        quantity=Decimal("1"),
        unit_price=Decimal("200.00"),
        discount_type=DISCOUNT_FIXED,
        discount_value=Decimal("20"),
    )

    result = calculate_document([widget_a, widget_b, service_fee])

    a, b, fee = result.lines

    # Widget A: 200.00 subtotal, 20.00 discount, 180.00 after discount, 9.00 tax, 189.00 total
    assert a.subtotal == Decimal("200.00")
    assert a.discount_amount == Decimal("20.00")
    assert a.after_discount == Decimal("180.00")
    assert a.tax_amount == Decimal("9.00")
    assert a.total == Decimal("189.00")

    # Widget B: 50.00 subtotal, 0 discount, 50.00 after discount, 2.50 tax, 52.50 total
    assert b.subtotal == Decimal("50.00")
    assert b.discount_amount == Decimal("0.00")
    assert b.after_discount == Decimal("50.00")
    assert b.tax_amount == Decimal("2.50")
    assert b.total == Decimal("52.50")

    # Service fee: 200.00 subtotal, 20.00 discount, 180.00 after discount, 0 tax, 180.00 total
    assert fee.subtotal == Decimal("200.00")
    assert fee.discount_amount == Decimal("20.00")
    assert fee.after_discount == Decimal("180.00")
    assert fee.tax_amount == Decimal("0.00")
    assert fee.total == Decimal("180.00")

    # Document totals
    assert result.subtotal == Decimal("450.00")
    assert result.total_discount == Decimal("40.00")
    assert result.total_tax == Decimal("11.50")
    assert result.grand_total == Decimal("421.50")


def test_percent_discount_only():
    line = LineInput(
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        discount_type=DISCOUNT_PERCENT,
        discount_value=Decimal("25"),
    )
    result = calculate_line(line)
    assert result.subtotal == Decimal("100.00")
    assert result.discount_amount == Decimal("25.00")
    assert result.after_discount == Decimal("75.00")
    assert result.tax_amount == Decimal("0.00")
    assert result.total == Decimal("75.00")


def test_fixed_discount_only():
    line = LineInput(
        quantity=Decimal("3"),
        unit_price=Decimal("10.00"),
        discount_type=DISCOUNT_FIXED,
        discount_value=Decimal("5"),
    )
    result = calculate_line(line)
    assert result.subtotal == Decimal("30.00")
    assert result.discount_amount == Decimal("5.00")
    assert result.after_discount == Decimal("25.00")
    assert result.total == Decimal("25.00")


def test_no_discount_no_tax():
    line = LineInput(quantity=Decimal("2"), unit_price=Decimal("19.99"))
    result = calculate_line(line)
    assert result.subtotal == Decimal("39.98")
    assert result.discount_amount == Decimal("0.00")
    assert result.tax_amount == Decimal("0.00")
    assert result.total == Decimal("39.98")


def test_fractional_quantity_rounds_at_subtotal():
    # 3.15 * 10.10 = 31.815 -> rounds to 31.82 under ROUND_HALF_UP
    line = LineInput(quantity=Decimal("3.15"), unit_price=Decimal("10.10"))
    result = calculate_line(line)
    assert result.subtotal == Decimal("31.82")


def test_fixed_discount_exceeding_subtotal_is_rejected():
    line = LineInput(
        quantity=Decimal("1"),
        unit_price=Decimal("10.00"),
        discount_type=DISCOUNT_FIXED,
        discount_value=Decimal("15.00"),
    )
    with pytest.raises(DiscountExceedsSubtotalError):
        calculate_line(line)


def test_tax_is_applied_after_discount_not_before():
    # If tax were applied before discount, tax would be 5% of 200 = 10.00, not 9.00.
    line = LineInput(
        quantity=Decimal("1"),
        unit_price=Decimal("200.00"),
        discount_type=DISCOUNT_PERCENT,
        discount_value=Decimal("10"),
        tax_percent=Decimal("5"),
    )
    result = calculate_line(line)
    assert result.tax_amount == Decimal("9.00")
