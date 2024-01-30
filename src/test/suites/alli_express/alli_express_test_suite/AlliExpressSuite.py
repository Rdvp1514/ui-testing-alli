import unittest

from test_junkie.decorators import Suite, beforeTest, afterTest

from src.page.get_started.GetStartedPage import GetStartedPage
from src.test.suites.transversal import Transversal
from src.page.utils.LogCustom import logger


@Suite(feature="As a Customer, we want to see if the second item from the second results page when searching for "
               "'instax mini' on www.aliexpress.com has at least 1 item to be bought.", owner="Ricardo Valbuena",
       parameters=[GetStartedPage])
class AlliExpressSuite(unittest.TestSuite):
    logger.info("@CLASS - AlliExpressSuite")

    @beforeTest()
    def before_test(self, suite_parameter):
        suite_parameter().open()

    @afterTest()
    def after_test(self):
        Transversal.logout()
