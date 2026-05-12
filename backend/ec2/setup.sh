#!/bin/bash
set -e

APP_DIR="/home/ubuntu/app"

sudo apt-get update -y
sudo apt-get install -y python3 python3-pip

sudo pip3 install -r "$APP_DIR/requirements.txt"

sudo nohup python3 "$APP_DIR/app.py" > /var/log/music-app.log 2>&1 &

echo "App started on port 80. Logs at /var/log/music-app.log"
