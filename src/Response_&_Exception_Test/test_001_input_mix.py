import sys
import time  # 3초 대기를 위해 time 모듈 추가
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage


##--------한글/영문/숫자/한,영,숫자 혼합 입력질의응답 TEST-------##


TEST_CASES = {
    "한글만 입력": "안녕하세요",
    "영문만 입력": "Hello AI Agent",
    "숫자만 입력": "1234567890",
    "한/영, 숫자 혼합 입력": "가나다 ABC123 456테스트",
}


def main():
    driver = get_driver()

    # 각 케이스별 결과를 저장할 딕셔너리
    test_results = {}

    try:
        # 로그인
        login = LoginPage(driver)
        login.login()

        # 채팅 페이지
        chat = ChatPage(driver)

        print("\n" + "=" * 60)
        print("     [TC_001] 다양한 입력 유형별 전송 및 응답 테스트 시작     ")
        print("=" * 60 + "\n")

        for case_name, test_text in TEST_CASES.items():
            print(f"▶ [{case_name}] 테스트 진행 중...")
            case_status = "[FAIL] ❌"  # 기본값을 실패로 설정

            try:
                # 1. 질문 입력
                chat.input_question(test_text)

                # 2. 입력값 검증
                actual = chat.get_input_value()
                if actual != test_text:
                    raise AssertionError(
                        f"입력값 불일치 (기대값: {test_text}, 실제값: {actual})"
                    )
                print(f"  [✓] 입력 완료: '{actual}'")

                # 3. 질문 전송
                chat.send_by_enter()
                print("  [✓] 질문 전송 성공")

                # 4. AI 답변 자동 대기
                print("  [...] AI 응답 생성 대기 중...")
                chat.wait_response_complete()

                # 5. AI 응답 내용 추출 및 검증
                ai_answer = chat.get_last_response()
                if not ai_answer:
                    raise AssertionError("AI 응답을 받지 못했거나 내용이 비어있습니다.")

                print(f"  [✓] AI 답변 수신 성공:\n      {ai_answer}")

                # 모든 단계를 에러 없이 통과했다면 성공 처리
                case_status = "[PASS] ✅"

            except Exception as e:
                # 에러 발생 시 원인 출력 (실패 처리 유지)
                print(f"  [✗] 실패 원인: {e}")

            finally:
                # 결과 기록 및 현재 케이스 마무리에 상태 출력
                test_results[case_name] = case_status
                print(f"\n▷ [{case_name}] 결과: {case_status}")
                print("-" * 60)

        # --------------------------------------------------
        # 최종 결과 요약 리포트 출력
        # --------------------------------------------------
        print("\n" + "=" * 60)
        print("                  [최종 테스트 결과 요약]                  ")
        print("=" * 60)

        all_passed = True
        for name, status in test_results.items():
            print(f" - {name:<18} : {status}")
            if "FAIL" in status:
                all_passed = False

        print("=" * 60)

        if all_passed:
            print(
                "\n🎉 완벽합니다! 모든 입력 유형 테스트가 성공적으로 통과되었습니다. 🎉\n"
            )
        else:
            print(
                "\n⚠️ 일부 테스트 케이스가 실패했습니다. 위 로그의 [✗] 실패 원인을 확인해주세요.\n"
            )

    finally:
        # ===== [추가된 부분] 브라우저 종료 전 3초 대기 =====
        print("\n테스트가 모두 종료되었습니다. 3초 후 브라우저를 닫습니다...")
        time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    main()
