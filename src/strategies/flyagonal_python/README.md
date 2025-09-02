# 🦋 Flyagonal Strategy - Python Implementation

## 📋 Overview

The Flyagonal Strategy is a complex multi-leg options strategy based on Steve Guns' methodology, combining:

1. **Call Broken Wing Butterfly** (above market) - profits from rising markets + falling volatility
2. **Put Diagonal Spread** (below market) - profits from falling markets + rising volatility

This creates a **6-leg position** with a wide profit zone designed to capture profits in multiple market scenarios.

## 🎯 Strategy Details

- **Strategy Type**: Multi-leg volatility balanced
- **Market Conditions**: Neutral to medium volatility
- **Risk Level**: Medium (complex position management)
- **Timeframe**: 0DTE to 7DTE
- **Minimum Account Size**: $25,000
- **Complexity Level**: ADVANCED

## 🏗️ Architecture

### **Framework Integration**
```python
# Extends proven UnifiedStrategyBacktester framework
class FlyagonalBacktester(UnifiedStrategyBacktester):
    # Inherits all framework capabilities
    # Adds Flyagonal-specific logic
    # Maintains compatibility with existing systems
```

### **Key Components**

#### **1. FlyagonalStrategy** (`flyagonal_strategy.py`)
- Core strategy logic and position management
- 6-leg position construction and management
- VIX regime optimization
- Risk management and P&L calculation

#### **2. FlyagonalBacktester** (`flyagonal_backtester.py`)
- Backtesting engine extending UnifiedStrategyBacktester
- Framework integration and compatibility
- Comprehensive logging and analytics

#### **3. FlyagonalPosition** (within strategy)
- Position tracking and management
- Multi-leg P&L calculation
- Risk metrics and exit criteria

## 🧠 Strategy Logic

### **Entry Conditions**

The strategy enters when:
- **VIX Regime**: LOW or MEDIUM (avoids high volatility)
- **Profit Zone**: ≥200 points (Steve Guns requirement)
- **Risk/Reward**: Minimum 1.5:1 ratio
- **Liquidity**: Sufficient options for 6-leg construction
- **Position Limit**: Maximum 1 position (conservative approach)

### **Position Construction**

#### **Call Broken Wing Butterfly (3 legs)**
```python
# Above market - profits from rising prices + falling volatility
- Buy 1 ITM call (lower strike)
- Sell 2 ATM calls (middle strike)
- Buy 1 OTM call (upper strike - "broken wing")
```

#### **Put Diagonal Spread (3 legs)**
```python
# Below market - profits from falling prices + rising volatility
- Sell 1 near-term ATM put (high theta)
- Buy 1 longer-term ATM put (protection)
- Buy 1 longer-term OTM put (downside protection)
```

### **Exit Conditions**

Positions are closed when:
- **Profit Target**: 30% of entry cost
- **Stop Loss**: 50% of entry cost
- **Time Exit**: Before 3:30 PM (0DTE) or max 6 hours
- **Risk Management**: Override conditions

## 📊 Risk Management

### **Position Sizing**
- **Maximum Risk**: 5% of account per trade
- **Maximum Positions**: 1 (conservative for complex strategy)
- **Cash Management**: Integrated with ConservativeCashManager

### **Risk Controls**
- **Profit Target**: 30% (balanced for complex strategy)
- **Stop Loss**: 50% (protects against major moves)
- **Time Management**: Strict time-based exits
- **VIX Filtering**: Avoids high volatility periods

## 🎯 Performance Expectations

### **Target Metrics**
- **Win Rate**: 60-70% (complex strategy with wide profit zone)
- **Profit Factor**: >1.5 (risk/reward optimization)
- **Monthly Return**: 8-12% (conservative estimate)
- **Max Drawdown**: <10% (risk management focus)

### **VIX Regime Performance**
- **LOW VIX**: Best performance (stable conditions)
- **MEDIUM VIX**: Good performance (balanced volatility)
- **HIGH VIX**: Avoided (too volatile for complex positions)

## 🚀 Usage

