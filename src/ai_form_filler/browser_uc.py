"""Undetected ChromeDriver: lighter stealth than stock automation (optional dependency)."""

from __future__ import annotations

import re
import subprocess
from typing import Any


def _detect_chrome_major_version(browser_executable_path: str | None) -> int | None:
    """Match ChromeDriver major to installed Chrome (avoids uc default mismatch)."""
    try:
        import undetected_chromedriver as uc

        exe = browser_executable_path or uc.find_chrome_executable()
        if not exe:
            return None
        proc = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        text = (proc.stdout or proc.stderr or "").strip()
        m = re.search(r"(?:Google Chrome|Chromium)\s+(\d+)\.", text)
        if m:
            return int(m.group(1))
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    return None


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
        version_main: int | None = None,
    ) -> None:
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.browser_executable_path = browser_executable_path
        self.version_main = version_main
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

        vm = self.version_main
        if vm is None:
            vm = _detect_chrome_major_version(self.browser_executable_path)

        self._driver = uc.Chrome(
            options=options,
            headless=self.headless,
            use_subprocess=True,
            version_main=vm,
        )
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            finally:
                self._driver = None
