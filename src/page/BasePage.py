import inspect
import sys
from selenium.common import WebDriverException, TimeoutException
from src.page.UiObject import *
from src.page.utils.Constants import Transversal

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


class BasePage:
    def __init__(self, domain, directory, title, element):

        self.__element = element

        self.__title = title
        self.__directory = directory
        self.__domain = domain

        self.__expected_url = "{domain}{directory}".format(domain=domain,
                                                           directory=directory)

    @property
    def expected_directory(self):
        return self.__directory

    @property
    def expected_domain(self):
        return self.__domain

    @property
    def expected_title(self):
        return self.__title

    @property
    def expected_element(self):
        return self.__element

    @property
    def expected_url(self):
        return self.__expected_url

    @staticmethod
    def get_actual_element(self, element):
        return UiObject.get_element(element)

    @staticmethod
    def get_actual_title():
        return Browser.get_driver().title

    @staticmethod
    def get_actual_url():
        driver = Browser.get_driver()
        try:
            return driver.current_url
        except WebDriverException:
            driver.implicitly_wait(2)
            return driver.current_url

    def open(self, country="CL", **kwargs):
        """
        This method will open the page which inherited BasePage
        :return: self (page Object which inherited BasePage will be returned)
        """

        expected_url = {
            Transversal.CL_COUNTRY: self.expected_url
        }

        driver = Browser.get_driver()
        driver.set_page_load_timeout(kwargs.get("page_load_timeout", 30))

        if country in expected_url:
            driver.get(expected_url[country])
            try:
                notification = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(text(),'Permitir')]"))
                )
                notification.click()
            except TimeoutException:
                pass

    def open_billing(self, expected_url, **kwargs):
        """
        This method will open the page which inherited BasePage
        :return: self (page Object which inherited BasePage will be returned)
        """

        Browser.get_driver().get(expected_url)

        return self

    def refresh(self):
        """
        This method will open the page which inherited BasePage
        :return: self (page Object which inherited BasePage will be returned)
        """
        Browser.get_driver().refresh()
        return self

    @staticmethod
    def change_url(url):
        Browser.get_driver().get(url)
