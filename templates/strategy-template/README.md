# 🎯 {{STRATEGY_NAME}} Trading Strategy

## 📋 Overview

{{STRATEGY_DESCRIPTION}}

This strategy is designed for **0DTE (Zero Days to Expiration) options trading** and focuses on {{STRATEGY_FOCUS}}. It uses {{MAIN_INDICATORS}} to identify optimal entry and exit points for short-term options positions.

## 🎯 Strategy Details

- **Strategy Type**: {{STRATEGY_TYPE}}
- **Market Conditions**: {{MARKET_CONDITIONS}}
- **Risk Level**: {{RISK_LEVEL}}
- **Timeframe**: {{TIMEFRAME}}
- **Minimum Account Size**: ${{MIN_ACCOUNT_SIZE}}
- **Complexity Level**: {{COMPLEXITY_LEVEL}}

## 🧠 Algorithm Logic

### Entry Conditions

The strategy generates **BUY CALL** signals when:
- {{CALL_CONDITION_1}}
- {{CALL_CONDITION_2}}
- {{CALL_CONDITION_3}}

The strategy generates **BUY PUT** signals when:
- {{PUT_CONDITION_1}}
- {{PUT_CONDITION_2}}
- {{PUT_CONDITION_3}}

### Exit Conditions

Positions are closed when:
- **Take Profit**: {{TAKE_PROFIT_CONDITION}}
- **Stop Loss**: {{STOP_LOSS_CONDITION}}
- **Time Exit**: {{TIME_EXIT_CONDITION}}

### Risk Management

- **Position Sizing**: {{POSITION_SIZING_LOGIC}}
- **Maximum Risk**: {{MAX_RISK_PER_TRADE}}
- **Daily Loss Limit**: {{DAILY_LOSS_LIMIT}}

## 📊 Technical Indicators

This strategy uses the following technical indicators:

### Primary Indicators
- **{{INDICATOR_1}}**: {{INDICATOR_1_DESCRIPTION}}
- **{{INDICATOR_2}}**: {{INDICATOR_2_DESCRIPTION}}

### Secondary Indicators
- **{{INDICATOR_3}}**: {{INDICATOR_3_DESCRIPTION}}
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
| `{{PARAM_1}}` | {{DEFAULT_1}} | {{RANGE_1}} | {{DESCRIPTION_1}} |
| `{{PARAM_2}}` | {{DEFAULT_2}} | {{RANGE_2}} | {{DESCRIPTION_2}} |
| `{{PARAM_3}}` | {{DEFAULT_3}} | {{RANGE_3}} | {{DESCRIPTION_3}} |

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
import { {{STRATEGY_CLASS_NAME}} } from './{{STRATEGY_ID}}';

// Create strategy with default configuration
const strategy = new {{STRATEGY_CLASS_NAME}}();

// Generate signal
const signal = strategy.generateSignal(marketData, optionsChain);

if (signal) {
  console.log(`Generated ${signal.action} signal with ${signal.confidence}% confidence`);
  // Execute trade...
}
```

### Custom Configuration

```typescript
import { {{STRATEGY_CLASS_NAME}} } from './{{STRATEGY_ID}}';

