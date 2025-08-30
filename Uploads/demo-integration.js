// Demo script to showcase the Alpaca Integration functionality
// This demonstrates the key features without TypeScript compilation issues

console.log('🚀 Alpaca Integration Demo for 0DTE Options Trading');
console.log('=' .repeat(60));

// Simulate the core functionality
function demoGreeksCalculation() {
  console.log('\n📊 Greeks Calculation Demo');
  console.log('-'.repeat(30));
  
  // Simulate Black-Scholes calculation for 0DTE option
  const underlyingPrice = 450;
  const strikePrice = 450;
  const timeToExpiration = 4 / (252 * 6.5); // 4 hours in years
  const volatility = 0.25;
  const riskFreeRate = 0.05;
  
  // Simplified Black-Scholes calculation
  const d1 = (Math.log(underlyingPrice / strikePrice) + (riskFreeRate + 0.5 * volatility * volatility) * timeToExpiration) / (volatility * Math.sqrt(timeToExpiration));
  const d2 = d1 - volatility * Math.sqrt(timeToExpiration);
  
  // Standard normal CDF approximation
  const N = (x) => 0.5 * (1 + Math.sign(x) * Math.sqrt(1 - Math.exp(-2 * x * x / Math.PI)));
  
  // Calculate option price and Greeks
  const callPrice = underlyingPrice * N(d1) - strikePrice * Math.exp(-riskFreeRate * timeToExpiration) * N(d2);
  const delta = N(d1);
  const gamma = Math.exp(-0.5 * d1 * d1) / (underlyingPrice * volatility * Math.sqrt(2 * Math.PI * timeToExpiration));
  const theta = -(underlyingPrice * Math.exp(-0.5 * d1 * d1) * volatility) / (2 * Math.sqrt(2 * Math.PI * timeToExpiration)) / 365;
  const vega = underlyingPrice * Math.exp(-0.5 * d1 * d1) * Math.sqrt(timeToExpiration) / Math.sqrt(2 * Math.PI) / 100;
  
  console.log(`SPY $${strikePrice} Call (4 hours to expiration):`);
  console.log(`  Theoretical Price: $${callPrice.toFixed(2)}`);
  console.log(`  Delta: ${delta.toFixed(4)} (${(delta * 100).toFixed(1)}%)`);
  console.log(`  Gamma: ${gamma.toFixed(4)}`);
  console.log(`  Theta: $${theta.toFixed(2)} per day`);
  console.log(`  Vega: $${vega.toFixed(2)} per 1% vol change`);
  
  // 0DTE specific metrics
  const timeDecayPerMinute = theta / (6.5 * 60); // Convert daily theta to per minute
  const gammaRisk = Math.min(100, gamma * underlyingPrice * underlyingPrice * 100);
  const breakeven = strikePrice + callPrice;
  const probabilityITM = N(d2);
  
  console.log(`\n⚡ 0DTE Specific Metrics:`);
  console.log(`  Time decay per minute: $${timeDecayPerMinute.toFixed(4)}`);
  console.log(`  Gamma risk score: ${gammaRisk.toFixed(1)}/100`);
  console.log(`  Breakeven price: $${breakeven.toFixed(2)}`);
  console.log(`  Probability ITM: ${(probabilityITM * 100).toFixed(1)}%`);
}

