##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Ykur Auxiliary
**************

:module: ykur_auxiliary

:synopsis: Auxiliary that can power on and off relays on an Ykur relay board.

.. currentmodule:: ykur_auxiliary

"""
import logging
from enum import IntEnum
from typing import List, Union

from pykiso.lib.auxiliaries.yepkit_auxiliaries.common.yepkit_base import (
    PortNumberError,
    PortState,
    SetStateError,
    StatePortNotRetrieved,
    YepkitBase,
)

log = logging.getLogger(__name__)

# Product id of the ykur device
YKUR_USB_PID_LIST = [0xF1CB]

# YKUR device protocol status declarations
YKUR_PROTO_ERROR = 0xAA
YKUR_PROTO_OK = 0xFF

# YKUR port state meaning declarations
YKUR_PORT_STATE_ERROR = 0xAA


# Dictionary with the byte to get a specific target
YKUR_TARGET_PORT = {
    1: 0x01,
    2: 0x02,
    3: 0x03,
    4: 0x04,
    0: 0x11,  # on board relay
    "external_relays": 0x0A,
    "all": 0xAA,
}


class RelayAction(IntEnum):
    SET_ON = 0x01
    SET_OFF = 0x02
    GET_STATE = 0x03


class YkurAuxiliary(YepkitBase):
    """Auxiliary used to power on and off the relays."""

    def __init__(self, serial_number: str = None, **kwargs):
        """Initialize attribute

        :param serial: Serial number of the device to connect, if he is not defined
            then it will connect to the first Ykush device it find, defaults to None.
        :raises DeviceNotFound: If no device is found or the serial number
            is not the serial of one device.
        """
        super().__init__()
        self.number_of_port = 4
        self.find_device(serial=serial_number, list_pid=YKUR_USB_PID_LIST)

    def _create_auxiliary_instance(self) -> bool:
        """
        :return: always True
        """
        log.internal_info("Create auxiliary instance")
        return True

    def _delete_auxiliary_instance(self) -> bool:
        """
        :return: always True
        """
        log.internal_info("Auxiliary instance deleted")
        return True

    def check_port_number(self, port_number: str):
        """Check if the port indicated is a port of the device

        :raises YkushPortNumberError: Raise error if no port has this number
        """
        if port_number not in range(0, self.number_of_port + 1):
            raise PortNumberError(
                f"The port number {port_number} is not valid for the device,"
                f" it has only {self.number_of_port} ports and the in board relay"
                "that has for 0 for port number"
            )

    def get_relay_state(self, port_number: int) -> PortState:
        """Returns the state of an external relays or the on board relay.

        :raises YkurStatePortNotRetrieved: If the state couldn't be retrieved
        :return: 0 if the port is off, 1 if the port is on
        """
        self.check_port_number(port_number)
        status, _, state = self._raw_sendreceive(
            [RelayAction.GET_STATE, YKUR_TARGET_PORT[port_number]]
        )

        if status == RelayAction.GET_STATE and state != YKUR_PORT_STATE_ERROR:
            return PortState.ON if state else PortState.OFF
        else:
            raise StatePortNotRetrieved("The state of the relay couldn't be retrieved")

    def get_all_ports_state(self) -> List[PortState]:
        """Returns the state of all the external relays.

        :raises YkurStatePortNotRetrieved: The states couldn't be retrieved
        :return: list with 0 if a port is off, 1 if on.
            The order is [on board relay, external relay 1, external relay 2 ...]
        """
        return [
            self.get_relay_state(port_number)
            for port_number in range(0, self.number_of_port + 1)
        ]

    def set_state(self, target: Union[int, str], state: int):
        """Set an external relay, on board relay, all external relays or all
            relays On or Off.

        :param target: number of the port or "external_relays" or "all_relays"
        :raises YkurSetStateError: if the operation had an error
        """
        _, _, status = self._raw_sendreceive([state, YKUR_TARGET_PORT[target]])

        if status != YKUR_PROTO_OK:
            if isinstance(target, int):
                raise SetStateError(
                    f"An error occured during the switch of the port {target}"
                )
            else:
                raise SetStateError(
                    f"An error occured during the switch for {target.split('_')[0]} relays"
                )

    def set_relay_on(self, port_number: int):
        """Power on an external relay or the on board relay.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_state(port_number, state=RelayAction.SET_ON)

    def set_relay_off(self, port_number: int):
        """Power off an external relay or the on board relay.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_state(port_number, state=RelayAction.SET_OFF)

    def set_all_relays_on(self):
        """Power on all the external relays and the on board relay.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_state("all", state=RelayAction.SET_ON)

    def set_all_relays_off(self):
        """Power off all the external relays and the on board relay.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_state("all", state=RelayAction.SET_OFF)

    def set_all_external_relays_on(self):
        """Power on all the external relays.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_state("external_relays", state=RelayAction.SET_ON)

    def set_all_external_relays_off(self):
        """Power off all the external relays.

        :raises YkushSetStateError: if the operation had an error
        """
        self.set_state("external_relays", state=RelayAction.SET_OFF)

    def is_relay_on(self, port_number: int) -> bool:
        """Check if a relay is on.

        :return: True if the relay is on, else False
        """
        return bool(self.get_relay_state(port_number))

    def is_relay_off(self, port_number: int) -> bool:
        """Check if a relay is off.

        :return: True if the relay is off, else False
        """
        return not bool(self.get_relay_state(port_number))
