import os

import pytest

from src.utils.history_data import unique_history_message


def test_history_can_be_deleted(history_page):
    """히스토리 단건 삭제가 새로고침 후에도 유지되는지 검증합니다."""
    message = unique_history_message("history_delete_")
    history_key = message

    # 준비: 다른 히스토리와 구분되는 테스트 전용 히스토리를 생성합니다.
    print(f"\n[CREATE] 삭제 테스트용 히스토리 생성: {history_key}")
    history_page.open()
    history_page.send_message(message)
    history_page.wait_for_message(message)
    history_page.wait_for_history(history_key)

    # 실행 및 1차 검증: 생성한 히스토리를 삭제하고 목록에서 사라졌는지 확인합니다.
    print(f"[DELETE 1/1] {history_key}")
    history_page.delete_history(history_key)
    assert not history_page.history_item(history_key)

    # 최종 검증: 서비스 루트로 재접속해도 삭제된 히스토리가 복구되지 않아야 합니다.
    print(f"[VERIFY] 재접속 후 삭제 상태 확인: {history_key}")
    history_page.open()
    assert not history_page.history_item(history_key)
    print("[PASS] 히스토리 1개 삭제 완료")


@pytest.mark.history_bulk_delete
def test_delete_histories_by_count(history_page, request):
    """화면에 표시된 히스토리를 지정된 개수만큼 삭제하고 결과를 검증합니다."""
    # 환경변수를 우선 사용하고, 대화형 옵션을 지정한 경우에만 사용자 입력을 받습니다.
    raw_count = os.getenv("HISTORY_DELETE_COUNT")
    if raw_count is None and request.config.getoption(
        "--interactive-history-delete"
    ):
        raw_count = input("삭제할 히스토리 개수를 입력하세요: ").strip()

    # collection 단계에서도 skip하지만 직접 호출되는 상황을 대비해 한 번 더 보호합니다.
    if raw_count is None:
        pytest.skip(
            "삭제 개수 또는 대화형 입력 옵션이 없어 다중 삭제 테스트를 건너뜁니다."
        )

    # 잘못된 값으로 예상하지 않은 항목이 삭제되는 것을 막습니다.
    try:
        delete_count = int(raw_count)
    except ValueError:
        pytest.fail("삭제 개수는 숫자로 입력해 주세요.")

    if delete_count <= 0:
        pytest.fail("삭제 개수는 1 이상이어야 합니다.")

    history_page.open()
    # 자동화 여부와 관계없이 현재 화면에 표시된 모든 히스토리를 수집합니다.
    entries = history_page.history_entries()
    if len(entries) < delete_count:
        pytest.fail(
            f"화면에서 찾은 히스토리는 {len(entries)}개입니다. "
            f"요청한 {delete_count}개를 삭제할 수 없습니다."
        )

    # 화면에 표시된 순서의 앞쪽 항목부터 요청한 개수만큼 삭제합니다.
    targets = entries[:delete_count]
    print("\n삭제 대상:")
    for entry in targets:
        print(f"- {entry['title']}")

    print()
    for index in range(1, delete_count + 1):
        # 삭제할 때마다 최신 DOM의 첫 번째 행을 다시 가져옵니다. 제목이 같아도
        # 서로 다른 행을 순서대로 처리하므로 특정 제목을 잘못 찾아가지 않습니다.
        before_titles = history_page.history_titles()
        current_title = before_titles[0]
        print(f"[DELETE {index}/{delete_count}] {current_title}")
        deleted_title = history_page.delete_history_at_index(0)
        assert deleted_title == current_title

        # 서버에 영구 반영됐는지 매 건 재접속해 확인합니다. 재접속 뒤에는 다음 반복에서
        # 요소를 새로 수집하므로 가상 목록의 stale 요소를 재사용하지 않습니다.
        history_page.open()
        after_titles = history_page.history_titles()
        assert after_titles != before_titles, (
            f"재접속 후 삭제 전 목록이 그대로 복구됐습니다: {current_title}"
        )
        print(f"[VERIFY {index}/{delete_count}] 영구 삭제 확인 완료")

    print(f"[PASS] 히스토리 {delete_count}개 삭제 완료")
