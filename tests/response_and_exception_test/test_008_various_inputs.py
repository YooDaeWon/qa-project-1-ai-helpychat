import time
import pytest
from src.pages.chat_page import ChatPage
from selenium.common.exceptions import TimeoutException

# ======================================================
# 공통 실패 신호 (애플리케이션 레벨의 명시적 실패/거절 상태)
# ======================================================
FAILURE_PATTERNS = [
    "인식하지 못했습니다",
    "인식할 수 없습니다",
    "이해하지 못했습니다",
    "이해할 수 없습니다",
    "요청을 처리할 수 없습니다",
    "오류가 발생했습니다",
]

# ======================================================
# 예외/특수 입력 케이스 정의
# ======================================================
EXCEPTION_CASES = [
    dict(name="특수문자 입력", question="!@#$%^&*()_+{}|:<>?~`"),
    dict(name="이모지 입력", question="😀🚀🌟🔥🎉"),
    dict(
        name="링크 요청 질문",
        question="OpenAI 공식 홈페이지 URL을 알려줘.",
        require_link=True,  # 키워드 속성 제거, 링크 형식(요소) 필수 여부만 추가
    ),
    dict(
        name="목록(리스트) 형태 입력",
        question="다음 목록의 공통점을 알려줘.\n1. 사과\n2. 바나나\n3. 오렌지",
    ),
    dict(
        name="링크 형식 질문",
        question="https://www.google.com 이 링크는 어디로 연결되어 있는가? 간략하게 말해줘",
    ),
    dict(
        name="이메일 형식 질문",
        question="test.account@example.com 은 이메일 주소 형식이 맞나요? 단답형으로 대답해줘.",
    ),
    dict(
        name="전화번호 형식 질문",
        question="010-1234-5678 이 번호가 유효한 휴대폰 번호 형식이니? 단답형으로 대답해줘.",
    ),
    dict(
        name="날짜 형식 (yyyy-mm-dd)",
        question="2024-12-25 은 무슨 요일이야?",
        required_answer="수요일",
    ),
    dict(name="날짜 형식 (yyyy/mm/dd)", question="2026/12/25까지 며칠 남았나?"),
    dict(
        name="날짜 형식 (yyyy.mm.dd)",
        question="2023.12.25 몇 년도인가?",
    ),
    dict(
        name="날짜 형식 (yyyy년mm월dd일)",
        question="2024년 12월 25일은 어떤 날 인가?",
    ),
    dict(name="날짜 형식 (yyyymmdd)", question="20241222 몇 월 인가?"),
]


@pytest.mark.parametrize(
    "case", EXCEPTION_CASES, ids=[c["name"] for c in EXCEPTION_CASES]
)
def test_exception_handling(module_setup_and_login, case):
    """
    [TC_008] 예외/특수 형식 입력에 대한 '입력~응답 파이프라인' 절차 검증
    """
    chat = ChatPage(module_setup_and_login)
    name = case["name"]
    question = case["question"]
    required_answer = case.get("required_answer")
    positive_keywords = case.get("positive_keywords")
    require_link = case.get("require_link")  # 새로 추가된 플래그

    print(f"\n▶ [{name}] 진행 중...")

    # 1단계: 입력창 검증
    chat.input_question(question)
    assert chat.get_input_value() == question, (
        f"[{name}] 1단계 실패: 입력창 텍스트 오류"
    )

    # 2단계: 질문 전송
    chat.click_send_button()

    # 3단계: 응답 대기 (POM으로 옮겨진 재시도 로직 사용)
    try:
        chat.wait_response_complete()
    except TimeoutException:
        # 1분 초과로 인한 타임아웃 발생 시, 일반 Fail과 구분되도록 [TIMEOUT] 명시
        pytest.fail(
            f"[{name}] 3단계 실패 - [TIMEOUT] AI 응답 로딩이 1분(SLA)을 초과했습니다."
        )
    except Exception as e:
        pytest.fail(f"[{name}] 3단계 실패 - 응답 대기 중 알 수 없는 오류 발생: {e}")

    # 4단계: 응답 도착 및 내용 검증
    response_text = chat.get_last_response()
    assert response_text and response_text.strip(), (
        f"[{name}] 4단계 실패: 응답 내용이 비어 있습니다."
    )

    matched_failure = next((p for p in FAILURE_PATTERNS if p in response_text), None)
    assert matched_failure is None, (
        f"[{name}] 4단계 실패: 명시적 실패 상태 반환 ('{matched_failure}')"
    )

    if required_answer:
        assert required_answer in response_text, f"[{name}] 4단계 실패: 기대 정답 누락"

    if positive_keywords:
        assert any(k in response_text for k in positive_keywords), (
            f"[{name}] 4단계 실패: 필수 텍스트 키워드 누락"
        )

    # ▶ 수정된 목적: 클릭 가능한 하이퍼링크 존재 여부 검증
    if require_link:
        # 응답 말풍선에서 실제 a 태그의 href 속성들을 추출 (POM에 추가해야 함)
        links = chat.get_last_response_links()

        # 키워드 확인 없이, 단순히 링크 요소(a 태그)가 1개 이상 존재하는지만 검증
        assert len(links) > 0, (
            f"[{name}] 4단계 실패: 화면에 클릭 가능한 하이퍼링크(a 태그)가 렌더링되지 않았습니다."
        )

    time.sleep(1)
