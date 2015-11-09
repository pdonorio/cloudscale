
# Clean previous
docker stop host
docker rm host

# Build image
cd myssh
docker build -t myssh .
cd ..

# Launch machine with ssh server
docker run -d --name host myssh /sbin/my_init --enable-insecure-key

# Add a file to check if it works later
docker exec host touch /tmp/itworks

# Execute invoke task which makes use of paramiko and ssh insecure_key
docker run -it --link host:host -w /test -v $(pwd):/test \
    pdonorio/py3kbase invoke ssh
