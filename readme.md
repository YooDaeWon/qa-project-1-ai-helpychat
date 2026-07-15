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
