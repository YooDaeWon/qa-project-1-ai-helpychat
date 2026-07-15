from datetime import datetime
import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


DEFAULT_LOGIN_URL = "https://dev-qaproject-helpy-chat.dev.elicer.io/"

BASE_URL = DEFAULT_LOGIN_URL.rstrip("/")
NEW_CHAT_URL = f"{BASE_URL}/#agents-organization"
BUILDER_URL = f"{BASE_URL}/agents/builder"


def load_env():
    """
    .env 파일 위치:
    C:/QA/Workspace/PythonEx/.env

    .env 형식:
    LOGIN_URL=https://dev-qaproject-helpy-chat.dev.elicer.io/
    LOGIN_EMAIL=your_email
    LOGIN_PASSWORD=your_password
    """
    env_candidates = [
        Path(__file__).resolve().parents[2] / ".env",
        Path.cwd() / ".env",
    ]

    env_path = None

    for path in env_candidates:
        if path.exists():
            env_path = path
            break

    if env_path is None:
        raise Exception(
            ".env 파일을 찾을 수 없습니다. "
            "C:\\QA\\Workspace\\PythonEx\\.env 위치에 LOGIN_URL, LOGIN_EMAIL, LOGIN_PASSWORD를 저장하세요."
        )

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

    required_keys = ["LOGIN_URL", "LOGIN_EMAIL", "LOGIN_PASSWORD"]
    missing_keys = []

    for key in required_keys:
        if not os.environ.get(key):
            missing_keys.append(key)

    if missing_keys:
        raise Exception(f".env 파일에 필요한 값이 없습니다: {', '.join(missing_keys)}")

    print(f".env 읽기 완료: {env_path}")


def configure_urls():
    """
    .env의 LOGIN_URL 기준으로 테스트 URL 설정
    """
    global BASE_URL, NEW_CHAT_URL, BUILDER_URL

    login_url = os.environ.get("LOGIN_URL", DEFAULT_LOGIN_URL).strip()

    if not login_url:
        login_url = DEFAULT_LOGIN_URL

    BASE_URL = login_url.rstrip("/")
    NEW_CHAT_URL = f"{BASE_URL}/#agents-organization"
    BUILDER_URL = f"{BASE_URL}/agents/builder"

    print(f"테스트 기준 URL 설정 완료: {BASE_URL}")


def ask_create_count():
    """
    터미널에서 생성할 에이전트 개수 입력받기
    """
    while True:
        user_input = input("생성할 에이전트 개수를 입력하세요: ").strip()

        if not user_input.isdigit():
            print("숫자만 입력하세요. 예: 1, 2, 3")
            continue

        count = int(user_input)

        if count <= 0:
            print("1개 이상 입력하세요.")
            continue

        return count


def make_test_agent_data(test_count):
    """
    테스트 에이전트 이름과 한줄 소개 생성
    실행할 때마다 001회차부터 다시 시작한다.
    """
    now = datetime.now()
    now_for_name = now.strftime("%Y%m%d_%H%M%S")
    now_for_text = now.strftime("%Y-%m-%d %H:%M:%S")

    agent_name = f"자동화테스트에이전트_{now_for_name}_{test_count:03d}회차"

    short_description = (
        f"{now_for_text} 기준 Selenium 자동화 테스트 "
        f"{test_count:03d}회차로 생성한 에이전트입니다."
    )

    rule_text = (
        "이 에이전트는 Selenium 자동화 테스트 검증용으로 생성되었습니다. "
        "사용자의 질문에 친절하고 간단하게 답변합니다."
    )

    start_conversation = (
        f"안녕하세요. 저는 자동화 테스트 {test_count:03d}회차로 생성된 에이전트입니다."
    )

    return agent_name, short_description, rule_text, start_conversation, test_count


def safe_click(driver, element):
    """
    화면 중앙으로 이동 후 JS 클릭
    """
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.2)
    driver.execute_script("arguments[0].click();", element)


def get_body_text(driver):
    """
    현재 화면의 body 텍스트를 안전하게 가져오기
    """
    try:
        return driver.execute_script(
            """
            return document.body ? document.body.innerText : '';
            """
        )
    except StaleElementReferenceException:
        return ""
    except Exception:
        return ""


def is_login_page(driver):
    """
    Password 입력창이 보이면 로그인 페이지로 판단.
    JS로 확인해서 stale element 오류를 줄인다.
    """
    try:
        return driver.execute_script(
            """
            const passwordInputs = Array.from(document.querySelectorAll("input[type='password']"));

            return passwordInputs.some((input) => {
                const rect = input.getBoundingClientRect();
                const style = window.getComputedStyle(input);

                return (
                    rect.width > 0 &&
                    rect.height > 0 &&
                    style.visibility !== 'hidden' &&
                    style.display !== 'none'
                );
            });
            """
        )
    except StaleElementReferenceException:
        return False
    except Exception:
        return False


