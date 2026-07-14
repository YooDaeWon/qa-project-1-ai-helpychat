import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage


# =====================================================
# TC004
# 이미지 생성 기능 테스트
# =====================================================

QUESTION = "잔디밭 위에 앉아 카메라를 바라보며 꼬리를 흔드는 귀여운 작은 강아지 일러스트를 생성해줘."


def main():

    driver = get_driver()

    try:
        print("=" * 70)
        print("TC004 이미지 생성 기능 테스트")
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
        print("이미지 생성 기능 테스트 시작")

        # -------------------------------------------------
        # '+' 버튼 클릭
        # -------------------------------------------------

        print("\n▶ '+' 버튼 클릭")

        chat.click_plus_button()

        print("PASS")

        time.sleep(1)

        # -------------------------------------------------
        # 이미지 생성 메뉴 클릭
        # -------------------------------------------------

        print("\n▶ '이미지 생성' 메뉴 클릭")

        chat.click_image_generate_menu()

        print("PASS")

        time.sleep(1)
        # -------------------------------------------------
        # 이미지 생성 모드 확인
        # -------------------------------------------------

        print("\n▶ 이미지 생성 모드 확인")

        chat.wait_image_mode()

        print("PASS")

        time.sleep(1)
        # -------------------------------------------------
        # 질문 입력
        # -------------------------------------------------

        print("\n질문 :")
        print(QUESTION)

        chat.input_question(QUESTION)

        # -------------------------------------------------
        # 보내기 버튼 클릭
        # -------------------------------------------------

        print("\n▶ 보내기 버튼 클릭")

        chat.click_send_button()

        # -------------------------------------------------
        # 이미지 생성 완료 대기
        # -------------------------------------------------

        print("\n▶ 이미지 생성 중...")

        chat.wait_image_created()

        # -------------------------------------------------
        # 결과 확인
        # -------------------------------------------------

        if chat.is_image_created():
            print("\n응답 : 이미지 생성 완료")

            print("검증 결과 : PASS")

            print("\n" + "=" * 70)
            print("TC004 PASS")
            print("=" * 70)

        else:
            print("\n응답 : 이미지 생성 실패")

            print("검증 결과 : FAIL")

            print("\n" + "=" * 70)
            print("TC004 FAIL")
            print("=" * 70)

    except Exception as e:
        print("\n" + "=" * 70)
        print("TC004 FAIL")
        print("=" * 70)

        print(e)

    finally:
        input("\n종료하려면 Enter를 누르세요...")

        driver.quit()


if __name__ == "__main__":
    main()
