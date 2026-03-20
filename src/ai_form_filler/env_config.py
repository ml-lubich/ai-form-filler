"""Environment boolean flags: one parser, strict `true` / `false` only.

Unset (or empty) uses each call site’s documented default. Invalid values raise
``ValueError`` so typos fail fast instead of silently doing the wrong thing.

See ``ai_form_filler.constants`` for variable names and defaults.
"""

from __future__ import annotations

import os


def parse_env_bool(env_name: str, *, default: bool) -> bool:
    """Read ``env_name`` from the environment.

    - Missing or whitespace-only → ``default``.
    - ``true`` / ``false`` (case-insensitive) → parsed boolean.
    - Anything else → ``ValueError``.
    """
    raw = os.environ.get(env_name)
    if raw is None:
        return default
    s = str(raw).strip().lower()
    if s == "":
        return default
    if s == "true":
        return True
    if s == "false":
        return False
    raise ValueError(
        f"{env_name} must be 'true' or 'false' (or unset for default {default!r}), got {raw!r}"
    )
