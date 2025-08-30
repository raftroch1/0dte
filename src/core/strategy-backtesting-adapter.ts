/**
 * 🎯 Strategy-Specific Backtesting Framework
 * ==========================================
 * 
 * This framework allows each strategy to define its own backtesting requirements
 * while maintaining the core real data fetching and account management.
 * 
 * Key Benefits:
 * - Strategy-specific options data generation
 * - Custom position management for complex strategies
 * - Strategy-specific performance metrics
 * - Maintains real data foundation
 * 
 * @fileoverview Strategy backtesting adapter interface and base classes
 * @author Trading System Architecture
 * @version 1.0.0
 * @created 2025-08-30
 */

import { MarketData, OptionsChain, TradeSignal, Position } from '../utils/types';

/**
 * Strategy-specific performance metrics interface
 * 
 * Each strategy can define its own metrics while maintaining common ones
 */
export interface StrategySpecificMetrics {
  // Common metrics (all strategies)
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnL: number;
  avgTradeReturn: number;
  
  // Strategy-specific metrics (extensible)
  [key: string]: any;
}

/**
 * VIX regime performance tracking
 * Simple metric as requested by user
 */
export interface VixRegimeMetrics {
  regime: string; // e.g., 'OPTIMAL_LOW', 'HIGH', etc.
  trades: number;
  wins: number;
  losses: number;
  winRate: number;
  avgReturn: number;
}

/**
 * Profit zone efficiency tracking
 * Simple metric for strategies with defined profit zones
 */
export interface ProfitZoneMetrics {
  totalSignals: number;
  signalsInProfitZone: number;
  profitZoneEfficiency: number; // percentage
  avgDistanceFromOptimal: number; // points
}

/**
 * Strategy Backtesting Adapter Interface
 * 
 * Each strategy implements this interface to customize its backtesting behavior
 * while the core engine handles real data fetching and basic execution.
 */
export interface StrategyBacktestingAdapter {
  /**
   * Strategy name (must match strategy registry)
   */
  readonly strategyName: string;
  
  /**
   * Generate strategy-specific options data
   * 
   * This is where each strategy defines exactly what options it needs.
   * For example:
   * - Flyagonal: Complex multi-leg options with specific strikes
   * - Simple Momentum: Basic ATM/OTM calls and puts
   * 
   * @param marketData Historical market data
   * @param currentPrice Current underlying price
   * @param currentTime Current timestamp for expiration calculations
   * @returns Array of options contracts tailored to strategy needs
   */
  generateOptionsData(
    marketData: MarketData[], 
    currentPrice: number, 
    currentTime: Date
  ): OptionsChain[];
  
  /**
   * Create strategy-specific position from signal
   * 
   * Handles the complexity of different position types:
   * - Simple strategies: Single option position
   * - Complex strategies: Multi-leg positions with multiple contracts
   * 
   * @param signal Trading signal from strategy
   * @param options Available options contracts
   * @param currentPrice Current underlying price
   * @returns Position object or null if cannot create position
   */
  createPosition(
    signal: TradeSignal, 
    options: OptionsChain[], 
    currentPrice: number
  ): Position | null;
  
  /**
   * Update position value based on current market conditions
   * 
   * @param position Current position
   * @param marketData Current market data
   * @param options Current options data
   * @returns Updated position
   */
  updatePosition(
    position: Position, 
    marketData: MarketData, 
    options: OptionsChain[]
  ): Position;
  
  /**
   * Determine if position should be exited
   * 
   * Strategy-specific exit logic beyond basic stop loss/take profit
   * 
   * @param position Current position
   * @param marketData Current market data
   * @param options Current options data
   * @param holdingTime Time position has been held (minutes)
   * @returns true if position should be exited
   */
  shouldExit(
    position: Position, 
    marketData: MarketData, 
    options: OptionsChain[], 
    holdingTime: number
  ): boolean;
  
  /**
   * Calculate strategy-specific performance metrics
   * 
   * @param trades Array of completed trades
   * @param signals Array of all signals generated (including those that didn't result in trades)
   * @returns Strategy-specific metrics including VIX regime and profit zone efficiency
   */
  calculateStrategyMetrics(
    trades: any[], 
    signals: TradeSignal[]
  ): StrategySpecificMetrics;
}

/**
 * Base Strategy Backtesting Adapter
 * 
 * Provides common functionality that most strategies can use
 * Strategies can extend this class and override specific methods
 */
export abstract class BaseStrategyBacktestingAdapter implements StrategyBacktestingAdapter {
  abstract readonly strategyName: string;
  
