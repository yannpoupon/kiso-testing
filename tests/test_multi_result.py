##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pykiso.test_result.multi_result import MultiTestResult
from pykiso.test_result.text_result import BannerTestResult
from pykiso.test_result.xml_result import XmlTestResult


@pytest.fixture
def multi_result_instance_multiple_classes():
    return MultiTestResult(BannerTestResult, XmlTestResult)(sys.stderr, True, 1)


@pytest.fixture
def test_mock(mocker):
    return mocker.patch("pykiso.test_coordinator.test_case.BasicTest")


@pytest.mark.parametrize(
    "name_function,argument",
    [
        ("startTest", {test_mock}),
        ("startTestRun", {}),
        ("stopTestRun", {}),
        ("stop", {}),
        ("stopTest", {test_mock}),
        ("addFailure", {test_mock, Exception}),
        ("addSuccess", {test_mock}),
        ("addSkip", {test_mock, "reason"}),
        ("addUnexpectedSuccess", {test_mock}),
        ("addExpectedFailure", {test_mock, Exception}),
        ("addSubTest", {test_mock, "subtest", Exception}),
        ("addError", {test_mock, Exception}),
    ],
)
def test_call_function(mocker, multi_result_instance_multiple_classes, name_function, argument):
    mock_xmltestresult = mocker.patch.object(XmlTestResult, name_function)
    mock_bannertestresult = mocker.patch.object(BannerTestResult, name_function)
    mocker.patch("pykiso.test_result.multi_result.test_runner_instance")

    getattr(multi_result_instance_multiple_classes, name_function)(*argument)

    mock_xmltestresult.assert_called_once_with(*argument)
    mock_bannertestresult.assert_called_once_with(*argument)


def test___getattr__(multi_result_instance_multiple_classes, test_mock, mocker):
    mocker.patch("pykiso.test_result.xml_result.XmlTestResult.getDescription")
    mocker.patch("json.dumps")
    reason = "test"

    multi_result_instance_multiple_classes.addSkip(test_mock, reason)

    assert multi_result_instance_multiple_classes.skipped == [(test_mock, reason)]


@pytest.mark.parametrize("failfast", [True, False])
def test___setattr__(multi_result_instance_multiple_classes, test_mock, failfast):

    multi_result_instance_multiple_classes.failfast = failfast

    for result in multi_result_instance_multiple_classes.result_classes:
        assert result.failfast == failfast


@pytest.mark.parametrize(
    "name_function,argument",
    [
        ("getDescription", {test_mock}),
        ("printErrors", {}),
        ("printErrorList", {"reason", Exception}),
    ],
)
def test_function_with_one_call_bannertestresult(
    multi_result_instance_multiple_classes, mocker, name_function, argument
):
    mock_bannertestresult = mocker.patch.object(BannerTestResult, name_function)

    getattr(multi_result_instance_multiple_classes, name_function)(*argument)

    mock_bannertestresult.assert_called_once_with(*argument)


@pytest.mark.parametrize(
    "name_function,argument",
    [
        ("getDescription", {test_mock}),
        ("printErrors", {}),
        ("printErrorList", {"reason", Exception}),
    ],
)
def test_function_with_one_call_xmltestresult(mocker, name_function, argument):
    mock_xmltestresult = mocker.patch.object(XmlTestResult, name_function)

    getattr(MultiTestResult(XmlTestResult, XmlTestResult), name_function)(*argument)

    mock_xmltestresult.assert_called_once_with(*argument)


def test_error_occured(multi_result_instance_multiple_classes):

    error_occured = multi_result_instance_multiple_classes.error_occurred

    assert error_occured is False


def test_generate_reports(multi_result_instance_multiple_classes, mocker):
    mock_generate_reports = mocker.patch.object(XmlTestResult, "generate_reports")

    multi_result_instance_multiple_classes.generate_reports("test_runner")

    mock_generate_reports.assert_called_once_with("test_runner")


@pytest.fixture
def dummy_test():
    # Dummy test object with required attributes
    class DummyTest:
        __class__ = type("DummyTestClass", (), {})
        _testMethodName = "test_method"

    return DummyTest()


