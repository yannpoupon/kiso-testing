##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Yepkit base
***********

:module: yepkit_base

:synopsis: Base that create general method to use with yepkit devices.

.. currentmodule:: yepkit_base

"""
import logging
from contextlib import contextmanager
from enum import IntEnum
from typing import Any, List, Optional

import hid

from pykiso.interfaces.dt_auxiliary import DTAuxiliaryInterface

log = logging.getLogger(__name__)

# YEPKIT device USB VID
YEPKIT_USB_VID = 0x04D8

# YEPKIT device USB comm declarations
YEPKIT_USB_TIMEOUT = 1000  # timeout in ms
YEPKIT_USB_PACKET_SIZE = 64
YEPKIT_USB_PACKET_PAYLOAD_SIZE = 20


class PortState(IntEnum):
    OFF = 0
    ON = 1


class YepkitBase(DTAuxiliaryInterface):
    """Base for auxiliary of yepkit device"""

    def __init__(self, **kwargs):
        """Initialize attribute"""
        super().__init__(
            is_proxy_capable=False,
            tx_task_on=False,
            rx_task_on=False,
            connector_required=False,
            **kwargs,
        )
        self._product_id = None
        self._path = None
        self._device = None

    def find_device(
        self,
        list_pid: List[int],
        serial: int = None,
        path: str = None,
    ) -> List[int]:
        """Find an Yepkit device that has a product id in the list, will
        automatically connect to the first one it find, if you have multiple devices
        connected you have to precise the serial number or the path to the device.

        :param list_pid: list of product id for the devices to find.
        :param serial: serial number of the device, defaults to None
        :param path: path of the device, defaults to None
        :raises YkushDeviceNotFound: if no ykush device is found
        """
        list_yepkit_device = []
        if path:
            # open the provided path
            # blocking by default
            self._device = hid.device()
            self._device.open_path(path)
            self._path = path
            self._device.close()
        else:
            # otherwise try to locate a device
            for device in hid.enumerate(0, 0):
                if (
                    device["vendor_id"] == YEPKIT_USB_VID
                    and device["product_id"] in list_pid
                ):
                    list_yepkit_device.append(device["serial_number"])
                    if serial is None or serial == device["serial_number"]:
                        # Alber3.1 3.2 object attribute for YKUSHXS
                        self._product_id = device["product_id"]
                        return self.find_device(list_pid=list_pid, path=device["path"])

        if self._path is None:
            if list_yepkit_device == []:
                raise DeviceNotFound(
                    "Could not connect to a device, no device was found."
                )
            else:
                raise DeviceNotFound(
                    f"The serial numbers available are : {list_yepkit_device}\n"
                    f"No device was found with the serial number {serial}\n"
                    if serial
                    else "",
                )

    @contextmanager
    def _open_and_close_device(self):
        """Context manager to open and close device every time we send a message
        else we will get an empty message every time in response.
        """
        self._device = hid.device()
        self._device.open_path(self._path)
        try:
            yield
        finally:
            self._device.close()

    def _raw_sendreceive(self, packetarray: List[int]) -> List[int]:
        """Send a message to the device and get the returned message.

        :param packetarray: packet to send to do an operation
        :return: response to the message send
        """
        with self._open_and_close_device():
            packetarray = packetarray + [0x00] * (
                YEPKIT_USB_PACKET_SIZE - len(packetarray)
            )
            self._device.write(packetarray)
            recvpacket = self._device.read(
                max_length=YEPKIT_USB_PACKET_SIZE, timeout_ms=YEPKIT_USB_TIMEOUT
            )

            # if not None return the bytes we actually need
            if recvpacket is None or len(recvpacket) < YEPKIT_USB_PACKET_PAYLOAD_SIZE:
                return [0xFF] * YEPKIT_USB_PACKET_PAYLOAD_SIZE
            return recvpacket[:YEPKIT_USB_PACKET_PAYLOAD_SIZE]

    def get_serial_number_string(self) -> str:
        """Returns the device serial number string"""
        with self._open_and_close_device():
            return self._device.get_serial_number_string()

    def _run_command(self, cmd_message: Any, cmd_data: Optional[bytes]) -> None:
        """Not used.

        Simply respect the interface.
        """

    def _receive_message(self, timeout_in_s: float) -> None:
        """Not used.

        Simply respect the interface.
        """


class YepkitError(Exception):
    """General Ykush specific exception used as basis for all others."""

    pass


class DeviceNotFound(YepkitError):
    """Raised when no device is found."""

    pass


class StatePortNotRetrieved(YepkitError):
    """Raised when the state of a port can't be retrieved."""

    pass


class SetStateError(YepkitError):
    """Raised when a port couldn't be switched on or off."""

    pass


class PortNumberError(YepkitError):
    """Raised when the port number doesn't exist."""

    pass
