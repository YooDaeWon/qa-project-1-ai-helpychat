import pytest
from src.pages.chat_page import ChatPage


# 테스트 상수 정의
BASE_TEXT = (
    "AI 응답 글자수 제한 및 긴 텍스트 입력 처리를 확인하기 위한 테스트 문장입니다. "
)

TEST_CASES = [
    ("100글자 이상 입력", BASE_TEXT * 3),
    ("500글자 이상 입력", BASE_TEXT * 12),
    ("1000글자 이상 입력", BASE_TEXT * 23),
]


def validate_answer(answer: str) -> bool:
    """AI 응답 검증 로직"""

    if not answer or answer.strip() == "":
        return False

    error_keywords = [
        "오류",
        "실패",
        "생성할 수 없습니다",
        "에러",
    ]

    return not any(keyword in answer for keyword in error_keywords)


def test_003_long_question(setup_and_login):
    """
    [TC_003] 다양한 길이별(100/500/1000자) 입력 및 응답 테스트
    - 브라우저를 1회 실행하여 모든 케이스를 연속 검증합니다.
    """

    driver = setup_and_login
    chat = ChatPage(driver)

    print("\n" + "=" * 60)
    print(" [TC_003] 다양한 길이 입력 및 응답 테스트 시작 ")
    print("=" * 60)

    for case_name, test_text in TEST_CASES:
        print(f"\n▶ [{case_name}] 테스트 진행 중... (길이: {len(test_text)}자)")

        # 질문 입력
        chat.input_question(test_text)

        # 입력값 검증
        actual_length = chat.get_input_length()

        assert actual_length == len(test_text), (
            f"입력 글자 수 불일치 (기대: {len(test_text)}, 실제: {actual_length})"
        )

        print(f"  [✓] {actual_length}자 입력 확인")

        # 전송 및 응답 대기
        chat.click_send_button()
        chat.wait_response_complete()

        # 응답 검증
        answer = chat.get_last_response()

        assert validate_answer(answer), f"[{case_name}] 응답 검증 실패"

        display_answer = f"{answer[:100]}..." if len(answer) > 100 else answer

        print(f"  [✓] 정상 응답 확인: {display_answer}")

    print("\n🎉 모든 길이 입력 테스트가 성공했습니다. 🎉")
