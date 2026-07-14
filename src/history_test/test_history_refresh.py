import os
import time
from datetime import datetime
from pathlib import Path

import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


# 현재 프로젝트의 .env 파일을 읽어 환경변수로 등록합니다.
load_dotenv()

# .env에 LOGIN_URL이 없을 때 사용할 기본 테스트 주소입니다.
DEFAULT_URL = (
    "https://dev-qaproject-helpy-chat.dev.elicer.io/"
    "?isFirstLogin=true#agents-organization"
)
URL = os.getenv("LOGIN_URL", DEFAULT_URL)

# 화면별 최대 대기시간과 테스트 종료 전 대기시간입니다.
DEFAULT_TIMEOUT = 90
LOGIN_TIMEOUT = 30
CHAT_READY_TIMEOUT = 180
FINISH_DELAY = 2

# 로그인 화면의 이메일 및 비밀번호 입력창 선택자입니다.
PASSWORD_LOCATOR = (By.CSS_SELECTOR, "input[type='password']")
EMAIL_LOCATOR = (
    By.CSS_SELECTOR,
    "input[type='email'], input[placeholder='Email']",
)

# 실제 입력창 구조가 바뀌어도 대응할 수 있도록 여러 선택자를 순서대로 확인합니다.
CHAT_INPUT_LOCATORS = [
    (By.CSS_SELECTOR, "textarea[placeholder*='메시지']"),
    (By.CSS_SELECTOR, "textarea[placeholder*='질문']"),
    (By.CSS_SELECTOR, "textarea"),
    (By.CSS_SELECTOR, "[contenteditable='true'][role='textbox']"),
    (By.CSS_SELECTOR, "[contenteditable='true']"),
]

# Enter가 메시지를 전송하지 못할 때 사용할 전송 버튼 후보입니다.
SEND_BUTTON_LOCATORS = [
    (By.CSS_SELECTOR, "button[type='submit']"),
    (By.CSS_SELECTOR, "button[aria-label*='전송']"),
    (By.CSS_SELECTOR, "button[aria-label*='보내기']"),
    (By.CSS_SELECTOR, "button[title*='전송']"),
    (By.CSS_SELECTOR, "button[title*='보내기']"),
]


def normalize_text(text: str) -> str:
    """여러 공백과 줄바꿈을 하나의 공백으로 변환합니다."""
    return " ".join(text.split())


def find_first_visible(driver, locators):
    """후보 선택자 중 현재 화면에서 사용할 수 있는 첫 요소를 찾습니다."""
    for locator in locators:
        try:
            for element in driver.find_elements(*locator):
                if element.is_displayed() and element.is_enabled():
                    return element
        except StaleElementReferenceException:
            continue

    return False


def wait_for_visible(driver, locators, timeout=DEFAULT_TIMEOUT):
    """지정한 요소가 화면에 나타날 때까지 기다립니다."""
    return WebDriverWait(driver, timeout).until(
        lambda current_driver: find_first_visible(
            current_driver,
            locators,
        )
    )


def find_history_item(driver, expected_text: str):
    """왼쪽 영역에서 예상 문구가 포함된 히스토리 항목을 찾습니다."""
    # 브라우저 폭을 기준으로 왼쪽 45% 영역만 검색 대상으로 사용합니다.
    window_width = driver.execute_script("return window.innerWidth")
    candidates = []

    for element in driver.find_elements(
        By.CSS_SELECTOR,
        "a, button, [role='button'], li",
    ):
        try:
            if not element.is_displayed():
                continue

            text = normalize_text(element.text)
            rect = element.rect
            width = rect.get("width", 0)
            height = rect.get("height", 0)

            # 예상 문구가 없거나 화면 오른쪽에 있는 요소는 제외합니다.
            if not text or expected_text not in text:
                continue
            if rect.get("x", 0) > window_width * 0.45:
                continue
            if width <= 0 or height <= 0:
                continue

            # 같은 문구를 가진 부모/자식 요소가 모두 검색될 수 있어 면적도 저장합니다.
            candidates.append((width * height, element))
        except StaleElementReferenceException:
            continue

    # 가장 작은 요소가 실제 클릭 대상일 가능성이 높으므로 우선 선택합니다.
    return min(candidates, key=lambda item: item[0])[1] if candidates else False


