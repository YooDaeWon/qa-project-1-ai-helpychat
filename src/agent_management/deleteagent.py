import csv
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# ============================================================
# 기본 설정
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

# 현재 구조:
# ProjectEx/
# ├─ .env
# └─ src/
#    └─ agent_management/
#       └─ deleteagent.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

HEADLESS_MODE = False

DEFAULT_WAIT_TIME = 15
PAGE_WAIT_TIME = 30
SHORT_WAIT_TIME = 5

MAX_SCROLL_COUNT = 25
SCROLL_WAIT_TIME = 0.5

DELETE_MODE_AUTOMATION = "automation"
DELETE_MODE_ALL = "all"

AUTOMATION_AGENT_TITLE_PATTERN = re.compile(
    r"^자동화테스트에이전트_\d{8}_\d{6}_\d{3}회차$"
)

RESULT_CSV_HEADERS = [
    "기록시간",
    "에이전트 제목",
    "삭제 결과",
    "비고",
]


# ============================================================
# 환경변수
# ============================================================

def load_env() -> tuple[str, str, str]:
    """
    프로젝트 루트의 .env 파일을 읽습니다.
    """

    if not ENV_PATH.exists():
        raise FileNotFoundError(
            f".env 파일을 찾을 수 없습니다: {ENV_PATH}"
        )

    load_dotenv(dotenv_path=ENV_PATH)

    login_url = os.getenv("LOGIN_URL", "").strip().rstrip("/")
    login_email = os.getenv("LOGIN_EMAIL", "").strip()
    login_password = os.getenv("LOGIN_PASSWORD", "").strip()

    missing_values = []

    if not login_url:
        missing_values.append("LOGIN_URL")

    if not login_email:
        missing_values.append("LOGIN_EMAIL")

    if not login_password:
        missing_values.append("LOGIN_PASSWORD")

    if missing_values:
        missing_text = ", ".join(missing_values)

        raise ValueError(
            f".env에 다음 환경변수를 입력해주세요: {missing_text}"
        )

    print(f".env 읽기 완료: {ENV_PATH}")

    return login_url, login_email, login_password


# ============================================================
# 삭제 방식 선택
# ============================================================

def select_delete_mode() -> str:
    """
    삭제 방식을 터미널에서 입력받습니다.
    """

    while True:
        print()
        print("=" * 60)
        print("에이전트 삭제 방식 선택")
        print("=" * 60)
        print("1. 자동 생성 테스트용 에이전트만 삭제")
        print("2. 전체 삭제")
        print("=" * 60)

        selected_value = input(
            "삭제 방식을 선택하세요 (1 또는 2): "
        ).strip()

        if selected_value == "1":
            print()
            print("자동 생성 테스트용 에이전트만 삭제합니다.")

            return DELETE_MODE_AUTOMATION

        if selected_value == "2":
            print()
            print("내 에이전트에 있는 모든 에이전트를 삭제합니다.")

            return DELETE_MODE_ALL

        print()
        print("잘못된 입력입니다. 1 또는 2를 입력해주세요.")


def get_delete_mode_name(delete_mode: str) -> str:
    """
    삭제 방식의 출력용 이름을 반환합니다.
    """

    if delete_mode == DELETE_MODE_AUTOMATION:
        return "자동 생성 테스트용 에이전트만 삭제"

    return "전체 삭제"


# ============================================================
# CSV
# ============================================================

