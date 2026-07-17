from datetime import datetime

from src.config.config import SCREENSHOT_DIR
from src.utils.history_data import unique_history_message


def test_chat_message_saved_after_refresh(history_page):
    """새로고침 후에도 생성한 대화와 히스토리가 유지되는지 검증합니다."""
    message = unique_history_message("history_save_")
    history_key = message
    SCREENSHOT_DIR.mkdir(exist_ok=True)

    try:
        # 준비: 고유한 메시지를 전송하고 히스토리가 생성될 때까지 기다립니다.
        print(f"\n[CREATE] 히스토리 생성: {history_key}")
        history_page.open()
        history_page.send_message(message)
        history_page.wait_for_message(message)
        history_page.wait_for_history(history_key)

        # 검증: 새로고침 후 해당 히스토리를 다시 열어 메시지 유지 여부를 확인합니다.
        print(f"[VERIFY] 새로고침 후 히스토리 확인: {history_key}")
        history_page.refresh()
        history_page.open_history(history_key)
        history_page.wait_for_message(message)
        history_page.driver.save_screenshot(
            str(SCREENSHOT_DIR / "history_test_pass.png")
        )
        print("[PASS] 새로고침 후 히스토리 저장 유지 확인 완료")
    except Exception:
        # 실패 당시의 화면을 남겨 UI 상태와 실패 원인을 추적할 수 있게 합니다.
        failure = (
            SCREENSHOT_DIR
            / f"history_test_fail_{datetime.now():%Y%m%d_%H%M%S}.png"
        )
        history_page.driver.save_screenshot(str(failure))
        print(f"[FAIL] 실패 화면 저장: {failure}")
        raise
