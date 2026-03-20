"""CLI behavior: URL normalization and default bootstrap."""

import sys
from unittest.mock import patch

import pytest

from ai_form_filler.cli import _normalized_url, main


def test_normalized_url() -> None:
    assert _normalized_url(None) is None
    assert _normalized_url("") is None
    assert _normalized_url("   ") is None
    assert _normalized_url("-") is None
    assert _normalized_url("https://example.com") == "https://example.com"


def test_main_no_args_runs_bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-form-filler"])
    with patch("ai_form_filler.cli.bootstrap_cli") as mock_bootstrap:
        main()
    mock_bootstrap.assert_called_once_with(verbose=True)


def test_main_single_dash_runs_bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-form-filler", "-"])
    with patch("ai_form_filler.cli.bootstrap_cli") as mock_bootstrap:
        main()
    mock_bootstrap.assert_called_once_with(verbose=True)


def test_main_no_auto_setup_alone_skips_default_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-form-filler", "--no-auto-setup"])
    with patch("ai_form_filler.cli.bootstrap_cli") as mock_bootstrap:
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    mock_bootstrap.assert_not_called()
