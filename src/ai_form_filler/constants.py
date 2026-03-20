"""Central defaults and environment overrides.

Boolean toggles use strict ``true`` / ``false`` strings (see ``env_config.parse_env_bool``).
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from .env_config import parse_env_bool

# Strong default for structured JSON (navigation + field mapping). See docs/DEPLOYMENT.md (Default Ollama model).
DEFAULT_OLLAMA_MODEL = "qwen2.5"

ENV_OLLAMA_MODEL = "AI_FORM_FILLER_MODEL"
ENV_OLLAMA_HOST = "OLLAMA_HOST"
ENV_AUTO_INSTALL_OLLAMA = "AI_FORM_FILLER_AUTO_INSTALL_OLLAMA"
ENV_AUTO_START_OLLAMA = "AI_FORM_FILLER_AUTO_START_OLLAMA"
ENV_SKIP_PLAYWRIGHT_INSTALL = "AI_FORM_FILLER_SKIP_PLAYWRIGHT_INSTALL"
ENV_SKIP_AUTO_PREPARE = "AI_FORM_FILLER_SKIP_AUTO_PREPARE"


def resolved_ollama_model(cli_or_explicit: str | None) -> str:
    """CLI wins; else env AI_FORM_FILLER_MODEL; else DEFAULT_OLLAMA_MODEL."""
    if cli_or_explicit is not None and cli_or_explicit.strip() != "":
        return cli_or_explicit.strip()
    env_val = os.environ.get(ENV_OLLAMA_MODEL, "").strip()
    if env_val:
        return env_val
    return DEFAULT_OLLAMA_MODEL


def ollama_host() -> str:
    """Ollama base URL (trailing slash stripped)."""
    h = os.environ.get(ENV_OLLAMA_HOST, "http://127.0.0.1:11434").strip().rstrip("/")
    return h or "http://127.0.0.1:11434"


def ollama_host_is_loopback() -> bool:
    """True if OLLAMA_HOST points at this machine (safe to spawn `ollama serve` locally)."""
    parsed = urlparse(ollama_host())
    host = (parsed.hostname or "").lower()
    return host in ("127.0.0.1", "localhost", "::1")


def auto_start_ollama_serve_enabled() -> bool:
    """If True (default), spawn `ollama serve` when the API is down and host is loopback.

    Set ``AI_FORM_FILLER_AUTO_START_OLLAMA=false`` to only use an already-running Ollama.
    """
    return parse_env_bool(ENV_AUTO_START_OLLAMA, default=True)


def auto_install_ollama_enabled() -> bool:
    """If ``true``, try Homebrew to install Ollama on macOS when the binary is missing."""
    return parse_env_bool(ENV_AUTO_INSTALL_OLLAMA, default=False)


def skip_playwright_browser_install() -> bool:
    return parse_env_bool(ENV_SKIP_PLAYWRIGHT_INSTALL, default=False)


def skip_auto_prepare() -> bool:
    """Disable automatic Playwright/Ollama setup (e.g. in tests)."""
    return parse_env_bool(ENV_SKIP_AUTO_PREPARE, default=False)
