# 🎯 Flyagonal Trading Strategy

## 📋 Overview

Call Broken Wing Butterfly (profits from rising markets + falling volatility) + Put Diagonal Spread (profits from falling markets + rising volatility)

This strategy is designed for **0DTE (Zero Days to Expiration) options trading** and focuses on short-term momentum opportunities. It uses vix to identify optimal entry and exit points for short-term options positions.

## 🎯 Strategy Details

- **Strategy Type**: volatility_balanced
- **Market Conditions**: volatile
- **Risk Level**: low
- **Timeframe**: 1hr
- **Minimum Account Size**: $25000
- **Complexity Level**: INTERMEDIATE

## 🧠 Algorithm Logic

### Entry Conditions

The strategy generates **BUY CALL** signals when:
- RSI indicates oversold conditions (< 30)
- MACD shows bullish crossover
- Price is above short-term moving average

The strategy generates **BUY PUT** signals when:
- RSI indicates overbought conditions (> 70)
- MACD shows bearish crossover
- Price is below short-term moving average

### Exit Conditions

Positions are closed when:
- **Take Profit**: 100% gain on premium
- **Stop Loss**: 50% loss on premium
- **Time Exit**: 30 minutes before expiration

### Risk Management

- **Position Sizing**: 2% of account per trade
- **Maximum Risk**: 2% of account
- **Daily Loss Limit**: $500

## 📊 Technical Indicators

This strategy uses the following technical indicators:

### Primary Indicators
- **vix**: {{INDICATOR_1_DESCRIPTION}}
- **MACD**: {{INDICATOR_2_DESCRIPTION}}

### Secondary Indicators
- **BB**: {{INDICATOR_3_DESCRIPTION}}
- **{{INDICATOR_4}}**: {{INDICATOR_4_DESCRIPTION}}

## ⚙️ Configuration Parameters

### Core Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `minConfidence` | 60 | 0-100 | Minimum confidence level for signal generation |
| `positionSize` | 0.02 | 0.001-0.1 | Position size as percentage of account |
| `strikeOffset` | 2 | -10 to 10 | Strike price offset from current price |

### Strategy-Specific Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `rsiPeriod` | 14 | 5-50 | RSI calculation period |
| `macdFast` | 12 | 5-20 | MACD fast EMA period |
| `macdSlow` | 26 | 20-50 | MACD slow EMA period |

### Risk Management Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `maxPositionSize` | 0.05 | 0.001-0.2 | Maximum position size limit |
| `stopLossPercent` | 0.5 | 0.1-1.0 | Stop loss as percentage of premium |
| `takeProfitPercent` | 1.0 | 0.2-5.0 | Take profit as percentage of premium |
| `maxDailyLoss` | 500 | 50-10000 | Maximum daily loss in dollars |

## 🚀 Usage Examples

### Basic Usage

```typescript
import { FlyagonalStrategy } from './flyagonal';

// Create strategy with default configuration
const strategy = new FlyagonalStrategy();

// Generate signal
const signal = strategy.generateSignal(marketData, optionsChain);

if (signal) {
  console.log(`Generated ${signal.action} signal with ${signal.confidence}% confidence`);
  // Execute trade...
}
```

### Custom Configuration

```typescript
import { FlyagonalStrategy } from './flyagonal';

// Create strategy with custom parameters
const strategy = new FlyagonalStrategy({
  parameters: {
    minConfidence: 70,
    positionSize: 0.015,
    strikeOffset: 3,
    // Add your custom parameters here
  },
  riskManagement: {
    maxPositionSize: 0.03,
    stopLossPercent: 0.4,
    takeProfitPercent: 0.8,
    maxDailyLoss: 300,
  },
  timeframe: '5Min',
  enabled: true,
});
```

### Using Performance Presets

```typescript
import { FlyagonalStrategy } from './flyagonal';
import { performancePresets } from './config';

// Use conservative preset
const conservativeStrategy = new FlyagonalStrategy(performancePresets.conservative);

// Use aggressive preset
const aggressiveStrategy = new FlyagonalStrategy(performancePresets.aggressive);

// Use scalping preset
const scalpingStrategy = new FlyagonalStrategy(performancePresets.scalping);
```

## 📈 Backtesting

### Running Backtests

```bash
# Run backtest with this strategy
npm run backtest -- --strategy=flyagonal --start=2024-01-01 --end=2024-01-31

# Run with custom configuration
npm run backtest -- --strategy=flyagonal --config=conservative --start=2024-01-01 --end=2024-01-31
```

### Expected Performance Metrics (CORRECTED - REALISTIC TARGETS)

**IMPORTANT CORRECTION**: The original claims of 90% win rate with 4:1 risk/reward were mathematically impossible. Below are realistic expectations based on actual options income strategy research:

