#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Machinery on top of docker-machine binary """

from __future__ import division, print_function, absolute_import
from .. import myself, lic, DLEVEL, logging
from .base import Basher  # , join_command, colors
# from collections import OrderedDict

__author__ = myself
__copyright__ = myself
__license__ = lic
_logger = logging.getLogger(__name__)
_logger.setLevel(DLEVEL)


#######################
class Dockerizing(Basher):

    _com = 'docker'

    def docker_com(self, operation='ls', node=None, params={}, debug=True):
        """ docker commands """

        # # Init environment variables only in Openstack case
        # if self._driver == DRIVER:
        #     self.init_environment()
        # # Start-up command
        # com = self._com
        # # Base options
        # opts = OrderedDict()
        # if debug:
        #     opts['debug'] = operation
        # else:
        #     com += ' ' + operation
        # if operation == 'create':
        #     # Choose driver
        #     opts["driver"] = self._driver
        #     # Remaining options (extra)
        #     for key, value in params.items():
        #         opts[key] = value
        # # Compose command
        # machine_com = join_command(com, opts)
        # if node is not None:
        #     machine_com += ' ' + node
        # # Execute
        # self.do(machine_com)  # , no_output=True)
        # return machine_com
