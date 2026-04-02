#!/bin/bash

container="$1"

# only kill if the container is still running
if docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null | grep -q true; then
    echo "killing running container: $container"
    docker kill "$container"
fi

# remove the container if it exists
docker rm "$container" 2>/dev/null

# remove the image to force rebuild with latest code
docker rmi "$container" 2>/dev/null

# prune dangling images to prevent disk bloat
docker image prune -f 2>/dev/null
