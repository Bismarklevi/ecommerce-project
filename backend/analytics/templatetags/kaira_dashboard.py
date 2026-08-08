"""Presentation-only formatting for the admin dashboard template -- kept as
thin template filters (Phase 15) rather than pre-formatted strings from
dashboard.py, so the service/context layer stays testable against real
numeric values.
"""
from django import template

register = template.Library()


@register.filter
def ghs(value):
    """GH\u20b5 12,345.67 -- never crashes on None/empty (Phase 7: zero-value
    cases must not error)."""
    try:
        return f"GH\u20b5 {float(value):,.2f}"
    except (TypeError, ValueError):
        return "GH\u20b5 0.00"


@register.filter
def pct_change(value):
    """None means "no baseline to compare against" (see
    analytics.services.percent_change) -- rendered as an em dash rather than
    a misleading 0% or +inf%."""
    if value is None:
        return "\u2014"
    arrow = "\u2191" if value >= 0 else "\u2193"
    return f"{arrow} {abs(value):.1f}%"


@register.filter
def pct_change_tone(value):
    if value is None:
        return "neutral"
    return "positive" if value >= 0 else "negative"
