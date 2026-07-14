import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage

TEST_TEXT = "가나다 ABC123 456테스트"


def main():

    driver = get_driver()

    try:
        # 로그인
        login = LoginPage(driver)
        login.login()

        # 채팅 페이지
        chat = ChatPage(driver)

        # 입력
        chat.input_question(TEST_TEXT)

        # 검증
        actual = chat.get_input_value()

        assert actual == TEST_TEXT, f"\n[FAIL]\n기대값 : {TEST_TEXT}\n실제값 : {actual}"

        print("[PASS] 한글/영문/숫자 혼합 입력 성공")

        # 질문 전송
        chat.send_by_enter()

        input("\n응답을 확인 후 Enter를 누르세요.")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
