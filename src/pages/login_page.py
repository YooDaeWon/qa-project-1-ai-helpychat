from __future__ import annotations

import time
from urllib.parse import urlparse

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config.config import (
    LOGIN_EMAIL,
    LOGIN_PASSWORD,
    LOGIN_URL,
    WAIT_TIME,
)
from src.pages.base_page import BasePage


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
        return self.get_email_input() is not None and self.get_password_input() is not None

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
            raise ValueError(
                ".env에 LOGIN_EMAIL과 LOGIN_PASSWORD를 입력해주세요."
            )

        print("로그인 상태 확인 중...")
        page_state = self.wait_for_login_or_service_page(base_url)

        if page_state == "service":
            print("기존 로그인 상태 확인 완료")
            return

        print("로그인 페이지 감지됨. 자동 로그인 진행")

        email_input = WebDriverWait(self.driver, self.timeout).until(
            lambda _: self.get_email_input() or False
        )
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
