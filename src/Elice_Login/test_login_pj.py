# -*- coding: utf-8 -*-
import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# 명시적 대기 기본 시간 (초)
DEFAULT_TIMEOUT = 15

# ══════════════════════════════════════════════════════════════
# 셀렉터 (한국어 로그인 페이지 HTML 기준, 빌드 시 변하지 않는 속성만 사용)
# ══════════════════════════════════════════════════════════════
LOGIN_FORM = (By.CSS_SELECTOR, "form[data-cy='signin-form']")
EMAIL_INPUT = (By.CSS_SELECTOR, "input[name='loginId']")
PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password']")
LOGIN_BUTTON = (By.CSS_SELECTOR, "form[data-cy='signin-form'] button[type='submit']")
# 화면에 뜨는 에러 문구 요소 (MUI 에러 텍스트)
ERROR_TEXT = (By.CSS_SELECTOR, "p.Mui-error, p[class*='error']")
# 로그인 성공 마커: 메인페이지 사이드바의 프로필 아바타
PROFILE_ICON = (By.CSS_SELECTOR, "[data-testid='PersonIcon']")
# 프로필 아바타를 감싼 클릭 가능한 버튼 (드롭다운 열기용)
PROFILE_BUTTON = (By.XPATH, "//*[@data-testid='PersonIcon']/ancestor::button")
# 비밀번호 마스킹(보기) 버튼 - aria-label 및 DOM 구조 기반 (한국어/영어 모두 호환)
MASKING_BUTTON = (
    By.CSS_SELECTOR,
    "button[aria-label='비밀번호 보기'], button[aria-label='비밀번호 표시'], button[aria-label='View password'], button[aria-label='Show password'], input[name='password'] ~ div button",
)
# 비밀번호 찾기 / 회원가입 링크 - href 부분일치 (언어 무관)
FORGOT_PW_LINK = (By.CSS_SELECTOR, "a[href*='recover/password']")
SIGNUP_LINK = (By.CSS_SELECTOR, "a[href*='signup']")
# 푸터의 언어 선택 드롭다운 (페이지에 select는 이것 하나뿐)
LANGUAGE_SELECT = (By.TAG_NAME, "select")
# 한국어 페이지 렌더링 완료 마커 (이메일 입력창의 한국어 placeholder)
KOREAN_MARKER = (By.CSS_SELECTOR, "input[placeholder='이메일']")

# ══════════════════════════════════════════════════════════════
# 화면 안내 문구 (부분일치로 검증 - 사이트 문구가 바뀌면 여기만 수정)
# ══════════════════════════════════════════════════════════════
MSG_INVALID_FORMAT = "잘못된 이메일 형식"
MSG_MISMATCH = "이메일 또는 비밀번호"
MSG_PW_MIN_LENGTH = "8자리 이상"
MSG_SERVER_ERROR = "예기치 못한 문제"

# ══════════════════════════════════════════════════════════════
# 공통 동작 헬퍼
# ══════════════════════════════════════════════════════════════


def set_korean_language(driver):
    """언어 드롭다운이 한국어가 아니면 ko-KR로 전환 후 한국어 렌더링 대기.
    (사이트가 언어 선택을 저장하지 않아 접속할 때마다 확인이 필요하다.)"""
    language = Select(driver.find_element(*LANGUAGE_SELECT))
    if language.first_selected_option.get_attribute("value") != "ko-KR":
        language.select_by_value("ko-KR")
        # 전환 시 lang=ko-KR로 페이지가 리로드되므로 한국어 폼이 뜰 때까지 대기
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located(KOREAN_MARKER)
        )


def open_login_page(driver, url):
    """로그인 페이지 접속 후 폼이 뜰 때까지 명시적 대기, 한국어 페이지로 전환.
    (implicit wait를 없앴으므로 페이지 로드 대기는 여기서 담당.
    폼이 뜨면 내부 요소들은 함께 렌더되므로 이후 find_element는 즉시 안전.)"""
    driver.get(url)
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        EC.visibility_of_element_located(LOGIN_FORM)
    )
    # 접속 시 lang=en-US로 리다이렉트되므로 매번 한국어로 전환
    set_korean_language(driver)


