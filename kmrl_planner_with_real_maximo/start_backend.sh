#!/bin/bash
# KMRL Planner Backend Startup Script

echo "Starting KMRL Planner Backend..."

# Set environment variables if needed
# export DATABASE_URL="sqlite:///./kmrl_mock_maximo.db"

# Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
