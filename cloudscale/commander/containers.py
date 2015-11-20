#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Machinery on top of docker-machine binary """

from __future__ import division, print_function, absolute_import
from .. import myself, lic, DLEVEL, logging
# from .base import join_command, colors
from .machinery import TheMachine
# from collections import OrderedDict

__author__ = myself
__copyright__ = myself
__license__ = lic
_logger = logging.getLogger(__name__)
_logger.setLevel(DLEVEL)


#######################
class Dockerizing(TheMachine):

    _mycom = 'docker'

    def docker(self, operation='ps', service=None):
        """ docker commands """

        # Start-up command
        com = self._mycom
        opts = {}
        # Compose command
        mycom = self.join_command(com, opts)
        mycom += ' ' + operation
        if service is not None:
            mycom += ' ' + service
        # Execute
        _logger.debug("Docker command\t'%s'" % mycom)
        return self.do(mycom)  # , no_output=True)

    def ps(self):
        """ Recover the list of running names of current docker engine """
        ps = []
        dlist = self.docker().strip().split("\n")
        if len(dlist) < 2:
            return ps
        # k = dlist[0].split().index('NAMES')
        del dlist[0]

        for row in dlist:
            tmp = row.split()
            ps.append(tmp[len(tmp)-1])
        return ps

    def join(self, token, image_name='swarm_join'):
        """ Use my internal ip to join a swarm cluster """

        # Get the internal ip
        out = self.do('ifconfig eth0')
        internal_ip = out.split("\n")[1].split()[1].split(':')[1]
        _logger.info("Internal master ip is: '%s'" % internal_ip)

        # Check if already joined?
        ps = self.ps()
        if image_name not in ps:
            # Join the swarm
            options = '--addr=' + internal_ip + ':2375' + ' ' + \
                'token://' + token
            self.docker('run -d --name ' + image_name + ' swarm join', options)
