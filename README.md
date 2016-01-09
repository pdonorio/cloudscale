
# Scaling Docker containers inside your cloud

## A little introduction

This project has born from the need to provide the same data analytics environment based on Python to a certain number of student of our training courses. We choosed for obviuosly reason Jupyter Notebooks as the centric technologies.

At some point we started using Docker as virtual environment to reproduce the training resources.
We created public Docker images to reproduce all Python libraries (Pydata: numpy, scipy, pandas, matplotlib, searborn, bokeh, cython) and/or Data analytics frameworks (Hadoop, Spark, Machine learning) behind a password protected Jupyter server.

But installing and using Docker on both our labs workstation and student laptops required quite a work, so we decided to spawn a Docker container on our new Openstack cloud for each student.

## The project

I tried to stay as generic as possible writing this code.

The main command is `themachine` which creates a certain number of virtual nodes on Openstack,
launch Docker on them, configure the engines to listen on a certain port, create a swarm cluster
and finally make the docker engines join the cluster, using the first node as the cluster master.

Moreover on this swarm cluster we automatically launch the same image for as many students as availabe in a CSV file,
providing at completion a table with one row per student, resource (host+port of the jupyter server) and password.

## Available commands

```bash

$ git clone https://github.com/pdonorio/cloudscale.git

$ cd cloudscale

$ invoke -l

Available tasks:

  com_containers     Execute a command on all running containers of your swarm cluster
  com_node           Execute a command on all running nodes of one driver
  containers_reset   List all machine with a driver, and clean up their containers
  driver_reset       Remove PERMANENTLY all machine within a driver class
  machine_new        A task to add a docker machine - on virtualbox
  machine_rm         A task to remove an existing machine - on virtualbox
  remote_com         Execute command to host via pythonic ssh (auth: password or key)
  themachine         Launch openstack cluster + replicate docker image

```

## The courses

Material used for courses is available on our [lecture dedicated repository](github.com/cineca-scai/lectures)

