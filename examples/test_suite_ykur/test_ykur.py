##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Ykur auxiliary test
*******************

:module: test_ykur

:synopsis: Example test that shows how to control the Ykur relays.

.. currentmodule:: test_ykur

"""

import logging

import pykiso
from pykiso.auxiliaries import ykur_aux
from pykiso.lib.auxiliaries.yepkit_auxiliaries.ykur_auxiliary import (
    YkurAuxiliary,
)


@pykiso.define_test_parameters(suite_id=1, case_id=1, aux_list=[ykur_aux])
class ExampleYkushTest(pykiso.BasicTest):
    def setUp(self):
        """Hook method from unittest in order to execute code before test case run."""
        logging.info(
            f"--------------- SETUP: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

    def test_run(self):
        logging.info(
            f"--------------- RUN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )

        state = ykur_aux.get_relay_state(port_number=0)
        logging.info(f"The state of the port is :{state.name}")

        ykur_aux.set_relay_off(0) if state else ykur_aux.set_relay_on(0)

    def tearDown(self):
        """Hook method from unittest in order to execute code after test case run."""
        logging.info(
            f"--------------- TEARDOWN: {self.test_suite_id}, {self.test_case_id} ---------------"
        )
