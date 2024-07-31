import os
import time
import requests
import shutil 

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

options = Options()
options.add_argument("--headless")
options.set_preference("pdfjs.disabled", True)



driver = webdriver.Firefox(options)
driver.get("https://www.durhamnc.gov/Archive.aspx?AMID=195")
driver.implicitly_wait(5)
test = driver.find_element(By.XPATH, '//a[contains(@href,"ADID=7013")]')
test.click()