def create_result_csv() -> Path:
    """
    실행 결과를 저장할 CSV 파일을 생성합니다.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = SCRIPT_DIR / f"deleteagent_result_{timestamp}.csv"

    # Excel에서 한글이 깨지지 않도록 UTF-8 BOM을 먼저 작성합니다.
    csv_path.write_text("\ufeff", encoding="utf-8")

    print(f"삭제 결과 CSV 생성 완료: {csv_path}")

    return csv_path


def write_result_csv(
    csv_path: Path,
    agent_title: str,
    result: str,
    comment: str = "",
) -> None:
    """
    삭제 결과를 CSV에 기록합니다.
    첫 번째 결과 작성 시 헤더를 추가합니다.
    """

    file_size = csv_path.stat().st_size if csv_path.exists() else 0
    needs_header = file_size <= 3

    with csv_path.open(
        mode="a",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.writer(csv_file)

        if needs_header:
            writer.writerow(RESULT_CSV_HEADERS)

        writer.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                agent_title,
                result,
                comment,
            ]
        )


def write_no_agent_result(
    csv_path: Path,
    delete_mode: str,
) -> None:
    """
    삭제 대상이 없을 때 실제 시간과 안내 문구를 기록합니다.
    """

    if delete_mode == DELETE_MODE_AUTOMATION:
        message = "삭제할 자동 생성 테스트용 에이전트가 없습니다."
    else:
        message = "삭제할 에이전트가 없습니다."

    with csv_path.open(
        mode="a",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                message,
            ]
        )


# ============================================================
# Chrome 설정
# ============================================================

def create_chrome_options() -> Options:
    """
    Chrome 실행 옵션을 생성합니다.
    """

    options = Options()

    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")

    if HEADLESS_MODE:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    return options


# ============================================================
# 공통 동작
# ============================================================

def safe_click(
    driver: webdriver.Chrome,
    element: WebElement,
) -> None:
    """
    일반 클릭을 우선 시도하고 실패하면 JavaScript로 클릭합니다.
    """

    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element,
        )

        time.sleep(0.2)
        element.click()

    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
        WebDriverException,
    ):
        driver.execute_script(
            "arguments[0].click();",
            element,
        )


def save_failure_screenshot(
    driver: webdriver.Chrome,
) -> Path:
    """
    실패 화면을 현재 스크립트 폴더에 저장합니다.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = (
        SCRIPT_DIR / f"deleteagent_failure_{timestamp}.png"
    )

    driver.save_screenshot(str(screenshot_path))

    print(f"실패 화면 저장 완료: {screenshot_path}")

    return screenshot_path


def get_relative_agent_href(agent_url: str) -> str:
    """
    절대 URL을 /agents/UUID 형태의 상대 경로로 변환합니다.
    """

    parsed_url = urlparse(agent_url)

    return parsed_url.path


def find_first_visible_element(
    driver: webdriver.Chrome,
    locators: list[tuple[str, str]],
) -> WebElement | None:
    """
    여러 셀렉터 중 화면에 표시된 첫 번째 요소를 반환합니다.
    """

    for by, value in locators:
        elements = driver.find_elements(by, value)

        for element in elements:
            try:
                if element.is_displayed():
                    return element
            except StaleElementReferenceException:
                continue

    return None


# ============================================================
# 로그인
# ============================================================

def get_visible_email_input(
    driver: webdriver.Chrome,
) -> WebElement | None:
    """
    현재 화면에 표시된 이메일 입력창을 반환합니다.
    """

    return find_first_visible_element(
        driver,
        [
            (By.CSS_SELECTOR, "input[name='loginId']"),
            (By.CSS_SELECTOR, "input[placeholder='Email']"),
            (By.CSS_SELECTOR, "input[type='email']"),
        ],
    )