def is_message_visible_in_chat(driver, expected_text: str) -> bool:
    """오른쪽 대화 영역에 테스트 메시지가 표시됐는지 확인합니다."""
    window_width = driver.execute_script("return window.innerWidth")

    for element in driver.find_elements(
        By.CSS_SELECTOR,
        "p, span, div, article, [role='listitem']",
    ):
        try:
            if not element.is_displayed():
                continue
            # 왼쪽 히스토리 영역의 같은 문구가 메시지로 오인되지 않게 제외합니다.
            if element.rect.get("x", 0) < window_width * 0.22:
                continue

            text = normalize_text(element.text)

            # 너무 긴 텍스트는 페이지 전체를 감싼 부모 요소일 수 있어 제외합니다.
            if expected_text in text and len(text) <= len(expected_text) + 100:
                return True
        except StaleElementReferenceException:
            continue

    return False


def wait_for_message(driver, message: str, timeout=DEFAULT_TIMEOUT):
    """대화 영역에 특정 메시지가 나타날 때까지 기다립니다."""
    return WebDriverWait(driver, timeout).until(
        lambda current_driver: is_message_visible_in_chat(
            current_driver,
            message,
        )
    )


def wait_for_history(driver, history_key: str, timeout=DEFAULT_TIMEOUT):
    """왼쪽 히스토리에 특정 항목이 나타날 때까지 기다립니다."""
    return WebDriverWait(driver, timeout).until(
        lambda current_driver: find_history_item(
            current_driver,
            history_key,
        )
    )


def enter_chat_message(element, message: str):
    """textarea와 contenteditable 입력창에 메시지를 입력합니다."""
    element.click()

    # 일반 입력창과 contenteditable 입력창은 기존 값 삭제 방법이 다릅니다.
    if element.get_attribute("contenteditable") == "true":
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.BACKSPACE)
    else:
        element.clear()

    element.send_keys(message)


def click_element(driver, element):
    """요소를 화면 중앙으로 이동한 뒤 클릭합니다."""
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        element,
    )

    try:
        element.click()
    except ElementClickInterceptedException:
        # 다른 요소가 클릭을 가로막으면 JavaScript 클릭으로 한 번 더 시도합니다.
        driver.execute_script("arguments[0].click();", element)


def find_login_button(driver):
    """화면에 표시되고 활성화된 Login 버튼을 찾습니다."""
    for button in driver.find_elements(By.CSS_SELECTOR, "button"):
        try:
            if (
                button.is_displayed()
                and button.is_enabled()
                and normalize_text(button.text).lower() == "login"
            ):
                return button
        except StaleElementReferenceException:
            continue

    return False


def login_if_needed(driver):
    """로그인 화면일 때 .env의 계정 정보로 자동 로그인합니다."""
    password_inputs = driver.find_elements(*PASSWORD_LOCATOR)

    # 비밀번호 입력창이 없으면 이미 로그인된 것으로 보고 건너뜁니다.
    if not password_inputs:
        return

    # 실제 계정 정보는 코드에 쓰지 않고 .env에서 가져옵니다.
    email = os.getenv("HELPYCHAT_EMAIL")
    password = os.getenv("HELPYCHAT_PASSWORD")

    if not password:
        pytest.fail("HELPYCHAT_PASSWORD 환경변수가 설정되지 않았습니다.")

    # 기억된 계정 화면에서는 이메일 입력창이 없을 수 있습니다.
    email_inputs = driver.find_elements(*EMAIL_LOCATOR)

    if email_inputs:
        if not email:
            pytest.fail("HELPYCHAT_EMAIL 환경변수가 설정되지 않았습니다.")

        email_inputs[0].clear()
        email_inputs[0].send_keys(email)

    password_inputs[0].clear()
    password_inputs[0].send_keys(password)

    # 계정 입력 후 버튼이 활성화될 때까지 기다렸다가 클릭합니다.
    login_button = WebDriverWait(driver, 10).until(find_login_button)
    click_element(driver, login_button)


