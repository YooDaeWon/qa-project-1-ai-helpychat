from __future__ import annotations

import time
from datetime import datetime

import pytest
from selenium import webdriver

from src.config.config import Settings
from src.core.login import login_if_needed
from src.pages.agent_delete_page import AgentDeletePage
from src.pages.agent_list_page import AgentListPage
from src.utils.result_writer import DeleteResultWriter


def get_delete_mode_name(delete_mode: str) -> str:
    if delete_mode == "automation":
        return "자동 생성 테스트용 에이전트만 삭제"
    return "전체 삭제"


@pytest.mark.delete_agent
def test_delete_agents(
    driver: webdriver.Chrome,
    settings: Settings,
    delete_mode: str,
) -> None:
    """선택한 방식에 맞는 에이전트를 목록에서 모두 삭제하고 결과를 검증합니다."""
    writer = DeleteResultWriter(settings.artifacts_dir)

    driver.get(settings.base_url)
    print("테스트 사이트 접속 완료")
    login_if_needed(driver, settings)

    list_page = AgentListPage(driver, settings)
    delete_page = AgentDeletePage(driver, timeout=settings.default_wait_time)
    list_page.open()

    print("\n" + "=" * 60)
    print("내 에이전트 삭제 테스트 시작")
    print(f"삭제 방식: {get_delete_mode_name(delete_mode)}")
    print("=" * 60)

    deleted_agents: list[str] = []
    failed_agents: list[tuple[str, str]] = []
    excluded_hrefs: set[str] = set()

    while True:
        if list_page.get_visible_private_panel() is None:
            list_page.open()

        target_agent = list_page.get_target_agent_info(
            delete_mode=delete_mode,
            excluded_hrefs=excluded_hrefs,
        )

        if target_agent is None:
            break

        agent_title = target_agent["title"]
        absolute_href = target_agent["absolute_href"]
        relative_href = target_agent["relative_href"]

        print("\n" + "-" * 60)
        print(f"삭제 대상 에이전트: {agent_title}")
        print(f"에이전트 링크: {absolute_href}")
        print("-" * 60)

        try:
            delete_page.delete_single_agent(list_page, target_agent)
            deleted_agents.append(agent_title)
            writer.write(agent_title, "PASS", "삭제 성공")
            print(f"삭제 성공: {agent_title}")
            time.sleep(0.5)
        except Exception as error:
            error_message = str(error)
            failed_agents.append((agent_title, error_message))
            excluded_hrefs.add(relative_href)
            writer.write(agent_title, "FAIL", error_message)
            print(f"삭제 실패: {agent_title}")
            print(f"오류 내용: {error_message}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = (
                settings.artifacts_dir
                / "failures"
                / f"deleteagent_failure_{timestamp}.png"
            )
            try:
                delete_page.save_screenshot(screenshot_path)
                print(f"실패 화면 저장 완료: {screenshot_path}")
            except Exception as screenshot_error:
                print(f"실패 화면 저장 실패: {screenshot_error}")

    if not deleted_agents and not failed_agents:
        writer.write_no_agent(delete_mode)

    print("\n" + "=" * 60)
    print("에이전트 삭제 테스트 결과")
    print(f"삭제 방식: {get_delete_mode_name(delete_mode)}")
    print(f"삭제 성공: {len(deleted_agents)}개")
    print(f"삭제 실패: {len(failed_agents)}개")

    if deleted_agents:
        print("- 삭제 성공 에이전트")
        for agent_title in deleted_agents:
            print(f"  - {agent_title}")

    if failed_agents:
        print("- 삭제 실패 에이전트")
        for agent_title, error_message in failed_agents:
            print(f"  - {agent_title}: {error_message}")

    print(f"결과 CSV: {writer.path}")
    print("=" * 60)

    assert not failed_agents, (
        "삭제 실패 에이전트가 있습니다: "
        + ", ".join(title for title, _ in failed_agents)
    )
