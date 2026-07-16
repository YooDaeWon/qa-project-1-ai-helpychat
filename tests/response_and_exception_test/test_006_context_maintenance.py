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
# TC006
# 문맥 검증 - 문맥 유지 (하나의 주제로 10회 이상 질문)
# =====================================================
def main():
    driver = get_driver()

    # 테스트에 사용할 별자리 관련 연속 질문 리스트 (총 11개)
    # 첫 질문에서 주어진 정보(내 생일)와 주제(별자리)를
    # 마지막 질문에서 잊지 않고 답변하는지 검증합니다.
    questions = [
        "안녕! 오늘은 별자리에 대해 이야기해보자. 내 생일은 11월 15일이야. 내 별자리는 뭐야?",  # 1
        "방금 말해준 내 별자리의 성격적인 특징은 어떤 것들이 있어?",  # 2
        "그 별자리를 상징하는 수호 행성은 무엇일까?",  # 3
        "내 별자리와 가장 찰떡궁합인 별자리는 어떤 별자리야?",  # 4
        "반대로 내 별자리와 잘 맞지 않는 별자리는 무엇일까?",  # 5
        "내 별자리에 얽힌 유명한 그리스 로마 신화나 전설이 있어?",  # 6
        "이 별자리를 가진 사람들에게 추천할 만한 직업이나 취미는 뭐가 있을까?",  # 7
        "나에게 행운을 가져다주는 색깔이나 행운의 숫자는 뭐야?",  # 8
        "실제로 밤하늘에서 내 별자리를 찾으려면 어느 계절이 가장 좋아?",  # 9
        "그 별자리에서 가장 밝게 빛나는 별의 이름은 무엇인지 알려줘.",  # 10
        "자, 이제 내 질문에 답해봐. 우리가 지금까지 무슨 별자리에 대해서 이야기하고 있었지? 그리고 내가 처음에 말했던 내 생일은 언제야?",  # 11 (검증용)
    ]
    try:
        print("=" * 70)
        print("TC006 예외 질문 입력 '맥락검증 - 문맥 유지' 테스트")
        print("=" * 70)
        # -------------------------------------------------
        # 로그인
        # -------------------------------------------------
        login = LoginPage(driver)
        login.login()
        chat = ChatPage(driver)

        # 입력창이 나타날 때까지 대기
        chat.get_input_box()

        print("\n[1/1]")
        print("문맥 유지 기능 테스트 시작 (주제: 별자리, 총 11회 질문)")
        # -------------------------------------------------
        # 10회 이상 질문 반복 입력 및 응답 대기
        # -------------------------------------------------
        for i, question in enumerate(questions):
            print(f"\n▶ 질문 {i + 1} : {question}")

            # 질문 입력 및 전송
            chat.input_question(question)
            time.sleep(1)  # 입력이 완전히 반영될 때까지 짧은 대기
            chat.click_send_button()

            # AI 응답 대기
            print("▷ 응답 대기 중...")
            chat.wait_response_complete()

            # 마지막 응답 텍스트 가져오기
            response = chat.get_last_response()

            # 로그창이 너무 길어지는 것을 방지하기 위해 50자까지만 출력
            short_response = (
                response[:50].replace("\n", " ") + "..."
                if len(response) > 50
                else response.replace("\n", " ")
            )
            print(f"▷ 응답 {i + 1} 완료 : {short_response}")

            time.sleep(2)  # 다음 질문을 입력하기 전 텀을 둠

        # -------------------------------------------------
        # 결과 확인 (마지막 11번째 응답 검증)
        # -------------------------------------------------
        print("\n▶ 최종 응답 검증 단계")

        final_response = chat.get_last_response()

        # 11월 15일은 '전갈자리'입니다.
        # 마지막 응답에 '전갈자리'와 '11월 15일'이 모두 포함되어 있는지 확인하여 문맥 유지를 검증합니다.
        if "전갈자리" in final_response and "11월 15일" in final_response:
            print("응답 : 11월 15일 및 전갈자리 키워드 확인 완료")
            print("검증 결과 : PASS (문맥 유지 확인됨)")

            print("\n" + "=" * 70)
            print("TC006 PASS")
            print("=" * 70)
        else:
            print("응답 : 필수 키워드를 잃어버렸습니다.")
            print(f"실제 마지막 응답: {final_response}")
            print("검증 결과 : FAIL (이전 문맥을 잃어버림)")

            print("\n" + "=" * 70)
            print("TC006 FAIL")
            print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print("TC006 FAIL")
        print("=" * 70)
        print(e)
    finally:
        input("\n종료하려면 Enter를 누르세요...")
        driver.quit()


if __name__ == "__main__":
    main()