@pytest.fixture
def dummy_log_options(tmp_path):
    class DummyLogOptions:
        log_path = tmp_path / "dummy.log"
        log_level = "DEBUG"

    return DummyLogOptions()


@pytest.fixture
def dummy_multifile_writer():
    class DummyMultiFileWriter:
        def __init__(self):
            self.files = []

        def add_file(self, path):
            self.files.append(path)

        def remove_file(self, path):
            if path in self.files:
                self.files.remove(path)

    return DummyMultiFileWriter()


@pytest.fixture
def dummy_stream(dummy_multifile_writer):
    class DummyStream:
        multifile_handler = dummy_multifile_writer

    class DummyStreamWrapper:
        stream = DummyStream()

    return DummyStreamWrapper()


@pytest.fixture
def patch_test_runner_instance(dummy_stream):
    import pykiso.test_result.multi_result as multi_result_mod

    class DummyRunner:
        stream = dummy_stream

    multi_result_mod.test_runner_instance = DummyRunner()
    yield
    multi_result_mod.test_runner_instance = None


@pytest.fixture
def patch_logging_options(monkeypatch, dummy_log_options):
    import pykiso.test_result.multi_result as multi_result_mod

    monkeypatch.setattr(multi_result_mod, "get_logging_options", lambda: dummy_log_options)
    monkeypatch.setattr(multi_result_mod, "get_internal_level", lambda level: logging.DEBUG)


@pytest.mark.usefixtures("patch_test_runner_instance", "patch_logging_options")
def test_handle_log_file_strategy_testRun(dummy_test, patch_test_runner_instance, patch_logging_options):
    mtr = MultiTestResult(object, log_file_strategy="testRun")

    mtr.handle_log_file_strategy(dummy_test)

    assert mtr.current_log_file is not None
    assert mtr.current_log_file.name.endswith(".log")


@pytest.mark.usefixtures("patch_test_runner_instance", "patch_logging_options")
def test_handle_log_file_strategy_testCase_reuses_logfile(
    tmp_path, dummy_test, patch_test_runner_instance, patch_logging_options
):
    mtr = MultiTestResult(object, log_file_strategy="testCase")
    mtr._list_test_results = [dummy_test.__class__]
    mtr.current_log_file = tmp_path / "existing.log"

    mtr.handle_log_file_strategy(dummy_test)

    # Should not change current_log_file if already present for testCase
    assert mtr.current_log_file == tmp_path / "existing.log"


def test_handle_log_file_strategy_none_strategy(dummy_test, patch_test_runner_instance, patch_logging_options):
    mtr = MultiTestResult(object, log_file_strategy=None)

    # Should not raise or do anything
    mtr.handle_log_file_strategy(dummy_test)
    assert mtr.current_log_file is None


def test_stopTest_with_log_file_strategy(dummy_test, mocker, patch_test_runner_instance):
    mocker.patch.object(BannerTestResult, "stopTest")
    mtr = MultiTestResult(BannerTestResult, log_file_strategy="testCase")
    mtr.result_classes = [BannerTestResult(sys.stderr, True, 1)]
    root_logger = logging.getLogger()
    mock_handler = MagicMock()
    mock_handler.name = "strategy_log_file_handler"
    root_logger.addHandler(mock_handler)

    mtr.current_log_file = Path("test.log")

    # Call stopTest
    mtr.stopTest(dummy_test)

    assert mock_handler not in root_logger.handlers
    mock_handler.close.assert_called_once()


def test_stopTest_without_log_file_strategy(dummy_test, mocker, patch_test_runner_instance):
    mocker.patch.object(BannerTestResult, "stopTest")
    mtr = MultiTestResult(BannerTestResult, log_file_strategy=None)
    mtr.result_classes = [BannerTestResult(sys.stderr, True, 1)]

    root_logger = logging.getLogger()
    mock_handler = MagicMock()
    mock_handler.name = "strategy_log_file_handler"
    root_logger.addHandler(mock_handler)

    # Call stopTest
    mtr.stopTest(dummy_test)

    assert mock_handler in root_logger.handlers
    root_logger.removeHandler(mock_handler)
