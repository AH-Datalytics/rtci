#!/bin/bash

# Set the source and destination paths
APP_DIR="."
DOCKER_TAG="rtci/chatbot"

# load DOCKER_REGISTRY from environment variable or command-line argument
if [[ "$1" == "--registry" && -n "$2" ]]; then
    DOCKER_REGISTRY="$2"
    shift 2
fi

# Check if 'clean' argument was passed
if [[ "$1" == "clean" ]]; then
    echo "Cleaning previous docker builds ..."
    docker system prune --all --force --volumes
fi

echo "Running docker build ..."
docker buildx build --platform linux/amd64 --tag $DOCKER_TAG "$APP_DIR"

echo "Pushing docker build ..."
docker tag $DOCKER_TAG "$DOCKER_REGISTRY/$DOCKER_TAG"
docker push "$DOCKER_REGISTRY/$DOCKER_TAG"