def is_logged_in(driver):
    """
    로그인 후 보이는 사이드바 메뉴 기준으로 로그인 여부 판단.
    로그인 직후 화면 전환 중 stale 오류가 나면 False로 처리하고 다시 대기한다.
    """
    try:
        if is_login_page(driver):
            return False

        page_text = get_body_text(driver)

        return (
            "새 대화" in page_text
            and "검색" in page_text
            and "에이전트 마켓플레이스" in page_text
        )

    except StaleElementReferenceException:
        time.sleep(0.3)
        return False
    except Exception:
        return False


def login(driver, wait):
    login_email = os.environ.get("LOGIN_EMAIL")
    login_password = os.environ.get("LOGIN_PASSWORD")

    print("로그인 상태 확인 중...")

    if is_logged_in(driver):
        print("이미 로그인된 상태입니다.")
        return

    print("로그인 페이지 감지됨. 자동 로그인 진행")

    email_input = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//input[@placeholder='Email']"
                " | //input[contains(@placeholder, 'Email')]"
                " | //input[@type='email']",
            )
        )
    )
    email_input.clear()
    email_input.send_keys(login_email)
    print("Email 입력 완료")

    password_input = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//input[@placeholder='Password']"
                " | //input[contains(@placeholder, 'Password')]"
                " | //input[@type='password']",
            )
        )
    )
    password_input.clear()
    password_input.send_keys(login_password)
    print("Password 입력 완료")

    login_success_click = False

    for attempt in range(1, 4):
        try:
            login_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[normalize-space()='Login']"
                        " | //button[contains(normalize-space(), 'Login')]",
                    )
                )
            )
            safe_click(driver, login_button)
            print("Login 버튼 클릭 완료")
            login_success_click = True
            break

        except StaleElementReferenceException:
            print(f"Login 버튼 stale 발생, 재시도 {attempt}/3")
            time.sleep(0.5)

        except Exception:
            try:
                password_input.send_keys(Keys.ENTER)
                print("Login 버튼 클릭 실패, Enter로 로그인 시도")
                login_success_click = True
                break
            except StaleElementReferenceException:
                print(f"Password 입력창 stale 발생, 재시도 {attempt}/3")
                time.sleep(0.5)

    if not login_success_click:
        raise Exception("로그인 버튼 클릭 또는 Enter 로그인 시도 실패")

    wait.until(lambda d: is_logged_in(d))
    time.sleep(1)
    print("로그인 완료")


def wait_for_new_chat_page(driver, wait):
    """
    새 대화 기본 화면 로딩 대기
    """
    wait.until(
        lambda d: (
            "AI Helpy Chat" in get_body_text(d)
            and "Helpy Pro Agent" in get_body_text(d)
        )
    )

    wait.until(
        lambda d: (
            "기관 에이전트" in get_body_text(d)
            or "내 에이전트" in get_body_text(d)
            or "필요한 모든 순간" in get_body_text(d)
        )
    )

    print("새 대화 기본 화면 확인 완료")


def go_to_private_agents(driver, wait):
    """
    내 에이전트 화면으로 이동

    실제 구조:
    새 대화 화면
    → #agents-organization
    → 내 에이전트 탭 클릭
    """
    print("새 대화 화면으로 이동 시도")

    driver.get(NEW_CHAT_URL)
    wait_for_new_chat_page(driver, wait)

    private_tab = None
    end_time = time.time() + 15

    while time.time() < end_time:
        private_tab_candidates = [
            (By.CSS_SELECTOR, "button[role='tab'][id$='agents-private']"),
            (By.CSS_SELECTOR, "button[role='tab'][aria-controls$='agents-private']"),
            (By.XPATH, "//button[@role='tab' and contains(normalize-space(), '내 에이전트')]"),
            (By.XPATH, "//*[@role='tab' and contains(normalize-space(), '내 에이전트')]"),
            (By.XPATH, "//button[contains(normalize-space(), '내 에이전트')]"),
        ]

        for by, selector in private_tab_candidates:
            try:
                elements = driver.find_elements(by, selector)

                for element in elements:
                    try:
                        if element.is_displayed():
                            private_tab = element
                            break
                    except StaleElementReferenceException:
                        private_tab = None
                        continue

                if private_tab is not None:
                    break

            except StaleElementReferenceException:
                private_tab = None
                time.sleep(0.3)

        if private_tab is not None:
            break

        time.sleep(0.3)

    if private_tab is None:
        raise Exception("내 에이전트 탭을 찾지 못했습니다.")

    safe_click(driver, private_tab)
    print("내 에이전트 탭 클릭 완료")

    wait.until(lambda d: "에이전트 만들기" in get_body_text(d))

    print("내 에이전트 화면 확인 완료")


