# Requirements

## User stories

- As a user, I can point the tool at a form URL and a **plain-text or JSON** payload (file or inline) so that the form is filled: the local LLM **infers** which facts map to which detected fields (I do not pre-align to each site’s `name=` attributes).
- As a user, I can start Chrome with remote debugging and run the tool so that it attaches to my open tab and fills the form there.
- As a user, I can run with a copy of my Chrome profile so that I can fill forms on sites where I am already logged in.
- As a user, I can pass a different Ollama model (e.g. Qwen) so that I can use my preferred local model for mapping.
- As a user, when the Ollama HTTP API is down on **localhost**, the tool can start **`ollama serve`** for me (unless I disable it with `AI_FORM_FILLER_AUTO_START_OLLAMA=false`).
- As a user, I can run with `--dry-run` so that I see the extracted form schema without filling or calling the **field-mapping** LLM; if I also pass `--goal`, the **navigation** LLM still runs to infer the URL.
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
