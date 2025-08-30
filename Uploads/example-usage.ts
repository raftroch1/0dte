
import { AlpacaIntegration } from './alpaca-integration';
import { AlpacaPaperTrading } from './alpaca-paper-trading_improved';
import { BacktestingEngine } from './backtesting-engine';
import { LiveTradingConnector } from './live-trading-connector';
import { GreeksSimulator } from './greeks-simulator';
import { IntegrationConfig } from './integration-config';
import { MarketData, OptionsChain } from './types';

// Example 1: Basic Alpaca Integration Setup
async function example1_BasicSetup() {
  console.log('📋 Example 1: Basic Alpaca Integration Setup');
  
  // Initialize Alpaca client
  const alpaca = new AlpacaIntegration({
    apiKey: process.env.ALPACA_API_KEY!,
    apiSecret: process.env.ALPACA_API_SECRET!,
    isPaper: true // Use paper trading for testing
  });

  try {
    // Test connection
    const connected = await alpaca.testConnection();
    console.log(`Connection status: ${connected ? 'Connected' : 'Failed'}`);

    // Get account information
    const account = await alpaca.getAccount();
    console.log(`Account equity: $${parseFloat(account.equity).toLocaleString()}`);

    // Get current positions
    const positions = await alpaca.getPositions();
    console.log(`Current positions: ${positions.length}`);

    // Get SPY option contracts expiring today
    const today = new Date().toISOString().split('T')[0];
    const contracts = await alpaca.getOptionContracts('SPY', today);
    console.log(`0DTE SPY contracts available: ${contracts.length}`);

  } catch (error) {
    console.error('Setup error:', error);
  }
}

// Example 2: Greeks Calculation for 0DTE Options
async function example2_GreeksCalculation() {
  console.log('📋 Example 2: Greeks Calculation for 0DTE Options');
  
  // Example: SPY at $450, 4 hours to expiration
  const inputs = {
    underlyingPrice: 450,
    strikePrice: 450, // ATM
    timeToExpiration: GreeksSimulator.hoursToYears(4),
    riskFreeRate: 0.05,
    volatility: 0.25,
    optionType: 'call' as const
  };

  // Calculate option price and Greeks
  const result = GreeksSimulator.calculateOptionPrice(inputs);
  
  console.log('🎯 ATM Call Option (4 hours to expiration):');
  console.log(`Theoretical Price: $${result.theoreticalPrice.toFixed(2)}`);
  console.log(`Delta: ${result.delta.toFixed(4)} (${(result.delta * 100).toFixed(1)}%)`);
  console.log(`Gamma: ${result.gamma.toFixed(4)}`);
  console.log(`Theta: $${result.theta.toFixed(2)} per day`);
  console.log(`Vega: $${result.vega.toFixed(2)} per 1% vol change`);

  // Calculate 0DTE specific metrics
  const zdteMetrics = GreeksSimulator.calculate0DTEMetrics(inputs);
  console.log('\n⚡ 0DTE Specific Metrics:');
  console.log(`Time decay per minute: $${zdteMetrics.timeDecayRate.toFixed(4)}`);
  console.log(`Gamma risk score: ${zdteMetrics.gammaRisk.toFixed(1)}/100`);
  console.log(`Breakeven price: $${zdteMetrics.breakeven.toFixed(2)}`);
  console.log(`Probability ITM: ${(zdteMetrics.probabilityITM * 100).toFixed(1)}%`);

  // Compare different strikes
  console.log('\n📊 Strike Comparison:');
  for (const strike of [445, 450, 455]) {
    const strikeInputs = { ...inputs, strikePrice: strike };
    const strikeResult = GreeksSimulator.calculateOptionPrice(strikeInputs);
    console.log(`$${strike} Call: $${strikeResult.theoreticalPrice.toFixed(2)} (Δ=${strikeResult.delta.toFixed(3)})`);
  }
}

