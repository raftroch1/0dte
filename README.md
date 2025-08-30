
# 0DTE Options Trading System

A clean, minimalistic 0DTE (Zero Days to Expiration) options trading system designed to target $200-250 daily profit on a $35,000 account using Alpaca Markets integration.

## 🎯 System Overview

- **Target**: $200-250 daily profit
- **Account Size**: $35,000
- **Strategy**: Momentum-based 0DTE options trading
- **Broker**: Alpaca Markets (Paper Trading)
- **Risk Management**: 1% risk per trade, 2% max position size

## 📁 Architecture

```
0dte-trading-system/
├── src/
│   ├── main.ts              # Main entry point
│   ├── core/                # Core trading logic
│   │   ├── alpaca-integration.ts
│   │   └── backtesting-engine.ts
│   ├── strategies/          # Trading strategies
│   │   ├── adaptive-strategy-selector.ts
│   │   └── simple-momentum-strategy.ts
│   ├── data/                # Market data & analysis
│   │   ├── alpaca-historical-data.ts
│   │   ├── market-regime-detector.ts
│   │   ├── technical-indicators.ts
│   │   └── greeks-simulator.ts
│   ├── trading/             # Trade execution
│   │   ├── alpaca-paper-trading.ts
│   │   └── live-trading-connector.ts
│   └── utils/               # Utilities & types
│       └── types.ts
├── config/                  # Configuration
│   └── integration-config.ts
├── tests/                   # Tests
│   ├── test-alpaca-integration.ts
│   └── test-improved-system.ts
└── docs/                    # Documentation
    ├── README.md
    └── IMPLEMENTATION_SUMMARY.md
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone/navigate to the project
cd 0dte-trading-system

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env with your Alpaca credentials
nano .env
```

### 2. Configure Alpaca API

Get your API credentials from [Alpaca Markets](https://alpaca.markets/):
- Sign up for a paper trading account
- Generate API key and secret
- Update `.env` file with your credentials

### 3. Run the System

```bash
# Start paper trading
npm run paper

# Run backtest
npm run backtest

# Run tests
npm test

# Development mode (auto-restart)
npm run dev
```

## 📊 Usage Examples

### Paper Trading
```bash
# Start paper trading with default settings
npm start paper

# The system will:
# - Connect to Alpaca paper trading
# - Monitor SPY 0DTE options
# - Execute momentum-based trades
# - Target $225 daily profit
# - Stop at $500 daily loss
```

### Backtesting
```bash
# Run backtest for specific date range
npm start backtest 2024-01-01 2024-03-31

# View results in console output
```

### Testing
```bash
# Test Alpaca integration
npm test

# Run specific test
ts-node tests/test-alpaca-integration.ts
```

## ⚙️ Configuration

Key settings in `config/integration-config.ts`:

```typescript
const config = {
  trading: {
    accountSize: 35000,        // Account size
    dailyProfitTarget: 225,    // Daily profit target
    maxDailyLoss: 500,         // Max daily loss
    maxPositionSize: 0.02,     // 2% max position size
    riskPerTrade: 0.01         // 1% risk per trade
  }
};
```

## 🛡️ Risk Management

- **Position Sizing**: Maximum 2% of account per trade
- **Risk Per Trade**: 1% of account at risk
- **Daily Loss Limit**: $500 maximum daily loss
- **Profit Target**: $200-250 daily profit target
- **Time Limits**: Only trade 0DTE options (same day expiration)

## 📈 Strategy Details

### Momentum Strategy
- Monitors SPY 0DTE options
- Uses technical indicators (RSI, MACD, Bollinger Bands)
- Enters trades based on momentum signals
- Exits at profit targets or stop losses

### Market Regime Detection
- Identifies trending vs ranging markets
- Adjusts strategy parameters accordingly
- Reduces trading in uncertain conditions

## 🔧 Development

### Project Structure
- **Core**: Essential trading logic and integrations
- **Strategies**: Trading strategy implementations
- **Data**: Market data fetching and analysis
- **Trading**: Trade execution and paper trading
- **Utils**: Shared utilities and type definitions

### Adding New Strategies
1. Create strategy file in `src/strategies/`
2. Implement strategy interface
3. Add to strategy selector
4. Test with backtesting engine

## 📝 Logging

The system provides comprehensive logging:
- Trade entries and exits
- P&L tracking
- Risk management alerts
- System status updates

## ⚠️ Important Notes

- **Paper Trading Only**: This system is configured for paper trading
- **0DTE Focus**: Designed specifically for same-day expiration options
- **Risk Warning**: Options trading involves significant risk
- **Testing Required**: Always backtest before live trading

## 🤝 Support

For issues or questions:
1. Check the logs for error messages
2. Verify Alpaca API credentials
3. Ensure market hours for options trading
4. Review configuration settings

## 📄 License

MIT License - See LICENSE file for details.
