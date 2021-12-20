*** Settings ***
Documentation   How to handle auxiliaries and connectors creation using Robot framework

Library    pykiso.lib.robot_framework.loader.RobotLoader    examples/robot_record.yaml    WITH NAME    Loader

Suite Setup       Loader.install
Suite Teardown    Loader.uninstall