def submit_login(driver, email, password):
    """이메일/비밀번호 입력 후 로그인 버튼 클릭까지 수행."""
    driver.find_element(*EMAIL_INPUT).send_keys(email)
    driver.find_element(*PASSWORD_INPUT).send_keys(password)
    driver.find_element(*LOGIN_BUTTON).click()


def login(driver, url, email, password):
    """로그인 전체 플로우: 페이지 접속 -> 제출 -> 로그인 완료(프로필 아이콘) 대기."""
    open_login_page(driver, url)
    submit_login(driver, email, password)
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        EC.presence_of_element_located(PROFILE_ICON)
    )


def expect_login_error(driver, url, email, password, expected_msg):
    """로그인 시도 후 화면 에러 문구에 expected_msg가 뜰 때까지 대기하고 실제 문구를 반환.
    제한시간 안에 안 뜨면 그 시점의 화면 문구를 그대로 반환한다 (판정은 호출부 assert 담당)."""
    open_login_page(driver, url)
    submit_login(driver, email, password)
    try:
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.text_to_be_present_in_element(ERROR_TEXT, expected_msg)
        )
    except TimeoutException:
        pass
    found = driver.find_elements(*ERROR_TEXT)
    return found[0].text if found else ""


def focused_validation(driver):
    """브라우저 기본 검증(HTML required)이 지목한 입력칸 name과 안내문구를 반환."""
    focused = driver.switch_to.active_element
    return focused.get_attribute("name"), focused.get_attribute("validationMessage")


@pytest.fixture
def logged_in_driver(driver, credentials):
    """로그인이 완료된 브라우저를 제공 (TID 23, 세션 유지 테스트용)."""
    login(driver, credentials["url"], credentials["email"], credentials["password"])
    return driver


# ══════════════════════════════════════════════════════════════
# 로그인 성공 / 세션 유지 / 로그아웃 (TID 40, 23, 57)
# ══════════════════════════════════════════════════════════════


def test_tid40_login_success(driver, credentials):
    """TID 40: 올바른 이메일/비밀번호 -> 로그인 성공 (프로필 아이콘 노출)"""
    login(driver, credentials["url"], credentials["email"], credentials["password"])
    assert driver.find_element(*PROFILE_ICON).is_displayed()


def test_tid23_back_button_keeps_login(logged_in_driver):
    """TID 23: 로그인 완료 후 뒤로가기 -> 로그인 상태 유지 (로그인 페이지로 안 감)"""
    logged_in_driver.back()
    icon = WebDriverWait(logged_in_driver, DEFAULT_TIMEOUT).until(
        EC.presence_of_element_located(PROFILE_ICON)
    )
    assert icon.is_displayed(), "[TID 23] 뒤로가기 후 프로필 아이콘이 사라짐 (로그인 풀림)"


def test_refresh_keeps_login(logged_in_driver):
    """로그인 후 메인페이지에서 새로고침(F5) -> 로그인 상태 유지"""
    logged_in_driver.refresh()
    icon = WebDriverWait(logged_in_driver, DEFAULT_TIMEOUT).until(
        EC.presence_of_element_located(PROFILE_ICON)
    )
    assert icon.is_displayed(), "새로고침 후 프로필 아이콘이 사라짐 (로그인 풀림)"


def test_tid57_logout(driver, credentials):
    """TID 57: 프로필 -> 로그아웃 -> 로그인 페이지로 복귀"""
    login(driver, credentials["url"], credentials["email"], credentials["password"])
    avatar = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        EC.element_to_be_clickable(PROFILE_BUTTON)
    )
    driver.execute_script("arguments[0].click();", avatar)
    logout = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, "//p[text()='로그아웃']"))
    )
    driver.execute_script("arguments[0].click();", logout)
    password_back = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        EC.visibility_of_element_located(PASSWORD_INPUT)
    )
    assert password_back.is_displayed(), "[TID 57] 로그아웃 후 로그인 페이지로 돌아오지 않음"


