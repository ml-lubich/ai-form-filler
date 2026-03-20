"""Browser integration: extract schema from arbitrary HTML, apply a **mock** fill plan.

No Ollama, no fixed domain vocabulary — field names are opaque. This is the same
shape as production (extract → plan → apply) with the LLM step replaced by a
deterministic :class:`FillPlan`.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import sync_playwright

from ai_form_filler.filler import apply_fill_plan
from ai_form_filler.form_extract import schema_from_raw_fields
from ai_form_filler.form_fields_js import PLAYWRIGHT_EXTRACT_JS
from ai_form_filler.models import FillAction, FillPlan


def _html_form_variant_a() -> str:
    return """
    <!DOCTYPE html><html><body>
      <form>
        <input type="text" name="opaque_q1" />
        <input type="checkbox" name="opaque_q2" id="opaque_q2" />
        <select name="opaque_q3">
          <option value="p">P</option>
          <option value="q">Q</option>
        </select>
      </form>
    </body></html>
    """


def _html_form_variant_b() -> str:
    """Different naming/layout; same pipeline."""
    return """
    <!DOCTYPE html><html><body>
      <form id="f">
        <textarea name="t_msg"></textarea>
        <input type="checkbox" name="t_agree" id="t_agree" />
        <select name="t_pick"><option value="1">One</option><option value="2">Two</option></select>
      </form>
    </body></html>
    """


@pytest.mark.integration
@pytest.mark.parametrize(
    ("html", "actions"),
    [
        (
            _html_form_variant_a(),
            [
                FillAction("opaque_q1", "hello-world"),
                FillAction("opaque_q2", True),
                FillAction("opaque_q3", "q"),
            ],
        ),
        (
            _html_form_variant_b(),
            [
                FillAction("t_msg", "line1\nline2"),
                FillAction("t_agree", True),
                FillAction("t_pick", "2"),
            ],
        ),
    ],
)
def test_extract_apply_fill_plan_without_llm(html: str, actions: list[FillAction]) -> None:
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as exc:  # pragma: no cover - CI may lack browsers
            pytest.skip(f"Chromium launch failed (install browsers: playwright install chromium): {exc}")
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="domcontentloaded")
            raw = page.evaluate(PLAYWRIGHT_EXTRACT_JS)
            assert isinstance(raw, list)
            schema = schema_from_raw_fields(raw)
            keys = {f.key for f in schema.fields}
            for a in actions:
                assert a.field_key in keys, f"missing key {a.field_key} in {keys}"

            apply_fill_plan(page, schema, FillPlan(actions=actions))

            for a in actions:
                el = page.locator(f'[name="{a.field_key}"]').first
                if a.field_key in ("opaque_q2", "t_agree"):
                    assert el.is_checked()
                elif a.field_key in ("opaque_q3", "t_pick"):
                    val = el.evaluate("e => e.value")
                    assert val == str(a.value)
                else:
                    val = el.input_value()
                    assert val == str(a.value)
        finally:
            browser.close()