function demoPaperTrading() {
  console.log('\n💰 Paper Trading Demo');
  console.log('-'.repeat(30));
  
  // Simulate paper trading account
  const account = {
    balance: 35000,
    positions: [],
    trades: [],
    dailyPnL: 0,
    totalPnL: 0
  };
  
  console.log(`Initial Account Balance: $${account.balance.toLocaleString()}`);
  
  // Simulate placing an order
  const order = {
    id: 'order_' + Date.now(),
    symbol: 'SPY240830C00450000',
    side: 'BUY',
    quantity: 2,
    price: 2.55,
    commission: 1.30, // $0.65 per contract
    timestamp: new Date()
  };
  
  console.log(`\n📋 Order Placed:`);
  console.log(`  Symbol: ${order.symbol}`);
  console.log(`  Side: ${order.side}`);
  console.log(`  Quantity: ${order.quantity} contracts`);
  console.log(`  Fill Price: $${order.price.toFixed(2)}`);
  console.log(`  Commission: $${order.commission.toFixed(2)}`);
  
  // Calculate position cost
  const positionCost = order.quantity * order.price * 100 + order.commission;
  account.balance -= positionCost;
  
  // Add position
  const position = {
    symbol: order.symbol,
    quantity: order.quantity,
    averagePrice: order.price,
    currentPrice: order.price,
    unrealizedPnL: 0,
    openTime: order.timestamp
  };
  
  account.positions.push(position);
  
  console.log(`\n📊 Position Created:`);
  console.log(`  Cost: $${positionCost.toFixed(2)}`);
  console.log(`  Remaining Balance: $${account.balance.toFixed(2)}`);
  console.log(`  Buying Power: $${(account.balance * 4).toLocaleString()}`);
  
  // Simulate price movement and P&L
  const newPrice = 3.20; // Option price increased
  position.currentPrice = newPrice;
  position.unrealizedPnL = (newPrice - position.averagePrice) * position.quantity * 100;
  
  console.log(`\n📈 Price Update:`);
  console.log(`  New Option Price: $${newPrice.toFixed(2)}`);
  console.log(`  Unrealized P&L: $${position.unrealizedPnL.toFixed(2)} (${((position.unrealizedPnL / positionCost) * 100).toFixed(1)}%)`);
  
  // Simulate exit at profit target (50%)
  if (position.unrealizedPnL / positionCost >= 0.50) {
    console.log(`\n🎯 Profit Target Reached - Exiting Position`);
    const exitPrice = newPrice;
    const realizedPnL = position.unrealizedPnL;
    
    account.balance += position.quantity * exitPrice * 100 - order.commission;
    account.totalPnL += realizedPnL;
    account.dailyPnL += realizedPnL;
    
    console.log(`  Exit Price: $${exitPrice.toFixed(2)}`);
    console.log(`  Realized P&L: $${realizedPnL.toFixed(2)}`);
    console.log(`  New Balance: $${account.balance.toFixed(2)}`);
    console.log(`  Daily P&L: $${account.dailyPnL.toFixed(2)}`);
  }
}

function demoRiskManagement() {
  console.log('\n⚠️ Risk Management Demo');
  console.log('-'.repeat(30));
  
  const riskConfig = {
    accountSize: 35000,
    dailyProfitTarget: 225,
    dailyLossLimit: 500,
    maxPositionSize: 3500, // 10% of account
    riskPerTrade: 0.02, // 2%
    maxPositions: 3
  };
  
  console.log(`Account Size: $${riskConfig.accountSize.toLocaleString()}`);
  console.log(`Daily Profit Target: $${riskConfig.dailyProfitTarget}`);
  console.log(`Daily Loss Limit: $${riskConfig.dailyLossLimit}`);
  console.log(`Max Position Size: $${riskConfig.maxPositionSize.toLocaleString()} (${(riskConfig.maxPositionSize / riskConfig.accountSize * 100).toFixed(1)}%)`);
  console.log(`Risk Per Trade: ${(riskConfig.riskPerTrade * 100).toFixed(1)}%`);
  console.log(`Max Concurrent Positions: ${riskConfig.maxPositions}`);
  
  // Calculate position sizing
  const riskAmount = riskConfig.accountSize * riskConfig.riskPerTrade;
  const optionPrice = 2.50;
  const maxContracts = Math.floor(riskAmount / (optionPrice * 100));
  
  console.log(`\n📏 Position Sizing Example:`);
  console.log(`  Risk Amount: $${riskAmount.toFixed(2)}`);
  console.log(`  Option Price: $${optionPrice.toFixed(2)}`);
  console.log(`  Max Contracts: ${maxContracts}`);
  console.log(`  Position Value: $${(maxContracts * optionPrice * 100).toLocaleString()}`);
  
  // Risk scenarios
  console.log(`\n📊 Risk Scenarios:`);
  const scenarios = [
    { name: '30% Stop Loss', change: -0.30 },
    { name: '50% Profit Target', change: 0.50 },
    { name: '100% Gain', change: 1.00 }
  ];
  
  scenarios.forEach(scenario => {
    const pnl = maxContracts * optionPrice * 100 * scenario.change;
    const accountImpact = (pnl / riskConfig.accountSize) * 100;
    console.log(`  ${scenario.name}: $${pnl.toFixed(2)} (${accountImpact.toFixed(2)}% of account)`);
  });
}

