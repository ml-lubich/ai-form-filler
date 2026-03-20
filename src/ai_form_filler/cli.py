"""CLI for AI form filler."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal

from .bootstrap import bootstrap_cli
from .constants import DEFAULT_OLLAMA_MODEL, resolved_ollama_model
from .module import AIFormModule
from .run import load_user_data

BackendName = Literal["playwright_cdp", "playwright_profile", "undetected_chrome"]


def _normalized_url(url: str | None) -> str | None:
    """Treat empty or lone '-' (common typo) as no URL."""
    if url is None:
        return None
    s = url.strip()
    if s == "" or s == "-":
        return None
    return url


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "AI-powered form filler (Playwright + Ollama). "
            "Run with no arguments (or --bootstrap) once to install Chromium and pull the default Ollama model. "
            "Then pass a URL and data, or use --goal. "
            "Undetected Chrome: uv sync --extra stealth (or pip install '.[stealth]') then --undetected."
        ),
        epilog=(
            "Examples:  ai-form-filler\n"
            "           ai-form-filler --bootstrap\n"
            "           ai-form-filler https://example.com/form data.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Install Playwright Chromium, ensure Ollama CLI/model, then exit",
    )
    parser.add_argument(
        "--no-auto-setup",
        action="store_true",
        help="Skip automatic Playwright/Ollama pull (for CI or custom images)",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Page URL with the form (omit if you use --goal)",
    )
    parser.add_argument(
        "data",
        nargs="?",
        default=None,
        help="Path to a UTF-8 file or inline string: JSON object, or any plain text the LLM should read",
    )
    parser.add_argument(
        "--goal",
        default=None,
        help="Natural-language goal; local LLM infers the URL to open (requires Ollama)",
    )
    parser.add_argument(
        "--hints",
        default=None,
        help="Optional hints for URL inference (sites, paths, constraints)",
    )
    parser.add_argument(
        "--hints-file",
        default=None,
        metavar="PATH",
        help="File whose contents are passed as hints for URL inference",
    )
    parser.add_argument(
        "--current-url",
        default=None,
        help="Current browser URL to pass to the LLM for context (optional)",
    )
    parser.add_argument(
        "--undetected",
        action="store_true",
        help="Use undetected-chromedriver + Selenium (install: pip install '.[stealth]')",
    )
    parser.add_argument(
        "--cdp-url",
        default="http://localhost:9222",
        help="CDP endpoint when using Playwright CDP (default: http://localhost:9222)",
    )
    parser.add_argument(
        "--user-data-dir",
        metavar="DIR",
        default=None,
        help="Playwright: Chrome user data dir (persistent profile). Close Chrome first.",
    )
    parser.add_argument(
        "--uc-user-data-dir",
        metavar="DIR",
        default=None,
        help="Undetected Chrome: optional user data dir",
    )
    parser.add_argument(
        "--channel",
        default="chrome",
        help="Playwright persistent context channel (default: chrome)",
    )
    parser.add_argument(
        "--model",
        default=None,
        metavar="NAME",
        help=(
            f"Ollama model tag (default: {DEFAULT_OLLAMA_MODEL!r} or env AI_FORM_FILLER_MODEL). "
            "Examples: llama3.2, mistral, gemma3, qwen2.5:7b"
        ),
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Click submit after filling",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and print form schema only (no fill). With --goal, still runs navigation LLM.",
    )
    args = parser.parse_args()
    url = _normalized_url(args.url)

    if args.bootstrap:
        bootstrap_cli(verbose=True)
        return

    if (
        url is None
        and args.data is None
        and not args.goal
        and not args.dry_run
        and not args.no_auto_setup
    ):
        bootstrap_cli(verbose=True)
        return

    if args.no_auto_setup:
        import os

        os.environ["AI_FORM_FILLER_SKIP_AUTO_PREPARE"] = "true"

    if not url and not args.goal:
        print("Error: provide a URL or --goal (or run with no args to set up)", file=sys.stderr)
        sys.exit(1)

    if args.data is None and not args.dry_run:
        print(
            "Error: data required unless --dry-run (JSON file, text file, or inline text/JSON)",
            file=sys.stderr,
        )
        sys.exit(1)

    hints: str | None = args.hints
    if args.hints_file:
        try:
            hints = Path(args.hints_file).read_text(encoding="utf-8")
        except OSError as e:
            print(f"Error reading hints file: {e}", file=sys.stderr)
            sys.exit(1)

    user_data: str | dict = "{}"
    if args.data:
        try:
            user_data = load_user_data(args.data)
        except OSError as e:
            print(f"Error loading data: {e}", file=sys.stderr)
            sys.exit(1)

    if args.undetected:
        backend_name: BackendName = "undetected_chrome"
    elif args.user_data_dir:
        backend_name = "playwright_profile"
    else:
        backend_name = "playwright_cdp"

    module = AIFormModule(
        model=args.model,
        backend=backend_name,
        cdp_url=args.cdp_url,
        user_data_dir=args.user_data_dir,
        channel=args.channel,
        uc_user_data_dir=args.uc_user_data_dir,
    )

    try:
        if args.dry_run:
            target_url = url
            if args.goal:
                intent = module.infer_navigation(
                    args.goal,
                    hints=hints,
                    current_url=args.current_url,
                )
                target_url = intent.url
                print(f"# Inferred URL: {intent.url}\n# Reason: {intent.reason}\n", file=sys.stderr)
            if not target_url:
                print("Error: --dry-run needs a URL or --goal", file=sys.stderr)
                sys.exit(1)

            if backend_name == "undetected_chrome":
                from .browser_uc import UndetectedChromeConnector
                from .form_extract import extract_form_schema_selenium

                conn = UndetectedChromeConnector(user_data_dir=args.uc_user_data_dir)
                try:
                    driver = conn.connect()
                    driver.get(target_url)
                    driver.implicitly_wait(2)
                    schema = extract_form_schema_selenium(driver)
                    print(schema.to_llm_description())
                finally:
                    conn.close()
            else:
                from .browser import CDPConnector, PersistentContextConnector
                from .form_extract import extract_form_schema

                if backend_name == "playwright_cdp":
                    conn = CDPConnector(cdp_url=args.cdp_url)
                else:
                    conn = PersistentContextConnector(
                        user_data_dir=args.user_data_dir or "",
                        channel=args.channel,
                    )
                try:
                    _, page = conn.connect()
                    page.goto(target_url, wait_until="domcontentloaded")
                    page.wait_for_load_state("networkidle", timeout=10000)
                    schema = extract_form_schema(page)
                    print(schema.to_llm_description())
                finally:
                    if hasattr(conn, "close"):
                        conn.close()
            return

        if args.goal:
            schema = module.run_from_goal(
                args.goal,
                user_data,
                hints=hints,
                current_url=args.current_url,
                submit=args.submit,
            )
        else:
            assert url is not None
            schema = module.fill_at_url(url, user_data, submit=args.submit)
        print(f"Filled {len(schema.fields)} field(s).")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
