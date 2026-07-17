from datetime import datetime


def unique_history_message(prefix):
    """동일 실행 안에서 겹치지 않는 히스토리 테스트 메시지를 만듭니다."""
    return prefix + datetime.now().strftime("%Y%m%d_%H%M%S")
