# 🚀 Getting Started with Your 0DTE Trading System

## ✅ System Status: READY TO USE!

Your 0DTE options trading system is fully functional and tested. Here's how to get started:

## 📋 What's Working

✅ **Core System**: All components are functional  
✅ **Configuration**: Strategy and account settings loaded  
✅ **Technical Analysis**: RSI, MACD, Bollinger Bands working  
✅ **Market Regime Detection**: Bullish/Bearish/Neutral detection  
✅ **Strategy Selection**: Adaptive 0DTE strategy selection  
✅ **Paper Trading**: Virtual trading simulation  
✅ **Backtesting**: Historical strategy testing  
✅ **Risk Management**: Position sizing and stop losses  

## 🔑 Step 1: Get Alpaca API Credentials

1. Go to [Alpaca Markets](https://alpaca.markets/)
2. Sign up for a **Paper Trading Account** (free)
3. Navigate to **API Keys** in your dashboard
4. Generate new API Key and Secret
5. **Important**: Start with Paper Trading, NOT live trading

## ⚙️ Step 2: Configure Environment

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` file with your credentials:
```bash
# Replace with your actual credentials
ALPACA_API_KEY=your_actual_api_key_here
ALPACA_API_SECRET=your_actual_api_secret_here

# Keep these for paper trading
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets
```

## 🎯 Step 3: Test Real Connectivity

Once you have real credentials, test the connection:

```bash
# Test with real API credentials
node -e "
const { AlpacaIntegration } = require('./src/core/alpaca-integration');
const alpaca = new AlpacaIntegration({
  apiKey: process.env.ALPACA_API_KEY,
  apiSecret: process.env.ALPACA_API_SECRET,
  isPaper: true
});
alpaca.testConnection().then(result => 
  console.log('Connection:', result ? '✅ SUCCESS' : '❌ FAILED')
);
"
```

## 📊 Step 4: Run Your First Backtest

Test your strategy on historical data:

```bash
# Run backtest for January 2024
npm run backtest 2024-01-01 2024-01-31
```

This will:
- Fetch real SPY historical data from Alpaca
- Generate realistic 0DTE options chains
- Test your momentum strategy
- Show detailed performance metrics

## 🎮 Step 5: Start Paper Trading

Begin live paper trading:

```bash
# Start paper trading (safe, no real money)
npm run paper
```

This will:
- Connect to live market data
- Monitor SPY 0DTE options in real-time
- Execute trades in paper trading mode
- Target $225 daily profit on $35k account

## 📈 Understanding Your Strategy

### **Default 0DTE Momentum Strategy**
- **Target**: $200-250 daily profit
- **Account**: $35,000
- **Risk**: 2% per trade, 1% account risk
- **Max Positions**: 3 concurrent
- **Stop Loss**: 30%
- **Profit Target**: 50%
- **Max Hold**: 4 hours
- **Exit Before**: 30 minutes to expiration

### **How It Works**
1. **Market Regime Detection**: Identifies bullish/bearish/neutral conditions
2. **Technical Analysis**: Uses RSI, MACD, Bollinger Bands
3. **Strategy Selection**: Chooses best approach for current conditions
4. **Risk Management**: Automatic position sizing and stop losses
5. **Time Management**: Exits before dangerous time decay

## 🛡️ Safety Features

- **Paper Trading First**: Always test before live trading
- **Daily Loss Limits**: Stops at $500 daily loss
- **Position Limits**: Maximum 3 positions at once
- **Time Decay Protection**: Exits 30 minutes before expiration
- **Market Hours Only**: Only trades during market hours

## 📊 Monitoring Your Performance

The system tracks:
- **Real-time P&L**: Unrealized and realized profits/losses
- **Win Rate**: Percentage of profitable trades
- **Risk Metrics**: Sharpe ratio, maximum drawdown
- **Greeks Exposure**: Delta, gamma, theta monitoring
- **Trade Quality**: Entry/exit timing analysis

## 🚨 Important Reminders

1. **Start with Paper Trading**: Never use real money until thoroughly tested
2. **Understand 0DTE Risks**: Same-day expiration options decay rapidly
3. **Monitor Closely**: 0DTE trading requires active management
4. **Market Conditions**: System works best in normal volatility (VIX 10-50)
5. **Commission Costs**: Factor in $0.65 per contract in real trading

## 🆘 Troubleshooting

### Connection Issues
- Verify API credentials are correct
- Check if Alpaca account is approved for options trading
- Ensure you're using paper trading URLs initially

### No Signals Generated
- Check if market is open (9:30 AM - 4:00 PM ET)
- Verify VIX is in acceptable range (10-50)
- Ensure sufficient options liquidity

### Performance Issues
- Monitor during active market hours
- Adjust strategy parameters if needed
- Review daily metrics for optimization opportunities

## 📞 Next Steps

1. **Get API credentials** from Alpaca
2. **Configure .env** with your keys
3. **Test connectivity** with real credentials
4. **Run backtests** to understand performance
5. **Start paper trading** to see live operation
6. **Monitor and optimize** based on results

## 🎯 Success Metrics

Target these metrics for successful operation:
- **Daily Profit**: $200-250 (0.57-0.71% of account)
- **Win Rate**: 60-70%
- **Max Drawdown**: <20%
- **Sharpe Ratio**: >2.0
- **Risk per Trade**: 1-2% of account

---

**Remember**: This system is designed for educational purposes and paper trading. Options trading involves substantial risk. Always trade responsibly and within your risk tolerance.

**Good luck with your 0DTE trading journey! 🚀**
