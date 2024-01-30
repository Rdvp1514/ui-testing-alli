from selenium.webdriver.common.by import By

from src.page.UiObject import UiObject


class SearchProductView:
    SEARCH_BAR_ = UiObject(By.ID, 'search-words')
    SEARCH_BUTTON_ = UiObject(By.XPATH, '//*[@id="_full_container_header_23_"]/div[2]/div/div[1]/div/input[2]')
    SCROLL_BAR_ = UiObject(By.XPATH, "//button[contains(text(),'confirmar')]")

    @staticmethod
    def search_bar_input(value):
        UiObject.wait_to_appear(SearchProductView.SEARCH_BAR_).set_text(value)

    @staticmethod
    def click_on_search_button():
        UiObject.wait_to_be_clickable(SearchProductView.SEARCH_BUTTON_).click()

    @staticmethod
    def scroll_to_paginator():
        UiObject.move(SearchProductView.SCROLL_BAR_)