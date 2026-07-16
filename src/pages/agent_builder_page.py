from __future__ import annotations

import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from src.pages.base_page import BasePage
from src.utils.agent_data import AgentData


class AgentBuilderPage(BasePage):
    """에이전트 만들기 설정 화면을 담당하는 Page Object입니다."""

    def verify_builder_tabs_displayed(self) -> None:
        """대화로 만들기 탭과 설정 탭 표시를 확인합니다."""
        end_time = time.time() + 10
        result = {"chatVisible": False, "formVisible": False}

        while time.time() < end_time:
            result = self.driver.execute_script(
                """
                const chatButton =
                    document.querySelector("button[value='chat']") ||
                    Array.from(document.querySelectorAll('button')).find((button) => {
                        const text = (button.innerText || button.textContent || '').trim();
                        return text.includes('대화로 만들기') || text.includes('대화');
                    });

                const formButton =
                    document.querySelector("button[value='form']") ||
                    Array.from(document.querySelectorAll('button')).find((button) => {
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

        print(f"[{'PASS' if result['chatVisible'] else 'FAIL'}] 대화로 만들기 탭 표시 확인")
        print(f"[{'PASS' if result['formVisible'] else 'FAIL'}] 설정 탭 표시 확인")

        if not result["chatVisible"]:
            raise AssertionError("대화로 만들기 탭이 표시되지 않습니다.")
        if not result["formVisible"]:
            raise AssertionError("설정 탭이 표시되지 않습니다.")

    def click_builder_tab(self, value: str, text: str) -> None:
        """value='chat' 또는 value='form'인 상단 탭을 클릭합니다."""
        element = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//button[@value='{value}']"
                    f" | //button[contains(normalize-space(), '{text}')]",
                )
            )
        )
        self.safe_click(element)
        time.sleep(0.7)
        print(f"{text} 탭 클릭 완료")

    def open_settings_tab(self) -> None:
        self.click_builder_tab("form", "설정")

    def _find_by_placeholder(self, placeholder_text: str):
        return self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"//input[contains(@placeholder, '{placeholder_text}')]"
                    f" | //textarea[contains(@placeholder, '{placeholder_text}')]",
                )
            )
        )

    def _find_by_name(self, name_value: str):
        return self.wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    f"input[name='{name_value}'], textarea[name='{name_value}']",
                )
            )
        )

    def _find_by_name_prefix(self, name_prefix: str):
        return self.wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    f"input[name^='{name_prefix}'], textarea[name^='{name_prefix}']",
                )
            )
        )

    def _set_react_value(self, element, value: str) -> None:
        """React/MUI 입력창에 native setter와 이벤트를 사용해 값을 반영합니다."""
        self.driver.execute_script(
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
            raise AssertionError(f"입력값 반영 실패. 현재값: {current_value}")

    @staticmethod
    def _print_check(check_name: str, result: bool) -> None:
        print(f"[{'PASS' if result else 'FAIL'}] {check_name}")

    def verify_preview_area_displayed(self) -> None:
        result = self.driver.execute_script(
            """
            const bodyText = document.body ? document.body.innerText : '';
            if (bodyText.includes('미리보기')) return true;
            if (bodyText.includes('메시지를 입력해 주세요')) return true;

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
        self._print_check("미리보기 영역 표시 확인", result)
        if not result:
            raise AssertionError("미리보기 영역을 확인하지 못했습니다.")

    def verify_file_upload_button_displayed(self) -> None:
        result = self.driver.execute_script(
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
        self._print_check("파일 업로드 버튼 표시 확인", result)
        if not result:
            raise AssertionError("파일 업로드 버튼 또는 파일 input을 확인하지 못했습니다.")

    def verify_feature_checkbox_displayed(self) -> None:
        result = self.driver.execute_script(
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
        self._print_check("기능 체크박스 표시 확인", result)
        if not result:
            raise AssertionError("기능 체크박스 또는 기능 항목을 확인하지 못했습니다.")

    def try_select_feature_checkbox(self) -> None:
        result = self.driver.execute_script(
            """
            function isVisible(el) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return (
                    rect.width > 0 && rect.height > 0 &&
                    style.display !== 'none' && style.visibility !== 'hidden'
                );
            }

            const checkboxes = Array.from(document.querySelectorAll("input[type='checkbox']"))
                .filter((el) => isVisible(el) || el.closest('label'));

            if (checkboxes.length > 0) {
                const target = checkboxes[0];
                if (!target.checked) target.click();
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
        self._print_check("기능 체크박스 선택 확인", result)
        if not result:
            raise AssertionError("기능 체크박스 선택에 실패했습니다.")

    def verify_public_scope_options_displayed(self) -> None:
        result = self.driver.execute_script(
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
        self._print_check("공개 범위 옵션 표시 확인", result)
        if not result:
            raise AssertionError("공개 범위 옵션을 확인하지 못했습니다.")

    def is_create_button_disabled(self) -> bool | None:
        return self.driver.execute_script(
            """
            const buttons = Array.from(document.querySelectorAll('button'));
            const target = buttons.find((button) => {
                const text = (button.innerText || button.textContent || '').trim();
                return text.includes('만들기');
            });
            if (!target) return null;

            const className = String(target.className || '');
            return (
                target.disabled ||
                target.getAttribute('aria-disabled') === 'true' ||
                className.includes('Mui-disabled')
            );
            """
        )

    def verify_create_button_disabled_before_required_input(self) -> None:
        result = self.is_create_button_disabled() is True
        self._print_check("필수값 입력 전 만들기 버튼 비활성 상태 확인", result)
        if not result:
            raise AssertionError("필수값 입력 전 만들기 버튼이 비활성 상태가 아닙니다.")

    def try_select_category_option(self) -> bool:
        """기존 코드와 동일하게 DOM이 확인되는 경우에만 카테고리 선택을 시도합니다."""
        result = self.driver.execute_script(
            """
            function isVisible(el) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return (
                    rect.width > 0 && rect.height > 0 &&
                    style.display !== 'none' && style.visibility !== 'hidden'
                );
            }

            const openKeywords = ['카테고리', '카테고리 선택', '선택'];
            const opener = Array.from(document.querySelectorAll('button, div, input'))
                .find((el) => {
                    const text = (
                        el.innerText || el.textContent ||
                        el.getAttribute('placeholder') || ''
                    ).trim();
                    return isVisible(el) && openKeywords.some((keyword) => text.includes(keyword));
                });

            if (!opener) return 'not-found';
            opener.scrollIntoView({ block: 'center' });
            opener.click();
            return 'clicked';
            """
        )

        if result != "clicked":
            print("[SKIP] 카테고리 선택 시도 - 정확한 카테고리 DOM 구조 확인 필요")
            return False

        time.sleep(0.5)
        selected = self.driver.execute_script(
            """
            function isVisible(el) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return (
                    rect.width > 0 && rect.height > 0 &&
                    style.display !== 'none' && style.visibility !== 'hidden'
                );
            }

            const optionKeywords = ['기타', '일반', '업무', '학습'];
            const option = Array.from(document.querySelectorAll('li, button, div, span'))
                .find((el) => {
                    const text = (el.innerText || el.textContent || '').trim();
                    return isVisible(el) && optionKeywords.some(
                        (keyword) => text === keyword || text.includes(keyword)
                    );
                });

            if (!option) return false;
            option.scrollIntoView({ block: 'center' });
            option.click();
            return true;
            """
        )
        self._print_check("카테고리 선택 시도", selected)
        return bool(selected)

    def run_pre_input_checks(self) -> None:
        self.verify_preview_area_displayed()
        self.verify_file_upload_button_displayed()
        self.verify_feature_checkbox_displayed()
        self.verify_public_scope_options_displayed()
        self.verify_create_button_disabled_before_required_input()

        try:
            self.try_select_category_option()
        except Exception as error:
            print(f"[SKIP] 카테고리 선택 시도 중 예외 발생: {error}")

        self.try_select_feature_checkbox()

    def input_name(self, agent_name: str) -> None:
        self._set_react_value(self._find_by_placeholder("이름"), agent_name)
        print(f"이름 입력 완료: {agent_name}")

    def input_short_description(self, short_description: str) -> None:
        self._set_react_value(
            self._find_by_placeholder("짧은 설명"),
            short_description,
        )
        print(f"한줄 소개 입력 완료: {short_description}")

    def input_rule(self, rule_text: str) -> None:
        self._set_react_value(self._find_by_name("systemPrompt"), rule_text)
        print("규칙 입력 완료")

    def input_start_conversation(self, start_conversation: str) -> None:
        self._set_react_value(
            self._find_by_name_prefix("conversationStarters"),
            start_conversation,
        )
        print("시작 대화 입력 완료")

    def fill_agent_form(self, data: AgentData) -> None:
        self.input_name(data.name)
        self.input_short_description(data.short_description)
        self.input_rule(data.rule_text)
        self.input_start_conversation(data.start_conversation)

    def check_private_scope(self) -> None:
        checked = self.driver.execute_script(
            """
            const privateRadio = document.querySelector("input[type='radio'][value='private']");
            if (!privateRadio) return 'not-found';
            if (privateRadio.checked) return 'checked';
            privateRadio.click();
            return privateRadio.checked ? 'checked-after-click' : 'not-checked';
            """
        )
        if checked in ["checked", "checked-after-click"]:
            print("공개 범위 나만 보기 확인 완료")
        else:
            raise AssertionError(f"공개 범위 나만 보기 확인 실패 또는 미존재: {checked}")

    def get_create_button_info(self) -> list[dict]:
        return self.driver.execute_script(
            """
            const buttons = Array.from(document.querySelectorAll('button'));
            return buttons
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
            """
        )

    def is_saved(self) -> bool:
        return bool(
            self.driver.execute_script(
                "const text = document.body ? document.body.innerText : ''; return text.includes('저장됨');"
            )
        )

    def is_create_button_enabled(self) -> bool:
        return bool(
            self.driver.execute_script(
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
        )

    def wait_until_ready_to_create(self, timeout: int = 20) -> None:
        print("저장됨 및 만들기 버튼 활성화 확인 중...")
        end_time = time.time() + timeout
        last_button_info = None

        while time.time() < end_time:
            if self.is_saved() and self.is_create_button_enabled():
                print("저장됨 상태 확인 완료")
                print("만들기 버튼 활성화 확인 완료")
                return
            last_button_info = self.get_create_button_info()
            time.sleep(0.3)

        print("만들기 버튼 최종 상태:")
        print(last_button_info)
        raise TimeoutException("저장됨 또는 만들기 버튼 활성화 상태를 확인하지 못했습니다.")

    def click_create_button(self) -> None:
        print("만들기 버튼 클릭 시도 중...")
        clicked = self.driver.execute_script(
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

            if (!target) return false;
            target.scrollIntoView({ block: 'center' });
            target.click();
            return true;
            """
        )
        if not clicked:
            print("만들기 버튼 상태:")
            print(self.get_create_button_info())
            raise AssertionError("활성화된 만들기 버튼을 클릭하지 못했습니다.")
        print("만들기 버튼 클릭 완료")

    def wait_for_created_agent(self, agent_name: str) -> None:
        self.wait.until(lambda _: agent_name in self.body_text())
        print(f"에이전트 생성 직후 검증 성공: {agent_name}")
