# Requirements

## User stories

- As a user, I can point the tool at a form URL and a JSON payload so that the form is filled using my data, using my own browser (existing session or profile).
- As a user, I can start Chrome with remote debugging and run the tool so that it attaches to my open tab and fills the form there.
- As a user, I can run with a copy of my Chrome profile so that I can fill forms on sites where I am already logged in.
- As a user, I can pass a different Ollama model (e.g. Qwen) so that I can use my preferred local model for mapping.
- As a user, I can run with `--dry-run` so that I see the extracted form schema without filling or calling the LLM.
- As a user, I can describe a **goal** in natural language so the local LLM suggests which URL to open before filling.
- As a developer, I can import **AIFormModule** and call `run_from_goal` / `fill_at_url` from my application.
- As a user, I can enable **undetected-chromedriver** (optional install) when sites flag standard automation.

## Constraints

- Must work with Python 3.10+.
- Must use only local LLM (Ollama) for mapping; no required cloud APIs.
- Must support at least: text inputs, textareas, selects, checkboxes, radio buttons.
- Must support two browser modes: CDP (existing browser) and persistent context (user profile).
- No more than the canonical set of docs (see cursor rules); no feature-specific docs.

## Non-goals

- Solving captcha or strong anti-bot.
- Multi-step wizard flows (single-page form per run).
- Full OpenClaw-style generic automation (this tool is form-filler focused).
