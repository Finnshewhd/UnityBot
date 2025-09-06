#!/bin/bash
echo "🚀 Starting UnityBot..."

# Optional: activate virtual environment (if exists)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies
pip install -r requirements.txt

# Start the bot
python3 UnityBot.py