import sys
import time
from pathlib import Path

# 프로젝트 루트 경로 설정
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage

# ---------------------------------------------------------
# 테스트 데이터: 다양한 길이의 텍스트 생성
# 100자, 500자, 1000자 이상의 텍스트 입력 및 응답 출력 테스트
# ---------------------------------------------------------
BASE_TEXT = (
    "AI 응답 글자수 제한 및 긴 텍스트 입력 처리를 확인하기 위한 테스트 문장입니다. "
)

TEST_CASES = {
    "100글자 이상 입력": BASE_TEXT * 3,  # 약 135자
    "500글자 이상 입력": BASE_TEXT * 12,  # 약 540자
    "1000글자 이상 입력": BASE_TEXT * 23,  # 약 1035자
}


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

    # 에러 키워드가 없으면 정상 응답으로 간주하여 True 반환
    return True


def main():
    driver = get_driver()
    test_results = {}

    try:
        # 1. 로그인
        login = LoginPage(driver)
        login.login()

        # 2. 채팅 페이지 준비
        chat = ChatPage(driver)

        print("\n" + "=" * 60)
        print("   [TC_003] 다양한 길이(100/500/1000자) 입력 및 응답 테스트   ")
        print("=" * 60 + "\n")

        # 로그인 직후 채팅창 로딩 대기
        time.sleep(3)

        # 각 케이스별로 순차적 테스트 수행
        for case_name, test_text in TEST_CASES.items():
            print(f"▶ [{case_name}] 테스트 진행 중... (입력 길이: {len(test_text)}자)")
            case_status = "[FAIL] ❌"

            try:
                # 1) 질문 입력
                chat.input_question(test_text)

                # 2) 입력값 검증: 글자가 잘리거나 누락되지 않고 모두 입력되었는지 확인
                actual_length = chat.get_input_length()
                if actual_length != len(test_text):
                    raise AssertionError(
                        f"입력 글자 수 불일치 (기대값: {len(test_text)}, 실제값: {actual_length})"
                    )
                print(f"  [✓] {actual_length}자 입력 완료")

                # 3) 질문 전송 (기존 코드에 있던 click_send_button 활용)
                chat.click_send_button()
                print("  [✓] 보내기 버튼 클릭 완료")

                # 4) AI 응답 대기
                print("  [...] AI 응답 생성 대기 중...")
                chat.wait_response_complete()

                # 5) AI 응답 추출
                answer = chat.get_last_response()

                # 6) 응답 유효성 검증
                if not validate_answer(answer):
                    raise AssertionError(
                        "응답 검증 실패 (에러 메시지 발생 또는 무응답)"
                    )

                # 콘솔 출력이 너무 길어지는 것을 방지 (앞 150자만 미리보기)
                display_answer = f"{answer[:150]}..." if len(answer) > 150 else answer
                print(f"  [✓] 정상 응답 확인:\n      {display_answer}")

                # 모두 통과 시 상태 업데이트
                case_status = "[PASS] ✅"

            except Exception as e:
                print(f"  [✗] 실패 원인: {e}")

            finally:
                # 결과 기록
                test_results[case_name] = case_status
                print(f"\n▷ [{case_name}] 결과: {case_status}")
                print("-" * 60)

                # 다음 입력을 위해 잠시 대기 (연속 전송 방지)
                time.sleep(2)

        # --------------------------------------------------
        # 최종 결과 요약 리포트
        # --------------------------------------------------
        print("\n" + "=" * 60)
        print("                  [최종 테스트 결과 요약]                  ")
        print("=" * 60)

        all_passed = True
        for name, status in test_results.items():
            print(f" - {name:<20} : {status}")
            if "FAIL" in status:
                all_passed = False

        print("=" * 60)

        if all_passed:
            print(
                "\n🎉 모든 길이(100/500/1000자 이상) 입력 테스트가 성공했습니다. 🎉\n"
            )
        else:
            print(
                "\n⚠️ 일부 길이에서 에러나 잘림 현상이 발생했습니다. 로그를 확인하세요.\n"
            )

    finally:
        # 종료 전 3초 대기
        print("\n테스트가 모두 종료되었습니다. 3초 후 브라우저를 닫습니다...")
        time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    main()
