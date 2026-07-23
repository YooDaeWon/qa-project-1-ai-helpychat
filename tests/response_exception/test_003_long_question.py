import pytest
from src.pages.chat_page import ChatPage


# 테스트 상수 정의
BASE_TEXT = (
    "AI 응답 글자수 제한 및 긴 텍스트 입력 처리를 확인하기 위한 테스트 문장입니다. "
)

TEST_CASES = [
    dict(name="100글자 이상 입력", question=BASE_TEXT * 3),
    dict(name="500글자 이상 입력", question=BASE_TEXT * 12),
    dict(name="1000글자 이상 입력", question=BASE_TEXT * 23),
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


@pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
def test_003_long_question(module_setup_and_login, case):
    """
    [TC_003] 다양한 길이별(100/500/1000자) 입력 및 응답 테스트

    - 브라우저(세션)는 파일 전체에서 1개만 생성/유지 (module_setup_and_login)
    - 각 길이 케이스는 parametrize로 분리되어 개별 테스트로 결과가 집계됨
    """

    driver = module_setup_and_login
    chat = ChatPage(driver)

    name = case["name"]
    test_text = case["question"]

    print(f"\n▶ [{name}] 테스트 진행 중... (길이: {len(test_text)}자)")

    # 질문 입력
    chat.input_question(test_text)

    # 입력값 검증
    actual_length = chat.get_input_length()

    assert actual_length == len(test_text), (
        f"[{name}] 입력 글자 수 불일치 (기대: {len(test_text)}, 실제: {actual_length})"
    )

    print(f"  [✓] {actual_length}자 입력 확인")

    # 전송 및 응답 대기
    before_count = chat.response_count()
    chat.click_send_button()
    chat.wait_response_complete(before_count)

    # 응답 검증
    answer = chat.get_last_response()

    assert validate_answer(answer), f"[{name}] 응답 검증 실패"

    display_answer = f"{answer[:100]}..." if len(answer) > 100 else answer

    print(f"  [✓] 정상 응답 확인: {display_answer}")
