from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from src.config.config import (
    LOGIN_EMAIL,
    LOGIN_PASSWORD,
    LOGIN_URL,
    WAIT_TIME,
)
from src.pages.base_page import BasePage
from src.pages.main_page import MainPage


class LoginPage(BasePage):
    """AI Helpy Chat 로그인 페이지 객체입니다."""

    EMAIL_LOCATORS = [
        (By.CSS_SELECTOR, "input[name='loginId']"),
        (By.CSS_SELECTOR, "input[placeholder='Email']"),
        (By.CSS_SELECTOR, "input[type='email']"),
    ]
    PASSWORD_LOCATORS = [
        (By.CSS_SELECTOR, "input[name='password']"),
        (By.CSS_SELECTOR, "input[placeholder='Password']"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ]
    LOGIN_BUTTON_LOCATORS = [
        (By.XPATH, "//button[@type='submit' and normalize-space()='Login']"),
        (By.XPATH, "//button[normalize-space()='Login']"),
        (By.CSS_SELECTOR, "button[type='submit']"),
    ]

    def __init__(self, driver, timeout: int = WAIT_TIME):
        super().__init__(driver, timeout=timeout)

    def get_email_input(self) -> WebElement | None:
        return self.find_first_visible(self.EMAIL_LOCATORS)

    def get_password_input(self) -> WebElement | None:
        return self.find_first_visible(self.PASSWORD_LOCATORS)

    def get_login_button(self) -> WebElement | None:
        return self.find_first_visible(self.LOGIN_BUTTON_LOCATORS)

    def is_login_page(self) -> bool:
        # After logout, a remembered account can show only the password field.
        return self.get_password_input() is not None

    def is_service_page(self, base_url: str) -> bool:
        if self.is_login_page():
            return False

        try:
            expected_host = urlparse(base_url).netloc
            current_host = urlparse(self.driver.current_url).netloc
            if expected_host != current_host:
                return False
        except Exception:
            return False

        page_text = self.body_text()
        service_texts = ["새 대화", "내 에이전트", "에이전트 마켓플레이스", "검색"]
        return any(text in page_text for text in service_texts)

    def wait_for_login_or_service_page(self, base_url: str, timeout: int = 40) -> str:
        def page_state(_driver):
            if self.is_login_page():
                return "login"
            if self.is_service_page(base_url):
                return "service"
            return False

        try:
            return WebDriverWait(self.driver, timeout).until(page_state)
        except TimeoutException as error:
            raise RuntimeError(
                "로그인 화면 또는 서비스 화면을 확인하지 못했습니다."
            ) from error

    def login(self) -> None:
        """기존 팀 테스트에서 사용하는 기본 로그인 메서드입니다."""
        self.driver.get(LOGIN_URL)
        self.login_if_needed(
            base_url=LOGIN_URL.rstrip("/"),
            login_email=LOGIN_EMAIL,
            login_password=LOGIN_PASSWORD,
        )

    def login_if_needed(
        self,
        base_url: str,
        login_email: str,
        login_password: str,
    ) -> None:
        """로그인 화면일 때만 로그인하고 완료 상태까지 검증합니다."""
        if not login_email or not login_password:
            raise ValueError(".env에 LOGIN_EMAIL과 LOGIN_PASSWORD를 입력해주세요.")

        print("로그인 상태 확인 중...")
        page_state = self.wait_for_login_or_service_page(base_url)

        if page_state == "service":
            print("기존 로그인 상태 확인 완료")
            return

        print("로그인 페이지 감지됨. 자동 로그인 진행")

        email_input = self.get_email_input()
        if email_input is not None:
            email_input.clear()
            email_input.send_keys(login_email)
        print("Email 입력 완료")

        password_input = WebDriverWait(self.driver, self.timeout).until(
            lambda _: self.get_password_input() or False
        )
        password_input.clear()
        password_input.send_keys(login_password)
        print("Password 입력 완료")

        login_succeeded = False

        for attempt in range(1, 4):
            try:
                login_button = WebDriverWait(self.driver, self.timeout).until(
                    lambda _: (
                        self.get_login_button()
                        if self.get_login_button() is not None
                        and self.get_login_button().is_enabled()
                        else False
                    )
                )
                self.safe_click(login_button)
                print("Login 버튼 클릭 완료")
                login_succeeded = True
                break
            except StaleElementReferenceException:
                print(f"Login 버튼 stale 발생, 재시도 {attempt}/3")
                time.sleep(0.5)
            except Exception:
                try:
                    password_input.send_keys(Keys.ENTER)
                    print("Login 버튼 클릭 실패, Enter로 로그인 시도")
                    login_succeeded = True
                    break
                except StaleElementReferenceException:
                    print(f"Password 입력창 stale 발생, 재시도 {attempt}/3")
                    time.sleep(0.5)

        if not login_succeeded:
            raise RuntimeError("로그인 버튼 클릭 또는 Enter 로그인 시도 실패")

        try:
            WebDriverWait(self.driver, 40).until(
                lambda _: self.is_service_page(base_url)
            )
        except TimeoutException as error:
            raise RuntimeError(
                "로그인 완료 상태를 확인하지 못했습니다. "
                f"현재 주소: {self.driver.current_url}"
            ) from error

        time.sleep(1)
        print("로그인 완료")


# ══════════════════════════════════════════════════════════════
# 로그인 기능 상세 검증용 Page Object (tests/login 전용)
# 팀 공통 LoginPage(위)와 역할이 달라 별도 클래스로 유지한다.
# ══════════════════════════════════════════════════════════════

# 명시적 대기 기본 시간 (초)
DEFAULT_TIMEOUT = 15

# 화면 안내 문구 (부분일치로 검증 - 사이트 문구가 바뀌면 여기만 수정)
MSG_INVALID_FORMAT = "잘못된 이메일 형식"
MSG_MISMATCH = "이메일 또는 비밀번호"
MSG_PW_MIN_LENGTH = "8자리 이상"
MSG_SERVER_ERROR = "예기치 못한 문제"

log = logging.getLogger(__name__)


class LoginUiPage:
    """로그인 페이지 상세 검증용. 셀렉터는 빌드 시 변하지 않는 속성만 사용한다."""

    FORM = (By.CSS_SELECTOR, "form[data-cy='signin-form']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[name='loginId']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password']")
    LOGIN_BUTTON = (
        By.CSS_SELECTOR,
        "form[data-cy='signin-form'] button[type='submit']",
    )
    # 화면에 뜨는 에러 문구 요소 (MUI 에러 텍스트)
    ERROR_TEXT = (By.CSS_SELECTOR, "p.Mui-error, p[class*='error']")
    # 비밀번호 마스킹(보기) 버튼 - aria-label 및 DOM 구조 기반 (한국어/영어 모두 호환)
    MASKING_BUTTON = (
        By.CSS_SELECTOR,
        "button[aria-label='비밀번호 보기'], button[aria-label='비밀번호 표시'], button[aria-label='View password'], button[aria-label='Show password'], input[name='password'] ~ div button",
    )
    # 비밀번호 찾기 / 회원가입 링크 - href 부분일치 (언어 무관)
    FORGOT_PW_LINK = (By.CSS_SELECTOR, "a[href*='recover/password']")
    SIGNUP_LINK = (By.CSS_SELECTOR, "a[href*='signup']")
    # 푸터의 언어 선택 드롭다운 (페이지에 select는 이것 하나뿐)
    LANGUAGE_SELECT = (By.TAG_NAME, "select")
    # 한국어 페이지 렌더링 완료 마커 (이메일 입력창의 한국어 placeholder)
    KOREAN_MARKER = (By.CSS_SELECTOR, "input[placeholder='이메일']")

    def __init__(self, driver, url=None):
        self.driver = driver
        self.url = url
        self.wait = WebDriverWait(driver, DEFAULT_TIMEOUT)

    # ── 페이지 진입 ──────────────────────────────────────────

    def open(self):
        """로그인 페이지 접속, 폼 로드 대기 후 한국어 페이지로 전환."""
        self.driver.get(self.url)
        self.wait.until(EC.visibility_of_element_located(self.FORM))
        # 접속 시 lang=en-US로 리다이렉트되므로 매번 한국어로 전환
        self._ensure_korean()
        return self

    def _ensure_korean(self):
        """언어 드롭다운이 한국어가 아니면 ko-KR로 전환 후 한국어 렌더링 대기.
        (사이트가 언어 선택을 저장하지 않아 접속할 때마다 확인이 필요하다.)"""
        # 폼보다 푸터(드롭다운)가 늦게 렌더링될 수 있어 명시적 대기 사용
        language = Select(
            self.wait.until(EC.presence_of_element_located(self.LANGUAGE_SELECT))
        )
        if language.first_selected_option.get_attribute("value") != "ko-KR":
            language.select_by_value("ko-KR")
            self.wait.until(EC.presence_of_element_located(self.KOREAN_MARKER))

    def refresh(self):
        """새로고침 후 로그인 폼이 다시 뜰 때까지 대기, 폼 요소 반환."""
        self.driver.refresh()
        return self.wait.until(EC.visibility_of_element_located(self.FORM))

    # ── 요소 접근 ──────────────────────────────────────────

    def form(self):
        return self.driver.find_element(*self.FORM)

    def email_input(self):
        return self.driver.find_element(*self.EMAIL_INPUT)

    def password_input(self):
        return self.driver.find_element(*self.PASSWORD_INPUT)

    def login_button(self):
        return self.driver.find_element(*self.LOGIN_BUTTON)

    def wait_password_visible(self):
        """비밀번호 입력창이 보일 때까지 대기 (로그인 화면 복귀 판정용)."""
        return self.wait.until(EC.visibility_of_element_located(self.PASSWORD_INPUT))

    # ── 로그인 동작 ────────────────────────────────────────

    def submit_login(self, email, password):
        """이메일/비밀번호 입력 후 로그인 버튼 클릭까지 수행."""
        self.email_input().send_keys(email)
        self.password_input().send_keys(password)
        self.login_button().click()

    def expect_error(self, email, password):
        """로그인 제출 후 확정된 화면 에러 문구를 반환한다 (판정은 호출부 assert 담당).

        기대 문구가 뜨는 순간 반환하면 안 된다. 이 화면은 클라이언트 검증 문구가 먼저
        잠깐 떴다가 서버 응답 문구로 바뀌므로(예: '잘못된 이메일 형식입니다.' 0.5초 →
        '예기치 못한 문제가 발생하였습니다.'), 과도기 문구를 잡아 거짓 통과할 수 있다.
        """
        self.submit_login(email, password)
        return self.settled_error_text()

    def settled_error_text(self, settle=1.5):
        """에러 문구가 settle초 동안 바뀌지 않을 때까지 기다린 뒤 그 값을 반환한다."""
        deadline = time.monotonic() + DEFAULT_TIMEOUT
        text = self.error_text_now()
        last_change = time.monotonic()
        while time.monotonic() < deadline:
            time.sleep(0.2)
            current = self.error_text_now()
            if current != text:
                text, last_change = current, time.monotonic()
            elif text and time.monotonic() - last_change >= settle:
                break
        log.info("확정 화면 문구: '%s'", text)
        return text

    def error_text_now(self):
        """현재 화면의 에러 문구 (없으면 빈 문자열, 대기하지 않음)."""
        found = self.driver.find_elements(*self.ERROR_TEXT)
        return found[0].text if found else ""

    # ── 브라우저 기본 검증 ─────────────────────────────────

    def focused_validation(self):
        """브라우저 기본 검증(required)이 지목한 입력칸 name과 안내문구를 반환."""
        # 클릭 직후 브라우저가 빈 칸으로 포커스를 옮길 때까지 대기
        # (제한시간 안에 안 옮겨지면 그 시점의 상태를 반환해 assert가 판정)
        try:
            self.wait.until(
                lambda d: d.switch_to.active_element.get_attribute("name")
            )
        except TimeoutException:
            pass
        focused = self.driver.switch_to.active_element
        field = focused.get_attribute("name")
        msg = focused.get_attribute("validationMessage")
        log.info("브라우저가 지목한 칸: %s | 안내문구: '%s'", field, msg)
        return field, msg

    def focused_name(self):
        """현재 포커스된 요소의 name 속성."""
        return self.driver.switch_to.active_element.get_attribute("name")

    def email_validation_message(self):
        """이메일 입력창의 브라우저 검증 말풍선 문구."""
        return self.email_input().get_attribute("validationMessage")

    def email_type_mismatch(self):
        """브라우저가 이메일 형식 오류(typeMismatch)로 판정했는지 여부."""
        return self.driver.execute_script(
            "return arguments[0].validity.typeMismatch;", self.email_input()
        )

    # ── 입력창 UI ─────────────────────────────────────────

    def email_placeholder(self):
        return self.email_input().get_attribute("placeholder")

    def password_placeholder(self):
        return self.password_input().get_attribute("placeholder")

    def password_type(self):
        """비밀번호 입력창의 type 속성 (password=마스킹, text=표시)."""
        return self.password_input().get_attribute("type")

    def toggle_masking(self):
        """마스킹(비밀번호 보기) 버튼 클릭. 오버레이 간섭을 피해 JS 클릭 사용."""
        btn = self.driver.find_element(*self.MASKING_BUTTON)
        self.driver.execute_script("arguments[0].click();", btn)

    def wait_password_type(self, expected):
        """비밀번호 입력창 type이 기대값으로 바뀔 때까지 대기."""
        self.wait.until(
            lambda d: (
                d.find_element(*self.PASSWORD_INPUT).get_attribute("type") == expected
            )
        )

    # ── 링크 이동 ─────────────────────────────────────────

    def click_forgot_password(self):
        """비밀번호 찾기 링크 클릭 후 이동 완료까지 대기, 이동한 URL 반환."""
        self.driver.find_element(*self.FORGOT_PW_LINK).click()
        self.wait.until(EC.url_contains("recover/password"))
        return self.driver.current_url

    def click_signup(self):
        """회원가입 링크 클릭 후 이동 완료까지 대기, 이동한 URL 반환."""
        self.driver.find_element(*self.SIGNUP_LINK).click()
        self.wait.until(EC.url_contains("signup"))
        return self.driver.current_url


def login(driver, url, email, password):
    """로그인 전체 플로우: 접속 -> 제출 -> 완료(프로필 아이콘) 대기. LoginUiPage 반환."""
    page = LoginUiPage(driver, url).open()
    page.submit_login(email, password)
    MainPage(driver).wait_logged_in(url)
    return page
