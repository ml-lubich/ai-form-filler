"""Unit tests for navigation inference parsing."""

import pytest

from ai_form_filler.llm import parse_navigation_intent


def test_parse_navigation_intent_raw_json() -> None:
    raw = '{"url": "https://example.com/contact", "reason": "Contact page"}'
    intent = parse_navigation_intent(raw)
    assert intent.url == "https://example.com/contact"
    assert "Contact" in intent.reason


def test_parse_navigation_intent_markdown_fence() -> None:
    raw = '```json\n{"url": "https://a.com", "reason": "x"}\n```'
    intent = parse_navigation_intent(raw)
    assert intent.url == "https://a.com"


def test_parse_navigation_intent_missing_url_raises() -> None:
    with pytest.raises(ValueError):
        parse_navigation_intent('{"reason": "no url"}')
