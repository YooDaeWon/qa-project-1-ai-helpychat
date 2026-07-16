import pytest
import time
from src.pages.chat_page import ChatPage

# 테스트 설정
QUESTION_LENGTH = 10000  # 테스트할 최대 길이
CHUNK_SIZE = 1000  # 분할 입력 단위


def create_question(length):
    """테스트용 대용량 텍스트 생성"""
    # 더 단순한 패턴으로 생성하여 입력 처리 부하를 줄임
    return "가" * length


def test_large_question_input(setup_and_login):
    """
    [TC_005] 대용량 질문 입력 및 처리 테스트 (5000자)
    - 중점: 5000자 입력 성공 여부, 전송 버튼 작동, 시스템 응답 여부
    """
    driver = setup_and_login
    chat = ChatPage(driver)

    print("\n" + "=" * 60)
    print(f" [TC_005] 대용량 질문 입력 테스트 시작 ({QUESTION_LENGTH}자)")
    print("=" * 60)

    # 1. 질문 생성
    question = create_question(QUESTION_LENGTH)

    # 2. 1000자씩 분할 입력
    textbox = chat.get_input_box()
    textbox.clear()

    print(f"  [>] 입력 시작 (총 {len(question)}자)")
    for index in range(0, len(question), CHUNK_SIZE):
        chunk = question[index : index + CHUNK_SIZE]
        textbox.send_keys(chunk)
        print(
            f"    - 입력 진행: {min(index + CHUNK_SIZE, len(question))} / {len(question)}"
        )
        time.sleep(0.1)

    # 3. 입력값 검증 (입력창에 5000자가 정상적으로 들어갔는지 확인)
    actual_length = chat.get_input_length()
    print(f"  [>] 입력창 실제 입력 글자수: {actual_length}자")
    assert actual_length == QUESTION_LENGTH, (
        f"입력 글자 수 불일치! 예상: {QUESTION_LENGTH}, 실제: {actual_length}"
    )

    # 4. 질문 전송
    print("  [>] 보내기 버튼 클릭")
    chat.click_send_button()

    # 5. AI 응답 여부 확인 (내용은 무관, 응답이 생성되었는지만 검증)
    print("  [>] AI 응답 대기 중...")
    chat.wait_response_complete()

    # 응답이 비어있지만 않으면 성공으로 간주
    answer = chat.get_last_response()
    assert answer is not None, "AI가 응답을 생성하지 않았습니다."

    print(f"  [✓] 응답 성공! (응답 길이: {len(answer)}자)")
    print("\n🎉 TC005 테스트가 성공적으로 완료되었습니다. 🎉")
