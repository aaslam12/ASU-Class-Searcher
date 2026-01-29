#!/bin/bash

# Quick start script for ASU Class Searcher Bot
# This script activates the virtual environment and runs the bot

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"
BOT_DIR="$SCRIPT_DIR/Discord_Bot"

echo "🎓 ASU Class Searcher Bot"
echo "=========================="
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please run setup first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if token file exists
if [ ! -f "$BOT_DIR/token_disc.py" ]; then
    echo "❌ Bot token file not found: $BOT_DIR/token_disc.py"
    echo "Please create it with your Discord bot token:"
    echo "  echo \"TOKEN = 'your-token-here'\" > Discord_Bot/token_disc.py"
    exit 1
fi

# Activate virtual environment and run bot
echo "✓ Virtual environment found"
echo "✓ Bot token configured"
echo ""
echo "Starting bot..."
echo ""

source "$VENV_PATH/bin/activate"
cd "$BOT_DIR"
python main.py

# Deactivate on exit
deactivate
