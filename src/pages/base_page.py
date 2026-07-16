from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """모든 Page Object가 공통으로 사용하는 기본 기능입니다."""

    def __init__(self, driver: webdriver.Chrome, timeout: int = 15) -> None:
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def safe_click(self, element: WebElement) -> None:
        """
        전달받은 WebElement를 클릭합니다.

        일반 클릭이 가로막힌 경우 JavaScript 클릭으로 대체합니다.
        단, stale element는 이미 사라진 요소이기 때문에
        locator 기반의 safe_click_locator()를 사용해야 합니다.
        """
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                element,
            )
            time.sleep(0.2)
            element.click()

        except ElementClickInterceptedException:
            self.driver.execute_script(
                "arguments[0].click();",
                element,
            )

    def safe_click_locator(
        self,
        locator: tuple[str, str],
        retries: int = 3,
    ) -> None:
        """
        locator로 요소를 매번 새로 찾아 클릭합니다.

        React 재렌더링으로 stale element가 발생할 수 있으므로
        클릭할 때마다 최신 요소를 다시 조회합니다.
        """
        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                element = WebDriverWait(
                    self.driver,
                    self.timeout,
                ).until(
                    EC.element_to_be_clickable(locator)
                )

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    element,
                )

                time.sleep(0.2)

                try:
                    element.click()

                except ElementClickInterceptedException:
                    self.driver.execute_script(
                        "arguments[0].click();",
                        element,
                    )

                return

            except (
                StaleElementReferenceException,
                WebDriverException,
            ) as error:
                last_error = error

                print(
                    "요소 클릭 중 화면 갱신 발생, "
                    f"재시도 {attempt}/{retries}"
                )

                time.sleep(0.5)

        raise RuntimeError(
            f"요소 클릭에 실패했습니다. locator={locator}"
        ) from last_error

    def body_text(self) -> str:
        """현재 화면의 body 텍스트를 안전하게 반환합니다."""
        try:
            return self.driver.execute_script(
                "return document.body ? document.body.innerText : '';"
            )

        except (
            StaleElementReferenceException,
            WebDriverException,
        ):
            return ""

    def find_first_visible(
        self,
        locators: Iterable[tuple[str, str]],
    ) -> WebElement | None:
        """여러 셀렉터 중 화면에 표시된 첫 번째 요소를 반환합니다."""
        for by, value in locators:
            elements = self.driver.find_elements(by, value)

            for element in elements:
                try:
                    if element.is_displayed():
                        return element

                except StaleElementReferenceException:
                    continue

        return None

    def save_screenshot(self, path: Path) -> Path:
        """현재 화면을 지정한 경로에 저장합니다."""
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.driver.save_screenshot(str(path))

        return path