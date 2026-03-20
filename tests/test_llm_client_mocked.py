"""Ollama client path with ``chat`` mocked: no live LLM, any model name.

These tests stay **domain-agnostic** (opaque field keys) and only assert that
prompt → fake JSON → parsed plan / navigation behaves as wired.
"""

from __future__ import annotations

import pytest

from ai_form_filler.llm import get_fill_plan, infer_navigation_intent
from ai_form_filler.models import FormField, FormSchema


def test_get_fill_plan_mocked_chat_opaque_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = FormSchema(
        fields=[
            FormField(
                key="fld_a",
                tag="input",
                input_type="text",
                name="fld_a",
                id=None,
                placeholder=None,
                label_text=None,
                options=[],
            ),
        ]
    )

    def fake_chat(*_args: object, **_kwargs: object) -> dict:
        return {"message": {"content": '{"fld_a": "synthetic-value"}'}}

    monkeypatch.setattr("ai_form_filler.llm.chat", fake_chat)
    plan = get_fill_plan(schema, {"note": "ignored by mock"}, model="not-a-real-model")
    assert len(plan.actions) == 1
    assert plan.actions[0].field_key == "fld_a"
    assert plan.actions[0].value == "synthetic-value"


def test_infer_navigation_intent_mocked_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_chat(*_args: object, **_kwargs: object) -> dict:
        return {
            "message": {
                "content": '{"url": "https://example.invalid/path", "reason": "test"}',
            },
        }

    monkeypatch.setattr("ai_form_filler.llm.chat", fake_chat)
    intent = infer_navigation_intent(
        "open some page",
        hints="hints ignored by mock",
        current_url="https://elsewhere.invalid/",
        model="placeholder-model",
    )
    assert intent.url == "https://example.invalid/path"
    assert "test" in intent.reason
