"""Minimal smoke tests: package imports and public surface."""

import importlib.metadata

import pytest

import ai_form_filler
from ai_form_filler import AIFormModule, DEFAULT_OLLAMA_MODEL
from ai_form_filler.constants import (
    ENV_OLLAMA_HOST,
    ollama_host,
    skip_auto_prepare,
)


def test_package_version_matches_metadata() -> None:
    dist_version = importlib.metadata.version("ai-form-filler")
    assert ai_form_filler.__version__ == dist_version


def test_public_exports() -> None:
    assert isinstance(DEFAULT_OLLAMA_MODEL, str) and DEFAULT_OLLAMA_MODEL
    assert AIFormModule is not None


def test_ollama_host_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_OLLAMA_HOST, raising=False)
    assert ollama_host() == "http://127.0.0.1:11434"


def test_skip_auto_prepare_false_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_FORM_FILLER_SKIP_AUTO_PREPARE", raising=False)
    assert skip_auto_prepare() is False
