
# Comprehensive Alpaca Integration for 0DTE Options Trading

A complete TypeScript implementation for 0DTE (Zero Days to Expiration) options trading using Alpaca's API, targeting $200-250 daily profit on a $35,000 account.

## 🎯 Overview

This system provides a comprehensive solution for algorithmic options trading with:

- **Alpaca API Integration**: Full REST and WebSocket support for market data and trading
- **Greeks Simulation**: Black-Scholes model with realistic options pricing and Greeks calculation
- **Paper Trading Engine**: Complete simulation environment with P&L tracking and risk management
- **Backtesting Framework**: Historical strategy testing with detailed performance metrics
- **Live Trading Connector**: Real-time trading with adaptive strategies and risk controls
- **0DTE Optimization**: Specialized for same-day expiration options trading

## 🏗️ Architecture

### Core Components

1. **AlpacaIntegration** (`alpaca-integration.ts`)
   - REST API client with rate limiting
   - WebSocket streaming for real-time data
   - Options contract management
   - Order execution and position tracking

2. **GreeksSimulator** (`greeks-simulator.ts`)
   - Black-Scholes options pricing model
   - Real-time Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
   - Implied volatility calculation
   - 0DTE-specific metrics (time decay, gamma risk, probability ITM)

3. **AlpacaPaperTrading** (`alpaca-paper-trading_improved.ts`)
   - Virtual trading environment
   - Realistic fill simulation with bid-ask spreads and slippage
   - Portfolio tracking and P&L calculation
   - Risk management and position sizing

4. **BacktestingEngine** (`backtesting-engine.ts`)
   - Historical data replay
   - Strategy performance analysis
   - Risk metrics calculation
   - Trade logging and reporting

5. **LiveTradingConnector** (`live-trading-connector.ts`)
   - Real-time strategy execution
   - Risk management and position monitoring
   - Market regime detection
   - Automated trade execution

6. **IntegrationConfig** (`integration-config.ts`)
   - Pre-configured strategies for different risk profiles
   - Account size-based recommendations
   - Validation and configuration management

## 🚀 Quick Start

### Prerequisites

```bash
npm install axios ws mathjs @types/node @types/ws uuid @types/uuid
```

### Environment Setup

Create a `.env` file with your Alpaca credentials:

```env
ALPACA_API_KEY=your_api_key_here
ALPACA_API_SECRET=your_api_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # For paper trading
```

### Basic Usage

```typescript
import { AlpacaIntegration } from './alpaca-integration';
import { IntegrationConfig } from './integration-config';

// Initialize Alpaca client
const alpaca = new AlpacaIntegration({
  apiKey: process.env.ALPACA_API_KEY!,
  apiSecret: process.env.ALPACA_API_SECRET!,
  isPaper: true
});

// Test connection
const connected = await alpaca.testConnection();
console.log(`Connected: ${connected}`);

// Get 0DTE SPY options
const today = new Date().toISOString().split('T')[0];
const contracts = await alpaca.getOptionContracts('SPY', today);
console.log(`Available contracts: ${contracts.length}`);
```

## 📊 Strategy Configuration

### Default 0DTE Strategy (Optimized for $35k Account)

```typescript
const strategy = IntegrationConfig.getDefault0DTEStrategy();
// - 2% position size per trade
// - Maximum 3 concurrent positions
// - 30% stop loss, 50% profit target
// - $225 daily profit target
// - 4-hour maximum hold time
```

### Strategy Variants

- **Conservative**: Lower risk, smaller positions, tighter stops
- **Aggressive**: Higher risk, larger positions, wider stops
- **Morning Momentum**: Optimized for morning market moves
- **Afternoon Mean Reversion**: Optimized for afternoon consolidation
- **Scalping**: Quick trades with tight profit targets

## 🧮 Greeks Calculation Example

```typescript
import { GreeksSimulator } from './greeks-simulator';

const inputs = {
  underlyingPrice: 450,
  strikePrice: 450,
  timeToExpiration: GreeksSimulator.hoursToYears(4), // 4 hours to expiration
  riskFreeRate: 0.05,
  volatility: 0.25,
  optionType: 'call' as const
};

const result = GreeksSimulator.calculateOptionPrice(inputs);
console.log(`Price: $${result.theoreticalPrice.toFixed(2)}`);
console.log(`Delta: ${result.delta.toFixed(4)}`);
console.log(`Theta: $${result.theta.toFixed(2)} per day`);

// 0DTE specific metrics
const zdteMetrics = GreeksSimulator.calculate0DTEMetrics(inputs);
console.log(`Time decay per minute: $${zdteMetrics.timeDecayRate.toFixed(4)}`);
console.log(`Probability ITM: ${(zdteMetrics.probabilityITM * 100).toFixed(1)}%`);
```

## 📈 Paper Trading Example

```typescript
import { AlpacaPaperTrading } from './alpaca-paper-trading_improved';
import { IntegrationConfig } from './integration-config';

const paperTrading = new AlpacaPaperTrading(
  IntegrationConfig.getPaperTradingConfig()
);

// Place a market order
const order = await paperTrading.submitOrder({
  symbol: 'SPY240830C00450000',
  side: 'BUY',
  quantity: 2,
  orderType: 'MARKET'
});

// Check account metrics
const metrics = paperTrading.getAccountMetrics();
console.log(`Total P&L: $${metrics.totalPnL.toFixed(2)}`);
console.log(`Win Rate: ${(metrics.winRate * 100).toFixed(1)}%`);
```

## 🔄 Backtesting Example

