#!/bin/bash
# 🚀 PAPER TRADING LAUNCHER
# =========================
# Loads environment variables and starts paper trading

echo "🚀 DYNAMIC RISK PAPER TRADING LAUNCHER"
echo "======================================"

# Load environment variables
if [ -f .env ]; then
    echo "📋 Loading environment from .env..."
    set -a
    source .env
    set +a
    echo "✅ Environment loaded"
else
    echo "❌ .env file not found"
    exit 1
fi

# Check if Alpaca SDK is installed
echo "🔍 Checking Alpaca SDK..."
if python -c "import alpaca.trading.client" 2>/dev/null; then
    echo "✅ Alpaca SDK available"
else
    echo "⚠️  Alpaca SDK not installed"
    echo "📦 Installing Alpaca SDK..."
    pip install alpaca-py
fi

# Check market status
current_time=$(date +%H%M)
current_day=$(date +%u)  # 1=Monday, 7=Sunday

echo "🕐 Current time: $(date)"

if [ "$current_day" -gt 5 ]; then
    echo "📅 Weekend - Market closed"
    echo "💡 Paper trader will wait for market hours"
elif [ "$current_time" -lt 0930 ] || [ "$current_time" -gt 1600 ]; then
    echo "🌙 Outside market hours (9:30 AM - 4:00 PM ET)"
    echo "💡 Paper trader will wait for market hours"
else
    echo "🔔 Market is open!"
fi

echo ""
echo "🎯 Starting Dynamic Risk Paper Trading..."
echo "   (Press Ctrl+C to stop)"
echo ""

# Start paper trading
python src/trading/demo_paper_trading.py
