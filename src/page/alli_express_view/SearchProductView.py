import time

from selenium.webdriver.common.by import By

from src.page.UiObject import UiObject


class SearchProductView:
    SEARCH_BAR_ = UiObject(By.ID, 'search-words')
    SEARCH_BUTTON_ = UiObject(By.XPATH, '//*[@id="_full_container_header_23_"]/div[2]/div/div[1]/div/input[2]')
    SCROLL_BAR_ = UiObject(By.XPATH, "//button[contains(text(),'confirm')]")
    JS_SECOND_PAGE_ = 'document.getElementsByClassName("comet-pagination-item comet-pagination-item-2")[0].click();'
    ORDER_BY_LIST_BUTTON_ = UiObject(By.XPATH, "//div[@id='root']//span[contains(text(), 'List')]")

    @staticmethod
    def search_bar_input(value):
        UiObject.wait_to_appear(SearchProductView.SEARCH_BAR_).set_text(value)

    @staticmethod
    def click_on_search_button():
        UiObject.wait_to_be_clickable(SearchProductView.SEARCH_BUTTON_).click()

    @staticmethod
    def scroll_to_paginator():
        UiObject.move(SearchProductView.SCROLL_BAR_)

    @staticmethod
    def click_on_order_list_button():
        UiObject.wait_to_be_clickable(SearchProductView.ORDER_BY_LIST_BUTTON_).click()

    @staticmethod
    def click_on_second_page():
        UiObject.js_element(SearchProductView.JS_SECOND_PAGE_)
