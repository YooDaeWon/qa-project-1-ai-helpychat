import sys
import time
from pathlib import Path

# 프로젝트 루트 경로 설정
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage


# =====================================================
# TC007
# 응답출력 - 입력창 "AI헬피 추천 질문" 영역 기능 검증
# =====================================================
def main():
    driver = get_driver()
    try:
        print("=" * 70)
        print("TC007 응답출력 - AI헬피 추천 질문 클릭 검증")
        print("=" * 70)
        # -------------------------------------------------
        # 로그인
        # -------------------------------------------------
        login = LoginPage(driver)
        login.login()
        chat = ChatPage(driver)

        # 입력창이 나타날 때까지 대기
        chat.get_input_box()

        # -------------------------------------------------
        # Step 1. 더미 질문 1개 전송하여 응답 영역 생성
        # -------------------------------------------------
        print("\n[Step 1] 첫 번째 더미 질문 전송 (응답 영역 생성용)")
        dummy_question = "안녕? 반가워!"
        chat.input_question(dummy_question)
        chat.click_send_button()

        print("▷ 첫 번째 질문 응답 대기 중...")
        chat.wait_response_complete()
        print("▷ 첫 번째 응답 완료")
        # -------------------------------------------------
        # Step 2. 추천 질문 대기 및 랜덤 클릭
        # -------------------------------------------------
        print("\n[Step 2] 추천 질문 탐색 및 랜덤 클릭")

        # AI헬피 추천 질문 텍스트가 뜰 때까지 대기
        chat.wait_for_recommend_questions()

        # ==========================================
        # 추가된 부분: 추천 질문 노출 후 2초 대기
        print("▷ 'AI헬피 추천 질문' 노출 완료. 2초 대기 후 클릭 진행...")
        time.sleep(3)
        # ==========================================

        # 추천 질문 중 랜덤으로 1개 클릭하고, 해당 텍스트를 반환받음
        clicked_question = chat.click_random_recommend_question()
        print(f"▶ 선택된 추천 질문: '{clicked_question}'")

        time.sleep(1.5)  # 클릭 후 화면이 반응할 시간을 잠시 줌
        # -------------------------------------------------
        # Step 3. 클릭 후 동작 검증 및 응답 대기
        # -------------------------------------------------
        print("\n[Step 3] 추천 질문 출력 및 동작 검증")

        # 버튼을 눌렀을 때 텍스트가 입력창에만 들어가는지, 아니면 즉시 전송되는지 판별
        current_input_value = chat.get_input_value()

        # 입력창에 선택한 텍스트가 들어가 있다면 -> 자동으로 전송된 것이 아니므로 수동으로 보내기 클릭
        if clicked_question in current_input_value:
            print("▷ 동작 방식: 추천 질문이 입력창에 채워졌습니다. (수동 전송 필요)")
            chat.click_send_button()
        else:
            print("▷ 동작 방식: 추천 질문이 즉시 전송되었습니다. (자동 전송)")
        # 추천 질문에 대한 답변 생성 대기
        print("▷ 추천 질문에 대한 AI 응답 대기 중...")
        chat.wait_response_complete()

        # -------------------------------------------------
        # 결과 확인
        # -------------------------------------------------
        final_response = chat.get_last_response()

        if final_response:
            print(f"\n최종 응답 미리보기 : {final_response[:50]}...")
            print(
                "검증 결과 : PASS (추천 질문이 정상적으로 전송되고 응답을 받았습니다.)"
            )

            print("\n" + "=" * 70)
            print("TC007 PASS")
            print("=" * 70)
        else:
            raise Exception("응답이 정상적으로 출력되지 않았습니다.")
    except Exception as e:
        print("\n" + "=" * 70)
        print("TC007 FAIL")
        print("=" * 70)
        print(e)
    finally:
        input("\n종료하려면 Enter를 누르세요...")
        driver.quit()


if __name__ == "__main__":
    main()
