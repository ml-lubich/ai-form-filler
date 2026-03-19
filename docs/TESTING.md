# Testing

## Strategy

- **Unit**: Pure domain and small application functions where I/O can be injected or mocked (e.g. prompt building, parsing LLM response).
- **Integration**: Form extraction and fill execution require a real browser and (for full flow) Ollama; optional integration tests can use a local HTML form and a running Ollama.

## Running tests

From the project root:

```bash
pip install -e ".[dev]"
pytest
```

## Coverage expectations

- Domain models and `to_llm_description` / `get_field_by_key`: covered by unit tests.
- `build_mapping_prompt`, `parse_fill_plan_from_response`, `parse_navigation_intent`: unit tests with no live Ollama.
- Form extraction and filler: integration tests against a static HTML form; Ollama can be mocked for the mapping step or run locally.

## Verification (manual)

1. Start Chrome with `--remote-debugging-port=9222`.
2. Open a page with a simple form (e.g. https://httpbin.org/forms/post or a local HTML file).
3. Run:  
   `ai-form-filler "<url>" '{"custname":"Test","custemail":"a@b.com"}'`  
   and confirm fields are filled.
4. Run:  
   `ai-form-filler "<url>" --dry-run`  
   and confirm the printed schema matches the form.
