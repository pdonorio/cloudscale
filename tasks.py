#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

import logging
from invoke import task
from cloudscale.commander.base import Basher
from cloudscale.commander.containers import Dockerizing
from plumbum import colors

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


#####################################################
# TESTS with the Basher Class
@task
def themachine(node='pymachine', driver=None, token=None, slaves=1,
               image="nginx", start=4321, end=4322, port=80, extra=None):
    """ Launch openstack cluster + replicate docker image """

    swarms = {}
    if driver == 'virtualbox':
        node = driver + '-' + node

    mach = Dockerizing(driver)
    # Does not recreate if already existing
    mach.create(node)
    mach.connect(node)

    #########################
    # ATTACH VOLUME?
    # nova api?

    #########################
    # SWARM!

    # Create
    if token is None:
        token = mach.docker('run --rm', 'swarm create').strip()
    _logger.info(colors.title | "Ready to start the cluster with '%s'" % token)
    # Join the swarm id
    mach.join(token)
    # Take the leadership
    mach.manage(token)
    swarms['master'] = mach
    # Add slaves
    for j in range(1, slaves+1):
        name = 'pyswarm' + str(j).zfill(2)
        _logger.info(colors.title | "Working off slave '%s'" % name)
        current = Dockerizing(driver)
        swarms[name] = current
        current.create(name)
        current.connect(name)
        current.join(token, name='slaves')
        # SSH connection not needed anymore after join
        current.exit()

    # Current swarms
    nodes = len(swarms)
    _logger.debug("Currently available %s nodes" % nodes)
    print(swarms)
    # Check for info on swarm cluster
    _logger.debug("Wait for cluster connections")
    import time
    time.sleep(10)
    mach.clus(token)

# TO FIX: separate function in containers
    # Run a docker image on the cluster
    counter = 0
    for i in range(1, nodes+1):
        for dport in range(start, end+1):
            counter += 1
            name = image.replace('/', '-') + str(counter).zfill(3)
            com = '-p %s:%s --name %s %s' % (dport, port, name, image)
            if extra is not None:
                com = extra + ' ' + com
            print(com)
            mach.swarming('run -d', com)

    ################################
    mach.swarming()
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
        mach.create(node)
        mach.connect(node)
        mach.destroy_all(skip_swarm)
        mach.exit()
    _logger.info("Completed")


@task
def driver_reset(driver='openstack'):
    """ List all machine with a driver, and clean up their containers """

    mach = Dockerizing(driver)
    # Find machines in list which are based on this driver
    for node in mach.list(with_driver=driver):
        # REMOVE THEM!!
        _logger.warning("Removing machine '%s'!" % node)
        import time
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
