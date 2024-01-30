import unittest

from test_junkie.decorators import Suite, beforeTest, afterTest, test

from src.page.alli_express_view.SearchProductView import SearchProductView
from src.page.get_started.GetStartedPage import GetStartedPage
from src.test.suites.transversal import Transversal
from src.page.utils.LogCustom import logger


@Suite(feature="As a Customer, we want to see if the second item from the second results page when searching for "
               "'instax mini' on www.aliexpress.com has at least 1 item to be bought.", owner="Ricardo Valbuena",
       parameters=[GetStartedPage])
class AlliExpressSuite(unittest.TestCase):
    logger.info("@CLASS - AlliExpressSuite")

    @beforeTest()
    def before_test(self, suite_parameter):
        suite_parameter().open()

    @afterTest()
    def after_test(self):
        Transversal.logout()

    @test(skip=False, component="validated if the second element of the second view is greater that one",
          parallelized_parameters=True, retry=2)
    def validated_if_the_second_element_of_the_second_view_is_greater_that_one(self, suite_parameter, parameter):
        logger.info("@TEST - validated_if_the_second_element_of_the_second_view_is_greater_that_one")
        SearchProductView.search_bar_input("instax mini")
        SearchProductView.click_on_search_button()
        SearchProductView.scroll_to_paginator()
        SearchProductView.click_on_second_page()
        SearchProductView.click_on_order_list_button()
        SearchProductView.get_second_element()
        SearchProductView.new_windows()  # This change the focus on the new window Tab
        product_total = SearchProductView.get_total_product_to_see()
        self.assertGreater(int(product_total), 0)
