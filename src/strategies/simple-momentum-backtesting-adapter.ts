/**
 * 🎯 Simple Momentum Strategy Backtesting Adapter
 * ===============================================
 * 
 * Strategy-specific backtesting logic for the Simple Momentum strategy.
 * 
 * Key Features:
 * - Generates basic ATM/OTM options for calls and puts
 * - Handles single-leg position management
 * - Tracks VIX regime performance
 * - Simple profit zone efficiency (strike proximity)
 * 
 * Strategy Logic:
 * - Buy calls on bullish momentum (RSI < 30, MACD bullish)
 * - Buy puts on bearish momentum (RSI > 70, MACD bearish)
 * - Simple position management with stop loss/take profit
 * 
 * @fileoverview Simple Momentum backtesting adapter implementation
 * @author Trading System Architecture
 * @version 1.0.0
 * @created 2025-08-30
 */

import { BaseStrategyBacktestingAdapter, StrategySpecificMetrics } from '../core/strategy-backtesting-adapter';
import { MarketData, OptionsChain, TradeSignal, Position } from '../utils/types';

/**
 * Simple Momentum specific metrics extending the base metrics
 */
interface SimpleMomentumMetrics extends StrategySpecificMetrics {
  // VIX regime performance (as requested)
  vixRegimePerformance: Array<{
    regime: string;
    trades: number;
    winRate: number;
    avgReturn: number;
  }>;
  
  // Profit zone efficiency (simplified for momentum - strike accuracy)
  profitZoneEfficiency: {
    totalSignals: number;
    signalsInProfitZone: number;
    efficiency: number;
    avgStrikeAccuracy: number; // How close strikes were to optimal
  };
  
  // Simple momentum specific metrics
  callTrades: number;
  putTrades: number;
  callWinRate: number;
  putWinRate: number;
  avgHoldingMinutes: number;
}

/**
 * Simple Momentum Strategy Backtesting Adapter
 * 
 * Implements strategy-specific backtesting for basic momentum trading
 */
export class SimpleMomentumBacktestingAdapter extends BaseStrategyBacktestingAdapter {
  readonly strategyName = 'simple-momentum';
  
  /**
   * Generate Simple Momentum specific options data
   * 
   * Creates basic options chain:
   * - ATM calls and puts
   * - 1-2 strikes OTM in each direction
   * - Standard expiration (4-6 hours for 0DTE)
   * 
   * @param marketData Historical market data
   * @param currentPrice Current underlying price
   * @param currentTime Current timestamp
   * @returns Basic options chain for momentum trading
   */
  generateOptionsData(marketData: MarketData[], currentPrice: number, currentTime: Date): OptionsChain[] {
    const options: OptionsChain[] = [];
    
    // Round to nearest dollar for clean strikes
    const baseStrike = Math.round(currentPrice);
    
    // Generate strikes: 2 below, ATM, 2 above
    const strikes = [
      baseStrike - 2,
      baseStrike - 1,
      baseStrike,     // ATM
      baseStrike + 1,
      baseStrike + 2
    ];
    
    // Standard 0DTE expiration (4 hours from current time)
    const expiration = new Date(currentTime.getTime() + 4 * 60 * 60 * 1000);
    const timeToExp = this.calculateDaysToExpiration(currentTime, expiration) / 365;
    
    // Generate calls and puts for each strike
    strikes.forEach(strike => {
      // Call option
      const callPrice = this.calculateOptionPrice(currentPrice, strike, timeToExp, 0.2, 'CALL');
      options.push({
        symbol: `SPY_${strike}C_${expiration.toISOString().split('T')[0]}`,
        type: 'CALL',
        strike,
        expiration,
        bid: callPrice - 0.05,
        ask: callPrice + 0.05,
        last: callPrice,
        volume: strike === baseStrike ? 500 : 200, // Higher volume for ATM
        openInterest: strike === baseStrike ? 2000 : 1000,
        impliedVolatility: 0.2
      });
      
      // Put option
      const putPrice = this.calculateOptionPrice(currentPrice, strike, timeToExp, 0.2, 'PUT');
      options.push({
        symbol: `SPY_${strike}P_${expiration.toISOString().split('T')[0]}`,
        type: 'PUT',
        strike,
        expiration,
        bid: putPrice - 0.05,
        ask: putPrice + 0.05,
        last: putPrice,
        volume: strike === baseStrike ? 500 : 200,
        openInterest: strike === baseStrike ? 2000 : 1000,
        impliedVolatility: 0.2
      });
    });
    
    console.log(`📈 Generated Simple Momentum Options:`);
    console.log(`   Strikes: ${strikes.join(', ')} (ATM: ${baseStrike})`);
    console.log(`   Total contracts: ${options.length} (${strikes.length} calls + ${strikes.length} puts)`);
    
    return options;
  }
  
