"""Unit tests for default model resolution."""

import pytest

from ai_form_filler.constants import (
    DEFAULT_OLLAMA_MODEL,
    ENV_AUTO_START_OLLAMA,
    ENV_OLLAMA_HOST,
    ENV_OLLAMA_MODEL,
    auto_start_ollama_serve_enabled,
    ollama_host_is_loopback,
    resolved_ollama_model,
)


def test_resolved_ollama_model_cli_wins() -> None:
    assert resolved_ollama_model("mistral") == "mistral"


def test_resolved_ollama_model_env(monkeypatch) -> None:
    monkeypatch.setenv(ENV_OLLAMA_MODEL, "gemma3")
    assert resolved_ollama_model(None) == "gemma3"


def test_resolved_ollama_model_default(monkeypatch) -> None:
    monkeypatch.delenv(ENV_OLLAMA_MODEL, raising=False)
    assert resolved_ollama_model(None) == DEFAULT_OLLAMA_MODEL


def test_ollama_host_is_loopback(monkeypatch) -> None:
    monkeypatch.setenv(ENV_OLLAMA_HOST, "http://127.0.0.1:11434")
    assert ollama_host_is_loopback() is True
    monkeypatch.setenv(ENV_OLLAMA_HOST, "http://localhost:11434")
    assert ollama_host_is_loopback() is True
    monkeypatch.setenv(ENV_OLLAMA_HOST, "http://10.0.0.1:11434")
    assert ollama_host_is_loopback() is False


def test_auto_start_ollama_serve_enabled_default(monkeypatch) -> None:
    monkeypatch.delenv(ENV_AUTO_START_OLLAMA, raising=False)
    assert auto_start_ollama_serve_enabled() is True


def test_auto_start_ollama_serve_disabled(monkeypatch) -> None:
    monkeypatch.setenv(ENV_AUTO_START_OLLAMA, "false")
    assert auto_start_ollama_serve_enabled() is False


def test_auto_start_ollama_serve_explicit_true(monkeypatch) -> None:
    monkeypatch.setenv(ENV_AUTO_START_OLLAMA, "true")
    assert auto_start_ollama_serve_enabled() is True


def test_parse_env_bool_invalid_auto_start(monkeypatch) -> None:
    monkeypatch.setenv(ENV_AUTO_START_OLLAMA, "yes")
    with pytest.raises(ValueError, match="AI_FORM_FILLER_AUTO_START_OLLAMA"):
        auto_start_ollama_serve_enabled()