// Example 3: Paper Trading Simulation
async function example3_PaperTrading() {
  console.log('📋 Example 3: Paper Trading Simulation');
  
  // Initialize paper trading with $35k account
  const paperTrading = new AlpacaPaperTrading({
    initialBalance: 35000,
    commissionPerContract: 0.65,
    bidAskSpreadPercent: 0.02,
    slippagePercent: 0.001,
    maxPositions: 3,
    riskFreeRate: 0.05
  });

  // Simulate market data
  const marketData: MarketData = {
    timestamp: new Date(),
    open: 449,
    high: 451,
    low: 448,
    close: 450,
    volume: 1500000
  };

  paperTrading.updateMarketData('SPY', marketData);

  // Simulate 0DTE options chain
  const optionsChain: OptionsChain[] = [
    {
      strike: 450,
      expiration: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
      type: 'CALL',
      bid: 2.45,
      ask: 2.65,
      impliedVolatility: 0.25,
      delta: 0.52,
      gamma: 0.08,
      theta: -0.18,
      vega: 0.06,
      volume: 850,
      openInterest: 2500
    },
    {
      strike: 450,
      expiration: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
      type: 'PUT',
      bid: 2.35,
      ask: 2.55,
      impliedVolatility: 0.26,
      delta: -0.48,
      gamma: 0.08,
      theta: -0.16,
      vega: 0.06,
      volume: 720,
      openInterest: 1800
    }
  ];

  paperTrading.updateOptionsChain('SPY', optionsChain);

  // Place a test order
  const order = await paperTrading.submitOrder({
    symbol: 'SPY240830C00450000',
    side: 'BUY',
    quantity: 2,
    orderType: 'MARKET'
  });

  console.log(`📋 Order placed: ${order.id}`);
  console.log(`Fill price: $${order.fillPrice?.toFixed(2)}`);
  console.log(`Commission: $${order.commission.toFixed(2)}`);

  // Check account metrics
  const metrics = paperTrading.getAccountMetrics();
  console.log('\n💰 Account Status:');
  console.log(`Balance: $${metrics.balance.toFixed(2)}`);
  console.log(`Equity: $${metrics.equity.toFixed(2)}`);
  console.log(`Buying Power: $${metrics.buyingPower.toFixed(2)}`);
  console.log(`Open Positions: ${metrics.positions.length}`);
  console.log(`Total P&L: $${metrics.totalPnL.toFixed(2)}`);

  if (metrics.positions.length > 0) {
    const position = metrics.positions[0];
    console.log('\n📊 Position Details:');
    console.log(`Symbol: ${position.symbol}`);
    console.log(`Quantity: ${position.quantity}`);
    console.log(`Avg Price: $${position.averagePrice.toFixed(2)}`);
    console.log(`Current Price: $${position.currentPrice.toFixed(2)}`);
    console.log(`Unrealized P&L: $${position.unrealizedPnL.toFixed(2)} (${position.unrealizedPnLPercent.toFixed(1)}%)`);
    console.log(`Greeks: Δ=${position.greeks.delta.toFixed(3)}, Θ=${position.greeks.theta.toFixed(2)}`);
  }
}

// Example 4: Backtesting a 0DTE Strategy
async function example4_Backtesting() {
  console.log('📋 Example 4: Backtesting a 0DTE Strategy');
  
  // Create backtest configuration
  const config = IntegrationConfig.createBacktestConfig(
    new Date('2024-01-01'),
    new Date('2024-01-31'),
    'default',
    'SPY'
  );

  console.log('📊 Backtest Configuration:');
  console.log(`Period: ${config.startDate.toDateString()} to ${config.endDate.toDateString()}`);
  console.log(`Initial Balance: $${config.initialBalance.toLocaleString()}`);
  console.log(`Strategy: ${config.strategy.name}`);
  console.log(`Daily Target: $${config.strategy.dailyProfitTarget}`);
  console.log(`Max Daily Loss: $${config.strategy.maxDailyLoss}`);

  // Note: Full backtesting would require historical data
  console.log('\n⚠️ Note: Full backtesting requires historical market data from Alpaca API');
  console.log('This example shows the configuration setup. To run a complete backtest:');
  console.log('1. Ensure valid Alpaca API credentials');
  console.log('2. Call backtest.loadHistoricalData()');
  console.log('3. Define your strategy function');
  console.log('4. Call backtest.runBacktest(strategyFunction)');
}

