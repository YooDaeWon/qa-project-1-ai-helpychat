from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def create_chrome_options(headless: bool = False) -> Options:
    """Chrome 실행 옵션을 생성합니다."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    return options


def create_driver(headless: bool = False) -> webdriver.Chrome:
    """Selenium Chrome WebDriver를 생성합니다."""
    driver = webdriver.Chrome(options=create_chrome_options(headless=headless))
    driver.set_page_load_timeout(40)
    return driver


def get_driver(headless: bool = False) -> webdriver.Chrome:
    """기존 팀 테스트와 호환되는 WebDriver 생성 함수입니다."""
    return create_driver(headless=headless)
