import os
from datetime import datetime
from pathlib import Path

import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import time

FINISH_DELAY = 5
load_dotenv()

URL = os.getenv(
    "LOGIN_URL",
    "https://dev-qaproject-helpy-chat.dev.elicer.io/"
    "?isFirstLogin=true#agents-organization",
)
TIMEOUT = 90
CHAT_READY_TIMEOUT = 180

PASSWORD = (By.CSS_SELECTOR, "input[type='password']")
EMAIL = (By.CSS_SELECTOR, "input[type='email'], input[placeholder='Email']")
CHAT_INPUTS = [
    (By.CSS_SELECTOR, "textarea[placeholder*='메시지']"),
    (By.CSS_SELECTOR, "textarea[placeholder*='질문']"),
    (By.CSS_SELECTOR, "textarea"),
    (By.CSS_SELECTOR, "[contenteditable='true'][role='textbox']"),
]


def normalized(text):
    return " ".join(text.split())


def first_visible(driver, locators):
    for locator in locators:
        try:
            for element in driver.find_elements(*locator):
                if element.is_displayed() and element.is_enabled():
                    return element
        except StaleElementReferenceException:
            pass
    return False


def wait_visible(driver, locators, timeout=TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        lambda current: first_visible(current, locators)
    )


def click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def login(driver):
    if not driver.find_elements(*PASSWORD):
        return

    email = os.getenv("HELPYCHAT_EMAIL")
    password = os.getenv("HELPYCHAT_PASSWORD")
    if not password:
        pytest.fail("HELPYCHAT_PASSWORD를 .env에 설정해 주세요.")

    # 일반 로그인 화면에는 이메일 입력칸이 있지만, 기억된 계정 화면에는
    # 비밀번호 입력칸만 표시되므로 이메일 입력은 있을 때만 수행합니다.
    visible_email_inputs = [
        element
        for element in driver.find_elements(*EMAIL)
        if element.is_displayed() and element.is_enabled()
    ]
    if visible_email_inputs:
        if not email:
            pytest.fail("HELPYCHAT_EMAIL을 .env에 설정해 주세요.")
        visible_email_inputs[0].clear()
        visible_email_inputs[0].send_keys(email)

    password_input = wait_visible(driver, [PASSWORD], timeout=30)
    password_input.clear()
    password_input.send_keys(password)

    login_button = WebDriverWait(driver, 15).until(
        lambda current: next(
            (
                button
                for button in current.find_elements(By.CSS_SELECTOR, "button")
                if button.is_displayed()
                and button.is_enabled()
                and normalized(button.text).lower() in {"login", "로그인"}
            ),
            False,
        )
    )
    click(driver, login_button)


def find_text_button(driver, labels):
    """버튼 태그가 아니어도 화면에 표시된 동작 문구를 찾습니다."""
    labels = {normalized(label).lower() for label in labels}
    candidates = []

    for element in driver.find_elements(
        By.CSS_SELECTOR,
        "button, a, [role='button'], [role='menuitem'], li, div, span, p",
    ):
        try:
            if not element.is_displayed():
                continue

            values = {
                normalized(element.text or "").lower(),
                normalized(element.get_attribute("aria-label") or "").lower(),
                normalized(element.get_attribute("title") or "").lower(),
            }
            if not labels.intersection(values):
                continue

            rect = element.rect
            area = rect.get("width", 0) * rect.get("height", 0)
            if area > 0:
                candidates.append((area, element))
        except StaleElementReferenceException:
            pass

    # 같은 문구를 가진 부모와 자식이 함께 검색되면 가장 작은 요소를 클릭합니다.
    return min(candidates, key=lambda item: item[0])[1] if candidates else False


