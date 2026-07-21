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
- 테스트 실패 시 assert 메시지에 기대값과 실제값이 함께 표시되고,
  실패 순간의 화면이 `artifacts/failures/` 폴더에 자동 저장됩니다.

### 4.1. 로그인 테스트 전체 실행

`login` 마커가 등록되어 있어 경로 대신 마커로 실행할 수 있습니다.

```powershell
python -m pytest -m login --log-cli-level=INFO
```

### 4.2. 특정 로그인 테스트 실행

단독 함수로 작성된 테스트는 함수명의 TID를 사용합니다.

```powershell
python -m pytest tests/login/test_login_pj.py::test_tid41_login_success --log-cli-level=INFO
```

파라미터화된 테스트(TID 12\~16, 30\~33 등)는 `-k` 옵션으로 TID를 지정합니다.

```powershell
python -m pytest tests/login -k "TID13" --log-cli-level=INFO
```

### 4.3. HTML 리포트 생성

```powershell
python -m pytest tests/login/test_login_pj.py --log-cli-level=INFO --html=report.html --self-contained-html
```

### 4.4. 실행 결과 예시

아래 명령어로 TID 14(비밀번호 불일치) 케이스를 실행한 결과입니다.

```powershell
python -m pytest tests/login -k "TID14" --log-cli-level=INFO
```

```text
tests/login/test_login_pj.py::test_login_server_validation[TID14-wrong-password]
-------------------------------- live log call --------------------------------
INFO     src.pages.login_page:login_page.py:286 화면 문구: '이메일 또는 비밀번호가 일치하지 않습니다.'
PASSED
```


## 5. 입력창 입력값, 응답 영역 기본 기능 및 예외 질문 동작 / AI 답변 테스트

테스트 코드 폴더 : tests/response_and_exception_test

### 5.1. 한글, 영문, 숫자, 한·영·숫자 혼합 입력 검증 테스트

```powershell
python -m pytest tests/response_and_exception_test/test_001_input_mix.py -v -s
```

입력한 값들이 정상적으로 입력되며, 질문 전송 및 AI 답변이 출력됩니다.

### 5.2. 동일한 반복 질문 10회 이상 질의응답 시 AI 답변 테스트

```powershell
python -m pytest tests/response_and_exception_test/test_002_repeat_question.py -v -s
```

동일한 질문을 10회 반복 요청 시 AI가 동일한 내용을 포함한 답변을 출력합니다.

### 5.3. 긴 텍스트 입력 길이별 AI 응답 처리 검증 테스트

```powershell
python -m pytest tests/response_and_exception_test/test_003_long_question.py -v -s
```

100자, 500자, 1000자 입력 시 질문이 입력 및 전송되며 AI가 답변합니다.

### 5.4. 입력창 부가 기능(+ 버튼) 동작 검증 테스트

```powershell
python -m pytest tests/response_and_exception_test/test_004_plus_button.py -v -s
```

'+' 버튼의 이미지 생성, 웹 검색, 파일 업로드 기능을 활용하여 질문 시 AI가 답변합니다.

### 5.5. 대용량 문자 입력 자동화 처리 안정성 테스트

```powershell
python -m pytest tests/response_and_exception_test/test_005_large_input_length.py -v -s
```

자동화 환경에서 대용량 문자 입력 처리 시 입력 처리 및 질문이 전송되며 AI가 답변합니다.

### 5.6. AI 대화 문맥 유지 및 기억력 검증 테스트

```powershell
python -m pytest tests/response_and_exception_test/test_006_context_maintenance.py -v -s
```

이전 대화 내용을 기억하고 문맥을 유지하며, 질문 시 AI가 이를 기억하여 답변합니다.

### 5.7. "AI 헬피 추천 질문" 기능 동작 검증 테스트

```powershell
python -m pytest tests/response_and_exception_test/test_007_recommend_question.py -v -s
```

AI 헬피 추천 질문을 선택하여 질문 시 AI가 질문을 확인하고 답변합니다.

### 5.8. 예외 및 특수 입력 처리 안정성 테스트

```powershell
python -m pytest tests/response_and_exception_test/test_008_various_inputs.py -v -s
```

특수문자, 이모지, URL, 날짜 등 다양한 예외 입력을 인식하고 처리하며 AI가 답변합니다.


## 6. 히스토리 테스트

### 6.1. 히스토리 저장 테스트

```powershell
python -m pytest tests/test_history/test_history_save.py -v -s --tb=long
```

### 6.2. 재로그인 후 히스토리 유지 테스트

```powershell
python -m pytest tests/test_history/test_history_relogin.py -v -s --tb=long
```

### 6.3. 히스토리 단건 생성 및 삭제 테스트

```powershell
python -m pytest tests/test_history/test_history_delete.py::test_history_can_be_deleted -v -s --tb=long
```

### 6.4. 삭제 개수를 직접 입력하는 다중 삭제 테스트

`--interactive-history-delete` 옵션을 사용하면 테스트 실행 중 삭제할 개수를 직접 입력할 수 있습니다.

```powershell
python -m pytest tests/test_history/test_history_delete.py::test_delete_histories_by_count -v -s --tb=long --interactive-history-delete
```

### 6.5. 삭제 개수를 미리 지정하는 다중 삭제 테스트

다음 예시는 화면 위에서부터 히스토리 3개를 삭제합니다.

> 주의: 현재 화면에 표시된 일반 대화와 자동화 대화를 합쳐 위에서부터 지정한 개수만큼 삭제합니다.

```powershell
$env:HISTORY_DELETE_COUNT="3"
python -m pytest tests/test_history/test_history_delete.py::test_delete_histories_by_count -v -s --tb=long
Remove-Item Env:HISTORY_DELETE_COUNT
```

### 6.6. 히스토리 테스트 전체 실행

`HISTORY_DELETE_COUNT`와 `--interactive-history-delete`를 지정하지 않으면 다중 삭제 테스트는
입력을 기다리지 않고 자동으로 건너뛰며, 나머지 테스트는 정상 실행됩니다.

```powershell
Remove-Item Env:HISTORY_DELETE_COUNT -ErrorAction SilentlyContinue
python -m pytest tests/test_history -v -s --tb=long
```
