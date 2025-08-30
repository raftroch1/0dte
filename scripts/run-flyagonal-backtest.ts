#!/usr/bin/env ts-node

/**
 * 🎯 Flyagonal Strategy - Real Data Backtest Runner
 * ================================================
 * 
 * Comprehensive backtesting script for the fixed Flyagonal strategy.
 * Uses real Alpaca historical data as required by .cursorrules.
 * 
 * Features:
 * - Real Alpaca market and options data
 * - Enhanced Greeks calculations
 * - Realistic performance metrics
 * - Comprehensive reporting
 * - Data quality validation
 * 
 * @fileoverview Flyagonal strategy backtest runner
 * @author Trading System
 * @version 1.0.0
 * @created 2025-08-30
 */

import { FlyagonalStrategy } from '../src/strategies/flyagonal';
import { FlyagonalBacktestingAdapter } from '../src/strategies/flyagonal/backtesting-adapter';
import { FlyagonalRealDataIntegration, DEFAULT_FLYAGONAL_BACKTEST_CONFIG } from '../src/strategies/flyagonal/real-data-integration';
import { BacktestingEngine } from '../src/core/backtesting-engine';
import { AlpacaHistoricalDataFetcher } from '../src/data/alpaca-historical-data';
import { TradeLogger } from '../src/utils/trade-logger';
import { MarketData, OptionsChain, Position } from '../src/utils/types';

/**
 * Backtest configuration interface
 */
interface BacktestConfig {
  symbol: string;
  startDate: Date;
  endDate: Date;
  initialCapital: number;
  timeframe: string;
  includeOptionsData: boolean;
  includeVIXData: boolean;
  minDataQualityScore: number;
  outputDir: string;
}

/**
 * Backtest results interface
 */
interface BacktestResults {
  summary: {
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    winRate: number;
    totalReturn: number;
    totalReturnPercent: number;
    maxDrawdown: number;
    sharpeRatio: number;
    profitFactor: number;
    avgTradeReturn: number;
    avgWinningTrade: number;
    avgLosingTrade: number;
    maxConsecutiveWins: number;
    maxConsecutiveLosses: number;
  };
  trades: Array<{
    entryTime: Date;
    exitTime: Date;
    symbol: string;
    action: string;
    entryPrice: number;
    exitPrice: number;
    quantity: number;
    pnl: number;
    pnlPercent: number;
    holdingTime: number;
    confidence: number;
    vixLevel?: number;
    vixRegime?: string;
    reason: string;
  }>;
  dataQuality: {
    marketDataPoints: number;
    optionsDataPoints: number;
    dataCompleteness: number;
    avgLiquidityScore: number;
    missingDataDays: number;
  };
  performance: {
    monthlyReturns: Array<{ month: string; return: number; trades: number }>;
    drawdownPeriods: Array<{ start: Date; end: Date; maxDrawdown: number }>;
    vixRegimePerformance: Array<{ regime: string; trades: number; winRate: number; avgReturn: number }>;
  };
}

/**
 * Main backtest execution function
 */
