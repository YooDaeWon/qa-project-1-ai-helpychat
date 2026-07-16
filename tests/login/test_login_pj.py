# -*- coding: utf-8 -*-
"""로그인 자동화 테스트.

셀렉터와 페이지 조작은 src/pages/login_page.py의 LoginUiPage(Page Object)에 있고,
이 파일에는 '무엇을 검증하는지'만 남긴다.
"""
import logging
from urllib.parse import urlparse

import pytest

from src.pages.login_page import (
    MSG_INVALID_FORMAT,
    MSG_MISMATCH,
    MSG_PW_MIN_LENGTH,
    MSG_SERVER_ERROR,
    LoginUiPage,
    MainPage,
    login,
)

log = logging.getLogger(__name__)


@pytest.fixture
def page(shared_driver, credentials):
    """한국어 로그인 페이지가 열린 상태의 Page Object (공유 브라우저 사용)."""
    return LoginUiPage(shared_driver, credentials["url"]).open()


@pytest.fixture
def logged_in_driver(driver, credentials):
    """로그인이 완료된 브라우저를 제공 (TID 23, 24 세션 유지 테스트용)."""
    login(driver, credentials["url"], credentials["email"], credentials["password"])
    return driver


# ══════════════════════════════════════════════════════════════
# 로그인 성공 / 세션 유지 / 로그아웃 (TID 41, 23, 24, 58, 59)
# ══════════════════════════════════════════════════════════════


def test_tid41_login_success(driver, credentials):
    """TID 41: 올바른 이메일/비밀번호 -> 로그인 성공 (프로필 아이콘 노출)"""
    login(driver, credentials["url"], credentials["email"], credentials["password"])
    assert MainPage(driver).profile_icon().is_displayed()


def test_tid23_back_button_keeps_login(logged_in_driver):
    """TID 23: 로그인 완료 후 뒤로가기 -> 로그인 상태 유지 (로그인 페이지로 안 감)"""
    logged_in_driver.back()
    icon = MainPage(logged_in_driver).wait_logged_in()
    assert icon.is_displayed(), "[TID 23] 뒤로가기 후 프로필 아이콘이 사라짐 (로그인 풀림)"


def test_tid24_refresh_keeps_login(logged_in_driver):
    """TID 24: 로그인 완료 후 새로고침(F5) -> 로그인 상태 유지"""
    logged_in_driver.refresh()
    icon = MainPage(logged_in_driver).wait_logged_in()
    log.info("새로고침 후 프로필 아이콘 표시: %s", icon.is_displayed())
    assert icon.is_displayed(), "[TID 24] 새로고침 후 프로필 아이콘이 사라짐 (로그인 풀림)"


def test_tid58_logout(driver, credentials):
    """TID 58: 프로필 -> 로그아웃 -> 로그인 페이지로 복귀"""
    login(driver, credentials["url"], credentials["email"], credentials["password"])
    MainPage(driver).logout()
    assert LoginUiPage(driver).password_input().is_displayed(), (
        "[TID 58] 로그아웃 후 로그인 페이지로 돌아오지 않음"
    )


def test_tid59_back_after_logout(driver, credentials):
    """TID 59: 로그아웃 완료 후 뒤로가기(alt+<-) -> 다시 로그인되지 않고 로그아웃 상태 유지"""
    login(driver, credentials["url"], credentials["email"], credentials["password"])
    MainPage(driver).logout()
    driver.back()
    # 미인증 상태이므로 뒤로가기해도 메인페이지가 아닌 로그인 화면이어야 함.
    # (로그아웃 후에는 아이디 저장된 로그인 페이지(signin/history)로 가므로
    #  signin-form 대신 비밀번호 입력창 존재로 로그인 화면 여부를 판단)
    pw_field = LoginUiPage(driver).wait_password_visible()
    # 재로그인 판정은 "메인페이지(앱 도메인)로 넘어갔는지"로 확인.
    # (PersonIcon은 아이디 저장된 로그인 페이지의 계정 아바타에도 쓰여 마커로 부적합)
    current_host = urlparse(driver.current_url).netloc
    app_host = urlparse(credentials["url"]).netloc
    log.info("뒤로가기 후 URL: %s", driver.current_url)
    assert "signin" in driver.current_url, (
        f"[TID 59] 뒤로가기 후 로그인 화면이 아님. URL: {driver.current_url}"
    )
    assert pw_field.is_displayed(), "[TID 59] 뒤로가기 후 로그인 입력창이 뜨지 않음"
    assert current_host != app_host, (
        "[TID 59] 뒤로가기 후 메인페이지로 재진입됨 (로그아웃 유지 실패)"
    )


# ══════════════════════════════════════════════════════════════
# 입력 누락 (TID 1~3) - 브라우저 기본 검증(required)이 빈 칸을 지목
# ══════════════════════════════════════════════════════════════


