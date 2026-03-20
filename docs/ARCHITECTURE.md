# Architecture

## Layers

- **Domain**: Pure data and types in `models.py` (FormField, FormSchema, FillAction, FillPlan). No I/O.
- **Application**: Orchestration and use cases: `form_extract.py` (extract schema from page), `llm.py` (Ollama → fill plan), `filler.py` (apply plan to page), `run.py` (connect → navigate → extract → plan → fill).
- **Infrastructure / Adapters**: `browser.py` (Playwright: CDP vs persistent context), `browser_uc.py` (undetected-chromedriver), `filler_selenium.py`, `form_fields_js.py` (shared extract script), `cli.py` (argparse → `AIFormModule`), `env_config.py` (strict `true`/`false` parsing for env toggles), `bootstrap.py` (Playwright/Ollama prep).

## Component diagram

```
CLI (cli.py)
  → AIFormModule
      → (optional) llm.infer_navigation_intent(goal, …)     → NavigationIntent
      → backend: CDP | PersistentContext | UndetectedChromeConnector
      → extract_form_schema (Playwright) | extract_form_schema_selenium
      → llm.get_fill_plan(schema, user_data)                → FillPlan
      → filler.apply_fill_plan | filler_selenium.apply_fill_plan_selenium
      → optional: submit

Legacy: run.run() still available for Playwright-only flows.
```

## Browser connection

- **CDP**: User starts Chrome with `--remote-debugging-port=9222`. Playwright connects via `chromium.connect_over_cdp(cdp_url)` and uses the existing context and tabs. No separate browser process; user’s session and extensions apply.
- **Persistent context**: Playwright launches Chromium with `launch_persistent_context(user_data_dir, channel="chrome")`. Uses the real Chrome binary and the given profile; user must close Chrome first or use a copy of the profile.

## Dependencies

- **playwright**: Browser automation; form extraction runs in the page via `page.evaluate()`, and filling uses locators (id, name, label).
- **ollama**: HTTP client to local Ollama API for chat completion; response is parsed as JSON (field key → value).

## Invariants

- Code follows specs in `docs/`. No hidden coupling; explicit parameters.
- Domain models are immutable where practical (e.g. FormField frozen).
- Errors are not swallowed; failures are surfaced to the CLI.
