#!/bin/bash

if [ "$1" = "server" ]; then
    uvicorn app:app --host 0.0.0.0 --port 8000
elif [ "$1" = "worker" ]; then
    python worker.py
elif [ "$1" = "migrate" ]; then
    python manage.py migrate
else
    echo "Usage: docker-entrypoint.sh [server|worker|migrate]"
fi