def get_visible_password_input(
    driver: webdriver.Chrome,
) -> WebElement | None:
    """
    현재 화면에 표시된 비밀번호 입력창을 반환합니다.
    """

    return find_first_visible_element(
        driver,
        [
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.CSS_SELECTOR, "input[placeholder='Password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ],
    )


def get_visible_login_button(
    driver: webdriver.Chrome,
) -> WebElement | None:
    """
    현재 화면에 표시된 Login 버튼을 반환합니다.
    """

    return find_first_visible_element(
        driver,
        [
            (
                By.XPATH,
                "//button[@type='submit' and normalize-space()='Login']",
            ),
            (
                By.XPATH,
                "//button[normalize-space()='Login']",
            ),
            (
                By.CSS_SELECTOR,
                "button[type='submit']",
            ),
        ],
    )


def is_login_page(
    driver: webdriver.Chrome,
) -> bool:
    """
    로그인 입력창 표시 여부로 로그인 페이지를 판별합니다.
    """

    email_input = get_visible_email_input(driver)
    password_input = get_visible_password_input(driver)

    return (
        email_input is not None
        and password_input is not None
    )


def get_visible_private_panel(
    driver: webdriver.Chrome,
) -> WebElement | None:
    """
    현재 표시된 내 에이전트 탭 패널을 반환합니다.
    """

    panels = driver.find_elements(
        By.CSS_SELECTOR,
        "[role='tabpanel'][id$='agents-private']",
    )

    for panel in panels:
        try:
            if panel.is_displayed():
                return panel
        except StaleElementReferenceException:
            continue

    return None


def get_visible_private_tab(
    driver: webdriver.Chrome,
) -> WebElement | None:
    """
    현재 화면에 표시된 내 에이전트 탭을 반환합니다.
    """

    tabs = driver.find_elements(
        By.XPATH,
        "//*[@role='tab' and "
        "contains(normalize-space(), '내 에이전트')]",
    )

    for tab in tabs:
        try:
            if tab.is_displayed():
                return tab
        except StaleElementReferenceException:
            continue

    return None


def is_service_page(
    driver: webdriver.Chrome,
    base_url: str,
) -> bool:
    """
    AI Helpy Chat 서비스 화면인지 확인합니다.
    """

    if is_login_page(driver):
        return False

    try:
        expected_host = urlparse(base_url).netloc
        current_host = urlparse(driver.current_url).netloc

        if expected_host != current_host:
            return False
    except WebDriverException:
        return False

    if get_visible_private_panel(driver) is not None:
        return True

    if get_visible_private_tab(driver) is not None:
        return True

    try:
        body_text = driver.find_element(
            By.TAG_NAME,
            "body",
        ).text

        service_texts = [
            "새 대화",
            "내 에이전트",
            "에이전트 마켓플레이스",
            "검색",
        ]

        return any(
            service_text in body_text
            for service_text in service_texts
        )

    except (
        NoSuchElementException,
        StaleElementReferenceException,
    ):
        return False


def wait_for_login_or_service_page(
    driver: webdriver.Chrome,
    base_url: str,
    timeout: int = PAGE_WAIT_TIME,
) -> str:
    """
    로그인 화면 또는 서비스 화면이 확실하게 표시될 때까지 기다립니다.
    """

    def page_state_condition(
        current_driver: webdriver.Chrome,
    ) -> str | bool:
        if is_login_page(current_driver):
            return "login"

        if is_service_page(current_driver, base_url):
            return "service"

        return False

    try:
        return WebDriverWait(
            driver,
            timeout,
        ).until(page_state_condition)

    except TimeoutException as error:
        raise RuntimeError(
            "로그인 화면 또는 서비스 화면을 확인하지 못했습니다."
        ) from error


def wait_for_login_success(
    driver: webdriver.Chrome,
    base_url: str,
) -> None:
    """
    로그인 화면이 사라지고 서비스 화면이 표시될 때까지 기다립니다.
    """

    def login_success_condition(
        current_driver: webdriver.Chrome,
    ) -> bool:
        return is_service_page(
            current_driver,
            base_url,
        )

    try:
        WebDriverWait(
            driver,
            PAGE_WAIT_TIME,
        ).until(login_success_condition)

    except TimeoutException as error:
        current_url = driver.current_url

        raise RuntimeError(
            "로그인 완료 상태를 확인하지 못했습니다. "
            f"현재 주소: {current_url}"
        ) from error


def login_if_needed(
    driver: webdriver.Chrome,
    base_url: str,
    login_email: str,
    login_password: str,
) -> None:
    """
    로그인 페이지가 표시되면 자동 로그인을 진행합니다.
    """

    print("로그인 상태 확인 중...")

    page_state = wait_for_login_or_service_page(
        driver=driver,
        base_url=base_url,
    )

    if page_state == "service":
        print("기존 로그인 상태 확인 완료")
        return

    print("로그인 페이지 감지됨. 자동 로그인 진행")

    try:
        email_input = WebDriverWait(
            driver,
            DEFAULT_WAIT_TIME,
        ).until(
            lambda current_driver: (
                get_visible_email_input(current_driver)
            )
        )

    except TimeoutException as error:
        raise RuntimeError(
            "Email 입력창을 찾지 못했습니다."
        ) from error

    email_input.clear()
    email_input.send_keys(login_email)

    print("Email 입력 완료")

    try:
        password_input = WebDriverWait(
            driver,
            DEFAULT_WAIT_TIME,
        ).until(
            lambda current_driver: (
                get_visible_password_input(current_driver)
            )
        )

    except TimeoutException as error:
        raise RuntimeError(
            "Password 입력창을 찾지 못했습니다."
        ) from error

    password_input.clear()
    password_input.send_keys(login_password)

    print("Password 입력 완료")

    try:
        login_button = WebDriverWait(
            driver,
            DEFAULT_WAIT_TIME,
        ).until(
            lambda current_driver: (
                get_visible_login_button(current_driver)
                if (
                    get_visible_login_button(current_driver)
                    is not None
                    and get_visible_login_button(
                        current_driver
                    ).is_enabled()
                )
                else False
            )
        )

    except TimeoutException as error:
        raise RuntimeError(
            "Login 버튼을 찾지 못했거나 활성화되지 않았습니다."
        ) from error

    safe_click(
        driver,
        login_button,
    )

    print("Login 버튼 클릭 완료")

    wait_for_login_success(
        driver=driver,
        base_url=base_url,
    )

    print("로그인 완료")


# ============================================================
# 내 에이전트 화면
# ============================================================

def go_to_private_agents(
    driver: webdriver.Chrome,
    base_url: str,
    login_email: str,
    login_password: str,
) -> None:
    """
    에이전트 조직 화면에서 내 에이전트 탭으로 이동합니다.
    이동 중 로그인 화면으로 전환되면 다시 로그인합니다.
    """

    new_chat_url = f"{base_url}/#agents-organization"

    print("새 대화 화면으로 이동 시도")

    driver.get(new_chat_url)

    page_state = wait_for_login_or_service_page(
        driver=driver,
        base_url=base_url,
    )

    if page_state == "login":
        print("화면 이동 중 로그인 페이지 감지됨")

        login_if_needed(
            driver=driver,
            base_url=base_url,
            login_email=login_email,
            login_password=login_password,
        )

    # 로그인 이후 다른 화면으로 이동한 경우 에이전트 조직 주소로 재진입합니다.
    if "#agents-organization" not in driver.current_url:
        driver.get(new_chat_url)

        page_state = wait_for_login_or_service_page(
            driver=driver,
            base_url=base_url,
        )

        if page_state == "login":
            login_if_needed(
                driver=driver,
                base_url=base_url,
                login_email=login_email,
                login_password=login_password,
            )

    print("에이전트 조직 화면 로딩 확인 완료")

    # 이미 내 에이전트 패널이 표시된 경우에는 탭을 다시 누르지 않습니다.
    if get_visible_private_panel(driver) is not None:
        print("내 에이전트 화면 진입 확인 완료")
        return

    try:
        private_tab = WebDriverWait(
            driver,
            PAGE_WAIT_TIME,
        ).until(
            lambda current_driver: (
                get_visible_private_tab(current_driver)
            )
        )

    except TimeoutException as error:
        raise RuntimeError(
            "내 에이전트 탭을 찾지 못했습니다."
        ) from error

    safe_click(
        driver,
        private_tab,
    )

    print("내 에이전트 탭 클릭 완료")

    try:
        WebDriverWait(
            driver,
            DEFAULT_WAIT_TIME,
        ).until(
            lambda current_driver: (
                get_visible_private_panel(current_driver)
                is not None
            )
        )

    except TimeoutException as error:
        raise RuntimeError(
            "내 에이전트 화면 진입을 확인하지 못했습니다."
        ) from error

    print("내 에이전트 화면 진입 확인 완료")


# ============================================================
# 에이전트 정보 탐색
# ============================================================

def get_agent_links(
    private_panel: WebElement,
) -> list[WebElement]:
    """
    내 에이전트 패널에 존재하는 상세 링크를 반환합니다.
    /agents/builder 링크는 제외합니다.
    """

    agent_links = private_panel.find_elements(
        By.CSS_SELECTOR,
        "a[href^='/agents/']",
    )

    unique_links = []
    seen_hrefs = set()

    for agent_link in agent_links:
        try:
            href = agent_link.get_attribute("href")

            if not href:
                continue

            relative_href = get_relative_agent_href(href)

            if relative_href == "/agents/builder":
                continue

            if not relative_href.startswith("/agents/"):
                continue

            if relative_href in seen_hrefs:
                continue

            seen_hrefs.add(relative_href)
            unique_links.append(agent_link)

        except StaleElementReferenceException:
            continue

    return unique_links


def get_agent_title(
    agent_link: WebElement,
) -> str:
    """
    에이전트 링크 내부의 제목을 가져옵니다.
    """

    try:
        title_elements = agent_link.find_elements(
            By.CSS_SELECTOR,
            "p",
        )

        for title_element in title_elements:
            title = title_element.text.strip()

            if title:
                return title

    except StaleElementReferenceException:
        pass

    return "제목 없음"


def build_agent_info(
    agent_link: WebElement,
) -> dict[str, str]:
    """
    에이전트의 제목과 링크 정보를 생성합니다.
    """

    absolute_href = agent_link.get_attribute("href")

    if not absolute_href:
        raise RuntimeError(
            "에이전트 상세 링크를 확인하지 못했습니다."
        )

    return {
        "title": get_agent_title(agent_link),
        "absolute_href": absolute_href,
        "relative_href": get_relative_agent_href(absolute_href),
    }


def is_automation_test_agent(
    agent_title: str,
) -> bool:
    """
    자동 생성 테스트용 제목 형식인지 확인합니다.
    """

    return (
        AUTOMATION_AGENT_TITLE_PATTERN.fullmatch(
            agent_title
        )
        is not None
    )


def reset_agent_scroll(
    driver: webdriver.Chrome,
) -> None:
    """
    내 에이전트 목록을 상단으로 이동합니다.
    """

    driver.execute_script(
        "window.scrollTo(0, 0);"
    )

    private_panel = get_visible_private_panel(driver)

    if private_panel is not None:
        try:
            driver.execute_script(
                "arguments[0].scrollTop = 0;",
                private_panel,
            )
        except StaleElementReferenceException:
            pass

    time.sleep(SCROLL_WAIT_TIME)


def scroll_agent_list(
    driver: webdriver.Chrome,
) -> None:
    """
    페이지와 내 에이전트 패널을 아래로 스크롤합니다.
    """

    private_panel = get_visible_private_panel(driver)

    if private_panel is not None:
        try:
            driver.execute_script(
                """
                arguments[0].scrollTop =
                    arguments[0].scrollTop +
                    Math.max(arguments[0].clientHeight * 0.8, 500);
                """,
                private_panel,
            )
        except StaleElementReferenceException:
            pass

    driver.execute_script(
        """
        window.scrollBy(
            0,
            Math.max(window.innerHeight * 0.8, 500)
        );
        """
    )

    time.sleep(SCROLL_WAIT_TIME)


def get_target_agent_info(
    driver: webdriver.Chrome,
    delete_mode: str,
    excluded_hrefs: set[str],
) -> dict[str, str] | None:
    """
    삭제 방식에 맞는 첫 번째 삭제 대상 에이전트를 찾습니다.
    """

    reset_agent_scroll(driver)

    checked_hrefs = set()

    for _ in range(MAX_SCROLL_COUNT):
        private_panel = get_visible_private_panel(driver)

        if private_panel is None:
            raise RuntimeError(
                "내 에이전트 패널을 찾지 못했습니다."
            )

        agent_links = get_agent_links(private_panel)

        for agent_link in agent_links:
            try:
                agent_info = build_agent_info(agent_link)
                relative_href = agent_info["relative_href"]

                if relative_href in checked_hrefs:
                    continue

                checked_hrefs.add(relative_href)

                if relative_href in excluded_hrefs:
                    continue

                if delete_mode == DELETE_MODE_ALL:
                    return agent_info

                if is_automation_test_agent(
                    agent_info["title"]
                ):
                    return agent_info

            except (
                StaleElementReferenceException,
                WebDriverException,
            ):
                continue

        scroll_agent_list(driver)

    return None


def locate_agent_link(
    driver: webdriver.Chrome,
    relative_href: str,
) -> WebElement:
    """
    상대 링크가 일치하는 에이전트 카드를 다시 찾습니다.
    """

    reset_agent_scroll(driver)

    xpath = f"//a[@href='{relative_href}']"

    for _ in range(MAX_SCROLL_COUNT):
        links = driver.find_elements(
            By.XPATH,
            xpath,
        )

        for link in links:
            try:
                if link.is_displayed():
                    return link
            except StaleElementReferenceException:
                continue

        scroll_agent_list(driver)

    raise RuntimeError(
        f"삭제 대상 에이전트 링크를 찾지 못했습니다: {relative_href}"
    )


def find_agent_card(
    agent_link: WebElement,
) -> WebElement:
    """
    에이전트 상세 링크를 포함한 카드 요소를 반환합니다.
    """

    try:
        return agent_link.find_element(
            By.XPATH,
            "./ancestor::*[contains(@class, 'MuiCard-root')][1]",
        )

    except NoSuchElementException as error:
        raise RuntimeError(
            "에이전트 카드 영역을 찾지 못했습니다."
        ) from error


# ============================================================
# 삭제 메뉴
# ============================================================

def click_more_menu_with_javascript(
    driver: webdriver.Chrome,
    agent_card: WebElement,
) -> None:
    """
    실제 마우스를 움직이지 않고 JavaScript 이벤트로
    점 3개 메뉴 버튼을 표시한 후 클릭합니다.
    """

    click_result = driver.execute_script(
        """
        const card = arguments[0];

        if (!card) {
            return {
                success: false,
                reason: "에이전트 카드가 없습니다."
            };
        }

        const eventNames = [
            "pointerover",
            "pointerenter",
            "mouseover",
            "mouseenter",
            "mousemove"
        ];

        for (const eventName of eventNames) {
            card.dispatchEvent(
                new MouseEvent(
                    eventName,
                    {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    }
                )
            );
        }

        const menuButton =
            card.querySelector(
                "button[class*='menu-trigger']"
            );

        if (!menuButton) {
            return {
                success: false,
                reason: "점 3개 메뉴 버튼을 찾지 못했습니다."
            };
        }

        menuButton.style.display = "flex";
        menuButton.style.opacity = "1";
        menuButton.style.visibility = "visible";
        menuButton.style.pointerEvents = "auto";

        menuButton.dispatchEvent(
            new PointerEvent(
                "pointerdown",
                {
                    bubbles: true,
                    cancelable: true
                }
            )
        );

        menuButton.dispatchEvent(
            new MouseEvent(
                "mousedown",
                {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }
            )
        );

        menuButton.dispatchEvent(
            new MouseEvent(
                "mouseup",
                {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }
            )
        );

        menuButton.click();

        return {
            success: true,
            reason: ""
        };
        """,
        agent_card,
    )

    if not click_result or not click_result.get("success"):
        reason = (
            click_result.get("reason")
            if click_result
            else "JavaScript 클릭 결과를 확인하지 못했습니다."
        )

        raise RuntimeError(reason)

    print("점 3개 메뉴 버튼 JavaScript 클릭 완료")


def click_remove_agent_menu(
    driver: webdriver.Chrome,
) -> None:
    """
    열린 메뉴에서 에이전트 제거 항목을 클릭합니다.
    """

    wait = WebDriverWait(driver, DEFAULT_WAIT_TIME)

    remove_menu_item = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//*[@role='menuitem' and "
                "normalize-space()='에이전트 제거']",
            )
        )
    )

    safe_click(
        driver,
        remove_menu_item,
    )

    print("에이전트 제거 메뉴 클릭 완료")


