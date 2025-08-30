# 🚀 0DTE Trading System - Development Guide

## 📋 Table of Contents
- [Architecture Overview](#architecture-overview)
- [Adding New Strategies](#adding-new-strategies)
- [Core File Protection](#core-file-protection)
- [Testing Guidelines](#testing-guidelines)
- [Code Quality Standards](#code-quality-standards)
- [Deployment Best Practices](#deployment-best-practices)

## 🏛️ Architecture Overview

### Protected Core Components
These files form the system's backbone and should **NEVER** be modified without explicit approval:

```
src/core/
├── alpaca-integration.ts    # 🔒 API integration layer
├── backtesting-engine.ts    # 🔒 Backtesting framework
└── ...

src/utils/
├── types.ts                 # 🔒 Core type definitions
└── ...

config/
├── integration-config.ts    # 🔒 System configuration
└── ...
```

### Extensible Components
These areas are designed for safe expansion:

```
src/strategies/              # ✅ Add new trading strategies
src/data/                   # ✅ Add new indicators/data sources
docs/                       # ✅ Add documentation
```

## 🎯 Adding New Strategies

### Step 1: Create Strategy Directory
Follow the standardized template structure:

```bash
src/strategies/my-new-strategy/
├── index.ts           # Main export
├── strategy.ts        # Core strategy logic  
├── config.ts          # Strategy configuration
├── types.ts           # Strategy-specific types
├── indicators.ts      # Custom indicators (optional)
├── tests/            # Strategy tests
│   ├── unit.test.ts
│   └── integration.test.ts
└── README.md         # Strategy documentation
```

### Step 2: Implement Required Interface
All strategies MUST implement the `TradingStrategy` interface:

```typescript
// src/strategies/my-new-strategy/strategy.ts
import { TradingStrategy, MarketData, OptionsChain, TradeSignal } from '../registry';

export class MyNewStrategy implements TradingStrategy {
  readonly name = 'my-new-strategy';
  readonly description = 'Description of what this strategy does';
  readonly version = '1.0.0';
  readonly author = 'Your Name';

  generateSignal(data: MarketData[], options: OptionsChain[]): TradeSignal | null {
    // Implementation here
    return null;
  }

  validateSignal(signal: TradeSignal): boolean {
    // Validation logic
    return true;
  }

  calculateRisk(signal: TradeSignal): RiskMetrics {
    // Risk calculation
    return {
      probabilityOfProfit: 0.6,
      maxLoss: 100,
      maxProfit: 150,
      riskRewardRatio: 1.5,
      timeDecayRisk: 'MEDIUM',
      volatilityRisk: 'LOW'
    };
  }

  // ... implement all other required methods
}
```

### Step 3: Register Strategy
Add your strategy to the registry:

```typescript
// src/strategies/registry.ts
export const STRATEGY_REGISTRY = {
  // ... existing strategies
  'my-new-strategy': () => import('./my-new-strategy'),
};

export const STRATEGY_METADATA = {
  // ... existing metadata
  'my-new-strategy': {
    category: 'MOMENTUM',
    marketConditions: ['TRENDING'],
    minAccountSize: 15000,
    complexity: 'INTERMEDIATE',
    status: 'EXPERIMENTAL',
    lastUpdated: new Date(),
  },
};
```

### Step 4: Create Tests
Write comprehensive tests for your strategy:

```typescript
// src/strategies/my-new-strategy/tests/unit.test.ts
import { MyNewStrategy } from '../strategy';
import { mockMarketData, mockOptionsChain } from '../../../tests/test-utils';

describe('MyNewStrategy', () => {
  let strategy: MyNewStrategy;

  beforeEach(() => {
    strategy = new MyNewStrategy();
  });

  test('should generate valid signals', () => {
    const signal = strategy.generateSignal(mockMarketData, mockOptionsChain);
    expect(signal).toBeDefined();
  });

  test('should validate signals correctly', () => {
    const signal = { /* mock signal */ };
    expect(strategy.validateSignal(signal)).toBe(true);
  });
});
```

## 🔒 Core File Protection

### What You CAN Do
- ✅ Add new strategies in `src/strategies/`
- ✅ Add new indicators in `src/data/`
- ✅ Extend existing interfaces (backward compatible)
- ✅ Add utility functions in appropriate modules
- ✅ Update documentation

### What You CANNOT Do Without Approval
- ❌ Modify core trading engine logic
- ❌ Change existing type definitions
- ❌ Alter API integration patterns
- ❌ Modify backtesting framework
- ❌ Change configuration structure

### Requesting Core Changes
If you need to modify core files:

1. **Analyze Impact**: Document what needs to change and why
2. **Propose Solution**: Include migration path and backward compatibility
3. **Get Approval**: Present to system architect/lead developer
4. **Document Changes**: Add comprehensive comments explaining modifications
5. **Test Thoroughly**: Ensure no existing functionality breaks

## 🧪 Testing Guidelines

### Test Organization
```
tests/
├── archived/           # Exploratory tests (kept for reference)
├── integration/        # Cross-component tests
├── unit/              # Individual component tests
└── test-utils.ts      # Shared testing utilities

src/strategies/[name]/tests/  # Strategy-specific tests
```

### Testing Requirements
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **Backtesting Validation**: Test with known historical data
- **Performance Tests**: Ensure acceptable execution times

### Real Data Testing
Following `.cursorrules`, all backtesting MUST use real Alpaca data:

```typescript
// ✅ Good - Real data
const backtest = new BacktestingEngine(config, alpacaClient);
await backtest.loadHistoricalData(); // Real Alpaca data

// ❌ Bad - Mock data (requires explicit approval)
const mockData = generateMockData(); // Not allowed
```

## 📊 Code Quality Standards

### TypeScript Requirements
- **Strict Mode**: No `any` types allowed
- **Comprehensive Types**: Define interfaces for all data structures
- **Error Handling**: Proper error types and handling
- **Documentation**: JSDoc comments for all public methods

### Naming Conventions
```typescript
// Directories: kebab-case
src/strategies/momentum-rsi-strategy/

// Classes: PascalCase
class MomentumRsiStrategy implements TradingStrategy

// Functions: camelCase
generateBuySignal(data: MarketData[]): TradeSignal

// Constants: UPPER_SNAKE_CASE
const MAX_POSITION_SIZE = 1000;

// Files: kebab-case
momentum-rsi-strategy.ts
```

### Documentation Requirements
```typescript
/**
 * Generates trading signals based on RSI momentum
 * 
 * @param data - Historical market data (minimum 20 bars required)
 * @param options - Available options chain for current timeframe
 * @returns TradeSignal if conditions met, null otherwise
 * 
 * @example
 * ```typescript
 * const signal = strategy.generateSignal(marketData, optionsChain);
 * if (signal) {
 *   await executeTradeSignal(signal);
 * }
 * ```
 */
generateSignal(data: MarketData[], options: OptionsChain[]): TradeSignal | null {
  // Implementation with inline comments explaining logic
}
```

## 🚀 Deployment Best Practices

### Environment Configuration
```typescript
// ✅ Environment-specific configs
const config = {
  development: {
    alpacaBaseUrl: 'https://paper-api.alpaca.markets',
    logLevel: 'DEBUG',
  },
  production: {
    alpacaBaseUrl: 'https://api.alpaca.markets',
    logLevel: 'INFO',
  }
};
```

### Security Checklist
- [ ] No hardcoded API keys
- [ ] Environment variables validated on startup
- [ ] Proper error handling for auth failures
- [ ] Secure logging (no credential exposure)
- [ ] Rate limiting for API calls

### Performance Monitoring
```typescript
// Add performance metrics
const startTime = performance.now();
const signal = strategy.generateSignal(data, options);
const executionTime = performance.now() - startTime;

logger.info('Strategy execution time', {
  strategy: strategy.name,
  executionTime,
  dataPoints: data.length
});
```

## 📋 Development Workflow Checklist

Before implementing any new feature:

### Planning Phase
- [ ] Architecture analysis completed
- [ ] Integration points identified
- [ ] User approval obtained (for core changes)
- [ ] Proper directory structure planned

### Implementation Phase
- [ ] Required interfaces implemented
- [ ] Comprehensive comments added
- [ ] Error handling implemented
- [ ] Performance considerations addressed

### Testing Phase
- [ ] Unit tests written and passing
- [ ] Integration tests completed
- [ ] Real data testing performed
- [ ] Performance benchmarks met

### Documentation Phase
- [ ] Code documentation updated
- [ ] README files updated
- [ ] Architecture decisions recorded
- [ ] Usage examples provided

### Deployment Phase
- [ ] Security review completed
- [ ] Environment configurations verified
- [ ] Monitoring and logging implemented
- [ ] Rollback procedures documented

## 🎓 Educational Resources

### Trading Concepts
- [Options Trading Basics](https://www.investopedia.com/options-basics-tutorial-4583012)
- [0DTE Options Explained](https://www.tastytrade.com/concepts-strategies/0dte-options)
- [Technical Analysis Fundamentals](https://www.investopedia.com/technical-analysis-4689657)

### Development Best Practices
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Clean Code Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)

### Financial Risk Management
- [Position Sizing Strategies](https://www.investopedia.com/articles/trading/09/position-sizing.asp)
- [Risk Management in Trading](https://www.investopedia.com/articles/trading/09/risk-management.asp)

## ⚠️ Critical Warnings

### Financial Risk
- Trading systems can cause significant financial loss
- Always test thoroughly before live deployment
- Implement proper position sizing and risk management
- Monitor system health continuously in production
- Have emergency shutdown procedures ready

### System Risk
- Backup all configurations and strategies
- Implement proper error recovery mechanisms
- Monitor API rate limits and quotas
- Have fallback procedures for system failures
- Maintain audit logs for all trading activities

---

**Remember**: This system handles real money and real trades. Always prioritize safety, testing, and risk management over speed of development.
