import logging
import os


def get_logger(name):
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "***** %(asctime)s : %(levelname)s : [%(filename)s:%(lineno)s - %(funcName)s()] : %(message)s *****",
        "%m/%d/%Y %I:%M:%S %p")
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(fmt)
    log.addHandler(stdout_handler)
    os.environ['WDM_LOG'] = str(logging.NOTSET)
    return log


logger = get_logger("TEST_AUTOMATION_FRONT")