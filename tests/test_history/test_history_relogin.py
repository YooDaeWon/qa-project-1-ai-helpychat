from src.core.login import login_if_needed
from src.pages.login_page import MainPage
from src.utils.history_data import unique_history_message


def test_history_survives_relogin(history_page):
    message = unique_history_message("history_relogin_")
    history_key = message

    history_page.open()
    history_page.send_message(message)
    history_page.wait_for_message(message)
    history_page.wait_for_history(history_key)

    MainPage(history_page.driver).logout()
    login_if_needed(history_page.driver)
    history_page.wait_until_ready()

    history_page.open_history(history_key)
    history_page.wait_for_message(message)
