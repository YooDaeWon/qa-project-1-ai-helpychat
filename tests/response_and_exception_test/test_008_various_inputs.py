import pytest
import time
from src.pages.chat_page import ChatPage


def test_exception_handling_all_cases(setup_and_login):
    """
    [TC_008] 다양한 형식의 예외/특수 입력 통합 검증 테스트
    - pytest 테스트 함수 구조 유지
    - 하나의 브라우저 세션에서 12개 케이스를 순차적으로 수행
    """
    driver = setup_and_login
    chat = ChatPage(driver)

    # 1. 테스트 케이스 리스트
    test_cases = [
        ("1. 특수문자 입력", "!@#$%^&*()_+{}|:<>?~`", lambda r: len(r.strip()) > 0),
        ("2. 이모지 입력", "😀🚀🌟🔥🎉", lambda r: len(r.strip()) > 0),
        (
            "3. 링크 요청 질문",
            "토끼와 관련 정보가 있는 웹사이트 링크(URL)를 하나 알려줘.",
            lambda r: "http" in r or "www" in r or len(r) > 0,
        ),
        (
            "4. 목록 형태 답변 요청",
            "인공지능의 장점 3가지를 목록(리스트) 형태로 상세하게 알려줘.",
            lambda r: any(s in r for s in ["1.", "-", "*", "[ ]", "•", "▪", "☐"]),
        ),
        (
            "5. 링크 형식 질문",
            "https://www.google.com 이 링크에 대해 어떻게 생각해?",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "6. 이메일 형식 질문",
            "test.account@example.com 으로 메일을 보내는 방법이 뭐야?",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "7. 전화번호 형식 질문",
            "010-1234-5678 이 번호가 유효한 휴대폰 번호 형식이니?",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "8. 날짜 형식 (20xx-xx-xx)",
            "2024-12-25 은 무슨 요일이야?",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "9. 날짜 형식 (20xx/xx/xx)",
            "2024/12/25 의 일정을 추천해 줄래?",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "10. 날짜 형식 (20xx.xx.xx)",
            "2024.12.25 에 개봉한 유명한 영화가 있어?",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "11. 날짜 형식 (20xx년xx월xx일)",
            "2024년 12월 25일은 크리스마스인데 너도 알고 있니?",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "12. 날짜 형식 (20xxxxxx)",
            "20241225 이 숫자의 의미가 무엇일까?",
            lambda r: len(r.strip()) > 0,
        ),
    ]

    print(f"\n[TC_008] 총 {len(test_cases)}개 케이스 검증 시작 (브라우저 유지)")

    # 2. 브라우저 하나에서 순차적으로 테스트 수행
    for name, question, check_func in test_cases:
        print(f"\n▶ [{name}] 진행 중...")

        # 질문 입력 및 전송
        chat.input_question(question)
        time.sleep(1)
        chat.click_send_button()

        # 응답 대기 및 수신
        chat.wait_response_complete()
        response = chat.get_last_response()

        # 결과 검증
        is_pass = check_func(response)

        # 결과 출력 (길이 로그 제거됨)
        preview = (
            (response[:30].replace("\n", " ") + "...")
            if len(response) > 30
            else response.replace("\n", " ")
        )
        print(f"  ▷ 응답 미리보기: {preview}")

        # 테스트 실패 시 예외 발생 (pytest는 assert를 통해 FAIL 판단)
        assert is_pass, f"[{name}] 검증 실패! (Q: {question})"
        print(f"  [✓] {name} PASS")

        # 다음 질문을 위한 텀
        time.sleep(1.5)
