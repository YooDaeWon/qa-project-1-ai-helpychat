import pytest
import time
from src.pages.chat_page import ChatPage

# 테스트 상수 정의
QUESTION = "30 × 90 = 무엇인가?"
REPEAT_COUNT = 10


def validate_answer(answer: str):
    """응답 검증 로직"""
    if not answer:
        return False
    error_keywords = ["오류", "죄송", "실패", "생성할 수 없습니다"]
    if any(keyword in answer for keyword in error_keywords):
        return False
    return "2700" in answer or "2,700" in answer


def test_repeat_question(setup_and_login):
    """
    10회 동일 질문 반복 테스트
    - setup_and_login: 테스트 시작 시 브라우저 실행 및 로그인 1회 수행
    """
    driver = setup_and_login
    chat = ChatPage(driver)

    # 브라우저 세션을 유지하며 10회 연속 질문 전송
    for i in range(REPEAT_COUNT):
        print(f"\n[{i + 1}/{REPEAT_COUNT}] 질문 전송 중...")

        chat.input_question(QUESTION)
        chat.click_send_button()

        # AI 응답 완료 대기
        chat.wait_response_complete()

        # 마지막 응답 가져오기
        answer = chat.get_last_response()

        # 검증
        assert validate_answer(answer), f"{i + 1}번째 응답 검증 실패: {answer}"

        # 응답 간 대기 (필요 시)
        time.sleep(1)

    print(f"\nTC002 10회 반복 테스트 PASS")