// Create strategy with custom parameters
const strategy = new {{STRATEGY_CLASS_NAME}}({
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
import { {{STRATEGY_CLASS_NAME}} } from './{{STRATEGY_ID}}';
import { performancePresets } from './config';

// Use conservative preset
const conservativeStrategy = new {{STRATEGY_CLASS_NAME}}(performancePresets.conservative);

// Use aggressive preset
const aggressiveStrategy = new {{STRATEGY_CLASS_NAME}}(performancePresets.aggressive);

// Use scalping preset
const scalpingStrategy = new {{STRATEGY_CLASS_NAME}}(performancePresets.scalping);
```

## 📈 Backtesting

### Running Backtests

```bash
# Run backtest with this strategy
npm run backtest -- --strategy={{STRATEGY_ID}} --start=2024-01-01 --end=2024-01-31

# Run with custom configuration
npm run backtest -- --strategy={{STRATEGY_ID}} --config=conservative --start=2024-01-01 --end=2024-01-31
```

### Expected Performance Metrics

Based on historical backtesting ({{BACKTEST_PERIOD}}):

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Return** | {{TOTAL_RETURN}}% | {{RETURN_NOTES}} |
| **Win Rate** | {{WIN_RATE}}% | {{WIN_RATE_NOTES}} |
| **Average Trade** | ${{AVG_TRADE}} | {{AVG_TRADE_NOTES}} |
| **Max Drawdown** | {{MAX_DRAWDOWN}}% | {{DRAWDOWN_NOTES}} |
| **Sharpe Ratio** | {{SHARPE_RATIO}} | {{SHARPE_NOTES}} |
| **Profit Factor** | {{PROFIT_FACTOR}} | {{PROFIT_FACTOR_NOTES}} |

> ⚠️ **Disclaimer**: Past performance does not guarantee future results. These metrics are based on historical backtesting and may not reflect live trading performance.

## 🧪 Testing

### Running Tests

```bash
# Run all strategy tests
npm test src/strategies/{{STRATEGY_ID}}/

# Run specific test suites
npm test src/strategies/{{STRATEGY_ID}}/tests/unit.test.ts
npm test src/strategies/{{STRATEGY_ID}}/tests/integration.test.ts
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
class CustomStrategy extends {{STRATEGY_CLASS_NAME}} {
  protected checkBullishConditions(indicators: any, data: MarketData[]): boolean {
    // Your custom bullish condition logic
    return super.checkBullishConditions(indicators, data) && additionalCondition;
  }
}
```

## 📚 Market Context

### Best Market Conditions

This strategy performs best in:
- **{{BEST_CONDITION_1}}**: {{CONDITION_1_EXPLANATION}}
- **{{BEST_CONDITION_2}}**: {{CONDITION_2_EXPLANATION}}
- **{{BEST_CONDITION_3}}**: {{CONDITION_3_EXPLANATION}}

### Avoid Trading During

- **{{AVOID_CONDITION_1}}**: {{AVOID_1_EXPLANATION}}
- **{{AVOID_CONDITION_2}}**: {{AVOID_2_EXPLANATION}}
- **{{AVOID_CONDITION_3}}**: {{AVOID_3_EXPLANATION}}

### Time of Day Considerations

- **Best Hours**: {{BEST_HOURS}} ({{TIMEZONE}})
- **Avoid Hours**: {{AVOID_HOURS}} ({{TIMEZONE}})
- **Market Open**: {{MARKET_OPEN_STRATEGY}}
- **Market Close**: {{MARKET_CLOSE_STRATEGY}}

## ⚠️ Risk Warnings

### 0DTE Options Risks

- **Time Decay**: Options lose value rapidly as expiration approaches
- **High Volatility**: Prices can move dramatically in short periods
- **Total Loss**: Options can expire worthless, resulting in 100% loss
- **Liquidity**: Some strikes may have poor liquidity near expiration

### Strategy-Specific Risks

- **{{RISK_1}}**: {{RISK_1_EXPLANATION}}
- **{{RISK_2}}**: {{RISK_2_EXPLANATION}}
- **{{RISK_3}}**: {{RISK_3_EXPLANATION}}

### Mitigation Strategies

- **Position Sizing**: Never risk more than you can afford to lose
- **Stop Losses**: Always use stop losses to limit downside
- **Diversification**: Don't put all capital in a single strategy
- **Paper Trading**: Test thoroughly before using real money

## 🔄 Version History

### Version {{VERSION}} ({{DATE}})
- Initial implementation
- {{FEATURE_1}}
- {{FEATURE_2}}
- {{FEATURE_3}}

### Planned Improvements
- [ ] {{IMPROVEMENT_1}}
- [ ] {{IMPROVEMENT_2}}
- [ ] {{IMPROVEMENT_3}}

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
- Contact the strategy author: {{AUTHOR_NAME}}

---

**⚠️ Important Disclaimer**: This trading strategy is for educational and research purposes. Trading options involves substantial risk and is not suitable for all investors. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.
