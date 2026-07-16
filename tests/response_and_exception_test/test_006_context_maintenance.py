import pytest
import time
from src.pages.chat_page import ChatPage


def test_context_retention(setup_and_login):
    """
    [TC_006] 문맥 유지 검증 테스트
    - 11회의 연속 질문을 통해 초기 정보(생일)와 주제(별자리)를 기억하는지 확인
    """
    driver = setup_and_login
    chat = ChatPage(driver)

    questions = [
        "안녕! 오늘은 별자리에 대해 이야기해보자. 내 생일은 11월 15일이야. 내 별자리는 뭐야?",
        "방금 말해준 내 별자리의 성격적인 특징은 어떤 것들이 있어?",
        "그 별자리를 상징하는 수호 행성은 무엇일까?",
        "내 별자리와 가장 찰떡궁합인 별자리는 어떤 별자리야?",
        "반대로 내 별자리와 잘 맞지 않는 별자리는 무엇일까?",
        "내 별자리에 얽힌 유명한 그리스 로마 신화나 전설이 있어?",
        "이 별자리를 가진 사람들에게 추천할 만한 직업이나 취미는 뭐가 있을까?",
        "나에게 행운을 가져다주는 색깔이나 행운의 숫자는 뭐야?",
        "실제로 밤하늘에서 내 별자리를 찾으려면 어느 계절이 가장 좋아?",
        "그 별자리에서 가장 밝게 빛나는 별의 이름은 무엇인지 알려줘.",
        "자, 이제 내 질문에 답해봐. 우리가 지금까지 무슨 별자리에 대해서 이야기하고 있었지? 그리고 내가 처음에 말했던 내 생일은 언제야?",
    ]

    print("\n" + "=" * 60)
    print(" [TC_006] 문맥 유지 검증 테스트 시작 ")
    print("=" * 60)

    for i, question in enumerate(questions):
        print(f"\n▶ 질문 {i + 1} : {question}")
        chat.input_question(question)
        chat.click_send_button()
        chat.wait_response_complete()

        response = chat.get_last_response()
        print(f"▷ 응답 완료 (길이: {len(response)}자)")
        time.sleep(2)

    # 최종 검증 단계
    final_response = chat.get_last_response()
    print("\n" + "=" * 60)
    print(f" [최종 응답 확인]:\n{final_response}")
    print("=" * 60)

    # 2. [수정된 검증 로직]
    # 문맥 유지 조건이 모두 포함되어 있는지 확인
    # "전갈자리"라는 단어와, "11월" 그리고 "15일"이라는 단어가 따로 떨어져 있어도 포함만 되어있다면 PASS
    is_pass = ("전갈자리" in final_response) and (
        "11월" in final_response and "15일" in final_response
    )

    # 3. 결과 출력 및 실패 시 상세 메시지
    assert is_pass, (
        f"\n[문맥 유지 검증 실패]\n"
        f" - 확인이 필요한 핵심 정보: '전갈자리', '11월', '15일'\n"
        f" - 실제 응답 확인: 전갈자리({'전갈자리' in final_response}), "
        f"11월({'11월' in final_response}), 15일({'15일' in final_response})\n"
        f" - 전체 응답 내용: {final_response}"
    )

    print("🎉 문맥 유지 검증 PASS: AI가 이전 대화 내용을 정확히 기억하고 있습니다.")
