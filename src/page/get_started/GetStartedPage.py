from src.page.BasePage import BasePage, Browser
from src.page.utils.Constants import Links


class GetStartedPage(BasePage):
    def __init__(self):
        BasePage.__init__(self,
                          domainco=Links.DOMAIN_CO,
                          domain=Links.DOMAIN_CL,
                          domainbr=Links.DOMAIN_BR,
                          domaincd=Links.DOMAIN_CD,
                          title="",
                          directory="",
                          element="")

    @staticmethod
    def get_actual_title():
        return Browser.get_driver().title
