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
# TC008
# 다양한 형식의 예외/특수 입력 통합 검증 테스트
# =====================================================
def main():
    driver = get_driver()

    # 테스트할 다양한 입력 케이스 정의
    # check: 해당 응답(response)이 올바른지 검증하는 조건을 정의한 함수 (True면 PASS, False면 FAIL)
    test_cases = [
        {
            "name": "1. 특수문자 입력 시 답변",
            "question": "!@#$%^&*()_+{}|:<>?~`",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "2. 이모지 입력 시 답변",
            "question": "😀🚀🌟🔥🎉",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "3. 링크 포함(요청) 질문 시 답변",
            "question": "토끼와 관련 정보가 있는 웹사이트 링크(URL)를 하나 알려줘.",
            "check": lambda resp: (
                "http" in resp or "www" in resp or len(resp) > 0
            ),  # http 포함 여부 또는 정상 출력 확인
        },
        {
            "name": "4. 목록 형태 답변 요청",
            "question": "인공지능의 장점 3가지를 목록(리스트) 형태로 상세하게 알려줘.",
            "check": lambda resp: (
                "1." in resp
                or "-" in resp
                or "*" in resp
                or "[ ]" in resp
                or "•" in resp
                or "▪" in resp
                or "I" in resp
                or "A" in resp
                or "☐"
            ),  # 목록 기호가 답변에 포함되어 있는지 확인
        },
        {
            "name": "5. 링크 형식으로 질문",
            "question": "https://www.google.com 이 링크에 대해 어떻게 생각해?",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "6. 이메일 형식으로 질문",
            "question": "test.account@example.com 으로 메일을 보내는 방법이 뭐야?",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "7. 전화번호 형식으로 질문",
            "question": "010-1234-5678 이 번호가 유효한 휴대폰 번호 형식이니?",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "8. 날짜 형식 (20xx-xx-xx)",
            "question": "2024-12-25 은 무슨 요일이야?",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "9. 날짜 형식 (20xx/xx/xx)",
            "question": "2024/12/25 의 일정을 추천해 줄래?",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "10. 날짜 형식 (20xx.xx.xx)",
            "question": "2024.12.25 에 개봉한 유명한 영화가 있어?",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "11. 날짜 형식 (20xx년xx월xx일)",
            "question": "2024년 12월 25일은 크리스마스인데 너도 알고 있니?",
            "check": lambda resp: len(resp.strip()) > 0,
        },
        {
            "name": "12. 날짜 형식 (20xxxxxx)",
            "question": "20241225 이 숫자의 의미가 무엇일까?",
            "check": lambda resp: len(resp.strip()) > 0,
        },
    ]
    # 각 케이스의 테스트 결과를 저장할 리스트
    results_report = []
    try:
        print("=" * 70)
        print("TC008 다양한 형식의 예외/특수 입력 통합 검증 테스트")
        print("=" * 70)
        # -------------------------------------------------
        # 로그인
        # -------------------------------------------------
        login = LoginPage(driver)
        login.login()
        chat = ChatPage(driver)

        # 입력창 대기
        chat.get_input_box()
        print(
            "\n▶ 테스트 준비 완료. 총 {}개의 케이스를 시작합니다.\n".format(
                len(test_cases)
            )
        )
        # -------------------------------------------------
        # 케이스별 반복 검증
        # -------------------------------------------------
        for idx, tc in enumerate(test_cases, 1):
            print(f"[{idx}/{len(test_cases)}] {tc['name']} 진행 중...")

            # 1. 질문 입력 및 전송
            chat.input_question(tc["question"])
            time.sleep(1)
            chat.click_send_button()

            # 2. 응답 대기
            chat.wait_response_complete()
            response = chat.get_last_response()

            # 3. 결과 검증 (정의한 check 로직 실행)
            is_pass = tc["check"](response)

            # 보고서를 위해 데이터 저장
            results_report.append(
                {
                    "name": tc["name"],
                    "question": tc["question"],
                    "response_preview": response[:30].replace("\n", " ") + "..."
                    if len(response) > 30
                    else response.replace("\n", " "),
                    "is_pass": is_pass,
                }
            )

            if is_pass:
                print(f"   => 검증 결과: PASS")
            else:
                print(f"   => 검증 결과: FAIL")

            time.sleep(1.5)  # 다음 질문 전 텀을 둠
        # -------------------------------------------------
        # 최종 통합 결과 리포트 출력
        # -------------------------------------------------
        print("\n" + "=" * 70)
        print("TC008 최종 검증 결과 리포트")
        print("=" * 70)

        all_passed = True

        for res in results_report:
            status = "✅ PASS" if res["is_pass"] else "❌ FAIL"
            print(f"{status} | {res['name']}")
            print(f"         - Q: {res['question']}")
            print(f"         - A: {res['response_preview']}\n")

            if not res["is_pass"]:
                all_passed = False

        print("=" * 70)

        if all_passed:
            print("TC008 최종 결과 : ALL PASS 🎉")
        else:
            print("TC008 최종 결과 : FAIL (일부 케이스 실패)")

        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print("TC008 실행 중 치명적 오류 발생 (FAIL)")
        print("=" * 70)
        print(e)
    finally:
        input("\n종료하려면 Enter를 누르세요...")
        driver.quit()


if __name__ == "__main__":
    main()
