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
    titles = history_page.history_titles()
    if len(titles) < delete_count:
        pytest.fail(
            f"화면에서 찾은 히스토리는 {len(titles)}개입니다. "
            f"요청한 {delete_count}개를 삭제할 수 없습니다."
        )

    # 화면에 표시된 순서의 앞쪽 항목부터 요청한 개수만큼 삭제합니다.
    targets = titles[:delete_count]
    print("\n삭제 대상:")
    for title in targets:
        print(f"- {title}")

    print()
    for index, title in enumerate(targets, start=1):
        print(f"[DELETE {index}/{len(targets)}] {title}")
        history_page.delete_history(title)

    # 모든 삭제가 끝난 뒤 한 번만 서비스 루트로 이동해 영구 반영 여부를 확인합니다.
    # 항목마다 재접속하면 가상 스크롤 목록이 반복 렌더링되어 stale 요소가 발생할 수 있습니다.
    print("\n[VERIFY] 재접속 후 삭제 상태 확인")
    history_page.open()
    for title in targets:
        assert not history_page.history_item(title), (
            f"재접속 후 삭제한 히스토리가 다시 나타났습니다: {title}"
        )
    print(f"[PASS] 히스토리 {len(targets)}개 삭제 완료")
