from __future__ import annotations

import time

import pytest
from selenium import webdriver

from src.config.config import Settings
from src.core.login import login_if_needed
from src.pages.agent_builder_page import AgentBuilderPage
from src.pages.agent_list_page import AgentListPage
from src.utils.agent_data import make_test_agent_data


@pytest.mark.create_agent
def test_create_agents(
    driver: webdriver.Chrome,
    settings: Settings,
    create_count: int,
) -> None:
    """요청한 개수만큼 에이전트를 생성하고 목록 및 카드 이동을 검증합니다."""
    driver.get(settings.new_chat_url)
    print("테스트 사이트 접속 완료")
    login_if_needed(driver, settings)

    list_page = AgentListPage(driver, settings)
    builder_page = AgentBuilderPage(driver, timeout=settings.page_wait_time)
    created_agents: list[str] = []

    for index in range(1, create_count + 1):
        data = make_test_agent_data(index)

        print("\n" + "=" * 60)
        print(f"{index}/{create_count}번째 에이전트 생성 시작")
        print(f"이번 실행 기준 자동화 테스트 회차: {data.test_count:03d}회차")
        print(f"생성할 에이전트 이름: {data.name}")
        print("=" * 60)

        list_page.open()
        list_page.click_create_agent_link()

        builder_page.verify_builder_tabs_displayed()
        builder_page.open_settings_tab()
        builder_page.run_pre_input_checks()
        builder_page.fill_agent_form(data)
        builder_page.check_private_scope()
        builder_page.wait_until_ready_to_create()
        builder_page.click_create_button()
        builder_page.wait_for_created_agent(data.name)

        created_agents.append(data.name)
        print(f"{index}/{create_count}번째 에이전트 생성 직후 검증 성공: {data.name}")
        time.sleep(1)

    found_agents = list_page.verify_agent_names(created_agents)
    assert found_agents == set(created_agents)

    list_page.click_agent_card(created_agents[-1])

    print("\n" + "=" * 60)
    print("전체 에이전트 생성 결과: PASS")
    print(f"요청 개수: {create_count}개")
    print(f"생성 성공: {len(created_agents)}개")
    print("내 에이전트 목록 최종 재검증: PASS")
    print("생성 카드 클릭 검증: PASS")
    print("- 생성된 에이전트 목록")
    for name in created_agents:
        print(f"  - {name}")
    print("=" * 60)
