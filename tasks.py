#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

import logging
from invoke import task
from cloudscale.commander.shell import Basher
from cloudscale.commander.containers import Dockerizing
from cloudscale.commander.swarmer import Swarmer, slave_factory
from plumbum import colors

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_path = 'data'
A_MACHINE = 'mymachine'


def read_list():
    """ Use a csv file to associate people to resources """
    import glob
    import csv

    slist = {}
    csvfile = glob.glob(_path + '/*.csv').pop()
    if csvfile is None:
        return slist

    hcsv = csv.reader(open(csvfile), delimiter=';')
    # Skip header
    next(hcsv)
    for line in hcsv:
        slist[line[3]] = {'name': line[2], 'surname': line[1]}
    return slist


@task
def com(driver='openstack', skipping='', com='ls /data'):
    """ Execute a command on all running containers of your swarm cluster """

    # Create machine
    mach = Dockerizing(driver)

    skips = []
    if skipping.strip() != '':
        skips = skipping.strip().split(',')
    print("But skip", skips)

    # Find machines in list which are based on this driver
    for node in mach.list(with_driver=driver):

        _logger.info("Working with node %s" % node)

        # Clean containers inside those machines
        mach.prepare(node)
        for container in mach.ps(filters={'label': 'swarm'}):
            do = True
            for skip in skips:
                if skip in container:
                    do = False
                    _logger.debug("Skip com on %s" % container)
                    break
            if do:
                _logger.info("Com on %s" % container)
                out = mach.exec_com_on_running(
                    container=container, tty=False, execcom=com)
                print("Obtained:", out)
        mach.exit()
    print("DONE")


@task
def themachine(node=A_MACHINE,
               driver=None, token=None, slaves=0, pw=False,
               image="nginx", start=4321, end=4321, port=80,
               onlycreate=False, extra=None):
    """ Launch openstack cluster + replicate docker image """

    slist = read_list()

    if driver == 'virtualbox':
        node = driver + '-' + node

# Should check for existing token before creating one.
# Can the token be found from a swarm manager? docker info/inspect?

    # Get the machine which will hold ssh connection to the master/manager
    mach = Swarmer(driver, token=token, node_name=node)

    ####################
    # ATTACH VOLUME? # nova api?
    ####################

    info = {}
    # Join the swarm and be the MASTER
    mach.be_the_master()
    x, y = mach.iam
    info[x] = y
    # Add slaves
    info = slave_factory(mach, driver=driver, info=info,
                         token=mach.get_token(True), slaves=slaves)

    # Check for info on swarm cluster
    _logger.info(mach.cluster_info().strip())

    if not onlycreate:
        # Run the image requested across my current cluster
        mach.cluster_run(image, data=slist, info=info, extra=extra, pw=pw,
                         internal_port=port, port_start=start, port_end=end)

    # # CHECK: process list
    # mach.swarming()

    # # Verify if everything is there again
    # missing = mach.cluster_health()
    # if len(missing) > 0:
    #     _logger.critical("Missing containers...")
    #     _logger.critical(missing)

    # Close connection to master
    mach.exit()
    _logger.info("Completed")


#####################################################
# Clean up resources on docker engines
@task
def containers_reset(driver='openstack', skipswarm=False):
    """ List all machine with a driver, and clean up their containers """

    mach = Dockerizing(driver)
    # Find machines in list which are based on this driver
    for node in mach.list(with_driver=driver):
        # Clean containers inside those machines
        mach.prepare(node)
        mach.destroy_all(skipswarm)
        mach.exit()
    _logger.info("Completed")


@task
def driver_reset(driver='openstack'):
    """ Remove PERMANENTLY all machine within a driver class """

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
    """ Execute command to host via pythonic ssh (auth: password or key) """

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
