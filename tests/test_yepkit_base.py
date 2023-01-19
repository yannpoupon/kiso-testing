##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################


import pytest

from pykiso.lib.auxiliaries.yepkit_auxiliaries.common.yepkit_base import (
    DeviceNotFound,
    YepkitBase,
)

TEST_PID_LIST = [0x0F2, 0x233F, 0x0042]


class YepkitBaseMocker(YepkitBase):
    def __init__(self, hid_device_mock, **kwargs):
        super().__init__(**kwargs)
        self._device = hid_device_mock

    def _create_auxiliary_instance(self):
        pass

    def _delete_auxiliary_instance(self):
        pass


@pytest.fixture
def hid_device_mock(mocker):
    return mocker.patch("hid.device")


@pytest.fixture
def hid_enumerate_mock(mocker):

    return mocker.patch("hid.enumerate")


@pytest.fixture
def yekpit_base_instance(hid_device_mock):
    return YepkitBaseMocker(hid_device_mock)


def test_find_device_path(hid_device_mock, yekpit_base_instance):
    path = "test"

    yekpit_base_instance.find_device(path=path, list_pid=TEST_PID_LIST)

    hid_device_mock.assert_called_once()


def test_find_device_serial(yekpit_base_instance, hid_enumerate_mock):
    serial = "YK28389"
    device = {
        "vendor_id": 0x04D8,
        "product_id": 0x0042,
        "serial_number": serial,
        "path": "test_path",
    }
    hid_enumerate_mock.return_value = [device]

    yekpit_base_instance.find_device(serial=serial, list_pid=TEST_PID_LIST)

    hid_enumerate_mock.assert_called_once_with(0, 0)
    assert yekpit_base_instance._product_id == device["product_id"]
    assert yekpit_base_instance._path == device["path"]


@pytest.mark.parametrize(
    "list_device_returned",
    [
        ([]),
        (
            [
                {
                    "vendor_id": 0x04D8,
                    "product_id": 0x0042,
                    "serial_number": "YK28389",
                    "path": "test_path",
                }
            ]
        ),
    ],
)
def test_find_device_no_device_found(
    yekpit_base_instance, hid_enumerate_mock, list_device_returned
):
    hid_enumerate_mock.return_value = list_device_returned
    yekpit_base_instance._device = None
    with pytest.raises(DeviceNotFound):
        yekpit_base_instance.find_device(serial=12, list_pid=TEST_PID_LIST)

    hid_enumerate_mock.assert_called_once_with(0, 0)


@pytest.mark.parametrize(
    "packet_received,msg_expected",
    [([0x0] * 65, [0x0] * 20), (None, [0xFF] * 20), ([0x0], [0xFF] * 20)],
)
def test__raw_sendreceive(
    yekpit_base_instance, mocker, hid_device_mock, packet_received, msg_expected
):
    mocker.patch.object(yekpit_base_instance, "_open_and_close_device")
    hid_device_mock.read.return_value = packet_received

    msg = yekpit_base_instance._raw_sendreceive(packetarray=[0x1])

    assert msg == msg_expected
    hid_device_mock.read.assert_called_once()
