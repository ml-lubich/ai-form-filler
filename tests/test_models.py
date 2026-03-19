"""Unit tests for domain models."""

from ai_form_filler.models import FormField, FormSchema


def test_form_schema_get_field_by_key() -> None:
    f1 = FormField(
        key="a",
        tag="input",
        input_type="text",
        name="a",
        id=None,
        placeholder=None,
        label_text=None,
        options=[],
    )
    f2 = FormField(
        key="b",
        tag="input",
        input_type="email",
        name="b",
        id=None,
        placeholder=None,
        label_text=None,
        options=[],
    )
    schema = FormSchema(fields=[f1, f2])
    assert schema.get_field_by_key("a") is f1
    assert schema.get_field_by_key("b") is f2
    assert schema.get_field_by_key("c") is None


def test_form_schema_to_llm_description() -> None:
    schema = FormSchema(
        fields=[
            FormField(
                key="x",
                tag="input",
                input_type="text",
                name="x",
                id="x",
                placeholder="Enter x",
                label_text="X",
                options=[],
            ),
        ]
    )
    desc = schema.to_llm_description()
    assert "key=x" in desc
    assert "name=" in desc
    assert "placeholder=" in desc
    assert "label=" in desc
