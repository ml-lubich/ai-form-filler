"""Tests for env_config.parse_env_bool."""

from __future__ import annotations

import pytest

from ai_form_filler.env_config import parse_env_bool


def test_parse_env_bool_default_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_FORM_FILLER_TEST_FLAG", raising=False)
    assert parse_env_bool("AI_FORM_FILLER_TEST_FLAG", default=True) is True
    assert parse_env_bool("AI_FORM_FILLER_TEST_FLAG", default=False) is False


def test_parse_env_bool_true_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_FORM_FILLER_TEST_FLAG", "true")
    assert parse_env_bool("AI_FORM_FILLER_TEST_FLAG", default=False) is True
    monkeypatch.setenv("AI_FORM_FILLER_TEST_FLAG", "FALSE")
    assert parse_env_bool("AI_FORM_FILLER_TEST_FLAG", default=True) is False


def test_parse_env_bool_empty_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_FORM_FILLER_TEST_FLAG", "  ")
    assert parse_env_bool("AI_FORM_FILLER_TEST_FLAG", default=False) is False


def test_parse_env_bool_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_FORM_FILLER_TEST_FLAG", "1")
    with pytest.raises(ValueError, match="AI_FORM_FILLER_TEST_FLAG"):
        parse_env_bool("AI_FORM_FILLER_TEST_FLAG", default=False)
