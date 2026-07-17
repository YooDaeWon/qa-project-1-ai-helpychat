from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from src.config.config import PAGE_WAIT_TIME, Settings, load_settings
from src.pages.login_page import LoginPage


def login_if_needed(driver: webdriver.Chrome, settings: Settings | None = None) -> None:
    """Run the shared login flow when the current page requires it."""
    if settings is None:
        settings = load_settings()

    login_page = LoginPage(driver, timeout=settings.default_wait_time)
    login_page.login_if_needed(
        base_url=settings.base_url,
        login_email=settings.login_email,
        login_password=settings.login_password,
    )


def wait_for_login_or_page(driver: webdriver.Chrome, ready_condition) -> None:
    """Wait until either the login page or the supplied service-page condition is ready."""
    login_page = LoginPage(driver)
    WebDriverWait(driver, PAGE_WAIT_TIME).until(
        lambda _: login_page.is_login_page() or ready_condition()
    )
