# API

## Public interfaces

### Domain (`models`)

- **FormField**: `key`, `tag`, `input_type`, `name`, `id`, `placeholder`, `label_text`, `options` (for select/radio).
- **FormSchema**: `fields: list[FormField]`; `get_field_by_key(key) -> FormField | None`; `to_llm_description() -> str`.
- **FillAction**: `field_key`, `value` (any).
- **FillPlan**: `actions: list[FillAction]`.
- **NavigationIntent**: `url`, `reason` (LLM output for “where to go”).

### AI module (`module`)

- **AIFormModule(model, backend, …)**  
  Reusable orchestrator. `backend` is one of: `playwright_cdp`, `playwright_profile`, `undetected_chrome`.

- **infer_navigation(goal, *, hints=None, current_url=None) -> NavigationIntent**  
  Calls Ollama to return JSON `{ "url", "reason" }`.

- **infer_url(goal, *, hints=None, current_url=None) -> str**  
  Same as above but returns only the URL string.

- **fill_at_url(url, user_data, *, submit=False) -> FormSchema**  
  Navigate, extract form, fill plan from Ollama, apply fills.

- **run_from_goal(goal, user_data, *, hints=None, current_url=None, submit=False) -> FormSchema**  
  Navigation inference + `fill_at_url`.

### Application

- **extract_form_schema(page: Page) -> FormSchema**  
  Extracts fillable form fields from the current page.

- **get_fill_plan(schema: FormSchema, user_data: str | dict, model: str | None = None) -> FillPlan**  
  Calls Ollama to infer which user facts belong in which extracted fields (schema keys → values); returns a FillPlan. Model defaults to `AI_FORM_FILLER_MODEL` or `DEFAULT_OLLAMA_MODEL` (`qwen2.5`).

- **apply_fill_plan(page: Page, schema: FormSchema, plan: FillPlan) -> None**  
  Applies each action to the page (fill, check, select_option).

- **run(url, user_data, *, use_cdp, cdp_url, user_data_dir, channel, model, submit) -> FormSchema**  
  Legacy Playwright-only pipeline. Prefer **AIFormModule** for URL inference and undetected Chrome.

- **infer_navigation_intent(goal, *, hints, current_url, model) -> NavigationIntent**  
  Ollama call for target URL.

- **extract_form_schema_selenium(driver) -> FormSchema**  
  Same extraction JS as Playwright, via `driver.execute_script`.

- **apply_fill_plan_selenium(driver, schema, plan)** / **click_submit_selenium(driver)**  
  Selenium fill path (requires `.[stealth]`).

### Browser connectors

- **CDPConnector(cdp_url="http://localhost:9222")**  
  `connect() -> (Browser, Page)`. Caller must call `close()` when done.

- **PersistentContextConnector(user_data_dir, channel="chrome", headless=False)**  
  `connect() -> (BrowserContext, Page)`. Caller should call `close()` when done.

- **UndetectedChromeConnector(headless=False, user_data_dir=None, …)**  
  Requires `pip install ".[stealth]"`. `connect() -> WebDriver`.

## CLI

```
ai-form-filler [url] [data] [options]
```

Same executable is also available as **`ai-filler`**.

**No URL, no `--goal`, no `--dry-run`:** runs **bootstrap** (Playwright Chromium + default Ollama model), same as **`--bootstrap`**, unless **`--no-auto-setup`** is set (then the CLI errors until you pass a run).

**Arguments**

- `url`: Optional if `--goal` is set. A lone **`-`** is treated as “no URL” (runs bootstrap when nothing else is passed).
- `data`: Optional with `--dry-run` only. Otherwise a UTF-8 file path or inline string: valid JSON object becomes structured input; any other text is sent to the mapping LLM as raw prose.

**Options**

- `--goal`: Natural-language goal; Ollama infers URL (`NavigationIntent`).
- `--hints`, `--hints-file`: Constraints for navigation inference.
- `--current-url`: Optional context for navigation LLM.
- `--undetected`: Use undetected-chromedriver (requires `.[stealth]`).
- `--uc-user-data-dir`: Chrome user data dir for undetected mode.
- `--cdp-url`: CDP endpoint (default: `http://localhost:9222`).
- `--user-data-dir DIR`: Playwright persistent Chrome profile.
- `--channel`: Browser channel for persistent context (default: `chrome`).
- `--model`: Ollama model tag (default: `qwen2.5` or `AI_FORM_FILLER_MODEL`).
- `--bootstrap`: Install Playwright Chromium + pull default model, exit.
- `--no-auto-setup`: Skip automatic Playwright / `ollama pull` / **auto `ollama serve`** (same as `AI_FORM_FILLER_SKIP_AUTO_PREPARE=true`).
- `--submit`: Click submit after filling.
- `--dry-run`: Print form schema; skips field-mapping LLM; with `--goal`, still runs navigation LLM.

**Exit codes**

- 0: Success.
- 1: Missing URL/goal, missing data (when not `--dry-run`), load error, or runtime error.

## Package import

```python
from ai_form_filler import AIFormModule, DEFAULT_OLLAMA_MODEL, resolved_ollama_model
```

- **`DEFAULT_OLLAMA_MODEL`**: built-in default Ollama tag when CLI/env do not override.
- **`resolved_ollama_model(explicit)`**: returns CLI/explicit value if set, else `AI_FORM_FILLER_MODEL`, else `DEFAULT_OLLAMA_MODEL`.
