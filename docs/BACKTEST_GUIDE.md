# 🎯 Flyagonal Strategy - Backtest User Guide

## Overview

This guide provides complete instructions for running backtests of the Flyagonal options trading strategy with your own parameters, date ranges, and account balance.

## Quick Start

### Basic Usage
```bash
# Run with default settings (6 months, Alpaca balance)
node scripts/flyagonal-backtest-user.js

# Run with custom date range
node scripts/flyagonal-backtest-user.js 2024-01-01 2024-06-30

# Run with custom date range and balance
node scripts/flyagonal-backtest-user.js 2024-03-01 2024-08-31 25000
```

## Prerequisites

### 1. Environment Setup
Ensure you have Node.js installed and dependencies:
```bash
npm install axios
```

### 2. Alpaca Integration (Optional)
To use your real Alpaca account balance, create a `.env` file:
```bash
# .env file
ALPACA_API_KEY_ID=your_alpaca_key_id
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading (recommended)
# ALPACA_BASE_URL=https://api.alpaca.markets      # Live trading (use with caution)
```

**Note**: If no `.env` file is found, the system uses a default balance of $25,000.

## Command Line Options

### Syntax
```bash
node scripts/flyagonal-backtest-user.js [start-date] [end-date] [starting-balance]
```

### Parameters

| Parameter | Format | Description | Example |
|-----------|--------|-------------|---------|
| `start-date` | YYYY-MM-DD | Backtest start date | `2024-01-01` |
| `end-date` | YYYY-MM-DD | Backtest end date | `2024-06-30` |
| `starting-balance` | Number | Starting capital in USD | `50000` |

### Examples

#### 1. Default 6-Month Backtest
```bash
node scripts/flyagonal-backtest-user.js
```
- Uses last 6 months
- Fetches Alpaca balance automatically
- Generates comprehensive logs

#### 2. Custom Date Range
```bash
node scripts/flyagonal-backtest-user.js 2024-01-01 2024-03-31
```
- Tests Q1 2024 (3 months)
- Uses Alpaca balance
- Perfect for quarterly analysis

#### 3. Specific Period with Custom Balance
```bash
node scripts/flyagonal-backtest-user.js 2024-06-01 2024-08-31 100000
```
- Tests summer period (3 months)
- Uses $100,000 starting capital
- Ideal for scaling analysis

#### 4. Year-to-Date Analysis
```bash
node scripts/flyagonal-backtest-user.js 2024-01-01 2024-12-31
```
- Full year backtest
- Uses current Alpaca balance
- Comprehensive annual review

#### 5. Short-Term Testing
```bash
node scripts/flyagonal-backtest-user.js 2024-07-01 2024-07-31 10000
```
- Single month analysis
- Smaller account testing
- Quick validation

## Output Files

Each backtest run creates four detailed files in the `logs/` directory:

### 1. Comprehensive Report (`flyagonal_report_[dates].txt`)
**Most Important File** - Contains complete analysis:
- Executive summary with key metrics
- Trade performance statistics
- Risk analysis and drawdown details
- Strategy validation scores
- Detailed trade-by-trade log

### 2. CSV Export (`flyagonal_trades_[dates].csv`)
Spreadsheet-ready data with:
- Entry/exit dates and times
- Price levels and P&L
- VIX levels and win probabilities
- Perfect for Excel analysis

### 3. JSON Trade Log (`flyagonal_trades_[dates].json`)
Structured data including:
- Complete trade metadata
- Confidence scores
- Market regime information
- Programmatic analysis ready

### 4. System Log (`flyagonal_backtest_[dates].json`)
Technical execution log:
- System decisions and reasoning
- Market analysis details
- Error handling and warnings

## Understanding the Results

### Key Performance Metrics

#### Win Rate
- **Excellent**: 65%+ 
- **Good**: 55-65%
- **Needs Improvement**: <55%

#### Risk/Reward Ratio
- **Excellent**: 1.4:1+
- **Good**: 1.2-1.4:1
- **Needs Improvement**: <1.2:1

#### Maximum Drawdown
- **Excellent**: <10%
- **Good**: 10-20%
- **High Risk**: >20%

#### Profit Factor
- **Excellent**: 2.0+
- **Good**: 1.5-2.0
- **Needs Improvement**: <1.5

#### Sharpe Ratio
- **Excellent**: 2.0+
- **Good**: 1.0-2.0
- **Fair**: <1.0

