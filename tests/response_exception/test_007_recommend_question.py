import pytest
import time
from src.pages.chat_page import ChatPage


def test_recommend_questions(setup_and_login):
    """
    [TC_007] 'AI헬피 추천 질문' 기능 동작 테스트 (메인 화면 & 응답 영역)
    """
    driver = setup_and_login
    chat = ChatPage(driver)

    print("\n" + "=" * 70)
    print(" [TC_007] AI헬피 추천 질문 기능 동작 테스트 시작 ")
    print("=" * 70)

    # 1차 검증: 로그인 후 메인 화면
    print("\n▶ [1차 검증] 메인 화면 추천 질문 선택")
    run_recommendation_flow(chat)

    # ❗ [수정된 부분] 무의미한 time.sleep(1) 대신, 스크롤을 내리고 명확히 대기
    print("  ▷ 2차 검증 준비: 화면 맨 아래로 스크롤")
    chat.scroll_to_bottom()

    # 2차 검증: 응답 후 다시 나타난 추천 질문 영역
    print("\n▶ [2차 검증] 응답 영역 내 추천 질문 선택")
    run_recommendation_flow(chat)

    print("\n🎉 모든 추천 질문 기능 테스트가 성공했습니다. 🎉")


def run_recommendation_flow(chat):
    """추천 질문 선택부터 응답 확인까지의 공통 흐름"""

    # 1. 추천 질문 영역이 나타날 때까지 대기
    chat.wait_for_recommend_questions()
    print("  ▷ 추천 질문 영역 발견!")

    # ❗ [핵심 수정 1] 클릭/전송 액션 이전에 현재 응답 개수를 미리 기록!
    before_count = chat.response_count()

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

    # ❗ [핵심 수정 2] 미리 기록해둔 before_count를 넘겨주어 레이스 컨디션 완벽 차단!
    chat.wait_response_complete(before_count)

    final_response = chat.get_last_response()

    assert len(final_response) > 0, "AI 응답이 생성되지 않았습니다."
    print("  [✓] 응답 수신 완료")
