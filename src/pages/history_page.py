from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from src.config.config import (
    BASE_URL,
    CHAT_READY_TIMEOUT,
    DEFAULT_TIMEOUT,
)
from src.core.login import login_if_needed, wait_for_login_or_page
from src.pages.base_page import BasePage


class HistoryPage(BasePage):
    """채팅 히스토리의 생성, 조회, 재접속, 삭제 동작을 다루는 페이지 객체입니다."""

    # 히스토리는 가상 스크롤 목록으로 렌더링되므로 현재 화면에 표시된 항목을 기준으로 찾습니다.
    HISTORY_LISTS = [
        (By.CSS_SELECTOR, "[data-testid='virtuoso-item-list']"),
    ]
    CHAT_AREAS = [
        (By.CSS_SELECTOR, "main"),
    ]
    CHAT_INPUTS = [
        (By.CSS_SELECTOR, "textarea[placeholder*='메시지']"),
        (By.CSS_SELECTOR, "textarea[placeholder*='질문']"),
        (By.CSS_SELECTOR, "textarea"),
        (By.CSS_SELECTOR, "[contenteditable='true'][role='textbox']"),
        (By.CSS_SELECTOR, "[contenteditable='true']"),
    ]
    SEND_BUTTONS = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "button[aria-label*='전송']"),
        (By.CSS_SELECTOR, "button[aria-label*='보내기']"),
        (By.CSS_SELECTOR, "button[title*='전송']"),
        (By.CSS_SELECTOR, "button[title*='보내기']"),
    ]

    def open(self):
        """서비스에 접속하고 로그인한 뒤 채팅 입력창이 준비될 때까지 기다립니다."""
        self.driver.get(BASE_URL)
        wait_for_login_or_page(
            self.driver,
            lambda: bool(self.first_visible(self.CHAT_INPUTS))
        )
        login_if_needed(self.driver)
        self.wait_until_ready()
        return self

    def wait_until_ready(self):
        """채팅 입력창을 사용할 수 있는 상태가 될 때까지 기다립니다."""
        return self.wait_visible(self.CHAT_INPUTS, CHAT_READY_TIMEOUT)

    def send_message(self, message):
        """메시지를 전송하고 실제 대화 영역에 표시됐는지 확인합니다."""
        chat_input = self.wait_until_ready()
        chat_input.click()
        if chat_input.get_attribute("contenteditable") == "true":
            chat_input.send_keys(Keys.CONTROL, "a")
            chat_input.send_keys(Keys.BACKSPACE)
        else:
            chat_input.clear()
        chat_input.send_keys(message)
        chat_input.send_keys(Keys.ENTER)

        # Enter 전송이 동작하지 않는 UI에서는 전송 버튼을 눌러 한 번 더 시도합니다.
        try:
            self.wait_for_message(message, timeout=5)
        except TimeoutException:
            self.click(self.wait_visible(self.SEND_BUTTONS, timeout=10))
            self.wait_for_message(message)

    def history_item(self, key):
        """사이드바에서 key를 포함하는 가장 구체적인 히스토리 항목을 찾습니다."""
        history_list = self.first_visible(self.HISTORY_LISTS)
        if not history_list:
            return False

        # 상위 li와 내부 링크가 같은 제목을 가질 수 있어 면적이 가장 작은 요소를 선택합니다.
        candidates = []
        for element in history_list.find_elements(
            By.CSS_SELECTOR,
            "a, button, [role='button'], li",
        ):
            try:
                rect = element.rect
                text = self.normalize(element.text)
                area = rect.get("width", 0) * rect.get("height", 0)
                if (
                    element.is_displayed()
                    and key in text
                    and area > 0
                ):
                    candidates.append((area, element))
            except StaleElementReferenceException:
                continue
        return min(candidates, key=lambda item: item[0])[1] if candidates else False

    def wait_for_history(self, key, timeout=DEFAULT_TIMEOUT):
        """새 히스토리가 사이드바에 나타날 때까지 기다립니다."""
        return WebDriverWait(self.driver, timeout).until(
            lambda _: self.history_item(key)
        )

    def open_history(self, key):
        """key에 해당하는 히스토리를 엽니다."""
        self.click(self.wait_for_history(key))

    def message_is_visible(self, message):
        """대화 영역에 테스트 메시지가 표시되어 있는지 확인합니다."""
        chat_area = self.first_visible(self.CHAT_AREAS)
        if not chat_area:
            return False

        # 넓은 상위 컨테이너의 텍스트가 우연히 일치하지 않도록 길이를 함께 제한합니다.
        for element in chat_area.find_elements(
            By.CSS_SELECTOR,
            "p, span, div, article, [role='listitem']",
        ):
            try:
                text = self.normalize(element.text)
                if (
                    element.is_displayed()
                    and message in text
                    and len(text) <= len(message) + 100
                ):
                    return True
            except StaleElementReferenceException:
                continue
        return False

    def wait_for_message(self, message, timeout=DEFAULT_TIMEOUT):
        """전송하거나 불러온 메시지가 화면에 나타날 때까지 기다립니다."""
        return WebDriverWait(self.driver, timeout).until(
            lambda _: self.message_is_visible(message)
        )

    def refresh(self):
        """현재 페이지를 새로고침하고 채팅 화면이 다시 준비될 때까지 기다립니다."""
        self.driver.refresh()
        self.wait_until_ready()

    def delete_history(self, key, href=None):
        """히스토리를 삭제하고 사이드바에서 사라졌는지 확인합니다."""
        WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            lambda _: self.first_visible(self.HISTORY_LISTS)
        )
        try:
            before_count = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                lambda _: self._history_target_count(key, href) or False
            )
        except TimeoutException as error:
            raise RuntimeError(f"삭제할 히스토리를 찾지 못했습니다: {key}") from error

        self._open_history_menu_and_click_delete(key, href)
        self._confirm_delete_if_needed()

        # 삭제 요청이 완료되기 전에 다른 URL로 이동하면 브라우저가 요청을 취소할 수 있습니다.
        # 현재 화면에서 대상 항목 수가 실제로 감소한 것을 먼저 확인합니다.
        print(f"[WAIT] 삭제 반영 확인 중: {key}")
        try:
            WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                lambda _: self._history_target_count(key, href) < before_count
            )
        except TimeoutException as error:
            raise RuntimeError(
                f"삭제 버튼을 눌렀지만 히스토리가 목록에서 줄어들지 않았습니다: {key}"
            ) from error
        print(f"[DONE] 삭제 반영 완료: {key}")

    def delete_history_at_index(self, index=0):
        """현재 화면에서 지정한 순서의 히스토리 행을 삭제합니다."""
        before_titles = self.history_titles()
        rows = self._history_rows()
        if index >= len(rows):
            raise RuntimeError(
                f"삭제할 히스토리 순서가 목록 범위를 벗어났습니다: {index}"
            )

        title = self.normalize(rows[index].text)
        self._open_history_row_menu_and_click_delete(index)
        self._confirm_delete_if_needed()

        print(f"[WAIT] 삭제 반영 확인 중: {title}")
        try:
            WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                lambda _: self.history_titles() != before_titles
            )
        except TimeoutException as error:
            raise RuntimeError(
                f"삭제 버튼을 눌렀지만 히스토리 목록이 변경되지 않았습니다: {title}"
            ) from error
        print(f"[DONE] 삭제 반영 완료: {title}")
        return title

    def _history_rows(self):
        """Virtuoso 목록에서 화면에 표시된 실제 히스토리 행을 반환합니다."""
        history_list = self.first_visible(self.HISTORY_LISTS)
        if not history_list:
            return []
        rows = []
        for row in history_list.find_elements(By.XPATH, "./*"):
            try:
                if row.is_displayed() and self.normalize(row.text):
                    rows.append(row)
            except StaleElementReferenceException:
                continue
        return rows

    def _open_history_row_menu_and_click_delete(self, index):
        """삭제 직전 최신 목록에서 지정한 행의 메뉴를 열어 삭제합니다."""
        last_error = None
        for _ in range(5):
            try:
                rows = self._history_rows()
                if index >= len(rows):
                    raise RuntimeError(
                        f"삭제할 히스토리 순서가 목록 범위를 벗어났습니다: {index}"
                    )
                row = rows[index]
                self._reveal_history_actions(row)
                menu_button = WebDriverWait(self.driver, 10).until(
                    lambda _: self._history_menu_button_in_row(row)
                )
                self._click_dom(menu_button)
                delete_action = self._wait_action({"삭제", "delete"})
                self._click_dom(delete_action)
                return
            except StaleElementReferenceException as error:
                last_error = error

        raise RuntimeError(
            f"목록이 갱신되어 {index + 1}번째 히스토리 메뉴를 열지 못했습니다."
        ) from last_error

    def _history_menu_button_in_row(self, row):
        """전달받은 실제 히스토리 행 내부의 메뉴 버튼을 찾습니다."""
        return self.driver.execute_script(
            """
            const row = arguments[0];
            for (const type of ['mouseover', 'mouseenter', 'mousemove']) {
                row.dispatchEvent(new MouseEvent(type, {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                }));
            }
            const selectors = [
                '.menu-button--visible button',
                '.menu-button button',
                '.menu-button--visible [data-testid="ellipsis-verticalIcon"]',
                '.menu-button [data-testid="ellipsis-verticalIcon"]',
                '[data-testid="ellipsis-verticalIcon"]',
            ];
            for (const selector of selectors) {
                const found = row.querySelector(selector);
                if (found) return found.closest('button') || found;
            }
            return null;
            """,
            row,
        )

    def _open_history_menu_and_click_delete(self, key, href=None):
        """최신 요소로 메뉴와 삭제 버튼을 누르고 stale 발생 시 재시도합니다."""
        last_error = None
        for _ in range(3):
            try:
                item = (
                    WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                        lambda _: self.history_entry(href)
                    )
                    if href
                    else self.wait_for_history(key)
                )
                self._reveal_history_actions(item)
                menu_button = WebDriverWait(self.driver, 10).until(
                    lambda _: self._history_menu_button(key, href)
                )
                self._click_dom(menu_button)
                WebDriverWait(self.driver, 10).until(
                    lambda _: self._find_action({"삭제", "delete"})
                )
                delete_action = self._wait_action({"삭제", "delete"})
                self._click_dom(delete_action)
                return
            except StaleElementReferenceException as error:
                last_error = error

        raise RuntimeError(
            f"목록이 갱신되어 히스토리 메뉴를 열지 못했습니다: {key}"
        ) from last_error

    def _reveal_history_actions(self, item):
        """대상 항목에 호버 이벤트를 보내 숨겨진 메뉴 버튼을 표시합니다."""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            item,
        )
        ActionChains(self.driver).move_to_element(item).pause(0.2).perform()
        self.driver.execute_script(
            """
            let element = arguments[0];
            for (let depth = 0; depth < 8 && element; depth++, element = element.parentElement) {
                for (const type of ['mouseover', 'mouseenter', 'mousemove']) {
                    element.dispatchEvent(new MouseEvent(type, {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                    }));
                }
            }
            """,
            item,
        )

    def _history_menu_button(self, key, href=None):
        """DOM 구조가 달라도 대상 히스토리 행 내부의 메뉴 버튼을 찾습니다."""
        return self.driver.execute_script(
            """
            const key = arguments[0];
            const href = arguments[1];
            const list = document.querySelector('[data-testid="virtuoso-item-list"]');
            if (!list) return null;
            const selectors = [
                '.menu-button--visible button',
                '.menu-button button',
                '.menu-button--visible [data-testid="ellipsis-verticalIcon"]',
                '.menu-button [data-testid="ellipsis-verticalIcon"]',
                '[data-testid="ellipsis-verticalIcon"]',
            ];
            const clickable = element => element.closest('button') || element;
            const unique = elements => [...new Set(elements.filter(Boolean))];
            const collect = root => unique(selectors.flatMap(
                selector => Array.from(root.querySelectorAll(selector))
            ));
            const dispatchHover = element => {
                for (const type of ['mouseover', 'mouseenter', 'mousemove']) {
                    element.dispatchEvent(new MouseEvent(type, {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                    }));
                }
            };
            const exactRowMenu = row => {
                if (!row) return null;
                if (!href && (!row.innerText || !row.innerText.includes(key))) return null;
                dispatchHover(row);
                const menus = collect(row);
                return menus.length ? clickable(menus[0]) : null;
            };

            if (href) {
                const anchor = Array.from(list.querySelectorAll('a[href]')).find(
                    element => element.href === href
                );
                for (
                    let row = anchor, depth = 0;
                    row && list.contains(row) && depth < 8;
                    row = row.parentElement, depth++
                ) {
                    const menu = exactRowMenu(row);
                    if (menu) return menu;
                }
                return null;
            }

            const rowSelectors = [
                'li',
                'a',
                '[role="button"]',
                '[role="listitem"]',
                '[class*="history"]',
                '[class*="History"]',
            ];
            for (const selector of rowSelectors) {
                for (const candidate of list.querySelectorAll(selector)) {
                    const menu = exactRowMenu(candidate);
                    if (menu) return menu;
                }
            }

            return null;
            """,
            key,
            href,
        )

    def _wait_action(self, labels, timeout=10, root=None):
        """주어진 라벨 중 하나와 일치하는 액션이 나타날 때까지 기다립니다."""
        return WebDriverWait(self.driver, timeout).until(
            lambda _: self._find_action(labels, root=root)
        )

    def _find_action(self, labels, root=None):
        """텍스트와 접근성 속성을 이용해 가장 정확한 액션 요소를 선택합니다."""
        labels = {self.normalize(label).lower() for label in labels}
        search_root = root or self.driver
        candidates = []
        for element in search_root.find_elements(
            By.CSS_SELECTOR,
            "[role='menuitem'], [role='option'], button, li, p, span",
        ):
            try:
                if not element.is_displayed():
                    continue
                values = [
                    self.normalize(element.text).lower(),
                    self.normalize(element.get_attribute("aria-label")).lower(),
                    self.normalize(element.get_attribute("title")).lower(),
                ]
                exact = any(label and label == value for label in labels for value in values)
                partial = any(label and label in value for label in labels for value in values)
                if not exact and not partial:
                    continue

                rect = element.rect
                area = rect.get("width", 0) * rect.get("height", 0)
                target = self.driver.execute_script(
                    """
                    const element = arguments[0];
                    return element.closest(
                        "[role='menuitem'], [role='option'], button, li, [tabindex]"
                    ) || element;
                    """,
                    element,
                )
                candidates.append((0 if exact else 1, area, target))
            except StaleElementReferenceException:
                continue

        if not candidates:
            return False
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]

    def _confirm_delete_if_needed(self):
        """삭제 확인 창이 표시되는 UI에서 확인 버튼을 누릅니다."""
        try:
            dialog = WebDriverWait(self.driver, 3).until(
                lambda _: self.first_visible(
                    [(By.CSS_SELECTOR, "[role='dialog']"), (By.CSS_SELECTOR, "dialog")]
                )
            )
        except TimeoutException:
            return

        confirm = self._find_action({"삭제", "확인", "delete", "confirm"}, root=dialog)
        if confirm:
            self._click_dom(confirm)
            WebDriverWait(self.driver, 10).until(
                lambda _: not self.first_visible(
                    [(By.CSS_SELECTOR, "[role='dialog']"), (By.CSS_SELECTOR, "dialog")]
                )
            )

    def _click_dom(self, element):
        """일반 클릭이 가려지는 경우를 피하기 위해 DOM에서 직접 클릭합니다."""
        self.driver.execute_script(
            """
            const element = arguments[0];
            element.scrollIntoView({block: 'center'});
            element.click();
            """,
            element,
        )

    def history_entries(self):
        """현재 화면의 히스토리를 제목과 고유 대화 링크 단위로 수집합니다."""
        history_list = self.first_visible(self.HISTORY_LISTS)
        if not history_list:
            return []

        # Virtuoso 목록의 직계 자식 하나가 실제 히스토리 한 건입니다. 동일 제목의
        # 대화도 href가 다르므로 링크를 고유 식별자로 함께 보관합니다.
        entries = self.driver.execute_script(
            """
            const list = arguments[0];
            const visible = element => {
                const rect = element.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            return Array.from(list.children)
                .filter(visible)
                .map(row => {
                    const anchors = Array.from(row.querySelectorAll('a[href]'));
                    const anchor = anchors.find(element =>
                        visible(element) &&
                        (element.innerText || '').trim()
                    );
                    const titleElement = anchor || Array.from(
                        row.querySelectorAll("[role='button'], li")
                    ).find(element =>
                        visible(element) &&
                        !element.closest('.menu-button') &&
                        (element.innerText || '').trim()
                    );
                    return {
                        title: ((titleElement || row).innerText || '').trim(),
                        href: anchor ? anchor.href : null,
                    };
                })
                .filter(entry => entry.title);
            """,
            history_list,
        )
        return [
            {
                "title": self.normalize(entry["title"]),
                "href": entry.get("href"),
            }
            for entry in entries
            if self.normalize(entry["title"])
        ]

    def history_titles(self):
        """현재 화면에 표시된 모든 히스토리 제목을 행 순서대로 수집합니다."""
        return [entry["title"] for entry in self.history_entries()]

    def history_entry(self, href):
        """고유 대화 링크와 일치하는 현재 히스토리 요소를 찾습니다."""
        if not href:
            return False
        return self.driver.execute_script(
            """
            const list = document.querySelector('[data-testid="virtuoso-item-list"]');
            if (!list) return null;
            return Array.from(list.querySelectorAll('a[href]')).find(
                element => element.href === arguments[0]
            ) || null;
            """,
            href,
        )

    def _history_target_count(self, key, href=None):
        """링크가 있으면 특정 대화를, 없으면 제목이 일치하는 대화 수를 반환합니다."""
        if href:
            return 1 if self.history_entry(href) else 0
        return self.history_item_count(key)

    def history_item_count(self, key):
        """현재 사이드바에서 key를 포함하는 실제 히스토리 행의 개수를 셉니다."""
        return sum(
            1
            for entry in self.history_entries()
            if key in entry["title"]
        )

