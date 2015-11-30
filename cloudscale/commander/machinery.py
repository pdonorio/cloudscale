#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Machinery on top of docker-machine binary """

from __future__ import division, print_function, absolute_import
from .. import myself, lic, DLEVEL, logging
from .shell import Basher, colors
from collections import OrderedDict

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

__author__ = myself
__copyright__ = myself
__license__ = lic
_logger = logging.getLogger(__name__)
_logger.setLevel(DLEVEL)

#######################
DRIVER = 'openstack'


def read_init(config_file='conf/'+DRIVER+'.ini',
              section='credentials', prefix='os_', upper=True):
    """ Read configuration for credentials to access a driver """
    conf = {}
    config = ConfigParser()
    config.read(config_file)

    # read values from a section
    for option in config.options(section):
        key = prefix + option
        if upper:
            key = key.upper()
        conf[key] = config.get(section, option)

    return conf


#######################
class TheMachine(Basher):

    _com = 'docker-machine'
    _eip = None
    _images_path = "/.docker/machine/machines/"
    _driver = DRIVER
    _user = 'root'
    _oovar = {
        # What we expect from configuration file (.ini)
        'OS_AUTH_URL': None,
        'OS_USERNAME': None,
        'OS_PASSWORD': None,
        'OS_REGION_NAME': None,
        'OS_TENANT_NAME': None,
    }

    def __init__(self, driver=None):
        """ Set the driver and read config """
        super(TheMachine, self).__init__()
        if driver is not None:
            self._driver = driver
        if self._driver == DRIVER:
            self._oovar = read_init()
        _logger.debug("Machine with driver '%s'" % self._driver)

    def init_environment(self):
        """ Define environment variables for machine driver """

        # Read the password if missing
        if self._oovar['OS_PASSWORD'] is None or \
                self._oovar['OS_PASSWORD'].strip() == '':
            self._oovar['OS_PASSWORD'] = self.passw()

        # Use them as environment
        for key, value in self._oovar.items():
            self.set_environment_var(key, value)
        _logger.info("Environment set for %s" % self._driver)

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

        # return self.do(machine_com, no_output=True)
        out = self.do(machine_com)  # , no_output=True)
        if out is False:
            # Command has failed...
            exit(1)
        return out

    def list(self, with_driver=None):
        """ Get all machine list """
        machines = []
        params = {}
        if with_driver is not None:
            params['filter'] = 'driver=' + with_driver
        _logger.info(colors.yellow | "Checking machine list")
        for line in self.machine_com(params=params).split('\n'):
            if line.strip() == '':
                continue
            pieces = line.split()
            machines.append(pieces[0])
        # Remove header
        del machines[0]
        return machines

    def exists(self, node):
        """ Check if current machine exists """
        current_list = self.list()
        check = node in current_list
        _logger.info("Check node *%s*: %s" % (node, check))
        # _logger.info(current_list)
        return check

    def create(self, node='machinerytest'):
        """ Machine creation (default for openstack) """

        dvars = {}
        mode = self._driver == DRIVER
        if not mode and self._driver == 'virtualbox':
            self._user = 'docker'

        if mode:
            self._user = 'ubuntu'
            # Remaining
            dvars = {
                self._driver + "-image-name": "ubuntu",
                self._driver + "-ssh-user": self._user,
                self._driver + "-sec-groups": "sec",
                self._driver + "-net-name": "my-net",
                self._driver + "-floatingip-pool": "ext-net",
                self._driver + "-flavor-name": "m1.small",
            }
            dvars = read_init(section='options',
                              prefix=self._driver, upper=False)

        if self.exists(node):
            print(colors.warn | "Skipping:", colors.bold |
                  "Machine '%s' Already exists" % node)
            return
        return self.machine_com('create', node, params=dvars, debug=mode)

    def connect(self, node):
        # Get ip
        self._eip = self.machine_com('ip', node).strip()
        # Get key
        k = self._shell.env.home + \
            self._images_path + node + "/id_rsa"
        # Connect
        self.remote(host=self._eip, user=self._user, kfile=k)

    def remove(self, node='machinerytest'):
        """ Machine removal """
        return self.machine_com('rm', node, debug=(self._driver == DRIVER))

    def prepare(self, node):
        self.create(node)
        self.connect(node)
        return self
