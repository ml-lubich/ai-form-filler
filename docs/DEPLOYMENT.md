# Deployment / setup

## Environment

- Python 3.10+ in a virtual environment (recommended).
- Chrome or Chromium installed for all modes.
- **Ollama** running locally (`ollama serve`) with at least one model pulled (e.g. `ollama pull llama3.2` or `ollama pull qwen2.5`).

## Core install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium   # only for Playwright persistent profile mode
```

## Optional stealth stack

For the `undetected_chrome` backend (CLI `--undetected` or `AIFormModule(..., backend="undetected_chrome")`):

```bash
pip install -e ".[stealth]"
```

No separate `playwright install` is required for that mode; Chrome is launched by undetected-chromedriver.

## Chrome CDP (your running browser)

Start Chrome with remote debugging so Playwright can attach:

- macOS: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`

Default CDP URL in this project: `http://localhost:9222`.

## Production notes

- This tool is intended for **local / trusted** automation. Do not expose Ollama or CDP ports to untrusted networks.
- LLM-inferred URLs are **not** validated against an allowlist by default; use `--hints` / `hints=` in code to constrain domains when automating sensitive flows.
