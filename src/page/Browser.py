import json
import os
import time

from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.edge.service import Service as EdgeService

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options

from selenium.webdriver.firefox.service import Service as FirefoxService, Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options

from src.page.utils.Constants import Transversal

ROOT_DIR = os.path.dirname(os.path.abspath("qa-automation-front"))
ROOT_DIR_DOWNLOAD = os.path.abspath(ROOT_DIR + "/download/")


class Browser:

    def __init__(self):
        pass



    @staticmethod
    def __chrome(**kwargs):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-features=NetworkService")
        options.add_argument("--add-gpu-appcontainer-cap")
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--start-fullscreen")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--enable-automation")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        # options.add_argument("--headless=new")
        options.add_argument('--lang=es')
        options.add_argument("--log-level=DEBUG")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--incognito")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--disable-extensions-file-access-check")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--test-type")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--kiosk-printing")
        options.add_argument("--log-level=3")
        options.add_argument("disable-features=NetworkService")
        options.add_argument("enable-features=NetworkServiceInProcess")
        options.add_argument("--disable-browser-side-navigation")
        print_settings = {
            "recentDestinations": [{
                "id": "Save as PDF",
                "origin": "local",
                "account": "",
            }],
            "selectedDestinationId": "Save as PDF",
            "version": 2,
            "isHeaderFooterEnabled": False,
            "isLandscapeEnabled": True
        }

        options.add_experimental_option("prefs", {
            "printing.print_preview_sticky_settings.appState": json.dumps(print_settings),
            "download.prompt_for_download": False,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "download.default_directory": ROOT_DIR_DOWNLOAD,
            "savefile.default_directory": ROOT_DIR_DOWNLOAD,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
            driver.delete_all_cookies()
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})

        except Exception:
            time.sleep(3)
            driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
            driver.delete_all_cookies()
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})

        return driver

    @staticmethod
    def __edge(**kwargs):
        options = Options()
        options.add_argument("headless")
        options.add_argument("disable-gpu")
        options.add_argument("start-fullscreen")
        driver = webdriver.Edge(options=options, service=EdgeService(EdgeChromiumDriverManager().install()))
        driver.set_page_load_timeout(kwargs.get("page_load_timeout", 60))

        return driver

    @staticmethod
    def __ff(**kwargs):
        ff_options = Options()
        ff_options.add_argument("--headless")
        ff_options.add_argument("--enable-automation")
        driver = webdriver.Firefox(options=ff_options, service=FirefoxService(GeckoDriverManager().install()))
        driver.fullscreen_window()
        driver.delete_all_cookies()
        driver.set_page_load_timeout(kwargs.get("page_load_timeout", 60))
        return driver

    @staticmethod
    def get_driver(**kwargs):
        return Yolo.get_target(target=getattr(Browser, kwargs.get("target", f"_Browser__chrome")),
                               freak_mode=kwargs.get("freak_mode", False),
                               **kwargs)

    @staticmethod
    def shutdown(**kwargs):
        Browser.get_driver().quit()
        Yolo.remove_target(target=getattr(Browser, kwargs.get("target", f"_Browser__chrome")))

    @staticmethod
    def back():
        Browser.get_driver().back()

    @staticmethod
    def forward():
        Browser.get_driver().forward()
    # All functions that control the browser such as open/close tabs, navigate to a page etc should go into this class


class Yolo:
    __MAP = {}

    @staticmethod
    def __get_caller():
        import threading
        return threading.current_thread()

    @staticmethod
    def get_target(target, **kwargs):
        """
        When you call Yolo.get_target() initially, the object created from the target argument gets mapped to the
        thread and then returned, any subsequent calls to Yolo
        to get the same object from the same thread will return the exact same instance of the object. However, if the
        call is made from a different thread, the object will be created again for that specific thread.
        Yolo was created to solve a primary use case for creating page Objects so that you never have to manage and
        pass the driver instance from page Object to page Object. It means that you can just ask for a driver from
        any of the page Object and be sure that a valid instance of the driver will be returned to you even when
        you are creating many instances of the same page in any of your tests and running them in parallel.
        :param target: Runnable FUNCTION/METHOD. Must returns an instance of an object when executed.
        :param kwargs: Any KWARGS that you want to pass in to your :param target: or any other properties
                       you want to support
        :return: Object created by the :param target:()
        """
        caller_thread = Yolo.__get_caller()
        if caller_thread not in Yolo.__MAP:
            Yolo.__MAP.update({caller_thread: {target: target(**kwargs)}})
        elif target not in Yolo.__MAP[caller_thread]:
            Yolo.__MAP[caller_thread].update({target: target(**kwargs)})
        return Yolo.__MAP[caller_thread][target]

    @staticmethod
    def remove_target(target):
        """
        Remove any previously mapped target
        :param target: Runnable FUNCTION/METHOD. Must returns an instance of an object when executed.
        :return: BOOLEAN, True/False depending on if the target was removed
        """
        caller_thread = Yolo.__get_caller()
        if caller_thread in Yolo.__MAP and target in Yolo.__MAP[caller_thread]:
            Yolo.__MAP[caller_thread].pop(target)
            return True
        return False
