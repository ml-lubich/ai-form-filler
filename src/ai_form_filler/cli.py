"""CLI for AI form filler."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Literal

from .module import AIFormModule

BackendName = Literal["playwright_cdp", "playwright_profile", "undetected_chrome"]
from .run import load_user_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "AI-powered form filler (Playwright + Ollama). "
            "Use --goal so the local LLM infers which URL to open, or pass a URL directly. "
            "Optional undetected-chromedriver backend: pip install '.[stealth]' --undetected."
        )
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
        help='JSON file or inline JSON (e.g. {"email":"a@b.com"})',
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
        default="llama3.2",
        help="Ollama model (default: llama3.2); e.g. qwen2.5",
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

    if not args.url and not args.goal:
        print("Error: provide a URL or --goal", file=sys.stderr)
        sys.exit(1)

    if args.data is None and not args.dry_run:
        print("Error: data (JSON file or inline JSON) required unless --dry-run", file=sys.stderr)
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
        except (json.JSONDecodeError, OSError) as e:
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
            target_url = args.url
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
            assert args.url is not None
            schema = module.fill_at_url(args.url, user_data, submit=args.submit)
        print(f"Filled {len(schema.fields)} field(s).")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
