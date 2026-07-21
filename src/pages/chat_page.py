from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import random
from src.config.config import WAIT_TIME, AI_RESPONSE_TIMEOUT
import os
import time


class ChatPage:
    def __init__(self, driver):
        self.driver = driver

    # ======================================================
    # 공통
    # ======================================================
    def get_input_box(self):
        return WebDriverWait(self.driver, WAIT_TIME).until(
            EC.visibility_of_element_located((By.NAME, "input"))
        )

    def input_question(self, text):
        textbox = self.get_input_box()
        textbox.clear()
        has_non_bmp = any(ord(char) > 0xFFFF for char in text)
        if has_non_bmp:
            textbox.click()
            js_code = """
            var input = arguments[0];
            var text = arguments[1];
            input.focus();
            document.execCommand('insertText', false, text);
            """
            self.driver.execute_script(js_code, textbox, text)
        else:
            # [수정된 부분] \n 이 포함된 경우 Shift+Enter로 줄바꿈을 처리하도록 변경
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if line:
                    textbox.send_keys(line)
                # 마지막 줄이 아니면 Shift + Enter 입력
                if i < len(lines) - 1:
                    textbox.send_keys(Keys.SHIFT + Keys.ENTER)

    def get_input_value(self):
        return self.get_input_box().get_attribute("value")

    def get_input_length(self):
        textbox = self.get_input_box()
        return len(textbox.get_attribute("value"))

    # ======================================================
    # 질문 전송
    # ======================================================
    def send_by_enter(self):
        self.get_input_box().send_keys(Keys.ENTER)

    def click_send_button(self):
        button = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='보내기']"))
        )
        self.driver.execute_script("arguments[0].click();", button)

    # ======================================================
    # 일반 응답
    # ======================================================
    def wait_response_complete(self, timeout=AI_RESPONSE_TIMEOUT):
        before = len(
            self.driver.find_elements(By.CSS_SELECTOR, "div[data-status='complete']")
        )
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: (
                    len(d.find_elements(By.CSS_SELECTOR, "div[data-status='complete']"))
                    > before
                )
            )
        except TimeoutException:
            raise TimeoutException(
                f"AI 응답이 {timeout}초 내에 도착하지 않았습니다 (SLA 초과로 Fail 처리)."
            )

    def get_last_response(self):
        responses = self.driver.find_elements(
            By.CSS_SELECTOR, "div[data-status='complete']"
        )
        if not responses:
            return ""
        return responses[-1].text.strip()

    # ▶ [추가된 부분] 가장 마지막 응답의 <a> 태그 href 속성값들을 리스트로 반환하는 메서드
    def get_last_response_links(self):
        responses = self.driver.find_elements(
            By.CSS_SELECTOR, "div[data-status='complete']"
        )
        if not responses:
            return []

        # 마지막 응답 요소 가져오기
        last_response_element = responses[-1]

        # 마지막 응답 내부의 모든 <a> 태그 찾기
        a_tags = last_response_element.find_elements(By.TAG_NAME, "a")

        # href 속성이 존재하는 태그들의 URL만 리스트로 반환
        return [
            tag.get_attribute("href") for tag in a_tags if tag.get_attribute("href")
        ]

    # ======================================================
    # TC004 이미지 생성 / 파일 업로드
    # ======================================================
    def click_plus_button(self):
        print("① '+' 버튼 찾는 중...")
        try:
            plus_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "div.css-8eju4k.e1826rbt2 > button")
                )
            )
            self.driver.execute_script("arguments[0].click();", plus_button)
            print("② '+' 버튼 클릭 성공 (1차)")
            return
        except Exception:
            pass
        print("③ 백업 방식으로 '+' 버튼 탐색")
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            try:
                button.find_element(By.CSS_SELECTOR, "svg[data-testid='plusIcon']")
                self.driver.execute_script("arguments[0].click();", button)
                print("④ '+' 버튼 클릭 성공 (2차)")
                return
            except Exception:
                continue
        raise Exception("'+ 버튼을 찾을 수 없습니다.'")

    def click_image_generate_menu(self):
        image_menu = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='이미지 생성']/ancestor::li")
            )
        )
        self.driver.execute_script("arguments[0].click();", image_menu)

    def wait_image_mode(self):
        WebDriverWait(self.driver, WAIT_TIME).until(
            EC.visibility_of_element_located((By.XPATH, "//span[text()='이미지 생성']"))
        )

    def wait_image_created(self):
        WebDriverWait(self.driver, 180).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "img[alt='generated image']")
            )
        )

    def is_image_created(self):
        images = self.driver.find_elements(
            By.CSS_SELECTOR, "img[alt='generated image']"
        )
        return len(images) > 0

    def is_specific_image_created(self, file_name):
        images = self.driver.find_elements(By.CSS_SELECTOR, "img")
        return any(
            file_name in (img.get_attribute("src") or "")
            or file_name in (img.get_attribute("alt") or "")
            for img in images
        )

    def click_web_search_menu(self):
        web_search_menu = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='웹 검색']/ancestor::li")
            )
        )
        self.driver.execute_script("arguments[0].click();", web_search_menu)

    def click_file_upload_menu(self):
        menu = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(), '파일 업로드')]/ancestor::li")
            )
        )
        self.driver.execute_script("arguments[0].click();", menu)

    def upload_file(self, file_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        absolute_path = os.path.join(project_root, file_path)
        file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(absolute_path)

    # ======================================================
    # TC007 추천 질문 (최종 보완본)
    # ======================================================
    def wait_for_recommend_questions(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'AI헬피 추천 질문')]")
                )
            )
        except:
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "button.e15docq31, button.css-16f78m")
                )
            )

    def click_random_recommend_question(self):
        buttons = self.driver.find_elements(
            By.CSS_SELECTOR, "button.e15docq31, button.css-16f78m"
        )
        if not buttons:
            raise Exception("추천 질문 버튼을 찾을 수 없습니다.")
        visible_buttons = [b for b in buttons if b.is_displayed()]
        if not visible_buttons:
            raise Exception("화면에 보이는 버튼이 없습니다.")
        target_button = random.choice(visible_buttons)
        self.driver.execute_script(
            "arguments[0].style.border = '3px solid red'; "
            "arguments[0].scrollIntoView({block: 'center'});",
            target_button,
        )
        time.sleep(1.5)
        question_text = target_button.text.strip()
        self.driver.execute_script("arguments[0].click();", target_button)
        return question_text
