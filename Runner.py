from test_junkie.reporter.html_reporter import ReportTemplate

from src.page.custon_fail.CustonFail import RunnerCustom
from src.page.html_reporter.CustomReporter import CustomReporter
from test_junkie.reporter.html_reporter import ReportTemplate

from src.page.custon_fail.CustonFail import RunnerCustom
from src.page.html_reporter.CustomReporter import CustomReporter
from src.test.suites.alli_express.alli_express_test_suite.AlliExpressSuite import AlliExpressSuite

report_template = ReportTemplate()
report_template.__class__.get_body_template = CustomReporter.get_custom_monkey_html_template

runner = RunnerCustom(
        suites=[
            AlliExpressSuite
        ],
        html_report=f"reports/chrome.html",
        monitor_resources=True
    )

runner.run(test_multithreading_limit=10,
           suite_multithreading_limit=24)