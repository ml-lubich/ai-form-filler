# AI Form Filler

Lightweight AI-powered form filler that works with **your own browser** (no headless/dev browser). Uses **Playwright** for automation and **Ollama** (or Qwen, Llama, etc.) for mapping your data to form fields.

## Features

- **Your browser**: Connect via Chrome DevTools Protocol (CDP) to an already-open Chrome, or launch Chrome with your profile (persistent context).
- **LLM picks the URL**: Optional `--goal` so Ollama infers *where* to go before filling (contact page, signup, etc.).
- **AI module**: Import `AIFormModule` in your own app (`from ai_form_filler import AIFormModule`).
- **Stealth option**: Optional `undetected-chromedriver` + Selenium backend (`pip install '.[stealth]'` + `--undetected`) for sites that flag plain automation.
- **Most forms**: Extracts inputs, textareas, selects, checkboxes, radios; uses a local LLM to map your data to the right fields.
- **Lightweight**: Core deps are Playwright + Ollama; stealth stack is optional.

## Step-by-step (how it works)

1. **Start Ollama** and pull a model: `ollama pull llama3.2` (or `qwen2.5`, etc.).
2. **Install** this repo in a venv: `pip install -e .` (add `'.[stealth]'` if you want undetected Chrome).
3. **Choose browser mode**:
   - **CDP**: Start Chrome with `--remote-debugging-port=9222` (your normal browser + extensions).
   - **Profile**: `--user-data-dir` with Playwright (close Chrome first).
   - **Undetected**: `--undetected` launches Chrome via undetected-chromedriver (install stealth extra first).
4. **Choose URL**:
   - Pass a **URL** directly, **or**
   - Use **`--goal "natural language"`** so the local LLM returns a JSON `url` + `reason` (see `infer_navigation` in code).
5. **Pass data** as JSON (file or inline); the LLM maps keys/labels to form field keys, then the tool fills the page.

## Prerequisites

1. **Chrome** (or Chromium) installed.
2. **Ollama** installed and running, with a model pulled (e.g. `ollama pull llama3.2` or `ollama pull qwen2.5`).
3. **Python 3.10+**.

## Install

```bash
cd ai-form-filler
python3 -m venv .venv && source .venv/bin/activate  # or use your venv
pip install -e .
playwright install chromium   # only if using persistent context; not needed for CDP

# Optional: undetected-chromedriver + Selenium
pip install -e ".[stealth]"
```

## Python module (embed in your app)

```python
from ai_form_filler import AIFormModule

mod = AIFormModule(model="qwen2.5", backend="playwright_cdp", cdp_url="http://localhost:9222")

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
# Inline JSON
ai-form-filler "https://example.com/form" '{"email":"you@example.com","name":"You"}'

# JSON file
ai-form-filler "https://example.com/form" data.json

# Use a different Ollama model
ai-form-filler "https://example.com/form" data.json --model qwen2.5

# Click submit after filling
ai-form-filler "https://example.com/form" data.json --submit

# LLM infers URL from a goal (still need data JSON for field mapping)
ai-form-filler --goal "go to example.com contact form" data.json --hints "https://example.com only"

# Undetected Chrome (after pip install -e ".[stealth]")
ai-form-filler "https://example.com/form" data.json --undetected
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
| `data` | JSON file path or inline JSON with data to fill |
| `--goal` | Natural-language goal; LLM infers URL to open |
| `--hints` / `--hints-file` | Constraints for URL inference |
| `--current-url` | Optional context for navigation LLM |
| `--undetected` | Use undetected-chromedriver (requires `.[stealth]`) |
| `--uc-user-data-dir` | User data dir for undetected Chrome |
| `--cdp-url` | CDP endpoint (default: `http://localhost:9222`) |
| `--user-data-dir` | Playwright persistent Chrome profile |
| `--channel` | Browser channel for persistent context (default: `chrome`) |
| `--model` | Ollama model (default: `llama3.2`; e.g. `qwen2.5`) |
| `--submit` | Click submit after filling |
| `--dry-run` | Print form schema only (navigation LLM still used if `--goal`) |

## Data format

Your JSON should contain key-value pairs that the LLM can map to form fields (by label, name, placeholder, etc.):

```json
{
  "email": "you@example.com",
  "name": "Your Name",
  "message": "Hello world",
  "agree": true
}
```

The LLM receives the form schema (field keys, types, labels) and your data, and returns a mapping from field keys to values; the tool then fills the form.

## Docs

- [docs/OVERVIEW.md](docs/OVERVIEW.md) – Product overview and flow
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) – Layers and components
- [docs/DESIGN.md](docs/DESIGN.md) – Extraction, LLM, backends
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) – Install, Ollama, optional stealth
- [docs/API.md](docs/API.md) – Public interfaces and CLI
- [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) – User stories and constraints
- [docs/TESTING.md](docs/TESTING.md) – How to run tests

## License

MIT
