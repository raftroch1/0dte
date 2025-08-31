# Enhanced 0DTE Strategy with Greeks

## Overview

This strategy addresses key insights from 0DTE options trading analysis:

### ✅ Key Improvements Implemented

1. **Slippage & Bid-Ask Spread Management**
   - Liquidity filtering with estimated spreads
   - Maximum 15% spread threshold
   - Volume and transaction-based scoring

2. **Gamma/Delta Sensitivity Analysis**
   - Real-time Greeks calculations using Black-Scholes
   - Delta filters (0.15 - 0.85 range)
   - Gamma risk thresholds for 0DTE protection

3. **Higher Confidence Thresholds**
   - 65-70% minimum confidence (vs previous 55%)
   - Market regime-specific thresholds
   - Greeks-based confidence adjustments

4. **Credit Spread Capabilities**
   - Market regime detection
   - Preference for credit spreads in high volatility
   - Delta-neutral strategies in low VIX conditions

5. **Machine Learning Readiness**
   - Comprehensive feature engineering
   - Target variable preparation
   - Multi-timeframe analysis support

## Usage

```python
from src.strategies.enhanced_0dte import Enhanced0DTEStrategy, Enhanced0DTEBacktester
from src.data import ParquetDataLoader

# Initialize
loader = ParquetDataLoader()
backtester = Enhanced0DTEBacktester(loader)

# Run backtest
results = backtester.run_enhanced_0dte_backtest(start_date, end_date)
```

## Configuration

See `config.py` for detailed parameter settings including:
- Confidence thresholds by market regime
- Greeks-based filters
- Liquidity requirements
- Risk management parameters

## Features

- **Greeks Integration**: Real-time Delta, Gamma, Theta, Vega calculations
- **Liquidity Scoring**: Estimated spreads and market impact analysis
- **Market Regime Detection**: Adaptive thresholds based on market conditions
- **Risk Management**: Position sizing with Greeks considerations
- **ML Features**: Ready for machine learning model integration