def click_create_agent_link(driver, wait):
    """
    개발자도구에서 확인한 구조:
    <a href="/agents/builder"> 에이전트 만들기 </a>
    """
    print("에이전트 만들기 링크 찾는 중...")

    create_link = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "a[href='/agents/builder']")
        )
    )

    safe_click(driver, create_link)
    print("에이전트 만들기 링크 클릭 완료")

    try:
        wait.until(
            lambda d: (
                "builder" in d.current_url
                or "새 에이전트 만들기" in get_body_text(d)
                or "대화로 만들기" in get_body_text(d)
                or "설정" in get_body_text(d)
            )
        )
        print("에이전트 만들기 화면 진입 확인 완료")
    except Exception:
        print("클릭 후 이동 확인 실패. builder URL로 직접 이동합니다.")
        driver.get(BUILDER_URL)

        wait.until(
            lambda d: (
                "builder" in d.current_url
                or "새 에이전트 만들기" in get_body_text(d)
                or "대화로 만들기" in get_body_text(d)
                or "설정" in get_body_text(d)
            )
        )
        print("builder URL 직접 이동 완료")


def click_builder_tab(driver, wait, value, text):
    """
    에이전트 만들기 화면 상단 탭 클릭

    실제 DOM 기준:
    value='chat' → 대화로 만들기
    value='form' → 설정
    """
    element = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                f"//button[@value='{value}']"
                f" | //button[contains(normalize-space(), '{text}')]",
            )
        )
    )

    safe_click(driver, element)
    time.sleep(0.7)
    print(f"{text} 탭 클릭 완료")


def find_by_placeholder(wait, placeholder_text):
    return wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                f"//input[contains(@placeholder, '{placeholder_text}')]"
                f" | //textarea[contains(@placeholder, '{placeholder_text}')]",
            )
        )
    )


def find_by_name(wait, name_value):
    return wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                f"input[name='{name_value}'], textarea[name='{name_value}']",
            )
        )
    )


def find_by_name_prefix(wait, name_prefix):
    return wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                f"input[name^='{name_prefix}'], textarea[name^='{name_prefix}']",
            )
        )
    )


def set_react_value(driver, element, value):
    """
    React/MUI 입력창에 값을 반영
    """
    driver.execute_script(
        """
        const element = arguments[0];
        const value = arguments[1];

        element.scrollIntoView({ block: 'center' });
        element.focus();

        const tagName = element.tagName.toLowerCase();

        let prototype;
        if (tagName === 'textarea') {
            prototype = window.HTMLTextAreaElement.prototype;
        } else {
            prototype = window.HTMLInputElement.prototype;
        }

        const valueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
        valueSetter.call(element, value);

        element.dispatchEvent(new InputEvent('input', {
            bubbles: true,
            inputType: 'insertText',
            data: value
        }));

        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.dispatchEvent(new Event('blur', { bubbles: true }));
        element.dispatchEvent(new FocusEvent('focusout', { bubbles: true }));
        """,
        element,
        value,
    )

    time.sleep(0.4)

    current_value = element.get_attribute("value")

    if current_value != value:
        raise Exception(f"입력값 반영 실패. 현재값: {current_value}")

    return element


def print_check_result(check_name, result):
    """
    검증 결과 출력
    """
    if result:
        print(f"[PASS] {check_name}")
    else:
        print(f"[FAIL] {check_name}")


def verify_builder_tabs_displayed(driver):
    """
    - 대화로 만들기 탭 표시 확인
    - 설정 탭 표시 확인

    실제 DOM 기준:
    <button value="chat">대화로 만들기</button>
    <button value="form">설정</button>
    """
    end_time = time.time() + 10
    result = {
        "chatVisible": False,
        "formVisible": False,
    }

    while time.time() < end_time:
        result = driver.execute_script(
            """
            const chatButton =
                document.querySelector("button[value='chat']") ||
                Array.from(document.querySelectorAll('button'))
                    .find((button) => {
                        const text = (button.innerText || button.textContent || '').trim();
                        return text.includes('대화로 만들기') || text.includes('대화');
                    });

            const formButton =
                document.querySelector("button[value='form']") ||
                Array.from(document.querySelectorAll('button'))
                    .find((button) => {
                        const text = (button.innerText || button.textContent || '').trim();
                        return text.includes('설정');
                    });

            return {
                chatVisible: Boolean(chatButton),
                formVisible: Boolean(formButton)
            };
            """
        )

        if result["chatVisible"] and result["formVisible"]:
            break

        time.sleep(0.3)

    conversation_tab_visible = result["chatVisible"]
    setting_tab_visible = result["formVisible"]

    print_check_result("대화로 만들기 탭 표시 확인", conversation_tab_visible)
    print_check_result("설정 탭 표시 확인", setting_tab_visible)

    if not conversation_tab_visible:
        raise Exception("대화로 만들기 탭이 표시되지 않습니다.")

    if not setting_tab_visible:
        raise Exception("설정 탭이 표시되지 않습니다.")


