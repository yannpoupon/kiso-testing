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
    PortState,
)
from pykiso.lib.auxiliaries.yepkit_auxiliaries.ykur_auxiliary import (
    YKUR_PROTO_ERROR,
    YKUR_PROTO_OK,
    YKUR_TARGET_PORT,
    PortNumberError,
    RelayAction,
    SetStateError,
    StatePortNotRetrieved,
    YkurAuxiliary,
)


@pytest.fixture
def hid_device_mock(mocker):
    return mocker.patch("hid.device")


@pytest.fixture
def ykur_aux_instance(hid_device_mock):
    return YkurAuxiliaryMocker(hid_device_mock)


class YkurAuxiliaryMocker(YkurAuxiliary):
    """Class used to test the function that are mocked in the init"""

    def __init__(self, hid_device_mock):
        self._device = hid_device_mock
        self._product_id = "test_product_id"
        self._path = "test_path"
        self.number_of_port = 4


@pytest.fixture
def raw_send_mock(mocker, ykur_aux_instance):
    return mocker.patch.object(ykur_aux_instance, "_raw_sendreceive")


@pytest.fixture
def set_state_mock(ykur_aux_instance, mocker):
    return mocker.patch.object(ykur_aux_instance, "set_state")


@pytest.fixture
def get_relay_state_mock(ykur_aux_instance, mocker):
    return mocker.patch.object(ykur_aux_instance, "get_relay_state")


def test_no_ykur_device_found_init():
    with pytest.raises(DeviceNotFound):
        YkurAuxiliary(serial_number=12)


def test_ykur_instance(ykur_aux_instance):
    is_instantiated = ykur_aux_instance._create_auxiliary_instance()
    assert is_instantiated

    result = ykur_aux_instance._delete_auxiliary_instance()
    assert result


def test_check_port_number(ykur_aux_instance):
    port_number = 12
    with pytest.raises(PortNumberError):
        ykur_aux_instance.check_port_number(port_number)


@pytest.mark.parametrize(
    "state_returned,result_expected",
    [
        ([RelayAction.GET_STATE, 0x0, 0x01], PortState.ON),
        ([RelayAction.GET_STATE, 0x0, 0x00], PortState.OFF),
    ],
)
def test_get_relay_state(
    ykur_aux_instance, raw_send_mock, state_returned, result_expected
):
    port_number = 1
    raw_send_mock.return_value = state_returned

    state = ykur_aux_instance.get_relay_state(port_number)

    assert state == result_expected
    raw_send_mock.assert_called_once_with([RelayAction.GET_STATE, 0x01])


@pytest.mark.parametrize(
    "state_returned",
    [([0x01, 0x0, 0x01]), ([RelayAction.GET_STATE, 0x0, 0xAA])],
)
def test_get_relay_state_error(ykur_aux_instance, raw_send_mock, state_returned):
    port_number = 1
    raw_send_mock.return_value = state_returned

    with pytest.raises(StatePortNotRetrieved):
        state = ykur_aux_instance.get_relay_state(port_number)

    raw_send_mock.assert_called_once_with([RelayAction.GET_STATE, 0x01])


def test_get_all_ports_state(ykur_aux_instance, get_relay_state_mock):
    list_state = [
        PortState.ON,
        PortState.OFF,
        PortState.ON,
        PortState.OFF,
        PortState.OFF,
    ]
    get_relay_state_mock.side_effect = list_state
    states = ykur_aux_instance.get_all_ports_state()

    assert states == list_state
    get_relay_state_mock.call_count = 5


@pytest.mark.parametrize(
    "message_returned,state_wanted",
    [([0x01, 0x0, YKUR_PROTO_OK], 1), ([0x0, 0x0, YKUR_PROTO_OK], 0)],
)
def test_set_state(ykur_aux_instance, raw_send_mock, message_returned, state_wanted):
    raw_send_mock.return_value = message_returned
    target = 0

    ykur_aux_instance.set_state(target, state_wanted)

    raw_send_mock.assert_called_once_with([state_wanted, 0x11])


@pytest.mark.parametrize(
    "message_returned,target",
    [([0x01, 0x0, 0x1], 1), ([0x01, 0x0, 0x1], "all")],
)
def test_set_state_error(ykur_aux_instance, raw_send_mock, message_returned, target):
    raw_send_mock.return_value = message_returned
    state_wanted = 1
    with pytest.raises(SetStateError):
        ykur_aux_instance.set_state(target, state_wanted)

    raw_send_mock.assert_called_once_with([state_wanted, YKUR_TARGET_PORT[target]])


def test_set_relay_on(set_state_mock, ykur_aux_instance):
    port_number = 2

    ykur_aux_instance.set_relay_on(port_number)

    set_state_mock.assert_called_once_with(port_number, state=RelayAction.SET_ON)


def test_set_relay_off(set_state_mock, ykur_aux_instance):
    port_number = 2

    ykur_aux_instance.set_relay_off(port_number)

    set_state_mock.assert_called_once_with(port_number, state=RelayAction.SET_OFF)


def test_set_all_relays_on(set_state_mock, ykur_aux_instance):

    ykur_aux_instance.set_all_relays_on()

    set_state_mock.assert_called_once_with("all", state=RelayAction.SET_ON)


def test_set_all_relays_off(set_state_mock, ykur_aux_instance):

    ykur_aux_instance.set_all_relays_off()

    set_state_mock.assert_called_once_with("all", state=RelayAction.SET_OFF)


def test_set_all_external_relays_on(set_state_mock, ykur_aux_instance):

    ykur_aux_instance.set_all_external_relays_on()

    set_state_mock.assert_called_once_with("external_relays", state=RelayAction.SET_ON)


def test_set_all_external_relays_off(set_state_mock, ykur_aux_instance):

    ykur_aux_instance.set_all_external_relays_off()

    set_state_mock.assert_called_once_with("external_relays", state=RelayAction.SET_OFF)


@pytest.mark.parametrize(
    "state_port,bool_expected", [(PortState.ON, True), (PortState.OFF, False)]
)
def test_is_relay_on(
    ykur_aux_instance, get_relay_state_mock, state_port, bool_expected
):
    get_relay_state_mock.return_value = state_port
    port_number = 1

    state = ykur_aux_instance.is_relay_on(port_number)

    assert state == bool_expected
    get_relay_state_mock.assert_called_once_with(port_number)


@pytest.mark.parametrize(
    "state_port,bool_expected", [(PortState.OFF, True), (PortState.ON, False)]
)
def test_is_relay_off(
    ykur_aux_instance, get_relay_state_mock, state_port, bool_expected
):
    get_relay_state_mock.return_value = state_port
    port_number = 1

    state = ykur_aux_instance.is_relay_off(port_number)

    assert state == bool_expected
    get_relay_state_mock.assert_called_once_with(port_number)


@pytest.mark.parametrize(
    "packet_received,msg_expected",
    [
        ([0x0] * 65, [0x0] * 20),
        (None, [YKUR_PROTO_ERROR] * 20),
        ([0x0], [YKUR_PROTO_ERROR] * 20),
    ],
)
def test__raw_sendreceive(
    ykur_aux_instance, mocker, hid_device_mock, packet_received, msg_expected
):
    mocker.patch.object(ykur_aux_instance, "_open_and_close_device")
    hid_device_mock.read.return_value = packet_received

    msg = ykur_aux_instance._raw_sendreceive(packetarray=[0x1])

    assert msg == msg_expected
    hid_device_mock.read.assert_called_once()
