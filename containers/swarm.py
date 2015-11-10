
"""

##########################
# OPENSTACK
docker-machine create --debug --driver openstack
--openstack-ssh-user ubuntu
--openstack-image-name ubuntu-trusty-server
--openstack-sec-groups default
--openstack-net-name mw-net
--openstack-floatingip-pool ext-net
--openstack-flavor-name m1.small
testmachine

##########################
# PURE SWARM
docker run swarm create
docker-machine create -d DRIVER \
        --swarm-discovery token://TOKEN \
        --swarm --swarm-master masterofp
docker-machine create -d DRIVER \
    --swarm --swarm-discovery token://TOKEN dnode01
eval $(docker-machine env --swarm swarm-master)


##########################
##########################
## ALTERNATIVE ##

# Docker Machine Setup
docker-machine create \
    -d virtualbox \
    swl-consul

docker $(docker-machine config swl-consul) run -d \
    -p "8500:8500" \
    -h "consul" \
    progrium/consul -server -bootstrap

docker-machine create \
    -d virtualbox \
    --virtualbox-disk-size 50000 \
    --swarm \
    --swarm-master \
    --swarm-discovery="consul://$(docker-machine ip swl-consul):8500" \
    --engine-opt="cluster-store=consul://$(docker-machine ip swl-consul):8500" \
    --engine-opt="cluster-advertise=eth1:0" \
    swl-demo0

docker-machine create \
    -d virtualbox \
    --virtualbox-disk-size 50000 \
    --swarm \
    --swarm-discovery="consul://$(docker-machine ip swl-consul):8500" \
    --engine-opt="cluster-store=consul://$(docker-machine ip swl-consul):8500" \
    --engine-opt="cluster-advertise=eth1:0" \
    swl-demo1
"""
