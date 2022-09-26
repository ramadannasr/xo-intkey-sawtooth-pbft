# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import json
import shlex
import logging
import unittest
import subprocess
import time
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


EXPECTED = {
    0: {3, 2, 1},
    1: {0, 3, 2},
    2: {0, 3, 1},
    3: {0, 2, 1},
}


class TestPeerList(unittest.TestCase):
    def setUp(self):
        endpoints = ['rest-api-{}:8008'.format(i)
                     for i in range(len(EXPECTED))]

        wait_for_rest_apis(endpoints)

    def test_peer_list(self):
        '''Test various CLI commands for reporting peers.

        Five validators are started, peered as described in EXPECTED
        (see the test's associated yaml file for details).
        '''

        LOGGER.info('Testing `sawtooth peer list`')

        for node_number, peer_numbers in EXPECTED.items():
            actual_peers = _get_peers(node_number)

            expected_peers = {
                _make_tcp_address(peer_number)
                for peer_number in peer_numbers
            }

            LOGGER.debug(
                'Actual: %s -- Expected: %s',
                actual_peers,
                expected_peers)

            self.assertEqual(
                actual_peers,
                expected_peers)

        ###

        LOGGER.info('Testing `sawtooth status show`')

        sawtooth_status_expected = {
            node_number: {
                _make_tcp_address(node_number): [
                    {'endpoint': _make_tcp_address(peer_number)}
                    for peer_number in peers
                ]
            }
            for node_number, peers in EXPECTED.items()
        }

        for node_number in EXPECTED:
            status = json.loads(_run_peer_command(
                'sawtooth status show --url {}'.format(
                    _make_http_address(node_number))))

            LOGGER.debug(
                'Node %s status: %s',
                node_number,
                json.dumps(status, indent=4))

            self.assertEqual(
                sawtooth_status_expected[node_number],
                {status['endpoint']: status['peers']},
            )

        ###

        LOGGER.info('Testing `sawnet peers list`')

        peers_list_expected = {
            _make_tcp_address(node_number): [
                _make_tcp_address(peer_number)
                for peer_number in peers
            ]
            for node_number, peers in EXPECTED.items()
        }

        http_addresses = ','.join([
            _make_http_address(node_number)
            for node_number in EXPECTED
        ])

        # make sure pretty-print option works
        subprocess.run(
            shlex.split(
                'sawnet peers list {} --pretty'.format(http_addresses)
            ), check=True
        )

        sawnet_peers_output = json.loads(
            _run_peer_command(
                'sawnet peers list {}'.format(http_addresses)
            )
        )

        self.assertEqual(
            sawnet_peers_output,
            peers_list_expected)


def _get_peers(node_number, fmt='json'):
    cmd_output = _run_peer_command(
        'sawtooth peer list --url {} --format {}'.format(
            _make_http_address(node_number),
            fmt))

    if fmt == 'json':
        parsed = json.loads(cmd_output)

    elif fmt == 'csv':
        parsed = cmd_output.split(',')

    return set(parsed)


def _run_peer_command(command):
    return subprocess.check_output(
        shlex.split(command)
    ).decode().strip().replace("'", '"')


def _make_http_address(node_number):
    return 'http://rest-api-{}:8008'.format(node_number)


def _make_tcp_address(node_number):
    return 'tcp://validator-{}:8800'.format(node_number)


def wait_for_rest_apis(endpoints):
    """Pause the program until all the given REST API endpoints are available.

    Args:
        endpoints (list of str): A list of host:port strings.
    """
    for endpoint in endpoints:
        http = 'http://'
        url = endpoint if endpoint.startswith(http) else http + endpoint
        wait_until_status(
            '{}/blocks'.format(url),
            status_code=200)
def wait_until_status(url, status_code=200):
    """Pause the program until the given url returns the required status.

    Args:
        url (str): The url to query.
        status_code (int, optional): The required status code. Defaults to 200.
    """
    sleep_time = 1
    while True:
        try:
            response = urlopen(url)
            if response.getcode() == status_code:
                return

        except HTTPError as err:
            if err.code == status_code:
                return

            LOGGER.debug('failed to read url: %s', str(err))
        except URLError as err:
            LOGGER.debug('failed to read url: %s', str(err))

        LOGGER.debug('Retrying in %s secs', sleep_time)
        time.sleep(sleep_time)
