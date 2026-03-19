"""Apply fill plan via Selenium WebDriver (application layer)."""

from __future__ import annotations

from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from .models import FillAction, FillPlan, FormField, FormSchema


def _find_element(driver: WebDriver, field: FormField, timeout_sec: float = 10.0) -> Any:
    """Locate element by id, name, or label text."""
    wait = WebDriverWait(driver, timeout_sec)
    if field.id:
        return wait.until(EC.presence_of_element_located((By.ID, field.id)))
    if field.name:
        return wait.until(EC.presence_of_element_located((By.NAME, field.name)))
    if field.label_text:
        # XPath: label containing text, then first following input/textarea/select
        fragment = field.label_text.strip()[:120].replace('"', "").replace("\n", " ")
        xpath = (
            f'//label[contains(normalize-space(.), "{fragment}")]'
            "/following::*[self::input or self::textarea or self::select][1]"
        )
        return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    raise RuntimeError(f"Cannot locate field with key={field.key!r}")


def apply_fill_action_selenium(
    driver: WebDriver,
    schema: FormSchema,
    action: FillAction,
    timeout_sec: float = 10.0,
) -> None:
    """Apply one fill action using Selenium."""
    field = schema.get_field_by_key(action.field_key)
    if not field:
        return
    value = action.value

    if field.input_type == "radio":
        if field.name:
            selector = f'input[type="radio"][name="{field.name}"][value="{value}"]'
            el = WebDriverWait(driver, timeout_sec).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            if not el.is_selected():
                el.click()
        return

    el = _find_element(driver, field, timeout_sec=timeout_sec)

    if field.input_type == "checkbox":
        if value in (True, "true", "1", "yes", "on"):
            if not el.is_selected():
                el.click()
        else:
            if el.is_selected():
                el.click()
        return

    if field.tag == "select":
        Select(el).select_by_value(str(value))
        return

    el.clear()
    el.send_keys(str(value))


def apply_fill_plan_selenium(
    driver: WebDriver,
    schema: FormSchema,
    plan: FillPlan,
    timeout_sec: float = 10.0,
) -> None:
    """Apply full fill plan via Selenium."""
    for action in plan.actions:
        apply_fill_action_selenium(driver, schema, action, timeout_sec=timeout_sec)


def click_submit_selenium(driver: WebDriver, timeout_sec: float = 10.0) -> bool:
    """Click first plausible submit control; return True if clicked."""
    wait = WebDriverWait(driver, timeout_sec)
    selectors = [
        (By.CSS_SELECTOR, 'input[type="submit"]'),
        (By.CSS_SELECTOR, 'button[type="submit"]'),
        (By.XPATH, "//button[contains(translate(., 'SUBMIT', 'submit'), 'submit')]"),
    ]
    for by, sel in selectors:
        try:
            el = wait.until(EC.element_to_be_clickable((by, sel)))
            el.click()
            return True
        except Exception:
            continue
    return False
