"""Ollama-backed LLM: map form schema + user data to a fill plan (application layer)."""

from __future__ import annotations

import json
import re

from ollama import chat

from .models import FillAction, FillPlan, FormSchema, NavigationIntent


def build_mapping_prompt(schema: FormSchema, user_data: str | dict) -> str:
    """Build the prompt for the LLM to produce field_key -> value mapping."""
    schema_text = schema.to_llm_description()
    if isinstance(user_data, dict):
        data_text = json.dumps(user_data, indent=2)
    else:
        data_text = user_data.strip()
    return f"""You are a form-filling assistant. Given a form schema and data to fill, output a JSON object that maps each form field key to the value to fill. Use only the field keys listed in the schema.

Form schema (each line is one field; key= is the identifier to use):
{schema_text}

Data to fill into the form:
{data_text}

Rules:
- Output ONLY a single JSON object: {{ "key1": value1, "key2": value2, ... }}. No markdown, no explanation.
- Use the exact field keys from the schema (key=...).
- For checkboxes use true/false.
- For selects/radios use the option value (from options list) that best matches the data.
- Omit fields that have no matching data.
"""


def parse_fill_plan_from_response(response_text: str) -> FillPlan:
    """Parse LLM response into FillPlan. Tolerates markdown code blocks."""
    text = response_text.strip()
    # Strip optional markdown code block
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("LLM did not return a JSON object")
    actions = [FillAction(field_key=k, value=v) for k, v in data.items()]
    return FillPlan(actions=actions)


def build_navigation_prompt(
    goal: str,
    hints: str | None,
    current_url: str | None,
) -> str:
    """Prompt for inferring the target URL from a natural-language goal."""
    hints_block = hints.strip() if hints else "(none — infer from goal only)"
    current = current_url or "(unknown — user has not opened a page yet)"
    return f"""You help a browser automation tool decide which URL to open to complete a task (usually to reach a form).

User goal:
{goal.strip()}

Optional hints (allowed sites, bookmarks, paths, or constraints — use only if relevant):
{hints_block}

Current browser URL (if known):
{current}

Rules:
- Output ONLY a single JSON object with keys: "url" (string, absolute https URL when possible), "reason" (short string).
- Prefer official or obvious pages for the goal (e.g. contact form, signup, checkout).
- If the goal already implies a specific URL, use it.
- Do not output markdown or any text outside the JSON.
"""


def parse_navigation_intent(response_text: str) -> NavigationIntent:
    """Parse LLM JSON into NavigationIntent."""
    text = response_text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Navigation response must be a JSON object")
    url = data.get("url")
    reason = data.get("reason", "")
    if not url or not isinstance(url, str):
        raise ValueError('Navigation JSON must include string "url"')
    if not isinstance(reason, str):
        reason = str(reason)
    return NavigationIntent(url=url.strip(), reason=reason.strip())


def infer_navigation_intent(
    goal: str,
    *,
    hints: str | None = None,
    current_url: str | None = None,
    model: str = "llama3.2",
) -> NavigationIntent:
    """Ask Ollama which URL to open for the given goal."""
    prompt = build_navigation_prompt(goal, hints, current_url)
    response = chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("Ollama returned empty navigation response")
    return parse_navigation_intent(content)


def get_fill_plan(schema: FormSchema, user_data: str | dict, model: str = "llama3.2") -> FillPlan:
    """Call Ollama to compute fill plan from form schema and user data."""
    prompt = build_mapping_prompt(schema, user_data)
    response = chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("Ollama returned empty response")
    return parse_fill_plan_from_response(content)
