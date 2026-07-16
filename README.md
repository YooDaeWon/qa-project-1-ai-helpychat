# error404 QA 자동화 프로젝트

AI Helpy Chat을 대상으로 Selenium과 pytest를 사용해 로그인, 에이전트 관리, 응답 및 예외 처리 기능을 검증하는 프로젝트입니다.

## 프로젝트 구조

```text
error404/
├─ src/
│  ├─ config/
│  ├─ core/
│  ├─ pages/
│  └─ utils/
├─ tests/
│  ├─ agent_management/
│  ├─ login/
│  └─ response_and_exception_test/
├─ test_004_upload_data/
├─ artifacts/
├─ conftest.py
├─ pytest.ini
├─ requirements.txt
└─ .env.example
```

## 1. 가상환경 생성 및 활성화

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. 패키지 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. 환경변수 설정

```powershell
Copy-Item .env.example .env
```

프로젝트 루트의 `.env` 파일에 본인 계정을 입력합니다.

```env
LOGIN_URL=https://dev-qaproject-helpy-chat.dev.elicer.io/
LOGIN_EMAIL=your_email
LOGIN_PASSWORD=your_password
```

`.env` 파일은 Git에 올리지 않습니다.

## 4. 테스트 실행

### 전체 테스트

```powershell
python -m pytest -s -v
```

### 에이전트 생성 테스트

```powershell
python -m pytest -s -v tests/agent_management/test_create_agents.py --create-count=1
```

### 에이전트 삭제 테스트

```powershell
python -m pytest -s -v tests/agent_management/test_delete_agents.py --delete-mode=automation
```

전체 에이전트를 삭제하려면 다음 옵션을 사용합니다.

```powershell
python -m pytest -s -v tests/agent_management/test_delete_agents.py --delete-mode=all
```

### 응답 및 예외 처리 테스트

```powershell
python -m pytest -s -v tests/response_and_exception_test
```

### 로그인 테스트

```powershell
python -m pytest -s -v tests/login
```

### Headless 실행

```powershell
python -m pytest -s -v --headless
```

### HTML 리포트 생성

```powershell
python -m pytest -s -v --html=report.html --self-contained-html
```

## 테스트 결과 파일

- 삭제 결과 CSV: `artifacts/deleteagent_result_*.csv`
- 실패 스크린샷: `artifacts/failures/*.png`

위 결과 파일은 `.gitignore`에 의해 Git에서 제외됩니다.

## Git 업로드 기본 순서

```powershell
git status
git add .
git commit -m "커밋 내용"
git push origin 브랜치명
```

## 이슈 등록

GitLab에서 이슈를 생성할 때 `.gitlab/issue_templates/`의 버그 및 개선 템플릿을 사용할 수 있습니다.
