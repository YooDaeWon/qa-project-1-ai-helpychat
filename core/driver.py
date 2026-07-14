from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_driver():
    """
    Chrome WebDriver 생성
    """

    options = Options()

    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    return driver
