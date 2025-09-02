# 🎯 Credit Spread Optimizer

Professional-grade credit spread trading system designed to achieve **$200/day profit** with a **$25,000 account** using advanced risk management and Kelly Criterion position sizing.

## 📋 Overview

This system implements the user's specifications for a disciplined credit spread trading approach:

- **Daily Target**: $200 profit (0.8% return)
- **Win Rate Target**: 75%
- **Risk Management**: 2% max per trade, 4% max daily drawdown
- **Position Sizing**: Kelly Criterion optimization
- **Profit Taking**: 50% of maximum profit
- **Time Management**: 9:45 AM - 2:30 PM ET trading window

## 🏗️ Architecture

Following @.cursorrules patterns, the system is modular and extensible:

```
src/strategies/credit_spread_optimizer/
├── __init__.py                 # Package exports
├── config.py                   # Configuration management
├── kelly_position_sizer.py     # Kelly Criterion position sizing
├── profit_manager.py           # Profit taking & risk management
├── market_filter.py           # Market condition filtering (TODO)
├── strike_optimizer.py        # 0.20 delta strike selection (TODO)
├── risk_controller.py         # Daily limits & controls (TODO)
└── README.md                  # This documentation
```

## 🎯 Key Components

### 1. Kelly Criterion Position Sizer

**Purpose**: Optimal position sizing based on historical performance

**Features**:
- Dynamic position sizing using Kelly formula: `f = (bp - q) / b`
- Adapts to recent trading performance
- Safety constraints and daily loss adjustments
- Confidence scoring for reliability assessment

**Usage**:
```python
from credit_spread_optimizer import KellyPositionSizer, DEFAULT_CONFIG, KELLY_CONFIG

sizer = KellyPositionSizer(DEFAULT_CONFIG, KELLY_CONFIG)

recommendation = sizer.get_position_size_recommendation(
    account_balance=25000.0,
    premium_per_contract=40.0,    # $0.40 premium = $40 per contract
    max_loss_per_contract=120.0,  # $1.20 max loss = $120 per contract
    current_positions=1,
    current_daily_pnl=-50.0
)

print(f"Recommended contracts: {recommendation['recommended_contracts']}")
```

### 2. Profit Manager

**Purpose**: Systematic profit taking and loss management

**Features**:
- 50% profit target system
- Trailing stop loss at 25% profit threshold
- Time-based exits before expiration
- Force close 30 minutes before market close
- Comprehensive position tracking

**Usage**:
```python
from credit_spread_optimizer import ProfitManager, DEFAULT_CONFIG

manager = ProfitManager(DEFAULT_CONFIG)

# Add position
manager.add_position(
    position_id="BPS_001",
    strategy_type="BULL_PUT_SPREAD",
    entry_time=datetime.now(),
    expiration_date=datetime.now() + timedelta(hours=6),
    contracts=5,
    short_strike=520.0,
    long_strike=515.0,
    premium_collected=200.0
)

# Check exit conditions
exit_signal = manager.check_exit_conditions("BPS_001", datetime.now())
if exit_signal.should_exit:
    print(f"Exit recommended: {exit_signal.exit_reason}")
```

### 3. Configuration System

**Purpose**: Centralized parameter management

**Key Parameters**:
```python
# Account & Risk Management
account_balance: 25000.0
daily_profit_target: 200.0
daily_loss_limit: -400.0
max_risk_per_trade_pct: 0.02

# Spread Configuration
spread_width: 5                 # $5 wide spreads
target_delta: 0.20             # 20 delta short strikes
min_premium_collected: 0.35    # Min $0.35 per spread

# Profit Management
profit_target_pct: 0.50        # 50% profit target
stop_loss_multiplier: 2.0      # 2x premium stop loss

# Time Management
market_open_time: time(9, 45)   # 9:45 AM ET
market_close_time: time(14, 30) # 2:30 PM ET
force_close_time: time(15, 30)  # 3:30 PM ET
```

## 📊 Expected Performance

### Target Metrics
| Metric | Target | Implementation |
|--------|--------|----------------|
| **Daily Profit** | $200 | Kelly sizing + 50% profit taking |
| **Win Rate** | 75% | 0.20 delta strikes + market filtering |
| **Max Daily Loss** | $400 | Daily risk controls |
| **Risk per Trade** | 2% | Kelly Criterion with safety limits |
| **Positions** | 4 max | Position count management |

### Risk-Adjusted Returns
- **Expected Annual Return**: ~200% (assuming 250 trading days)
- **Maximum Drawdown**: 8% (monthly)
- **Sharpe Ratio Target**: > 2.0
- **Win/Loss Ratio**: 1:2 (risk $120 to make $60, but 75% win rate)