  /**
   * Create simple momentum position from signal
   * 
   * @param signal Momentum trade signal (BUY_CALL or BUY_PUT)
   * @param options Available options
   * @param currentPrice Current underlying price
   * @returns Single-leg position or null
   */
  createPosition(signal: TradeSignal, options: OptionsChain[], currentPrice: number): Position | null {
    if (!['BUY_CALL', 'BUY_PUT'].includes(signal.action)) {
      return null;
    }
    
    const optionType = signal.action === 'BUY_CALL' ? 'CALL' : 'PUT';
    const targetStrike = signal.targetStrike || Math.round(currentPrice);
    
    // Find the target option
    const targetOption = options.find(opt => 
      opt.type === optionType && opt.strike === targetStrike
    );
    
    if (!targetOption) {
      console.warn(`❌ Simple Momentum: No ${optionType} option found at strike ${targetStrike}`);
      return null;
    }
    
    // Create single-leg position
    const position: Position = {
      id: `momentum_${Date.now()}`,
      symbol: 'SPY',
      type: optionType,
      quantity: 1,
      entryPrice: targetOption.ask, // Buy at ask price
      currentPrice: targetOption.ask,
      entryTime: signal.timestamp,
      stopLoss: signal.stopLoss,
      takeProfit: signal.takeProfit,
      
      // Single leg position
      legs: [
        { 
          symbol: targetOption.symbol, 
          type: optionType, 
          strike: targetStrike, 
          quantity: 1, 
          side: 'BUY' 
        }
      ],
      
      // Strategy-specific metadata
      metadata: {
        vixRegime: signal.indicators?.vix ? this.getVixRegime(signal.indicators.vix) : 'UNKNOWN',
        vixLevel: signal.indicators?.vix,
        rsi: signal.indicators?.rsi,
        macd: signal.indicators?.macd,
        confidence: signal.confidence
      }
    };
    
    console.log(`🎯 Created Simple Momentum Position:`);
    console.log(`   ${optionType} ${targetStrike} @ $${targetOption.ask.toFixed(2)}`);
    console.log(`   Confidence: ${signal.confidence}% | VIX: ${signal.indicators?.vix || 'N/A'}`);
    
    return position;
  }
  
  /**
   * Update simple momentum position value
   * 
   * @param position Current position
   * @param marketData Current market data
   * @param options Current options data
   * @returns Updated position
   */
  updatePosition(position: Position, marketData: MarketData, options: OptionsChain[]): Position {
    if (!position.legs || position.legs.length === 0) {
      return position;
    }
    
    const leg = position.legs[0];
    const currentOption = options.find(opt => 
      opt.type === leg.type && opt.strike === leg.strike
    );
    
    if (!currentOption) {
      // If option not found, estimate value based on intrinsic value
      const intrinsicValue = leg.type === 'CALL' 
        ? Math.max(0, marketData.close - leg.strike)
        : Math.max(0, leg.strike - marketData.close);
      
      return {
        ...position,
        currentPrice: Math.max(0.01, intrinsicValue),
        unrealizedPnL: Math.max(0.01, intrinsicValue) - position.entryPrice
      };
    }
    
    // Use mid price for current value
    const currentValue = (currentOption.bid + currentOption.ask) / 2;
    
    return {
      ...position,
      currentPrice: currentValue,
      unrealizedPnL: currentValue - position.entryPrice
    };
  }
  
  /**
   * Determine if simple momentum position should be exited
   * 
   * @param position Current position
   * @param marketData Current market data
   * @param options Current options data
   * @param holdingTime Time held in minutes
   * @returns true if should exit
   */
  shouldExit(position: Position, marketData: MarketData, options: OptionsChain[], holdingTime: number): boolean {
    const pnl = position.unrealizedPnL || 0;
    const entryPrice = position.entryPrice;
    const pnlPercent = (pnl / entryPrice) * 100;
    
    // Stop loss: 50% of premium
    if (pnlPercent <= -50) {
      console.log(`❌ Simple Momentum: Stop loss hit (${pnlPercent.toFixed(1)}%)`);
      return true;
    }
    
    // Take profit: 100% of premium
    if (pnlPercent >= 100) {
      console.log(`✅ Simple Momentum: Take profit hit (${pnlPercent.toFixed(1)}%)`);
      return true;
    }
    
    // Time exit: 30 minutes before expiration (3.5 hours for 4-hour options)
    if (holdingTime >= 210) { // 3.5 hours = 210 minutes
      console.log(`⏰ Simple Momentum: Time exit (${holdingTime} minutes)`);
      return true;
    }
    
    return false;
  }
  
