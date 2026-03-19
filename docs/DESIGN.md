# Design

## Shared extraction script

- The same logic lives in `form_fields_js.py` as **PLAYWRIGHT_EXTRACT_JS** and **SELENIUM_EXTRACT_JS** so Playwright and undetected-chromedriver paths stay aligned.

## Form extraction

- The extractor runs in the page context via `page.evaluate()` with a single JS snippet.
- It queries `input`, `textarea`, `select`, and for each collects: tag, type, name, id, placeholder, and label text (from `<label for="...">` or ancestor `<label>`). For `select`, it collects options as `[value, label]` pairs.
- A unique **key** per field is chosen: `name` or `id` if present, otherwise `field_N` / `select_N`. This key is what the LLM uses in the fill plan.
- Result is a `FormSchema` (list of `FormField`). Buttons and hidden inputs are skipped.

## LLM navigation (where to go)

- Separate prompt (`build_navigation_prompt`): goal, optional hints (sites/paths), optional current URL.
- Model returns JSON `{ "url": "https://...", "reason": "..." }` parsed into **NavigationIntent**.
- Callers should supply **hints** (allowlist / domain constraints) when automating untrusted goals.

## LLM mapping (what to fill)

- Prompt includes the form schema (one line per field: key, tag, type, name, id, placeholder, label, options) and the user’s data (JSON or free text).
- The model is asked to output **only** a JSON object mapping field keys to values (no markdown or explanation).
- Response is parsed with optional stripping of markdown code fences; then `json.loads()` to obtain the fill plan. Unknown keys are ignored at fill time; missing keys are simply not filled.

## Filling

### Playwright

- For each action in the fill plan, the corresponding `FormField` is looked up by key.
- **Locator order**: id → name → label. Id and name use CSS-style locators; label uses `page.get_by_label(label_text)`.
- **Input types**: Text-like inputs and textareas use `loc.fill(value)`. Checkboxes/radios use `check()` / `uncheck()`; for radio, the locator is narrowed to `[value="..."]` when possible. Selects use `loc.select_option(value)`.
- No retries or complex waiting beyond the initial page load; the page is assumed to be static enough after “networkidle”.

### Selenium (undetected Chrome)

- **filler_selenium**: id → name → XPath label fallback; radio by `name` + `value`; `Select` for `<select>`.
- Launched via **UndetectedChromeConnector**; optional `--user-data-dir` for profile reuse.

## CLI and data

- First positional: URL. Second positional: optional data (file path or inline JSON).
- If data is omitted and `--dry-run` is set, only extraction runs and the schema is printed.
- Connection mode: `--undetected` → undetected Chrome; else if `--user-data-dir` → Playwright persistent context; else CDP with `--cdp-url`.
- If `--goal` is set, navigation LLM runs first (unless using dry-run without goal — then URL is required).
