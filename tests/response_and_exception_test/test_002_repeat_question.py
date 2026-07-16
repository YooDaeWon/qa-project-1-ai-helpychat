import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage


##-------10회 이상 동일 질문 반복 전송, AI동일 답변 응답 TEST-----##

QUESTION = "30 × 90 = 무엇인가?"
REPEAT_COUNT = 10


def validate_answer(answer: str):
    if answer == "":
        return False

    error_keywords = ["오류", "죄송", "실패", "생성할 수 없습니다"]

    for keyword in error_keywords:
        if keyword in answer:
            return False

    if "2700" in answer:
        return True

    if "2,700" in answer:
        return True

    return False


def main():
    driver = get_driver()

    try:
        print("=" * 60)
        print("TC002 동일 질문 10회 반복 테스트")
        print("=" * 60)

        login = LoginPage(driver)
        login.login()

        chat = ChatPage(driver)

        success = 0

        for i in range(REPEAT_COUNT):
            # 질문 출력
            print(f"\n[{i + 1}/{REPEAT_COUNT}]")
            print(f"질문 : {QUESTION}")

            # 질문 입력
            chat.input_question(QUESTION)

            # 보내기 버튼 클릭
            chat.click_send_button()

            # AI 응답 완료 대기
            chat.wait_response_complete()

            # 마지막 응답 가져오기
            answer = chat.get_last_response()

            # 응답 출력
            print(f"응답 : {answer}")

            # 검증
            assert validate_answer(answer), f"{i + 1}번째 응답 검증 실패"

            # PASS 출력
            print("검증 결과 : PASS")

            success += 1

            time.sleep(1)

        assert success == REPEAT_COUNT

        print("\n")
        print("=" * 60)
        print("TC002 PASS")
        print("=" * 60)

    finally:
        # ===== [추가된 부분] 브라우저 종료 전 3초 대기 =====
        print("\n테스트가 모두 종료되었습니다. 3초 후 브라우저를 닫습니다...")
        time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    main()
