#!/bin/bash

container="$1"

docker kill "$container"
docker rm "$container"

docker rmi "$container"

docker compose down