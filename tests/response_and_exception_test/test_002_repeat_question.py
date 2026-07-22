import pytest
from src.pages.chat_page import ChatPage


# 테스트 상수 정의
QUESTION = "30 × 90 = 무엇인가?"
EXPECTED_ANSWER = "2700"
REPEAT_COUNT = 10


def validate_answer(answer: str):
    """응답 검증 로직 (숫자 및 한글 정답 지원)"""

    if not answer:
        return False

    # 응답 실패 및 예외 메시지 검증
    error_keywords = [
        "오류",
        "죄송",
        "실패",
        "생성할 수 없습니다",
        "계산할 수 없습니다",
        "알 수 없습니다",
    ]

    if any(keyword in answer for keyword in error_keywords):
        return False

    # 1. 쉼표 제거 후 숫자 정답 값 검증
    normalized_answer = answer.replace(",", "")
    if EXPECTED_ANSWER in normalized_answer:
        return True

    # 2. [추가] 한글 정답 검증 (띄어쓰기 변형 포함 방어)
    # AI가 "이천칠백", "이천 칠백" 등으로 답변할 경우 대비
    answer_no_space = answer.replace(" ", "")
    korean_expected_keywords = ["이천칠백"]

    if any(korean in answer_no_space for korean in korean_expected_keywords):
        return True

    return False


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
        before_count = chat.response_count()
        chat.click_send_button()

        # AI 응답 완료 대기
        chat.wait_response_complete(before_count)

        # 마지막 응답 가져오기
        answer = chat.get_last_response()

        # 검증
        assert validate_answer(answer), f"{i + 1}번째 응답 검증 실패: {answer}"

    print("\nTC002 10회 반복 테스트 PASS")
