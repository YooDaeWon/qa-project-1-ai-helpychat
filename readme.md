# 1. 가상환경 생성 및 활성화
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
# 전체 실행 + HTML 리포트 생성
pytest src\Elice_Login\test_login_pj.py -v --html=report.html --self-contained-html

# 특정 테스트만 실행 (함수명에 TID가 붙어 있음)
pytest src\Elice_Login\test_login_pj.py::test_tid40_login_success -v
```
- 로그인 테스트 코드는 `src\Elice_Login\` 폴더에 있습니다 (`conftest.py` + `test_login_pj.py`).
- 접속하면 영문 페이지로 리다이렉트되므로, 테스트가 언어 드롭다운으로 한국어 페이지로 전환한 뒤 검증합니다.
- 실패 원인은 assert 메시지로 출력되므로 `-s` 옵션은 필요 없습니다.
