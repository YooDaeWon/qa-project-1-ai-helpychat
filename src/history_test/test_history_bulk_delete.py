import os

import pytest
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# 기존 test_history.py는 수정하지 않고 필요한 기능만 가져옵니다.
from test_history import (
    CHAT_INPUTS,
    CHAT_READY_TIMEOUT,
    PASSWORD,
    URL,
    delete_history,
    driver,
    first_visible,
    history_item,
    login,
    normalized,
    wait_visible,
)


AUTOMATION_HISTORY_PREFIXES = (
    "히스토리검증",
    "히스토리재로그인검증",
    "히스토리삭제검증",
)


def automation_history_titles(browser):
    """화면에 보이는 자동화 히스토리 제목을 위에서부터 반환합니다."""
    width = browser.execute_script("return window.innerWidth")
    candidates_by_title = {}

    for element in browser.find_elements(
        By.CSS_SELECTOR,
        "a, button, [role='button'], li",
    ):
        try:
            if not element.is_displayed():
                continue

            title = normalized(element.text)
            rect = element.rect
            if not title.startswith(AUTOMATION_HISTORY_PREFIXES):
                continue
            if rect.get("x", 0) >= width * 0.45:
                continue

            area = rect.get("width", 0) * rect.get("height", 0)
            if area <= 0:
                continue

            existing = candidates_by_title.get(title)
            if not existing or area < existing[0]:
                candidates_by_title[title] = (
                    area,
                    rect.get("y", 0),
                    title,
                )
        except StaleElementReferenceException:
            pass

    return [
        item[2]
        for item in sorted(
            candidates_by_title.values(),
            key=lambda item: item[1],
        )
    ]


def test_delete_histories_by_count(driver):
    """입력받은 개수만큼 자동화 히스토리를 위에서부터 삭제합니다."""
    raw_count = os.getenv("HISTORY_DELETE_COUNT")
    if raw_count is None:
        raw_count = input("삭제할 자동화 히스토리 개수를 입력하세요: ").strip()

    try:
        delete_count = int(raw_count)
    except ValueError:
        pytest.fail("삭제 개수는 숫자로 입력해 주세요.")

    if delete_count <= 0:
        pytest.fail("삭제 개수는 1 이상이어야 합니다.")

    driver.get(URL)
    WebDriverWait(driver, 30).until(
        lambda current: (
            current.find_elements(*PASSWORD) or first_visible(current, CHAT_INPUTS)
        )
    )
    login(driver)
    wait_visible(driver, CHAT_INPUTS, CHAT_READY_TIMEOUT)

    titles = automation_history_titles(driver)
    if len(titles) < delete_count:
        pytest.fail(
            f"화면에서 찾은 자동화 히스토리는 {len(titles)}개입니다. "
            f"요청한 {delete_count}개를 삭제할 수 없습니다."
        )

    targets = titles[:delete_count]
    print("\n삭제 대상:")
    for title in targets:
        print(f"- {title}")

    for index, title in enumerate(targets, start=1):
        print(f"\n[DELETE {index}/{delete_count}] {title}")
        delete_history(driver, title)

    driver.refresh()
    wait_visible(driver, CHAT_INPUTS, CHAT_READY_TIMEOUT)

    for title in targets:
        assert not history_item(driver, title), (
            f"새로고침 후 삭제한 히스토리가 다시 나타났습니다: {title}"
        )

    print(f"\n[PASS] 자동화 히스토리 {delete_count}개 삭제 완료")
