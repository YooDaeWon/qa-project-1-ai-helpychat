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
