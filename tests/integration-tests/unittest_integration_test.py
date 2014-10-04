from __future__ import print_function

__author__ = 'Leonid.Shalupov'

import os
import sys
import subprocess

import pytest

import virtual_environments
from service_messages import parse_service_messages, ServiceMessage, assert_service_messages


@pytest.fixture(scope='module')
def venv(request):
    """
    Prepares a virtual environment for unittest, no extra packages required
    :rtype : virtual_environments.VirtualEnvDescription
    """
    return virtual_environments.prepare_virtualenv()


def test_nested_suits(venv):
    output = run_directly(venv, 'nested_suits.py')

    ms = parse_service_messages(output)
    assert_service_messages(
        ms,
        [
            ServiceMessage('testStarted', {'name': '__main__.TestXXX.runTest'}),
            ServiceMessage('testFinished', {'name': '__main__.TestXXX.runTest'}),
        ])


def test_docstring(venv):
    output = run_directly(venv, 'docstring.py')

    ms = parse_service_messages(output)
    assert_service_messages(
        ms,
        [
            ServiceMessage('testStarted', {'name': 'A test'}),
            ServiceMessage('testFinished', {'name': 'A test'}),
        ])


def test_assert(venv):
    output = run_directly(venv, 'assert.py')

    ms = parse_service_messages(output)
    assert_service_messages(
        ms,
        [
            ServiceMessage('testStarted', {'name': '__main__.TestXXX.runTest'}),
            ServiceMessage('testFailed', {'name': '__main__.TestXXX.runTest', 'message': 'Failure'}),
            ServiceMessage('testFinished', {'name': '__main__.TestXXX.runTest'}),
        ])

    assert ms[1].params['details'].index("assert 1 == 0") > 0


def test_setup_error(venv):
    output = run_directly(venv, 'setup_error.py')

    ms = parse_service_messages(output)
    assert_service_messages(
        ms,
        [
            ServiceMessage('testStarted', {'name': '__main__.TestXXX.runTest'}),
            ServiceMessage('testFailed', {'name': '__main__.TestXXX.runTest', 'message': 'Error'}),
            ServiceMessage('testFinished', {'name': '__main__.TestXXX.runTest'}),
        ])

    assert ms[1].params['details'].index("RRR") > 0
    assert ms[1].params['details'].index("setUp") > 0


def test_teardown_error(venv):
    output = run_directly(venv, 'teardown_error.py')

    ms = parse_service_messages(output)
    assert_service_messages(
        ms,
        [
            ServiceMessage('testStarted', {'name': '__main__.TestXXX.runTest'}),
            ServiceMessage('testFailed', {'name': '__main__.TestXXX.runTest', 'message': 'Error'}),
            ServiceMessage('testFinished', {'name': '__main__.TestXXX.runTest'}),
        ])

    assert ms[1].params['details'].index("RRR") > 0
    assert ms[1].params['details'].index("tearDown") > 0


def test_discovery(venv):
    if sys.version_info < (2, 7):
        pytest.skip("unittest discovery requires Python 2.7+")

    output = run_directly(venv, 'discovery.py')

    ms = parse_service_messages(output)
    assert_service_messages(
        ms,
        [
            ServiceMessage('testStarted', {'name': 'testsimple.TestTeamcityMessages.runTest'}),
            ServiceMessage('testFinished', {'name': 'testsimple.TestTeamcityMessages.runTest'}),
        ])


def test_discovery_errors(venv):
    if sys.version_info < (2, 7):
        pytest.skip("unittest discovery requires Python 2.7+")

    output = run_directly(venv, 'discovery_errors.py')

    ms = parse_service_messages(output)
    assert_service_messages(
        ms,
        [
            ServiceMessage('testStarted', {'name': 'unittest.loader.ModuleImportFailure.testsimple'}),
            ServiceMessage('testFailed', {'name': 'unittest.loader.ModuleImportFailure.testsimple', 'message': 'Error'}),
            ServiceMessage('testFinished', {'name': 'unittest.loader.ModuleImportFailure.testsimple'}),
        ])

    assert ms[1].params['details'].index("ImportError") > 0


def run_directly(venv, file):
    env = virtual_environments.get_clean_system_environment()
    env['TEAMCITY_VERSION'] = "0.0.0"

    # Start the process and wait for its output
    command = os.path.join(venv.bin, 'python') + " " + os.path.join('tests', 'guinea-pigs', 'unittest', file)
    print("RUN: " + command)
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, shell=True)
    output = "".join([x.decode() for x in proc.stdout.readlines()])
    proc.wait()

    print("OUTPUT:" + output.replace("#", "*"))

    return output