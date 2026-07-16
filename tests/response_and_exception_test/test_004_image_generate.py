import sys
import time
from pathlib import Path
from selenium.webdriver.common.by import By

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage

##-----입력창 "+" 버튼 이미지생성/웹 검색 활용 질문시 응답영역 AI 답변 테스트-----##

TEST_DATA = {
    "이미지 생성": {
        "question": "잔디밭 위에 앉아 카메라를 바라보며 꼬리를 흔드는 귀여운 작은 강아지 일러스트를 생성해줘.",
        "type": "image",
    },
    "웹 검색": {
        "question": "강아지의 종류를 정리하는 내용을 찾아줘",  # 관련 내용을 가져오는지 확인
        "type": "web",
    },
}


def main():
    driver = get_driver()
    test_results = {}

    try:
        login = LoginPage(driver)
        login.login()
        chat = ChatPage(driver)
        chat.get_input_box()

        print("\n" + "=" * 60)
        print("   [TC_004] '+ 버튼' 기능 검증 (이미지 생성/웹 검색)   ")
        print("=" * 60 + "\n")

        for feature, data in TEST_DATA.items():
            print(f"▶ [{feature}] 기능 테스트 시작")
            case_status = "[FAIL] ❌"

            try:
                # 1) + 버튼 클릭
                chat.click_plus_button()

                # 2) 메뉴 클릭 (이미지 생성 vs 웹 검색)
                if data["type"] == "image":
                    chat.click_image_generate_menu()
                    chat.wait_image_mode()
                else:
                    # [필요] chat_page.py에 웹 검색 메뉴 클릭 메서드 추가 필요
                    chat.click_web_search_menu()

                time.sleep(1)

                # 3) 질문 입력 및 전송
                chat.input_question(data["question"])
                chat.click_send_button()

                # 4) 결과 검증
                if data["type"] == "image":
                    chat.wait_image_created()
                    if chat.is_image_created():
                        case_status = "[PASS] ✅"
                else:
                    chat.wait_response_complete()
                    answer = chat.get_last_response()
                    if answer and len(answer) > 10:  # 응답 내용이 존재하는지 확인
                        print(f"  [✓] 검색 결과 확인: {answer[:50]}...")
                        case_status = "[PASS] ✅"

            except Exception as e:
                print(f"  [✗] 실패 원인: {e}")

            finally:
                test_results[feature] = case_status
                print(f"▷ [{feature}] 결과: {case_status}")
                print("-" * 60)
                time.sleep(2)

        # 리포트 출력
        print("\n[최종 테스트 결과 요약]")
        for name, status in test_results.items():
            print(f" - {name} : {status}")

    finally:
        print("\n테스트가 모두 종료되었습니다. 3초 후 브라우저를 닫습니다...")
        time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    main()
