"""Browser connection: CDP (existing browser) or persistent context (your profile)."""

from __future__ import annotations

from typing import Protocol

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


class BrowserConnector(Protocol):
    """Protocol for obtaining a browser context and page."""

    def connect(self) -> tuple[Browser | BrowserContext, Page]:
        """Return (browser_or_context, page). Caller must close when done."""
        ...


def _ensure_page(context: Browser | BrowserContext) -> Page:
    if isinstance(context, Browser):
        ctx = context.contexts[0] if context.contexts else None
        if not ctx:
            raise RuntimeError("No browser context; ensure browser has at least one page open.")
        pages = ctx.pages
    else:
        pages = context.pages
    if not pages:
        raise RuntimeError("No page open. Open a tab to the form URL first.")
    return pages[0]


class CDPConnector:
    """Connect to an existing browser via Chrome DevTools Protocol.
    User must start Chrome with: --remote-debugging-port=9222
    """

    def __init__(self, cdp_url: str = "http://localhost:9222") -> None:
        self.cdp_url = cdp_url.rstrip("/")
        self._playwright = None
        self._browser: Browser | None = None

    def connect(self) -> tuple[Browser, Page]:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        page = _ensure_page(self._browser)
        return self._browser, page

    def close(self) -> None:
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None


class PersistentContextConnector:
    """Launch Chromium with a persistent user data dir (your profile).
    Close all Chromium/Chrome windows before using, or use a copy of the profile.
    """

    def __init__(
        self,
        user_data_dir: str,
        channel: str | None = "chrome",  # "chrome" uses installed Chrome
        headless: bool = False,
    ) -> None:
        self.user_data_dir = user_data_dir
        self.channel = channel
        self.headless = headless
        self._playwright = None
        self._context: BrowserContext | None = None

    def connect(self) -> tuple[BrowserContext, Page]:
        p = sync_playwright().start()
        self._playwright = p
        opts: dict = {
            "headless": self.headless,
            "channel": self.channel,
        }
        if self.channel is None:
            opts.pop("channel", None)
        self._context = p.chromium.launch_persistent_context(
            self.user_data_dir,
            **opts,
        )
        if not self._context.pages:
            page = self._context.new_page()
        else:
            page = self._context.pages[0]
        return self._context, page

    def close(self) -> None:
        if self._context:
            self._context.close()
            self._context = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
