# Deployment / setup

## Quick path for humans

See the **Quick start (KISS)** section in the root `README.md`. Keep your answers in a JSON file; start from `examples/my-form-data.example.json` and copy to `my-form-data.json` (gitignored name suggested in README).

## Recommended: uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv once
cd path/to/ai-form-filler
uv sync --no-editable   # add --extra stealth for undetected Chrome
uv run ai-form-filler   # no args = bootstrap (or use --bootstrap)
uv run ai-form-filler "https://example.com/form" data.json
```

`uv.lock` pins dependencies; commit it with the repo. Build backend: **`uv_build`**. **`[tool.uv] link-mode = "copy"`** is set in `pyproject.toml`; **`--no-editable`** is still required on **Python 3.14** so the project is not installed via a **`.pth`** shim that the interpreter may ignore.

### If `ModuleNotFoundError: ai_form_filler`

You probably ran plain **`uv sync`** first. Run **`uv sync --no-editable --reinstall-package ai-form-filler`** (then plain **`uv sync --no-editable`** is enough for later syncs).

## Default Ollama model

- **Code default**: `qwen2.5` (see `ai_form_filler.constants.DEFAULT_OLLAMA_MODEL`) — good balance for structured JSON (navigation + field mapping).
- **Override**: environment variable `AI_FORM_FILLER_MODEL` (e.g. `llama3.2`, `mistral`, `gemma3`, `qwen2.5:7b`, `qwen2.5:14b`).
- **CLI**: `--model <tag>` wins over env.
- **Pull**: `ollama pull <tag>` must succeed for the chosen tag; the app runs `ollama pull` automatically when Ollama’s HTTP API is reachable and the model is missing (unless `AI_FORM_FILLER_SKIP_AUTO_PREPARE=true` or CLI `--no-auto-setup`).

## Automatic setup (Playwright + Ollama)

Unless disabled, before runs the package will:

1. Run **`python -m playwright install chromium`** when using a Playwright backend (idempotent).  
   - Disable: `AI_FORM_FILLER_SKIP_PLAYWRIGHT_INSTALL=true`.
2. If **`ollama` is missing on macOS** and **`AI_FORM_FILLER_AUTO_INSTALL_OLLAMA=true`**, attempt **`brew install ollama`** when `brew` is on `PATH`.  
   - Otherwise print install hints (https://ollama.com/download).
3. **Start Ollama locally** if the HTTP API is not reachable, **`OLLAMA_HOST` is loopback** (`127.0.0.1`, `localhost`, `::1`), the **`ollama` binary is on `PATH`**, and **`AI_FORM_FILLER_AUTO_START_OLLAMA`** is not **`false`** (default is auto-start on). The package runs **`ollama serve`** in a **background** process (detached) and waits up to ~60s for **`OLLAMA_HOST/api/tags`** to respond. It does **not** stop the server when the filler exits (same as starting Ollama yourself).  
   - Disable auto-start: `AI_FORM_FILLER_AUTO_START_OLLAMA=false` (use an already-running Ollama or a remote server only).  
   - Remote **`OLLAMA_HOST`** (non-loopback): auto-start is **skipped**; start Ollama on that machine yourself.
4. If Ollama’s API responds at **`OLLAMA_HOST`** and the model is not listed, run **`ollama pull <model>`**.

Explicit one-shot: **`uv run ai-form-filler`** (no args) or **`uv run ai-form-filler --bootstrap`**.

CI / frozen images: **`uv run ai-form-filler --no-auto-setup`** (or set `AI_FORM_FILLER_SKIP_AUTO_PREPARE=true`).

## Environment variables

### Boolean flags (`true` / `false` only)

Toggles under `AI_FORM_FILLER_*` use **only** the strings **`true`** or **`false`** (case-insensitive). **Unset** means the default shown below. Any other value (including `0`, `1`, `yes`, `no`) raises **`ValueError`** the first time the setting is read so misconfiguration is obvious. Parser: `ai_form_filler.env_config.parse_env_bool`.

| Variable | Default when unset | Purpose |
|----------|-------------------|---------|
| `AI_FORM_FILLER_AUTO_INSTALL_OLLAMA` | `false` | `true`: try `brew install ollama` on macOS when `ollama` is missing |
| `AI_FORM_FILLER_AUTO_START_OLLAMA` | `true` | `false`: do not spawn `ollama serve`; use an already-running or remote Ollama only |
| `AI_FORM_FILLER_SKIP_PLAYWRIGHT_INSTALL` | `false` | `true`: skip Playwright Chromium download |
| `AI_FORM_FILLER_SKIP_AUTO_PREPARE` | `false` | `true`: skip all automatic prepare (tests set this via `conftest.py`) |

### Other variables

| Variable | Purpose |
|----------|---------|
| `AI_FORM_FILLER_MODEL` | Default Ollama model tag |
| `OLLAMA_HOST` | Ollama base URL (standard Ollama env) |

## Core install (pip, without uv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ai_form_filler --bootstrap
```

## Optional stealth stack

For `undetected_chrome`:

```bash
uv sync --no-editable --extra stealth
# or: pip install -e ".[stealth]"
```

## Chrome CDP (your running browser)

- macOS: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
- Default CDP URL: `http://localhost:9222`.
- **CDP does not open a new Chrome** for you: it connects to the instance you started with the debug port. The filler uses the **first open tab** and may navigate it to your target URL.
- **Anti-bot / “stealth”**: CDP-driven pages can still be detected as automated. **`--undetected`** launches a **different** Chrome via Selenium; it does **not** attach to an arbitrary already-open window.

## Production notes

- Intended for **local / trusted** automation. Do not expose Ollama or CDP ports to untrusted networks.
- LLM-inferred URLs are **not** allowlisted by default; use `--hints` / `hints=` to constrain domains.

## License

The project is released under the **MIT License**; see the `LICENSE` file at the repository root (also `license = "MIT"` in `pyproject.toml`).