def test_tid1_empty_email(page, credentials):
    """TID 1: 이메일 누락 -> 브라우저가 이메일 칸을 지목"""
    page.password_input().send_keys(credentials["password"])
    page.login_button().click()

    field, msg = page.focused_validation()
    assert field == "loginId", f"[TID 1] 브라우저가 지목한 칸: {field} (기대: loginId)"
    assert msg != "", "[TID 1] 브라우저 안내문구가 비어 있음"


def test_tid2_empty_password(page, credentials):
    """TID 2: 비밀번호 누락 -> 브라우저가 비밀번호 칸을 지목"""
    page.email_input().send_keys(credentials["email"])
    page.login_button().click()

    field, msg = page.focused_validation()
    assert field == "password", f"[TID 2] 브라우저가 지목한 칸: {field} (기대: password)"
    assert msg != "", "[TID 2] 브라우저 안내문구가 비어 있음"


def test_tid3_empty_both(page, credentials):
    """TID 3: 전체 누락 -> 브라우저가 첫 빈 칸(이메일)을 먼저 지목"""
    page.login_button().click()

    field, msg = page.focused_validation()
    assert field == "loginId", f"[TID 3] 브라우저가 지목한 칸: {field} (기대: loginId)"
    assert msg != "", "[TID 3] 브라우저 안내문구가 비어 있음"


# ══════════════════════════════════════════════════════════════
# 이메일 형식 오류 (TID 4~9)
# ══════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "tid, email_value",
    [
        pytest.param(4, "qa6_project _06@elicer.com", id="TID4-space-before-at"),
        pytest.param(5, "qa6_project_06@ elicer.com", id="TID5-space-after-at"),
        pytest.param(7, "qa6@project@elicer.com", id="TID7-multiple-at"),
        pytest.param(8, "qa6_project_06elicer.com", id="TID8-missing-at"),
        pytest.param(9, "qa6_프로젝트@elicer.com", id="TID9-korean-char"),
    ],
)
def test_email_format_error(page, credentials, tid, email_value):
    """TID 4/5/7/8/9: 잘못된 이메일 형식 -> 브라우저(typeMismatch) 또는
    사이트 화면 문구("잘못된 이메일 형식입니다.") 중 하나가 로그인을 막아야 한다."""
    page.submit_login(email_value, credentials["password"])

    type_mismatch = page.email_type_mismatch()
    screen_msg = page.error_text_now()
    browser_msg = page.email_validation_message()
    log.info("[TID %s] typeMismatch=%s | 화면 문구: '%s' | 브라우저 말풍선: '%s'",
             tid, type_mismatch, screen_msg, browser_msg)

    assert type_mismatch is True or MSG_INVALID_FORMAT in screen_msg, (
        f"[TID {tid}] 입력 '{email_value}'가 차단되지 않음. "
        f"typeMismatch={type_mismatch}, 화면 문구='{screen_msg}'"
    )


def test_tid6_email_special_char(page, credentials):
    """TID 6: 이메일 특수문자(#) 포함 -> 화면에 형식 오류 문구 (브라우저 말풍선은 없음)"""
    msg = page.expect_error(
        "qa6_project#06@elicer.com", credentials["password"], MSG_INVALID_FORMAT
    )
    browser_msg = page.email_validation_message()
    log.info("브라우저 말풍선: '%s' (특수문자는 말풍선 없음)", browser_msg)
    assert MSG_INVALID_FORMAT in msg, f"[TID 6] 실제 화면 문구: '{msg}'"


# ══════════════════════════════════════════════════════════════
# 로그인 실패 - 서버 검증 (TID 12~16)
# ══════════════════════════════════════════════════════════════


def test_tid12_email_too_long(page, credentials):
    """TID 12: 이메일 128자 이상 -> 서버 오류 안내 (예기치 못한 문제가 발생하였습니다)"""
    long_email = ("a" * 120) + "@elicer.com"  # 131자
    msg = page.expect_error(long_email, credentials["password"], MSG_SERVER_ERROR)
    assert MSG_SERVER_ERROR in msg, f"[TID 12] 실제 화면 문구: '{msg}'"


def test_tid13_nonexistent_email(page, credentials):
    """TID 13: 존재하지 않는 이메일 -> 불일치 안내문구"""
    msg = page.expect_error(
        "no_such_user_9999@elicer.com", credentials["password"], MSG_MISMATCH
    )
    assert MSG_MISMATCH in msg, f"[TID 13] 실제 화면 문구: '{msg}'"


def test_tid14_wrong_password(page, credentials):
    """TID 14: 일치하지 않는 비밀번호 -> 불일치 안내문구"""
    msg = page.expect_error(
        credentials["email"], "definitely_wrong_pw_123", MSG_MISMATCH
    )
    assert MSG_MISMATCH in msg, f"[TID 14] 실제 화면 문구: '{msg}'"


