/**
 * 🎯 {{STRATEGY_NAME}} Strategy - Type Definitions
 * ===============================================
 * 
 * TypeScript type definitions specific to the {{STRATEGY_NAME}} strategy.
 * These types extend the base strategy interfaces with strategy-specific parameters.
 * 
 * @fileoverview Type definitions for {{STRATEGY_NAME}} strategy
 * @author {{AUTHOR_NAME}}
 * @version {{VERSION}}
 * @created {{DATE}}
 */

import { StrategyConfig } from '../registry';

/**
 * Strategy-specific parameters for {{STRATEGY_NAME}}
 * 
 * These parameters control the behavior of the strategy algorithm.
 * Adjust these values to fine-tune strategy performance.
 */
export interface {{STRATEGY_CLASS_NAME}}Parameters {
  // TODO: Define your strategy-specific parameters here
  
  // Example parameters (replace with your own):
  
  /**
   * Minimum confidence level required to generate a signal (0-100)
   * Higher values = more selective signals
   * @default 60
   */
  minConfidence: number;

  /**
   * Position size as percentage of account (0-1)
   * @default 0.02 (2% of account)
   */
  positionSize: number;

  /**
   * Strike price offset from current price
   * Positive = OTM calls/puts, Negative = ITM calls/puts
   * @default 2
   */
  strikeOffset: number;

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
 * Complete configuration interface for {{STRATEGY_NAME}}
 * 
 * Extends the base StrategyConfig with strategy-specific parameters.
 */
export interface {{STRATEGY_CLASS_NAME}}Config extends StrategyConfig {
  /**
   * Strategy-specific parameters
   */
  parameters: {{STRATEGY_CLASS_NAME}}Parameters;

  /**
   * Risk management settings (inherited from base)
   * - maxPositionSize: Maximum position size as percentage of account
   * - stopLossPercent: Stop loss percentage (0-1)
   * - takeProfitPercent: Take profit percentage (0-1)
   * - maxDailyLoss: Maximum daily loss limit
   */
  riskManagement: {
    maxPositionSize: number;
    stopLossPercent: number;
    takeProfitPercent: number;
    maxDailyLoss: number;
  };

  /**
   * Timeframe for strategy execution
   * Supported values: '1Min', '5Min', '15Min', '1Hour'
   */
  timeframe: string;

  /**
   * Whether the strategy is currently enabled
   */
  enabled: boolean;
}

/**
 * Market condition types that this strategy can handle
 */
export type {{STRATEGY_CLASS_NAME}}MarketCondition = 
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
export type {{STRATEGY_CLASS_NAME}}SignalStrength = 
  | 'WEAK'
  | 'MODERATE'
  | 'STRONG'
  | 'VERY_STRONG';

/**
 * Strategy state for tracking internal conditions
 */
export interface {{STRATEGY_CLASS_NAME}}State {
  /**
   * Last signal generation timestamp
   */
  lastSignalTime?: Date;

  /**
   * Current market condition assessment
   */
  marketCondition?: {{STRATEGY_CLASS_NAME}}MarketCondition;

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
export interface {{STRATEGY_CLASS_NAME}}Indicators {
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
export interface {{STRATEGY_CLASS_NAME}}ValidationResult {
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
  suggestions?: Partial<{{STRATEGY_CLASS_NAME}}Parameters>;
}

/**
 * Backtest result specific to this strategy
 */
export interface {{STRATEGY_CLASS_NAME}}BacktestResult {
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
  config: {{STRATEGY_CLASS_NAME}}Config;

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
    // marketConditionBreakdown: Record<{{STRATEGY_CLASS_NAME}}MarketCondition, number>;
  };
}

/**
 * Export all types for external use
 */
export type {
  {{STRATEGY_CLASS_NAME}}Parameters,
  {{STRATEGY_CLASS_NAME}}Config,
  {{STRATEGY_CLASS_NAME}}MarketCondition,
  {{STRATEGY_CLASS_NAME}}SignalStrength,
  {{STRATEGY_CLASS_NAME}}State,
  {{STRATEGY_CLASS_NAME}}Indicators,
  {{STRATEGY_CLASS_NAME}}ValidationResult,
  {{STRATEGY_CLASS_NAME}}BacktestResult
};
