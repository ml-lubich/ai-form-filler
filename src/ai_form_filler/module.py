"""Reusable AI module: infer where to go (LLM) + fill forms (Playwright or undetected Chrome)."""

from __future__ import annotations

from typing import Literal

from .browser import CDPConnector, PersistentContextConnector
from .browser_uc import UndetectedChromeConnector
from .filler import apply_fill_plan
from .form_extract import extract_form_schema, extract_form_schema_selenium
from .llm import get_fill_plan, infer_navigation_intent
from .models import FormSchema, NavigationIntent

Backend = Literal["playwright_cdp", "playwright_profile", "undetected_chrome"]


class AIFormModule:
    """High-level API: navigation inference + form filling.

    Step-by-step usage:
    1. Create ``AIFormModule(model=..., backend=...)``.
    2. Optionally call ``infer_navigation(goal, hints=..., current_url=...)`` to get a URL from the LLM.
    3. Call ``fill_at_url(url, user_data)`` to extract the form, plan fills with Ollama, and apply them.
    Or use ``run_from_goal(goal, user_data)`` to do (2)+(3) in one call.
    """

    def __init__(
        self,
        model: str = "llama3.2",
        backend: Backend = "playwright_cdp",
        *,
        cdp_url: str = "http://localhost:9222",
        user_data_dir: str | None = None,
        channel: str = "chrome",
        uc_headless: bool = False,
        uc_user_data_dir: str | None = None,
        uc_browser_executable_path: str | None = None,
    ) -> None:
        self.model = model
        self.backend = backend
        self.cdp_url = cdp_url
        self.user_data_dir = user_data_dir
        self.channel = channel
        self.uc_headless = uc_headless
        self.uc_user_data_dir = uc_user_data_dir
        self.uc_browser_executable_path = uc_browser_executable_path

    def infer_navigation(
        self,
        goal: str,
        *,
        hints: str | None = None,
        current_url: str | None = None,
    ) -> NavigationIntent:
        """Use the local LLM to infer which URL to open for ``goal``."""
        return infer_navigation_intent(
            goal,
            hints=hints,
            current_url=current_url,
            model=self.model,
        )

    def infer_url(
        self,
        goal: str,
        *,
        hints: str | None = None,
        current_url: str | None = None,
    ) -> str:
        """Return only the URL string from navigation inference."""
        return self.infer_navigation(goal, hints=hints, current_url=current_url).url

    def fill_at_url(
        self,
        url: str,
        user_data: str | dict,
        *,
        submit: bool = False,
    ) -> FormSchema:
        """Navigate to ``url``, extract form, get fill plan from Ollama, apply fills."""
        if self.backend == "undetected_chrome":
            return self._fill_at_url_selenium(url, user_data, submit=submit)
        return self._fill_at_url_playwright(url, user_data, submit=submit)

    def run_from_goal(
        self,
        goal: str,
        user_data: str | dict,
        *,
        hints: str | None = None,
        current_url: str | None = None,
        submit: bool = False,
    ) -> FormSchema:
        """Infer URL from ``goal``, then fill the form at that URL."""
        intent = self.infer_navigation(goal, hints=hints, current_url=current_url)
        return self.fill_at_url(intent.url, user_data, submit=submit)

    def _fill_at_url_playwright(
        self,
        url: str,
        user_data: str | dict,
        *,
        submit: bool,
    ) -> FormSchema:
        if self.backend == "playwright_cdp":
            connector = CDPConnector(cdp_url=self.cdp_url)
        elif self.backend == "playwright_profile":
            if not self.user_data_dir:
                raise ValueError("playwright_profile requires user_data_dir")
            connector = PersistentContextConnector(
                user_data_dir=self.user_data_dir,
                channel=self.channel,
                headless=False,
            )
        else:
            raise RuntimeError("internal: wrong backend for Playwright fill")

        try:
            _, page = connector.connect()
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=10000)

            schema = extract_form_schema(page)
            if schema.fields:
                plan = get_fill_plan(schema, user_data, model=self.model)
                apply_fill_plan(page, schema, plan)

            if submit:
                submit_btn = page.locator(
                    'input[type="submit"], button[type="submit"], button:has-text("Submit"), '
                    'button:has-text("Send"), [type="submit"]'
                ).first
                if submit_btn.count() > 0:
                    submit_btn.click()

            return schema
        finally:
            if hasattr(connector, "close"):
                connector.close()

    def _fill_at_url_selenium(
        self,
        url: str,
        user_data: str | dict,
        *,
        submit: bool,
    ) -> FormSchema:
        from .filler_selenium import apply_fill_plan_selenium, click_submit_selenium

        connector = UndetectedChromeConnector(
            headless=self.uc_headless,
            user_data_dir=self.uc_user_data_dir,
            browser_executable_path=self.uc_browser_executable_path,
        )
        try:
            driver = connector.connect()
            driver.get(url)
            driver.implicitly_wait(2)

            schema = extract_form_schema_selenium(driver)
            if schema.fields:
                plan = get_fill_plan(schema, user_data, model=self.model)
                apply_fill_plan_selenium(driver, schema, plan)

            if submit:
                click_submit_selenium(driver)

            return schema
        finally:
            connector.close()
