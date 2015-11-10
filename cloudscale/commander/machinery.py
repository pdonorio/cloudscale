#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Machinery on top of docker-machine binary """

from __future__ import division, print_function, absolute_import
import logging
from .. import myself, lic  # , __version__
from .base import Basher, join_command
from collections import OrderedDict
import getpass

__author__ = myself
__copyright__ = myself
__license__ = lic

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

#######################
DRIVER = 'openstack'


#######################
class TheMachine(Basher):

    _com = 'docker-machine'
    _driver = DRIVER
    _oovar = {
        'OS_AUTH_URL': "http://cloud.pico.cineca.it:5000/v2.0",
        'OS_USERNAME': "pdonorio",
        'OS_PASSWORD': "",
        'OS_REGION_NAME': "RegionOne",
        'OS_TENANT_NAME': "mw",
    }

    def __init__(self, driver=None):
        super(TheMachine, self).__init__()
        if driver is not None:
            self._driver = driver
        _logger.debug("Machine with driver '%s'" % self._driver)

    def init_environment(self):
        """ Define environment variables for machine driver """
        envvars = self._oovar
        pwd = getpass.getpass()
        envvars['OS_PASSWORD'] = pwd

        for key, value in envvars.items():
            self.set_environment_var(key, value)
        _logger.info("Environment set for %s" % self._driver)
        # print(machine._shell.env['OS_TENANT_NAME'])

    def machine_com(self, operation='ls', node=None, params={}, debug=True):
        """ Machine for openstack """

        # Init environment variables only in Openstack case
        if self._driver == DRIVER:
            self.init_environment()
        # Start-up command
        com = self._com
        # Base options
        opts = OrderedDict()
        if debug:
            opts['debug'] = operation
        else:
            com += ' ' + operation
        # Choose driver
        opts["driver"] = self._driver
        # Remaining options (extra)
        for key, value in params.items():
            opts[key] = value
        # Compose command
        machine_com = join_command(com, opts)
        if node is not None:
            machine_com += ' ' + node
        # Execute
        self.do(machine_com)
        return machine_com

    def create(self, node='machinerytest'):
        """ Machine for openstack """

        vars = {}
        mode = self._driver == DRIVER

        if mode:
            # Remaining
            vars = {
                self._driver + "-image-name": "ubuntu-trusty-server",
                self._driver + "-ssh-user": "ubuntu",
                self._driver + "-sec-groups": "default",
                self._driver + "-net-name": "mw-net",
                self._driver + "-floatingip-pool": "ext-net",
                self._driver + "-flavor-name": "m1.small",
            }
        return self.machine_com('create', node, params=vars, debug=mode)
