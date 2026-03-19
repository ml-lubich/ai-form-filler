"""Orchestration: connect, navigate, extract, plan, fill (application layer).

For LLM-inferred URLs, undetected Chrome, or a single importable entrypoint, prefer
:class:`ai_form_filler.module.AIFormModule`.
"""

from __future__ import annotations

import json
from pathlib import Path

from .browser import CDPConnector, PersistentContextConnector
from .filler import apply_fill_plan
from .form_extract import extract_form_schema
from .llm import get_fill_plan
from .models import FormSchema


def load_user_data(data_source: str) -> str | dict:
    """Load user data from JSON file path or inline JSON string."""
    path = Path(data_source)
    if path.is_file():
        text = path.read_text()
        return json.loads(text)
    return json.loads(data_source)


def run(
    url: str,
    user_data: str | dict,
    *,
    use_cdp: bool = True,
    cdp_url: str = "http://localhost:9222",
    user_data_dir: str | None = None,
    channel: str = "chrome",
    model: str = "llama3.2",
    submit: bool = False,
) -> FormSchema:
    """
    Run the form-fill pipeline: connect to browser, go to URL, extract form,
    get fill plan from Ollama, apply it. Returns the extracted schema.
    """
    if use_cdp:
        connector = CDPConnector(cdp_url=cdp_url)
    elif user_data_dir:
        connector = PersistentContextConnector(
            user_data_dir=user_data_dir,
            channel=channel,
            headless=False,
        )
    else:
        raise ValueError("Either use_cdp=True or user_data_dir must be set")

    try:
        browser_or_ctx, page = connector.connect()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=10000)

        schema = extract_form_schema(page)
        if not schema.fields:
            return schema

        plan = get_fill_plan(schema, user_data, model=model)
        apply_fill_plan(page, schema, plan)

        if submit:
            submit_btn = page.locator(
                'input[type="submit"], button[type="submit"], button:has-text("Submit"), '
                'button:has-text("Send"), [type="submit"]'
            ).first
            if submit_btn.count() > 0:
                submit_btn.click()

        return schema
    finally:
        if hasattr(connector, "close"):
            connector.close()