  /**
   * ENHANCED: Calculate option price using proper Black-Scholes model
   * Uses GreeksSimulator for accurate pricing in backtesting
   */
  protected calculateOptionPrice(
    underlyingPrice: number,
    strike: number,
    timeToExpiration: number, // in years
    volatility: number = 0.2, // default 20% IV
    optionType: 'CALL' | 'PUT' = 'CALL'
  ): number {
    // Use proper Black-Scholes calculation via GreeksSimulator
    try {
      // Import GreeksSimulator dynamically to avoid circular dependencies
      const { GreeksSimulator } = require('../data/greeks-simulator');
      
      const result = GreeksSimulator.calculateOptionPrice({
        underlyingPrice,
        strikePrice: strike,
        timeToExpiration,
        riskFreeRate: 0.05, // 5% risk-free rate (typical)
        volatility,
        optionType: optionType.toLowerCase() as 'call' | 'put',
        dividendYield: 0 // Assume no dividends for SPX options
      });
      
      return Math.max(0.01, result.theoreticalPrice);
      
    } catch (error) {
      console.warn('⚠️ Black-Scholes calculation failed, using fallback method:', error);
      
      // Fallback to improved approximation if GreeksSimulator fails
      const intrinsicValue = optionType === 'CALL' 
        ? Math.max(0, underlyingPrice - strike)
        : Math.max(0, strike - underlyingPrice);
      
      // Improved time value calculation using more realistic formula
      const moneyness = underlyingPrice / strike;
      const timeValue = underlyingPrice * volatility * Math.sqrt(timeToExpiration) * 
                       (optionType === 'CALL' ? 
                         Math.max(0.1, Math.min(1.0, moneyness)) : 
                         Math.max(0.1, Math.min(1.0, 2 - moneyness))) * 0.4;
      
      return Math.max(0.01, intrinsicValue + timeValue);
    }
  }
  
  /**
   * Helper method to calculate days to expiration
   */
  protected calculateDaysToExpiration(currentTime: Date, expiration: Date): number {
    const msPerDay = 24 * 60 * 60 * 1000;
    return Math.max(0, (expiration.getTime() - currentTime.getTime()) / msPerDay);
  }
  
  /**
   * Helper method to calculate VIX regime metrics
   */
  protected calculateVixRegimeMetrics(trades: any[]): VixRegimeMetrics[] {
    const regimeMap = new Map<string, { trades: number; wins: number; totalReturn: number }>();
    
    trades.forEach(trade => {
      const regime = trade.signal?.indicators?.vixRegime || 'UNKNOWN';
      const isWin = (trade.pnl || 0) > 0;
      
      if (!regimeMap.has(regime)) {
        regimeMap.set(regime, { trades: 0, wins: 0, totalReturn: 0 });
      }
      
      const regimeData = regimeMap.get(regime)!;
      regimeData.trades++;
      if (isWin) regimeData.wins++;
      regimeData.totalReturn += (trade.pnl || 0);
    });
    
    return Array.from(regimeMap.entries()).map(([regime, data]) => ({
      regime,
      trades: data.trades,
      wins: data.wins,
      losses: data.trades - data.wins,
      winRate: data.trades > 0 ? (data.wins / data.trades) * 100 : 0,
      avgReturn: data.trades > 0 ? data.totalReturn / data.trades : 0
    }));
  }
  
  /**
   * Helper method to calculate profit zone efficiency
   */
  protected calculateProfitZoneEfficiency(signals: TradeSignal[]): ProfitZoneMetrics {
    const signalsWithProfitZone = signals.filter(s => s.indicators?.profitZoneWidth);
    
    if (signalsWithProfitZone.length === 0) {
      return {
        totalSignals: signals.length,
        signalsInProfitZone: 0,
        profitZoneEfficiency: 0,
        avgDistanceFromOptimal: 0
      };
    }
    
    const inProfitZone = signalsWithProfitZone.filter(s => 
      s.indicators?.profitZoneWidth && s.indicators.profitZoneWidth >= 200
    );
    
    return {
      totalSignals: signals.length,
      signalsInProfitZone: inProfitZone.length,
      profitZoneEfficiency: (inProfitZone.length / signalsWithProfitZone.length) * 100,
      avgDistanceFromOptimal: signalsWithProfitZone.reduce((sum, s) => 
        sum + (s.indicators?.profitZoneWidth || 0), 0) / signalsWithProfitZone.length
    };
  }
  
  // Abstract methods that each strategy must implement
  abstract generateOptionsData(marketData: MarketData[], currentPrice: number, currentTime: Date): OptionsChain[];
  abstract createPosition(signal: TradeSignal, options: OptionsChain[], currentPrice: number): Position | null;
  abstract updatePosition(position: Position, marketData: MarketData, options: OptionsChain[]): Position;
  abstract shouldExit(position: Position, marketData: MarketData, options: OptionsChain[], holdingTime: number): boolean;
  abstract calculateStrategyMetrics(trades: any[], signals: TradeSignal[]): StrategySpecificMetrics;
}
