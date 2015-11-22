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

SWARM_PORT = '2375'
DOCKER_PORT = '2376'
SWARM_MANAGER_PORT = '3333'


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
        _logger.debug("Docker command\t'%s'" % mycom)
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

    def destroy_all(self):
        for container in self.ps(all=True):
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

    def stop_daemon(self):
        if self.check_daemon(standard=True):
            self.do('service docker stop', admin=True)
        else:
            if self.check_daemon(standard=False):
                self.do('killall docker', admin=True, die_on_fail=False)
        _logger.info("Stopped docker engine")

    def daemon_up(self, standard=False, port=DOCKER_PORT, skip_check=False):
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
                _logger.info("Starting docker daemon on port %s" % port)

# Not working but solved with workaround
# self.docker('daemon', tcp + ' ' + sock, admin=True, wait=False)

                com = 'docker daemon ' + tcp + ' ' + sock
                self.remote_bg(com, admin=True)

    ###########################################
    # SWARM CLUSTERS

# IF I WANT TO REFACTOR
    # def swarm_com(self, token, com, opts={}):
    #     pass

    # def swarm(self, token, com, opts={}):
    #     pass
# IF I WANT TO REFACTOR

    def clus(self, token):

        # Docker info on SWARM port
        self.swarm_run('info')

        # List nodes
        com = 'run --rm swarm list'
        opt = 'token://' + token
        self.docker(com, opt)

    def join(self, token, bind_port=False, image_name='swarm_join'):
        """ Use my internal ip to join a swarm cluster """

        if image_name in self.ps():
            return False

        # Use ip from the LAN net
        internal_ip = self.iip()

        # Put the daemon on Swarm port
        self.stop_daemon()
        self.daemon_up(port=SWARM_PORT, skip_check=True)

        # Join the swarm
        com = 'run -d --name ' + image_name
        if bind_port:
            com += ' -p ' + SWARM_PORT + ':' + SWARM_PORT
        com += ' swarm join'
        options = '--addr=' + internal_ip + ':' + SWARM_PORT + ' ' + \
            'token://' + token
        return self.docker(com, options)

    def manage(self, token, image_name='swarm_manage'):
        """ Take leadership of a swarm cluster """

        if image_name in self.ps():
            return False

        com = 'run -d --name ' + image_name + \
            ' -p ' + SWARM_MANAGER_PORT + ':' + SWARM_PORT + ' swarm'
        opt = 'manage token://' + token
        out = self.docker(com, opt)
        return out

    def swarm_run(self, com='ps'):

        # From the manager you can you 0.0.0.0
        ip = '0.0.0.0'
        # ip = self._eip
        # if self._driver != 'virtualbox':
        #     ip = self.iip()

        opt = "-H tcp://" + ip + ":" + SWARM_MANAGER_PORT
        return self.docker(opt, com)
