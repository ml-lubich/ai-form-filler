"""Unit tests for schema building from raw browser payloads (no Playwright)."""

from ai_form_filler.form_extract import schema_from_raw_fields


def test_schema_from_raw_fields_empty() -> None:
    schema = schema_from_raw_fields([])
    assert schema.fields == []


def test_schema_from_raw_fields_one_field() -> None:
    raw = [
        {
            "key": "email",
            "tag": "input",
            "input_type": "email",
            "name": "email",
            "id": "e1",
            "placeholder": "you@example.com",
            "label_text": "Email",
            "options": [],
        },
    ]
    schema = schema_from_raw_fields(raw)
    assert len(schema.fields) == 1
    f = schema.fields[0]
    assert f.key == "email"
    assert f.input_type == "email"
    assert f.label_text == "Email"


def test_schema_from_raw_fields_select_options() -> None:
    raw = [
        {
            "key": "country",
            "tag": "select",
            "input_type": "select-one",
            "name": "country",
            "id": None,
            "placeholder": None,
            "label_text": None,
            "options": [["us", "US"], ["uk", "UK"]],
        },
    ]
    schema = schema_from_raw_fields(raw)
    assert schema.fields[0].options == [("us", "US"), ("uk", "UK")]
