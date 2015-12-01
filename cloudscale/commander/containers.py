#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Machinery on top of docker-machine binary """

from __future__ import division, print_function, absolute_import
from .. import myself, lic, DLEVEL, logging
from .machinery import TheMachine, colors
# from collections import OrderedDict

__author__ = myself
__copyright__ = myself
__license__ = lic
_logger = logging.getLogger(__name__)
_logger.setLevel(DLEVEL)

DOCKER_PORT = '2376'


#######################
class Dockerizing(TheMachine):

    _mycom = 'docker'

    def docker(self, operation='ps', service=None,
               labels={}, admin=False, wait=True):
        """ docker commands """

        # Start-up command
        com = self._mycom
        opts = {}
        # Compose command
        mycom = self.join_command(com, opts)
        mycom += ' ' + operation

        # Labels
        for key, value in labels.items():
            mycom += ' --label %s=%s' % (key, value)

        if service is not None:
            mycom += ' ' + service
        # Execute
        _logger.info(colors.yellow | "Docker command\t'%s'" % mycom.strip())
        return self.do(mycom, admin=admin, wait=wait)

    def ps(self, all=False, filters={}, extra=None):
        """ Recover the list of running names of current docker engine """
        ps = []
        opts = ''
        if all:
            opts = '-a'
        # docker ps -a -f label=test
        for key, value in filters.items():
            opts += ' -f ' + key + '=' + value
        com = 'ps'
        if extra is not None:
            com = extra + ' ' + com

        dlist = self.docker(operation=com, service=opts).strip().split("\n")

        if len(dlist) < 2:
            return ps
        # k = dlist[0].split().index('NAMES')
        del dlist[0]

        for row in dlist:
            tmp = row.split()
            ps.append(tmp[len(tmp)-1])
        return ps

    def exec_com_on_running(self, execcom='ls',
                            container='one', extra=None, tty=True):
        com = 'exec -i'
        if tty:
            com += 't'
        if extra is not None:
            com = extra + ' ' + com
        com += ' ' + container
        return self.docker(operation=com, service=execcom)

    def destroy(self, container):
        _logger.info("Destroy %s" % container)
        self.docker('stop', container)
        self.docker('rm', container)

    def destroy_running(self):
        for container in self.ps():
            self.destroy(container)

    def destroy_all(self, skip_swarm=False):
        for container in self.ps(all=True):
            if not (skip_swarm and 'swarm_' in container):
                self.destroy(container)

    ###########################################
    # ENGINE operations - normal mode
    def check_daemon(self, standard=False):
        status = 'running' in self.do('service docker status').strip()
        _logger.debug("Daemon running: '%s'" % status)
        return status

    def stop_daemon(self):
        if self.check_daemon():
            self.do('service docker stop', admin=True)
            _logger.info("Stopped docker engine")
            return True
        return False

    def daemon_up(self, name='unknown', port=DOCKER_PORT, skip_check=False):

        status = self.check_daemon() or not skip_check

        if not status:
            _logger.info("Starting standard daemon")
            self.do('service docker start', admin=True)

        return status