def verify_preview_area_displayed(driver):
    """
    미리보기 영역 표시 확인
    """
    result = driver.execute_script(
        """
        const bodyText = document.body ? document.body.innerText : '';

        if (bodyText.includes('미리보기')) {
            return true;
        }

        if (bodyText.includes('메시지를 입력해 주세요')) {
            return true;
        }

        const inputs = Array.from(document.querySelectorAll('input, textarea'));

        return inputs.some((el) => {
            const placeholder = el.getAttribute('placeholder') || '';
            return (
                placeholder.includes('메시지') ||
                placeholder.includes('대화') ||
                placeholder.includes('입력')
            );
        });
        """
    )

    print_check_result("미리보기 영역 표시 확인", result)

    if not result:
        raise Exception("미리보기 영역을 확인하지 못했습니다.")


def verify_file_upload_button_displayed(driver):
    """
    파일 업로드 버튼 표시 확인

    실제 업로드는 하지 않고 버튼/파일 input 노출만 확인한다.
    """
    result = driver.execute_script(
        """
        const bodyText = document.body ? document.body.innerText : '';

        const fileInputExists = Boolean(document.querySelector("input[type='file']"));

        const textExists =
            bodyText.includes('파일 업로드') ||
            bodyText.includes('업로드') ||
            bodyText.includes('파일');

        return fileInputExists || textExists;
        """
    )

    print_check_result("파일 업로드 버튼 표시 확인", result)

    if not result:
        raise Exception("파일 업로드 버튼 또는 파일 input을 확인하지 못했습니다.")


def verify_feature_checkbox_displayed(driver):
    """
    기능 체크박스 표시 확인

    체크박스 input 또는 기능 관련 텍스트가 보이는지 확인한다.
    """
    result = driver.execute_script(
        """
        const bodyText = document.body ? document.body.innerText : '';

        const checkboxCount = document.querySelectorAll("input[type='checkbox']").length;

        const featureTextExists =
            bodyText.includes('웹 검색') ||
            bodyText.includes('웹 브라우저') ||
            bodyText.includes('이미지 생성') ||
            bodyText.includes('코드 실행') ||
            bodyText.includes('데이터 분석') ||
            bodyText.includes('기능');

        return checkboxCount > 0 || featureTextExists;
        """
    )

    print_check_result("기능 체크박스 표시 확인", result)

    if not result:
        raise Exception("기능 체크박스 또는 기능 항목을 확인하지 못했습니다.")


def try_select_feature_checkbox(driver):
    """
    기능 체크박스 선택 확인

    가능한 경우 첫 번째 기능 체크박스를 선택한다.
    구조가 MUI 버튼형일 수도 있어서 여러 방식으로 시도한다.
    """
    result = driver.execute_script(
        """
        function isVisible(el) {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);

            return (
                rect.width > 0 &&
                rect.height > 0 &&
                style.display !== 'none' &&
                style.visibility !== 'hidden'
            );
        }

        const checkboxes = Array.from(document.querySelectorAll("input[type='checkbox']"))
            .filter((el) => isVisible(el) || el.closest('label'));

        if (checkboxes.length > 0) {
            const target = checkboxes[0];

            if (!target.checked) {
                target.click();
            }

            return target.checked;
        }

        const keywords = ['웹 검색', '웹 브라우저', '이미지 생성', '코드 실행', '데이터 분석'];

        const candidates = Array.from(document.querySelectorAll('button, label, div, span'))
            .filter((el) => {
                const text = (el.innerText || el.textContent || '').trim();
                return keywords.some((keyword) => text.includes(keyword));
            });

        for (const candidate of candidates) {
            try {
                candidate.scrollIntoView({ block: 'center' });
                candidate.click();
                return true;
            } catch (e) {}
        }

        return false;
        """
    )

    print_check_result("기능 체크박스 선택 확인", result)

    if not result:
        raise Exception("기능 체크박스 선택에 실패했습니다.")


def verify_public_scope_options_displayed(driver):
    """
    공개 범위 옵션 표시 확인
    """
    result = driver.execute_script(
        """
        const bodyText = document.body ? document.body.innerText : '';

        const privateRadio = document.querySelector("input[type='radio'][value='private']");
        const radioCount = document.querySelectorAll("input[type='radio']").length;

        const textExists =
            bodyText.includes('나만 보기') ||
            bodyText.includes('기관 공개') ||
            bodyText.includes('공개 범위') ||
            bodyText.includes('공개범위');

        return Boolean(privateRadio) || radioCount > 0 || textExists;
        """
    )

    print_check_result("공개 범위 옵션 표시 확인", result)

    if not result:
        raise Exception("공개 범위 옵션을 확인하지 못했습니다.")


