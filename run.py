from core.driver import get_driver
from pages.login_page import LoginPage

# Chrome 실행
driver = get_driver()

try:
    # 로그인 객체 생성
    login_page = LoginPage(driver)

    # 로그인 실행
    login_page.login()

    input("로그인이 완료되었습니다. Enter를 누르면 종료합니다.")

finally:
    driver.quit()