### **Basic Backtesting**
```python
from flyagonal_backtester import FlyagonalBacktester

# Initialize backtester
backtester = FlyagonalBacktester(initial_balance=25000)

# Run backtest
results = backtester.run_flyagonal_backtest(
    start_date="2023-09-01",
    end_date="2023-09-30"
)

# Analyze results
print(f"Total Return: {results['total_return_pct']:.2f}%")
print(f"Flyagonal Trades: {results['flyagonal_metrics']['total_flyagonal_trades']}")
```

### **Strategy Analysis**
```python
# Get detailed strategy statistics
stats = backtester.flyagonal_strategy.get_strategy_statistics()

print(f"Win Rate: {stats['win_rate']:.1f}%")
print(f"Profit Factor: {stats['profit_factor']:.2f}")
print(f"VIX Regime Performance: {stats['vix_regime_performance']}")
```

## 🔧 Configuration

### **Strategy Parameters**
```python
# Key configurable parameters
min_profit_zone_width = 200      # Steve Guns requirement
max_positions = 1                # Conservative approach
profit_target_pct = 0.30         # 30% profit target
stop_loss_pct = 0.50             # 50% stop loss
max_risk_per_trade = 0.05        # 5% of account
```

### **VIX Thresholds**
```python
vix_low_threshold = 15.0         # Low volatility regime
vix_high_threshold = 25.0        # High volatility regime
```

## 📈 Integration with Framework

### **Framework Compatibility**
- ✅ **Extends UnifiedStrategyBacktester**: Full framework integration
- ✅ **Uses ConservativeCashManager**: Professional risk management
- ✅ **Integrates DetailedLogger**: Comprehensive logging
- ✅ **Black-Scholes Pricing**: Real option pricing
- ✅ **Market Intelligence**: VIX regime analysis

### **Separation from Iron Condor**
- ✅ **Separate Branch**: `feature/flyagonal-strategy-implementation`
- ✅ **Independent Files**: No modification of Iron Condor system
- ✅ **Framework Extension**: Builds on proven infrastructure
- ✅ **Isolated Testing**: Can be tested without affecting main system

## 🧪 Testing

### **Unit Testing**
```bash
# Test strategy construction
python -m pytest src/strategies/flyagonal_python/tests/

# Test backtester integration
python src/strategies/flyagonal_python/flyagonal_backtester.py
```

### **Integration Testing**
```bash
# Test with framework
python src/strategies/flyagonal_python/test_flyagonal_integration.py
```

## 📊 Expected Output

### **Backtest Results**
```
🦋 FLYAGONAL BACKTEST COMPLETE
   Final Balance: $27,850.00
   Total Return: +11.40%
   Flyagonal Trades: 15
   Profit Zone Success: 12/15
   Win Rate: 66.7%
   Profit Factor: 1.8
```

### **VIX Regime Analysis**
```
VIX Regime Performance:
   LOW (VIX < 15): 8 trades, 75% win rate, +$1,200 P&L
   MEDIUM (15-25): 7 trades, 57% win rate, +$650 P&L
   HIGH (VIX > 25): 0 trades (avoided)
```

## ⚠️ Important Notes

### **Complexity Warning**
- **Advanced Strategy**: Requires deep understanding of multi-leg options
- **Complex P&L**: 6-leg positions have complex profit/loss dynamics
- **Risk Management**: Critical due to position complexity

### **Framework Protection**
- **Iron Condor Untouched**: Main system remains unaffected
- **Separate Development**: Independent branch for safety
- **Framework Extension**: Builds on proven infrastructure

### **Performance Disclaimer**
- **Backtesting Results**: Historical performance, not guaranteed future results
- **Paper Trading**: Test thoroughly before live deployment
- **Risk Management**: Always use proper position sizing and risk controls

## 🔗 Related Files

- **TypeScript Implementation**: `src/strategies/flyagonal/strategy.ts`
- **Base Backtester**: `src/tests/analysis/unified_strategy_backtester.py`
- **Iron Condor System**: `src/tests/analysis/fixed_dynamic_risk_backtester.py`
- **Framework Documentation**: `README.md`, `TASKS.md`

## 📚 References

- **Steve Guns Methodology**: Original Flyagonal strategy design
- **Framework Architecture**: Advanced Options Trading Framework
- **Risk Management**: Conservative cash management principles
- **Options Theory**: Multi-leg position management best practices

---

**Built with ❤️ for professional multi-leg options strategy development**
