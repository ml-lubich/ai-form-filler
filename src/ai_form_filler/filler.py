"""Execute fill plan on page (application layer)."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from .models import FillAction, FillPlan, FormField, FormSchema


def _locator_for_field(page: Page, field: FormField) -> Locator | None:
    """Return a Playwright locator for the field. Prefer id, then name, then label."""
    if field.id:
        return page.locator(f"#{field.id}").first
    if field.name:
        return page.locator(f'[name="{field.name}"]').first
    if field.label_text:
        return page.get_by_label(field.label_text, exact=False).first
    return None


def apply_fill_action(
    page: Page,
    schema: FormSchema,
    action: FillAction,
) -> None:
    """Apply a single fill action to the page."""
    field = schema.get_field_by_key(action.field_key)
    if not field:
        return
    value = action.value
    loc = _locator_for_field(page, field)
    if not loc:
        return

    if field.input_type == "radio":
        if field.name:
            loc = page.locator(
                f'input[type="radio"][name="{field.name}"][value="{value}"]'
            ).first
        if value in (True, "true", "1", "yes", "on") or value:
            loc.check()
        return
    if field.input_type == "checkbox":
        if value in (True, "true", "1", "yes", "on"):
            loc.check()
        else:
            loc.uncheck()
        return
    if field.tag == "select":
        loc.select_option(str(value))
        return
    # text, email, password, textarea, etc.
    loc.fill(str(value))


def apply_fill_plan(
    page: Page,
    schema: FormSchema,
    plan: FillPlan,
) -> None:
    """Apply the full fill plan to the page."""
    for action in plan.actions:
        apply_fill_action(page, schema, action)
