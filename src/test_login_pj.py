from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── 셀렉터 (한국어 로그인 페이지 HTML 기준, 빌드 시 변하지 않는 속성만 사용) ──
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


def open_login_page(driver, url):
    """로그인 페이지 접속 후 폼이 뜰 때까지 명시적 대기.
    (implicit wait를 없앴으므로 페이지 로드 대기는 여기서 담당.
    폼이 뜨면 내부 요소들은 함께 렌더되므로 이후 find_element는 즉시 안전.)"""
    driver.get(url)
    WebDriverWait(driver, 15).until(EC.visibility_of_element_located(LOGIN_FORM))


def fill_login(driver, email, password):
    driver.find_element(*EMAIL_INPUT).send_keys(email)
    driver.find_element(*PASSWORD_INPUT).send_keys(password)
    driver.find_element(*LOGIN_BUTTON).click()


def test_login_success(driver, credentials):
    """TID 40: 올바른 이메일/비밀번호 -> 로그인 성공 (프로필 아이콘 노출)"""
    open_login_page(driver, credentials["url"])
    fill_login(driver, credentials["email"], credentials["password"])
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(PROFILE_ICON))
    assert driver.find_element(*PROFILE_ICON).is_displayed()


def test_back_button_keeps_login(logged_in_driver):
    """TID 23: 로그인 완료 후 뒤로가기 -> 로그인 상태 유지 (로그인 페이지로 안 감)"""
    driver = logged_in_driver  # conftest fixture: 로그인 완료된 브라우저
    driver.back()
    # 뒤로가기 후에도 프로필 아이콘(로그인 상태 마커)이 여전히 존재
    icon = WebDriverWait(driver, 10).until(EC.presence_of_element_located(PROFILE_ICON))
    assert icon.is_displayed()


def test_refresh_keeps_login(logged_in_driver):
    """로그인 후 메인페이지에서 새로고침(F5) -> 로그인 상태 유지"""
    driver = logged_in_driver  # conftest fixture: 로그인 완료된 브라우저

    driver.refresh()

    # 새로고침 후에도 프로필 아이콘(로그인 상태 마커)이 다시 나타나면 유지된 것
    icon = WebDriverWait(driver, 15).until(EC.presence_of_element_located(PROFILE_ICON))
    print(f"\n[세션 유지] 새로고침 후 프로필 아이콘 표시: {icon.is_displayed()}")
    assert icon.is_displayed()


def test_logout(driver, credentials):
    """TID 57: 프로필 -> 로그아웃 -> 아이디 저장된 로그인 페이지로 복귀"""
    open_login_page(driver, credentials["url"])
    fill_login(driver, credentials["email"], credentials["password"])
    WebDriverWait(driver, 15).until(EC.presence_of_element_located(PROFILE_ICON))
    avatar = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(PROFILE_BUTTON))
    driver.execute_script("arguments[0].click();", avatar)
    logout = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//p[text()='로그아웃']"))
    )
    driver.execute_script("arguments[0].click();", logout)
    password_back = WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
    )
    assert password_back.is_displayed()


def test_empty_email(shared_driver, credentials):
    """TID 1: 이메일 누락 -> 브라우저가 이메일 칸을 지목"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.find_element(*PASSWORD_INPUT).send_keys(credentials["password"])
    driver.find_element(*LOGIN_BUTTON).click()

    focused = driver.switch_to.active_element  # 브라우저가 지목한 칸
    field = focused.get_attribute("name")
    msg = focused.get_attribute("validationMessage")
    print(f"\n[TID 1] 브라우저가 지목한 칸: {field} | 안내문구: '{msg}'")
    assert field == "loginId"
    assert msg != ""


def test_empty_password(shared_driver, credentials):
    """TID 2: 비밀번호 누락 -> 브라우저가 비밀번호 칸을 지목"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.find_element(*EMAIL_INPUT).send_keys(credentials["email"])
    driver.find_element(*LOGIN_BUTTON).click()

    focused = driver.switch_to.active_element
    field = focused.get_attribute("name")
    msg = focused.get_attribute("validationMessage")
    print(f"\n[TID 2] 브라우저가 지목한 칸: {field} | 안내문구: '{msg}'")
    assert field == "password"
    assert msg != ""