def is_create_button_disabled(driver):
    """
    만들기 버튼 비활성 여부 확인
    """
    return driver.execute_script(
        """
        const buttons = Array.from(document.querySelectorAll('button'));

        const target = buttons.find((button) => {
            const text = (button.innerText || button.textContent || '').trim();
            return text.includes('만들기');
        });

        if (!target) {
            return null;
        }

        const className = String(target.className || '');

        const disabled =
            target.disabled ||
            target.getAttribute('aria-disabled') === 'true' ||
            className.includes('Mui-disabled');

        return disabled;
        """
    )


def verify_create_button_disabled_before_required_input(driver):
    """
    필수값 입력 전 만들기 버튼 비활성 상태 확인
    """
    disabled = is_create_button_disabled(driver)

    result = disabled is True

    print_check_result("필수값 입력 전 만들기 버튼 비활성 상태 확인", result)

    if not result:
        raise Exception("필수값 입력 전 만들기 버튼이 비활성 상태가 아닙니다.")


def try_select_category_option(driver):
    """
    카테고리 선택 시도

    현재 카테고리 DOM 구조가 정확히 확인되지 않아 가능한 경우만 시도한다.
    실패해도 전체 생성 테스트는 중단하지 않는다.
    """
    result = driver.execute_script(
        """
        function isVisible(el) {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);

            return (
                rect.width > 0 &&
                rect.height > 0 &&
                style.display !== 'none' &&
                style.visibility !== 'hidden'
            );
        }

        const openKeywords = ['카테고리', '카테고리 선택', '선택'];

        const opener = Array.from(document.querySelectorAll('button, div, input'))
            .find((el) => {
                const text = (el.innerText || el.textContent || el.getAttribute('placeholder') || '').trim();
                return isVisible(el) && openKeywords.some((keyword) => text.includes(keyword));
            });

        if (!opener) {
            return 'not-found';
        }

        opener.scrollIntoView({ block: 'center' });
        opener.click();

        return 'clicked';
        """
    )

    if result == "clicked":
        time.sleep(0.5)

        selected = driver.execute_script(
            """
            function isVisible(el) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);

                return (
                    rect.width > 0 &&
                    rect.height > 0 &&
                    style.display !== 'none' &&
                    style.visibility !== 'hidden'
                );
            }

            const optionKeywords = ['기타', '일반', '업무', '학습'];

            const option = Array.from(document.querySelectorAll('li, button, div, span'))
                .find((el) => {
                    const text = (el.innerText || el.textContent || '').trim();
                    return isVisible(el) && optionKeywords.some((keyword) => text === keyword || text.includes(keyword));
                });

            if (!option) {
                return false;
            }

            option.scrollIntoView({ block: 'center' });
            option.click();

            return true;
            """
        )

        print_check_result("카테고리 선택 시도", selected)
        return selected

    print("[SKIP] 카테고리 선택 시도 - 정확한 카테고리 DOM 구조 확인 필요")
    return False


def run_builder_checks_before_input(driver):
    """
    설정 입력 전에 확인 가능한 항목을 순서대로 검증한다.
    """
    verify_preview_area_displayed(driver)
    verify_file_upload_button_displayed(driver)
    verify_feature_checkbox_displayed(driver)
    verify_public_scope_options_displayed(driver)
    verify_create_button_disabled_before_required_input(driver)

    try:
        try_select_category_option(driver)
    except Exception as e:
        print(f"[SKIP] 카테고리 선택 시도 중 예외 발생: {e}")

    try_select_feature_checkbox(driver)


def input_name(driver, wait, agent_name):
    element = find_by_placeholder(wait, "이름")
    set_react_value(driver, element, agent_name)
    print("이름 입력 완료:", agent_name)


def input_short_description(driver, wait, short_description):
    element = find_by_placeholder(wait, "짧은 설명")
    set_react_value(driver, element, short_description)
    print("한줄 소개 입력 완료:", short_description)


def input_rule(driver, wait, rule_text):
    element = find_by_name(wait, "systemPrompt")
    set_react_value(driver, element, rule_text)
    print("규칙 입력 완료")


def input_start_conversation(driver, wait, start_conversation):
    element = find_by_name_prefix(wait, "conversationStarters")
    set_react_value(driver, element, start_conversation)
    print("시작 대화 입력 완료")


