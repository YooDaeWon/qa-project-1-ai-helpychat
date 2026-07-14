import sys
import time
from pathlib import Path


# 프로젝트 루트 경로 설정
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage


# =====================================================
# TC005
# 대용량 질문 입력 테스트
# 500자 단위 입력 방식 적용
# =====================================================


QUESTION_LENGTHS = [50000]


# -----------------------------------------------------
# 테스트 질문 생성
# -----------------------------------------------------


def create_question(length):

    base_text = (
        "AI 채팅 대용량 질문 입력 테스트를 위한 문장입니다. "
        "긴 질문 입력 상황에서 시스템이 정상적으로 처리하는지 확인합니다. "
    )

    repeat_count = (length // len(base_text)) + 1

    return (base_text * repeat_count)[:length]


# -----------------------------------------------------
# 대용량 입력 함수
# 500자씩 나누어 입력
# -----------------------------------------------------


def input_large_question_by_chunk(chat, question, chunk_size=1000):
    """
    긴 질문을 일정 크기로 나누어 입력
    """

    textbox = chat.get_input_box()

    textbox.clear()

    total_length = len(question)

    print(f"총 입력 예정 길이 : {total_length}자")

    for index in range(0, total_length, chunk_size):
        chunk = question[index : index + chunk_size]

        textbox.send_keys(chunk)

        print(f"입력 진행 : {min(index + chunk_size, total_length)} / {total_length}")

        # 입력 이벤트 처리 시간 확보
        time.sleep(0.05)


# -----------------------------------------------------
# AI 응답 검증
# -----------------------------------------------------


def validate_answer(answer: str) -> bool:

    if not answer or answer.strip() == "":
        return False

    error_keywords = [
        "오류",
        "실패",
        "생성할 수 없습니다",
        "인식하지 못",
        "인식할 수 없",
        "답변할 수 없",
        "답변을 제공할 수 없",
        "에러",
    ]

    for keyword in error_keywords:
        if keyword in answer:
            return False

    return True


# -----------------------------------------------------
# TC005 실행
# -----------------------------------------------------


def main():

    driver = get_driver()

    try:
        print("=" * 70)
        print("TC005 대용량 질문 입력 테스트 시작")
        print("=" * 70)

        # -------------------------------------------------
        # 로그인
        # -------------------------------------------------

        print("\n▶ 로그인 진행 중...")

        login = LoginPage(driver)

        login.login()

        time.sleep(3)

        # -------------------------------------------------
        # ChatPage 생성
        # -------------------------------------------------

        chat = ChatPage(driver)

        chat.get_input_box()

        # -------------------------------------------------
        # 질문 길이별 테스트
        # -------------------------------------------------

        for length in QUESTION_LENGTHS:
            print("\n" + "-" * 70)

            print(f"테스트 질문 길이 : {length}자")

            print("-" * 70)

            question = create_question(length)

            print(f"생성된 질문 길이 : {len(question)}자")

            # -------------------------------------------------
            # 500자 단위 입력
            # -------------------------------------------------

            input_large_question_by_chunk(chat, question, chunk_size=1000)

            print("▶ 질문 입력 완료")

            # -------------------------------------------------
            # 질문 전송
            # -------------------------------------------------

            print("▶ 보내기 버튼 클릭")

            chat.click_send_button()

            # -------------------------------------------------
            # 응답 대기
            # -------------------------------------------------

            print("⏳ AI 응답 대기 중...")

            chat.wait_response_complete()

            # -------------------------------------------------
            # 응답 확인
            # -------------------------------------------------

            answer = chat.get_last_response()

            print("\n[AI 응답]")

            display_answer = answer[:200] + "..." if len(answer) > 200 else answer

            print(display_answer)

            assert validate_answer(answer), f"{length}자 질문 응답 검증 실패"

            print(f"\nTC005 {length}자 테스트 PASS")

        print("\n")

        print("=" * 70)

        print("TC005 PASS : 대용량 질문 입력 및 응답 확인 완료")

        print("=" * 70)

    except Exception as e:
        print("\n" + "=" * 70)

        print("TC005 FAIL")

        print("=" * 70)

        print(e)

    finally:
        input("\n결과 확인 후 Enter를 누르세요...")

        driver.quit()


if __name__ == "__main__":
    main()
