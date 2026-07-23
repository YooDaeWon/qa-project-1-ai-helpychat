import pytest
from src.pages.chat_page import ChatPage

# ======================================================
# 테스트 케이스 데이터
# ======================================================
TEST_CASES = [
    dict(name="한글만 입력", question="안녕하세요"),
    dict(name="영문만 입력", question="Hello AI Agent"),
    dict(name="숫자만 입력", question="1234567890"),
    dict(name="한글 + 영문 + 숫자", question="안녕하세요 Hello AI Agent 1234567890"),
    dict(name="일본어 입력", question="こんにちは"),
    dict(name="일본어 + 영문", question="こんにちは Hello AI Agent"),
    dict(name="일본어 + 숫자", question="こんにちは 1234567890"),
    dict(name="일본어 + 영문 + 숫자", question="こんにちは Hello AI Agent 1234567890"),
    dict(name="태국어 입력", question="สวัสดี"),
    dict(name="태국어 + 영문", question="สวัสดี Hello AI Agent"),
    dict(name="태국어 + 숫자", question="สวัสดี 1234567890"),
    dict(name="태국어 + 영문 + 숫자", question="สวัสดี Hello AI Agent 1234567890"),
]


@pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
def test_001_chat_input_types(module_setup_and_login, case):
    """
    [TC_001] 다양한 언어 및 입력 유형별 전송/응답 테스트

    - 브라우저(세션)는 파일 전체에서 1개만 생성/유지 (module_setup_and_login)
    - 각 언어/입력 유형 케이스는 parametrize로 분리되어
      개별 테스트로 결과가 집계됨 (하나 실패해도 나머지 케이스 계속 진행)
    """

    driver = module_setup_and_login
    chat = ChatPage(driver)

    name = case["name"]
    test_text = case["question"]

    print(f"\n>>> 실행 중인 케이스: {name}")

    # 1. 질문 입력
    chat.input_question(test_text)

    # 2. 입력값 검증
    actual = chat.get_input_value()
    assert actual == test_text, (
        f"[{name}] 입력값 불일치 (기대값: {test_text}, 실제값: {actual})"
    )

    # 3. 질문 전송
    before_count = chat.response_count()
    chat.send_by_enter()

    # 4. AI 응답 대기
    chat.wait_response_complete(before_count)

    # 5. AI 응답 검증
    ai_answer = chat.get_last_response()
    assert ai_answer and ai_answer.strip(), (
        f"[{name}] AI 응답을 받지 못했거나 내용이 비어 있습니다."
    )

    # 성공 로그
    print(f"[{name}] 정상 응답 확인: {ai_answer[:20]}...")
