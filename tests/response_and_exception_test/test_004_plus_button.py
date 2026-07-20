import pytest
import time
from src.pages.chat_page import ChatPage

# 테스트 데이터: 지정하신 폴더명과 확장자 적용
TEST_DATA = {
    "이미지 생성": {"type": "image", "question": "강아지 일러스트 생성해줘."},
    "웹 검색": {"type": "web", "question": "강아지의 종류를 알려줘"},
    "파일 업로드": {"type": "file", "path": "test_004_upload_data/test_image.png"},
}


def test_plus_button_features(setup_and_login):
    driver = setup_and_login
    chat = ChatPage(driver)

    print("\n" + "=" * 60)
    print(" [TC_004] '+ 버튼' 기능 검증 (이미지/검색/업로드) ")
    print("=" * 60)

    for feature, data in TEST_DATA.items():
        print(f"\n▶ [{feature}] 기능 테스트 시작")

        # 1) + 버튼 클릭
        chat.click_plus_button()
        time.sleep(1)  # 메뉴 표시 대기

        # 2) 각 메뉴 선택
        if data["type"] == "image":
            chat.click_image_generate_menu()
            chat.wait_image_mode()
        elif data["type"] == "web":
            chat.click_web_search_menu()
        elif data["type"] == "file":
            chat.click_file_upload_menu()
            chat.upload_file(data["path"])

        # 기능 선택 후 전송 전 1.5초 대기 (눈으로 확인 가능)
        print(f"  [!] {feature} 선택 완료, 전송 전 1.5초 대기 중...")
        time.sleep(1.5)

        # 3) 질문 입력 및 전송
        if data["type"] != "file":
            chat.input_question(data["question"])

        chat.click_send_button()
        chat.wait_response_complete()

        # 4) 결과 검증
        if data["type"] == "image":
            assert chat.is_image_created(), "이미지 생성 실패"
        elif data["type"] == "file":
            # [최종 검증] 업로드한 파일명이 화면에 존재하는지 확인
            file_name = data["path"].split("/")[-1]
            assert chat.is_specific_image_created(file_name), (
                f"{file_name} 파일이 화면에 보이지 않습니다."
            )
        else:
            answer = chat.get_last_response()
            assert answer, f"{feature} 응답 없음"

        print(f"  [✓] [{feature}] 기능 PASS")

    print("\n🎉 모든 '+' 버튼 기능 테스트가 성공했습니다. 🎉")
