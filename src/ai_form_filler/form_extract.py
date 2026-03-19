"""Extract form field schema from a page using Playwright or Selenium (application layer)."""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Page

from .form_fields_js import PLAYWRIGHT_EXTRACT_JS, SELENIUM_EXTRACT_JS
from .models import FormField, FormSchema


def schema_from_raw_fields(fields_raw: list[dict[str, Any]]) -> FormSchema:
    """Build FormSchema from raw list returned by browser JS."""
    fields = []
    for r in fields_raw:
        f = FormField(
            key=r["key"],
            tag=r["tag"],
            input_type=r["input_type"],
            name=r.get("name"),
            id=r.get("id"),
            placeholder=r.get("placeholder"),
            label_text=r.get("label_text"),
            options=[tuple(o) for o in r.get("options", [])],
        )
        fields.append(f)
    return FormSchema(fields=fields)


def extract_form_schema(page: Page) -> FormSchema:
    """Extract all fillable form fields from the current page (Playwright)."""
    fields_raw = page.evaluate(PLAYWRIGHT_EXTRACT_JS)
    return schema_from_raw_fields(fields_raw)


def extract_form_schema_selenium(driver: object) -> FormSchema:
    """Extract form fields using Selenium WebDriver (undetected-chromedriver, etc.)."""
    fields_raw = driver.execute_script(SELENIUM_EXTRACT_JS)
    if not isinstance(fields_raw, list):
        raise RuntimeError("Form extraction script did not return a list")
    return schema_from_raw_fields(fields_raw)
