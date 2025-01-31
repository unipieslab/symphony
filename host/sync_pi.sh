#!/bin/bash
while true; do
    rsync -avz --exclude 'venv/' --exclude 'state' --exclude 'results' --exclude 'logs' --exclude '__pycache' --delete ./ pi@192.168.201.225:/home/pi/symphony/host/

    sleep 1
done
