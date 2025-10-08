# from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from time import sleep


def click_element(self, tag, feature, value):
    self.wait = WebDriverWait(self.driver, 20)
    xpath = f"//{tag}[@{feature}='{value}']"
    if feature == "text":
        xpath = f"//{tag}[{feature}()='{value}']"
    self.wait.until(ec.visibility_of_element_located((By.XPATH, xpath))).click()
    sleep(1)
    self.logger.info(f"clicked {xpath}")
    return


def click_element_by_index(self, tag, feature, value, index):
    self.wait = WebDriverWait(self.driver, 20)
    xpath = f"//{tag}[@{feature}='{value}']"
    if feature == "text":
        xpath = f"//{tag}[{feature}()='{value}']"
    self.wait.until(ec.visibility_of_element_located((By.XPATH, xpath)))
    self.driver.find_elements(By.XPATH, xpath)[index].click()
    sleep(1)
    self.logger.info(f"clicked {xpath}")
    return


def click_element_previous(self, tag, feature, value, previous_tag, steps):
    self.wait = WebDriverWait(self.driver, 20)
    xpath = f"//{tag}[@{feature}='{value}']/preceding-sibling::{previous_tag}[{steps}]"
    if feature == "text":
        xpath = (
            f"//{tag}[{feature}()='{value}']/preceding-sibling::{previous_tag}[{steps}]"
        )
        if xpath.count("'") > 2:
            xpath = f'//{tag}[{feature}()="{value}"]/preceding-sibling::{previous_tag}[{steps}]'
    self.wait.until(ec.visibility_of_element_located((By.XPATH, xpath))).click()
    sleep(1)
    self.logger.info(f"clicked {xpath}")
    return


def click_element_next(self, tag, feature, value, next_tag, steps):
    self.wait = WebDriverWait(self.driver, 20)
    xpath = f"//{tag}[@{feature}='{value}']/following-sibling::{next_tag}[{steps}]"
    if feature == "text":
        xpath = f"//{tag}[{feature}()='{value}']/following-sibling::{next_tag}[{steps}]"
        if xpath.count("'") > 2:
            xpath = (
                f'//{tag}[{feature}()="{value}"]/following-sibling::{next_tag}[{steps}]'
            )
    self.wait.until(ec.visibility_of_element_located((By.XPATH, xpath))).click()
    sleep(1)
    self.logger.info(f"clicked {xpath}")
    return


def check_for_element(self, tag, feature, value):
    xpath = f"//{tag}[@{feature}='{value}']"
    if feature == "text":
        xpath = f"//{tag}[{feature}()='{value}']"
    element = self.driver.find_element(By.XPATH, xpath)
    sleep(1)
    if element:
        self.logger.info(f"found {xpath}")
        return True
    return False


def wait_for_element(self, tag, feature, value, wait=20):
    self.wait = WebDriverWait(self.driver, wait)
    xpath = f"//{tag}[@{feature}='{value}']"
    if feature == "text":
        xpath = f"//{tag}[{feature}()='{value}']"
    self.wait.until(ec.visibility_of_element_located((By.XPATH, xpath)))
    sleep(1)
    self.logger.info(f"found {xpath}")


def click_select_element_value(self, tag, feature, value, option):
    wait_for_element(self, tag, feature, value)
    xpath = f"//{tag}[@{feature}='{value}']"
    if feature == "text":
        xpath = f"//{tag}[{feature}()='{value}']"
    element = self.driver.find_element(By.XPATH, xpath)
    select = Select(element)
    select.select_by_visible_text(option)
    sleep(1)
    self.logger.info(f"selected option {xpath}")


def hide_element(self, xpath):
    self.driver.execute_script(
        "arguments[0].style.visibility='hidden'",
        self.driver.find_element(By.XPATH, xpath),
    )
    sleep(1)
    self.logger.info(f"hid {xpath}")
    return


def drag_element(self, element_from, element_to):
    tag_from, feature_from, value_from = element_from
    tag_to, feature_to, value_to = element_to
    self.wait = WebDriverWait(self.driver, 20)

    xpath_from = f"//{tag_from}[@{feature_from}='{value_from}']"
    if feature_from == "text":
        xpath_from = f"//{tag_from}[{feature_from}()='{value_from}']"
    xpath_to = f"//{tag_to}[@{feature_to}='{value_to}']"
    if feature_to == "text":
        xpath_to = f"//{tag_to}[{feature_to}()='{value_to}']"
    drag = WebDriverWait(self.driver, 20).until(
        ec.element_to_be_clickable((By.XPATH, xpath_from))
    )
    drop = WebDriverWait(self.driver, 20).until(
        ec.element_to_be_clickable((By.XPATH, xpath_to))
    )
    ActionChains(self.driver).drag_and_drop(drag, drop).perform()
    sleep(1)
    self.logger.info(f"dragged {xpath_from} to {xpath_to}")
    return
