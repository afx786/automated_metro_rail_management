x#!/bin/bash
# KMRL Planner Backend Startup Script

echo "Starting KMRL Planner Backend..."

# Set environment variables if needed
# export MAXIMO_URL="https://your-maximo-instance.com"
# export MAXIMO_USER="your-username"
# export MAXIMO_PASS="your-password"

# Start the server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload