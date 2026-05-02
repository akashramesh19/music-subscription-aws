#!/bin/bash
set -e

APP_DIR="/home/ubuntu/app"

# Update system packages
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip

# Install Python dependencies
sudo pip3 install -r "$APP_DIR/requirements.txt"

# Run Flask app on port 80 (background, logs to /var/log/music-app.log)
sudo nohup python3 "$APP_DIR/app.py" > /var/log/music-app.log 2>&1 &

echo "App started on port 80. Logs at /var/log/music-app.log"
