import pytest
from src.pages.chat_page import ChatPage


def test_context_retention(setup_and_login):
    """
    [TC_006] 멀티턴 대화 문맥 유지 및 이전 정보 기억 테스트

    검증 항목:
    1. 여러 번의 연속 대화 후 이전 사용자 정보 유지 여부
    2. 초기 질문의 핵심 정보(생일, 별자리) 기억 여부
    3. 장시간 대화 이후에도 문맥 연결 가능 여부

    테스트 흐름:
    - 첫 질문에서 생일 정보 제공
    - 별자리 관련 연속 대화 진행
    - 마지막 질문에서 초기 정보 기억 여부 검증
    """

    driver = setup_and_login
    chat = ChatPage(driver)

    questions = [
        "안녕! 오늘은 별자리에 대해 이야기해보자. 내 생일은 11월 15일이야. 내 별자리는 뭐야?",
        "방금 말해준 내 별자리의 성격적인 특징은 어떤 것들이 있어? 간략하게 말해줘",
        "그 별자리를 상징하는 수호 행성은 무엇일까? 간략하게 말해줘",
        "내 별자리와 가장 찰떡궁합인 별자리는 어떤 별자리야? 간략하게 말해줘",
        "반대로 내 별자리와 잘 맞지 않는 별자리는 무엇일까? 간략하게 말해줘",
        "내 별자리에 얽힌 유명한 그리스 로마 신화나 전설이 있어? 간략하게 말해줘",
        "이 별자리를 가진 사람들에게 추천할 만한 직업이나 취미는 뭐가 있을까? 간략하게 말해줘",
        "나에게 행운을 가져다주는 색깔이나 행운의 숫자는 뭐야? 간략하게 말해줘",
        "실제로 밤하늘에서 내 별자리를 찾으려면 어느 계절이 가장 좋아? 간략하게 말해줘",
        "그 별자리에서 가장 밝게 빛나는 별의 이름은 무엇인지 알려줘. 간략하게 말해줘",
        "자, 이제 내 질문에 답해봐. 우리가 지금까지 무슨 별자리에 대해서 이야기하고 있었지? 그리고 내가 처음에 말했던 내 생일은 언제야?",
    ]

    print("\n" + "=" * 60)
    print(" [TC_006] 멀티턴 대화 문맥 유지 테스트 시작 ")
    print("=" * 60)

    # 1. 연속 질문 진행
    for i, question in enumerate(questions):
        print(f"\n▶ 질문 {i + 1}: {question}")

        chat.input_question(question)
        chat.click_send_button()

        # AI 응답 완료까지 대기
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

    # 초기 대화 정보 기억 여부 확인
    required_keywords = [
        "전갈자리",
        "11월",
        "15일",
    ]

    missing_keywords = [
        keyword for keyword in required_keywords if keyword not in final_response
    ]

    assert not missing_keywords, (
        f"\n[문맥 유지 검증 실패]\n"
        f"누락된 정보: {missing_keywords}\n"
        f"최종 응답:\n{final_response}"
    )

    print("🎉 문맥 유지 검증 PASS: AI가 이전 대화 정보를 유지하고 있습니다.")