| Metric | Realistic Range | Conservative Target | Notes |
|--------|-----------------|-------------------|-------|
| **Win Rate** | 65-75% | 70% | Typical for income strategies |
| **Risk/Reward Ratio** | 1:1 to 1.5:1 | 1.5:1 | $750 profit / $500 risk |
| **Annual Return** | 15-25% | 20% | Based on $25k account |
| **Max Drawdown** | 15-25% | 20% | Expected during stress periods |
| **Sharpe Ratio** | 0.8-1.2 | 1.0 | Risk-adjusted return metric |
| **Trade Frequency** | 2-3 per week | 1 per 4 days | Highly selective strategy |
| **Average Hold Time** | 3-6 days | 4.5 days | Multi-day strategy |

**Key Corrections Made:**
- ❌ **Removed impossible 90% win rate claim**
- ❌ **Removed impossible 4:1 risk/reward claim** 
- ✅ **Added realistic 65-75% win rate range**
- ✅ **Added achievable 1.5:1 risk/reward ratio**
- ✅ **Added proper drawdown expectations**

> ⚠️ **Critical Disclaimer**: The original strategy documentation contained unrealistic performance claims. No options strategy can sustainably maintain 90% win rates with 4:1 risk/reward ratios. These corrected metrics reflect actual market realities and proper risk management principles.

## 🧪 Testing

### Running Tests

```bash
# Run all strategy tests
npm test src/strategies/flyagonal/

# Run specific test suites
npm test src/strategies/flyagonal/tests/unit.test.ts
npm test src/strategies/flyagonal/tests/integration.test.ts
```

### Test Coverage

The strategy includes comprehensive tests for:

- ✅ Signal generation logic
- ✅ Risk calculation accuracy
- ✅ Configuration validation
- ✅ Edge case handling
- ✅ Performance benchmarks

## 🔧 Customization

### Adding Custom Indicators

```typescript
// In indicators.ts
export function calculateCustomIndicator(data: MarketData[]): number {
  // Your custom indicator logic
  return result;
}

// In strategy.ts
import { calculateCustomIndicator } from './indicators';

private analyzeMarketConditions(data: MarketData[], indicators: any): TradeSignal | null {
  const customValue = calculateCustomIndicator(data);
  
  // Use custom indicator in strategy logic
  if (customValue > threshold) {
    return this.generateBullishSignal(/* ... */);
  }
  
  return null;
}
```

### Modifying Entry/Exit Logic

```typescript
// Override specific methods for custom behavior
class CustomStrategy extends FlyagonalStrategy {
  protected checkBullishConditions(indicators: any, data: MarketData[]): boolean {
    // Your custom bullish condition logic
    return super.checkBullishConditions(indicators, data) && additionalCondition;
  }
}
```

## 📚 Market Context

### Best Market Conditions

This strategy performs best in:
- **Trending markets with clear direction**: Strategy works best when markets show sustained momentum
- **Moderate volatility (VIX 15-25)**: Provides enough movement without excessive noise
- **High volume periods**: Ensures good option liquidity and tight spreads

### Avoid Trading During

- **Major news events or earnings**: Can cause unpredictable price movements
- **Very low volatility (VIX < 12)**: Insufficient price movement for profitable trades
- **Market holidays or low volume periods**: Poor liquidity can lead to wide spreads

### Time of Day Considerations

- **Best Hours**: 10:00 AM - 3:00 PM (EST)
- **Avoid Hours**: 3:30 PM - 4:00 PM (EST)
- **Market Open**: Wait for initial volatility to settle
- **Market Close**: Close all positions 30 minutes before expiration

## ⚠️ Risk Warnings

### 0DTE Options Risks

- **Time Decay**: Options lose value rapidly as expiration approaches
- **High Volatility**: Prices can move dramatically in short periods
- **Total Loss**: Options can expire worthless, resulting in 100% loss
- **Liquidity**: Some strikes may have poor liquidity near expiration

### Strategy-Specific Risks

- **Rapid time decay in final hours**: 0DTE options lose value quickly as expiration approaches
- **High sensitivity to market volatility**: Small price movements can cause large percentage changes
- **Potential for total loss**: Options can expire worthless if not in-the-money

### Mitigation Strategies

- **Position Sizing**: Never risk more than you can afford to lose
- **Stop Losses**: Always use stop losses to limit downside
- **Diversification**: Don't put all capital in a single strategy
- **Paper Trading**: Test thoroughly before using real money

## 🔄 Version History

### Version 1.0.0 (2025-08-30)
- Initial implementation
- Real-time signal generation
- Adaptive risk management
- Multi-timeframe analysis

### Planned Improvements
- [ ] Add machine learning signal filtering
- [ ] Implement dynamic position sizing
- [ ] Add market regime detection

## 👥 Contributing

### Development Guidelines

1. Follow the established code structure
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Run backtests to validate improvements
5. Follow the project's `.cursorrules`

### Reporting Issues

When reporting issues, please include:
- Strategy version
- Configuration used
- Market conditions when issue occurred
- Expected vs actual behavior
- Steps to reproduce

## 📄 License

This strategy is part of the 0DTE Trading System and follows the same license terms.

## 📞 Support

For questions or support:
- Check the main project documentation
- Review the development guide
- Open an issue in the project repository
- Contact the strategy author: Steve Guns

---

**⚠️ Important Disclaimer**: This trading strategy is for educational and research purposes. Trading options involves substantial risk and is not suitable for all investors. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.
