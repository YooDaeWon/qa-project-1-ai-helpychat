## 가상환경
python -m venv .venv
.\.venv\Scripts\Activate.ps1

## 패키지설치
python -m pip install -r requirements.txt


## 환경변수 설정
copy .env.example .env

프로젝트 루트(src 폴더와 동일 경로)에 `.env` 파일이 생성됩니다.
생성된 `.env` 파일을 열어 본인 계정을 채우세요 (URL은 이미 입력되어 있음):

.env
LOGIN_URL=https://dev-qaproject-helpy-chat.dev.elicer.io/
LOGIN_EMAIL=your_email
LOGIN_PASSWORD=your_password


## 실행

전체 pytest 테스트 수집 및 실행:
pytest -s -v


에이전트 3개 생성:
pytest -s -v tests/agent_management/test_create_agents.py --create-count=3


자동 생성 테스트용 에이전트만 삭제:
pytest -s -v tests/agent_management/test_delete_agents.py --delete-mode=automation


내 에이전트 전체 삭제:
pytest -s -v tests/agent_management/test_delete_agents.py --delete-mode=all


브라우저 화면 없이 실행하려면 `--headless`를 추가합니다.

## 로그인 테스트 실행

```
# 전체 실행 (확인 값 로그 포함)
pytest tests\login\test_login_pj.py --log-cli-level=INFO

# 특정 테스트만 실행 (함수명에 TID가 붙어 있음)
pytest tests\login\test_login_pj.py::test_tid41_login_success --log-cli-level=INFO

# HTML 리포트 생성
pytest tests\login\test_login_pj.py --log-cli-level=INFO --html=report.html --self-contained-html
```

- 로그인 테스트 코드는 `tests\login\` 폴더에 있고, Page Object(`LoginUiPage`)는 `src\pages\login_page.py`에 있습니다.
- 접속하면 영문 페이지로 리다이렉트되므로, 테스트가 언어 드롭다운으로 한국어 페이지로 전환한 뒤 검증합니다.
- `--log-cli-level=INFO` 옵션을 붙이면 각 테스트 아래에 실제 확인 값(화면 문구, 브라우저 말풍선,
  placeholder 등)이 `INFO` 로그로 실시간 출력됩니다. 옵션을 빼면 로그 없이 조용히 실행됩니다.
  (다른 팀원의 실행 방식에 영향을 주지 않도록 공통 설정 파일 대신 옵션 방식을 사용)
- 실패 시에는 assert 메시지로 기대값과 실제값이 함께 표시됩니다.

실행 화면 예시:
```
tests/login/test_login_pj.py::test_tid14_wrong_password
------------------------------ live log call ------------------------------
INFO  화면 문구: '이메일 또는 비밀번호가 일치하지 않습니다.'
PASSED
```

#히스토리 테스트 예시
 1. 히스토리 저장 테스트
python -m pytest tests/test_history/test_history_save.py -v -s --tb=long
 2. 재로그인 후 히스토리 유지 테스트
python -m pytest tests/test_history/test_history_relogin.py -v -s --tb=long
 3. 히스토리 1개 생성 후 삭제 테스트
python -m pytest tests/test_history/test_history_delete.py::test_history_can_be_deleted -v -s --tb=long
 4. 삭제 개수를 직접 입력하는 다중 삭제 테스트
python -m pytest tests/test_history/test_history_delete.py::test_delete_histories_by_count -v -s --tb=long
 5. 삭제 개수를 미리 지정해서 다중 삭제
$env:HISTORY_DELETE_COUNT="3"
python -m pytest tests/test_history/test_history_delete.py::test_delete_histories_by_count -v -s --tb=long
 6. 히스토리 테스트 전체 실행
$env:HISTORY_DELETE_COUNT="1"
python -m pytest tests/test_history -v -s --tb=long