##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import sys
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pykiso.test_result.text_result import BannerTestResult, MultiFileHandler, ResultStream

DUMMY_FILE = "dummy.txt"


@pytest.fixture()
def mock_stderr(mocker):
    return mocker.patch("sys.stderr")


@pytest.fixture()
def mock_open(mocker):
    return mocker.patch("builtins.open", return_value=MagicMock())


class TestResultStream:

    test_result_inst = None

    @pytest.fixture()
    def test_result_instance(self, mock_stderr, mock_open, mocker):
        result_stream = ResultStream(DUMMY_FILE)
        mocker.patch.object(result_stream, "multifile_handler", mock_open)
        return result_stream

    @pytest.mark.parametrize(
        "provided_file, expected_type, expected_type_ctx, close_calls",
        [
            (None, nullcontext, type(sys.stderr), 0),
            ("my_file", ResultStream, ResultStream, 1),
        ],
    )
    def test_open(
        self,
        mocker,
        mock_open,
        provided_file,
        expected_type,
        expected_type_ctx,
        close_calls,
    ):
        mock_close = mocker.patch.object(ResultStream, "close", return_value=None)

        stream = ResultStream(provided_file)
        assert type(stream) == expected_type

        del stream

        with ResultStream(provided_file) as stream:
            assert type(stream) == expected_type_ctx

        assert mock_close.call_count == close_calls

    def test_constructor(self, mock_open):
        stream = ResultStream(DUMMY_FILE)

        assert isinstance(stream, ResultStream)
        mock_open.assert_called_once_with(Path(DUMMY_FILE), "a", encoding="utf-8")

    def test_write(self, test_result_instance):
        to_write = "data"
        test_result_instance.write(to_write)
        test_result_instance.stderr.write.assert_called_once_with(to_write)
        test_result_instance.multifile_handler.write.assert_called_once_with(to_write)

    def test_flush(self, mocker, test_result_instance):
        test_result_instance.flush()

        test_result_instance.stderr.flush.assert_called_once()
        test_result_instance.multifile_handler.flush.assert_called_once()

    def test_close(self, test_result_instance):
        assert test_result_instance.stderr is not None
        assert test_result_instance.multifile_handler is not None

        test_result_instance.close()

        assert test_result_instance.stderr is None
        assert test_result_instance.multifile_handler is None


class TestBannerTestResult:
    @pytest.fixture()
    def banner_test_result_instance(self):
        return BannerTestResult(sys.stderr, True, 1)

    @pytest.mark.parametrize(
        "error, result_expected",
        [
            ((ValueError, None, None), True),
            (None, False),
        ],
    )
    def test_addSubTest(self, mocker, banner_test_result_instance, error, result_expected):
        add_subTest_mock = mocker.patch("unittest.result.TestResult.addSubTest")
        test_mock = mocker.patch("pykiso.test_coordinator.test_case.BasicTest")
        subtest_mock = mocker.patch("unittest.case._SubTest", failureException=AssertionError)

        banner_test_result_instance.addSubTest(test_mock, subtest_mock, error)

        add_subTest_mock.assert_called_once_with(test_mock, subtest_mock, error)

        assert banner_test_result_instance.error_occurred == result_expected


class TestMultiFileHandler:

    @pytest.fixture()
    def multi_file_handler(self):
        return MultiFileHandler()

    def test_init_with_files_opens_files(self, tmp_path: Path, mock_open: MagicMock):
        tmp_files = [tmp_path / "file1.txt", tmp_path / "file2.txt"]
        writer = MultiFileHandler(tmp_files)
        assert set(writer.files.keys()) == {f.resolve() for f in tmp_files}
        assert mock_open.call_count == 2

    def test_add_file_adds_and_opens_file(
        self, mock_open: MagicMock, tmp_path: Path, multi_file_handler: MultiFileHandler
    ):
        file_path = tmp_path / "file.txt"
        multi_file_handler.add_file(file_path)
        assert file_path.resolve() in multi_file_handler.files
        mock_open.assert_called_once_with(file_path, "a", encoding="utf-8")

    def test_remove_file_closes_and_removes(self, tmp_path: Path, multi_file_handler: MultiFileHandler):
        file_path = tmp_path / "file.txt"
        mock_file = MagicMock()
        multi_file_handler.files[file_path.resolve()] = mock_file
        multi_file_handler.remove_file(file_path)
        mock_file.close.assert_called_once()
        assert file_path.resolve() not in multi_file_handler.files

    def test_write_writes_to_all_files(self, tmp_path: Path, multi_file_handler: MultiFileHandler):
        file1 = tmp_path / "f1.txt"
        file2 = tmp_path / "f2.txt"
        mock_file1 = MagicMock()
        mock_file2 = MagicMock()
        multi_file_handler.files[file1.resolve()] = mock_file1
        multi_file_handler.files[file2.resolve()] = mock_file2

        multi_file_handler.write("hello")

        mock_file1.write.assert_called_once_with("hello")
        mock_file2.write.assert_called_once_with("hello")

    def test_flush_flushes_and_fsyncs(self, mocker, tmp_path: Path, multi_file_handler: MultiFileHandler):
        file1 = tmp_path / "f1.txt"
        mock_file = MagicMock()
        mock_file.fileno.return_value = 42
        multi_file_handler.files[file1.resolve()] = mock_file
        mock_fsync = mocker.patch("os.fsync")

        multi_file_handler.flush()

        mock_file.flush.assert_called_once()
        mock_file.fileno.assert_called_once()
        mock_fsync.assert_called_once_with(42)

    def test_close_closes_all_and_clears(self, tmp_path: Path, multi_file_handler: MultiFileHandler):
        file1 = tmp_path / "f1.txt"
        file2 = tmp_path / "f2.txt"
        mock_file1 = MagicMock()
        mock_file2 = MagicMock()
        multi_file_handler.files[file1.resolve()] = mock_file1
        multi_file_handler.files[file2.resolve()] = mock_file2

        multi_file_handler.close()

        mock_file1.close.assert_called_once()
        mock_file2.close.assert_called_once()
        assert multi_file_handler.files == {}
