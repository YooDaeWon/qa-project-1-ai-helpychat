import pytest
import time
from src.pages.chat_page import ChatPage


def test_recommend_questions(setup_and_login):
    """
    [TC_007] 'AI헬피 추천 질문' 기능 검증 (메인 화면 & 응답 영역)
    """
    driver = setup_and_login
    chat = ChatPage(driver)

    print("\n" + "=" * 70)
    print(" [TC_007] AI헬피 추천 질문 기능 검증 시작 ")
    print("=" * 70)

    # 1차 검증: 로그인 후 메인 화면
    print("\n▶ [1차 검증] 메인 화면 추천 질문 선택")
    run_recommendation_flow(chat)

    # 응답 영역 생성을 위해 짧은 대기 후 다시 시도
    time.sleep(2)

    # 2차 검증: 응답 후 다시 나타난 추천 질문 영역
    print("\n▶ [2차 검증] 응답 영역 내 추천 질문 선택")
    run_recommendation_flow(chat)

    print("\n🎉 모든 추천 질문 기능 테스트가 성공했습니다. 🎉")


def run_recommendation_flow(chat):
    """추천 질문 선택부터 응답 확인까지의 공통 흐름"""

    # 1. 추천 질문 영역이 나타날 때까지 대기
    chat.wait_for_recommend_questions()
    print("  ▷ 추천 질문 영역 발견!")

    # 2. 랜덤 클릭 (빨간 테두리 포커스 효과 적용)
    clicked_question = chat.click_random_recommend_question()
    print(f"  ▷ 선택된 질문: '{clicked_question}'")

    # 3. 동작 확인 및 전송
    time.sleep(1)
    current_input_value = chat.get_input_value()

    if clicked_question in current_input_value:
        print("  ▷ 동작: 입력창에 질문이 채워짐 -> 수동 전송 수행")
        chat.click_send_button()
    else:
        print("  ▷ 동작: 추천 질문이 즉시 전송되었습니다.")

    # 4. AI 응답 대기 및 검증
    print("  ▷ AI 응답 대기 중...")
    chat.wait_response_complete()

    final_response = chat.get_last_response()

    # 응답이 비어있지 않은지 검증 (길이 로그 제거)
    assert len(final_response) > 0, "AI 응답이 생성되지 않았습니다."
    print("  [✓] 응답 수신 완료")