// Example 5: Live Trading Setup (Paper Mode)
async function example5_LiveTrading() {
  console.log('📋 Example 5: Live Trading Setup (Paper Mode)');
  
  // Create live trading configuration
  const config = IntegrationConfig.getLiveTradingConfig(
    process.env.ALPACA_API_KEY || 'demo_key',
    process.env.ALPACA_API_SECRET || 'demo_secret',
    true // Paper trading mode
  );

  console.log('🎯 Live Trading Configuration:');
  console.log(`Account Balance: $${config.accountConfig.balance.toLocaleString()}`);
  console.log(`Daily Target: $${config.accountConfig.dailyProfitTarget}`);
  console.log(`Daily Loss Limit: $${config.accountConfig.dailyLossLimit}`);
  console.log(`Max Position Size: $${config.riskManagement.maxPositionSize.toLocaleString()}`);
  console.log(`Max Open Positions: ${config.riskManagement.maxOpenPositions}`);
  console.log(`Paper Trading: ${config.enablePaperTrading ? 'Enabled' : 'Disabled'}`);

  // Initialize live trading connector
  const liveTrading = new LiveTradingConnector(config);

  // Set up event handlers
  liveTrading.on('authenticated', () => {
    console.log('✅ Live trading authenticated');
  });

  liveTrading.on('trade_update', (update) => {
    console.log('📈 Trade update:', update.event);
  });

  liveTrading.on('order_placed', (order) => {
    console.log('📋 Order placed:', order.symbol);
  });

  liveTrading.on('position_exited', ({ symbol, reason }) => {
    console.log(`🚪 Position exited: ${symbol} (${reason})`);
  });

  liveTrading.on('risk_violation', ({ level, riskCheck }) => {
    console.log(`⚠️ Risk violation (${level}):`, riskCheck.violations);
  });

  console.log('\n⚠️ Note: To start live trading, call liveTrading.start()');
  console.log('This will connect to Alpaca WebSocket streams and begin monitoring');
}

// Example 6: Strategy Configuration and Validation
async function example6_StrategyConfiguration() {
  console.log('📋 Example 6: Strategy Configuration and Validation');
  
  // Get different strategy configurations
  const strategies = {
    conservative: IntegrationConfig.getConservativeStrategy(),
    default: IntegrationConfig.getDefault0DTEStrategy(),
    aggressive: IntegrationConfig.getAggressiveStrategy(),
    morning: IntegrationConfig.getMorningMomentumStrategy(),
    scalping: IntegrationConfig.getScalpingStrategy()
  };

  console.log('📊 Available Strategies:');
  Object.entries(strategies).forEach(([name, strategy]) => {
    console.log(`\n${name.toUpperCase()}:`);
    console.log(`  Position Size: ${strategy.positionSizePercent}%`);
    console.log(`  Max Positions: ${strategy.maxPositions}`);
    console.log(`  Stop Loss: ${strategy.stopLossPercent}%`);
    console.log(`  Take Profit: ${strategy.takeProfitPercent}%`);
    console.log(`  Daily Target: $${strategy.dailyProfitTarget}`);
    console.log(`  Max Hold Time: ${strategy.maxHoldingTimeMinutes} minutes`);
    
    // Validate strategy
    const validation = IntegrationConfig.validateStrategy(strategy);
    console.log(`  Validation: ${validation.valid ? '✅ PASSED' : '❌ FAILED'}`);
    if (!validation.valid) {
      console.log(`  Errors: ${validation.errors.join(', ')}`);
    }
  });

  // Show recommended settings for different account sizes
  console.log('\n💰 Recommended Settings by Account Size:');
  const accountSizes = [15000, 35000, 75000, 150000];
  
  accountSizes.forEach(size => {
    const recommendation = IntegrationConfig.getRecommendedSettings(size);
    console.log(`\n$${size.toLocaleString()} Account:`);
    console.log(`  Risk Level: ${recommendation.riskLevel}`);
    console.log(`  Strategy: ${recommendation.strategy.name}`);
    console.log(`  Daily Target: $${recommendation.accountConfig.dailyProfitTarget}`);
    console.log(`  Risk Per Trade: ${(recommendation.accountConfig.riskPerTrade * 100).toFixed(1)}%`);
  });
}