# ============================================================
# 삭제 확인창
# ============================================================

def wait_delete_dialog(
    driver: webdriver.Chrome,
) -> WebElement:
    """
    에이전트 삭제 확인창 표시를 확인합니다.
    """

    wait = WebDriverWait(driver, DEFAULT_WAIT_TIME)

    dialog = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[@role='dialog' and "
                ".//*[normalize-space()='에이전트를 제거할까요?']]",
            )
        )
    )

    print("'에이전트를 제거할까요?' 팝업 확인 완료")

    return dialog


def click_confirm_delete(
    driver: webdriver.Chrome,
    dialog: WebElement,
) -> None:
    """
    삭제 확인창의 제거하기 버튼을 클릭합니다.
    """

    try:
        confirm_button = WebDriverWait(
            driver,
            DEFAULT_WAIT_TIME,
        ).until(
            lambda current_driver: (
                dialog.find_element(
                    By.XPATH,
                    ".//button[normalize-space()='제거하기']",
                )
            )
        )

    except TimeoutException as error:
        raise RuntimeError(
            "제거하기 버튼을 찾지 못했습니다."
        ) from error

    safe_click(
        driver,
        confirm_button,
    )

    print("제거하기 버튼 클릭 완료")


# ============================================================
# 삭제 결과 검증
# ============================================================

