from __future__ import annotations

import os
import time
from datetime import datetime

import pytest
from selenium import webdriver

from src.config.config import (
    LOGIN_EMAIL,
    LOGIN_PASSWORD,
    LOGIN_URL,
    Settings,
    load_settings,
)
from src.core.driver import get_driver
from src.pages.history_page import HistoryPage
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
    parser.addoption(
        "--interactive-history-delete",
        action="store_true",
        default=False,
        help="다중 삭제 테스트 실행 중 삭제할 히스토리 개수를 직접 입력합니다.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """삭제 개수가 없는 전체 실행에서는 다중 삭제 테스트를 미리 건너뜁니다."""
    has_delete_count = os.getenv("HISTORY_DELETE_COUNT") is not None
    interactive = bool(config.getoption("--interactive-history-delete"))
    if has_delete_count or interactive:
        return

    skip_bulk_delete = pytest.mark.skip(
        reason=(
            "HISTORY_DELETE_COUNT 또는 --interactive-history-delete가 없어 "
            "다중 삭제 테스트를 건너뜁니다."
        )
    )
    for item in items:
        if "history_bulk_delete" in item.keywords:
            item.add_marker(skip_bulk_delete)


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
            settings.artifacts_dir / "failures" / f"{request.node.name}_{timestamp}.png"
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

    # 로그인 페이지 접속
    driver.get(LOGIN_URL)

    # 쿠키 및 스토리지 초기화 (유대원 브랜치 기능 반영)
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")

    # 로그인
    LoginPage(driver).login()

    yield driver


@pytest.fixture
def logged_in_driver(setup_and_login: webdriver.Chrome) -> webdriver.Chrome:
    """이름이 명확한 로그인 완료 드라이버 별칭 fixture입니다."""
    return setup_and_login


@pytest.fixture
def history_page(driver: webdriver.Chrome) -> HistoryPage:
    """히스토리 테스트용 Page Object fixture입니다."""
    return HistoryPage(driver)


@pytest.fixture
def login_page(driver: webdriver.Chrome) -> LoginPage:
    """히스토리 재로그인 테스트에서 사용하는 로그인 Page Object fixture입니다."""
    return LoginPage(driver)


@pytest.fixture(scope="session")
def shared_driver(request: pytest.FixtureRequest) -> webdriver.Chrome:
    """로그인하지 않는 테스트용 공유 브라우저 (전체 실행에서 1회만 열림)."""
    headless = bool(request.config.getoption("--headless"))
    browser = get_driver(headless=headless)
    yield browser
    browser.quit()


@pytest.fixture(autouse=True)
def _reset_shared_driver(request: pytest.FixtureRequest) -> None:
    """shared_driver를 사용하는 테스트의 세션을 초기화합니다."""
    if "shared_driver" in request.fixturenames:
        drv = request.getfixturevalue("shared_driver")
        drv.delete_all_cookies()
        drv.execute_script(
            "try { window.localStorage.clear(); window.sessionStorage.clear(); } catch (e) {}"
        )


@pytest.fixture(scope="session")
def credentials() -> dict:
    """로그인 테스트에서 사용하는 계정 정보 (.env 값)."""
    return {
        "url": LOGIN_URL,
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD,
    }


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
