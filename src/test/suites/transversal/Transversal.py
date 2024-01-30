from src.page.Browser import Browser


def logout():
    Browser.shutdown()


def login(suite_parameter):
    suite_parameter().open()