def verify_agent_removed(
    driver: webdriver.Chrome,
    relative_href: str,
) -> None:
    """
    삭제한 에이전트 링크가 목록에서 사라졌는지 확인합니다.
    """

    xpath = f"//a[@href='{relative_href}']"

    try:
        WebDriverWait(
            driver,
            DEFAULT_WAIT_TIME,
        ).until(
            lambda current_driver: (
                len(
                    current_driver.find_elements(
                        By.XPATH,
                        xpath,
                    )
                )
                == 0
            )
        )

    except TimeoutException as error:
        raise RuntimeError(
            "삭제한 에이전트가 목록에서 사라지지 않았습니다."
        ) from error

    print(
        "삭제한 에이전트가 목록에서 사라진 것을 확인했습니다."
    )


def verify_delete_success_toast(
    driver: webdriver.Chrome,
) -> None:
    """
    삭제 완료 안내 문구를 확인합니다.
    """

    try:
        WebDriverWait(
            driver,
            DEFAULT_WAIT_TIME,
        ).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//*[normalize-space()='에이전트가 제거되었습니다.']",
                )
            )
        )

    except TimeoutException as error:
        raise RuntimeError(
            "'에이전트가 제거되었습니다.' 알림을 확인하지 못했습니다."
        ) from error

    print("'에이전트가 제거되었습니다.' 알림 확인 완료")