async function runFlyagonalBacktest(config?: Partial<BacktestConfig>): Promise<BacktestResults> {
  console.log('🎯 Starting Flyagonal Strategy Backtest...\n');

  // Merge with default configuration
  const backtestConfig: BacktestConfig = {
    symbol: 'SPY',
    startDate: new Date('2024-01-01'),
    endDate: new Date('2024-01-31'),
    initialCapital: 25000,
    timeframe: '1Hour',
    includeOptionsData: true,
    includeVIXData: true,
    minDataQualityScore: 70,
    outputDir: './logs/backtests',
    ...config
  };

  console.log('📋 Backtest Configuration:');
  console.log(`   Symbol: ${backtestConfig.symbol}`);
  console.log(`   Period: ${backtestConfig.startDate.toDateString()} to ${backtestConfig.endDate.toDateString()}`);
  console.log(`   Initial Capital: $${backtestConfig.initialCapital.toLocaleString()}`);
  console.log(`   Timeframe: ${backtestConfig.timeframe}`);
  console.log(`   Include Options: ${backtestConfig.includeOptionsData}`);
  console.log(`   Include VIX: ${backtestConfig.includeVIXData}`);
  console.log(`   Min Data Quality: ${backtestConfig.minDataQualityScore}%\n`);

  try {
    // Step 1: Initialize strategy and components
    console.log('🏗️ Initializing Strategy Components...');
    const strategy = new FlyagonalStrategy();
    const adapter = new FlyagonalBacktestingAdapter();
    const tradeLogger = new TradeLogger();

    console.log(`   ✅ Strategy: ${strategy.name} v${strategy.version}`);
    console.log(`   ✅ Risk Level: ${strategy.getRiskLevel()}`);
    console.log(`   ✅ Required Indicators: ${strategy.getRequiredIndicators().join(', ')}`);

    // Step 2: Fetch real historical data
    console.log('\n📊 Fetching Real Historical Data...');
    const historicalData = await AlpacaHistoricalDataFetcher.fetchBacktestData({
      symbol: backtestConfig.symbol,
      startDate: backtestConfig.startDate,
      endDate: backtestConfig.endDate,
      timeframe: backtestConfig.timeframe,
      includeOptionsData: backtestConfig.includeOptionsData,
      includeVIXData: backtestConfig.includeVIXData
    });

    console.log(`   ✅ Market Data: ${historicalData.marketData.length} bars`);
    console.log(`   ✅ Options Data: ${historicalData.optionsData?.length || 0} trading days`);
    console.log(`   ✅ Data Quality: ${(historicalData.dataQuality.dataCompleteness * 100).toFixed(1)}%`);

    // Validate data quality
    if (historicalData.dataQuality.dataCompleteness < backtestConfig.minDataQualityScore / 100) {
      throw new Error(`Data quality ${(historicalData.dataQuality.dataCompleteness * 100).toFixed(1)}% below minimum ${backtestConfig.minDataQualityScore}%`);
    }

    // Step 3: Initialize backtesting engine
    console.log('\n🔧 Initializing Backtesting Engine...');
    const backtestingEngine = new BacktestingEngine({
      initialCapital: backtestConfig.initialCapital,
      startDate: backtestConfig.startDate,
      endDate: backtestConfig.endDate,
      timeframe: backtestConfig.timeframe,
      commissionPerTrade: 1.00, // $1 per option contract
      riskFreeRate: 0.05
    });

    // Step 4: Run backtest simulation
    console.log('\n🚀 Running Backtest Simulation...\n');
    
    const results = await runBacktestSimulation(
      backtestingEngine,
      strategy,
      adapter,
      historicalData.marketData,
      historicalData.optionsData || [],
      tradeLogger
    );

    // Step 5: Generate comprehensive results
    console.log('\n📈 Generating Results...');
    const backtestResults = await generateBacktestResults(
      results,
      historicalData,
      backtestConfig
    );

    // Step 6: Save results and generate reports
    console.log('\n💾 Saving Results...');
    await saveBacktestResults(backtestResults, backtestConfig);

    // Step 7: Display summary
    displayBacktestSummary(backtestResults);

    return backtestResults;

  } catch (error) {
    console.error('❌ Backtest failed:', error);
    throw error;
  }
}

/**
 * Run the actual backtest simulation
 */