def logout(driver):
    # '모바일 앱 다운로드' 버튼의 실제 높이를 기준으로 바로 오른쪽에 있는
    # 원형 프로필을 찾습니다. 상단 안내 배너 높이가 달라져도 영향을 받지 않습니다.
    profile = driver.execute_script(
        r"""
        const visible = element => {
            const rect = element.getBoundingClientRect();
            const style = getComputedStyle(element);
            return rect.width > 0 && rect.height > 0
                && style.visibility !== 'hidden'
                && style.display !== 'none';
        };
        const normalize = text => (text || '').replace(/\s+/g, ' ').trim();

        const labels = Array.from(document.querySelectorAll('body *'))
            .filter(element => visible(element)
                && normalize(element.innerText) === '모바일 앱 다운로드')
            .sort((a, b) => {
                const ar = a.getBoundingClientRect();
                const br = b.getBoundingClientRect();
                return ar.width * ar.height - br.width * br.height;
            });

        if (!labels.length) return null;

        const downloadRect = labels[0].getBoundingClientRect();
        const y = downloadRect.top + downloadRect.height / 2;
        const xPoints = [
            window.innerWidth - 20,
            window.innerWidth - 28,
            window.innerWidth - 36,
            window.innerWidth - 44
        ];

        for (const x of xPoints) {
            const element = document.elementFromPoint(x, y);
            if (!element) continue;

            const clickable = element.closest(
                "button, a, [role='button'], [aria-haspopup='menu']"
            );
            const target = clickable || element;
            const targetRect = target.getBoundingClientRect();

            if (targetRect.left > downloadRect.right) return target;
        }
        return null;
        """
    )

    if not profile:
        pytest.fail("우측 상단 프로필 버튼을 찾지 못했습니다.")
    driver.execute_script("arguments[0].click();", profile)

    logout_button = WebDriverWait(driver, 15).until(
        lambda current: find_text_button(current, {"로그아웃", "logout", "log out"})
    )
    driver.execute_script("arguments[0].click();", logout_button)

    # 서비스에 로그아웃 확인 창이 있으면 확인합니다.
    try:
        confirm = WebDriverWait(driver, 3).until(
            lambda current: find_text_button(
                current, {"로그아웃", "확인", "logout", "log out", "confirm"}
            )
        )
        click(driver, confirm)
    except Exception:
        pass

    WebDriverWait(driver, 30).until(
        lambda current: bool(current.find_elements(*PASSWORD))
    )


def history_item(driver, key):
    width = driver.execute_script("return window.innerWidth")
    candidates = []
    for element in driver.find_elements(
        By.CSS_SELECTOR, "a, button, [role='button'], li"
    ):
        try:
            rect = element.rect
            text = normalized(element.text)
            if (
                element.is_displayed()
                and key in text
                and rect.get("x", 0) < width * 0.45
                and rect.get("width", 0) > 0
                and rect.get("height", 0) > 0
            ):
                candidates.append((rect["width"] * rect["height"], element))
        except StaleElementReferenceException:
            pass
    return min(candidates, key=lambda item: item[0])[1] if candidates else False


def message_visible(driver, message):
    width = driver.execute_script("return window.innerWidth")
    for element in driver.find_elements(By.CSS_SELECTOR, "p, span, div, article"):
        try:
            text = normalized(element.text)
            if (
                element.is_displayed()
                and element.rect.get("x", 0) >= width * 0.22
                and message in text
                and len(text) <= len(message) + 100
            ):
                return True
        except StaleElementReferenceException:
            pass
    return False


def find_action(driver, labels, root=None):
    """표시 중인 버튼 또는 메뉴에서 지정한 동작을 찾습니다."""
    labels = {normalized(label).lower() for label in labels}
    search_root = root or driver
    for element in search_root.find_elements(
        By.CSS_SELECTOR, "button, [role='button'], [role='menuitem']"
    ):
        try:
            values = {
                normalized(element.text or "").lower(),
                normalized(element.get_attribute("aria-label") or "").lower(),
                normalized(element.get_attribute("title") or "").lower(),
            }
            if element.is_displayed() and element.is_enabled() and labels & values:
                return element
        except StaleElementReferenceException:
            pass
    return False


def open_history_menu(driver, history_key):
    """대상 히스토리에 마우스를 올리고 더보기 메뉴를 엽니다."""
    item = WebDriverWait(driver, TIMEOUT).until(
        lambda current: history_item(current, history_key)
    )
    ActionChains(driver).move_to_element(item).perform()

    menu_button = find_action(
        driver, {"더보기", "메뉴", "옵션", "more", "more options"}
    )
    if not menu_button:
        menu_button = driver.execute_script(
            """
            let row = arguments[0];
            for (let depth = 0; depth < 5 && row; depth++, row = row.parentElement) {
                const buttons = Array.from(row.querySelectorAll('button')).filter(button => {
                    const rect = button.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                });
                if (buttons.length > 0) return buttons[buttons.length - 1];
            }
            return null;
            """,
            item,
        )
    if not menu_button:
        pytest.fail(f"'{history_key}' 히스토리의 더보기 버튼을 찾지 못했습니다.")
    click(driver, menu_button)


