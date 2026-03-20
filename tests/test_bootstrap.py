"""Tests for Ollama bootstrap / auto-start helpers."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from ai_form_filler import bootstrap


def test_try_start_local_ollama_skips_when_auto_prepare_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_FORM_FILLER_SKIP_AUTO_PREPARE", "true")
    called: list[str] = []

    def _fake_popen(bin_path: str) -> subprocess.Popen[bytes]:
        called.append(bin_path)
        raise AssertionError("should not start ollama when skip auto prepare")

    monkeypatch.setattr(bootstrap, "_popen_ollama_serve", _fake_popen)
    bootstrap.try_start_local_ollama_server()
    assert called == []


def test_try_start_local_ollama_skips_when_api_already_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_FORM_FILLER_SKIP_AUTO_PREPARE", "false")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    called: list[str] = []

    monkeypatch.setattr(bootstrap, "_ollama_api_reachable", lambda h: True)
    monkeypatch.setattr(
        bootstrap,
        "_popen_ollama_serve",
        lambda b: called.append(b) or subprocess.Popen(["true"], stdout=subprocess.DEVNULL),
    )
    bootstrap.try_start_local_ollama_server()
    assert called == []


def test_try_start_local_ollama_skips_when_auto_start_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_FORM_FILLER_SKIP_AUTO_PREPARE", "false")
    monkeypatch.setenv("AI_FORM_FILLER_AUTO_START_OLLAMA", "false")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    called: list[str] = []

    monkeypatch.setattr(bootstrap, "_ollama_api_reachable", lambda h: False)
    monkeypatch.setattr(
        bootstrap,
        "_popen_ollama_serve",
        lambda b: called.append(b) or subprocess.Popen(["true"], stdout=subprocess.DEVNULL),
    )
    bootstrap.try_start_local_ollama_server()
    assert called == []


def test_try_start_local_ollama_skips_when_not_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_FORM_FILLER_SKIP_AUTO_PREPARE", "false")
    monkeypatch.setenv("OLLAMA_HOST", "http://192.168.1.50:11434")
    called: list[str] = []

    monkeypatch.setattr(bootstrap, "_ollama_api_reachable", lambda h: False)
    monkeypatch.setattr(
        bootstrap,
        "_popen_ollama_serve",
        lambda b: called.append(b) or subprocess.Popen(["true"], stdout=subprocess.DEVNULL),
    )
    bootstrap.try_start_local_ollama_server()
    assert called == []


def test_try_start_local_ollama_invokes_serve_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_FORM_FILLER_SKIP_AUTO_PREPARE", "false")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    monkeypatch.setenv("AI_FORM_FILLER_AUTO_START_OLLAMA", "true")
    popen_bins: list[str] = []

    def fake_reachable(_host: str) -> bool:
        return len(popen_bins) > 0

    monkeypatch.setattr(bootstrap, "_ollama_api_reachable", fake_reachable)
    monkeypatch.setattr(bootstrap, "_wait_ollama_api", lambda h, timeout_s=60.0, interval_s=0.5: True)

    def record_popen(bin_path: str) -> subprocess.Popen[bytes]:
        popen_bins.append(bin_path)
        return subprocess.Popen(["true"], stdout=subprocess.DEVNULL)

    monkeypatch.setattr(shutil, "which", lambda _: "/fake/ollama")
    monkeypatch.setattr(bootstrap, "_popen_ollama_serve", record_popen)
    bootstrap.try_start_local_ollama_server()
    assert popen_bins == ["/fake/ollama"]
