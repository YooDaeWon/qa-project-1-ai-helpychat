import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage


# =====================================================
# 로그인 기능 시연
# =====================================================
def main():
    driver = get_driver()

    try:
        print("=" * 70)
        print("자동화 시연: AI 헬피챗 로그인 기능")
        print("=" * 70)

        print("\n▶ 사이트 접속 및 로그인 진행 중...")
        login = LoginPage(driver)

        login.login()
        print("▶ 로그인 완료! 채팅 화면 진입 대기 중...")
        chat = ChatPage(driver)

        chat.get_input_box()

        print("\n" + "=" * 70)
        print("로그인 성공 및 화면 진입 완료 (PASS)")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print("로그인 시연 중 오류 발생 (FAIL)")
        print("=" * 70)
        print(e)
    finally:
        print("\n(브라우저가 열려 있습니다. 동작을 확인해 보세요.)")
        input("시연을 종료하고 창을 닫으려면 Enter를 누르세요...")

        driver.quit()


if __name__ == "__main__":
    main()