def delete_history(driver, history_key):
    """대상 히스토리를 삭제하고 목록에서 사라질 때까지 기다립니다."""
    open_history_menu(driver, history_key)
    delete_button = WebDriverWait(driver, 15).until(
        lambda current: find_action(current, {"삭제", "delete"})
    )
    click(driver, delete_button)

    try:
        dialog = WebDriverWait(driver, 3).until(
            lambda current: first_visible(
                current,
                [(By.CSS_SELECTOR, "[role='dialog']"), (By.CSS_SELECTOR, "dialog")],
            )
        )
        confirm = find_action(dialog, {"삭제", "확인", "delete", "confirm"})
        if confirm:
            click(driver, confirm)
    except Exception:
        pass

    WebDriverWait(driver, TIMEOUT).until(
        lambda current: not history_item(current, history_key)
    )


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    profile = Path.cwd() / ".helpychat-selenium-profile"
    options.add_argument(f"--user-data-dir={profile.resolve()}")
    browser = webdriver.Chrome(options=options)
    try:
        yield browser
    finally:
        time.sleep(FINISH_DELAY)
    browser.quit()


def test_history_survives_relogin(driver):
    message = "히스토리재로그인검증_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    history_key = message[:18]

    driver.get(URL)
    WebDriverWait(driver, 30).until(
        lambda current: (
            current.find_elements(*PASSWORD) or first_visible(current, CHAT_INPUTS)
        )
    )
    login(driver)

    chat_input = wait_visible(driver, CHAT_INPUTS, CHAT_READY_TIMEOUT)
    chat_input.click()
    if chat_input.get_attribute("contenteditable") == "true":
        chat_input.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
    else:
        chat_input.clear()
    chat_input.send_keys(message)
    chat_input.send_keys(Keys.ENTER)

    WebDriverWait(driver, TIMEOUT).until(
        lambda current: message_visible(current, message)
    )

    WebDriverWait(driver, TIMEOUT).until(
        lambda current: history_item(current, history_key)
    )

    logout(driver)
    login(driver)
    wait_visible(driver, CHAT_INPUTS, CHAT_READY_TIMEOUT)

    saved_history = WebDriverWait(driver, TIMEOUT).until(
        lambda current: history_item(current, history_key)
    )
    click(driver, saved_history)

    WebDriverWait(driver, TIMEOUT).until(
        lambda current: message_visible(current, message)
    )


def test_history_can_be_deleted(driver):
    """이번 테스트가 생성한 히스토리를 삭제하고 영구 삭제를 검증합니다."""
    message = "히스토리삭제검증_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    history_key = message[:18]

    driver.get(URL)
    WebDriverWait(driver, 30).until(
        lambda current: (
            current.find_elements(*PASSWORD) or first_visible(current, CHAT_INPUTS)
        )
    )
    login(driver)

    chat_input = wait_visible(driver, CHAT_INPUTS, CHAT_READY_TIMEOUT)
    chat_input.click()
    if chat_input.get_attribute("contenteditable") == "true":
        chat_input.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE)
    else:
        chat_input.clear()
    chat_input.send_keys(message)
    chat_input.send_keys(Keys.ENTER)

    WebDriverWait(driver, TIMEOUT).until(
        lambda current: message_visible(current, message)
    )
    WebDriverWait(driver, TIMEOUT).until(
        lambda current: history_item(current, history_key)
    )

    delete_history(driver, history_key)
    assert not history_item(driver, history_key)

    driver.refresh()
    wait_visible(driver, CHAT_INPUTS, CHAT_READY_TIMEOUT)
    WebDriverWait(driver, 15).until(
        lambda current: not history_item(current, history_key)
    )
    assert not history_item(driver, history_key)