async function runBacktestSimulation(
  engine: BacktestingEngine,
  strategy: FlyagonalStrategy,
  adapter: FlyagonalBacktestingAdapter,
  marketData: MarketData[],
  optionsData: Array<{ date: Date; chain: OptionsChain[] }>,
  tradeLogger: TradeLogger
): Promise<any> {
  
  const trades: any[] = [];
  const positions: Position[] = [];
  let currentCapital = engine['config'].initialCapital;
  
  console.log('📊 Processing market data...');
  
  // Process each market data point
  for (let i = 20; i < marketData.length; i++) { // Need 20 bars for indicators
    const currentBar = marketData[i];
    const historicalBars = marketData.slice(0, i + 1);
    
    // Find corresponding options data
    const currentDate = currentBar.timestamp.toDateString();
    const optionsForDay = optionsData.find(opt => 
      opt.date.toDateString() === currentDate
    );
    
    if (!optionsForDay || optionsForDay.chain.length === 0) {
      continue; // Skip days without options data
    }

    try {
      // Calculate data requirements for this price level
      const requirements = FlyagonalRealDataIntegration.calculateDataRequirements(
        currentBar.close,
        currentBar.timestamp
      );

      // Filter options for Flyagonal requirements
      const filteredOptions = FlyagonalRealDataIntegration.filterOptionsForFlyagonal(
        optionsForDay.chain,
        requirements
      );

      // Skip if data quality is insufficient
      if (filteredOptions.dataQuality.completeness < 0.8) {
        continue;
      }

      // Enhance options with Greeks
      const enhancedOptions = FlyagonalRealDataIntegration.enhanceWithGreeks(
        filteredOptions.flyagonalOptions,
        currentBar.close
      );

      // Generate signal using real data
      const signal = await strategy.generateSignal(historicalBars, enhancedOptions);

      if (signal) {
        console.log(`📅 ${currentBar.timestamp.toDateString()}: Signal generated - ${signal.action} (${signal.confidence}% confidence)`);
        
        // Create position using adapter
        const position = adapter.createPosition(signal, enhancedOptions, currentBar.close);
        
        if (position) {
          positions.push(position);
          
          // Log trade entry
          tradeLogger.logTrade({
            timestamp: currentBar.timestamp,
            symbol: position.symbol,
            action: 'ENTRY',
            type: position.type || 'FLYAGONAL_COMBO',
            strike: signal.targetStrike,
            quantity: position.quantity,
            price: position.entryPrice,
            premium: position.entryPrice,
            expiration: signal.expiration,
            confidence: signal.confidence,
            reason: signal.reason,
            vixLevel: signal.indicators?.vix,
            vixRegime: signal.indicators?.vixRegime,
            metadata: position.metadata
          });
        }
      }

      // Update existing positions
      for (let j = positions.length - 1; j >= 0; j--) {
        const position = positions[j];
        
        // Update position value
        const updatedPosition = adapter.updatePosition(
          position,
          currentBar,
          enhancedOptions
        );

        // Check exit conditions
        const holdingTime = (currentBar.timestamp.getTime() - position.entryTime.getTime()) / (1000 * 60); // minutes
        const shouldExit = adapter.shouldExit(updatedPosition, currentBar, enhancedOptions, holdingTime);

        if (shouldExit) {
          // Close position
          const pnl = updatedPosition.unrealizedPnL || 0;
          const pnlPercent = updatedPosition.unrealizedPnLPercent || 0;
          
          trades.push({
            entryTime: position.entryTime,
            exitTime: currentBar.timestamp,
            symbol: position.symbol,
            action: position.type || 'FLYAGONAL_COMBO',
            entryPrice: position.entryPrice,
            exitPrice: updatedPosition.currentPrice || position.entryPrice,
            quantity: position.quantity,
            pnl,
            pnlPercent,
            holdingTime: holdingTime / (24 * 60), // Convert to days
            confidence: position.metadata?.confidence || 0,
            vixLevel: position.metadata?.vixLevel,
            vixRegime: position.metadata?.vixRegime,
            reason: `Exit: ${pnl > 0 ? 'Profit target' : 'Stop loss'} hit`
          });

          // Update capital
          currentCapital += pnl;

          // Log trade exit
          tradeLogger.logTrade({
            timestamp: currentBar.timestamp,
            symbol: position.symbol,
            action: 'EXIT',
            type: position.type || 'FLYAGONAL_COMBO',
            strike: position.strike,
            quantity: position.quantity,
            price: updatedPosition.currentPrice || position.entryPrice,
            premium: updatedPosition.currentPrice || position.entryPrice,
            pnl,
            pnlPercent,
            reason: `Exit: ${pnl > 0 ? 'Profit' : 'Loss'}`,
            metadata: { holdingDays: holdingTime / (24 * 60) }
          });

          // Remove position
          positions.splice(j, 1);
          
          console.log(`💰 Position closed: ${pnl > 0 ? '+' : ''}$${pnl.toFixed(2)} (${pnlPercent.toFixed(1)}%)`);
        } else {
          // Update position in array
          positions[j] = updatedPosition;
        }
      }

    } catch (error) {
      console.warn(`⚠️ Error processing ${currentBar.timestamp.toDateString()}:`, error.message);
      continue;
    }

    // Progress indicator
    if (i % 50 === 0) {
      const progress = ((i / marketData.length) * 100).toFixed(1);
      console.log(`   Progress: ${progress}% (${trades.length} trades completed)`);
    }
  }

  // Close any remaining positions
  for (const position of positions) {
    const finalBar = marketData[marketData.length - 1];
    const pnl = position.unrealizedPnL || 0;
    
    trades.push({
      entryTime: position.entryTime,
      exitTime: finalBar.timestamp,
      symbol: position.symbol,
      action: position.type || 'FLYAGONAL_COMBO',
      entryPrice: position.entryPrice,
      exitPrice: position.currentPrice || position.entryPrice,
      quantity: position.quantity,
      pnl,
      pnlPercent: position.unrealizedPnLPercent || 0,
      holdingTime: (finalBar.timestamp.getTime() - position.entryTime.getTime()) / (1000 * 60 * 24),
      confidence: position.metadata?.confidence || 0,
      vixLevel: position.metadata?.vixLevel,
      vixRegime: position.metadata?.vixRegime,
      reason: 'End of backtest period'
    });

    currentCapital += pnl;
  }

  return {
    trades,
    finalCapital: currentCapital,
    initialCapital: engine['config'].initialCapital
  };
}