# ══════════════════════════════════════════════════════════════
# 입력 누락 (TID 1~3) - 브라우저 기본 검증(required)이 빈 칸을 지목
# ══════════════════════════════════════════════════════════════


def test_tid1_empty_email(shared_driver, credentials):
    """TID 1: 이메일 누락 -> 브라우저가 이메일 칸을 지목"""
    open_login_page(shared_driver, credentials["url"])
    shared_driver.find_element(*PASSWORD_INPUT).send_keys(credentials["password"])
    shared_driver.find_element(*LOGIN_BUTTON).click()

    field, msg = focused_validation(shared_driver)
    assert field == "loginId", f"[TID 1] 브라우저가 지목한 칸: {field} (기대: loginId)"
    assert msg != "", "[TID 1] 브라우저 안내문구가 비어 있음"


def test_tid2_empty_password(shared_driver, credentials):
    """TID 2: 비밀번호 누락 -> 브라우저가 비밀번호 칸을 지목"""
    open_login_page(shared_driver, credentials["url"])
    shared_driver.find_element(*EMAIL_INPUT).send_keys(credentials["email"])
    shared_driver.find_element(*LOGIN_BUTTON).click()

    field, msg = focused_validation(shared_driver)
    assert field == "password", f"[TID 2] 브라우저가 지목한 칸: {field} (기대: password)"
    assert msg != "", "[TID 2] 브라우저 안내문구가 비어 있음"


def test_tid3_empty_both(shared_driver, credentials):
    """TID 3: 전체 누락 -> 브라우저가 첫 빈 칸(이메일)을 먼저 지목"""
    open_login_page(shared_driver, credentials["url"])
    shared_driver.find_element(*LOGIN_BUTTON).click()

    field, msg = focused_validation(shared_driver)
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
def test_email_format_error(shared_driver, credentials, tid, email_value):
    """TID 4/5/7/8/9: 잘못된 이메일 형식 -> 브라우저(typeMismatch) 또는
    사이트 화면 문구("잘못된 이메일 형식입니다.") 중 하나가 로그인을 막아야 한다."""
    open_login_page(shared_driver, credentials["url"])
    submit_login(shared_driver, email_value, credentials["password"])

    email_el = shared_driver.find_element(*EMAIL_INPUT)
    type_mismatch = shared_driver.execute_script(
        "return arguments[0].validity.typeMismatch;", email_el
    )
    found = shared_driver.find_elements(*ERROR_TEXT)
    screen_msg = found[0].text if found else ""

    assert type_mismatch is True or MSG_INVALID_FORMAT in screen_msg, (
        f"[TID {tid}] 입력 '{email_value}'가 차단되지 않음. "
        f"typeMismatch={type_mismatch}, 화면 문구='{screen_msg}'"
    )


def test_tid6_email_special_char(shared_driver, credentials):
    """TID 6: 이메일 특수문자(#) 포함 -> 화면에 형식 오류 문구 (브라우저 말풍선은 없음)"""
    msg = expect_login_error(
        shared_driver,
        credentials["url"],
        "qa6_project#06@elicer.com",
        credentials["password"],
        MSG_INVALID_FORMAT,
    )
    assert MSG_INVALID_FORMAT in msg, f"[TID 6] 실제 화면 문구: '{msg}'"


# ══════════════════════════════════════════════════════════════
# 로그인 실패 - 서버 검증 (TID 12~16)
# ══════════════════════════════════════════════════════════════


