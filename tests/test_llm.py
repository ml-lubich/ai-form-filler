"""Unit tests for LLM prompt building and response parsing."""

import json

import pytest

from ai_form_filler.llm import build_mapping_prompt, parse_fill_plan_from_response
from ai_form_filler.models import FillPlan, FormField, FormSchema


def test_build_mapping_prompt_includes_schema_and_data() -> None:
    schema = FormSchema(
        fields=[
            FormField(
                key="email",
                tag="input",
                input_type="email",
                name="email",
                id="email",
                placeholder="Your email",
                label_text="Email",
                options=[],
            ),
        ]
    )
    data = {"email": "a@b.com"}
    prompt = build_mapping_prompt(schema, data)
    assert "key=email" in prompt
    assert "a@b.com" in prompt
    assert "Form schema" in prompt or "form" in prompt.lower()


def test_parse_fill_plan_from_response_raw_json() -> None:
    raw = '{"email": "a@b.com", "name": "Alice"}'
    plan = parse_fill_plan_from_response(raw)
    assert len(plan.actions) == 2
    keys = {a.field_key for a in plan.actions}
    assert keys == {"email", "name"}
    values = {a.field_key: a.value for a in plan.actions}
    assert values["email"] == "a@b.com"
    assert values["name"] == "Alice"


def test_parse_fill_plan_from_response_markdown_fence() -> None:
    raw = '```json\n{"agree": true}\n```'
    plan = parse_fill_plan_from_response(raw)
    assert len(plan.actions) == 1
    assert plan.actions[0].field_key == "agree"
    assert plan.actions[0].value is True


def test_parse_fill_plan_from_response_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse_fill_plan_from_response("not json at all")
    with pytest.raises(ValueError):
        parse_fill_plan_from_response("[1,2,3]")  # must be object
