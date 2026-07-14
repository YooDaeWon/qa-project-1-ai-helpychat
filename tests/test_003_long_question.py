import sys
from pathlib import Path
import time

# 프로젝트 루트 경로 설정
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage

# ---------------------------------------------------------
# 테스트 데이터: 1000글자 이상을 충족하기 위한 텍스트 생성
# BASE_TEXT(65자) * 16회 반복 = 총 1040자
# ---------------------------------------------------------
BASE_TEXT = "AI 응답 글자수 제한 테스트용 문장입니다. 1000글자 이상의 질문에 대해 시스템이 어떻게 반응하는지 확인합니다. "
LONG_QUESTION = BASE_TEXT * 16


def validate_answer(answer: str) -> bool:
    """
    AI 응답 검증: 에러 메시지가 뜨거나 답변을 거부하면 False 반환
    """
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

    # 에러 키워드가 없으면 정상 응답(혹은 의도를 묻는 응답)으로 간주하여 PASS
    return True


def main():
    driver = get_driver()

    try:
        print("=" * 60)
        print("TC003 1000글자 질문 시 응답 출력 테스트 시작")
        print("=" * 60)

        # 1. 로그인 진행 (config의 정보 활용)
        print("▶ 로그인 진행 중...")
        login = LoginPage(driver)
        login.login()

        # 로그인 후 채팅 페이지 렌더링 대기
        time.sleep(3)

        # 2. 채팅 페이지 인스턴스 생성 및 질문 입력
        chat = ChatPage(driver)

        print(f"\n입력할 질문 길이: {len(LONG_QUESTION)}자")
        chat.input_question(LONG_QUESTION)
        print("▶ 1000글자 이상 질문 입력 완료")

        # 3. 질문 전송
        chat.click_send_button()
        print("▶ 보내기 버튼 클릭 완료")

        # 4. AI 응답 대기 및 수집
        print("⏳ AI 응답 대기 중...")
        chat.wait_response_complete()

        answer = chat.get_last_response()

        print(f"\n[AI 응답 내용]")
        # 콘솔 출력이 너무 길어지는 것을 방지 (앞 200자만 출력)
        display_answer = f"{answer[:200]}..." if len(answer) > 200 else answer
        print(display_answer)

        # 5. 응답 검증
        assert validate_answer(answer), "응답 검증 실패 (에러 메시지 발생 또는 무응답)"

        # PASS 처리
        print("\n")
        print("=" * 60)
        print("TC003 PASS : 1000글자 이상 입력 시 정상 응답 확인")
        print("=" * 60)

        input("결과 확인 후 Enter를 누르세요.")

    finally:
        # 6. 브라우저 종료
        driver.quit()


if __name__ == "__main__":
    main()
