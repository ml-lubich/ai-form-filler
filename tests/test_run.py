"""Tests for run orchestration helpers."""

import json
from pathlib import Path

from ai_form_filler.run import load_user_data


def test_load_user_data_plain_text_file(tmp_path: Path) -> None:
    p = tmp_path / "notes.txt"
    p.write_text("Jane Doe\nEmail: jane@example.com\nWorks at Acme", encoding="utf-8")
    out = load_user_data(str(p))
    assert out == "Jane Doe\nEmail: jane@example.com\nWorks at Acme"


def test_load_user_data_json_object_file(tmp_path: Path) -> None:
    p = tmp_path / "data.json"
    payload = {"email": "a@b.com", "name": "A"}
    p.write_text(json.dumps(payload), encoding="utf-8")
    out = load_user_data(str(p))
    assert out == payload


def test_load_user_data_json_array_file_becomes_string(tmp_path: Path) -> None:
    p = tmp_path / "list.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    out = load_user_data(str(p))
    assert isinstance(out, str)
    assert json.loads(out) == [1, 2, 3]


def test_load_user_data_inline_json_object() -> None:
    out = load_user_data('  {"x": 1}  ')
    assert out == {"x": 1}


def test_load_user_data_inline_plain_text() -> None:
    out = load_user_data("Just some pasted text, no JSON.")
    assert out == "Just some pasted text, no JSON."


def test_load_user_data_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.txt"
    p.write_text("   \n", encoding="utf-8")
    assert load_user_data(str(p)) == ""
