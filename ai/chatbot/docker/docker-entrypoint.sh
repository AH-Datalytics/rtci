#!/bin/bash

# Start fastapi application, prefect service
fastapi run "/app/main.py" --proxy-headers --port 8000 

# Wait for any process to exit
sleep 1m
wait -n

# Exit with status of process that exited first
exit $?
