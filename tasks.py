#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

import logging
from invoke import task
from cloudscale.commander.base import Basher
from cloudscale.commander.containers import Dockerizing
from cloudscale.commander.swarmer import Swarmer
from plumbum import colors

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


#####################################################
# TESTS with the Basher Class
@task
def themachine(node='pymachine', driver=None, token=None, slaves=1,
               image="nginx", start=4321, end=4322, port=80, extra=None):
    """ Launch openstack cluster + replicate docker image """

    if driver == 'virtualbox':
        node = driver + '-' + node
    # Get the machine which will hold ssh connection to the master/manager
    mach = Swarmer(driver, token=token).prepare(node)
####################
# TO FIX
    # # ATTACH VOLUME? # nova api?
####################
    # Join the swarm and be the MASTER
    mach.be_the_master()
    # Add slaves
    for j in range(1, slaves+1):
        mach.slave_factory(driver, num=j)
    # Check for info on swarm cluster
    mach.cluster_info()
    # Run the image requested across my current cluster
    mach.cluster_run(image, extra=extra,
                     internal_port=port, port_start=start, port_end=end)
    # CHECK: process list
    mach.swarming()
    # Close connection to master
    mach.exit()
    _logger.info("Completed")


#####################################################
# Clean up resources on docker engines
@task
def containers_reset(driver='openstack', skip_swarm=True):
    """ Remove PERMANENTLY all machine within a driver class """

    mach = Dockerizing(driver)
    # Find machines in list which are based on this driver
    for node in mach.list(with_driver=driver):
        # Clean containers inside those machines
        mach.prepare(node)
        mach.destroy_all(skip_swarm)
        mach.exit()
    _logger.info("Completed")


@task
def driver_reset(driver='openstack'):
    """ List all machine with a driver, and clean up their containers """

    mach = Dockerizing(driver)
    import time
    # Find machines in list which are based on this driver
    for node in mach.list(with_driver=driver):
        # REMOVE THEM!!
        _logger.warning("Removing machine '%s'!" % node)
        time.sleep(5)
        mach.remove(node)
    _logger.info("Done")


#####################################################
# SSH with Paramiko
@task
def remote_com(hosts='host', port=22, user='root', com='ls', path=None,
               pwd=None, kfile=None, timeout=5):
    """ Execute command to host via pythonic ssh (auth: passwork or key) """

    bash = Basher()
    for host in hosts.split(','):
        bash.remote(host=host, port=port, user=user,
                    pwd=pwd, kfile=kfile, timeout=timeout)
        bash.cd(path)
        bash.do(com)
        bash.exit()


#####################################################
# DOCKER MACHINE
@task
def machine_new(node="dev", driver='virtualbox'):
    """ A task to add a docker machine - on virtualbox """
    machine = Dockerizing(driver)

    # Check that the requested node does not already exist
    if node in machine.list():
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' Already exists" % node)
        return
    machine.create(node)

    # Create the machine
    _logger.info("Preparing machine", node)
    print(machine.create(node))
    _logger.info(colors.green | "Created!\n\n")


@task
def machine_rm(node="dev", driver='virtualbox'):
    """ A task to remove an existing machine - on virtualbox """
    machine = Dockerizing(driver)

    # Check that the requested node does not already exist
    if node not in machine.list():
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' does not exist" % node)
        return

    _logger.info(colors.bold | "Trying to remove '%s'" % node)
    print(machine.remove(node))
    _logger.info(colors.green | "Removed")
