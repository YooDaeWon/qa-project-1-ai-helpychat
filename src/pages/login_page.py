from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config.config import LOGIN_URL, LOGIN_EMAIL, LOGIN_PASSWORD, WAIT_TIME


class LoginPage:
    def __init__(self, driver):
        self.driver = driver

    def login(self):

        self.driver.get(LOGIN_URL)

        email = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.NAME, "loginId"))
        )
        email.send_keys(LOGIN_EMAIL)

        password = self.driver.find_element(By.NAME, "password")
        password.send_keys(LOGIN_PASSWORD)

        login_button = self.driver.find_element(
            By.CSS_SELECTOR, "button[type='submit']"
        )
        login_button.click()
