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

    def docker(self, operation='ps', service=None, admin=False, wait=True):
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
        _logger.debug(colors.yellow | "Docker command\t'%s'" % mycom.strip())
        return self.do(mycom, admin=admin, wait=wait)  # , no_output=True)

    def ps(self, all=False):
        """ Recover the list of running names of current docker engine """
        ps = []
        opts = ''
        if all:
            opts = '-a'
        dlist = self.docker(service=opts).strip().split("\n")
        if len(dlist) < 2:
            return ps
        # k = dlist[0].split().index('NAMES')
        del dlist[0]

        for row in dlist:
            tmp = row.split()
            ps.append(tmp[len(tmp)-1])
        return ps

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
    # ENGINE operations
    def check_daemon(self, standard=False):
        status = False
        if standard:
            status = 'running' in self.do('service docker status').strip()
        else:
            status = self.do('docker ps', die_on_fail=False) is not False
        _logger.debug("Daemon running: '%s'" % status)
        return status

    def stop_daemon(self, slave=False):
        if self.check_daemon(standard=True):
            self.do('service docker stop', admin=True)
        else:
            if self.check_daemon(standard=False):
                self.do('killall docker', admin=True, die_on_fail=False)
        _logger.info("Stopped docker engine")

        if slave:
            # Being a replicated image/docker installation
            # there will be the same ID on each node for Swarm.
            # Understood it here: https://github.com/docker/swarm/issues/563
            self.do('rm /etc/docker/key.json', admin=True)
            _logger.debug("Removed original ID: becoming a new slave")

    def daemon_up(self, standard=False, name='unknown',
                  port=DOCKER_PORT, skip_check=False):
        status = self.check_daemon(standard) or not skip_check

        if standard:
            if not status:
                _logger.info("Starting standard daemon")
                self.do('service docker start', admin=True)
        else:
            if not status:
                ip = '0.0.0.0'
                tcp = '-H tcp://' + ip + ':' + port
                path = '/var/run/docker.sock'
                sock = '-H unix://' + path
                label = '--label name=' + name
                _logger.info("Starting docker daemon on port %s" % port)

# self.docker('daemon', tcp + ' ' + sock, admin=True, wait=False)
# Not working but solved with workaround:
                com = 'docker daemon %s %s %s' % (label, tcp, sock)
                self.remote_bg(com, admin=True)

        return status
