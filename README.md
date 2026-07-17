Error404 테스트 실행 가이드

## 1. 실행 환경 설정

### 1.1. 가상환경 생성 및 활성화

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 1.2. 패키지 설치

```powershell
python -m pip install -r requirements.txt
```

### 1.3. 환경변수 설정

```powershell
Copy-Item .env.example .env
```

프로젝트 루트(`src` 폴더와 동일한 경로)에 생성된 `.env` 파일을 열고 본인 계정 정보를 입력합니다.
`LOGIN_URL`은 기본값이 입력되어 있습니다.

```dotenv
LOGIN_URL=https://dev-qaproject-helpy-chat.dev.elicer.io/
LOGIN_EMAIL=your_email
LOGIN_PASSWORD=your_password
```

## 2. 전체 테스트 실행

전체 pytest 테스트를 수집하고 실행합니다.

```powershell
python -m pytest -s -v
```

브라우저 화면 없이 실행하려면 명령어 마지막에 `--headless` 옵션을 추가합니다.

```powershell
python -m pytest -s -v --headless
```

## 3. 에이전트 관리 테스트

### 3.1. 에이전트 3개 생성

```powershell
python -m pytest -s -v tests/agent_management/test_create_agents.py --create-count=3
```

### 3.2. 자동 생성 테스트용 에이전트만 삭제

```powershell
python -m pytest -s -v tests/agent_management/test_delete_agents.py --delete-mode=automation
```

### 3.3. 내 에이전트 전체 삭제

> 주의: 현재 계정의 모든 에이전트가 삭제됩니다.

```powershell
python -m pytest -s -v tests/agent_management/test_delete_agents.py --delete-mode=all
```

## 4. 로그인 테스트

로그인 테스트 코드는 `tests/login/` 폴더에 있으며, Page Object인 `LoginUiPage`는
`src/pages/login_page.py`에 있습니다.

- 접속 시 영문 페이지로 리다이렉트되므로 언어 드롭다운에서 한국어로 전환한 뒤 검증합니다.
- `--log-cli-level=INFO` 옵션을 사용하면 화면 문구, 브라우저 말풍선, placeholder 등의 실제 확인 값이 출력됩니다.
- 해당 옵션을 생략하면 로그 없이 실행됩니다.
- 테스트 실패 시 assert 메시지에 기대값과 실제값이 함께 표시됩니다.

### 4.1. 로그인 테스트 전체 실행

```powershell
python -m pytest tests/login/test_login_pj.py --log-cli-level=INFO
```

### 4.2. 특정 로그인 테스트 실행

테스트 함수명에 지정된 TID를 사용합니다.

```powershell
python -m pytest tests/login/test_login_pj.py::test_tid41_login_success --log-cli-level=INFO
```

### 4.3. HTML 리포트 생성

```powershell
python -m pytest tests/login/test_login_pj.py --log-cli-level=INFO --html=report.html --self-contained-html
```

### 4.4. 실행 결과 예시

```text
tests/login/test_login_pj.py::test_tid14_wrong_password
------------------------------ live log call ------------------------------
INFO  화면 문구: '이메일 또는 비밀번호가 일치하지 않습니다.'
PASSED
```

## 5. 히스토리 테스트

### 5.1. 히스토리 저장 테스트

```powershell
python -m pytest tests/test_history/test_history_save.py -v -s --tb=long
```

### 5.2. 재로그인 후 히스토리 유지 테스트

```powershell
python -m pytest tests/test_history/test_history_relogin.py -v -s --tb=long
```

### 5.3. 히스토리 단건 생성 및 삭제 테스트

```powershell
python -m pytest tests/test_history/test_history_delete.py::test_history_can_be_deleted -v -s --tb=long
```

### 5.4. 삭제 개수를 직접 입력하는 다중 삭제 테스트

> 주의: 현재 화면에 표시된 일반 대화와 자동화 대화를 합쳐 위에서부터 입력한 개수만큼 삭제합니다.

```powershell
python -m pytest tests/test_history/test_history_delete.py::test_delete_histories_by_count -v -s --tb=long
```

### 5.5. 삭제 개수를 미리 지정하는 다중 삭제 테스트

다음 예시는 화면 위에서부터 히스토리 3개를 삭제합니다.

```powershell
$env:HISTORY_DELETE_COUNT="3"
python -m pytest tests/test_history/test_history_delete.py::test_delete_histories_by_count -v -s --tb=long
```

### 5.6. 히스토리 테스트 전체 실행

다중 삭제 테스트가 입력을 기다리지 않도록 삭제 개수를 미리 지정합니다.

```powershell
$env:HISTORY_DELETE_COUNT="1"
python -m pytest tests/test_history -v -s --tb=long
```