def is_empty_agent_list(
    driver: webdriver.Chrome,
) -> bool:
    """
    내 에이전트 목록의 빈 상태 문구 표시 여부를 확인합니다.
    """

    empty_messages = driver.find_elements(
        By.XPATH,
        "//*[normalize-space()='나만의 에이전트를 만들어 보세요.']",
    )

    for empty_message in empty_messages:
        try:
            if empty_message.is_displayed():
                return True
        except StaleElementReferenceException:
            continue

    return False


# ============================================================
# 개별 에이전트 삭제
# ============================================================

def delete_single_agent(
    driver: webdriver.Chrome,
    agent_info: dict[str, str],
) -> None:
    """
    에이전트 한 개를 삭제하고 결과를 검증합니다.
    """

    relative_href = agent_info["relative_href"]

    agent_link = locate_agent_link(
        driver,
        relative_href,
    )

    agent_card = find_agent_card(agent_link)

    click_more_menu_with_javascript(
        driver,
        agent_card,
    )

    click_remove_agent_menu(driver)

    dialog = wait_delete_dialog(driver)

    click_confirm_delete(
        driver,
        dialog,
    )

    verify_agent_removed(
        driver,
        relative_href,
    )

    verify_delete_success_toast(driver)


# ============================================================
# 전체 삭제 반복
# ============================================================

