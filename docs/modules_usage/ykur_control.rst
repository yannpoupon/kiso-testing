.. _ykur_aux:

Controlling an Yepkit USB relay
===============================

The ykur auxiliary offers commands to control an Yepkit USB relay,
allowing to switch the on board relay and external relay on and off individually.

More information on the device can be found on the following link :
`YKUSH (Yepkit USB Switchable Hub) <https://www.yepkit.com/product/300106/YKUR>`_.

Usage Examples
~~~~~~~~~~~~~~

To use the auxiliary in your test scripts the auxiliary must be properly defined
in the config yaml. Example:

.. code:: yaml

  auxiliaries:
      ykur_aux:
        config:
          # Serial number to connect to. Example: "YK00006"
          serial_number : null # null = auto detection.
        type: pykiso.lib.auxiliaries.yepkit_auxiliaries.ykush_auxiliary:YkurAuxiliary

Below find a example for the usage in a test script. All available methods are shown there.

.. literalinclude:: ../../examples/test_suite_ykur/test_ykur.py
    :language: python
