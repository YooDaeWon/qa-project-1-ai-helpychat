from src.core.login import login_if_needed
from src.pages.main_page import MainPage
from src.utils.history_data import unique_history_message


def test_history_survives_relogin(history_page):
    """로그아웃 후 다시 로그인해도 생성한 히스토리가 유지되는지 검증합니다."""
    message = unique_history_message("history_relogin_")
    history_key = message

    # 준비: 재로그인 후 찾을 수 있도록 고유한 메시지로 히스토리를 생성합니다.
    print(f"\n[CREATE] 히스토리 생성: {history_key}")
    history_page.open()
    history_page.send_message(message)
    history_page.wait_for_message(message)
    history_page.wait_for_history(history_key)

    # 실행: 현재 계정에서 로그아웃한 뒤 동일한 테스트 계정으로 다시 로그인합니다.
    print("[RELOGIN] 로그아웃 후 테스트 계정으로 다시 로그인")
    MainPage(history_page.driver).logout()
    login_if_needed(history_page.driver)
    history_page.wait_until_ready()

    # 검증: 기존 히스토리를 다시 열었을 때 원래 메시지가 표시되어야 합니다.
    print(f"[VERIFY] 재로그인 후 히스토리 확인: {history_key}")
    history_page.open_history(history_key)
    history_page.wait_for_message(message)
    print("[PASS] 재로그인 후 히스토리 유지 확인 완료")
