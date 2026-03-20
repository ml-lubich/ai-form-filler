"""Orchestration: connect, navigate, extract, plan, fill (application layer).

For LLM-inferred URLs, undetected Chrome, or a single importable entrypoint, prefer
:class:`ai_form_filler.module.AIFormModule`.
"""

from __future__ import annotations

import json
from pathlib import Path

from .bootstrap import prepare_environment
from .browser import CDPConnector, PersistentContextConnector
from .constants import resolved_ollama_model
from .filler import apply_fill_plan
from .form_extract import extract_form_schema
from .llm import get_fill_plan
from .models import FormSchema


def load_user_data(data_source: str) -> str | dict:
    """Load user facts from a file path or inline string.

    - If ``data_source`` points to an existing file, reads UTF-8 text from it.
    - Otherwise treats ``data_source`` as inline content (CLI paste).
    - If the text parses as JSON **object**, returns a ``dict`` (structured facts).
    - If it parses as JSON array/number/string/bool, returns a pretty-printed JSON
      string for the LLM.
    - If parsing fails, returns the **raw text** (plain prose, notes, resume
      snippet, etc.) — same flexibility as pasting unstructured text into a chat.
    """
    path = Path(data_source)
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = data_source

    stripped = text.strip()
    if not stripped:
        return ""

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return text if path.is_file() else data_source

    if isinstance(parsed, dict):
        return parsed
    return json.dumps(parsed, indent=2)


def run(
    url: str,
    user_data: str | dict,
    *,
    use_cdp: bool = True,
    cdp_url: str = "http://localhost:9222",
    user_data_dir: str | None = None,
    channel: str = "chrome",
    model: str | None = None,
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

    m = resolved_ollama_model(model)
    prepare_environment(m, use_playwright=True, need_ollama=True)

    try:
        browser_or_ctx, page = connector.connect()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=10000)

        schema = extract_form_schema(page)
        if not schema.fields:
            return schema

        plan = get_fill_plan(schema, user_data, model=m)
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

