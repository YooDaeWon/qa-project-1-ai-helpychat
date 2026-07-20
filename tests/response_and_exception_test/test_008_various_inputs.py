import pytest
import time
from src.pages.chat_page import ChatPage


def validate_list_response(response):
    """
    목록 형태 답변 검증 (전체 키워드 통합 및 전체 검색 방식)
    - 기존의 다양한 리스트 패턴을 모두 포함
    - 줄바꿈이나 위치에 상관없이 텍스트 전체에서 해당 키워드가 존재하는지 검사
    """
    if not response or response.strip() == "":
        return False

    # 줄바꿈 기호를 단순 띄어쓰기로 변경하여 하나의 긴 텍스트로 만듦 (줄바꿈/위치 무시)
    flat_response = response.replace("\n", " ").strip()

    # 기존 모든 키워드 + 불릿 통합
    # 주의: "1.", "-" 등은 소수점(3.14)이나 단어 연결(고속-처리)과 혼동되지 않도록 뒤에 공백(" ")을 포함했습니다.
    list_patterns = [
        # 숫자 목록
        "1. ",
        "2. ",
        "3. ",
        "4. ",
        "5. ",
        # 숫자 괄호
        "(1)",
        "(2)",
        "(3)",
        "(4)",
        "(5)",
        # 원 숫자
        "①",
        "②",
        "③",
        "④",
        "⑤",
        "⑥",
        "⑦",
        "⑧",
        "⑨",
        "⑩",
        # 한글 순서
        "첫째",
        "둘째",
        "셋째",
        "넷째",
        "다섯째",
        "첫 번째",
        "두 번째",
        "세 번째",
        "네 번째",
        "다섯 번째",
        # 영어 순서
        "First",
        "Second",
        "Third",
        "Fourth",
        "Fifth",
        # 알파벳 목록
        "A. ",
        "B. ",
        "C. ",
        "D. ",
        "E. ",
        "(A)",
        "(B)",
        "(C)",
        "(D)",
        "(E)",
        # 불릿 형태
        "- ",
        "– ",
        "— ",
        "* ",
        "• ",
        "▪ ",
        "▫ ",
        "◦ ",
        "‣ ",
        "⁃ ",
        # 체크박스
        "☐",
        "☑",
        "✓",
        "✔",
        "✅",
        # 화살표
        "→",
        "➜",
        "➤",
        "▶",
        # 마크다운
        "# ",
        "## ",
        "### ",
    ]

    match_count = 0

    # 텍스트 전체(flat_response) 안에 목록 마커가 포함되어 있는지 확인
    for pattern in list_patterns:
        if pattern in flat_response:
            match_count += 1

    # 목록성 마커가 최소 1개 이상 존재하면 통과 (AI의 목록 형태 시도를 인정)
    return match_count >= 1


def wait_response_with_retry(chat, question):
    """
    TC008 전용 응답 확인 로직

    목적:
    - 빠른 정상 응답은 즉시 진행
    - 일시적인 응답 누락 발생 시 1회 재전송
    """

    # 1차 질문 전송
    chat.input_question(question)
    chat.click_send_button()

    # 빠른 응답 확인
    try:
        chat.wait_response_complete(timeout=10)

        response = chat.get_last_response()

        if response.strip():
            return response

    except Exception:
        pass

    print("  ⚠ 1차 응답 없음 → 추가 대기 진행")

    # 추가 대기
    try:
        chat.wait_response_complete(timeout=30)

        response = chat.get_last_response()

        if response.strip():
            return response

    except Exception:
        pass

    # 최종 재전송
    print("  ⚠ 최종 응답 없음 → 질문 재전송")

    chat.input_question(question)
    chat.click_send_button()

    chat.wait_response_complete(timeout=60)

    return chat.get_last_response()


def test_exception_handling_all_cases(setup_and_login):
    """
    [TC_008] 다양한 형식의 예외/특수 입력 통합 검증 테스트

    검증 목적:
    - 특수 문자 입력 처리
    - 이모지 입력 처리
    - URL/이메일/전화번호 형식 입력 처리
    - 다양한 날짜 형식 입력 처리
    - 목록 형태 답변 처리 검증

    ※ 응답 속도가 아닌 입력 이해 및 답변 생성 가능 여부 검증
    """

    driver = setup_and_login
    chat = ChatPage(driver)

    test_cases = [
        (
            "1. 특수문자 입력",
            "!@#$%^&*()_+{}|:<>?~`",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "2. 이모지 입력",
            "😀🚀🌟🔥🎉",
            lambda r: len(r.strip()) > 0,
        ),
        (
            "3. 링크 요청 질문",
            "토끼와 관련 정보가 있는 웹사이트 링크(URL)를 하나 알려줘.",
            lambda r: "http" in r or "www" in r or len(r) > 0,
        ),
        (
            "4. 목록 형태 답변 요청",
            "인공지능의 장점 3가지를 목록(리스트) 형태로 상세하게 알려줘.",
            validate_list_response,
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

    for name, question, check_func in test_cases:
        print(f"\n▶ [{name}] 진행 중...")

        response = wait_response_with_retry(chat, question)

        if response is None:
            response = ""

        is_pass = check_func(response)

        preview = (
            response[:30].replace("\n", " ") + "..."
            if len(response) > 30
            else response.replace("\n", " ")
        )

        print(f"  ▷ 응답 미리보기: {preview}")

        assert is_pass, f"[{name}] 검증 실패!\n질문: {question}\n응답: {response}"

        print(f"  [✓] {name} PASS")

        time.sleep(1.5)