def test_empty_both(shared_driver, credentials):
    """TID 3: 전체 누락 -> 브라우저가 첫 빈 칸(이메일)을 먼저 지목"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.find_element(*LOGIN_BUTTON).click()

    focused = driver.switch_to.active_element
    field = focused.get_attribute("name")
    msg = focused.get_attribute("validationMessage")
    print(f"\n[TID 3] 브라우저가 지목한 칸: {field} | 안내문구: '{msg}'")
    assert field == "loginId"  # 첫 빈 칸이 이메일이어야 함
    assert msg != ""


# ── 이메일 형식 오류 (화면 문구 "Invalid email format" + 브라우저 검증 말풍선) ──
def _email_format_error(driver, credentials, tid, email_value):
    """이메일 형식 오류 공통 로직.
    잘못된 이메일 입력 시 (1) 화면에 형식 오류 문구, (2) 로그인 클릭 시
    브라우저 기본 검증 말풍선(validationMessage)이 뜬다. 둘 다 출력하고
    브라우저가 형식 오류(typeMismatch)로 막았는지를 검증한다."""
    open_login_page(driver, credentials["url"])
    driver.find_element(*EMAIL_INPUT).send_keys(email_value)
    driver.find_element(*PASSWORD_INPUT).send_keys(credentials["password"])
    driver.find_element(*LOGIN_BUTTON).click()

    email_el = driver.find_element(*EMAIL_INPUT)
    type_mismatch = driver.execute_script(
        "return arguments[0].validity.typeMismatch;", email_el
    )
    browser_msg = email_el.get_attribute("validationMessage")
    screen_msg = (
        driver.find_element(*ERROR_TEXT).text
        if driver.find_elements(*ERROR_TEXT)
        else ""
    )

    print(f"\n[TID {tid}] 입력='{email_value}'")
    print(f"[TID {tid}] 화면 문구: '{screen_msg}'")
    print(f"[TID {tid}] 브라우저 말풍선: '{browser_msg}'")
    # 형식 오류를 브라우저(typeMismatch)가 막거나, 사이트 화면 문구가 막으면 통과.
    # (특수문자 '#' 등은 브라우저 기준 형식 위반이 아니라 사이트 검증만 걸림)
    assert type_mismatch is True or "Invalid email format" in screen_msg


def test_email_space_before_at(shared_driver, credentials):
    """TID 4: 이메일 '@' 앞 공백 포함 -> Invalid email format."""
    driver = shared_driver  # 공유 브라우저 사용
    _email_format_error(driver, credentials, 4, "qa6_project _06@elicer.com")


def test_email_space_after_at(shared_driver, credentials):
    """TID 5: 이메일 '@' 뒤 공백 포함 -> Invalid email format."""
    driver = shared_driver  # 공유 브라우저 사용
    _email_format_error(driver, credentials, 5, "qa6_project_06@ elicer.com")


def test_email_special_char(shared_driver, credentials):
    """TID 6: 이메일 특수문자(#) 포함 -> 화면에 형식 오류 문구 (말풍선 없음)"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.find_element(*EMAIL_INPUT).send_keys("qa6_project#06@elicer.com")
    driver.find_element(*PASSWORD_INPUT).send_keys(credentials["password"])
    driver.find_element(*LOGIN_BUTTON).click()

    screen_msg = (
        WebDriverWait(driver, 10)
        .until(EC.visibility_of_element_located(ERROR_TEXT))
        .text
    )
    browser_msg = driver.find_element(*EMAIL_INPUT).get_attribute("validationMessage")
    print(f"\n[TID 6] 화면 문구: '{screen_msg}'")
    print(f"[TID 6] 브라우저 말풍선: '{browser_msg}' (특수문자는 말풍선 없음)")
    assert "Invalid email format" in screen_msg  # 화면 문구로 검증


def test_email_multiple_at(shared_driver, credentials):
    """TID 7: 이메일 '@' 다중 입력 -> Invalid email format."""
    driver = shared_driver  # 공유 브라우저 사용
    _email_format_error(driver, credentials, 7, "qa6@project@elicer.com")


def test_email_missing_at(shared_driver, credentials):
    """TID 8: 이메일 '@' 누락 -> 형식 오류 (브라우저 '@ 포함' 안내)"""
    driver = shared_driver  # 공유 브라우저 사용
    _email_format_error(driver, credentials, 8, "qa6_project_06elicer.com")


def test_email_korean(shared_driver, credentials):
    """TID 9: 이메일 한글 포함 -> Invalid email format."""
    driver = shared_driver  # 공유 브라우저 사용
    _email_format_error(driver, credentials, 9, "qa6_프로젝트@elicer.com")


def test_email_too_long(shared_driver, credentials):
    """TID 12: 이메일 128자 이상 -> 서버 오류 안내 (Oops, Something went wrong)"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    long_email = ("a" * 120) + "@elicer.com"  # 131자
    fill_login(driver, long_email, credentials["password"])
    # 서버 응답 문구("Oops...")가 뜰 때까지 대기 - 입력 중 잠깐 뜨는 형식 오류는 무시
    WebDriverWait(driver, 15).until(
        EC.text_to_be_present_in_element(ERROR_TEXT, "Oops")
    )
    error = driver.find_element(*ERROR_TEXT)
    print(f"\n[TID 12] 이메일 128자 이상 안내문구: '{error.text}'")
    assert "Oops" in error.text


def test_nonexistent_email(shared_driver, credentials):
    """TID 13: 존재하지 않는 이메일 -> 실패 안내문구"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    fill_login(driver, "no_such_user_9999@elicer.com", credentials["password"])
    WebDriverWait(driver, 15).until(
        EC.text_to_be_present_in_element(ERROR_TEXT, "Email or password")
    )
    error = driver.find_element(*ERROR_TEXT)
    print(f"\n[TID 13] 존재하지 않는 이메일 안내문구: '{error.text}'")
    assert "Email or password" in error.text


def test_wrong_password(shared_driver, credentials):
    """TID 14: 일치하지 않는 비밀번호 -> 실패 안내문구"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    fill_login(driver, credentials["email"], "definitely_wrong_pw_123")
    WebDriverWait(driver, 15).until(
        EC.text_to_be_present_in_element(ERROR_TEXT, "Email or password")
    )
    error = driver.find_element(*ERROR_TEXT)
    print(f"\n[TID 14] 비밀번호 불일치 안내문구: '{error.text}'")
    assert "Email or password" in error.text


def test_password_too_long(shared_driver, credentials):
    """TID 15: 비밀번호 128자 이상 -> Email or password does not match"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    fill_login(driver, credentials["email"], "A" * 130)
    WebDriverWait(driver, 15).until(
        EC.text_to_be_present_in_element(ERROR_TEXT, "Email or password")
    )
    error = driver.find_element(*ERROR_TEXT)
    print(f"\n[TID 15] 비밀번호 128자 이상 안내문구: '{error.text}'")
    assert "Email or password" in error.text


def test_password_too_short(shared_driver, credentials):
    """TID 16: 비밀번호 7자 이하 -> 최소 8자 안내"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    fill_login(driver, credentials["email"], "abc123")  # 6자
    WebDriverWait(driver, 15).until(EC.text_to_be_present_in_element(ERROR_TEXT, "8"))
    error = driver.find_element(*ERROR_TEXT)
    print(f"\n[TID 16] 비밀번호 7자 이하 안내문구: '{error.text}'")
    assert "8" in error.text


# ══════════════════════════════════════════════════════════════
# 페이지 진입 (TID 24~26)
# ══════════════════════════════════════════════════════════════


def test_page_load(shared_driver, credentials):
    """TID 24: 로그인 URL 접속 -> 정상 진입"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    assert driver.find_element(*LOGIN_FORM).is_displayed()


def test_form_elements_load(shared_driver, credentials):
    """TID 25: 로그인 폼 구성요소(이메일/비밀번호/버튼) 정상 로드"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    assert driver.find_element(*EMAIL_INPUT).is_displayed()
    assert driver.find_element(*PASSWORD_INPUT).is_displayed()
    assert driver.find_element(*LOGIN_BUTTON).is_displayed()


def test_page_refresh(shared_driver, credentials):
    """TID 26: 새로고침(F5) 후에도 로그인 페이지 정상 로드"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.refresh()
    form = WebDriverWait(driver, 15).until(EC.visibility_of_element_located(LOGIN_FORM))
    assert form.is_displayed()


# ══════════════════════════════════════════════════════════════
# 입력창 UI (TID 29~32, 35)
# ══════════════════════════════════════════════════════════════


def test_email_placeholder(shared_driver, credentials):
    """TID 29: 이메일 입력창 placeholder '이메일' 노출"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    placeholder = driver.find_element(*EMAIL_INPUT).get_attribute("placeholder")
    print(f"\n[TID 29] 이메일 placeholder: '{placeholder}'")
    assert placeholder in ["Email", "이메일"]


def test_email_click_focus(shared_driver, credentials):
    """TID 30: 이메일 입력창 클릭 -> 활성화(포커스)"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.find_element(*EMAIL_INPUT).click()
    focused = driver.switch_to.active_element
    name = focused.get_attribute("name")
    print(f"\n[TID 30] 클릭 후 포커스된 칸: {name}")
    assert name == "loginId"


def test_password_placeholder(shared_driver, credentials):
    """TID 31: 비밀번호 입력창 placeholder '비밀번호' 노출"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    placeholder = driver.find_element(*PASSWORD_INPUT).get_attribute("placeholder")
    print(f"\n[TID 31] 비밀번호 placeholder: '{placeholder}'")
    assert placeholder in ["Password", "비밀번호"]


def test_password_click_focus(shared_driver, credentials):
    """TID 32: 비밀번호 입력창 클릭 -> 활성화(포커스)"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.find_element(*PASSWORD_INPUT).click()
    focused = driver.switch_to.active_element
    name = focused.get_attribute("name")
    print(f"\n[TID 32] 클릭 후 포커스된 칸: {name}")
    assert name == "password"


def test_password_masking_toggle(shared_driver, credentials):
    """TID 35: 마스킹 버튼 클릭 -> 비밀번호 표시/숨김 토글"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    pw_el = driver.find_element(*PASSWORD_INPUT)
    pw_el.send_keys("toggle_test_123")

    print(f"\n[TID 35] 초기 type: {pw_el.get_attribute('type')}")
    assert pw_el.get_attribute("type") == "password"  # 처음엔 마스킹 상태

    mask_btn = driver.find_element(*MASKING_BUTTON)
    driver.execute_script("arguments[0].click();", mask_btn)
    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(*PASSWORD_INPUT).get_attribute("type") == "text"
    )
    print(
        f"[TID 35] 버튼 클릭 후 type: {driver.find_element(*PASSWORD_INPUT).get_attribute('type')}"
    )

    driver.execute_script("arguments[0].click();", mask_btn)
    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(*PASSWORD_INPUT).get_attribute("type") == "password"
    )
    print(
        f"[TID 35] 재클릭 후 type: {driver.find_element(*PASSWORD_INPUT).get_attribute('type')}"
    )


# ══════════════════════════════════════════════════════════════
# 링크 이동 (TID 37, 42)
# ══════════════════════════════════════════════════════════════


def test_forgot_password_navigation(shared_driver, credentials):
    """TID 37: 비밀번호 찾기 링크 클릭 -> 비밀번호 찾기 페이지 이동"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.find_element(*FORGOT_PW_LINK).click()
    WebDriverWait(driver, 15).until(EC.url_contains("recover/password"))
    print(f"\n[TID 37] 이동한 URL: {driver.current_url}")
    assert "recover/password" in driver.current_url


def test_signup_navigation(shared_driver, credentials):
    """TID 42: 회원가입 링크 클릭 -> 회원가입 페이지 이동"""
    driver = shared_driver  # 공유 브라우저 사용
    open_login_page(driver, credentials["url"])
    driver.find_element(*SIGNUP_LINK).click()
    WebDriverWait(driver, 15).until(EC.url_contains("signup"))
    print(f"\n[TID 42] 이동한 URL: {driver.current_url}")
    assert "signup" in driver.current_url
