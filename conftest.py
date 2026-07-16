from __future__ import annotations

import time
from datetime import datetime

import pytest
from selenium import webdriver

from src.config.config import LOGIN_URL, Settings, load_settings
from src.core.driver import get_driver
from src.pages.login_page import LoginPage


def pytest_addoption(parser: pytest.Parser) -> None:
    """에이전트 테스트용 pytest 실행 옵션을 등록합니다."""
    parser.addoption(
        "--create-count",
        action="store",
        default="1",
        help="생성할 에이전트 개수입니다. 기본값: 1",
    )
    parser.addoption(
        "--delete-mode",
        action="store",
        default="automation",
        choices=("automation", "all"),
        help="automation: 자동화 테스트 에이전트만 삭제, all: 전체 삭제",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Chrome을 headless 모드로 실행합니다.",
    )


@pytest.fixture(scope="session")
def settings() -> Settings:
    """.env와 공통 설정을 pytest 세션에서 한 번 불러옵니다."""
    return load_settings()


@pytest.fixture
def create_count(request: pytest.FixtureRequest) -> int:
    raw_value = str(request.config.getoption("--create-count")).strip()
    if not raw_value.isdigit() or int(raw_value) <= 0:
        raise pytest.UsageError("--create-count에는 1 이상의 정수를 입력해야 합니다.")
    return int(raw_value)


@pytest.fixture
def delete_mode(request: pytest.FixtureRequest) -> str:
    return str(request.config.getoption("--delete-mode"))


@pytest.fixture
def driver(
    request: pytest.FixtureRequest,
    settings: Settings,
) -> webdriver.Chrome:
    """각 테스트 전 브라우저를 만들고 종료 시 정리합니다."""
    headless = bool(request.config.getoption("--headless"))
    browser = get_driver(headless=headless)

    yield browser

    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = (
            settings.artifacts_dir
            / "failures"
            / f"{request.node.name}_{timestamp}.png"
        )
        try:
            browser.save_screenshot(str(screenshot_path))
            print(f"실패 화면 저장 완료: {screenshot_path}")
        except Exception as error:
            print(f"실패 화면 저장 실패: {error}")

    # 기존 팀 테스트의 브라우저 종료 전 대기를 유지합니다.
    time.sleep(3)
    browser.quit()


@pytest.fixture
def setup_and_login(driver: webdriver.Chrome) -> webdriver.Chrome:
    """브라우저 상태를 초기화하고 로그인한 드라이버를 제공합니다."""
    driver.get(LOGIN_URL)
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")

    LoginPage(driver).login()

    yield driver


@pytest.fixture
def logged_in_driver(setup_and_login: webdriver.Chrome) -> webdriver.Chrome:
    """이름이 명확한 로그인 완료 드라이버 별칭 fixture입니다."""
    return setup_and_login


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
