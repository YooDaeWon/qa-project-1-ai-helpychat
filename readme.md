<<<<<<< HEAD
<<<<<<< HEAD
# 🚀 1차 프로젝트: QA 이슈 관리 가이드

본 프로젝트는 실제 현업 개발팀의 워크플로우를 경험하기 위해 **회사 표준 이슈 풀(Issue Pool) 양식**을 사용합니다. 모든 수강생(Racer)은 발견한 결함이나 개선 사항을 아래 가이드에 따라 보고해주시기 바랍니다.

---

## 🛠 1. 이슈 보고 방법 (How to Report)

1. **이슈 생성**: 왼쪽 메뉴의 **Issues** > **[New issue]** 버튼을 클릭합니다.
2. **템플릿 선택**: `Description` 영역 상단의 **[Choose a template]** 드롭다운을 눌러 유형을 선택합니다.
   - `bug_report`: 기능 오류 및 결함 보고
   - `improvement_report`: UI/UX 개선 및 기능 제안
3. **내용 작성**: 양식에 맞춰 내용을 기입합니다. (재현 경로는 상세할수록 좋습니다!)
4. **저장**: 하단의 **[Create issue]**를 누르면 자동으로 기본 라벨이 부여됩니다.

---

## 🏷 2. 라벨(Label) 운영 규정

본 프로젝트는 효율적인 관리를 위해 **Scoped Label(`::`)** 시스템을 사용합니다. 라벨을 변경하면 이전 상태는 자동으로 삭제됩니다.

### 🚦 상태 (Status)
| 라벨명 | 의미 | 비고 |
| :--- | :--- | :--- |
| `상태::TODO` | 확인 및 수정이 필요한 대기 상태 | 이슈 생성 시 기본값 |
| `상태::WON'T DO` | 중복 리포트, 정상 동작, 또는 수정 불필요 판명 시 | 운영진 가이드에 따라 변경 |

### 🛠 업무 유형 (Type)
- `업무유형::버그`: 프로덕트의 기술적 결함
- `업무유형::개선`: 기획적 개선 제안 및 편의성 향상

### ⚡ 우선순위 (Priority)
- `우선순위::P0`: 서비스 이용 불가 등 최우선 수정 필요
- `우선순위::P1~P2`: 주요 기능 오류 및 일반 결함
- `우선순위::P3~P4`: 사소한 UI 오타 및 단순 건의

---

## 💡 유의사항 (Tips for Racers)

- **중복 확인**: 이슈를 올리기 전, 이미 다른 조원이나 수강생이 올린 유사한 내용이 있는지 **Search** 기능을 통해 먼저 확인하세요. (동일 오류는 한 건으로 취합합니다.)
- **데이터 보호**: 재현용 계정 이메일 외에 개인정보(전화번호 등)가 스크린샷에 노출되지 않도록 주의하세요.
- **증거 첨부**: 오류 화면 캡처나 로그 데이터는 해결 속도를 2배 이상 높여줍니다. 본문에 `Ctrl+V`로 바로 붙여넣으세요.

---
=======
# 🚀 1차 프로젝트: QA 이슈 관리 가이드

본 프로젝트는 실제 현업 개발팀의 워크플로우를 경험하기 위해 **회사 표준 이슈 풀(Issue Pool) 양식**을 사용합니다. 모든 수강생(Racer)은 발견한 결함이나 개선 사항을 아래 가이드에 따라 보고해주시기 바랍니다.

---

## 🛠 1. 이슈 보고 방법 (How to Report)

1. **이슈 생성**: 왼쪽 메뉴의 **Issues** > **[New issue]** 버튼을 클릭합니다.
2. **템플릿 선택**: `Description` 영역 상단의 **[Choose a template]** 드롭다운을 눌러 유형을 선택합니다.
   - `bug_report`: 기능 오류 및 결함 보고
   - `improvement_report`: UI/UX 개선 및 기능 제안
3. **내용 작성**: 양식에 맞춰 내용을 기입합니다. (재현 경로는 상세할수록 좋습니다!)
4. **저장**: 하단의 **[Create issue]**를 누르면 자동으로 기본 라벨이 부여됩니다.

---

## 🏷 2. 라벨(Label) 운영 규정

본 프로젝트는 효율적인 관리를 위해 **Scoped Label(`::`)** 시스템을 사용합니다. 라벨을 변경하면 이전 상태는 자동으로 삭제됩니다.

