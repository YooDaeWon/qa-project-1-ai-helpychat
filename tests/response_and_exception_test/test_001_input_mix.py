import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pages.chat_page import ChatPage

# pytest의 파라미터화 기능을 사용하기 위해 리스트 형태로 변경합니다.
TEST_CASES = [
    ("한글만 입력", "안녕하세요"),
    ("영문만 입력", "Hello AI Agent"),
    ("숫자만 입력", "1234567890"),
    ("한/영, 숫자 혼합 입력", "가나다 ABC123 456테스트"),
]


class TestChatInput:
    """채팅 입력 및 응답 관련 테스트 클래스"""

    # @pytest.mark.parametrize를 사용하면 for문을 쓰지 않아도 4개의 케이스를 각각 독립된 테스트로 자동 실행합니다.
    @pytest.mark.parametrize("case_name, test_text", TEST_CASES)
    def test_001_chat_input_types(self, setup_and_login, case_name, test_text):
        """[TC_001] 다양한 입력 유형별 전송 및 응답 테스트"""

        # 0. 준비 (setup_and_login은 드라이버를 켜고 로그인까지 완료해주는 공통 함수입니다)
        driver = setup_and_login
        chat = ChatPage(driver)

        # 1. 질문 입력
        chat.input_question(test_text)

        # 2. 입력값 검증 (if문과 raise 대신 assert 한 줄로 끝냅니다)
        actual = chat.get_input_value()
        assert actual == test_text, (
            f"입력값 불일치 (기대값: {test_text}, 실제값: {actual})"
        )

        # 3. 질문 전송
        chat.send_by_enter()

        # 4. AI 답변 대기 및 검증
        chat.wait_response_complete()
        ai_answer = chat.get_last_response()
        assert ai_answer, "AI 응답을 받지 못했거나 내용이 비어있습니다."

        # 테스트 성공 시 로그에 남길 내용 (pytest 실행 시 -s 옵션을 주면 보입니다)
        print(f"\n[{case_name}] 정상 응답 확인: {ai_answer[:20]}...")