def test_tid12_email_too_long(shared_driver, credentials):
    """TID 12: 이메일 128자 이상 -> 서버 오류 안내 (예기치 못한 문제가 발생하였습니다)"""
    long_email = ("a" * 120) + "@elicer.com"  # 131자
    msg = expect_login_error(
        shared_driver, credentials["url"], long_email, credentials["password"], MSG_SERVER_ERROR
    )
    assert MSG_SERVER_ERROR in msg, f"[TID 12] 실제 화면 문구: '{msg}'"


def test_tid13_nonexistent_email(shared_driver, credentials):
    """TID 13: 존재하지 않는 이메일 -> 불일치 안내문구"""
    msg = expect_login_error(
        shared_driver,
        credentials["url"],
        "no_such_user_9999@elicer.com",
        credentials["password"],
        MSG_MISMATCH,
    )
    assert MSG_MISMATCH in msg, f"[TID 13] 실제 화면 문구: '{msg}'"


def test_tid14_wrong_password(shared_driver, credentials):
    """TID 14: 일치하지 않는 비밀번호 -> 불일치 안내문구"""
    msg = expect_login_error(
        shared_driver,
        credentials["url"],
        credentials["email"],
        "definitely_wrong_pw_123",
        MSG_MISMATCH,
    )
    assert MSG_MISMATCH in msg, f"[TID 14] 실제 화면 문구: '{msg}'"


def test_tid15_password_too_long(shared_driver, credentials):
    """TID 15: 비밀번호 128자 이상 -> 불일치 안내문구"""
    msg = expect_login_error(
        shared_driver, credentials["url"], credentials["email"], "A" * 130, MSG_MISMATCH
    )
    assert MSG_MISMATCH in msg, f"[TID 15] 실제 화면 문구: '{msg}'"


def test_tid16_password_too_short(shared_driver, credentials):
    """TID 16: 비밀번호 7자 이하 -> 최소 8자리 안내"""
    msg = expect_login_error(
        shared_driver, credentials["url"], credentials["email"], "abc123", MSG_PW_MIN_LENGTH
    )
    assert MSG_PW_MIN_LENGTH in msg, f"[TID 16] 실제 화면 문구: '{msg}'"


# ══════════════════════════════════════════════════════════════
# 페이지 진입 (TID 24~26)
# ══════════════════════════════════════════════════════════════


def test_tid24_page_load(shared_driver, credentials):
    """TID 24: 로그인 URL 접속 -> 정상 진입"""
    open_login_page(shared_driver, credentials["url"])
    assert shared_driver.find_element(*LOGIN_FORM).is_displayed()


def test_tid25_form_elements_load(shared_driver, credentials):
    """TID 25: 로그인 폼 구성요소(이메일/비밀번호/버튼) 정상 로드"""
    open_login_page(shared_driver, credentials["url"])
    assert shared_driver.find_element(*EMAIL_INPUT).is_displayed(), "[TID 25] 이메일 입력창 없음"
    assert shared_driver.find_element(*PASSWORD_INPUT).is_displayed(), "[TID 25] 비밀번호 입력창 없음"
    assert shared_driver.find_element(*LOGIN_BUTTON).is_displayed(), "[TID 25] 로그인 버튼 없음"


def test_tid26_page_refresh(shared_driver, credentials):
    """TID 26: 새로고침(F5) 후에도 로그인 페이지 정상 로드"""
    open_login_page(shared_driver, credentials["url"])
    shared_driver.refresh()
    form = WebDriverWait(shared_driver, DEFAULT_TIMEOUT).until(
        EC.visibility_of_element_located(LOGIN_FORM)
    )
    assert form.is_displayed(), "[TID 26] 새로고침 후 로그인 폼이 뜨지 않음"


# ══════════════════════════════════════════════════════════════
# 입력창 UI (TID 29~32, 35)
# ══════════════════════════════════════════════════════════════


