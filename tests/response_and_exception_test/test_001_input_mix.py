import pytest
from src.pages.chat_page import ChatPage

# 테스트 케이스 데이터
TEST_CASES = [
    ("한글만 입력", "안녕하세요"),
    ("영문만 입력", "Hello AI Agent"),
    ("숫자만 입력", "1234567890"),
    ("한글 + 영문 + 숫자", "안녕하세요 Hello AI Agent 1234567890"),
    ("일본어 입력", "こんにちは"),
    ("일본어 + 영문", "こんにちは Hello AI Agent"),
    ("일본어 + 숫자", "こんにちは 1234567890"),
    ("일본어 + 영문 + 숫자", "こんにちは Hello AI Agent 1234567890"),
    ("태국어 입력", "สวัสดี"),
    ("태국어 + 영문", "สวัสดี Hello AI Agent"),
    ("태국어 + 숫자", "สวัสดี 1234567890"),
    ("태국어 + 영문 + 숫자", "สวัสดี Hello AI Agent 1234567890"),
]


def test_001_chat_input_types(setup_and_login):
    """
    [TC_001] 다양한 언어 및 입력 유형별 전송/응답 테스트

    검증 항목
    - 한글 입력
    - 영문 입력
    - 숫자 입력
    - 한글 + 영문 + 숫자 혼합 입력
    - 일본어 입력 및 혼합 입력
    - 태국어 입력 및 혼합 입력

    각 입력값이 정상적으로 입력되고,
    AI가 정상적으로 응답하는지 확인한다.
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
            f"[{case_name}] 입력값 불일치 (기대값: {test_text}, 실제값: {actual})"
        )

        # 3. 질문 전송
        before_count = chat.response_count()
        chat.send_by_enter()

        # 4. AI 응답 대기
        chat.wait_response_complete(before_count)

        # 5. AI 응답 검증
        ai_answer = chat.get_last_response()
        assert ai_answer and ai_answer.strip(), (
            f"[{case_name}] AI 응답을 받지 못했거나 내용이 비어 있습니다."
        )

        # 성공 로그
        print(f"[{case_name}] 정상 응답 확인: {ai_answer[:20]}...")
