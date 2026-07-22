import pytest
from src.pages.chat_page import ChatPage


def test_context_retention(setup_and_login):
    """
    [TC_006] 멀티턴 대화 문맥 유지 및 이전 정보 기억 테스트

    검증 항목:
    1. 여러 번의 연속 대화 후 이전 퍼즐 단서 유지 여부
    2. 복잡한 물리적 조건과 진술의 모순 관계 기억 여부
    3. 장시간 대화 이후에도 문맥 연결 및 최종 범인 추론 가능 여부

    테스트 흐름:
    - 탐정 역할 부여 및 자정 금고 도난 사건 단서 순차 제공 (10턴)
    - 진술과 물리적 조건의 모순 조합
    - 마지막 질문에서 진범(직업) 추론 결과 검증
    """

    driver = setup_and_login
    chat = ChatPage(driver)

    questions = [
        "너는 지금부터 탐정이다. 내가 사건의 단서들을 하나씩 말해줄 테니 '확인'이라고만 대답해.",
        "어느 날 자정, 저택 서재에서 금고가 털리는 사건이 발생했어.",
        "제일 먼저 달려온 집사는 '범인이 서재 창문으로 뛰어내려 도망치는 것을 보았다'고 진술했어.",
        "하지만 이 저택의 서재 창문은 바깥쪽에서 두꺼운 철창살로 완전히 용접되어 있어서, 사람이 통과하는 것은 절대 불가능해.",
        "정원사는 '사건 당시 1층 거실 시계가 정확히 자정을 가리키고 있었다'고 증언했어.",
        "저택의 거실 시계는 평소에도 항상 30분 빠르게 고장 나 있는 상태였어.",
        "가정부는 '범인이 도망칠 때 바닥에 파란색 유리 조각을 흘렸다'고 말했어.",
        "저택 내부에 파란색 유리로 된 물건은 2층 욕실의 거울 외에는 존재하지 않아.",
        "그런데 사건 발생 시각, 2층 욕실 거울은 이미 완벽하게 깨끗한 온전한 상태였어.",
        "즉, 사건 현장과 관련된 목격자들의 진술 중 최소 2개 이상은 명백한 거짓(모순)이야.",
        "단서들을 종합할 때 범인은 누구야? 직업만 딱 한 단어로 대답해.",
    ]

    print("\n" + "=" * 60)
    print(" [TC_006] 멀티턴 대화 문맥 유지 테스트 시작 ")
    print("=" * 60)

    # 1. 연속 질문 진행
    for i, question in enumerate(questions):
        print(f"\n▶ 질문 {i + 1}: {question}")

        chat.input_question(question)
        chat.click_send_button()

        # AI 응답 완료까지 대기 (config.py의 AI_RESPONSE_TIMEOUT 적용)
        chat.wait_response_complete()

        response = chat.get_last_response()

        if response:
            print(f"▷ 응답 완료 (길이: {len(response)}자)")
        else:
            print("▷ 응답 없음")

    # 2. 마지막 응답 검증
    final_response = chat.get_last_response()

    print("\n" + "=" * 60)
    print("[최종 응답 확인]")
    print(final_response)
    print("=" * 60)

    assert final_response, "최종 응답이 존재하지 않습니다."

    # 진범(집사) 도출 여부 검증
    expected_answer = "집사"

    assert expected_answer in final_response, (
        f"\n[문맥 유지 검증 실패]\n"
        f"기대 정답: {expected_answer}\n"
        f"실제 최종 응답:\n{final_response}"
    )

    print("🎉 문맥 유지 검증 PASS: AI가 이전 대화의 문맥을 올바르게 유지했습니다.")
