from __future__ import annotations

from selenium import webdriver

from src.config.config import Settings
from src.pages.login_page import LoginPage


def login_if_needed(driver: webdriver.Chrome, settings: Settings) -> None:
    """공통 로그인 절차를 실행합니다."""
    login_page = LoginPage(driver, timeout=settings.default_wait_time)
    login_page.login_if_needed(
        base_url=settings.base_url,
        login_email=settings.login_email,
        login_password=settings.login_password,
    )
