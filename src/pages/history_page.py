from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from src.config.config import (
    AUTOMATION_HISTORY_PREFIXES,
    BASE_URL,
    CHAT_READY_TIMEOUT,
    DEFAULT_TIMEOUT,
)
from src.core.login import login_if_needed, wait_for_login_or_page
from src.pages.base_page import BasePage


class HistoryPage(BasePage):
    HISTORY_LISTS = [
        (By.CSS_SELECTOR, "[data-testid='virtuoso-item-list']"),
    ]
    CHAT_AREAS = [
        (By.CSS_SELECTOR, "main"),
    ]
    CHAT_INPUTS = [
        (By.CSS_SELECTOR, "textarea[placeholder*='硫붿떆吏']"),
        (By.CSS_SELECTOR, "textarea[placeholder*='吏덈Ц']"),
        (By.CSS_SELECTOR, "textarea"),
        (By.CSS_SELECTOR, "[contenteditable='true'][role='textbox']"),
        (By.CSS_SELECTOR, "[contenteditable='true']"),
    ]
    SEND_BUTTONS = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "button[aria-label*='?꾩넚']"),
        (By.CSS_SELECTOR, "button[aria-label*='蹂대궡湲?]"),
        (By.CSS_SELECTOR, "button[title*='?꾩넚']"),
        (By.CSS_SELECTOR, "button[title*='蹂대궡湲?]"),
    ]

    def open(self):
        self.driver.get(BASE_URL)
        wait_for_login_or_page(
            self.driver,
            lambda: bool(self.first_visible(self.CHAT_INPUTS))
        )
        login_if_needed(self.driver)
        self.wait_until_ready()
        return self

    def wait_until_ready(self):
        return self.wait_visible(self.CHAT_INPUTS, CHAT_READY_TIMEOUT)

    def send_message(self, message):
        chat_input = self.wait_until_ready()
        chat_input.click()
        if chat_input.get_attribute("contenteditable") == "true":
            chat_input.send_keys(Keys.CONTROL, "a")
            chat_input.send_keys(Keys.BACKSPACE)
        else:
            chat_input.clear()
        chat_input.send_keys(message)
        chat_input.send_keys(Keys.ENTER)

        try:
            self.wait_for_message(message, timeout=5)
        except TimeoutException:
            self.click(self.wait_visible(self.SEND_BUTTONS, timeout=10))
            self.wait_for_message(message)

    def history_item(self, key):
        history_list = self.first_visible(self.HISTORY_LISTS)
        if not history_list:
            return False

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
        return WebDriverWait(self.driver, timeout).until(
            lambda _: self.history_item(key)
        )

    def open_history(self, key):
        self.click(self.wait_for_history(key))

    def message_is_visible(self, message):
        chat_area = self.first_visible(self.CHAT_AREAS)
        if not chat_area:
            return False

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
        return WebDriverWait(self.driver, timeout).until(
            lambda _: self.message_is_visible(message)
        )

    def refresh(self):
        self.driver.refresh()
        self.wait_until_ready()

    def delete_history(self, key):
        item = self.wait_for_history(key)
        self._open_history_menu(item, key)
        delete_action = self._wait_action({"삭제", "delete"})
        self._click_dom(delete_action)
        self._confirm_delete_if_needed()

        # Reloading the deleted conversation URL can restore the stale active item.
        # Return to the service root before reading the sidebar again.
        self.driver.get(BASE_URL)
        self.wait_until_ready()
        WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            lambda _: not self.history_item(key)
        )

    def _open_history_menu(self, item, key):
        self._reveal_history_actions(item)
        menu_button = WebDriverWait(self.driver, 10).until(
            lambda _: self._history_menu_button(item, key)
        )
        self._click_dom(menu_button)
        WebDriverWait(self.driver, 10).until(
            lambda _: self._find_action({"삭제", "delete"})
        )

    def _reveal_history_actions(self, item):
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

    def _history_menu_button(self, item, key):
        return self.driver.execute_script(
            """
            const item = arguments[0];
            const key = arguments[1];
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
                if (!row || !row.innerText || !row.innerText.includes(key)) return null;
                dispatchHover(row);
                const menus = collect(row);
                return menus.length ? clickable(menus[0]) : null;
            };

            let row = item;
            for (let depth = 0; depth < 12 && row; depth++, row = row.parentElement) {
                const menu = exactRowMenu(row);
                if (menu) return menu;
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
                for (const candidate of document.querySelectorAll(selector)) {
                    const menu = exactRowMenu(candidate);
                    if (menu) return menu;
                }
            }

            return null;
            """,
            item,
            key,
        )

    def _wait_action(self, labels, timeout=10, root=None):
        return WebDriverWait(self.driver, timeout).until(
            lambda _: self._find_action(labels, root=root)
        )

    def _find_action(self, labels, root=None):
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
        self.driver.execute_script(
            """
            const element = arguments[0];
            element.scrollIntoView({block: 'center'});
            element.click();
            """,
            element,
        )

    def automation_history_titles(self):
        history_list = self.first_visible(self.HISTORY_LISTS)
        if not history_list:
            return []

        titles = []
        seen = set()
        for element in history_list.find_elements(
            By.CSS_SELECTOR,
            "a, button, [role='button'], li",
        ):
            try:
                if not element.is_displayed():
                    continue
                title = self.normalize(element.text)
                if title.startswith(AUTOMATION_HISTORY_PREFIXES) and title not in seen:
                    seen.add(title)
                    titles.append(title)
            except StaleElementReferenceException:
                continue
        return titles

