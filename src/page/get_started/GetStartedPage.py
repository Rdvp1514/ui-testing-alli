from src.page.BasePage import BasePage, Browser
from src.page.utils.Constants import Links


class GetStartedPage(BasePage):
    def __init__(self):
        BasePage.__init__(self,

                          domain=Links.DOMAIN_CL,
                          title="",
                          directory="",
                          element="")

    @staticmethod
    def get_actual_title():
        return Browser.get_driver().title
