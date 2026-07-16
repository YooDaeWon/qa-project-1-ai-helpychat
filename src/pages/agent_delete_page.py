from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.pages.agent_list_page import AgentListPage
from src.pages.base_page import BasePage


class AgentDeletePage(BasePage):
    """에이전트 카드의 삭제 메뉴와 삭제 확인창을 담당합니다."""

    def click_more_menu_with_javascript(self, agent_card: WebElement) -> None:
        click_result = self.driver.execute_script(
            """
            const card = arguments[0];
            if (!card) {
                return {success: false, reason: '에이전트 카드가 없습니다.'};
            }

            const eventNames = [
                'pointerover', 'pointerenter', 'mouseover', 'mouseenter', 'mousemove'
            ];
            for (const eventName of eventNames) {
                card.dispatchEvent(new MouseEvent(eventName, {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
            }

            const menuButton = card.querySelector("button[class*='menu-trigger']");
            if (!menuButton) {
                return {success: false, reason: '점 3개 메뉴 버튼을 찾지 못했습니다.'};
            }

            menuButton.style.display = 'flex';
            menuButton.style.opacity = '1';
            menuButton.style.visibility = 'visible';
            menuButton.style.pointerEvents = 'auto';

            menuButton.dispatchEvent(new PointerEvent('pointerdown', {
                bubbles: true,
                cancelable: true
            }));
            menuButton.dispatchEvent(new MouseEvent('mousedown', {
                bubbles: true,
                cancelable: true,
                view: window
            }));
            menuButton.dispatchEvent(new MouseEvent('mouseup', {
                bubbles: true,
                cancelable: true,
                view: window
            }));
            menuButton.click();
            return {success: true, reason: ''};
            """,
            agent_card,
        )

        if not click_result or not click_result.get("success"):
            reason = (
                click_result.get("reason")
                if click_result
                else "JavaScript 클릭 결과를 확인하지 못했습니다."
            )
            raise RuntimeError(reason)
        print("점 3개 메뉴 버튼 JavaScript 클릭 완료")

    def click_remove_agent_menu(self) -> None:
        remove_menu_item = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//*[@role='menuitem' and normalize-space()='에이전트 제거']",
                )
            )
        )
        self.safe_click(remove_menu_item)
        print("에이전트 제거 메뉴 클릭 완료")

    def wait_delete_dialog(self) -> WebElement:
        dialog = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//*[@role='dialog' and .//*[normalize-space()='에이전트를 제거할까요?']]",
                )
            )
        )
        print("'에이전트를 제거할까요?' 팝업 확인 완료")
        return dialog

    def click_confirm_delete(self, dialog: WebElement) -> None:
        try:
            confirm_button = WebDriverWait(
                self.driver,
                self.timeout,
            ).until(
                lambda _: dialog.find_element(
                    By.XPATH,
                    ".//button[normalize-space()='제거하기']",
                )
            )
        except TimeoutException as error:
            raise RuntimeError("제거하기 버튼을 찾지 못했습니다.") from error

        self.safe_click(confirm_button)
        print("제거하기 버튼 클릭 완료")

    def verify_agent_removed(self, relative_href: str) -> None:
        xpath = f"//a[@href='{relative_href}']"
        try:
            self.wait.until(
                lambda _: len(self.driver.find_elements(By.XPATH, xpath)) == 0
            )
        except TimeoutException as error:
            raise RuntimeError("삭제한 에이전트가 목록에서 사라지지 않았습니다.") from error
        print("삭제한 에이전트가 목록에서 사라진 것을 확인했습니다.")

    def verify_delete_success_toast(self) -> None:
        try:
            self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//*[normalize-space()='에이전트가 제거되었습니다.']",
                    )
                )
            )
        except TimeoutException as error:
            raise RuntimeError(
                "'에이전트가 제거되었습니다.' 알림을 확인하지 못했습니다."
            ) from error
        print("'에이전트가 제거되었습니다.' 알림 확인 완료")

    def delete_single_agent(
        self,
        list_page: AgentListPage,
        agent_info: dict[str, str],
    ) -> None:
        relative_href = agent_info["relative_href"]
        agent_link = list_page.locate_agent_link(relative_href)
        agent_card = list_page.find_agent_card(agent_link)

        self.click_more_menu_with_javascript(agent_card)
        self.click_remove_agent_menu()
        dialog = self.wait_delete_dialog()
        self.click_confirm_delete(dialog)
        self.verify_agent_removed(relative_href)
        self.verify_delete_success_toast()