## 🔧 Integration with Existing System

The Credit Spread Optimizer integrates with the Enhanced Adaptive Router:

```python
# Integration example (TODO: implement)
from strategies.adaptive_zero_dte import EnhancedAdaptiveRouter
from strategies.credit_spread_optimizer import KellyPositionSizer, ProfitManager

class OptimizedAdaptiveRouter(EnhancedAdaptiveRouter):
    def __init__(self, account_balance: float = 25000):
        super().__init__(account_balance)
        self.position_sizer = KellyPositionSizer(DEFAULT_CONFIG, KELLY_CONFIG)
        self.profit_manager = ProfitManager(DEFAULT_CONFIG)
    
    def execute_optimized_trade(self, strategy_rec, market_data):
        # Use Kelly sizing for position size
        size_rec = self.position_sizer.get_position_size_recommendation(...)
        
        # Execute trade with optimal size
        # Add to profit manager for exit management
        # Return trade result
```

## 🚀 Implementation Status

### ✅ Completed (Phase 1)
- [x] Configuration system with validation
- [x] Kelly Criterion position sizer with safety constraints
- [x] Profit manager with 50% target and trailing stops
- [x] Comprehensive logging and monitoring
- [x] Unit tests and validation

### 🔄 In Progress (Phase 2)
- [ ] Market filtering (VIX, volume, time windows)
- [ ] Strike optimizer for 0.20 delta selection
- [ ] Daily risk controller integration
- [ ] Performance tracking dashboard

### 📋 Planned (Phase 3)
- [ ] Integration with Enhanced Adaptive Router
- [ ] Comprehensive backtesting validation
- [ ] Paper trading integration
- [ ] Live deployment preparation

## 📈 Usage Examples

### Basic Setup
```python
from credit_spread_optimizer import *

# Initialize components
config = get_config_for_account_size(25000.0)
sizer = KellyPositionSizer(config, KELLY_CONFIG)
manager = ProfitManager(config)

# Validate configuration
errors = validate_config(config)
if errors:
    print("Configuration errors:", errors)
```

### Position Sizing Workflow
```python
# Get position size recommendation
recommendation = sizer.get_position_size_recommendation(
    account_balance=25000.0,
    premium_per_contract=40.0,
    max_loss_per_contract=120.0,
    current_positions=2,
    current_daily_pnl=50.0
)

if recommendation['can_trade']:
    contracts = recommendation['recommended_contracts']
    print(f"Trade {contracts} contracts (Kelly: {recommendation['kelly_fraction']:.2%})")
else:
    print(f"Cannot trade: {recommendation['reason']}")
```

### Profit Management Workflow
```python
# Add position to management
manager.add_position(
    position_id="BPS_20241201_001",
    strategy_type="BULL_PUT_SPREAD",
    entry_time=datetime.now(),
    expiration_date=datetime.now() + timedelta(hours=6),
    contracts=contracts,
    short_strike=520.0,
    long_strike=515.0,
    premium_collected=contracts * 40.0
)

# Monitor and manage exits
while position_active:
    # Update position value from market data
    manager.update_position_value(position_id, current_market_value, datetime.now())
    
    # Check exit conditions
    exit_signal = manager.check_exit_conditions(position_id, datetime.now())
    
    if exit_signal.should_exit:
        # Execute exit trade
        final_pnl = execute_exit_trade(position_id)
        manager.close_position(position_id, exit_signal.exit_reason, datetime.now(), final_pnl)
        break
```

## ⚠️ Risk Considerations

### Implementation Risks
1. **Over-optimization**: Avoid curve-fitting to historical data
2. **Market regime changes**: System may need adaptation
3. **Execution slippage**: Real trading costs vs backtests
4. **Psychological factors**: Discipline required

### Mitigation Strategies
1. **Conservative Kelly**: Use 75% of calculated Kelly fraction
2. **Daily limits**: Hard stops at $400 loss / $300 profit
3. **Position limits**: Maximum 4 concurrent positions
4. **Time limits**: No trading outside 9:45 AM - 2:30 PM ET

## 📚 References

- **Kelly Criterion**: Optimal position sizing for favorable odds
- **Credit Spreads**: Limited risk, limited reward options strategies
- **0DTE Trading**: Same-day expiration options trading
- **Risk Management**: Professional trading risk controls

---

*This system follows @.cursorrules architecture principles and integrates with the existing Enhanced Adaptive Router infrastructure while providing the sophisticated risk management required for consistent $200/day performance.*
