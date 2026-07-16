<<<<<<< HEAD
from __future__ import annotations

=======
>>>>>>> 유대원
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


<<<<<<< HEAD
def create_chrome_options(headless: bool = False) -> Options:
    """Chrome 실행 옵션을 생성합니다."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")

    # Chrome '비밀번호 유출 감지' 팝업이 로그인 테스트를 막지 않도록 비활성화
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        },
    )

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
=======
def get_driver():
    """
    Chrome WebDriver 생성
    """

    options = Options()

    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    return driver
>>>>>>> 유대원
