# Testing

## Strategy

- **Unit**: Pure domain and small application functions where I/O can be injected or mocked (e.g. prompt building, parsing LLM response, `load_user_data`, env parsing).
- **LLM client (mocked)**: `tests/test_llm_client_mocked.py` patches `ai_form_filler.llm.chat` so `get_fill_plan` and `infer_navigation_intent` run **without a live Ollama** and **without caring which model name** is passed. Field keys in fixtures are opaque (not “email” / “contact” domain words).
- **Browser integration (no LLM)**: `tests/test_pipeline_browser_integration.py` marks tests with `@pytest.mark.integration`. A real Chromium loads **generic** HTML (arbitrary `name=` attributes), runs the same extract JS as production, then applies a hand-built `FillPlan` — **form-agnostic** and **LLM-free** (the LLM step is replaced by deterministic actions).
- **Full stack (manual / optional automation)**: Connecting to your own Chrome (CDP), hitting real sites, and calling Ollama is not run in CI by default; use the manual verification steps below.

## Running tests

From the project root (uv):

```bash
uv sync --no-editable
uv run playwright install chromium   # once, for @integration browser tests
uv run pytest
```

Skip browser integration tests: `uv run pytest -m "not integration"`.

**CLI:** `tests/test_cli.py` covers URL normalization (`-` → no URL) and default bootstrap when argv is empty (with `bootstrap_cli` mocked).

Or with pip: `pip install -e ".[dev]" && pytest`

Tests set `AI_FORM_FILLER_SKIP_AUTO_PREPARE=true` via `tests/conftest.py` so Playwright/Ollama bootstrap does not run during unit tests.

## Coverage expectations

- **Smoke**: package metadata/version, public exports, a few `constants` helpers (`ollama_host`, `skip_auto_prepare`).
- **Bootstrap**: `try_start_local_ollama_server` respects skip/auto-start/loopback (see `tests/test_bootstrap.py`).
- **Env parsing**: `parse_env_bool` accepts only `true`/`false` (see `tests/test_env_config.py`).
- **Form extract**: `schema_from_raw_fields` builds `FormSchema` from raw dicts (no browser).
- Domain models and `to_llm_description` / `get_field_by_key`: covered by unit tests.
- `build_mapping_prompt`, `parse_fill_plan_from_response`, `parse_navigation_intent`: unit tests with no live Ollama.
- `load_user_data`: accepts JSON objects, non-JSON prose files, and inline text (`tests/test_run.py`).
- **Mocked LLM client**: `get_fill_plan` / `infer_navigation_intent` with `chat` patched (`tests/test_llm_client_mocked.py`).
- **Browser pipeline**: extract + apply with opaque field names (`tests/test_pipeline_browser_integration.py`, marker `integration`).

## Verification (manual)

1. Start Chrome with `--remote-debugging-port=9222`.
2. Open a page with a simple form (e.g. https://httpbin.org/forms/post or a local HTML file).
3. Run:  
   `ai-form-filler "<url>" '{"custname":"Test","custemail":"a@b.com"}'`  
   and confirm fields are filled.
4. Run:  
   `ai-form-filler "<url>" --dry-run`  
   and confirm the printed schema matches the form.
