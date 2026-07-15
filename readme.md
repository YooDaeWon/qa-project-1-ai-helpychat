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