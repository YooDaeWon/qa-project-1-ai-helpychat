from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
<<<<<<< HEAD
from config.config import WAIT_TIME
=======
from src.config.config import WAIT_TIME
import os
import time
>>>>>>> 유대원


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

<<<<<<< HEAD
        # 1. 텍스트 내에 BMP 범위를 벗어나는 문자(이모지 등)가 있는지 사전 검사
        has_non_bmp = any(ord(char) > 0xFFFF for char in text)

        if has_non_bmp:
            # 2. 이모지가 포함된 경우: 브라우저 내장 텍스트 삽입 명령어(insertText) 사용
            textbox.click()  # 입력창에 포커스를 맞춤

=======
        has_non_bmp = any(ord(char) > 0xFFFF for char in text)

        if has_non_bmp:
            textbox.click()
>>>>>>> 유대원
            js_code = """
            var input = arguments[0];
            var text = arguments[1];
            input.focus();
<<<<<<< HEAD
            // 브라우저 자체 기능으로 텍스트를 '붙여넣기' 한 것과 같은 효과를 냄
            document.execCommand('insertText', false, text);
            """
            self.driver.execute_script(js_code, textbox, text)

        else:
            # 3. 일반 텍스트인 경우: 정상적으로 키보드 입력
=======
            document.execCommand('insertText', false, text);
            """
            self.driver.execute_script(js_code, textbox, text)
        else:
>>>>>>> 유대원
            textbox.send_keys(text)

    def get_input_value(self):
        return self.get_input_box().get_attribute("value")

    def get_input_length(self):
<<<<<<< HEAD
        """
        입력창의 실제 글자 수 반환
        """

        textbox = self.get_input_box()

=======
        textbox = self.get_input_box()
>>>>>>> 유대원
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
<<<<<<< HEAD

=======
>>>>>>> 유대원
        self.driver.execute_script("arguments[0].click();", button)

    # ======================================================
    # 일반 응답
    # ======================================================

    def wait_response_complete(self):
<<<<<<< HEAD

        before = len(
            self.driver.find_elements(By.CSS_SELECTOR, "div[data-status='complete']")
        )

=======
        before = len(
            self.driver.find_elements(By.CSS_SELECTOR, "div[data-status='complete']")
        )
>>>>>>> 유대원
        WebDriverWait(self.driver, 120).until(
            lambda d: (
                len(d.find_elements(By.CSS_SELECTOR, "div[data-status='complete']"))
                > before
            )
        )

    def get_last_response(self):
<<<<<<< HEAD

        responses = self.driver.find_elements(
            By.CSS_SELECTOR, "div[data-status='complete']"
        )

        if not responses:
            return ""

        return responses[-1].text.strip()

    # ======================================================
    # TC004 이미지 생성
    # ======================================================

    def click_plus_button(self):
        """
        '+' 버튼 클릭
        """

        print("① '+' 버튼 찾는 중...")

        # ---------- 1차 ----------
=======
        responses = self.driver.find_elements(
            By.CSS_SELECTOR, "div[data-status='complete']"
        )
        if not responses:
            return ""
        return responses[-1].text.strip()

    # ======================================================
    # TC004 이미지 생성 / 파일 업로드
    # ======================================================

    def click_plus_button(self):
        print("① '+' 버튼 찾는 중...")
>>>>>>> 유대원
        try:
            plus_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "div.css-8eju4k.e1826rbt2 > button")
                )
            )
<<<<<<< HEAD

            self.driver.execute_script("arguments[0].click();", plus_button)

            print("② '+' 버튼 클릭 성공 (1차)")

            return

        except Exception:
            pass

        # ---------- 2차 ----------
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

=======
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
>>>>>>> 유대원
        image_menu = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='이미지 생성']/ancestor::li")
            )
        )
<<<<<<< HEAD

        self.driver.execute_script("arguments[0].click();", image_menu)

    def wait_image_mode(self):

=======
        self.driver.execute_script("arguments[0].click();", image_menu)

    def wait_image_mode(self):
>>>>>>> 유대원
        WebDriverWait(self.driver, WAIT_TIME).until(
            EC.visibility_of_element_located((By.XPATH, "//span[text()='이미지 생성']"))
        )

    def wait_image_created(self):
<<<<<<< HEAD

=======
>>>>>>> 유대원
        WebDriverWait(self.driver, 180).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "img[alt='generated image']")
            )
        )

    def is_image_created(self):
<<<<<<< HEAD

        images = self.driver.find_elements(
            By.CSS_SELECTOR, "img[alt='generated image']"
        )

        return len(images) > 0

    # ======================================================
    # 추가: 웹 검색 기능
    # ======================================================

    def click_web_search_menu(self):
        """
        '+' 버튼 클릭 후 나타나는 '웹 검색' 메뉴를 클릭합니다.
        """
=======
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
>>>>>>> 유대원
        web_search_menu = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='웹 검색']/ancestor::li")
            )
        )
        self.driver.execute_script("arguments[0].click();", web_search_menu)

<<<<<<< HEAD
    # ======================================================
    # TC007 추천 질문
    # ======================================================
    def wait_for_recommend_questions(self):
        """
        'AI헬피 추천 질문' 영역이 화면에 나타날 때까지 대기합니다.
        """
        WebDriverWait(self.driver, WAIT_TIME).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//p[text()='AI헬피 추천 질문']")
            )
        )

    def click_random_recommend_question(self):
        """
        추천 질문 3개 중 랜덤으로 1개를 클릭하고, 클릭한 질문의 텍스트를 반환합니다.
        """
        # 'AI헬피 추천 질문' 텍스트를 가진 요소의 형제(아래쪽) 영역에 있는 모든 button 찾기
        buttons = self.driver.find_elements(
            By.XPATH,
            "//p[text()='AI헬피 추천 질문']/parent::div/following-sibling::div//button",
=======
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
        """
        메인/응답 영역 상관없이 버튼이 나타날 때까지 대기합니다.
        """
        # 1. 텍스트가 있는 경우 (응답 영역용)
        # 2. 텍스트가 없는 경우도 고려하여, 버튼 클래스명(e15docq31 또는 css-16f78m) 기반 대기
        try:
            # 텍스트 기준 탐색 (응답 영역)
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'AI헬피 추천 질문')]")
                )
            )
        except:
            # 텍스트가 없으면 버튼 클래스로 찾기 (메인 영역)
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "button.e15docq31, button.css-16f78m")
                )
            )

    def click_random_recommend_question(self):
        """
        메인(e15docq31)과 응답 영역(css-16f78m)의 모든 버튼을 찾아 클릭합니다.
        """
        # 두 영역의 버튼 클래스를 모두 포함하는 선택자
        buttons = self.driver.find_elements(
            By.CSS_SELECTOR, "button.e15docq31, button.css-16f78m"
>>>>>>> 유대원
        )

        if not buttons:
            raise Exception("추천 질문 버튼을 찾을 수 없습니다.")

<<<<<<< HEAD
        # 랜덤하게 하나 선택
        target_button = random.choice(buttons)

        # 버튼 안의 텍스트 추출 (무엇을 할 수 있나요? 등)
        question_text = target_button.text.strip()

        # 클릭 수행
=======
        # 현재 보이는 버튼들만 필터링 (렌더링 된 것만 선택)
        visible_buttons = [b for b in buttons if b.is_displayed()]
        if not visible_buttons:
            raise Exception("화면에 보이는 버튼이 없습니다.")

        target_button = random.choice(visible_buttons)

        # 포커스 및 강조
        self.driver.execute_script(
            "arguments[0].style.border = '3px solid red'; "
            "arguments[0].scrollIntoView({block: 'center'});",
            target_button,
        )
        time.sleep(1.5)

        question_text = target_button.text.strip()
>>>>>>> 유대원
        self.driver.execute_script("arguments[0].click();", target_button)

        return question_text
