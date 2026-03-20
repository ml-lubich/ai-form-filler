"""Ensure Playwright browsers, Ollama binary, and pulled models when possible."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

from .constants import (
    DEFAULT_OLLAMA_MODEL,
    auto_install_ollama_enabled,
    auto_start_ollama_serve_enabled,
    ollama_host,
    ollama_host_is_loopback,
    resolved_ollama_model,
    skip_auto_prepare,
    skip_playwright_browser_install,
)

logger = logging.getLogger(__name__)


def _ollama_api_reachable(host: str) -> bool:
    url = f"{host}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
        return False


def _popen_ollama_serve(ollama_bin: str) -> subprocess.Popen[bytes]:
    """Start `ollama serve` detached from the filler process (keeps running after we exit)."""
    if sys.platform == "win32":
        return subprocess.Popen(
            [ollama_bin, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(
        [ollama_bin, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _wait_ollama_api(host: str, *, timeout_s: float = 60.0, interval_s: float = 0.5) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _ollama_api_reachable(host):
            return True
        time.sleep(interval_s)
    return False


def try_start_local_ollama_server() -> None:
    """If Ollama HTTP API is down and policy allows, run `ollama serve` in the background and wait briefly.

    No-op when AI_FORM_FILLER_SKIP_AUTO_PREPARE=true, when the API is already up, when OLLAMA_HOST is
    not loopback, or when the `ollama` binary is missing.
    """
    if skip_auto_prepare():
        return
    host = ollama_host()
    if _ollama_api_reachable(host):
        return
    if not auto_start_ollama_serve_enabled():
        logger.debug("Auto-start Ollama disabled (AI_FORM_FILLER_AUTO_START_OLLAMA=false).")
        return
    if not ollama_host_is_loopback():
        logger.info(
            "Ollama API not reachable at %s; not starting `ollama serve` automatically "
            "(OLLAMA_HOST is not loopback). Start Ollama on that host yourself.",
            host,
        )
        return
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        return
    logger.info(
        "Ollama API not reachable at %s; starting `ollama serve` in the background...",
        host,
    )
    try:
        _popen_ollama_serve(ollama_bin)
    except OSError as e:
        logger.warning("Could not start `ollama serve`: %s", e)
        return
    if _wait_ollama_api(host):
        logger.info("Ollama API is reachable at %s.", host)
        return
    logger.warning(
        "Ollama API at %s still unreachable after starting `ollama serve`. "
        "If the server is starting slowly, wait and retry; otherwise check the port and logs.",
        host,
    )


def ensure_playwright_chromium() -> None:
    """Idempotent: install Playwright Chromium if missing (skip if env disables)."""
    if skip_playwright_browser_install():
        logger.info("Skipping Playwright browser install (%s set).", "AI_FORM_FILLER_SKIP_PLAYWRIGHT_INSTALL")
        return
    logger.info("Ensuring Playwright Chromium is installed (idempotent)...")
    proc = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        logger.warning(
            "Playwright chromium install exited %s. stderr: %s",
            proc.returncode,
            (proc.stderr or proc.stdout or "")[:500],
        )
    else:
        logger.info("Playwright Chromium ready.")


def _fetch_ollama_tags(host: str) -> list[str]:
    url = f"{host}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            body = resp.read().decode("utf-8")
        data = json.loads(body)
        models = data.get("models") or []
        names: list[str] = []
        for m in models:
            if isinstance(m, dict) and m.get("name"):
                names.append(str(m["name"]))
        return names
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        logger.debug("Could not list Ollama models from %s: %s", url, e)
        return []


def _model_available_locally(requested: str, installed: list[str]) -> bool:
    """True if requested tag or same family is already pulled (e.g. qwen2.5 matches qwen2.5:7b)."""
    if not installed:
        return False
    req = requested.strip()
    if req in installed:
        return True
    base = req.split(":")[0].lower()
    for name in installed:
        n = name.split(":")[0].lower()
        if n == base:
            return True
    return False


def try_install_ollama_via_homebrew() -> bool:
    """Return True if `ollama` is on PATH after attempt (macOS + Homebrew only)."""
    if shutil.which("ollama"):
        return True
    if sys.platform != "darwin":
        return False
    brew = shutil.which("brew")
    if not brew:
        return False
    if not auto_install_ollama_enabled():
        logger.info(
            "Ollama not found. Install from https://ollama.com or set %s=true to try `brew install ollama` on macOS.",
            "AI_FORM_FILLER_AUTO_INSTALL_OLLAMA",
        )
        return False
    logger.info("Installing Ollama via Homebrew (AI_FORM_FILLER_AUTO_INSTALL_OLLAMA=true)...")
    proc = subprocess.run([brew, "install", "ollama"], timeout=600)
    return proc.returncode == 0 and shutil.which("ollama") is not None


def ensure_ollama_model_pulled(model: str) -> None:
    """If Ollama server responds and the model is missing, run `ollama pull <model>`."""
    try_start_local_ollama_server()
    host = ollama_host()
    tags = _fetch_ollama_tags(host)
    if not tags:
        if not shutil.which("ollama"):
            try_install_ollama_via_homebrew()
        if not shutil.which("ollama"):
            logger.warning(
                "Ollama does not appear to be running or reachable at %s. "
                "Start the Ollama app or run `ollama serve`, then `ollama pull %s`.",
                host,
                model,
            )
            return
        logger.warning(
            "Cannot reach Ollama API at %s (is `ollama serve` running?). "
            "After it is up, run: ollama pull %s",
            host,
            model,
        )
        return

    if _model_available_locally(model, tags):
        logger.info("Ollama model %r is already available.", model)
        return

    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        logger.warning("`ollama` CLI not on PATH; cannot pull %s automatically.", model)
        return

    logger.info("Pulling Ollama model %r (first run may take a while)...", model)
    proc = subprocess.run([ollama_bin, "pull", model], timeout=3600)
    if proc.returncode != 0:
        logger.warning("`ollama pull %s` failed; install manually: ollama pull %s", model, model)


def prepare_environment(
    model: str,
    *,
    use_playwright: bool,
    need_ollama: bool,
) -> None:
    """Best-effort setup before a run (skipped if AI_FORM_FILLER_SKIP_AUTO_PREPARE=true)."""
    if skip_auto_prepare():
        return
    if use_playwright:
        ensure_playwright_chromium()
    if need_ollama:
        if not shutil.which("ollama"):
            try_install_ollama_via_homebrew()
        ensure_ollama_model_pulled(model)


def bootstrap_cli(verbose: bool = False) -> None:
    """Explicit first-time setup (also what --bootstrap runs)."""
    if verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    m = resolved_ollama_model(None)
    print(f"Default model (env or built-in): {m!r} (built-in default is {DEFAULT_OLLAMA_MODEL!r})")
    ensure_playwright_chromium()
    if not shutil.which("ollama"):
        installed = try_install_ollama_via_homebrew()
        if not installed:
            print(
                "Install Ollama: https://ollama.com/download\n"
                "  macOS (Homebrew): brew install ollama\n"
                "  Or set AI_FORM_FILLER_AUTO_INSTALL_OLLAMA=true and re-run --bootstrap"
            )
    ensure_ollama_model_pulled(m)
    print("Bootstrap finished.")