def test_tid29_email_placeholder(shared_driver, credentials):
    """TID 29: 이메일 입력창 placeholder '이메일' 노출"""
    open_login_page(shared_driver, credentials["url"])
    placeholder = shared_driver.find_element(*EMAIL_INPUT).get_attribute("placeholder")
    assert placeholder == "이메일", f"[TID 29] 실제 placeholder: '{placeholder}'"


def test_tid30_email_click_focus(shared_driver, credentials):
    """TID 30: 이메일 입력창 클릭 -> 활성화(포커스)"""
    open_login_page(shared_driver, credentials["url"])
    shared_driver.find_element(*EMAIL_INPUT).click()
    name = shared_driver.switch_to.active_element.get_attribute("name")
    assert name == "loginId", f"[TID 30] 클릭 후 포커스된 칸: {name} (기대: loginId)"


def test_tid31_password_placeholder(shared_driver, credentials):
    """TID 31: 비밀번호 입력창 placeholder '비밀번호' 노출"""
    open_login_page(shared_driver, credentials["url"])
    placeholder = shared_driver.find_element(*PASSWORD_INPUT).get_attribute("placeholder")
    assert placeholder == "비밀번호", f"[TID 31] 실제 placeholder: '{placeholder}'"


def test_tid32_password_click_focus(shared_driver, credentials):
    """TID 32: 비밀번호 입력창 클릭 -> 활성화(포커스)"""
    open_login_page(shared_driver, credentials["url"])
    shared_driver.find_element(*PASSWORD_INPUT).click()
    name = shared_driver.switch_to.active_element.get_attribute("name")
    assert name == "password", f"[TID 32] 클릭 후 포커스된 칸: {name} (기대: password)"


def test_tid35_password_masking_toggle(shared_driver, credentials):
    """TID 35: 마스킹 버튼 클릭 -> 비밀번호 표시/숨김 토글"""
    open_login_page(shared_driver, credentials["url"])
    pw_el = shared_driver.find_element(*PASSWORD_INPUT)
    pw_el.send_keys("toggle_test_123")
    assert pw_el.get_attribute("type") == "password", "[TID 35] 초기 상태가 마스킹(password)이 아님"

    mask_btn = shared_driver.find_element(*MASKING_BUTTON)
    # 클릭 -> 표시(text)로 전환
    shared_driver.execute_script("arguments[0].click();", mask_btn)
    WebDriverWait(shared_driver, 5).until(
        lambda d: d.find_element(*PASSWORD_INPUT).get_attribute("type") == "text"
    )
    # 재클릭 -> 다시 마스킹(password)으로 복귀
    shared_driver.execute_script("arguments[0].click();", mask_btn)
    WebDriverWait(shared_driver, 5).until(
        lambda d: d.find_element(*PASSWORD_INPUT).get_attribute("type") == "password"
    )


# ══════════════════════════════════════════════════════════════
# 링크 이동 (TID 37, 42)
# ══════════════════════════════════════════════════════════════


def test_tid37_forgot_password_navigation(shared_driver, credentials):
    """TID 37: 비밀번호 찾기 링크 클릭 -> 비밀번호 찾기 페이지 이동"""
    open_login_page(shared_driver, credentials["url"])
    shared_driver.find_element(*FORGOT_PW_LINK).click()
    WebDriverWait(shared_driver, DEFAULT_TIMEOUT).until(EC.url_contains("recover/password"))
    assert "recover/password" in shared_driver.current_url, (
        f"[TID 37] 이동한 URL: {shared_driver.current_url}"
    )


def test_tid42_signup_navigation(shared_driver, credentials):
    """TID 42: 회원가입 링크 클릭 -> 회원가입 페이지 이동"""
    open_login_page(shared_driver, credentials["url"])
    shared_driver.find_element(*SIGNUP_LINK).click()
    WebDriverWait(shared_driver, DEFAULT_TIMEOUT).until(EC.url_contains("signup"))
    assert "signup" in shared_driver.current_url, (
        f"[TID 42] 이동한 URL: {shared_driver.current_url}"
    )
