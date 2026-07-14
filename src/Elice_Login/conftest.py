import os
import pytest
from dotenv import load_dotenv, find_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv(find_dotenv())  # 실행 위치와 무관하게 상위로 올라가며 .env 탐색


@pytest.fixture
def driver():
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
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def shared_driver():
    """로그인하지 않는 테스트용 공유 브라우저 (전체 실행에서 1회만 열림).
    로그인 상태를 만드는 테스트(TID 40, 57)는 격리를 위해 driver를 사용할 것."""
    options = webdriver.ChromeOptions()
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        },
    )
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def credentials():
    return {
        "url": os.environ["LOGIN_URL"],
        "email": os.environ["LOGIN_EMAIL"],
        "password": os.environ["LOGIN_PASSWORD"],
    }


@pytest.fixture
def logged_in_driver(driver, credentials):
    """로그인이 완료된 브라우저를 제공.
    로그인 자체를 테스트하는 게 아니라, 로그인 이후 화면을 테스트하는 팀원용."""
    driver.get(credentials["url"])

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.NAME, "loginId"))
    ).send_keys(credentials["email"])
    driver.find_element(By.NAME, "password").send_keys(credentials["password"])
    driver.find_element(
        By.CSS_SELECTOR, "form[data-cy='signin-form'] button[type='submit']"
    ).click()

    # 로그인 완료(프로필 아이콘 등장)까지 대기 후 넘겨줌
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='PersonIcon']"))
    )
    return driver
