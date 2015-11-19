#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Machinery on top of docker-machine binary """

from __future__ import division, print_function, absolute_import
from .. import myself, lic, DLEVEL, logging
from .base import Basher, colors
from collections import OrderedDict
import getpass

__author__ = myself
__copyright__ = myself
__license__ = lic
_logger = logging.getLogger(__name__)
_logger.setLevel(DLEVEL)

#######################
DRIVER = 'openstack'


#######################
class TheMachine(Basher):

    _com = 'docker-machine'
    _images_path = "/.docker/machine/machines/"
    _driver = DRIVER
    _user = 'root'
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
        envvars['OS_PASSWORD'] = getpass.getpass()

        for key, value in envvars.items():
            self.set_environment_var(key, value)
        _logger.info("Environment set for %s" % self._driver)
        # print(machine._shell.env['OS_TENANT_NAME'])

    def machine_com(self, operation='ls', node=None, params={}, debug=False):
        """ Machine for openstack """

        # Init environment variables only in Openstack case
        if operation == 'create' and self._driver == DRIVER:
            self.init_environment()
            debug = True
        # Start-up command
        com = self._com
        # Base options
        opts = OrderedDict()
        if debug:
            opts['debug'] = operation
        else:
            com += ' ' + operation
        if operation == 'create':
            # Choose driver
            opts["driver"] = self._driver
            # Remaining options (extra)
            for key, value in params.items():
                opts[key] = value
        # Compose command
        machine_com = self.join_command(com, opts)
        if node is not None:
            machine_com += ' ' + node
        # Execute
        _logger.debug("Command: %s" % machine_com)
        return self.do(machine_com)  # , no_output=True)
        # return machine_com

    def list(self):
        """ Get all machine list """
        machines = []
        _logger.info(colors.yellow | "Checking machine list")
        for line in self.machine_com().split('\n'):
            if line.strip() == '':
                continue
            machines.append(line.split()[0])
        return machines

    def exists(self, node):
        """ Check if current machine exists """
        return node in self.list()

    def create(self, node='machinerytest'):
        """ Machine creation (default for openstack) """

        vars = {}
        mode = self._driver == DRIVER
        if not mode and self._driver == 'virtualbox':
            self._user = 'docker'

        if mode:
            self._user = 'ubuntu'
            # Remaining
            vars = {
                self._driver + "-image-name": "dockerMin",
                self._driver + "-ssh-user": self._user,
                self._driver + "-sec-groups": "paulie",
                self._driver + "-net-name": "mw-net",
                self._driver + "-floatingip-pool": "ext-net",
                self._driver + "-flavor-name": "m1.small",
            }

        if self.exists(node):
            print(colors.warn | "Skipping:", colors.bold |
                  "Machine '%s' Already exists" % node)
            return
        return self.machine_com('create', node, params=vars, debug=mode)

    def connect(self, node):
        # Get ip
        IP = self.machine_com('ip', node).strip()
        # Get key
        k = self._shell.env.home + \
            self._images_path + node + "/id_rsa"
        print(k)
        # Connect
        self.remote(host=IP, user=self._user, kfile=k)

    def remove(self, node='machinerytest'):
        """ Machine removal """
        return self.machine_com('rm', node, debug=(self._driver == DRIVER))