def check_private_scope(driver):
    checked = driver.execute_script(
        """
        const privateRadio = document.querySelector("input[type='radio'][value='private']");

        if (!privateRadio) {
            return 'not-found';
        }

        if (privateRadio.checked) {
            return 'checked';
        }

        privateRadio.click();

        return privateRadio.checked ? 'checked-after-click' : 'not-checked';
        """
    )

    if checked in ["checked", "checked-after-click"]:
        print("공개 범위 나만 보기 확인 완료")
    else:
        print(f"공개 범위 나만 보기 확인 실패 또는 미존재: {checked}")


def get_create_button_info(driver):
    return driver.execute_script(
        """
        const buttons = Array.from(document.querySelectorAll('button'));

        const candidates = buttons
            .filter((button) => {
                const text = (button.innerText || button.textContent || '').trim();
                return text.includes('만들기');
            })
            .map((button) => {
                const className = String(button.className || '');
                const disabled =
                    button.disabled ||
                    button.getAttribute('aria-disabled') === 'true' ||
                    className.includes('Mui-disabled');

                return {
                    text: (button.innerText || button.textContent || '').trim(),
                    disabled: disabled,
                    realDisabled: button.disabled,
                    ariaDisabled: button.getAttribute('aria-disabled'),
                    className: className,
                    id: button.id || ''
                };
            });

        return candidates;
        """
    )


def is_saved(driver):
    return driver.execute_script(
        """
        const text = document.body ? document.body.innerText : '';
        return text.includes('저장됨');
        """
    )


def is_create_button_enabled(driver):
    return driver.execute_script(
        """
        const buttons = Array.from(document.querySelectorAll('button'));

        const target = buttons.find((button) => {
            const text = (button.innerText || button.textContent || '').trim();
            const className = String(button.className || '');

            const disabled =
                button.disabled ||
                button.getAttribute('aria-disabled') === 'true' ||
                className.includes('Mui-disabled');

            return text.includes('만들기') && !disabled;
        });

        return Boolean(target);
        """
    )


def wait_until_ready_to_create(driver):
    """
    저장됨 + 만들기 버튼 활성화 상태 확인
    """
    print("저장됨 및 만들기 버튼 활성화 확인 중...")

    end_time = time.time() + 20
    last_button_info = None

    while time.time() < end_time:
        saved = is_saved(driver)
        button_enabled = is_create_button_enabled(driver)

        if saved and button_enabled:
            print("저장됨 상태 확인 완료")
            print("만들기 버튼 활성화 확인 완료")
            return

        last_button_info = get_create_button_info(driver)
        time.sleep(0.3)

    print("만들기 버튼 최종 상태:")
    print(last_button_info)

    raise Exception("저장됨 또는 만들기 버튼 활성화 상태를 확인하지 못했습니다.")


def click_create_button(driver):
    print("만들기 버튼 클릭 시도 중...")

    clicked = driver.execute_script(
        """
        const buttons = Array.from(document.querySelectorAll('button'));

        const target = buttons.find((button) => {
            const text = (button.innerText || button.textContent || '').trim();
            const className = String(button.className || '');

            const disabled =
                button.disabled ||
                button.getAttribute('aria-disabled') === 'true' ||
                className.includes('Mui-disabled');

            return text.includes('만들기') && !disabled;
        });

        if (!target) {
            return false;
        }

        target.scrollIntoView({ block: 'center' });
        target.click();

        return true;
        """
    )

    if not clicked:
        print("만들기 버튼 상태:")
        print(get_create_button_info(driver))
        raise Exception("활성화된 만들기 버튼을 클릭하지 못했습니다.")

    print("만들기 버튼 클릭 완료")


def create_one_agent(driver, wait, current_index, total_count):
    (
        agent_name,
        short_description,
        rule_text,
        start_conversation,
        test_count,
    ) = make_test_agent_data(current_index)

    print("")
    print("=" * 60)
    print(f"{current_index}/{total_count}번째 에이전트 생성 시작")
    print(f"이번 실행 기준 자동화 테스트 회차: {test_count:03d}회차")
    print(f"생성할 에이전트 이름: {agent_name}")
    print("=" * 60)

    go_to_private_agents(driver, wait)

    click_create_agent_link(driver, wait)

    verify_builder_tabs_displayed(driver)

    click_builder_tab(driver, wait, "form", "설정")

    run_builder_checks_before_input(driver)

    input_name(driver, wait, agent_name)
    input_short_description(driver, wait, short_description)
    input_rule(driver, wait, rule_text)
    input_start_conversation(driver, wait, start_conversation)

    check_private_scope(driver)

    wait_until_ready_to_create(driver)

    click_create_button(driver)

    wait.until(lambda d: agent_name in get_body_text(d))

    print(f"{current_index}/{total_count}번째 에이전트 생성 직후 검증 성공:", agent_name)

    return agent_name