### 🚦 상태 (Status)
| 라벨명 | 의미 | 비고 |
| :--- | :--- | :--- |
| `상태::TODO` | 확인 및 수정이 필요한 대기 상태 | 이슈 생성 시 기본값 |
| `상태::WON'T DO` | 중복 리포트, 정상 동작, 또는 수정 불필요 판명 시 | 운영진 가이드에 따라 변경 |

### 🛠 업무 유형 (Type)
- `업무유형::버그`: 프로덕트의 기술적 결함
- `업무유형::개선`: 기획적 개선 제안 및 편의성 향상

### ⚡ 우선순위 (Priority)
- `우선순위::P0`: 서비스 이용 불가 등 최우선 수정 필요
- `우선순위::P1~P2`: 주요 기능 오류 및 일반 결함
- `우선순위::P3~P4`: 사소한 UI 오타 및 단순 건의

---

## 💡 유의사항 (Tips for Racers)

- **중복 확인**: 이슈를 올리기 전, 이미 다른 조원이나 수강생이 올린 유사한 내용이 있는지 **Search** 기능을 통해 먼저 확인하세요. (동일 오류는 한 건으로 취합합니다.)
- **데이터 보호**: 재현용 계정 이메일 외에 개인정보(전화번호 등)가 스크린샷에 노출되지 않도록 주의하세요.
- **증거 첨부**: 오류 화면 캡처나 로그 데이터는 해결 속도를 2배 이상 높여줍니다. 본문에 `Ctrl+V`로 바로 붙여넣으세요.

---
>>>>>>> 4e9249a (Initial commit)
*문의사항은 QA 트랙 운영 매니저에게 전달 바랍니다.*
=======
## 깃 업로드순서
git add
git commit -m "(커밋내용)"
git push origin "develop"

## 필수 라이브러리 설치
python -m pip install -r requirements.txt


## 생성 자동화 테스트 실행코드
python ".\src\agent_management\createagent.py"


## 삭제 자동화 테스트 실행코드
python ".\src\agent_management\deleteagent.py"

---

# 1. 로그인 테스트 가상환경 생성 및 활성화
```
python -m venv .venv
.venv\Scripts\activate
```

# 2. 패키지 설치
```
pip install -r requirements.txt
#위 명령어 실행 안될 시 
pip install selenium
pip install pytest
pip install python-dotenv
pip install pytest-html
pip install pytest-sugar
```

# 3. 계정 파일 생성
```
copy .env.example .env
```
프로젝트 루트(src 폴더와 동일 경로)에 `.env` 파일이 생성됩니다.
생성된 `.env` 파일을 열어 **본인 계정**을 채우세요 (URL은 이미 입력되어 있음):

```
LOGIN_URL=https://dev-qaproject-helpy-chat.dev.elicer.io/
LOGIN_EMAIL=본인계정
LOGIN_PASSWORD=본인비밀번호
```

# 4. 테스트 실행
```
# 전체 실행 (확인 값 로그 포함)
pytest src\Elice_Login\test_login_pj.py --log-cli-level=INFO

# 특정 테스트만 실행 (함수명에 TID가 붙어 있음)
pytest src\Elice_Login\test_login_pj.py::test_tid41_login_success --log-cli-level=INFO

# HTML 리포트 생성
pytest src\Elice_Login\test_login_pj.py --log-cli-level=INFO --html=report.html --self-contained-html
```
- 로그인 테스트 코드는 `src\Elice_Login\` 폴더에 있습니다 (`conftest.py` + `test_login_pj.py`).
- 접속하면 영문 페이지로 리다이렉트되므로, 테스트가 언어 드롭다운으로 한국어 페이지로 전환한 뒤 검증합니다.
- `--log-cli-level=INFO` 옵션을 붙이면 각 테스트 아래에 실제 확인 값(화면 문구, 브라우저 말풍선,
  placeholder 등)이 `INFO` 로그로 실시간 출력됩니다. 옵션을 빼면 로그 없이 조용히 실행됩니다.
  (다른 팀원의 실행 방식에 영향을 주지 않도록 공통 설정 파일 대신 옵션 방식을 사용)
- 실패 시에는 assert 메시지로 기대값과 실제값이 함께 표시됩니다.

실행 화면 예시:
```
src/Elice_Login/test_login_pj.py::test_tid14_wrong_password
------------------------------ live log call ------------------------------
INFO  화면 문구: '이메일 또는 비밀번호가 일치하지 않습니다.'
PASSED
```
>>>>>>> develop
