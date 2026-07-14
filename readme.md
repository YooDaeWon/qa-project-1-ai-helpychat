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
copy .env.example .env
```
src 파일과 동일 경로에 .env 파일 생성
5번 후 생성된 `.env` 파일을 열어 **본인 계정**을 채우세요 (URL은 이미 입력되어 있음):

```
LOGIN_URL=https://dev-qaproject-helpy-chat.dev.elicer.io/
LOGIN_EMAIL=본인계정
LOGIN_PASSWORD=본인비밀번호
```

# 전체 실행 + HTML 리포트 생성
pytest src\test_login_pj.py -v -s --html=report.html --self-contained-html

# 특정 테스트만 실행
pytest src\test_login_pj.py::test_login_success -v -s
```