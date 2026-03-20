# AI Form Filler

Lightweight AI-powered form filler that works with **your own browser** (no headless/dev browser). Uses **Playwright** for automation and **Ollama** (or Qwen, Llama, etc.) to **infer** what goes where: you pass **plain text or JSON** (file or inline); the tool reads the real form from the page (labels, placeholders, types) and the LLM decides what to type — same idea as pasting the form + your notes into ChatGPT, except the tool **types, optionally submits**, and can use **CDP or your Chrome profile** so you **log in once**, then run the CLI.

## Table of contents

- [Quick start (KISS)](#quick-start-kiss)
- [Features](#features)
- [Prototype flow](#prototype-flow)
- [Default model](#default-model-and-using-any-ollama-model)
- [Prerequisites](#prerequisites)
- [Install with uv](#install-with-uv-recommended)
- [Install without uv (pip)](#install-without-uv-pip)
- [Python module](#python-module-embed-in-your-app)
- [Use your own browser (CDP)](#use-your-own-browser-cdp)
- [Chrome profile (persistent context)](#use-your-chrome-profile-persistent-context)
- [Dry run](#dry-run-inspect-form-only)
- [Options](#options)
- [Boolean environment variables](#boolean-environment-variables)
- [Data format](#data-format)
- [Documentation](#docs)
- [License](#license)

## Quick start (KISS)

Do this once, then repeat only steps **5–6** when you fill another form.

1. **Install [uv](https://docs.astral.sh/uv/)** (one line installer on their site).
2. **Clone** this repo and `cd` into it.
3. **Install and bootstrap** (from the repo root):

```bash
uv sync --no-editable
uv run ai-form-filler   # no args = bootstrap (Chromium + default model); same as --bootstrap
```

**`--no-editable`** installs this package into **`site-packages/`** instead of an editable **`.pth`** shim. On **Python 3.14**, plain **`uv sync`** often leaves **`import ai_form_filler`** broken; always use **`--no-editable`** here. If you already synced without it, run once: **`uv sync --no-editable --reinstall-package ai-form-filler`**.
4. **Your facts** — either a **text file** (resume snippet, bullet list, anything you’d paste into a chat) or a **JSON object** (optional: copy `examples/my-form-data.example.json` → **`my-form-data.json`**). The LLM reads it and decides what goes in each field.
5. **Chrome** — pick one:
   - **A — Already logged in elsewhere (CDP):** Quit Chrome, start it with remote debugging, log in once, open a tab.  
     macOS:  
     `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
   - **B — Fresh window with a saved profile (login persists):** Close all Chrome windows, then run the CLI with **`--user-data-dir`** pointing at your Chrome user data (see [Chrome profile](#use-your-chrome-profile-persistent-context) below). Log in once; next runs reuse the same profile.
6. **Fill:** from the repo (use your real URL and file path):

```bash
uv run ai-form-filler "https://example.com/contact" my-form-data.json
```

Optional: **`--submit`** to click the first submit-like button after filling. **`--dry-run`** prints what fields were detected without filling.

That’s the whole product in six steps: **bootstrap once → maintain one JSON → point at URL → run CLI.**

## Features

- **Your browser**: Connect via Chrome DevTools Protocol (CDP) to an already-open Chrome, or launch Chrome with your profile (persistent context).
- **LLM picks the URL**: Optional `--goal` so Ollama infers *where* to go before filling (contact page, signup, etc.).
- **AI module**: Import `AIFormModule` in your own app (`from ai_form_filler import AIFormModule`).
- **Stealth option**: Optional `undetected-chromedriver` + Selenium (`uv sync --no-editable --extra stealth` or `pip install '.[stealth]'`) + `--undetected`.
- **Auto setup**: On each run (unless `--no-auto-setup`), installs **Playwright Chromium** if needed; if **`OLLAMA_HOST` is localhost** and the API is down, starts **`ollama serve`** in the background (disable with `AI_FORM_FILLER_AUTO_START_OLLAMA=false`); then **`ollama pull`** for the default model when the API is up. First-time: **`uv run ai-form-filler`** (no args) or **`--bootstrap`**.
- **Most forms**: Extracts inputs, textareas, selects, checkboxes, radios; uses a local LLM to map your data to the right fields.
- **Lightweight**: Core deps are Playwright + Ollama; stealth stack is optional.

## Prototype flow

1. **`uv sync --no-editable`** then **`uv run ai-form-filler`** once (no args = bootstrap).
2. **Chrome + Ollama** — install [Ollama](https://ollama.com/download); start Chrome with **`--remote-debugging-port=9222`** for CDP mode (see [Use your own browser](#use-your-own-browser-cdp)).
3. **`uv run ai-form-filler "<url>" your-data.json`** — or **`--goal "…"`** instead of a URL. Stealth Chrome: **`uv sync --no-editable --extra stealth`** then **`--undetected`**.

More install and env detail: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Default model (and using any Ollama model)

| Item | Value |
|------|--------|
| **Built-in default** | `qwen2.5` — strong at instruction-following and JSON for navigation + field mapping |
| **Override via env** | `export AI_FORM_FILLER_MODEL=llama3.2` (or `mistral`, `gemma3`, `qwen2.5:7b`, etc.) |
| **Override via CLI** | `--model llama3.2` |
| **Pull a model** | `ollama pull <name>` — same tag you pass to `--model` |

Smaller / faster options: `llama3.2`, `phi3`. Larger / sharper: `qwen2.5:14b`, `llama3.1:8b` (machine-dependent).

## Prerequisites

1. **Chrome** (or Chromium) installed.
2. **Ollama** installed (`ollama` on `PATH` or the desktop app). The filler can **start `ollama serve`** automatically on localhost (see step 4 above) and **pull** the default model when the API is up.
3. **Python 3.10+** (uv will pick a compatible interpreter).

## Install with uv (recommended)

```bash
cd path/to/ai-form-filler
uv sync --no-editable
uv run ai-form-filler              # first run: bootstrap
uv run ai-form-filler "https://example.com/form" data.json
```

Use **`uv run ai-form-filler`** or **`uv run ai-filler`** (same CLI). Stealth deps: **`uv sync --no-editable --extra stealth`**.

### Install without uv (pip)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -e ".[stealth]"   # optional
python -m ai_form_filler --bootstrap
```

## Python module (embed in your app)

```python
from ai_form_filler import AIFormModule, DEFAULT_OLLAMA_MODEL

# Uses DEFAULT_OLLAMA_MODEL or AI_FORM_FILLER_MODEL unless you pass model=
mod = AIFormModule(backend="playwright_cdp", cdp_url="http://localhost:9222")

# Let the LLM infer the URL, then fill
mod.run_from_goal(
    "open the contact form on example.com",
    {"email": "you@example.com", "message": "Hello"},
    hints="Only use https://example.com",
    submit=False,
)

# Or you already know the URL
mod.fill_at_url("https://example.com/contact", {"email": "you@example.com"})
```

## Use your own browser (CDP)

**Default mode (no `--user-data-dir`, no `--undetected`)** does **not** launch a new Chrome window. It **attaches** to Chrome you already started with a debug port and drives the **first open tab** (the tool may `goto` your form URL in that tab).

Some sites detect **any** DevTools automation, including CDP. **`--undetected`** uses a **separate** Chrome started by undetected-chromedriver—it is **not** the same as “the window I already have open.”

1. Start Chrome with remote debugging:
   - **macOS**:  
     `Google Chrome --remote-debugging-port=9222`  
     (or create a shortcut with that argument)
   - **Windows**:  
     `chrome.exe --remote-debugging-port=9222`
   - **Linux**:  
     `google-chrome --remote-debugging-port=9222`

2. Open a tab and go to the page with the form (or leave it blank and pass the URL to the CLI).

3. Run the filler (data can be a JSON file or inline JSON):

```bash
# Inline JSON (prefix with uv run if you use uv)
uv run ai-form-filler "https://example.com/form" '{"email":"you@example.com","name":"You"}'

# JSON file
ai-form-filler "https://example.com/form" data.json

# Use a different Ollama model
ai-form-filler "https://example.com/form" data.json --model qwen2.5

# Click submit after filling
ai-form-filler "https://example.com/form" data.json --submit

# LLM infers URL from a goal (still need data JSON for field mapping)
ai-form-filler --goal "go to example.com contact form" data.json --hints "https://example.com only"

# Undetected Chrome (after uv sync --no-editable --extra stealth)
uv run ai-form-filler "https://example.com/form" data.json --undetected
```

## Use your Chrome profile (persistent context)

This launches Chrome with your real user data dir (cookies, logins). **Close all Chrome windows first.**

```bash
# macOS default Chrome profile
ai-form-filler "https://example.com/form" data.json --user-data-dir "$HOME/Library/Application Support/Google/Chrome"

# Or use a copy of your profile to avoid "Chrome is already running"
cp -r "$HOME/Library/Application Support/Google/Chrome" /tmp/chrome-profile
ai-form-filler "https://example.com/form" data.json --user-data-dir /tmp/chrome-profile
```

## Dry run (inspect form only)

Extract and print the form schema. **Field-mapping LLM is skipped.** If you use `--goal`, the **navigation** LLM still runs to pick the URL.

```bash
ai-form-filler "https://example.com/form" --dry-run
ai-form-filler --goal "example.com contact" --dry-run --hints "https://example.com"
```

## Options

| Option | Description |
|--------|-------------|
| `url` | Page URL (optional if `--goal` is set) |
| `data` | File path (UTF-8 text or JSON) or inline string (plain text or JSON) |
| `--goal` | Natural-language goal; LLM infers URL to open |
| `--hints` / `--hints-file` | Constraints for URL inference |
| `--current-url` | Optional context for navigation LLM |
| `--undetected` | Use undetected-chromedriver (requires `.[stealth]`) |
| `--uc-user-data-dir` | User data dir for undetected Chrome |
| `--cdp-url` | CDP endpoint (default: `http://localhost:9222`) |
| `--user-data-dir` | Playwright persistent Chrome profile |
| `--channel` | Browser channel for persistent context (default: `chrome`) |
| `--model` | Ollama model (default: `qwen2.5` or `AI_FORM_FILLER_MODEL`; e.g. `llama3.2`) |
| `--submit` | Click submit after filling |
| `--dry-run` | Print form schema only (navigation LLM still used if `--goal`) |
| `--bootstrap` | Same as running with **no arguments**: Chromium + default model, then exit |
| `--no-auto-setup` | Skip auto Playwright / `ollama pull` / auto `ollama serve` (same as `AI_FORM_FILLER_SKIP_AUTO_PREPARE=true`) |

## Boolean environment variables

All `AI_FORM_FILLER_*` **toggles** use only **`true`** or **`false`** (case-insensitive). **Unset** uses the default documented in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#boolean-flags-true--false-only). Values like `0`, `1`, or `yes` are **rejected** with a clear error so config stays predictable.

Shared parser: [`src/ai_form_filler/env_config.py`](src/ai_form_filler/env_config.py) (`parse_env_bool`).

## Data format

**Flexible input** (second CLI argument or file path):

- **Plain text** — paste notes, a paragraph, bullets, half a résumé; if the file or string is **not** valid JSON, the whole thing is sent to the model as-is. Best when you want zero structure.
- **JSON object** — optional: keys are *your* names; values are strings, numbers, or booleans. Handy when you like stable, editable fields; the LLM still aligns them to the form by meaning, not by matching the site’s `name=` or `id`.

Either way, the tool extracts the **real** controls from the DOM and the LLM **infers** what to type where.

**Vision / screenshot agents** (OpenClaw-style): out of scope for the core tool — see [docs/DESIGN.md](docs/DESIGN.md#why-dom--llm-mapping-not-screenshots--openclaw-style-clicks).

**JSON template (optional):** [`examples/my-form-data.example.json`](examples/my-form-data.example.json) → **`my-form-data.json`** (gitignored).

Plain-text example (save as `my-profile.txt` or pass inline if your shell allows):

```text
Alex Kim
alex@example.com
Phone: 555-0100
Company: Northwind
```

Minimal JSON example:

```json
{
  "email": "you@example.com",
  "name": "Your Name",
  "message": "Hello world",
  "agree": true
}
```

## Docs

- [docs/OVERVIEW.md](docs/OVERVIEW.md) – Product overview and flow
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) – Layers and components
- [docs/DESIGN.md](docs/DESIGN.md) – Extraction, LLM, backends
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) – Install, Ollama, optional stealth
- [docs/API.md](docs/API.md) – Public interfaces and CLI
- [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) – User stories and constraints
- [docs/TESTING.md](docs/TESTING.md) – How to run tests

## License

This project is licensed under the [MIT License](LICENSE). SPDX: `MIT` (see `pyproject.toml`).
