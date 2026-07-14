import sys
from pathlib import Path

# 프로젝트 루트 경로 설정 (폴더가 달라도 똑같이 동작합니다)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.driver import get_driver
from pages.login_page import LoginPage
from pages.chat_page import ChatPage


# =====================================================
# DEMO TEST
# 로그인 기능 시연
# =====================================================
def main():
    driver = get_driver()

    try:
        print("=" * 70)
        print("🚀 자동화 시연: AI 헬피챗 로그인 기능")
        print("=" * 70)
        # -------------------------------------------------
        # 로그인 수행
        # -------------------------------------------------
        print("\n▶ 사이트 접속 및 로그인 진행 중...")
        login = LoginPage(driver)

        # login_page.py에 구현되어 있는 로그인 로직 실행
        login.login()
        # -------------------------------------------------
        # 로그인 완료 확인 (채팅 화면 진입)
        # -------------------------------------------------
        print("▶ 로그인 완료! 채팅 화면 진입 대기 중...")
        chat = ChatPage(driver)

        # 채팅 입력창이 나타나는 것을 확인하면 로그인이 정상적으로 완료된 것
        chat.get_input_box()

        print("\n" + "=" * 70)
        print("✅ 로그인 성공 및 화면 진입 완료 (PASS)")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 로그인 시연 중 오류 발생 (FAIL)")
        print("=" * 70)
        print(e)
    finally:
        # 보여주기 용도이므로 화면을 확인할 수 있도록 사용자가 Enter를 누를 때까지 창을 유지
        print("\n(브라우저가 열려 있습니다. 동작을 확인해 보세요.)")
        input("시연을 종료하고 창을 닫으려면 Enter를 누르세요...")

        driver.quit()


if __name__ == "__main__":
    main()
