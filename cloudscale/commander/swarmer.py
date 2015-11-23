#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Machinery on top of docker-machine binary """

from __future__ import division, print_function, absolute_import
from .. import myself, lic, DLEVEL, logging

import time
from .containers import Dockerizing, colors

__author__ = myself
__copyright__ = myself
__license__ = lic
_logger = logging.getLogger(__name__)
_logger.setLevel(DLEVEL)

SWARM_PORT = '2375'
SWARM_MANAGER_PORT = '3333'
SWARM_ALL = '0.0.0.0'


#######################
class Swarmer(Dockerizing):
    """
    Use docker-swarm project to prepare a real cluster of containers
    across multiple virtual hosts launched with docker-machine.
    """

    _token = None
    _swarms = {}

    def __init__(self, driver='openstack', token=None):
        self.init_shell()
        self.cluster_prepare(token)
        super(Dockerizing, self).__init__(driver)

    def cluster_prepare(self, token):
        if token is None:
            token = self.docker('run --rm', 'swarm create').strip()
        _logger.info(colors.title |
                     "Ready to start the cluster with '%s'" % token)
        self._token = token
        return token

    def get_token(self):
        return 'token://' + self._token

    def cluster_info(self):
        """ Checks about current cluster """
        # List nodes
        self.docker('run --rm swarm list', self.get_token())
        # Current swarms
        _logger.debug("Currently available %s machines" % len(self._swarms))
        print(self._swarms)
        # Docker info on SWARM port
        _logger.debug("Wait for cluster connections")
        time.sleep(5)
        self.swarming('info')

    def cluster_join(self, change_did=True, name='master',
                     bind_port=False, image_name='swarm_join'):
        """ Use my internal ip to join a swarm cluster """

        if image_name in self.ps():
            return False

        _logger.debug("Pulling latest swarm")
        self.docker('pull', 'swarm')
        # Use ip from the LAN net
        myip = self.iip()
        # Put the daemon on Swarm port
        self.stop_daemon(slave=change_did)
        self.daemon_up(port=SWARM_PORT, skip_check=True, name=name)
        # Join the swarm token
        com = 'run -d --name ' + image_name
        if bind_port:
            com += ' -p ' + SWARM_PORT + ':' + SWARM_PORT
        com += ' swarm join'
        options = '--addr=' + myip + ':' + SWARM_PORT + ' ' + \
            self.get_token()
        return self.docker(com, options)

    def cluster_manage(self, image_name='swarm_manage'):
        """ Take leadership of a swarm cluster """

        if image_name in self.ps():
            return False

        com = 'run -d --name ' + image_name + \
            ' -p ' + SWARM_MANAGER_PORT + ':' + SWARM_PORT + ' swarm'
        opt = 'manage ' + self.get_token()
        out = self.docker(com, opt)
        return out

    def swarming(self, com='ps', opts=None):
        # From the manager you can use 0.0.0.0
        swarm = "-H tcp://" + SWARM_ALL + ":" + SWARM_MANAGER_PORT
        return self.docker(swarm + ' ' + com, service=opts)

# A method for swarm run?
    # def swarm_run(self, opts=None, name='noname000', check=False):
    #     if check and self.swarming(opts='')
    #     return self.swarming('run -d --name %s' % name, opts)
# A method for swarm run?

    def cluster_run(self, image, extra=None,
                    internal_port=80, port_start=80, port_end=80):
        """ Run a container image on a port range """
        dcount = 0
        for i in range(1, len(self._swarms)+1):
            for dport in range(port_start, port_end+1):
                dcount += 1
                # Create command
                name = image.replace('/', '-') + str(dcount).zfill(3)
                com = '-p %s:%s --name %s %s' \
                    % (dport, internal_port, name, image)
                if extra is not None:
                    com = extra + ' ' + com
                print(com)
                # Execute on cluster
                self.swarming('run -d', com)

    def be_the_master(self):
        # Join the swarm id
        self.cluster_join()
        # Take the leadership
        self.cluster_manage()
        # Add to available nodes
        self._swarms['master'] = self
        return self

    def slave_factory(self, num=1):
        name = 'pyswarm' + str(num).zfill(2)
        _logger.info(colors.title | "Working off slave '%s'" % name)
        # Create a new machine for a new slave
        current = Dockerizing(self._driver)
        current.create(name)
        current.connect(name)
        current.cluster_join(name='slaves')
        # SSH connection not needed anymore after join
        # Close it otherwhise the script would hang
        current.exit()
        self._swarms[name] = current
        return current

    def get_cluster(self):
        return self._swarms
