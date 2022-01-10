import time

from selenium import webdriver
from selenium.webdriver.support.ui import Select,WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_binary
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')    # ヘッドレスモードに
driver = webdriver.Chrome()
wait = WebDriverWait(driver,10)