"""Pytest: skip automatic Playwright/Ollama setup during unit tests."""

from __future__ import annotations

import os

os.environ.setdefault("AI_FORM_FILLER_SKIP_AUTO_PREPARE", "true")