def reset_all_scroll_positions(driver):
    """
    내 에이전트 목록 검증 전에 모든 스크롤 위치를 맨 위로 초기화한다.
    window 스크롤뿐만 아니라 내부 스크롤 div까지 초기화한다.
    """
    driver.execute_script(
        """
        window.scrollTo(0, 0);

        const elements = Array.from(document.querySelectorAll('*'));

        elements.forEach((el) => {
            try {
                if (el.scrollHeight > el.clientHeight) {
                    el.scrollTop = 0;
                }
            } catch (e) {}
        });
        """
    )

    time.sleep(1)


def collect_found_agent_names_from_current_screen(driver, created_agents):
    """
    현재 DOM에 올라와 있는 텍스트에서 생성한 에이전트명을 찾는다.
    """
    page_text = get_body_text(driver)
    found = set()

    for agent_name in created_agents:
        if agent_name in page_text:
            found.add(agent_name)

    return found


def scroll_down_all_possible_containers(driver):
    """
    화면 전체 스크롤뿐만 아니라 내부 스크롤 가능한 영역까지 전부 아래로 이동한다.
    내 에이전트 목록이 내부 div 스크롤인 경우를 대비한다.
    """
    return driver.execute_script(
        """
        function isVisible(el) {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);

            return (
                rect.width > 0 &&
                rect.height > 0 &&
                rect.bottom > 0 &&
                rect.top < window.innerHeight &&
                style.display !== 'none' &&
                style.visibility !== 'hidden'
            );
        }

        const elements = Array.from(document.querySelectorAll('*'));

        const scrollables = elements.filter((el) => {
            try {
                const style = window.getComputedStyle(el);
                const overflowY = style.overflowY;

                const hasScrollableOverflow = el.scrollHeight > el.clientHeight + 50;
                const overflowAllowsScroll =
                    overflowY === 'auto' ||
                    overflowY === 'scroll' ||
                    overflowY === 'overlay' ||
                    overflowY === 'visible';

                return (
                    isVisible(el) &&
                    hasScrollableOverflow &&
                    overflowAllowsScroll &&
                    el.clientHeight >= 100 &&
                    el.clientWidth >= 100
                );
            } catch (e) {
                return false;
            }
        });

        let moved = false;
        let movedCount = 0;

        scrollables.forEach((el) => {
            try {
                const before = el.scrollTop;
                const step = Math.max(400, Math.floor(el.clientHeight * 0.9));
                const maxScrollTop = el.scrollHeight - el.clientHeight;

                el.scrollTop = Math.min(before + step, maxScrollTop);

                if (Math.abs(el.scrollTop - before) > 1) {
                    moved = true;
                    movedCount += 1;
                }
            } catch (e) {}
        });

        const beforeWindowY = window.scrollY;
        window.scrollBy(0, 600);

        if (Math.abs(window.scrollY - beforeWindowY) > 1) {
            moved = true;
            movedCount += 1;
        }

        return {
            moved: moved,
            movedCount: movedCount,
            scrollableCount: scrollables.length,
            windowY: window.scrollY
        };
        """
    )


def verify_created_agents_in_private_list(driver, wait, created_agents):
    """
    전체 생성 완료 후 내 에이전트 목록에서 제목 일치 여부 재검증

    개선된 방식:
    - 내 에이전트 목록으로 다시 이동
    - 스크롤 위치를 맨 위로 초기화
    - 현재 화면에 보이는 제목 수집
    - 목록 내부 스크롤 div까지 아래로 이동
    - 새로 로딩된 제목을 계속 수집
    - 생성한 에이전트가 전부 발견되면 PASS
    """
    print("")
    print("=" * 60)
    print("내 에이전트 목록 최종 재검증 시작")
    print("=" * 60)

    go_to_private_agents(driver, wait)
    time.sleep(2)

    reset_all_scroll_positions(driver)

    found_agents = set()
    no_move_count = 0
    max_scan_count = 120

    for scan_count in range(1, max_scan_count + 1):
        current_found = collect_found_agent_names_from_current_screen(driver, created_agents)
        newly_found = current_found - found_agents

        if newly_found:
            for agent_name in sorted(newly_found):
                print(f"목록 제목 검증 성공: {agent_name}")

        found_agents.update(current_found)

        if len(found_agents) == len(created_agents):
            print("")
            print("생성한 모든 에이전트를 내 에이전트 목록에서 확인했습니다.")
            print("내 에이전트 목록 최종 재검증 PASS")
            return

        remaining_count = len(created_agents) - len(found_agents)
        print(
            f"목록 스캔 {scan_count}/{max_scan_count}회차 "
            f"- 확인 완료 {len(found_agents)}개 / 남은 항목 {remaining_count}개"
        )

        scroll_result = scroll_down_all_possible_containers(driver)
        time.sleep(0.8)

        if not scroll_result.get("moved"):
            no_move_count += 1
            time.sleep(1)

            current_found = collect_found_agent_names_from_current_screen(driver, created_agents)
            found_agents.update(current_found)

            if len(found_agents) == len(created_agents):
                print("")
                print("생성한 모든 에이전트를 내 에이전트 목록에서 확인했습니다.")
                print("내 에이전트 목록 최종 재검증 PASS")
                return

            if no_move_count >= 5:
                break
        else:
            no_move_count = 0

    missing_agents = []

    for agent_name in created_agents:
        if agent_name not in found_agents:
            missing_agents.append(agent_name)

    if missing_agents:
        print("")
        print("내 에이전트 목록에서 찾지 못한 에이전트:")
        for name in missing_agents:
            print(f"  - {name}")

        raise Exception("내 에이전트 목록 최종 재검증 실패")

    print("")
    print("내 에이전트 목록 최종 재검증 PASS")


