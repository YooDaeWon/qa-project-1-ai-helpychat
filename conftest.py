from __future__ import annotations

import os
import re
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


def _clear_session(driver: webdriver.Chrome) -> None:
    """쿠키와 로컬/세션 스토리지를 비웁니다.
    (아직 사이트에 접속 전이면 스토리지 접근이 막히므로 try로 감쌉니다.)"""
    driver.delete_all_cookies()
    driver.execute_script(
        "try { window.localStorage.clear(); window.sessionStorage.clear(); } catch (e) {}"
    )


def _save_failure_screenshot(driver, node, settings) -> None:
    """테스트가 실패한 경우에만 실패 화면을 artifacts/failures에 저장합니다.
    파일명은 파라미터 케이스의 특수문자를 제거해 안전하게 만듭니다."""
    report = getattr(node, "rep_call", None)
    if report is None or not report.failed:
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", node.name)
    screenshot_path = settings.artifacts_dir / "failures" / f"{safe_name}_{timestamp}.png"
    try:
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(screenshot_path))
        print(f"실패 화면 저장 완료: {screenshot_path}")
    except Exception as error:
        print(f"실패 화면 저장 실패: {error}")


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

    _save_failure_screenshot(browser, request.node, settings)

    browser.quit()


@pytest.fixture
def setup_and_login(driver: webdriver.Chrome) -> webdriver.Chrome:
    """브라우저 상태를 초기화하고 로그인한 드라이버를 제공합니다."""

    # 로그인 페이지 접속
    driver.get(LOGIN_URL)

    # 쿠키 및 스토리지 초기화 (유대원 브랜치 기능 반영)
    _clear_session(driver)

    # 로그인
    LoginPage(driver).login()

    yield driver


@pytest.fixture
def history_page(driver: webdriver.Chrome) -> HistoryPage:
    """히스토리 테스트용 Page Object fixture입니다."""
    return HistoryPage(driver)


@pytest.fixture(scope="module")
def shared_driver(request: pytest.FixtureRequest) -> webdriver.Chrome:
    """로그인하지 않는 테스트용 공유 브라우저.
    (모듈 단위로 1회만 열리고, 해당 파일의 테스트가 끝나면 바로 닫힘)"""
    headless = bool(request.config.getoption("--headless"))
    browser = get_driver(headless=headless)
    yield browser
    browser.quit()


@pytest.fixture(autouse=True)
def _reset_shared_driver(request: pytest.FixtureRequest) -> None:
    """shared_driver를 사용하는 테스트의 세션을 초기화하고,
    실패 시 driver fixture와 동일하게 실패 화면을 저장합니다."""
    uses_shared = "shared_driver" in request.fixturenames
    settings = None
    drv = None
    if uses_shared:
        # teardown에서 fixture를 새로 요청하면 에러가 되므로 setup에서 미리 확보한다.
        settings = request.getfixturevalue("settings")
        drv = request.getfixturevalue("shared_driver")
        _clear_session(drv)

    yield

    if uses_shared:
        _save_failure_screenshot(drv, request.node, settings)


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


# ==============================================================================
# test008 등 단일 브라우저 유지가 필요한 테스트용 추가 픽스처
# (이름을 다르게 지정했으므로 기존 팀원들의 테스트 코드와 충돌하지 않습니다)
# ==============================================================================


@pytest.fixture(scope="module")
def module_driver(request: pytest.FixtureRequest) -> webdriver.Chrome:
    headless = bool(request.config.getoption("--headless"))
    browser = get_driver(headless=headless)
    yield browser
    browser.quit()


@pytest.fixture(scope="module")
def module_setup_and_login(module_driver: webdriver.Chrome) -> webdriver.Chrome:
    module_driver.get(LOGIN_URL)
    _clear_session(module_driver)
    LoginPage(module_driver).login()
    yield module_driver


@pytest.fixture(autouse=True)
def _test008_screenshot(request: pytest.FixtureRequest) -> None:
    uses_module = "module_setup_and_login" in request.fixturenames

    # teardown에서 fixture를 새로 요청하면 에러가 되므로 setup에서 미리 확보한다.
    settings = None
    drv = None
    if uses_module:
        settings = request.getfixturevalue("settings")
        drv = request.getfixturevalue("module_setup_and_login")

    yield

    if uses_module:
        _save_failure_screenshot(drv, request.node, settings)