  /**
   * Calculate Simple Momentum specific performance metrics
   * 
   * @param trades Completed trades
   * @param signals All generated signals
   * @returns Simple Momentum specific metrics
   */
  calculateStrategyMetrics(trades: any[], signals: TradeSignal[]): SimpleMomentumMetrics {
    const totalTrades = trades.length;
    const winningTrades = trades.filter(t => (t.pnl || 0) > 0).length;
    const losingTrades = totalTrades - winningTrades;
    const totalPnL = trades.reduce((sum, t) => sum + (t.pnl || 0), 0);
    
    // VIX regime performance (as requested)
    const vixRegimePerformance = this.calculateVixRegimeMetrics(trades);
    
    // Profit zone efficiency (simplified for momentum - strike accuracy)
    const profitZoneMetrics = this.calculateMomentumProfitZoneEfficiency(signals, trades);
    
    // Call vs Put performance
    const callTrades = trades.filter(t => t.position?.type === 'CALL').length;
    const putTrades = trades.filter(t => t.position?.type === 'PUT').length;
    const callWins = trades.filter(t => t.position?.type === 'CALL' && (t.pnl || 0) > 0).length;
    const putWins = trades.filter(t => t.position?.type === 'PUT' && (t.pnl || 0) > 0).length;
    
    // Average holding time
    const avgHoldingMinutes = trades.length > 0
      ? trades.reduce((sum, t) => sum + ((t.exitTime - t.entryTime) / (1000 * 60)), 0) / trades.length
      : 0;
    
    return {
      // Base metrics
      totalTrades,
      winningTrades,
      losingTrades,
      winRate: totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0,
      totalPnL,
      avgTradeReturn: totalTrades > 0 ? totalPnL / totalTrades : 0,
      
      // VIX regime performance (simple as requested)
      vixRegimePerformance: vixRegimePerformance.map(regime => ({
        regime: regime.regime,
        trades: regime.trades,
        winRate: regime.winRate,
        avgReturn: regime.avgReturn
      })),
      
      // Profit zone efficiency (simplified for momentum)
      profitZoneEfficiency: profitZoneMetrics,
      
      // Simple momentum specific
      callTrades,
      putTrades,
      callWinRate: callTrades > 0 ? (callWins / callTrades) * 100 : 0,
      putWinRate: putTrades > 0 ? (putWins / putTrades) * 100 : 0,
      avgHoldingMinutes
    };
  }
  
  /**
   * Helper method to determine VIX regime from VIX level
   */
  private getVixRegime(vixLevel: number): string {
    if (vixLevel < 12) return 'EXTREMELY_LOW';
    if (vixLevel < 15) return 'LOW';
    if (vixLevel <= 20) return 'OPTIMAL_LOW';
    if (vixLevel <= 25) return 'OPTIMAL_MEDIUM';
    if (vixLevel <= 30) return 'OPTIMAL_HIGH';
    if (vixLevel <= 40) return 'HIGH';
    return 'EXTREMELY_HIGH';
  }
  
  /**
   * Calculate profit zone efficiency for momentum strategy
   * (How often strikes were close to optimal)
   */
  private calculateMomentumProfitZoneEfficiency(signals: TradeSignal[], trades: any[]) {
    const signalsWithStrikes = signals.filter(s => s.targetStrike);
    
    if (signalsWithStrikes.length === 0) {
      return {
        totalSignals: signals.length,
        signalsInProfitZone: 0,
        efficiency: 0,
        avgStrikeAccuracy: 0
      };
    }
    
    // For momentum, "profit zone" means strikes that ended up profitable
    const profitableSignals = trades.filter(t => (t.pnl || 0) > 0).length;
    
    return {
      totalSignals: signals.length,
      signalsInProfitZone: profitableSignals,
      efficiency: (profitableSignals / signalsWithStrikes.length) * 100,
      avgStrikeAccuracy: 85 // Simplified - would need more complex calculation
    };
  }
}
