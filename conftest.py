import pytest
import time
from src.core.driver import get_driver
from src.pages.login_page import LoginPage
from src.config.config import LOGIN_URL


@pytest.fixture()
def driver():
    """
    브라우저를 실행하고, 테스트가 끝나면 자동으로 닫아주는 픽스처
    """
    _driver = get_driver()
    yield _driver

    # 테스트 종료 후 브라우저 닫기 전 3초 대기
    time.sleep(3)
    _driver.quit()


@pytest.fixture()
def setup_and_login(driver):
    """
    1. 로그인 URL 접속
    2. 쿠키 및 로컬/세션 스토리지 초기화 (독립적인 테스트 환경 보장)
    3. 공통 로그인 수행
    """
    # 스크립트로 스토리지를 지우려면 먼저 해당 도메인(URL)에 접속해 있어야 합니다.
    driver.get(LOGIN_URL)

    # 쿠키 및 스토리지 완벽 초기화 (팀 코치님 지적사항 해결 포인트)
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")

    # 깨끗해진 브라우저 환경에서 로그인 진행
    login_page = LoginPage(driver)
    login_page.login()

    # 로그인이 완료된 드라이버 객체를 테스트 함수에 전달
    yield driver

    # 테스트가 모두 끝난 후 실행되는 부분
    print("\n테스트가 모두 종료되었습니다. 3초 후 브라우저를 닫습니다...")
    time.sleep(5)  # 브라우저 종료 전 3초 대기
    driver.quit()
