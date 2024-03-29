import copy
import inspect
import threading
import time
import traceback
import sys
from datetime import datetime

from test_junkie.constants import SuiteCategory, TestCategory, Event, DocumentationLinks
from test_junkie.debugger import LogJunkie, suppressed_stdout
from test_junkie.decorators import DecoratorType, synchronized
from test_junkie.errors import ConfigError, TestJunkieExecutionError, TestListenerError, BadParameters
from test_junkie.listener import Listener
from test_junkie.metrics import Aggregator, ResourceMonitor
from test_junkie.objects import Limiter
from test_junkie.parallels import ParallelProcessor
from test_junkie.builder import Builder
from test_junkie.reporter.html_reporter import Reporter
from test_junkie.reporter.xml_reporter import XmlReporter
from test_junkie.settings import Settings
from test_junkie.compatability_utils import CompatibilityUtils as CU
from src.page.UiObject import UiObject
from src.page.custon_fail.CustonParallel import CustomParallelProcessor


class RunnerCustom:

    __STATS = {}

    def __init__(self, suites, **kwargs):

        if not suites or not isinstance(suites, list):
            raise BadParameters("Runner needs to be initiated with a mandatory argument \"suites\" which must be of "
                                "type {} and it can not be empty. Instead got: {}. Please see documentation: {}"
                                .format(list, suites, DocumentationLinks.RUNNER_OBJECT))

        self.__stats = {}

        self.__suites = self.__prioritize(suites=suites)
        for suite in self.__suites:
            suite_object = Builder.get_execution_roster().get(suite, None)
            suite_object.update_test_objects(self.__prioritize(suite_object=suite_object))
            RunnerCustom.__process_owners(suite_object)

        self.__kwargs = kwargs
        self.__settings = None
        self.__processor = None

        self.__cancel = False

        self.__executed_suites = []
        self.__active_suites = []

        self.__group_rules = Builder.build_group_definitions(self.__suites)

        self.__before_group_failure_records = {}

    @staticmethod
    def __process_owners(suite_object):

        tests = suite_object.get_test_objects()
        for test in tests:
            if test.get_owner() is None:
                test.get_kwargs().update({"owner": suite_object.get_owner()})

    @staticmethod
    def __prioritize(suites=None, suite_object=None):
        """
        This function will order the lists of suites and tests according to the priority set by user
        - Suites/Tests with priorities, will be pushed towards the front according to the priorities defined
        - Suites/Tests with no priority defined, will be pushed towards the middle
        - Suites/Tests with no priority defined and not parallelized, will be pushed towards the end
        :param suites: LIST of class objects decorated with @Suite
        :param suite_object: SuiteObject
        :return: LIST ordered list of suites or tests
        """
        ordered = []
        priorities = {}
        no_priority = []
        not_parallelized = []

        items = suites if suites is not None else suite_object.get_test_objects()

        for item in items:

            if suites is not None:
                suite_object = Builder.get_execution_roster().get(item, None)
                if suite_object is None:
                    raise BadParameters("Check Runner instance, you initialized it with incorrect test suite object: "
                                        "{}.".format(item))
                priority = suite_object.get_priority()
                is_parallelized = suite_object.is_parallelized()
            else:
                priority = item.get_priority()
                is_parallelized = item.is_parallelized()
            if priority is None:
                if is_parallelized:
                    no_priority.append(item)
                else:
                    not_parallelized.append(item)
            else:
                if priority not in priorities:
                    priorities.update({priority: [item]})
                else:
                    priorities[priority].append(item)

        ordered_priorities = list(priorities.keys())
        ordered_priorities.sort()
        for priority in ordered_priorities:
            for item in priorities[priority]:
                ordered.append(item)

        ordered += no_priority + not_parallelized
        return ordered

    def get_executed_suites(self):
        """
        :return: LIST of SuiteObjects that begun executing
        """
        return self.__executed_suites

    def cancel(self):
        """
        Flips the switch to cancel the execution of tests
        :return: None
        """
        self.__cancel = True

    def run(self, **kwargs):
        """
        Initiates the execution process that runs tests
        :return: None
        """
        self.__settings = Settings(runner_kwargs=self.__kwargs, run_kwargs=kwargs)
        initial_start_time = time.time()
        resource_monitor = None
        try:
            if self.__settings.monitor_resources:
                resource_monitor = ResourceMonitor()
                resource_monitor.start()
            self.__processor = CustomParallelProcessor(self.__settings)

            with suppressed_stdout(self.__settings.quiet):
                while self.__suites:
                    for suite in list(self.__suites):
                        suite_object = Builder.get_execution_roster().get(suite, None)
                        if suite_object is not None:
                            if self.__processor.suite_multithreading() and suite_object.is_parallelized():
                                while True:
                                    if self.__processor.suite_qualifies(suite_object):
                                        time.sleep(Limiter.get_suite_throttling())
                                        self.__executed_suites.append(suite_object)
                                        CustomParallelProcessor.run_suite_in_a_thread(self.__run_suite, suite_object)
                                        time.sleep(3)
                                        self.__suites.remove(suite)
                                        break
                                    elif suite_object.get_priority() is None:
                                        break
                                    else:
                                        time.sleep(1)
                            else:
                                if not suite_object.is_parallelized():
                                    LogJunkie.debug("Cant run suite: {} in parallel with any other suites. Waiting for "
                                                    "parallel suites to finish so I can run it by itself."
                                                    .format(suite_object.get_class_object()))
                                    CustomParallelProcessor.wait_currently_active_suites_to_finish()
                                self.__executed_suites.append(suite_object)
                                self.__run_suite(suite_object)
                                self.__suites.remove(suite)
                        else:
                            LogJunkie.warn("Suite: {} not found! Make sure that your input is correct. "
                                           "If it is, make sure the use of Test Junkie's decorators "
                                           "is correct.".format(suite))
                            self.__suites.remove(suite)
                    LogJunkie.debug("{} Suite(s) left in queue.".format(len(self.__suites)))
                    time.sleep(0.2)

                CustomParallelProcessor.wait_currently_active_suites_to_finish()
        finally:
            if self.__settings.monitor_resources:
                resource_monitor.shutdown()

        runtime = time.time() - initial_start_time
        print("========== Test Junkie finished in {:0.2f} seconds ==========".format(runtime))
        aggregator = Aggregator(self.get_executed_suites())
        Aggregator.present_console_output(aggregator)
        if self.__settings.html_report:
            reporter = Reporter(monitoring_file=resource_monitor.get_file_path()
                                if resource_monitor is not None else None,
                                runtime=runtime,
                                aggregator=aggregator,
                                multi_threading_enabled=self.__processor.test_multithreading()
                                or self.__processor.suite_multithreading())
            reporter.generate_html_report(self.__settings.html_report)
        XmlReporter.create_xml_report(write_file=self.__settings.xml_report, suites=self.get_executed_suites())
        if self.__settings.monitor_resources:
            resource_monitor.cleanup()
        return aggregator

    @staticmethod
    def __validate_suite_parameters(suite):
        parameters = suite.get_parameters(process_functions=True)
        if not parameters or not isinstance(parameters, list):
            if isinstance(parameters, list):
                return BadParameters("Argument: \"parameters\" in @Suite() decorator returned empty: <class 'list'>. "
                                     "For more info, see this explanation: {}"
                                     .format(DocumentationLinks.ON_CLASS_IGNORE))
            else:
                return BadParameters("Argument: \"parameters\" in @Suite() decorator must be of type: <class 'list'> "
                                     "but found: {}. For more info, see @Suite() decorator documentation: {}"
                                     .format(type(parameters), DocumentationLinks.SUITE_DECORATOR))
        return False

    @staticmethod
    def __validate_test_parameters(test):
        parameters = test.get_parameters(process_functions=True)
        if not parameters or not isinstance(parameters, list):
            exception = None
            try:
                if isinstance(parameters, list):
                    exception = BadParameters("Argument: \"parameters\" in @test() decorator returned empty: "
                                              "<class 'list'>. For more info, see: {}"
                                              .format(DocumentationLinks.ON_TEST_IGNORE))
                else:
                    exception = BadParameters("Argument: \"parameters\" in @test() decorator must be of type: "
                                              "<class 'list'> but found: {}. For more info, see @test() decorator "
                                              "documentation: {}"
                                              .format(type(parameters), DocumentationLinks.TEST_DECORATOR))
                raise exception
            except:
                return {"exception": exception, "trace": traceback.format_exc()}

    def __run_suite(self, suite):

        def before_group_rule_failed():
            for group, _result in self.__before_group_failure_records.items():
                if suite.get_class_object() in _result["definition"]["suites"]:
                    return _result["trace"]

        suite_start_time = time.time()
        unsuccessful_tests = None
        exception = RunnerCustom.__validate_suite_parameters(suite)

        if not exception:
            exception = before_group_rule_failed()
            if not exception:
                result = self.__group_rules.run_before_group(suite, DecoratorType.BEFORE_GROUP)
                if result is not None:
                    self.__before_group_failure_records.update(result)
                    exception = result[list(result.keys())[0]]["trace"]

        if not suite.can_skip(self.__settings) and not self.__cancel and not exception:
            RunnerCustom.__process_event(event=Event.ON_CLASS_IN_PROGRESS, suite=suite)
            for suite_retry_attempt in range(1, suite.get_retry_limit() + 1):
                if suite_retry_attempt == 1 or suite.get_status() in SuiteCategory.ALL_UN_SUCCESSFUL:

                    for class_param in suite.get_parameters(process_functions=True):
                        LogJunkie.debug("Running suite: {}".format(suite.get_class_object()))
                        LogJunkie.debug("Suite Retry {}/{} with Param: {}"
                                        .format(suite_retry_attempt, suite.get_retry_limit(), class_param))

                        before_class_error = RunnerCustom.__run_before_class(suite, class_param)

                        if suite_retry_attempt > 1:
                            unsuccessful_tests = suite.get_unsuccessful_tests()
                            LogJunkie.debug("There are {} unsuccessful tests that need to be retried"
                                            .format(len(unsuccessful_tests)))
                            if not unsuccessful_tests:
                                break
                            tests = unsuccessful_tests
                        else:
                            tests = list(suite.get_test_objects())

                        while tests:
                            for test in list(tests):

                                test_start_time = time.time()  # will use in case of a failure in context of this loop

                                if not self.__positive_skip_condition(test=test) and \
                                        RunnerCustom.__runnable_tags(test=test, tag_config=self.__settings.tags):

                                    if not test.is_parallelized():
                                        LogJunkie.debug("Cant run test: {} in parallel with any other tests"
                                                        .format(test.get_function_object()))
                                        CustomParallelProcessor.wait_currently_active_tests_to_finish()

                                    bad_params = RunnerCustom.__validate_test_parameters(test)
                                    if bad_params is not None:
                                        tests.remove(test)
                                        test.metrics.update_metrics(status=TestCategory.IGNORE,
                                                                    start_time=test_start_time,
                                                                    exception=bad_params["exception"],
                                                                    formatted_traceback=bad_params["trace"])
                                        RunnerCustom.__process_event(event=Event.ON_IGNORE, suite=suite, test=test,
                                                                     class_param=class_param, error=bad_params)
                                        continue

                                    while not self.__processor.test_qualifies(test):
                                        time.sleep(0.2)
                                        if test.get_priority() is None:
                                            continue

                                    for param in test.get_parameters(process_functions=True):
                                        if unsuccessful_tests is not None and \
                                                not test.is_qualified_for_retry(param, class_param=class_param):
                                            # If does not qualify with current parameter, will move to the next
                                            continue
                                        if ((self.__processor.test_multithreading()
                                             and param is None) or (self.__processor.test_multithreading()
                                                                    and test.parallelized_parameters()
                                                                    and param is not None)):

                                                while self.__processor.test_limit_reached():
                                                    time.sleep(0.2)
                                                time.sleep(Limiter.get_test_throttling())
                                                self.__processor.run_test_in_a_thread(RunnerCustom.__run_test,
                                                                                      suite, test, param,
                                                                                      class_param,
                                                                                      before_class_error,
                                                                                      self.__cancel)
                                        else:
                                            RunnerCustom.__run_test(suite=suite, test=test,
                                                                    parameter=param,
                                                                    class_parameter=class_param,
                                                                    before_class_error=before_class_error,
                                                                    cancel=self.__cancel)
                                    tests.remove(test)

                                else:
                                    tests.remove(test)
                                    test.metrics.update_metrics(status=TestCategory.SKIP, start_time=test_start_time)
                                    RunnerCustom.__process_event(event=Event.ON_SKIP, suite=suite, test=test,
                                                                 class_param=class_param)
                        CustomParallelProcessor.wait_currently_active_tests_to_finish()
                        RunnerCustom.__run_after_class(suite, class_param)
                    suite.metrics.update_suite_metrics(status=SuiteCategory.FAIL
                                                       if suite.has_unsuccessful_tests() else SuiteCategory.SUCCESS,
                                                       start_time=suite_start_time)
            RunnerCustom.__process_event(event=Event.ON_CLASS_COMPLETE, suite=suite)
            after_group_failed = self.__group_rules.run_after_group(suite)
            if after_group_failed:
                event = Event.ON_AFTER_GROUP_FAIL if isinstance(after_group_failed["exception"],
                                                                AssertionError) else Event.ON_AFTER_GROUP_ERROR
                RunnerCustom.__process_event(event=event, suite=suite, error=after_group_failed["exception"],
                                             formatted_traceback=after_group_failed["trace"])
        elif self.__cancel:
            suite.metrics.update_suite_metrics(status=SuiteCategory.CANCEL, start_time=suite_start_time)
            RunnerCustom.__process_event(event=Event.ON_CLASS_CANCEL, suite=suite)
        elif exception or before_group_rule_failed():
            suite.metrics.update_suite_metrics(status=SuiteCategory.IGNORE, start_time=suite_start_time,
                                               initiation_error=exception)
            RunnerCustom.__process_event(event=Event.ON_CLASS_IGNORE, suite=suite)
        else:
            suite.metrics.update_suite_metrics(status=SuiteCategory.SKIP, start_time=suite_start_time)
            RunnerCustom.__process_event(event=Event.ON_CLASS_SKIP, suite=suite)

    @staticmethod
    def __run_test(suite, test, parameter=None, class_parameter=None, before_class_error=None, cancel=False):

        def run_before_test():
            try:
                if not test.skip_before_test_rule():
                    suite.get_rules().before_test(test=copy.deepcopy(test))
                if not test.skip_before_test():
                    before_test_error = RunnerCustom.__process_decorator(decorator_type=DecoratorType.BEFORE_TEST,
                                                                         suite=suite, class_parameter=class_parameter,
                                                                         test=test, parameter=parameter)
                    if before_test_error is not None:  # updating **test** metrics (no decorator passed in)
                        process_failure(before_test_error, pre_processed=True)
                        return False
                return True
            except Exception as before_test_error:
                process_failure(before_test_error, decorator=DecoratorType.BEFORE_TEST)
                process_failure(before_test_error)  # updating **test** metrics (no decorator passed in)
                return False

        def process_failure(error, pre_processed=False, decorator=None):
            _runtime = time.time() - start_time  # start time defined in the outside scope before each decorated func
            if not isinstance(error, TestJunkieExecutionError):
                if pre_processed:
                    trace = error.message if sys.version_info[0] < 3 else str(error)
                else:
                    trace = traceback.format_exc()
                __category, __event = TestCategory.ERROR, Event.ON_ERROR
                if isinstance(error, AssertionError):
                    __category, __event = TestCategory.FAIL, Event.ON_FAILURE
                test.metrics.update_metrics(status=__category,
                                            start_time=test_start_time,
                                            param=parameter,
                                            class_param=class_parameter,
                                            exception=error,
                                            formatted_traceback=trace,
                                            runtime=_runtime,
                                            decorator=decorator)
                if decorator is None:
                    RunnerCustom.__process_event(event=__event, suite=suite, test=test, error=error,
                                                 class_param=class_parameter, param=parameter, formatted_traceback=trace)
                else:
                    suite.metrics.update_decorator_metrics(decorator, start_time, error, trace)
            else:
                raise error

        def run_after_test(_record_test_failure=True):
            try:
                # Running after test functions
                if not test.skip_after_test():
                    after_test_error = RunnerCustom.__process_decorator(decorator_type=DecoratorType.AFTER_TEST,
                                                                        suite=suite, class_parameter=class_parameter,
                                                                        test=test, parameter=parameter)
                    if after_test_error is not None:  # updating **test** metrics (no decorator passed in)
                        process_failure(after_test_error, pre_processed=True)
                        return False
                if not test.skip_after_test_rule():
                    suite.get_rules().after_test(test=copy.deepcopy(test))
                return True
            except Exception as after_test_error:
                if _record_test_failure:
                    process_failure(after_test_error, decorator=DecoratorType.AFTER_TEST)
                    process_failure(after_test_error)  # updating **test** metrics (no decorator passed in)
                return False

        if not test.accepts_suite_parameters():
            # for reporting purposes, so reports are properly nested
            class_parameter = None

        test_start_time = time.time()
        if before_class_error is not None or cancel:
            if not test.accepts_suite_parameters():
                if None in test.suite.metrics.get_metrics()[DecoratorType.BEFORE_CLASS]["exceptions"] \
                        and test.get_status(parameter, class_parameter) is not None:
                    return  # fixes ticket: #19
                elif test.get_number_of_actual_retries(parameter, class_parameter) >= test.suite.get_retry_limit():
                    return  # fixes ticket: #27
            _status = TestCategory.IGNORE if not cancel else TestCategory.CANCEL
            _event = Event.ON_IGNORE if not cancel else Event.ON_CANCEL
            test.metrics.update_metrics(status=_status,
                                        start_time=test_start_time,
                                        param=parameter,
                                        class_param=class_parameter,
                                        exception=before_class_error["exception"],
                                        formatted_traceback=before_class_error["traceback"])
            RunnerCustom.__process_event(event=_event, error=before_class_error["exception"], suite=suite, test=test,
                                         class_param=class_parameter, param=parameter,
                                         formatted_traceback=before_class_error["traceback"])
            return

        status = test.get_status(parameter, class_parameter)
        if not test.accepts_suite_parameters() and status is not None:
            """
            making sure that we do not run tests with suite parameters if suite parameters are not accepted in the
            test signature. But we still want to run all other parameters and tests without any params.
            Also we want to make sure we honor the suite level retries
            """
            if status != TestCategory.SUCCESS:  # test already ran and was unsuccessful
                # if it did not reach its max retry limit, will rerun it again
                max_retry_allowed = suite.get_retry_limit() * test.get_retry_limit()
                actual_retries = test.get_number_of_actual_retries(parameter, class_parameter)
                if actual_retries >= max_retry_allowed:
                    return
            else:
                return

        RunnerCustom.__process_event(event=Event.ON_IN_PROGRESS, suite=suite, test=test,
                                     class_param=class_parameter, param=parameter)
        try:
            for retry_attempt in range(1, test.get_retry_limit() + 1):
                if test.is_qualified_for_retry(parameter, class_param=class_parameter):
                    LogJunkie.debug("\n===============Running test==================\n"
                                    "Test Case: {}\n"
                                    "Test Suite: {}\n"
                                    "Test Parameter: {}\n"
                                    "Class Parameter: {}\n"
                                    "Retry Attempt: {}/{}\n"
                                    "============================================="
                                    .format(test.get_function_name(), suite.get_class_name(), parameter,
                                            class_parameter, retry_attempt, test.get_retry_limit()))
                    record_test_failure = True
                    try:
                        start_time = time.time()  # before test start time
                        if run_before_test() is False:  # if before test failed, moving on without running the test
                            continue  # everything recorded at this point in the metrics and flow is solid
                        # Running actual test
                        start_time = time.time()  # test start time
                        time.sleep(1)
                        RunnerCustom.__process_decorator(decorator_type=DecoratorType.TEST_CASE, suite=suite,
                                                         test=test, parameter=parameter, class_parameter=class_parameter)
                        runtime = time.time() - start_time
                    except Exception as test_error:
                        UiObject.screen(test)
                        runtime = time.time() - start_time
                        process_failure(test_error)
                        record_test_failure = False  # already recorded the failure just above this
                    start_time = time.time()  # after test start time
                    if run_after_test(record_test_failure) is True:  # if did not fail, test is OK
                        if record_test_failure:  # Test failed and failure was already recorded thus can't pass it
                            test.metrics.update_metrics(status=TestCategory.SUCCESS, start_time=None, param=parameter,
                                                        class_param=class_parameter, runtime=runtime)
                            RunnerCustom.__process_event(event=Event.ON_SUCCESS, suite=suite, test=test,
                                                         class_param=class_parameter, param=parameter)
                            return
        finally:
            RunnerCustom.__process_event(event=Event.ON_COMPLETE, suite=suite, test=test,
                                         class_param=class_parameter, param=parameter)

    @staticmethod
    def __run_before_class(suite, class_parameter=None):
        try:
            suite.get_rules().before_class()
            before_class_error = RunnerCustom.__process_decorator(decorator_type=DecoratorType.BEFORE_CLASS,
                                                                  suite=suite, class_parameter=class_parameter)
            if before_class_error is not None:
                raise before_class_error
            return
        except Exception as error:
            trace = traceback.format_exc()
            event = Event.ON_BEFORE_CLASS_FAIL if isinstance(error, AssertionError) else Event.ON_BEFORE_CLASS_ERROR
            RunnerCustom.__process_event(event=event, suite=suite, error=error,
                                         class_param=class_parameter, formatted_traceback=trace)
            return {"exception": error, "traceback": trace}

    @staticmethod
    def __run_after_class(suite, class_parameter=None):
        try:
            after_class_error = RunnerCustom.__process_decorator(decorator_type=DecoratorType.AFTER_CLASS,
                                                                 suite=suite, class_parameter=class_parameter)
            if after_class_error is not None:
                raise after_class_error
            suite.get_rules().after_class()
        except Exception as error:
            trace = traceback.format_exc()
            event = Event.ON_AFTER_CLASS_FAIL if isinstance(error, AssertionError) else Event.ON_AFTER_CLASS_ERROR
            RunnerCustom.__process_event(event=event, suite=suite, error=error,
                                         class_param=class_parameter, formatted_traceback=trace)
            return {"exception": error, "traceback": trace}

    @staticmethod
    # @synchronized(threading.Lock())
    def __process_decorator(decorator_type, suite, test=None, parameter=None,  class_parameter=None):

        def update_metrics(_decorator_type, error=None, _trace=None):
            suite.metrics.update_decorator_metrics(_decorator_type, start_time, error, _trace)
            if _decorator_type in [DecoratorType.BEFORE_TEST, DecoratorType.AFTER_TEST]:
                test.metrics.update_metrics(status=None, start_time=start_time, param=parameter,
                                            class_param=class_parameter, decorator=_decorator_type,
                                            formatted_traceback=_trace, exception=error)
        start_time = time.time()
        if DecoratorType.TEST_CASE != decorator_type:
            functions_list = suite.get_decorated_definition(decorator_type)
            for func in functions_list:
                try:
                    # deprecated but supports Python 2
                    if "suite_parameter" in CU.getargspec(func["decorated_function"]).args:
                        func["decorated_function"](suite.get_class_instance(), suite_parameter=class_parameter)
                    else:
                        func["decorated_function"](suite.get_class_instance())
                except Exception as decorator_error:
                    trace = traceback.format_exc()
                    update_metrics(decorator_type, decorator_error, trace)
                    if DecoratorType.BEFORE_TEST == decorator_type:  # if before test fails, after test wont run
                        if suite.get_decorated_definition(DecoratorType.AFTER_TEST):
                            update_metrics(DecoratorType.AFTER_TEST, None, "N/A")  # but we need to keep list synced
                    return AssertionError(trace) if isinstance(decorator_error, AssertionError) else Exception(trace)
            if functions_list:  # will updated only if we had decorated function(s)
                update_metrics(decorator_type)
        else:
            if test.accepts_test_and_suite_parameters():
                test.get_function_object()(suite.get_class_instance(),
                                           parameter=parameter, suite_parameter=class_parameter)
            elif test.accepts_suite_parameters():
                test.get_function_object()(suite.get_class_instance(), suite_parameter=class_parameter)
            elif test.accepts_test_parameters():
                test.get_function_object()(suite.get_class_instance(), parameter=parameter)
            else:
                test.get_function_object()(suite.get_class_instance())

    @staticmethod
    def __process_event(event, suite, test=None, param=None, class_param=None, error=None, formatted_traceback=None):

        event_mapping = {Event.ON_SUCCESS: {"custom": suite.get_listener().on_success,
                                            "native": Listener().on_success},
                         Event.ON_FAILURE: {"custom": suite.get_listener().on_failure,
                                            "native": Listener().on_failure},
                         Event.ON_ERROR: {"custom": suite.get_listener().on_error,
                                          "native": Listener().on_error},
                         Event.ON_SKIP: {"custom": suite.get_listener().on_skip,
                                         "native": Listener().on_skip},
                         Event.ON_CANCEL: {"custom": suite.get_listener().on_cancel,
                                           "native": Listener().on_cancel},
                         Event.ON_IGNORE: {"custom": suite.get_listener().on_ignore,
                                           "native": Listener().on_ignore},
                         Event.ON_IN_PROGRESS: {"custom": suite.get_listener().on_in_progress,
                                                "native": Listener().on_in_progress},
                         Event.ON_COMPLETE: {"custom": suite.get_listener().on_complete,
                                             "native": Listener().on_complete},
                         Event.ON_CLASS_CANCEL: {"custom": suite.get_listener().on_class_cancel,
                                                 "native": Listener().on_class_cancel},
                         Event.ON_CLASS_SKIP: {"custom": suite.get_listener().on_class_skip,
                                               "native": Listener().on_class_skip},
                         Event.ON_BEFORE_CLASS_ERROR: {"custom": suite.get_listener().on_before_class_error,
                                                       "native": Listener().on_before_class_error},
                         Event.ON_BEFORE_CLASS_FAIL: {"custom": suite.get_listener().on_before_class_failure,
                                                      "native": Listener().on_before_class_failure},
                         Event.ON_CLASS_IGNORE: {"custom": suite.get_listener().on_class_ignore,
                                                 "native": Listener().on_class_ignore},
                         Event.ON_AFTER_CLASS_ERROR: {"custom": suite.get_listener().on_after_class_error,
                                                      "native": Listener().on_after_class_error},
                         Event.ON_AFTER_CLASS_FAIL: {"custom": suite.get_listener().on_after_class_failure,
                                                     "native": Listener().on_after_class_failure},
                         Event.ON_CLASS_IN_PROGRESS: {"custom": suite.get_listener().on_class_in_progress,
                                                      "native": Listener().on_class_in_progress},
                         Event.ON_BEFORE_GROUP_FAIL: {"custom": suite.get_listener().on_before_group_failure,
                                                      "native": Listener().on_before_group_failure},
                         Event.ON_BEFORE_GROUP_ERROR: {"custom": suite.get_listener().on_before_group_error,
                                                       "native": Listener().on_before_group_error},
                         Event.ON_AFTER_GROUP_FAIL: {"custom": suite.get_listener().on_after_group_failure,
                                                     "native": Listener().on_after_group_failure},
                         Event.ON_AFTER_GROUP_ERROR: {"custom": suite.get_listener().on_after_group_error,
                                                      "native": Listener().on_after_group_error},
                         Event.ON_CLASS_COMPLETE: {"custom": suite.get_listener().on_class_complete,
                                                   "native": Listener().on_class_complete}
                         }

        native_function = event_mapping[event]["native"]
        custom_function = event_mapping[event]["custom"]
        custom_function = custom_function \
            if str(custom_function).split(" at ")[0] != str(native_function).split(" at ")[0] else None

        @synchronized(threading.Lock())
        def __create_properties():
            properties = {"suite_meta": suite.get_meta(copy_of_meta=True),
                          "test_meta": test.get_meta(param, class_param, copy_of_meta=True) if test else None,
                          "jm": {"jso": suite}}
            if test:
                properties["test_meta"].update({"parameter": param})
                properties["jm"].update({"jto": test})
            properties["suite_meta"].update({"parameter": class_param})
            return properties
        try:

            if error is not None:
                native_function(custom_function=custom_function,
                                properties=__create_properties(),
                                error=error,
                                trace=formatted_traceback)
            else:
                native_function(custom_function=custom_function,
                                properties=__create_properties())
        except Exception:
            trace = ""
            if sys.version_info[0] < 3:
                trace = "\n\n{}".format(traceback.format_exc())
            raise TestListenerError("Exception occurred while processing custom event listener for function: {}. "
                                    "For help on defining custom event listeners, see documentation: {}{}"
                                    .format(custom_function, DocumentationLinks.LISTENERS, trace))

    @staticmethod
    def __runnable_tags(test, tag_config):
        """
        This function evaluates if test should be executed based on its tags and the tag config
        :param test: TestObject
        :param tag_config: DICT
        :return: BOOLEAN
        """

        def __config_set(prop=None):
            """
            Checks if tag config was defined for any of the following settings:
            - skip_on_match_all
            - skip_on_match_any
            - run_on_match_all
            - run_on_match_any
            :return: BOOLEAN, if any of of the settings are set, tag config is considered set
            """
            props = ["skip_on_match_all", "skip_on_match_any", "run_on_match_all", "run_on_match_any"]
            for setting in props if not prop else [prop]:
                val = tag_config.get(setting, None) is not None
                if val is True:
                    return True
            return False

        def __full_match(prop):
            tags = tag_config.get(prop, [])
            if not tags:
                return False
            for tag in tags:
                if tag not in test_tags:
                    return False
            return True

        def __partial_match(prop):
            tags = tag_config.get(prop, [])
            if not tags:
                return False
            for tag in tags:
                if tag in test_tags:
                    return True

        test_tags = test.get_tags()
        if tag_config is not None:
            try:
                if __config_set():
                    if __full_match("skip_on_match_all") or __partial_match("skip_on_match_any"):
                        return False
                    elif __full_match("run_on_match_all") or __partial_match("run_on_match_any"):
                        return True
                    else:
                        if not __config_set("run_on_match_all") and not __config_set("run_on_match_any"):
                            return True
                        return False

            except Exception:
                trace = ""
                if sys.version_info[0] < 3:
                    trace = "\n\n{}".format(traceback.format_exc())
                raise ConfigError("Error occurred while trying to parse `tag_config`. For help on defining the config, "
                                  "see documentation: {}{}".format(DocumentationLinks.TAGS, trace))
        return True

    def __positive_skip_condition(self, test):
        """
        This function will evaluate inputs for skip parameter whether its a function or a boolean
        :param test: TestObject object
        :return: BOOLEAN
        """
        can_skip = test.can_skip()

        # Run only tests that were requested
        if can_skip is False and self.__settings.tests is not None:
            requested = False
            if sys.version_info[0] < 3:
                """
                While both in Python 2 and 3 function objects look like, tests.junkie_suites.SkipSuites
                in Python 2 the list gets stored as:
                    [<unbound method SkipTests.test_1>, <unbound method SkipTests.test_2>]
                and in Python 3 its stored as:
                    [<function SkipTests.test_1 at 0x0438A780>, <function SkipTests.test_2 at 0x0438A7C8>]
                So oddly enough in Python 2 the regular check did not work, thus this hack
                """

                for t in self.__settings.tests:
                    if not isinstance(t, str):
                        if inspect.getsource(test.get_function_object()) == inspect.getsource(t):
                            requested = True
                            break
                    else:
                        if test.get_function_name() in self.__settings.tests:
                            requested = True
                            break
            else:
                requested = test.get_function_object() in self.__settings.tests or \
                                test.get_function_name() in self.__settings.tests

            can_skip = not requested  # if test was not requested as part of the tests set, we can skip it

        # Out of those tests, run only components that were requested
        if can_skip is False and self.__settings.components is not None:
            can_skip = not test.get_component() in self.__settings.components

        # Out of those tests, run only those that belong to the owners requested
        if can_skip is False and self.__settings.owners is not None:
            can_skip = not test.get_owner() in self.__settings.owners
        return can_skip