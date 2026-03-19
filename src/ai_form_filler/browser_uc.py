"""Undetected ChromeDriver: lighter stealth than stock automation (optional dependency)."""

from __future__ import annotations

from typing import Any


class UndetectedChromeConnector:
    """Launch Chrome via undetected-chromedriver (Selenium).

    Install: pip install "ai-form-filler[stealth]"
    """

    def __init__(
        self,
        *,
        headless: bool = False,
        user_data_dir: str | None = None,
        browser_executable_path: str | None = None,
    ) -> None:
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.browser_executable_path = browser_executable_path
        self._driver: Any = None

    def connect(self) -> Any:
        try:
            import undetected_chromedriver as uc
        except ImportError as e:
            raise ImportError(
                'undetected-chromedriver is not installed. Run: pip install "ai-form-filler[stealth]"'
            ) from e

        options = uc.ChromeOptions()
        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
        if self.browser_executable_path:
            options.binary_location = self.browser_executable_path

        self._driver = uc.Chrome(options=options, headless=self.headless, use_subprocess=True)
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            finally:
                self._driver = None