### Sample Report Output
```
🎯 FLYAGONAL STRATEGY - COMPREHENSIVE BACKTEST REPORT
===================================================

📊 EXECUTIVE SUMMARY
===================
Period: 2024-03-01 to 2024-08-31 (184 days)
Starting Balance: $50,000
Ending Balance: $62,570
Total P&L: +$12,570
Total Return: +25.14%
Annualized Return: +50.28%
Max Drawdown: $1,536 (3.07%)
Sharpe Ratio: 2.73

🎯 TRADE PERFORMANCE
===================
Total Trades: 42
Winning Trades: 27 (64.3%)
Losing Trades: 15 (35.7%)
Average Win: $750
Average Loss: $513
Risk/Reward Ratio: 1.46:1
Profit Factor: 2.34
Best Trade: +$839
Worst Trade: -$593
Avg P&L per Trade: +$299

📈 TRADING ACTIVITY
==================
Trading Period: 6.0 months
Trades per Month: 7.0
Max Consecutive Wins: 6
Max Consecutive Losses: 4

⚠️ RISK ANALYSIS
================
Maximum Drawdown: 3.07% ($1,536)
Risk per Trade: $500
Target per Trade: $750
Risk as % of Balance: 1.00%
Sharpe Ratio: 2.73 (Excellent)

✅ STRATEGY VALIDATION
=====================
Win Rate: 64.3% ✅ Excellent
Risk/Reward: 1.46:1 ✅ Excellent
Profit Factor: 2.34 ✅ Excellent
Max Drawdown: 3.07% ✅ Excellent
```

## Advanced Usage

### Batch Testing Multiple Periods
Create a script to test multiple periods:

```bash
#!/bin/bash
# test-multiple-periods.sh

echo "Testing multiple periods..."

# Q1 2024
node scripts/flyagonal-backtest-user.js 2024-01-01 2024-03-31 50000

# Q2 2024
node scripts/flyagonal-backtest-user.js 2024-04-01 2024-06-30 50000

# Q3 2024
node scripts/flyagonal-backtest-user.js 2024-07-01 2024-09-30 50000

echo "All tests complete. Check logs/ directory for results."
```

### Different Market Conditions
Test various market environments:

```bash
# Bull market period
node scripts/flyagonal-backtest-user.js 2023-01-01 2023-06-30

# Bear market period  
node scripts/flyagonal-backtest-user.js 2022-01-01 2022-06-30

# Volatile period
node scripts/flyagonal-backtest-user.js 2020-03-01 2020-09-30
```

### Account Size Analysis
Test different account sizes:

```bash
# Small account
node scripts/flyagonal-backtest-user.js 2024-01-01 2024-06-30 10000

# Medium account
node scripts/flyagonal-backtest-user.js 2024-01-01 2024-06-30 50000

# Large account
node scripts/flyagonal-backtest-user.js 2024-01-01 2024-06-30 250000
```

## Troubleshooting

### Common Issues

#### 1. "Cannot find module 'axios'"
```bash
npm install axios
```

#### 2. "No .env file found"
This is normal if you haven't set up Alpaca integration. The system will use default balance.

#### 3. "VIX fetch failed"
The system automatically falls back to VIX estimation. This doesn't affect backtest quality.

#### 4. "Alpaca balance fetch failed"
Check your `.env` file credentials. The system will use default balance as fallback.

### Performance Tips

1. **Use realistic date ranges**: Avoid periods longer than 2 years for faster execution
2. **Weekend handling**: The system automatically skips weekends
3. **File management**: Old log files are not automatically deleted

## Integration with Trading Systems

### Paper Trading Preparation
Use backtest results to configure paper trading:

1. Validate win rate expectations (target 60-70%)
2. Confirm risk management parameters
3. Set appropriate position sizing
4. Establish drawdown limits

### Live Trading Considerations
Before live deployment:

1. Run multiple period backtests
2. Validate across different market conditions
3. Confirm account size appropriateness
4. Test with paper trading first

## File Management

### Log Directory Structure
```
logs/
├── flyagonal_backtest_2024-01-01_to_2024-06-30.json
├── flyagonal_trades_2024-01-01_to_2024-06-30.json
├── flyagonal_trades_2024-01-01_to_2024-06-30.csv
├── flyagonal_report_2024-01-01_to_2024-06-30.txt
└── [additional backtest files...]
```

### Cleanup Commands
```bash
# Remove old logs (be careful!)
rm logs/flyagonal_*

# Archive logs by date
mkdir -p logs/archive/2024
mv logs/flyagonal_*2024* logs/archive/2024/
```

## Support and Validation

### Strategy Validation Checklist
- [ ] Win rate between 60-75%
- [ ] Risk/reward ratio above 1.3:1
- [ ] Maximum drawdown below 15%
- [ ] Profit factor above 1.5
- [ ] Consistent performance across periods

### Getting Help
1. Check the comprehensive report file first
2. Verify your command line parameters
3. Ensure proper date format (YYYY-MM-DD)
4. Review the system log for technical details

---

## 🎯 Ready to Start?

Run your first backtest:
```bash
node scripts/flyagonal-backtest-user.js
```

The system will guide you through the process and create detailed reports for analysis!
