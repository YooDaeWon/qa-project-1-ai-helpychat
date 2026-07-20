import pytest
import time
from src.pages.chat_page import ChatPage


# 테스트 설정
QUESTION_LENGTH = 10000  # 자동 입력할 전체 문자 수
CHUNK_SIZE = 1000  # 한번에 입력할 문자 수


def create_question(length):
    """
    테스트용 대용량 문자 데이터 생성

    - 의미 있는 질문이 아닌 단순 문자 반복
    - 입력 처리 안정성 검증 목적
    """
    return "가" * length


def validate_answer(answer: str) -> bool:
    """
    AI 응답 생성 여부 검증

    검증 기준:
    - 빈 응답 실패
    - 시스템 오류 메시지 실패
    - 답변 내용의 정확성은 검증하지 않음

    목적:
    대량 입력 후 AI가 요청을 처리하고
    응답 생성까지 가능한지 확인
    """

    if not answer or answer.strip() == "":
        return False

    error_keywords = [
        "오류",
        "에러",
        "실패",
        "생성할 수 없습니다",
        "응답할 수 없습니다",
        "처리할 수 없습니다",
    ]

    return not any(keyword in answer for keyword in error_keywords)


def test_large_text_input_stability(setup_and_login):
    """
    [TC_005] 대용량 문자 입력 처리 안정성 테스트

    검증 항목:
    1. 대량 문자 자동 입력 가능 여부
    2. 입력창 정상 처리 여부
    3. 입력 데이터 전송 가능 여부
    4. AI 응답 생성 여부

    ※ 본 테스트는 Selenium 자동 입력 환경 기준 테스트이며,
      실제 최대 입력 가능 길이 검증은 별도 수동 테스트에서 진행
    """

    driver = setup_and_login
    chat = ChatPage(driver)

    print("\n" + "=" * 60)
    print(f" [TC_005] 대용량 문자 입력 처리 안정성 테스트 시작 ({QUESTION_LENGTH}자)")
    print("=" * 60)

    # 1. 테스트 데이터 생성
    question = create_question(QUESTION_LENGTH)

    # 2. 입력창 초기화
    textbox = chat.get_input_box()
    textbox.clear()

    print(f"  [>] 대용량 문자 입력 시작 (총 {len(question)}자)")

    # 3. CHUNK 단위 분할 입력
    for index in range(0, len(question), CHUNK_SIZE):
        chunk = question[index : index + CHUNK_SIZE]

        textbox.send_keys(chunk)

        print(
            f"    - 입력 진행: "
            f"{min(index + CHUNK_SIZE, len(question))}"
            f" / {len(question)}"
        )

        # 브라우저 입력 이벤트 처리 안정화 대기
        time.sleep(0.1)

    # 4. 실제 입력 글자 수 검증
    actual_length = chat.get_input_length()

    print(f"  [>] 입력창 실제 입력 글자수: {actual_length}자")

    assert actual_length == QUESTION_LENGTH, (
        f"입력 글자 수 불일치! 예상: {QUESTION_LENGTH}, 실제: {actual_length}"
    )

    # 5. 전송
    print("  [>] 보내기 버튼 클릭")

    chat.click_send_button()

    # 6. 응답 대기
    print("  [>] AI 응답 대기 중...")

    chat.wait_response_complete()

    # 7. 응답 생성 여부 검증
    answer = chat.get_last_response()

    assert validate_answer(answer), f"AI 응답 생성 실패: {answer}"

    print(f"  [✓] 응답 생성 성공 (응답 길이: {len(answer)}자)")

    print("\n🎉 TC005 대용량 문자 입력 처리 안정성 테스트 완료 🎉")
