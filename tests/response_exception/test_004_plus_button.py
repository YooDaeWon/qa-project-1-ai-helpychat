import pytest
import time
from src.pages.chat_page import ChatPage

# 테스트 데이터: 지정하신 폴더명과 확장자 적용
TEST_CASES = [
    dict(
        name="이미지 생성",
        type="image",
        question="단순한 사과 모양의 미니멀한 빨간색 벡터 아이콘, 하얀색 배경",
    ),
    dict(
        name="웹 검색",
        type="web",
        question="이번 주 넷플릭스 대한민국 TOP 10 영화 1위가 뭐야? 간략하게 말해줘",
    ),
    dict(
        name="파일 업로드",
        type="file",
        path="test_004_upload_data/test_image.png",
    ),
]


@pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
def test_plus_button_features(module_setup_and_login, case):
    """
    [TC_004] '+ 버튼' 기능 검증 (이미지/검색/업로드)

    - 브라우저(세션)는 파일 전체에서 1개만 생성/유지 (module_setup_and_login)
    - 각 기능(이미지 생성/웹 검색/파일 업로드) 케이스는 parametrize로 분리되어
      개별 테스트로 결과가 집계됨
    """

    driver = module_setup_and_login
    chat = ChatPage(driver)

    feature = case["name"]
    data_type = case["type"]

    print(f"\n▶ [{feature}] 기능 테스트 시작")

    # 1) + 버튼 클릭
    chat.click_plus_button()
    time.sleep(1)  # 메뉴 표시 대기

    # 2) 각 메뉴 선택
    if data_type == "image":
        chat.click_image_generate_menu()
        chat.wait_image_mode()
    elif data_type == "web":
        chat.click_web_search_menu()
    elif data_type == "file":
        chat.click_file_upload_menu()
        chat.upload_file(case["path"])

    # 기능 선택 후 전송 전 1.5초 대기 (눈으로 확인 가능)
    print(f"  [!] {feature} 선택 완료, 전송 전 1.5초 대기 중...")
    time.sleep(1.5)

    # 3) 질문 입력 및 전송
    if data_type != "file":
        chat.input_question(case["question"])

    before_count = chat.response_count()
    chat.click_send_button()
    chat.wait_response_complete(before_count)

    # 4) 결과 검증
    if data_type == "image":
        assert chat.is_image_created(), f"[{feature}] 이미지 생성 실패"
    elif data_type == "file":
        # [최종 검증] 업로드한 파일명이 화면에 존재하는지 확인
        file_name = case["path"].split("/")[-1]
        assert chat.is_specific_image_created(file_name), (
            f"[{feature}] {file_name} 파일이 화면에 보이지 않습니다."
        )
    else:
        answer = chat.get_last_response()
        assert answer, f"[{feature}] 응답 없음"

    print(f"  [✓] [{feature}] 기능 PASS")