```typescript
import { BacktestingEngine } from './backtesting-engine';
import { IntegrationConfig } from './integration-config';

const backtest = new BacktestingEngine(
  IntegrationConfig.createBacktestConfig(
    new Date('2024-01-01'),
    new Date('2024-01-31'),
    'default',
    'SPY'
  ),
  alpacaClient
);

// Load historical data
await backtest.loadHistoricalData();

// Define strategy function
const strategy = (data, options) => {
  // Your strategy logic here
  // Return TradeSignal or null
};

// Run backtest
const results = await backtest.runBacktest(strategy);
console.log(`Total Return: ${results.summary.totalReturnPercent.toFixed(2)}%`);
console.log(`Sharpe Ratio: ${results.summary.sharpeRatio.toFixed(2)}`);
```

## 🔴 Live Trading Example

```typescript
import { LiveTradingConnector } from './live-trading-connector';
import { IntegrationConfig } from './integration-config';

const liveTrading = new LiveTradingConnector(
  IntegrationConfig.getLiveTradingConfig(
    process.env.ALPACA_API_KEY!,
    process.env.ALPACA_API_SECRET!,
    true // Paper trading mode
  )
);

// Set up event handlers
liveTrading.on('trade_update', (update) => {
  console.log('Trade update:', update);
});

liveTrading.on('risk_violation', ({ level, riskCheck }) => {
  console.log(`Risk violation (${level}):`, riskCheck.violations);
});

// Start live trading
await liveTrading.start();
```

## ⚠️ Risk Management

### Built-in Risk Controls

- **Daily Loss Limits**: Automatic trading halt at $500 daily loss
- **Position Sizing**: Maximum 2% account risk per trade
- **Time Decay Protection**: Automatic exit 30 minutes before expiration
- **Maximum Positions**: Limit of 3 concurrent positions
- **Greeks Monitoring**: Real-time portfolio Greeks tracking

### Risk Metrics

- **Value at Risk (VaR)**: Portfolio risk estimation
- **Maximum Drawdown**: Peak-to-trough loss tracking
- **Sharpe Ratio**: Risk-adjusted return measurement
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss

## 📊 Performance Targets

### $35,000 Account Targets

- **Daily Profit Target**: $200-250 (0.57-0.71% of account)
- **Daily Loss Limit**: $500 (1.43% of account)
- **Monthly Target**: $4,500-5,500 (12.9-15.7% monthly return)
- **Maximum Drawdown**: 20% of account value
- **Target Win Rate**: 60-70%

## 🧪 Testing

Run the comprehensive test suite:

```bash
npx ts-node test-alpaca-integration.ts
```

Run individual examples:

```bash
npx ts-node example-usage.ts
```

## 📁 File Structure

```
├── alpaca-integration.ts           # Core Alpaca API client
├── greeks-simulator.ts            # Options pricing and Greeks
├── alpaca-paper-trading_improved.ts # Paper trading engine
├── backtesting-engine.ts          # Historical testing framework
├── live-trading-connector.ts      # Real-time trading system
├── integration-config.ts          # Configuration management
├── enhanced-types.ts              # TypeScript type definitions
├── test-alpaca-integration.ts     # Comprehensive test suite
├── example-usage.ts               # Usage examples
└── README.md                      # This file
```

## 🔧 Configuration Options

### Strategy Parameters

- `positionSizePercent`: Risk per trade (1-3%)
- `maxPositions`: Maximum concurrent positions (1-5)
- `stopLossPercent`: Stop loss threshold (20-40%)
- `takeProfitPercent`: Profit target (30-75%)
- `maxHoldingTimeMinutes`: Maximum position hold time (30-300 minutes)
- `timeDecayExitMinutes`: Exit time before expiration (15-60 minutes)

### Risk Management

- `maxDailyLoss`: Daily loss limit ($300-750)
- `dailyProfitTarget`: Daily profit target ($150-300)
- `vixFilterMax`: Maximum VIX for trading (35-60)
- `momentumThreshold`: Minimum momentum for entry (0.3-0.8)

## 🚨 Important Notes

1. **Paper Trading First**: Always test strategies in paper trading mode before live trading
2. **Risk Management**: Never risk more than you can afford to lose
3. **Market Hours**: 0DTE options are only available during market hours
4. **Liquidity**: Ensure sufficient option volume and open interest
5. **Commissions**: Factor in $0.65 per contract commission in calculations

## 📈 Performance Monitoring

The system provides comprehensive performance tracking:

- Real-time P&L monitoring
- Greeks exposure tracking
- Risk metric calculation
- Trade execution quality analysis
- Strategy performance attribution

## 🤝 Contributing

This is a comprehensive trading system designed for educational and research purposes. Always:

1. Test thoroughly in paper trading mode
2. Understand the risks involved in options trading
3. Comply with all applicable regulations
4. Consider consulting with financial professionals

## 📄 License

This project is for educational purposes. Trading involves substantial risk and is not suitable for all investors.

## ⚡ Quick Commands

```bash
# Install dependencies
npm install

# Run tests
npx ts-node test-alpaca-integration.ts

# Run examples
npx ts-node example-usage.ts

# Compile TypeScript
npx tsc

# Start paper trading simulation
npx ts-node -e "
import { runAllExamples } from './example-usage';
runAllExamples();
"
```

---

**Disclaimer**: This software is for educational purposes only. Options trading involves substantial risk and is not suitable for all investors. Past performance does not guarantee future results. Always trade responsibly and within your risk tolerance.