def click_created_agent_card(driver, wait, agent_name):
    """
    생성 카드 클릭 검증
    생성한 에이전트 카드 클릭 시 화면 이동 또는 해당 에이전트 화면 표시 확인
    """
    print("")
    print("=" * 60)
    print("생성 카드 클릭 검증 시작")
    print(f"클릭 대상: {agent_name}")
    print("=" * 60)

    go_to_private_agents(driver, wait)
    time.sleep(1)
    reset_all_scroll_positions(driver)

    found_and_clicked = False

    for _ in range(120):
        found_and_clicked = driver.execute_script(
            """
            const targetName = arguments[0];

            function isVisible(el) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);

                return (
                    rect.width > 0 &&
                    rect.height > 0 &&
                    style.display !== 'none' &&
                    style.visibility !== 'hidden'
                );
            }

            const candidates = Array.from(document.querySelectorAll('a, button, div'))
                .filter((el) => {
                    const text = (el.innerText || el.textContent || '').trim();
                    return isVisible(el) && text.includes(targetName);
                });

            if (candidates.length === 0) {
                return false;
            }

            let target = candidates[0];

            const clickableParent =
                target.closest('a') ||
                target.closest('button') ||
                target.closest('[role="button"]') ||
                target;

            clickableParent.scrollIntoView({ block: 'center' });
            clickableParent.click();

            return true;
            """,
            agent_name,
        )

        if found_and_clicked:
            break

        scroll_down_all_possible_containers(driver)
        time.sleep(0.5)

    if not found_and_clicked:
        raise Exception(f"생성 카드 클릭 대상 에이전트를 찾지 못했습니다: {agent_name}")

    time.sleep(2)

    result = (
        agent_name in get_body_text(driver)
        or "대화" in get_body_text(driver)
        or "메시지" in get_body_text(driver)
        or "#agents" not in driver.current_url
    )

    print_check_result("생성 카드 클릭 후 화면 이동 확인", result)

    if not result:
        raise Exception("생성 카드 클릭 후 화면 이동 또는 에이전트 화면 표시를 확인하지 못했습니다.")

    print("생성 카드 클릭 검증 완료")


def create_agents(driver, wait, create_count):
    created_agents = []

    for index in range(1, create_count + 1):
        agent_name = create_one_agent(driver, wait, index, create_count)
        created_agents.append(agent_name)
        time.sleep(1)

    verify_created_agents_in_private_list(driver, wait, created_agents)

    if created_agents:
        click_created_agent_card(driver, wait, created_agents[-1])

    print("")
    print("=" * 60)
    print("전체 에이전트 생성 결과: PASS")
    print(f"요청 개수: {create_count}개")
    print(f"생성 성공: {len(created_agents)}개")
    print("내 에이전트 목록 최종 재검증: PASS")
    print("생성 카드 클릭 검증: PASS")
    print("- 생성된 에이전트 목록")

    for name in created_agents:
        print(f"  - {name}")

    print("=" * 60)


def main():
    load_env()
    configure_urls()

    create_count = ask_create_count()

    options = Options()
    options.add_argument("--window-size=1600,1000")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 40)

    try:
        driver.get(NEW_CHAT_URL)
        print("테스트 사이트 접속 완료")

        login(driver, wait)

        create_agents(driver, wait, create_count)

    except TimeoutException as e:
        print("테스트 결과: FAIL")
        print("오류 내용: 제한 시간 안에 필요한 화면 또는 요소를 찾지 못했습니다.")
        print(e)

    except StaleElementReferenceException as e:
        print("테스트 결과: FAIL")
        print("오류 내용: 화면 전환 중 요소가 갱신되어 stale element 오류가 발생했습니다.")
        print(e)

    except Exception as e:
        print("테스트 결과: FAIL")
        print("오류 내용:", e)

    finally:
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    main()