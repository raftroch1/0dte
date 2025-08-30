/**
 * 🎯 Flyagonal Strategy - Type Definitions
 * ===============================================
 * 
 * TypeScript type definitions specific to the Flyagonal strategy.
 * These types extend the base strategy interfaces with strategy-specific parameters.
 * 
 * @fileoverview Type definitions for Flyagonal strategy
 * @author Steve Guns
 * @version 1.0.0
 * @created 2025-08-30
 */

import { StrategyConfig } from '../registry';

/**
 * Flyagonal Strategy-specific parameters
 * 
 * Controls the sophisticated Flyagonal algorithm that combines
 * a call broken wing butterfly with a put diagonal spread.
 * Based on Steve Guns' 96-97% win rate strategy.
 */
export interface FlyagonalStrategyParameters {
  /**
   * Minimum confidence level required to generate a signal (0-100)
   * @default 65
   */
  minConfidence: number;

  /**
   * Position size as percentage of account (0-1)
   * @default 0.03 (3% of account)
   */
  positionSize: number;

  /**
   * VIX range for optimal Flyagonal conditions
   */
  optimalVixRange: {
    min: number;
    max: number;
  };

  /**
   * Days before expiration to initiate trades
   */
  entryTiming: {
    min: number;
    max: number;
  };

  /**
   * Target holding period in days
   * @default 4.5
   */
  targetHoldingDays: number;

  /**
   * Butterfly strike spacing (SPX-specific)
   * @default { lower: 50, upper: 60 }
   */
  butterflyStrikeSpacing: { lower: number; upper: number };

  /**
   * Diagonal strike spacing (SPX-specific)
   * @default { percentBelow: 3, protection: 50 }
   */
  diagonalStrikeSpacing: { percentBelow: number; protection: number };

  /**
   * Maximum trend strength to allow entry
   * @default 0.05
   */
  maxTrendStrength: number;

  /**
   * Adjustment threshold (delta)
   * @default 0.15
   */
  adjustmentThreshold: number;

  // Add your specific parameters here:
  // Example for RSI-based strategy:
  // rsiPeriod: number;
  // oversoldThreshold: number;
  // overboughtThreshold: number;
  
  // Example for MACD-based strategy:
  // macdFastPeriod: number;
  // macdSlowPeriod: number;
  // macdSignalPeriod: number;
  
  // Example for Bollinger Bands strategy:
  // bbPeriod: number;
  // bbStdDev: number;
  
  // Example for moving average strategy:
  // shortMaPeriod: number;
  // longMaPeriod: number;
}

/**
 * Complete configuration interface for Flyagonal
 * 
 * Extends the base StrategyConfig with Flyagonal-specific parameters.
 */
export interface FlyagonalStrategyConfig extends StrategyConfig {
  /**
   * Flyagonal-specific parameters
   */
  parameters: FlyagonalStrategyParameters;

  /**
   * Enhanced risk management for Flyagonal
   */
  riskManagement: {
    maxPositionSize: number;
    stopLossPercent: number;
    takeProfitPercent: number;
    maxDailyLoss: number;
    maxTradesPerDay: number;
    maxConcurrentPositions: number;
    maxAdjustmentsPerPosition: number;
  };

  /**
   * Timeframe for strategy execution
   * Primary: '1Hour', Secondary: '4Hour', '1Day'
   */
  timeframe: string;

  /**
   * Whether the strategy is currently enabled
   */
  enabled: boolean;
}

/**
 * Flyagonal components structure
 * Represents the two parts of the Flyagonal strategy
 */
export interface FlyagonalComponents {
  butterfly: {
    type: 'CALL_BROKEN_WING';
    longLower: number;
    short: number;
    longUpper: number;
    expiration: Date;
  };
  diagonal: {
    type: 'PUT_DIAGONAL';
    longStrike: number;
    shortStrike: number;
    shortExpiration: Date;
    longExpiration: Date;
  };
}

/**
 * Flyagonal position tracking
 */
export interface FlyagonalPosition {
  id: string;
  entryTime: Date;
  components: FlyagonalComponents;
  currentDelta: number;
  currentTheta: number;
  currentVega: number;
  unrealizedPnL: number;
  adjustmentCount: number;
  status: 'OPEN' | 'CLOSED' | 'ADJUSTED';
}

/**
 * Market condition types that this strategy can handle
 */
export type FlyagonalStrategyMarketCondition = 
  | 'TRENDING_UP'
  | 'TRENDING_DOWN'
  | 'SIDEWAYS'
  | 'HIGH_VOLATILITY'
  | 'LOW_VOLATILITY'
  | 'BREAKOUT'
  | 'REVERSAL';

/**
 * Signal strength levels
 */
export type FlyagonalStrategySignalStrength = 
  | 'WEAK'
  | 'MODERATE'
  | 'STRONG'
  | 'VERY_STRONG';

/**
 * Strategy state for tracking internal conditions
 */
export interface FlyagonalStrategyState {
  /**
   * Last signal generation timestamp
   */
  lastSignalTime?: Date;

  /**
   * Current market condition assessment
   */
  marketCondition?: FlyagonalStrategyMarketCondition;

  /**
   * Recent signal count for rate limiting
   */
  recentSignalCount: number;

  /**
   * Strategy performance metrics
   */
  performance: {
    totalSignals: number;
    successfulSignals: number;
    failedSignals: number;
    averageReturn: number;
    lastUpdateTime: Date;
  };
}

/**
 * Custom indicator result interface (if strategy uses custom indicators)
 */
export interface FlyagonalStrategyIndicators {
  // TODO: Define custom indicator results if needed
  
  // Example custom indicators:
  // customRsi?: number;
  // customMacd?: {
  //   macd: number;
  //   signal: number;
  //   histogram: number;
  // };
  // customBollinger?: {
  //   upper: number;
  //   middle: number;
  //   lower: number;
  //   bandwidth: number;
  // };
}

/**
 * Strategy validation result
 */
export interface FlyagonalStrategyValidationResult {
  /**
   * Whether validation passed
   */
  isValid: boolean;

  /**
   * Validation error messages (if any)
   */
  errors: string[];

  /**
   * Validation warnings (if any)
   */
  warnings: string[];

  /**
   * Suggested parameter adjustments
   */
  suggestions?: Partial<FlyagonalStrategyParameters>;
}

/**
 * Backtest result specific to this strategy
 */
export interface FlyagonalStrategyBacktestResult {
  /**
   * Strategy name and version
   */
  strategy: {
    name: string;
    version: string;
  };

  /**
   * Test period
   */
  period: {
    start: Date;
    end: Date;
  };

  /**
   * Configuration used for backtest
   */
  config: FlyagonalStrategyConfig;

  /**
   * Performance metrics
   */
  performance: {
    totalReturn: number;
    totalReturnPercent: number;
    totalTrades: number;
    winRate: number;
    averageWin: number;
    averageLoss: number;
    maxDrawdown: number;
    sharpeRatio: number;
    profitFactor: number;
  };

  /**
   * Trade-by-trade results
   */
  trades: Array<{
    timestamp: Date;
    action: string;
    strike: number;
    premium: number;
    exitPrice: number;
    pnl: number;
    holdTime: number;
    confidence: number;
    reason: string;
  }>;

  /**
   * Strategy-specific metrics
   */
  strategyMetrics: {
    // TODO: Add strategy-specific performance metrics
    // Example:
    // averageConfidence: number;
    // signalFrequency: number;
    // marketConditionBreakdown: Record<FlyagonalStrategyMarketCondition, number>;
  };
}

// Types are already exported individually above
// Removed duplicate export block to fix TypeScript errors
