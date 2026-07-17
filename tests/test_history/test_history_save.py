from datetime import datetime

from src.config.config import SCREENSHOT_DIR
from src.utils.history_data import unique_history_message


def test_chat_message_saved_after_refresh(history_page):
    message = unique_history_message("history_save_")
    history_key = message
    SCREENSHOT_DIR.mkdir(exist_ok=True)

    try:
        history_page.open()
        history_page.send_message(message)
        history_page.wait_for_message(message)
        history_page.wait_for_history(history_key)

        history_page.refresh()
        history_page.open_history(history_key)
        history_page.wait_for_message(message)
        history_page.driver.save_screenshot(
            str(SCREENSHOT_DIR / "history_test_pass.png")
        )
    except Exception:
        failure = (
            SCREENSHOT_DIR
            / f"history_test_fail_{datetime.now():%Y%m%d_%H%M%S}.png"
        )
        history_page.driver.save_screenshot(str(failure))
        raise
