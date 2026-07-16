from __future__ import annotations

import re
import time
from urllib.parse import urlparse

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from src.config.config import Settings
from src.pages.base_page import BasePage
from src.pages.login_page import LoginPage


AUTOMATION_AGENT_TITLE_PATTERN = re.compile(
    r"^자동화테스트에이전트_\d{8}_\d{6}_\d{3}회차$"
)


class AgentListPage(BasePage):
    """내 에이전트 목록 화면을 담당하는 Page Object입니다."""

    PRIVATE_PANEL = (
        By.CSS_SELECTOR,
        "[role='tabpanel'][id$='agents-private']",
    )
    PRIVATE_TAB_LOCATORS = [
        (By.CSS_SELECTOR, "button[role='tab'][id$='agents-private']"),
        (By.CSS_SELECTOR, "button[role='tab'][aria-controls$='agents-private']"),
        (By.XPATH, "//button[@role='tab' and contains(normalize-space(), '내 에이전트')]"),
        (By.XPATH, "//*[@role='tab' and contains(normalize-space(), '내 에이전트')]"),
        (By.XPATH, "//button[contains(normalize-space(), '내 에이전트')]"),
    ]
    CREATE_AGENT_LINK = (By.CSS_SELECTOR, "a[href='/agents/builder']")
    EMPTY_MESSAGE = (
        By.XPATH,
        "//*[normalize-space()='나만의 에이전트를 만들어 보세요.']",
    )

    def __init__(self, driver, settings: Settings) -> None:
        super().__init__(driver, timeout=settings.default_wait_time)
        self.settings = settings

    def get_visible_private_panel(self) -> WebElement | None:
        for panel in self.driver.find_elements(*self.PRIVATE_PANEL):
            try:
                if panel.is_displayed():
                    return panel
            except StaleElementReferenceException:
                continue
        return None

    def get_visible_private_tab(self) -> WebElement | None:
        return self.find_first_visible(self.PRIVATE_TAB_LOCATORS)

    def wait_for_new_chat_page(self) -> None:
        """새 대화 기본 화면이 로딩될 때까지 기다립니다."""
        self.wait.until(
            lambda _: (
                "AI Helpy Chat" in self.body_text()
                and "Helpy Pro Agent" in self.body_text()
            )
        )
        self.wait.until(
            lambda _: (
                "기관 에이전트" in self.body_text()
                or "내 에이전트" in self.body_text()
                or "필요한 모든 순간" in self.body_text()
            )
        )
        print("새 대화 기본 화면 확인 완료")

    def open(self) -> None:
        """에이전트 조직 화면에서 내 에이전트 탭으로 이동합니다."""
        print("새 대화 화면으로 이동 시도")
        self.driver.get(self.settings.new_chat_url)

        login_page = LoginPage(self.driver, timeout=self.settings.default_wait_time)
        page_state = login_page.wait_for_login_or_service_page(
            self.settings.base_url,
            timeout=self.settings.page_wait_time,
        )

        if page_state == "login":
            print("화면 이동 중 로그인 페이지 감지됨")
            login_page.login_if_needed(
                base_url=self.settings.base_url,
                login_email=self.settings.login_email,
                login_password=self.settings.login_password,
            )

        if "#agents-organization" not in self.driver.current_url:
            self.driver.get(self.settings.new_chat_url)
            page_state = login_page.wait_for_login_or_service_page(
                self.settings.base_url,
                timeout=self.settings.page_wait_time,
            )
            if page_state == "login":
                login_page.login_if_needed(
                    base_url=self.settings.base_url,
                    login_email=self.settings.login_email,
                    login_password=self.settings.login_password,
                )
                self.driver.get(self.settings.new_chat_url)

        try:
            self.wait_for_new_chat_page()
        except TimeoutException:
            # 서비스 문구가 일부 변경되어도 내 에이전트 탭/패널이 있으면 진행합니다.
            if self.get_visible_private_panel() is None and self.get_visible_private_tab() is None:
                raise RuntimeError("에이전트 조직 화면 로딩을 확인하지 못했습니다.")

        print("에이전트 조직 화면 로딩 확인 완료")

        if self.get_visible_private_panel() is not None:
            print("내 에이전트 화면 진입 확인 완료")
            return

        try:
            private_tab = WebDriverWait(
                self.driver,
                self.settings.page_wait_time,
            ).until(lambda _: self.get_visible_private_tab() or False)
        except TimeoutException as error:
            raise RuntimeError("내 에이전트 탭을 찾지 못했습니다.") from error

        self.safe_click(private_tab)
        print("내 에이전트 탭 클릭 완료")

        try:
            WebDriverWait(
                self.driver,
                self.settings.default_wait_time,
            ).until(
                lambda _: (
                    self.get_visible_private_panel() is not None
                    or "에이전트 만들기" in self.body_text()
                )
            )
        except TimeoutException as error:
            raise RuntimeError("내 에이전트 화면 진입을 확인하지 못했습니다.") from error

        print("내 에이전트 화면 진입 확인 완료")

    def click_create_agent_link(self) -> None:
        """
        에이전트 만들기 링크를 클릭합니다.

        내 에이전트 탭 전환 직후 React 화면이 다시 렌더링되면서
        기존 WebElement가 stale 상태가 될 수 있으므로 locator 기준으로
        요소를 매번 새로 찾아 클릭합니다.
        """
        print("에이전트 만들기 링크 찾는 중...")

        try:
            self.safe_click_locator(
                self.CREATE_AGENT_LINK,
                retries=5,
            )
            print("에이전트 만들기 링크 클릭 완료")

        except RuntimeError:
            print(
                "에이전트 만들기 링크 클릭 실패. "
                "builder URL로 직접 이동합니다."
            )
            self.driver.get(self.settings.builder_url)

        try:
            self.wait.until(
                lambda _: (
                    "builder" in self.driver.current_url
                    or "새 에이전트 만들기" in self.body_text()
                    or "대화로 만들기" in self.body_text()
                    or "설정" in self.body_text()
                )
            )
            print("에이전트 만들기 화면 진입 확인 완료")

        except TimeoutException:
            print("화면 이동 확인 실패. builder URL로 직접 이동합니다.")
            self.driver.get(self.settings.builder_url)

            self.wait.until(
                lambda _: (
                    "builder" in self.driver.current_url
                    or "새 에이전트 만들기" in self.body_text()
                    or "대화로 만들기" in self.body_text()
                    or "설정" in self.body_text()
                )
            )
            print("builder URL 직접 이동 완료")

    @staticmethod
    def get_relative_agent_href(agent_url: str) -> str:
        return urlparse(agent_url).path

    def get_agent_links(self, private_panel: WebElement) -> list[WebElement]:
        """내 에이전트 상세 링크를 중복 없이 반환합니다."""
        agent_links = private_panel.find_elements(By.CSS_SELECTOR, "a[href^='/agents/']")
        unique_links: list[WebElement] = []
        seen_hrefs: set[str] = set()

        for agent_link in agent_links:
            try:
                href = agent_link.get_attribute("href")
                if not href:
                    continue
                relative_href = self.get_relative_agent_href(href)
                if relative_href == "/agents/builder":
                    continue
                if not relative_href.startswith("/agents/"):
                    continue
                if relative_href in seen_hrefs:
                    continue
                seen_hrefs.add(relative_href)
                unique_links.append(agent_link)
            except StaleElementReferenceException:
                continue

        return unique_links

    @staticmethod
    def get_agent_title(agent_link: WebElement) -> str:
        try:
            for title_element in agent_link.find_elements(By.CSS_SELECTOR, "p"):
                title = title_element.text.strip()
                if title:
                    return title
        except StaleElementReferenceException:
            pass
        return "제목 없음"

    def build_agent_info(self, agent_link: WebElement) -> dict[str, str]:
        absolute_href = agent_link.get_attribute("href")
        if not absolute_href:
            raise RuntimeError("에이전트 상세 링크를 확인하지 못했습니다.")
        return {
            "title": self.get_agent_title(agent_link),
            "absolute_href": absolute_href,
            "relative_href": self.get_relative_agent_href(absolute_href),
        }

    @staticmethod
    def is_automation_test_agent(agent_title: str) -> bool:
        return AUTOMATION_AGENT_TITLE_PATTERN.fullmatch(agent_title) is not None

    def reset_scroll_positions(self) -> None:
        """window와 내부 스크롤 영역을 모두 맨 위로 초기화합니다."""
        self.driver.execute_script(
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

    def scroll_down_all_possible_containers(self) -> dict:
        """화면과 내부 스크롤 가능한 영역을 아래로 이동합니다."""
        return self.driver.execute_script(
            """
            function isVisible(el) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return (
                    rect.width > 0 && rect.height > 0 && rect.bottom > 0 &&
                    rect.top < window.innerHeight && style.display !== 'none' &&
                    style.visibility !== 'hidden'
                );
            }

            const elements = Array.from(document.querySelectorAll('*'));
            const scrollables = elements.filter((el) => {
                try {
                    const style = window.getComputedStyle(el);
                    const overflowY = style.overflowY;
                    const hasScrollableOverflow = el.scrollHeight > el.clientHeight + 50;
                    const overflowAllowsScroll = ['auto', 'scroll', 'overlay', 'visible'].includes(overflowY);
                    return (
                        isVisible(el) && hasScrollableOverflow && overflowAllowsScroll &&
                        el.clientHeight >= 100 && el.clientWidth >= 100
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

    def collect_visible_agent_names(self, expected_names: list[str]) -> set[str]:
        page_text = self.body_text()
        return {name for name in expected_names if name in page_text}

    def verify_agent_names(self, expected_names: list[str]) -> set[str]:
        """목록 전체를 스캔하여 생성한 에이전트 제목을 재검증합니다."""
        print("\n" + "=" * 60)
        print("내 에이전트 목록 최종 재검증 시작")
        print("=" * 60)

        self.open()
        time.sleep(2)
        self.reset_scroll_positions()

        found_agents: set[str] = set()
        no_move_count = 0

        for scan_count in range(1, self.settings.max_list_scan_count + 1):
            current_found = self.collect_visible_agent_names(expected_names)
            newly_found = current_found - found_agents
            for agent_name in sorted(newly_found):
                print(f"목록 제목 검증 성공: {agent_name}")
            found_agents.update(current_found)

            if len(found_agents) == len(expected_names):
                print("생성한 모든 에이전트를 내 에이전트 목록에서 확인했습니다.")
                print("내 에이전트 목록 최종 재검증 PASS")
                return found_agents

            remaining_count = len(expected_names) - len(found_agents)
            print(
                f"목록 스캔 {scan_count}/{self.settings.max_list_scan_count}회차 "
                f"- 확인 완료 {len(found_agents)}개 / 남은 항목 {remaining_count}개"
            )

            scroll_result = self.scroll_down_all_possible_containers()
            time.sleep(0.8)

            if not scroll_result.get("moved"):
                no_move_count += 1
                time.sleep(1)
                found_agents.update(self.collect_visible_agent_names(expected_names))
                if no_move_count >= 5:
                    break
            else:
                no_move_count = 0

        missing_agents = [name for name in expected_names if name not in found_agents]
        if missing_agents:
            print("내 에이전트 목록에서 찾지 못한 에이전트:")
            for name in missing_agents:
                print(f"  - {name}")
            raise AssertionError("내 에이전트 목록 최종 재검증 실패")

        return found_agents

    def click_agent_card(self, agent_name: str) -> None:
        """지정한 에이전트 카드를 찾아 클릭하고 화면 이동을 검증합니다."""
        print("\n" + "=" * 60)
        print("생성 카드 클릭 검증 시작")
        print(f"클릭 대상: {agent_name}")
        print("=" * 60)

        self.open()
        time.sleep(1)
        self.reset_scroll_positions()

        found_and_clicked = False

        for _ in range(self.settings.max_list_scan_count):
            found_and_clicked = self.driver.execute_script(
                """
                const targetName = arguments[0];
                function isVisible(el) {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return (
                        rect.width > 0 && rect.height > 0 &&
                        style.display !== 'none' && style.visibility !== 'hidden'
                    );
                }

                const candidates = Array.from(document.querySelectorAll('a, button, div'))
                    .filter((el) => {
                        const text = (el.innerText || el.textContent || '').trim();
                        return isVisible(el) && text.includes(targetName);
                    });

                if (candidates.length === 0) return false;
                const target = candidates[0];
                const clickableParent =
                    target.closest('a') || target.closest('button') ||
                    target.closest('[role="button"]') || target;
                clickableParent.scrollIntoView({ block: 'center' });
                clickableParent.click();
                return true;
                """,
                agent_name,
            )
            if found_and_clicked:
                break
            self.scroll_down_all_possible_containers()
            time.sleep(0.5)

        if not found_and_clicked:
            raise AssertionError(f"생성 카드 클릭 대상 에이전트를 찾지 못했습니다: {agent_name}")

        time.sleep(2)
        result = (
            agent_name in self.body_text()
            or "대화" in self.body_text()
            or "메시지" in self.body_text()
            or "#agents" not in self.driver.current_url
        )
        if not result:
            raise AssertionError(
                "생성 카드 클릭 후 화면 이동 또는 에이전트 화면 표시를 확인하지 못했습니다."
            )
        print("[PASS] 생성 카드 클릭 후 화면 이동 확인")

    def reset_agent_scroll(self) -> None:
        self.driver.execute_script("window.scrollTo(0, 0);")
        private_panel = self.get_visible_private_panel()
        if private_panel is not None:
            try:
                self.driver.execute_script("arguments[0].scrollTop = 0;", private_panel)
            except StaleElementReferenceException:
                pass
        time.sleep(self.settings.scroll_wait_time)

    def scroll_agent_list(self) -> None:
        private_panel = self.get_visible_private_panel()
        if private_panel is not None:
            try:
                self.driver.execute_script(
                    """
                    arguments[0].scrollTop = arguments[0].scrollTop +
                        Math.max(arguments[0].clientHeight * 0.8, 500);
                    """,
                    private_panel,
                )
            except StaleElementReferenceException:
                pass
        self.driver.execute_script(
            "window.scrollBy(0, Math.max(window.innerHeight * 0.8, 500));"
        )
        time.sleep(self.settings.scroll_wait_time)

    def get_target_agent_info(
        self,
        delete_mode: str,
        excluded_hrefs: set[str],
    ) -> dict[str, str] | None:
        """삭제 방식에 맞는 첫 번째 삭제 대상 에이전트를 반환합니다."""
        self.reset_agent_scroll()
        checked_hrefs: set[str] = set()

        for _ in range(self.settings.max_scroll_count):
            private_panel = self.get_visible_private_panel()
            if private_panel is None:
                raise RuntimeError("내 에이전트 패널을 찾지 못했습니다.")

            for agent_link in self.get_agent_links(private_panel):
                try:
                    agent_info = self.build_agent_info(agent_link)
                    relative_href = agent_info["relative_href"]
                    if relative_href in checked_hrefs or relative_href in excluded_hrefs:
                        continue
                    checked_hrefs.add(relative_href)

                    if delete_mode == "all":
                        return agent_info
                    if self.is_automation_test_agent(agent_info["title"]):
                        return agent_info
                except (StaleElementReferenceException, WebDriverException):
                    continue

            self.scroll_agent_list()

        return None

    def locate_agent_link(self, relative_href: str) -> WebElement:
        self.reset_agent_scroll()
        xpath = f"//a[@href='{relative_href}']"

        for _ in range(self.settings.max_scroll_count):
            for link in self.driver.find_elements(By.XPATH, xpath):
                try:
                    if link.is_displayed():
                        return link
                except StaleElementReferenceException:
                    continue
            self.scroll_agent_list()

        raise RuntimeError(f"삭제 대상 에이전트 링크를 찾지 못했습니다: {relative_href}")

    @staticmethod
    def find_agent_card(agent_link: WebElement) -> WebElement:
        try:
            return agent_link.find_element(
                By.XPATH,
                "./ancestor::*[contains(@class, 'MuiCard-root')][1]",
            )
        except NoSuchElementException as error:
            raise RuntimeError("에이전트 카드 영역을 찾지 못했습니다.") from error

    def is_empty_agent_list(self) -> bool:
        for empty_message in self.driver.find_elements(*self.EMPTY_MESSAGE):
            try:
                if empty_message.is_displayed():
                    return True
            except StaleElementReferenceException:
                continue
        return False