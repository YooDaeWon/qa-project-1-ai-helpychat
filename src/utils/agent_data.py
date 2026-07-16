from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AgentData:
    name: str
    short_description: str
    rule_text: str
    start_conversation: str
    test_count: int


def make_test_agent_data(test_count: int) -> AgentData:
    """실행할 때마다 001회차부터 사용하는 테스트 에이전트 데이터를 생성합니다."""
    now = datetime.now()
    now_for_name = now.strftime("%Y%m%d_%H%M%S")
    now_for_text = now.strftime("%Y-%m-%d %H:%M:%S")

    return AgentData(
        name=f"자동화테스트에이전트_{now_for_name}_{test_count:03d}회차",
        short_description=(
            f"{now_for_text} 기준 Selenium 자동화 테스트 "
            f"{test_count:03d}회차로 생성한 에이전트입니다."
        ),
        rule_text=(
            "이 에이전트는 Selenium 자동화 테스트 검증용으로 생성되었습니다. "
            "사용자의 질문에 친절하고 간단하게 답변합니다."
        ),
        start_conversation=(
            f"안녕하세요. 저는 자동화 테스트 {test_count:03d}회차로 생성된 에이전트입니다."
        ),
        test_count=test_count,
    )
