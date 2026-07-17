import os

import pytest

from src.utils.history_data import unique_history_message


def test_history_can_be_deleted(history_page):
    message = unique_history_message("history_delete_")
    history_key = message

    history_page.open()
    history_page.send_message(message)
    history_page.wait_for_message(message)
    history_page.wait_for_history(history_key)

    history_page.delete_history(history_key)
    assert not history_page.history_item(history_key)

    history_page.refresh()
    assert not history_page.history_item(history_key)


def test_delete_histories_by_count(history_page):
    raw_count = os.getenv("HISTORY_DELETE_COUNT")
    if raw_count is None:
        raw_count = input("삭제할 자동화 히스토리 개수를 입력하세요: ").strip()

    try:
        delete_count = int(raw_count)
    except ValueError:
        pytest.fail("삭제 개수는 숫자로 입력해 주세요.")

    if delete_count <= 0:
        pytest.fail("삭제 개수는 1 이상이어야 합니다.")

    history_page.open()
    titles = history_page.automation_history_titles()
    if len(titles) < delete_count:
        pytest.fail(
            f"화면에서 찾은 자동화 히스토리는 {len(titles)}개입니다. "
            f"요청한 {delete_count}개를 삭제할 수 없습니다."
        )

    targets = titles[:delete_count]
    for title in targets:
        history_page.delete_history(title)

    history_page.refresh()
    for title in targets:
        assert not history_page.history_item(title), (
            f"새로고침 후 삭제한 히스토리가 다시 나타났습니다: {title}"
        )