/**
 * Generate comprehensive backtest results
 */
async function generateBacktestResults(
  simulationResults: any,
  historicalData: any,
  config: BacktestConfig
): Promise<BacktestResults> {
  
  const { trades, finalCapital, initialCapital } = simulationResults;
  
  // Calculate basic metrics
  const totalTrades = trades.length;
  const winningTrades = trades.filter((t: any) => t.pnl > 0).length;
  const losingTrades = totalTrades - winningTrades;
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;
  
  const totalReturn = finalCapital - initialCapital;
  const totalReturnPercent = (totalReturn / initialCapital) * 100;
  
  const avgTradeReturn = totalTrades > 0 ? totalReturn / totalTrades : 0;
  const avgWinningTrade = winningTrades > 0 ? 
    trades.filter((t: any) => t.pnl > 0).reduce((sum: number, t: any) => sum + t.pnl, 0) / winningTrades : 0;
  const avgLosingTrade = losingTrades > 0 ? 
    trades.filter((t: any) => t.pnl < 0).reduce((sum: number, t: any) => sum + t.pnl, 0) / losingTrades : 0;

  // Calculate drawdown
  let maxDrawdown = 0;
  let peak = initialCapital;
  let currentCapital = initialCapital;
  
  for (const trade of trades) {
    currentCapital += trade.pnl;
    if (currentCapital > peak) {
      peak = currentCapital;
    }
    const drawdown = (peak - currentCapital) / peak * 100;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }

  // Calculate Sharpe ratio (simplified)
  const returns = trades.map((t: any) => t.pnlPercent);
  const avgReturn = returns.reduce((sum: number, r: number) => sum + r, 0) / returns.length;
  const returnStdDev = Math.sqrt(returns.reduce((sum: number, r: number) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length);
  const sharpeRatio = returnStdDev > 0 ? avgReturn / returnStdDev : 0;

  // Calculate profit factor
  const grossProfit = trades.filter((t: any) => t.pnl > 0).reduce((sum: number, t: any) => sum + t.pnl, 0);
  const grossLoss = Math.abs(trades.filter((t: any) => t.pnl < 0).reduce((sum: number, t: any) => sum + t.pnl, 0));
  const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 999 : 0;

  // Calculate consecutive wins/losses
  let maxConsecutiveWins = 0;
  let maxConsecutiveLosses = 0;
  let currentWinStreak = 0;
  let currentLossStreak = 0;

  for (const trade of trades) {
    if (trade.pnl > 0) {
      currentWinStreak++;
      currentLossStreak = 0;
      maxConsecutiveWins = Math.max(maxConsecutiveWins, currentWinStreak);
    } else {
      currentLossStreak++;
      currentWinStreak = 0;
      maxConsecutiveLosses = Math.max(maxConsecutiveLosses, currentLossStreak);
    }
  }

  // VIX regime performance
  const vixRegimes = ['LOW', 'OPTIMAL_LOW', 'OPTIMAL_MEDIUM', 'OPTIMAL_HIGH', 'HIGH'];
  const vixRegimePerformance = vixRegimes.map(regime => {
    const regimeTrades = trades.filter((t: any) => t.vixRegime === regime);
    const regimeWins = regimeTrades.filter((t: any) => t.pnl > 0).length;
    const regimeWinRate = regimeTrades.length > 0 ? (regimeWins / regimeTrades.length) * 100 : 0;
    const regimeAvgReturn = regimeTrades.length > 0 ? 
      regimeTrades.reduce((sum: number, t: any) => sum + t.pnl, 0) / regimeTrades.length : 0;
    
    return {
      regime,
      trades: regimeTrades.length,
      winRate: regimeWinRate,
      avgReturn: regimeAvgReturn
    };
  });

  return {
    summary: {
      totalTrades,
      winningTrades,
      losingTrades,
      winRate,
      totalReturn,
      totalReturnPercent,
      maxDrawdown,
      sharpeRatio,
      profitFactor,
      avgTradeReturn,
      avgWinningTrade,
      avgLosingTrade,
      maxConsecutiveWins,
      maxConsecutiveLosses
    },
    trades,
    dataQuality: {
      marketDataPoints: historicalData.marketData.length,
      optionsDataPoints: historicalData.optionsData?.length || 0,
      dataCompleteness: historicalData.dataQuality.dataCompleteness,
      avgLiquidityScore: historicalData.dataQuality.avgLiquidityScore || 0,
      missingDataDays: historicalData.dataQuality.missingDays?.length || 0
    },
    performance: {
      monthlyReturns: [], // TODO: Calculate monthly returns
      drawdownPeriods: [], // TODO: Calculate drawdown periods
      vixRegimePerformance
    }
  };
}

/**
 * Save backtest results to files
 */
async function saveBacktestResults(results: BacktestResults, config: BacktestConfig): Promise<void> {
  const fs = require('fs').promises;
  const path = require('path');
  
  // Ensure output directory exists
  await fs.mkdir(config.outputDir, { recursive: true });
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
  const baseFilename = `flyagonal_backtest_${config.symbol}_${timestamp}`;
  
  // Save detailed results as JSON
  const jsonPath = path.join(config.outputDir, `${baseFilename}.json`);
  await fs.writeFile(jsonPath, JSON.stringify(results, null, 2));
  
  // Save trades as CSV
  const csvPath = path.join(config.outputDir, `${baseFilename}_trades.csv`);
  const csvHeader = 'Entry Time,Exit Time,Symbol,Action,Entry Price,Exit Price,Quantity,PnL,PnL %,Holding Days,Confidence,VIX Level,VIX Regime,Reason\n';
  const csvRows = results.trades.map(trade => 
    `${trade.entryTime.toISOString()},${trade.exitTime.toISOString()},${trade.symbol},${trade.action},${trade.entryPrice},${trade.exitPrice},${trade.quantity},${trade.pnl.toFixed(2)},${trade.pnlPercent.toFixed(2)},${trade.holdingTime.toFixed(2)},${trade.confidence},${trade.vixLevel || ''},${trade.vixRegime || ''},${trade.reason}`
  ).join('\n');
  await fs.writeFile(csvPath, csvHeader + csvRows);
  
  console.log(`   ✅ Results saved to: ${jsonPath}`);
  console.log(`   ✅ Trades saved to: ${csvPath}`);
}

/**
 * Display backtest summary
 */
function displayBacktestSummary(results: BacktestResults): void {
  console.log('\n🎯 FLYAGONAL STRATEGY BACKTEST RESULTS');
  console.log('=====================================\n');
  
  console.log('📊 PERFORMANCE SUMMARY:');
  console.log(`   Total Trades: ${results.summary.totalTrades}`);
  console.log(`   Winning Trades: ${results.summary.winningTrades}`);
  console.log(`   Losing Trades: ${results.summary.losingTrades}`);
  console.log(`   Win Rate: ${results.summary.winRate.toFixed(1)}%`);
  console.log(`   Total Return: $${results.summary.totalReturn.toFixed(2)} (${results.summary.totalReturnPercent.toFixed(2)}%)`);
  console.log(`   Max Drawdown: ${results.summary.maxDrawdown.toFixed(2)}%`);
  console.log(`   Sharpe Ratio: ${results.summary.sharpeRatio.toFixed(2)}`);
  console.log(`   Profit Factor: ${results.summary.profitFactor.toFixed(2)}`);
  
  console.log('\n💰 TRADE ANALYSIS:');
  console.log(`   Average Trade: $${results.summary.avgTradeReturn.toFixed(2)}`);
  console.log(`   Average Winner: $${results.summary.avgWinningTrade.toFixed(2)}`);
  console.log(`   Average Loser: $${results.summary.avgLosingTrade.toFixed(2)}`);
  console.log(`   Max Consecutive Wins: ${results.summary.maxConsecutiveWins}`);
  console.log(`   Max Consecutive Losses: ${results.summary.maxConsecutiveLosses}`);
  
  console.log('\n📈 VIX REGIME PERFORMANCE:');
  results.performance.vixRegimePerformance.forEach(regime => {
    if (regime.trades > 0) {
      console.log(`   ${regime.regime}: ${regime.trades} trades, ${regime.winRate.toFixed(1)}% win rate, $${regime.avgReturn.toFixed(2)} avg`);
    }
  });
  
  console.log('\n📊 DATA QUALITY:');
  console.log(`   Market Data Points: ${results.dataQuality.marketDataPoints}`);
  console.log(`   Options Data Points: ${results.dataQuality.optionsDataPoints}`);
  console.log(`   Data Completeness: ${(results.dataQuality.dataCompleteness * 100).toFixed(1)}%`);
  console.log(`   Avg Liquidity Score: ${results.dataQuality.avgLiquidityScore.toFixed(1)}`);
  
  // Performance assessment
  console.log('\n🎯 PERFORMANCE ASSESSMENT:');
  if (results.summary.winRate >= 65 && results.summary.winRate <= 75) {
    console.log('   ✅ Win rate within realistic range (65-75%)');
  } else if (results.summary.winRate > 75) {
    console.log('   ⚠️ Win rate higher than expected - may indicate overfitting');
  } else {
    console.log('   ⚠️ Win rate below expected range - strategy may need adjustment');
  }
  
  if (results.summary.profitFactor >= 1.2 && results.summary.profitFactor <= 2.0) {
    console.log('   ✅ Profit factor within healthy range (1.2-2.0)');
  } else if (results.summary.profitFactor > 2.0) {
    console.log('   ⚠️ Profit factor very high - may indicate overfitting');
  } else {
    console.log('   ❌ Profit factor below 1.2 - strategy not profitable enough');
  }
  
  if (results.summary.maxDrawdown <= 25) {
    console.log('   ✅ Maximum drawdown within acceptable range (<25%)');
  } else {
    console.log('   ⚠️ Maximum drawdown high - consider reducing position sizes');
  }
}

/**
 * Run backtest with command line arguments or default configuration
 */
async function main(): Promise<void> {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const config: Partial<BacktestConfig> = {};
    
    for (let i = 0; i < args.length; i += 2) {
      const key = args[i]?.replace('--', '');
      const value = args[i + 1];
      
      switch (key) {
        case 'symbol':
          config.symbol = value;
          break;
        case 'start':
          config.startDate = new Date(value);
          break;
        case 'end':
          config.endDate = new Date(value);
          break;
        case 'capital':
          config.initialCapital = parseInt(value);
          break;
        case 'timeframe':
          config.timeframe = value;
          break;
      }
    }
    
    // Run backtest
    const results = await runFlyagonalBacktest(config);
    
    console.log('\n✅ Backtest completed successfully!');
    process.exit(0);
    
  } catch (error) {
    console.error('\n❌ Backtest failed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

export { runFlyagonalBacktest, BacktestConfig, BacktestResults };
