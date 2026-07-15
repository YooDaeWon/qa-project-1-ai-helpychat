# -*- coding: utf-8 -*-
import os
import pytest
from dotenv import load_dotenv, find_dotenv
from selenium import webdriver

load_dotenv(find_dotenv())  # 실행 위치와 무관하게 상위로 올라가며 .env 탐색


def _make_driver():
    """공통 옵션이 적용된 Chrome 드라이버 생성."""
    options = webdriver.ChromeOptions()
    # Chrome '비밀번호 유출 감지' 팝업이 테스트를 막지 않도록 비활성화
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        },
    )
    drv = webdriver.Chrome(options=options)
    drv.maximize_window()
    return drv


@pytest.fixture
def driver():
    """테스트마다 새로 열리는 격리된 브라우저."""
    drv = _make_driver()
    yield drv
    drv.quit()


@pytest.fixture(scope="session")
def shared_driver():
    """로그인하지 않는 테스트용 공유 브라우저 (전체 실행에서 1회만 열림).
    로그인 상태를 만드는 테스트(TID 41, 58)는 격리를 위해 driver를 사용할 것."""
    drv = _make_driver()
    yield drv
    drv.quit()


@pytest.fixture(autouse=True)
def _reset_shared_driver(request):
    """shared_driver를 쓰는 테스트 시작 전에 쿠키를 비워,
    앞선 테스트에서 세션이 생겨도 다음 테스트로 새어가지 않게 한다."""
    if "shared_driver" in request.fixturenames:
        request.getfixturevalue("shared_driver").delete_all_cookies()


@pytest.fixture(scope="session")
def credentials():
    return {
        "url": os.environ["LOGIN_URL"],
        "email": os.environ["LOGIN_EMAIL"],
        "password": os.environ["LOGIN_PASSWORD"],
    }