def test_tid15_password_too_long(page, credentials):
    """TID 15: 비밀번호 128자 이상 -> 불일치 안내문구"""
    msg = page.expect_error(credentials["email"], "A" * 130, MSG_MISMATCH)
    assert MSG_MISMATCH in msg, f"[TID 15] 실제 화면 문구: '{msg}'"


def test_tid16_password_too_short(page, credentials):
    """TID 16: 비밀번호 7자 이하 -> 최소 8자리 안내"""
    msg = page.expect_error(credentials["email"], "abc123", MSG_PW_MIN_LENGTH)
    assert MSG_PW_MIN_LENGTH in msg, f"[TID 16] 실제 화면 문구: '{msg}'"


# ══════════════════════════════════════════════════════════════
# 페이지 진입 (TID 25~27)
# ══════════════════════════════════════════════════════════════


def test_tid25_page_load(page):
    """TID 25: 로그인 URL 접속 -> 정상 진입"""
    assert page.form().is_displayed()


def test_tid26_form_elements_load(page):
    """TID 26: 로그인 폼 구성요소(이메일/비밀번호/버튼) 정상 로드"""
    assert page.email_input().is_displayed(), "[TID 26] 이메일 입력창 없음"
    assert page.password_input().is_displayed(), "[TID 26] 비밀번호 입력창 없음"
    assert page.login_button().is_displayed(), "[TID 26] 로그인 버튼 없음"


def test_tid27_page_refresh(page):
    """TID 27: 새로고침(F5) 후에도 로그인 페이지 정상 로드"""
    form = page.refresh()
    assert form.is_displayed(), "[TID 27] 새로고침 후 로그인 폼이 뜨지 않음"


# ══════════════════════════════════════════════════════════════
# 입력창 UI (TID 30~33, 36)
# ══════════════════════════════════════════════════════════════


def test_tid30_email_placeholder(page):
    """TID 30: 이메일 입력창 placeholder '이메일' 노출"""
    placeholder = page.email_placeholder()
    log.info("이메일 placeholder: '%s'", placeholder)
    assert placeholder == "이메일", f"[TID 30] 실제 placeholder: '{placeholder}'"


def test_tid31_email_click_focus(page):
    """TID 31: 이메일 입력창 클릭 -> 활성화(포커스)"""
    page.email_input().click()
    name = page.focused_name()
    log.info("클릭 후 포커스된 칸: %s", name)
    assert name == "loginId", f"[TID 31] 클릭 후 포커스된 칸: {name} (기대: loginId)"


def test_tid32_password_placeholder(page):
    """TID 32: 비밀번호 입력창 placeholder '비밀번호' 노출"""
    placeholder = page.password_placeholder()
    log.info("비밀번호 placeholder: '%s'", placeholder)
    assert placeholder == "비밀번호", f"[TID 32] 실제 placeholder: '{placeholder}'"


def test_tid33_password_click_focus(page):
    """TID 33: 비밀번호 입력창 클릭 -> 활성화(포커스)"""
    page.password_input().click()
    name = page.focused_name()
    log.info("클릭 후 포커스된 칸: %s", name)
    assert name == "password", f"[TID 33] 클릭 후 포커스된 칸: {name} (기대: password)"


def test_tid36_password_masking_toggle(page):
    """TID 36: 마스킹 버튼 클릭 -> 비밀번호 표시/숨김 토글"""
    page.password_input().send_keys("toggle_test_123")
    assert page.password_type() == "password", "[TID 36] 초기 상태가 마스킹(password)이 아님"

    # 클릭 -> 표시(text)로 전환
    page.toggle_masking()
    page.wait_password_type("text")
    log.info("버튼 클릭 후 type: %s", page.password_type())

    # 재클릭 -> 다시 마스킹(password)으로 복귀
    page.toggle_masking()
    page.wait_password_type("password")
    log.info("재클릭 후 type: %s", page.password_type())


# ══════════════════════════════════════════════════════════════
# 링크 이동 (TID 38, 43)
# ══════════════════════════════════════════════════════════════


def test_tid38_forgot_password_navigation(page):
    """TID 38: 비밀번호 찾기 링크 클릭 -> 비밀번호 찾기 페이지 이동"""
    url = page.click_forgot_password()
    log.info("이동한 URL: %s", url)
    assert "recover/password" in url, f"[TID 38] 이동한 URL: {url}"


def test_tid43_signup_navigation(page):
    """TID 43: 회원가입 링크 클릭 -> 회원가입 페이지 이동"""
    url = page.click_signup()
    log.info("이동한 URL: %s", url)
    assert "signup" in url, f"[TID 43] 이동한 URL: {url}"
