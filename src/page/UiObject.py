import glob
import random
import string
from collections import Counter
from datetime import datetime, date, timedelta
import csv
from re import search

import pandas

import openpyxl
from selenium.common import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from src.page.Browser import *
from src.page.utils.LogCustom import logger


def current_time():
    now = datetime.now()
    current = now.strftime("%H:%M:%S")
    today = date.today()
    return "Started run date {} at time {}".format(today, current)


def round_well(obtained_value, calculated_value, looseness_value=0.001000):
    if obtained_value == calculated_value:
        return obtained_value
    elif (obtained_value + looseness_value or obtained_value - looseness_value) == calculated_value:
        return calculated_value
    else:
        return obtained_value


def round_well_with_rank(obtained_value, calculated_value, looseness_value=0.001000):
    if obtained_value == calculated_value:
        return obtained_value
    elif abs(obtained_value - calculated_value) <= looseness_value:
        return calculated_value
    else:
        return obtained_value


def passed_argument():
    pass  # pass is pass


class UiObject:
    LOAD = By.CLASS_NAME, "overlay"

    def __init__(self, by, locator, **kwargs):
        self.__by = by
        self.__locator = locator
        self.__web_element = kwargs.get("web_element", None)

    @staticmethod
    def switch_window():
        try:
            driver = Browser.get_driver()
            driver.switch_to.window(driver.window_handles[1])
            return driver.current_url
        except:
            passed_argument()

    @staticmethod
    def remove_all_file(detail_path="download"):
        import os

        dir = ROOT_DIR + f"/{detail_path}"
        logger.info(f"Deleting - {dir}")
        init = "init.txt"
        for files in os.listdir(dir):
            if files != init:
                os.remove(os.path.join(dir, files))

    @staticmethod
    def validate_download_file():
        time.sleep(10)
        archive = next(os.walk(ROOT_DIR + "/download/"))[2]
        number_files = len(archive)
        if number_files >= 2:
            passed_argument()
            return True
        else:
            return False

    @staticmethod
    def get_name_file():
        return os.listdir(ROOT_DIR_DOWNLOAD)

    @staticmethod
    def js_element(js_web_element, wait=1):
        js = Browser.get_driver()
        js.execute_script("arguments[0].checked = true;", js_web_element)
        js.execute_script(js_web_element)

    @staticmethod
    def switch_frame(xpath_frame):
        try:
            driver = Browser.get_driver()
            driver.switch_to_default_content()
            iframe = driver.find_elements_by_xpath(xpath_frame)
            driver.switch_to.frame(iframe[0])
        except:
            passed_argument()

    @staticmethod
    def default_content_frame():
        driver = Browser.get_driver()
        driver.switch_to.default_content()

    @staticmethod
    def from_web_element(web_element):
        return UiObject(by=None, locator=None, web_element=web_element)

    def get_element(self, wait=20):
        if self.__web_element:
            return self.__web_element
        self.wait_to_appear(wait)
        return Browser.get_driver().find_element(self.by, self.locator)

    def get_elements(self, wait=60):
        if self.__web_element:
            return [self.__web_element]
        self.wait_to_appear(wait)
        return Browser.get_driver().find_elements(self.by, self.locator)

    @property
    def locator(self):
        return self.__locator

    @property
    def by(self):
        return self.__by

    def exists(self, wait=10):
        try:
            WebDriverWait(Browser.get_driver(), wait).until(
                EC.presence_of_element_located((self.by, self.locator)))
            return True
        except:
            UiObject.screen(EC)
            return False

    def visible(self, wait=15):
        try:
            WebDriverWait(Browser.get_driver(), wait).until(
                EC.invisibility_of_element_located((self.by, self.locator)))
            return False
        except:
            return True

    def clickable(self, wait=20):
        try:
            WebDriverWait(Browser.get_driver(), wait).until(
                EC.element_to_be_clickable((self.by, self.locator)))
            return True
        except:
            return False

    def wait_to_appear(self, wait=60):
        if self.exists(wait):
            return self
        raise AssertionError("Locator did not appear: {} in {} seconds!"
                             .format(self.locator, wait))

    def wait_to_appear_long_time(self, wait=120):
        if self.exists(wait):
            return self
        raise AssertionError("Locator did not appear: {} in {} seconds!".format(self.locator, wait))

    def wait_to_disappear(self, wait=500):
        if not self.visible(wait):
            return self
        raise AssertionError("Locator did not disappear: {} in {} seconds!"
                             .format(self.locator, wait))

    def element_not_preset(self, wait=120):
        if self.visible(wait):
            return True
        else:
            return False

    def wait_to_be_clickable(self, wait=20):
        if self.clickable(wait):
            return self
        if self.exists():
            raise AssertionError("Locator did not become click-able: {} in {} seconds"
                                 .format(self.locator, wait))
        raise AssertionError("Locator does not exist: {}".format(self.locator))

    def get_text(self, encoding=None, wait=5):
        counter = 1
        text = self.get_element(wait).text
        while text == '' and counter < 10:
            text = self.get_element(wait).text
            counter = counter + 1
            time.sleep(0.2)
        return text.encode(encoding) if encoding else text

    @staticmethod
    def validate_load_pro(element, wait):
        try:
            wait_element = WebDriverWait(Browser.get_driver(), wait)
            wait_element.until(EC.presence_of_element_located(element))
            wait_element.until(EC.invisibility_of_element_located(element))
        except TimeoutException:
            pass

    def set_text(self, value, wait=20):
        self.get_element(wait).clear()
        self.get_element(wait).send_keys(value)
        return self

    def upload_file(self, value, wait=20):
        self.get_element(wait).send_keys(value)
        return self

    def set_space_key(self, value, wait=5):
        self.get_element(wait).send_keys(Keys.CONTROL + value)
        time.sleep(2)
        self.get_element(wait).send_keys(Keys.SPACE)
        return self

    def press_key(self, key, use_ac=False, wait=5):
        if use_ac:
            ActionChains(Browser.get_driver()).send_keys(key).perform()
        else:
            self.get_element(wait).send_keys(key)
        return self

    @staticmethod
    def force_press_key(key):
        ActionChains(Browser.get_driver()).send_keys(key).perform()

    def get_attribute(self, value, wait=5):
        return self.get_element(wait).get_attribute(value)

    def click(self, use_ac=False, wait=5):
        try:
            if use_ac:
                ActionChains(Browser.get_driver()).move_to_element(
                    self.get_element(wait)).perform().click()
            else:
                self.get_element(wait).click()
            return self
        except Exception:
            UiObject.screen(self.locator)
            return self

    def submit(self, use_ac=False, wait=5):
        ActionChains(Browser.get_driver()).move_to_element(
            self.get_element(wait)).send_keys(Keys.ENTER).perform()

    def enter(self, use_ac=False, wait=5):
        ActionChains(Browser.get_driver()).move_to_element(
            self.get_element(wait)).send_keys(Keys.ENTER).perform()

    def move(self, wait=5):
        Browser.get_driver().execute_script("arguments[0].scrollIntoView();", self.get_element(wait))

    def move_to_element(self, wait=5):
        ActionChains(Browser.get_driver()).move_to_element(
            self.get_element(wait)).perform()

    def double_click(self, wait=5):
        ActionChains(Browser.get_driver()).move_to_element(
            self.get_element(wait)).double_click().perform()

    @staticmethod
    def get_text_table(element_father, element_son):
        time.sleep(1)
        tr = UiObject.get_elements(element_father)
        list_need = []

        for registry in tr:
            n_opers = registry.find_elements(By.CLASS_NAME, element_son)
            for value in n_opers:
                value_text = value.text
                if value_text is None:
                    print(value)
                list_need.append(value_text)
        return list_need

    @staticmethod
    def get_text_table_xpath(element_father, element_son):
        tr = UiObject.get_elements(element_father)
        list_need = []
        for registry in tr:
            n_opers = registry.find_elements(By.XPATH, element_son)
            for value in n_opers:
                value_text = value.text
                if value_text is None:
                    print(value)
                list_need.append(value_text)
        result = []
        for item in list_need:
            if item not in result:
                result.append(item)
        return result

    @staticmethod
    def get_text_table_list(values):
        list_need = []
        values = values.get_elements()
        for item in values:
            value = item.text
            list_need.append(value)
        return list_need

    @staticmethod
    def get_text_table_attribute(element_father, element_son):
        tr = UiObject.get_elements(element_father)
        list_need = []
        for registry in tr:
            n_opers = registry.find_elements(By.XPATH, element_son)
            for value in n_opers:
                value_text = value.get_attribute("id")
                if value_text is None:
                    print(value)
                list_need.append(value_text)
        return list_need

    @staticmethod
    def remove_specific_characters_list(elements, remove):
        return [UiObject.remove_specific_characters(element, remove) for element in elements]

    @staticmethod
    def remove_specific_characters(element, remove):
        for value in remove:
            element = str(element).replace(value, '')
        return element

    @staticmethod
    def get_text_table_id(element_father, element_son):
        tr = UiObject.get_elements(element_father)
        list_need = []

        for registry in tr:
            n_opers = registry.find_elements(By.ID, element_son)
            for value in n_opers:
                value_text = value.text
                if value_text is None:
                    print(value)
                list_need.append(value_text)
        return list_need

    @staticmethod
    def go_to_business(element, more_options_element, js_query):
        focus = UiObject.wait_to_appear(element, wait=15)
        if focus.visible(wait=15):
            UiObject.clickable(focus)
            focus.clicking()
        else:
            UiObject.wait_to_be_clickable(more_options_element).clicking()
            time.sleep(1)
            UiObject.js_element(js_query)

    @staticmethod
    def numbers():
        import datetime
        import time
        a = int(random.randint(100, 99999999))
        b = random.choice(string.ascii_letters)
        current_day = datetime.datetime.now()
        mill_seg = int(time.time() * 1000)
        c = current_day.strftime("%M%S") + f"{mill_seg}"
        return "AUTO" + f"{a}" + b + f"{c}"

    @staticmethod
    def screen(test_name):
        test_name = UiObject.remove_specific_characters(test_name, ["<", ">"])
        random_name = UiObject.numbers()
        name_image_with_error = random_name + "_" + f"{test_name}" + "_screenshot.png"
        (Browser.get_driver()).save_screenshot(ROOT_DIR + "/screenshot/" + name_image_with_error)
        if os.path.exists(ROOT_DIR + "/screenshot/" + name_image_with_error):
            logger.info("This image has the error detail for the next test: ", name_image_with_error)

    @staticmethod
    def read_csv(path):
        results = []
        with open(path) as file:
            csv_file = csv.DictReader(file)
            for lines in csv_file:
                results.append(lines)
            return results

    @staticmethod
    def read_structure(data):
        return data.columns

    @staticmethod
    def read_xlsx(name_file="reporte_de_liquidaciones_nuevo_0.xlsx"):
        xlsx = openpyxl.load_workbook(f'download/{name_file}')
        sheet = xlsx.active
        return sheet

    @staticmethod
    def select_item(value, values):
        value = str(value).lower()
        find = True
        values = values.get_elements()
        for item in values:
            item_aux = str(item.text).lower()
            if value == item_aux:
                try:
                    item.click()
                except:
                    item.click()
                find = False
                break
        if find:
            raise AssertionError("Value {} does not exit".format(value))

    @staticmethod
    def validate_item(value, values):
        values = values.get_elements()
        for item in values:
            if value == item.text:
                pass
            else:
                raise AssertionError("the value {} is not equal to {}".format(item.text, value))

    @staticmethod
    def compare_list_array(first_list, second_list):
        return Counter(first_list) == Counter(second_list)

    @staticmethod
    def read_csv_dynamic(name_file, number_row, type):
        df = pandas.read_csv(f"download/{name_file}.csv")
        cont_fila = []
        index_column = 0
        while index_column < len(df.columns):
            cont_fila.append(df.iloc[number_row][index_column])
            index_column += 1

        if type == 'NAME_COLUMN':
            colum_name = []
            for value in df:
                colum_name.append(value)
            return colum_name
        return cont_fila

    @staticmethod
    def select_first_item(values):
        values = values.get_elements()
        value = ""
        for item in values:
            value = item.text
            break
        if value == "":
            raise Exception("Value does not exit")

        return value

    @staticmethod
    def get_text_element_list_map(list_element):
        dicts = {}
        UiObject.wait_to_appear(list_element)
        invoiceElements = UiObject.get_elements(list_element)
        for index, invoice in enumerate(invoiceElements):
            dicts[index] = invoice.text
        return dicts

    @staticmethod
    def get_text_element(element):
        return UiObject.wait_to_appear(element).get_text()

    @staticmethod
    def get_text_elements(list_element):
        list_text_element = []
        invoiceElements = UiObject.get_elements(list_element)
        for index, invoice in enumerate(invoiceElements):
            list_text_element.append(invoice.text)
        return list_text_element

    @staticmethod
    def count_holidays_between_two_date(star_date, end_date):
        holiday = 0
        if star_date < end_date:
            for n in range((end_date - star_date).days):
                date_cal = star_date + timedelta(n + 1)
                if (date_cal.weekday() == 5) or (date_cal.weekday() == 6):
                    holiday += 1
        return holiday

    def delete_keys_value(self, value, wait=10):
        for n in range(value):
            self.get_element(wait).send_keys(Keys.BACKSPACE)
        return self

    @staticmethod
    def create_header_csv_file(path: str, file_name: str, name_colum):
        with open(os.path.join(path, file_name), 'a') as fp:
            fp.writelines(name_colum + '\n')
        fp.close()

    @staticmethod
    def create_csv_file_content(path: str, file_name: str, list_content):
        with open(os.path.join(path, file_name), 'a') as fp:
            for item in list_content:
                fp.writelines(item + '\n')
        fp.close()

    @staticmethod
    def switch_frame_xpath_frame(xpath_frame):
        try:
            driver = Browser.get_driver()
            driver.switch_to.frame(driver.find_element(By.XPATH, xpath_frame))
        except:
            raise Exception("page without elements")

    @staticmethod
    def default_content_xpath_frame():
        driver = Browser.get_driver()
        driver.switch_to.default_content()
