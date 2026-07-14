from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
from config.config import WAIT_TIME


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
        textbox.send_keys(text)

    def get_input_value(self):
        return self.get_input_box().get_attribute("value")

    def get_input_length(self):
        """
        입력창의 실제 글자 수 반환
        """

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

    def wait_response_complete(self):

        before = len(
            self.driver.find_elements(By.CSS_SELECTOR, "div[data-status='complete']")
        )

        WebDriverWait(self.driver, 120).until(
            lambda d: (
                len(d.find_elements(By.CSS_SELECTOR, "div[data-status='complete']"))
                > before
            )
        )

    def get_last_response(self):

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
        )

        if not buttons:
            raise Exception("추천 질문 버튼을 찾을 수 없습니다.")

        # 랜덤하게 하나 선택
        target_button = random.choice(buttons)

        # 버튼 안의 텍스트 추출 (무엇을 할 수 있나요? 등)
        question_text = target_button.text.strip()

        # 클릭 수행
        self.driver.execute_script("arguments[0].click();", target_button)

        return question_text
