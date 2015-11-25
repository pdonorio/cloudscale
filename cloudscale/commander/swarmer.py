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

    def __init__(self, driver='openstack',
                 token=None, node_name='swarm_master',
                 keys={}):
        # Get the shell ready
        super(Dockerizing, self).__init__(driver)
        # Prepare encryption or use the one existing
        self.set_cryptedp(**keys)
        # Create machine master and connect
        self.prepare(node_name)
        # Save the private token if any and create the swarm address
        self.cluster_prepare(token)

    def cluster_prepare(self, token):
        self._token = token
        if self._token is None:
            self._token = self.docker('run --rm', 'swarm create').strip()
        _logger.info(colors.title |
                     "Ready to start the cluster with '%s'" % self._token)
        return self._token

    def get_token(self, only_key=False):
        if only_key:
            return self._token
        return 'token://' + self._token

    def cluster_info(self):
        """ Checks about current cluster """
        # Current swarms
        _logger.warning("Currently available %s machines" % len(self._swarms))
        print(self._swarms)

        # Wait to make sure at least one node is connected
        _logger.critical("Waiting the cluster to have active nodes...")
        time.sleep(5)
        info = self.swarming('info')

        # # List nodes
        # dlist = self.docker('run --rm swarm list', self.get_token()).strip()
        # _logger.info(dlist)
        return info

    def cluster_join(self, change_did=True, name='uknown', label='master',
                     bind_port=False, image_name='swarm_join'):
        """ Use my internal ip to join a swarm cluster """

        # Add to current swarm list
        self._swarms[name] = self
        # Skip if already joined
        if image_name in self.ps():
            return False
        # Update swarm image?
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
        com += ' swarm --debug join'
        options = '--addr=' + myip + ':' + SWARM_PORT + ' ' \
            + ' --heartbeat=5s ' + self.get_token()
        return self.docker(com, options)

    def cluster_manage(self, image_name='swarm_manage'):
        """ Take leadership of a swarm cluster """

        if image_name in self.ps():
            return False

        com = 'run -d --name ' + image_name + \
            ' -p ' + SWARM_MANAGER_PORT + ':' + SWARM_PORT + ' swarm'
        opt = '--debug manage ' \
            + ' --heartbeat=5s ' + self.get_token()
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

    def cluster_run(self, image, extra=None, pw=False,
                    internal_port=80, port_start=80, port_end=80):
        """ Run a container image on a port range """
        dcount = 0
        containers = {}

        for i in range(1, len(self._swarms)+1):
            for dport in range(port_start, port_end+1):
                _logger.info("Run '%s' on port '%s'" % (image, dport))
                dcount += 1
                name = image.replace('/', '-') + str(dcount).zfill(3)
                # Create command
                com = '-p %s:%s --name %s %s' \
                    % (dport, internal_port, name, image)
                # Passw
                if pw:
                    pwd = self.get_salt(name, force=True, truncate=8)
                    com = '-e PASSWORD=' + pwd + ' ' + com
                # Other options
                if extra is not None:
                    com = extra + ' ' + com
                # Execute on cluster
                cid = self.swarming('run -d', com).strip()
                _logger.info("Executed...")
                # Save info
                containers[name] = {
                    'dhash': cid,
                    'port': dport,
                    'pwd': pwd,
                    'token': self.get_token(),
                    'ip': None,
                }
                _logger.info(containers)

        return containers

    def be_the_master(self):
        # Join the swarm id
        self.cluster_join(name='master')
        # Take the leadership
        self.cluster_manage()
        return self

    def get_cluster(self):
        return self._swarms


################################
def slave_factory(master_machine, driver='virtualbox', token=None, slaves=1):
    """ A factory for all the slave machine on the same driver """

    # Using same creadentials of the master!
    keys = master_machine.get_cryptedp()

    for j in range(1, slaves+1):
        name = 'pyswarm' + str(j).zfill(2)
        _logger.info(colors.title | "Working off slave '%s'" % name)
        # Create a new machine for a new slave
        current = Swarmer(driver, token=token, node_name=name, keys=keys)
        current.cluster_join(name=name, label='slave')
        # SSH connection not needed anymore after join
        # Close it otherwhise the script would hang
        current.exit()