// Example 7: Real-time Greeks Monitoring
async function example7_GreeksMonitoring() {
  console.log('📋 Example 7: Real-time Greeks Monitoring');
  
  // Simulate a portfolio of 0DTE positions
  const positions = [
    {
      inputs: {
        underlyingPrice: 450,
        strikePrice: 450,
        timeToExpiration: GreeksSimulator.hoursToYears(3),
        riskFreeRate: 0.05,
        volatility: 0.25,
        optionType: 'call' as const
      },
      quantity: 2,
      multiplier: 100
    },
    {
      inputs: {
        underlyingPrice: 450,
        strikePrice: 455,
        timeToExpiration: GreeksSimulator.hoursToYears(3),
        riskFreeRate: 0.05,
        volatility: 0.23,
        optionType: 'put' as const
      },
      quantity: 1,
      multiplier: 100
    }
  ];

  // Calculate portfolio Greeks
  const portfolioGreeks = GreeksSimulator.calculatePortfolioGreeks(positions);
  
  console.log('📊 Portfolio Greeks:');
  console.log(`Total Delta: ${portfolioGreeks.delta.toFixed(2)}`);
  console.log(`Total Gamma: ${portfolioGreeks.gamma.toFixed(2)}`);
  console.log(`Total Theta: $${portfolioGreeks.theta.toFixed(2)} per day`);
  console.log(`Total Vega: $${portfolioGreeks.vega.toFixed(2)} per 1% vol change`);

  // Simulate price movements and show P&L attribution
  console.log('\n📈 P&L Scenarios:');
  const priceChanges = [-2, -1, 0, 1, 2];
  
  priceChanges.forEach(change => {
    const deltaP_L = portfolioGreeks.delta * change;
    const gammaP_L = 0.5 * portfolioGreeks.gamma * change * change;
    const totalP_L = deltaP_L + gammaP_L;
    
    console.log(`SPY ${change >= 0 ? '+' : ''}${change}: $${totalP_L.toFixed(2)} (Δ: $${deltaP_L.toFixed(2)}, Γ: $${gammaP_L.toFixed(2)})`);
  });

  // Time decay simulation
  console.log('\n⏰ Time Decay Simulation:');
  const timeSteps = [0, 1, 2, 3]; // Hours
  timeSteps.forEach(hours => {
    const newPositions = positions.map(pos => ({
      ...pos,
      inputs: {
        ...pos.inputs,
        timeToExpiration: GreeksSimulator.hoursToYears(3 - hours)
      }
    }));
    
    const newGreeks = GreeksSimulator.calculatePortfolioGreeks(newPositions);
    const thetaDecay = newGreeks.theta - portfolioGreeks.theta;
    
    console.log(`After ${hours}h: Theta = $${newGreeks.theta.toFixed(2)} (decay: $${thetaDecay.toFixed(2)})`);
  });
}

// Main example runner
async function runAllExamples() {
  console.log('🚀 Alpaca Integration Examples\n');
  console.log('These examples demonstrate the comprehensive 0DTE options trading system');
  console.log('targeting $200-250 daily profit on a $35k account.\n');

  const examples = [
    example1_BasicSetup,
    example2_GreeksCalculation,
    example3_PaperTrading,
    example4_Backtesting,
    example5_LiveTrading,
    example6_StrategyConfiguration,
    example7_GreeksMonitoring
  ];

  for (let i = 0; i < examples.length; i++) {
    try {
      await examples[i]();
      console.log('\n' + '='.repeat(60) + '\n');
    } catch (error) {
      console.error(`Example ${i + 1} failed:`, error);
      console.log('\n' + '='.repeat(60) + '\n');
    }
  }

  console.log('🎉 All examples completed!');
  console.log('\n📚 Next Steps:');
  console.log('1. Set up your Alpaca API credentials in environment variables');
  console.log('2. Start with paper trading to test your strategies');
  console.log('3. Run backtests on historical data to validate performance');
  console.log('4. Use the live trading connector for automated execution');
  console.log('5. Monitor Greeks and risk metrics in real-time');
  console.log('\n🎯 Happy Trading! Target: $200-250 daily profit with proper risk management.');
}

// Export examples for individual use
export {
  example1_BasicSetup,
  example2_GreeksCalculation,
  example3_PaperTrading,
  example4_Backtesting,
  example5_LiveTrading,
  example6_StrategyConfiguration,
  example7_GreeksMonitoring,
  runAllExamples
};

// Run examples if this file is executed directly
if (require.main === module) {
  runAllExamples().catch(console.error);
}