def delete_agents(
    driver: webdriver.Chrome,
    delete_mode: str,
    csv_path: Path,
) -> tuple[list[str], list[tuple[str, str]]]:
    """
    선택한 삭제 방식에 따라 삭제 대상이 없을 때까지 반복합니다.
    """

    deleted_agents: list[str] = []
    failed_agents: list[tuple[str, str]] = []
    excluded_hrefs: set[str] = set()

    while True:
        target_agent = get_target_agent_info(
            driver,
            delete_mode,
            excluded_hrefs,
        )

        if target_agent is None:
            break

        agent_title = target_agent["title"]
        absolute_href = target_agent["absolute_href"]
        relative_href = target_agent["relative_href"]

        print()
        print("-" * 60)
        print(f"삭제 대상 에이전트: {agent_title}")
        print(f"에이전트 링크: {absolute_href}")
        print("-" * 60)

        try:
            delete_single_agent(
                driver,
                target_agent,
            )

            deleted_agents.append(agent_title)

            write_result_csv(
                csv_path=csv_path,
                agent_title=agent_title,
                result="PASS",
                comment="삭제 성공",
            )

            print(f"삭제 성공: {agent_title}")

            time.sleep(0.5)

        except Exception as error:
            error_message = str(error)

            failed_agents.append(
                (
                    agent_title,
                    error_message,
                )
            )

            excluded_hrefs.add(relative_href)

            write_result_csv(
                csv_path=csv_path,
                agent_title=agent_title,
                result="FAIL",
                comment=error_message,
            )

            print(f"삭제 실패: {agent_title}")
            print(f"오류 내용: {error_message}")

            save_failure_screenshot(driver)

    if not deleted_agents and not failed_agents:
        write_no_agent_result(
            csv_path,
            delete_mode,
        )

    return deleted_agents, failed_agents


