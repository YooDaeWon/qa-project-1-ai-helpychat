from datetime import datetime


def unique_history_message(prefix):
    """테스트 접두사와 현재 시각을 조합해 구분 가능한 히스토리 메시지를 만듭니다."""
    # 테스트별 접두사를 유지해 일반 사용자 히스토리와 자동화 데이터를 구분합니다.
    return prefix + datetime.now().strftime("%Y%m%d_%H%M%S")
