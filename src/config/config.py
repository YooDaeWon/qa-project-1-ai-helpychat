<<<<<<< HEAD
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_LOGIN_URL = "https://dev-qaproject-helpy-chat.dev.elicer.io/"
DEFAULT_WAIT_TIME = 15
PAGE_WAIT_TIME = 40
SHORT_WAIT_TIME = 5
MAX_SCROLL_COUNT = 25
MAX_LIST_SCAN_COUNT = 120
SCROLL_WAIT_TIME = 0.5


def find_project_root() -> Path:
    """현재 파일 위치를 기준으로 프로젝트 루트를 반환합니다."""
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = find_project_root()
ENV_PATH = PROJECT_ROOT / ".env"

# 모듈 import 시에는 .env가 없어도 오류를 발생시키지 않습니다.
# 실제 테스트 실행 시 load_settings()에서 필수 값을 검증합니다.
load_dotenv(dotenv_path=ENV_PATH if ENV_PATH.exists() else None, override=False)

# 기존 팀 코드와의 호환을 위한 상수입니다.
LOGIN_URL = os.getenv("LOGIN_URL", DEFAULT_LOGIN_URL).strip()
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL", "").strip()
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "").strip()
WAIT_TIME = DEFAULT_WAIT_TIME


@dataclass(frozen=True)
class Settings:
    """에이전트 자동화와 공통 테스트에서 사용하는 환경설정입니다."""

    project_root: Path
    env_path: Path
    login_url: str
    login_email: str
    login_password: str
    default_wait_time: int = DEFAULT_WAIT_TIME
    page_wait_time: int = PAGE_WAIT_TIME
    short_wait_time: int = SHORT_WAIT_TIME
    max_scroll_count: int = MAX_SCROLL_COUNT
    max_list_scan_count: int = MAX_LIST_SCAN_COUNT
    scroll_wait_time: float = SCROLL_WAIT_TIME

    @property
    def base_url(self) -> str:
        return self.login_url.rstrip("/")

    @property
    def new_chat_url(self) -> str:
        return f"{self.base_url}/#agents-organization"

    @property
    def builder_url(self) -> str:
        return f"{self.base_url}/agents/builder"

    @property
    def artifacts_dir(self) -> Path:
        return self.project_root / "artifacts"


def find_env_path(project_root: Path) -> Path:
    """프로젝트 루트 또는 현재 작업 폴더에서 .env 파일을 찾습니다."""
    candidates = [
        project_root / ".env",
        Path.cwd() / ".env",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        ".env 파일을 찾을 수 없습니다. 프로젝트 루트에 .env 파일을 만들고 "
        "LOGIN_URL, LOGIN_EMAIL, LOGIN_PASSWORD를 입력하세요."
    )


def load_settings() -> Settings:
    """.env를 읽고 필수 환경변수를 검증합니다."""
    project_root = find_project_root()
    env_path = find_env_path(project_root)

    load_dotenv(dotenv_path=env_path, override=True)

    login_url = os.getenv("LOGIN_URL", DEFAULT_LOGIN_URL).strip().rstrip("/")
    login_email = os.getenv("LOGIN_EMAIL", "").strip()
    login_password = os.getenv("LOGIN_PASSWORD", "").strip()

    missing_values: list[str] = []

    if not login_url:
        missing_values.append("LOGIN_URL")
    if not login_email:
        missing_values.append("LOGIN_EMAIL")
    if not login_password:
        missing_values.append("LOGIN_PASSWORD")

    if missing_values:
        raise ValueError(
            ".env에 다음 환경변수를 입력해주세요: " + ", ".join(missing_values)
        )

    settings = Settings(
        project_root=project_root,
        env_path=env_path,
        login_url=login_url,
        login_email=login_email,
        login_password=login_password,
    )

    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    (settings.artifacts_dir / "failures").mkdir(parents=True, exist_ok=True)

    print(f".env 읽기 완료: {env_path}")
    print(f"테스트 기준 URL 설정 완료: {settings.base_url}")

    return settings
=======
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ===============================
# URL
# ===============================
LOGIN_URL = os.getenv("LOGIN_URL")

# ===============================
# 계정 정보
# ===============================
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")

# ===============================
# 대기 시간
# ===============================
WAIT_TIME = 10
>>>>>>> 유대원