# ============================================================
# 최종 결과 출력
# ============================================================

def print_final_result(
    delete_mode: str,
    deleted_agents: list[str],
    failed_agents: list[tuple[str, str]],
    csv_path: Path,
) -> None:
    """
    삭제 작업의 최종 결과를 출력합니다.
    """

    print()
    print("=" * 60)
    print("에이전트 삭제 테스트 결과")
    print(
        f"삭제 방식: {get_delete_mode_name(delete_mode)}"
    )
    print(f"삭제 성공: {len(deleted_agents)}개")
    print(f"삭제 실패: {len(failed_agents)}개")

    if deleted_agents:
        print("- 삭제 성공 에이전트")

        for agent_title in deleted_agents:
            print(f"  - {agent_title}")

    if failed_agents:
        print("- 삭제 실패 에이전트")

        for agent_title, error_message in failed_agents:
            print(
                f"  - {agent_title}: {error_message}"
            )

    if failed_agents:
        print("삭제 작업 결과: FAIL")
    else:
        print("삭제 작업 결과: PASS")

    print(f"결과 CSV: {csv_path}")
    print("=" * 60)


# ============================================================
# main
# ============================================================

def main() -> None:
    """
    에이전트 삭제 자동화 프로그램을 실행합니다.
    """

    driver: webdriver.Chrome | None = None
    csv_path: Path | None = None

    try:
        base_url, login_email, login_password = load_env()

        delete_mode = select_delete_mode()

        csv_path = create_result_csv()

        chrome_options = create_chrome_options()

        driver = webdriver.Chrome(
            options=chrome_options,
        )

        driver.set_page_load_timeout(30)

        driver.get(base_url)

        print("테스트 사이트 접속 완료")

        login_if_needed(
            driver=driver,
            base_url=base_url,
            login_email=login_email,
            login_password=login_password,
        )

        print()
        print("=" * 60)
        print("내 에이전트 삭제 테스트 시작")
        print(
            f"삭제 방식: {get_delete_mode_name(delete_mode)}"
        )
        print("=" * 60)

        go_to_private_agents(
            driver=driver,
            base_url=base_url,
            login_email=login_email,
            login_password=login_password,
        )

        deleted_agents, failed_agents = delete_agents(
            driver=driver,
            delete_mode=delete_mode,
            csv_path=csv_path,
        )

        print_final_result(
            delete_mode=delete_mode,
            deleted_agents=deleted_agents,
            failed_agents=failed_agents,
            csv_path=csv_path,
        )

    except Exception as error:
        print()
        print("=" * 60)
        print("deleteagent.py 실행 실패")
        print(f"오류 내용: {error}")
        print("=" * 60)

        if (
            driver is not None
            and csv_path is not None
        ):
            try:
                write_result_csv(
                    csv_path=csv_path,
                    agent_title="전체 실행",
                    result="FAIL",
                    comment=str(error),
                )
            except Exception:
                pass

            try:
                save_failure_screenshot(driver)
            except Exception:
                pass

    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    main()