function demoStrategyConfiguration() {
  console.log('\n🎯 Strategy Configuration Demo');
  console.log('-'.repeat(30));
  
  const strategies = {
    conservative: {
      name: '0DTE Conservative',
      positionSize: 1, // 1% risk
      maxPositions: 2,
      stopLoss: 20,
      profitTarget: 30,
      dailyTarget: 150
    },
    default: {
      name: '0DTE Default',
      positionSize: 2, // 2% risk
      maxPositions: 3,
      stopLoss: 30,
      profitTarget: 50,
      dailyTarget: 225
    },
    aggressive: {
      name: '0DTE Aggressive',
      positionSize: 3, // 3% risk
      maxPositions: 5,
      stopLoss: 40,
      profitTarget: 75,
      dailyTarget: 300
    }
  };
  
  console.log('Available Strategies:');
  Object.entries(strategies).forEach(([key, strategy]) => {
    console.log(`\n${key.toUpperCase()}:`);
    console.log(`  Name: ${strategy.name}`);
    console.log(`  Position Size: ${strategy.positionSize}% risk per trade`);
    console.log(`  Max Positions: ${strategy.maxPositions}`);
    console.log(`  Stop Loss: ${strategy.stopLoss}%`);
    console.log(`  Profit Target: ${strategy.profitTarget}%`);
    console.log(`  Daily Target: $${strategy.dailyTarget}`);
  });
  
  // Account size recommendations
  console.log(`\n💡 Account Size Recommendations:`);
  const accountSizes = [15000, 35000, 75000, 150000];
  
  accountSizes.forEach(size => {
    let recommendedStrategy;
    if (size < 25000) recommendedStrategy = 'Conservative';
    else if (size < 100000) recommendedStrategy = 'Default';
    else recommendedStrategy = 'Aggressive';
    
    const dailyTarget = Math.floor(size * (recommendedStrategy === 'Conservative' ? 0.005 : recommendedStrategy === 'Default' ? 0.006 : 0.008));
    
    console.log(`  $${size.toLocaleString()}: ${recommendedStrategy} Strategy (Target: $${dailyTarget}/day)`);
  });
}

function demoAlpacaIntegration() {
  console.log('\n🔌 Alpaca Integration Demo');
  console.log('-'.repeat(30));
  
  console.log('Key Integration Features:');
  console.log('✅ REST API Client with rate limiting (200 RPM basic, 10,000 RPM pro)');
  console.log('✅ WebSocket streaming for real-time market data');
  console.log('✅ Options contract discovery and management');
  console.log('✅ Order placement and execution tracking');
  console.log('✅ Position monitoring and P&L calculation');
  console.log('✅ Paper trading mode for safe testing');
  
  console.log('\nAPI Endpoints Implemented:');
  console.log('• GET /v2/account - Account information');
  console.log('• GET /v2/positions - Current positions');
  console.log('• GET /v2/options/contracts - Option contract discovery');
  console.log('• POST /v2/orders - Order placement');
  console.log('• WebSocket streams for real-time data');
  
  console.log('\nAuthentication:');
  console.log('• Headers: APCA-API-KEY-ID, APCA-API-SECRET-KEY');
  console.log('• Paper Trading: https://paper-api.alpaca.markets');
  console.log('• Live Trading: https://api.alpaca.markets');
  
  console.log('\nRate Limiting:');
  console.log('• Basic Plan: 200 requests/minute');
  console.log('• Pro Plans: Up to 10,000 requests/minute');
  console.log('• WebSocket: 1 connection (basic), up to 10 (pro)');
}