def wait_for_login_or_chat(driver):
    """페이지 이동 후 로그인 화면 또는 채팅 화면이 준비될 때까지 기다립니다."""
    WebDriverWait(driver, LOGIN_TIMEOUT).until(
        lambda current_driver: (
            current_driver.find_elements(*PASSWORD_LOCATOR)
            or find_first_visible(current_driver, CHAT_INPUT_LOCATORS)
        )
    )


@pytest.fixture
def driver():
    """테스트용 Chrome을 생성하고 테스트가 끝나면 안전하게 종료합니다."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    # 별도 프로필을 사용해 일반 Chrome 사용자 데이터와 충돌하지 않게 합니다.
    profile_directory = Path.cwd() / ".helpychat-selenium-profile"
    options.add_argument(f"--user-data-dir={profile_directory.resolve()}")

    chrome_driver = webdriver.Chrome(options=options)

    try:
        yield chrome_driver
    finally:
        # 테스트 성공 여부와 관계없이 Chrome과 드라이버 프로세스를 종료합니다.
        chrome_driver.quit()


def test_chat_message_saved_in_history(driver):
    """메시지가 히스토리에 저장되고 새로고침 후 복원되는지 검증합니다."""
    # 실행마다 겹치지 않는 고유한 테스트 메시지를 만듭니다.
    test_message = "히스토리검증_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    # 히스토리 제목이 잘릴 수 있으므로 메시지 앞부분만 검색 키로 사용합니다.
    history_key = test_message[:18]

    # 성공 및 실패 화면을 보관할 폴더를 준비합니다.
    screenshot_directory = Path("screenshots")
    screenshot_directory.mkdir(exist_ok=True)

    try:
        # 1. 테스트 페이지에 접속합니다.
        driver.get(URL)

        # 2. 로그인 화면이면 자동 로그인하고 채팅 입력창을 기다립니다.
        wait_for_login_or_chat(driver)
        login_if_needed(driver)

        chat_input = wait_for_visible(
            driver,
            CHAT_INPUT_LOCATORS,
            CHAT_READY_TIMEOUT,
        )

        # 3. 고유한 테스트 메시지를 입력하고 Enter로 전송합니다.
        enter_chat_message(chat_input, test_message)
        chat_input.send_keys(Keys.ENTER)

        # 4. Enter가 줄바꿈으로 동작하면 전송 버튼을 찾아 클릭합니다.
        try:
            wait_for_message(driver, test_message, timeout=5)
        except TimeoutException:
            send_button = wait_for_visible(
                driver,
                SEND_BUTTON_LOCATORS,
                timeout=10,
            )
            click_element(driver, send_button)

        # 5. 메시지가 대화 영역과 왼쪽 히스토리에 모두 나타나는지 확인합니다.
        wait_for_message(driver, test_message)
        wait_for_history(driver, history_key)

        # 6. 새로고침하여 데이터가 실제로 저장됐는지 확인합니다.
        driver.refresh()
        wait_for_visible(driver, CHAT_INPUT_LOCATORS)

        # 7. 새로고침 후 남아 있는 히스토리를 다시 엽니다.
        history_item = wait_for_history(driver, history_key)
        click_element(driver, history_item)

        # 8. 저장된 대화에서 원래 메시지가 복원되는지 최종 검증합니다.
        wait_for_message(driver, test_message)

        # 9. 성공 화면을 저장하고 결과를 터미널에 출력합니다.
        success_path = screenshot_directory / "history_test_pass.png"
        driver.save_screenshot(str(success_path))

        print(f"\n[PASS] 입력값: {test_message}")
        print("[PASS] 히스토리 저장 및 재진입 검증 완료")

    except Exception:
        # 실패 시점의 화면을 날짜가 포함된 파일명으로 저장합니다.
        failure_path = (
            screenshot_directory
            / f"history_test_fail_{datetime.now():%Y%m%d_%H%M%S}.png"
        )
        driver.save_screenshot(str(failure_path))
        print(f"\n[FAIL] 스크린샷 저장 위치: {failure_path}")
        raise

    finally:
        # 성공 또는 실패 결과 화면을 눈으로 확인할 수 있도록 2초 기다립니다.
        time.sleep(FINISH_DELAY)
