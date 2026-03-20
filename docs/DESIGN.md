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

- Prompt includes the form schema (one line per field: key, tag, type, name, id, placeholder, label, options) and the user’s data (**plain text or JSON object**, loaded by `load_user_data` in `run.py`).
- **Semantic inference (not “known fields”)**: the user’s JSON is a **vault of facts** (whatever keys they like). The extractor already produced stable **schema keys** from the DOM (`name` / `id` / `field_N`). The LLM’s job is the same as if someone pasted the form plus their details into ChatGPT: decide **which fact goes to which field** using labels, placeholders, types, and options. Output keys must still be those schema keys so Playwright/Selenium can apply the plan.
- The model is asked to output **only** a JSON object mapping schema field keys to values (no markdown or explanation).
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
- If data is omitted and `--dry-run` is set, only extraction runs and the schema is printed (field-mapping LLM is skipped; with `--goal`, navigation LLM still runs to choose the URL).
- Connection mode: `--undetected` → undetected Chrome; else if `--user-data-dir` → Playwright persistent context; else CDP with `--cdp-url`.
- For `--dry-run` without `--goal`, a **URL** is required (no navigation inference).

## Why DOM + LLM mapping (not screenshots / OpenClaw-style clicks)

This tool is intentionally **form-shaped**: it reads **structured fields** from the page, asks the LLM to **map your JSON** to those keys, then fills via stable locators (id / name / label). That path is **more reliable** for standard forms than:

- **Vision loops** (screenshot → multimodal model → click coordinates): fragile across DPI, themes, scroll, and popups; needs a vision-capable model and large prompts; hard to test deterministically.
- **General “click anything” agents**: broad scope, high brittleness, and different security/review surface.

**User data** should live in one JSON file (see `examples/my-form-data.example.json` in the repo); the LLM’s job is **semantic alignment** (infer which facts fill which detected fields — like ChatGPT reading a pasted form), not matching `name=` attributes by hand and not guessing pixels.

A future **separate** project or optional plugin could add screenshot-assisted recovery for edge cases; it is **out of scope** for the core package so this codebase stays small, testable, and KISS.