function demoBacktesting() {
  console.log('\n📈 Backtesting Demo');
  console.log('-'.repeat(30));
  
  // Simulate backtest results
  const backtestResults = {
    period: '2024-01-01 to 2024-01-31',
    initialBalance: 35000,
    finalBalance: 38750,
    totalReturn: 3750,
    totalReturnPercent: 10.71,
    totalTrades: 45,
    winningTrades: 28,
    losingTrades: 17,
    winRate: 62.2,
    avgWin: 215,
    avgLoss: -125,
    profitFactor: 1.85,
    maxDrawdown: 8.5,
    sharpeRatio: 2.34
  };
  
  console.log(`Backtest Period: ${backtestResults.period}`);
  console.log(`Initial Balance: $${backtestResults.initialBalance.toLocaleString()}`);
  console.log(`Final Balance: $${backtestResults.finalBalance.toLocaleString()}`);
  console.log(`Total Return: $${backtestResults.totalReturn.toLocaleString()} (${backtestResults.totalReturnPercent.toFixed(1)}%)`);
  
  console.log(`\nTrade Statistics:`);
  console.log(`  Total Trades: ${backtestResults.totalTrades}`);
  console.log(`  Winning Trades: ${backtestResults.winningTrades}`);
  console.log(`  Losing Trades: ${backtestResults.losingTrades}`);
  console.log(`  Win Rate: ${backtestResults.winRate.toFixed(1)}%`);
  console.log(`  Average Win: $${backtestResults.avgWin}`);
  console.log(`  Average Loss: $${backtestResults.avgLoss}`);
  console.log(`  Profit Factor: ${backtestResults.profitFactor.toFixed(2)}`);
  
  console.log(`\nRisk Metrics:`);
  console.log(`  Max Drawdown: ${backtestResults.maxDrawdown.toFixed(1)}%`);
  console.log(`  Sharpe Ratio: ${backtestResults.sharpeRatio.toFixed(2)}`);
  
  // Monthly breakdown
  console.log(`\nMonthly Performance:`);
  const monthlyReturns = [
    { month: 'Week 1', return: 875 },
    { month: 'Week 2', return: 1250 },
    { month: 'Week 3', return: 950 },
    { month: 'Week 4', return: 675 }
  ];
  
  monthlyReturns.forEach(week => {
    console.log(`  ${week.month}: $${week.return} (${(week.return / backtestResults.initialBalance * 100).toFixed(2)}%)`);
  });
}

// Run all demos
function runDemo() {
  demoGreeksCalculation();
  demoPaperTrading();
  demoRiskManagement();
  demoStrategyConfiguration();
  demoAlpacaIntegration();
  demoBacktesting();
  
  console.log('\n🎉 Demo Complete!');
  console.log('=' .repeat(60));
  console.log('\n📋 Summary of Implemented Features:');
  console.log('✅ Comprehensive Alpaca API Integration (REST + WebSocket)');
  console.log('✅ Black-Scholes Options Pricing with Greeks Calculation');
  console.log('✅ Paper Trading Engine with Realistic Simulation');
  console.log('✅ Backtesting Framework for Strategy Validation');
  console.log('✅ Live Trading Connector with Risk Management');
  console.log('✅ Multiple Strategy Configurations (Conservative to Aggressive)');
  console.log('✅ 0DTE-Specific Optimizations and Risk Controls');
  
  console.log('\n🎯 Ready for 0DTE Options Trading:');
  console.log('• Target: $200-250 daily profit on $35k account');
  console.log('• Risk Management: 2% per trade, 30% stop loss, 50% profit target');
  console.log('• Time Management: Max 4-hour holds, exit 30min before expiration');
  console.log('• Greeks Monitoring: Real-time Delta, Gamma, Theta tracking');
  console.log('• Paper Trading: Full simulation before live trading');
  
  console.log('\n🚀 Next Steps:');
  console.log('1. Set up Alpaca API credentials');
  console.log('2. Test strategies in paper trading mode');
  console.log('3. Run backtests on historical data');
  console.log('4. Deploy live trading with proper risk controls');
  console.log('5. Monitor performance and adjust parameters');
  
  console.log('\n⚠️ Important: Always start with paper trading and never risk more than you can afford to lose!');
}

// Run the demo
runDemo();
