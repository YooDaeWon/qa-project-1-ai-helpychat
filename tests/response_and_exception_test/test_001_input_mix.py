import pytest
from src.pages.chat_page import ChatPage

# 테스트 케이스 데이터
TEST_CASES = [
    ("한글만 입력", "안녕하세요"),
    ("영문만 입력", "Hello AI Agent"),
    ("숫자만 입력", "1234567890"),
    ("한/영, 숫자 혼합 입력", "가나다 ABC123 456테스트"),
]


def test_001_chat_input_types(setup_and_login):
    """
    [TC_001] 다양한 입력 유형별 전송 및 응답 테스트
    - 4개의 케이스를 브라우저 종료 없이 연속 실행합니다.
    """
    driver = setup_and_login
    chat = ChatPage(driver)

    for case_name, test_text in TEST_CASES:
        print(f"\n>>> 실행 중인 케이스: {case_name}")

        # 1. 질문 입력
        chat.input_question(test_text)

        # 2. 입력값 검증
        actual = chat.get_input_value()
        assert actual == test_text, (
            f"입력값 불일치 (기대값: {test_text}, 실제값: {actual})"
        )

        # 3. 질문 전송
        chat.send_by_enter()

        # 4. AI 답변 대기 및 검증
        chat.wait_response_complete()
        ai_answer = chat.get_last_response()
        assert ai_answer, f"[{case_name}] AI 응답을 받지 못했거나 내용이 비어있습니다."

        # 성공 로그
        print(f"[{case_name}] 정상 응답 확인: {ai_answer[:20]}...")
