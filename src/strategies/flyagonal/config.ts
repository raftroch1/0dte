/**
 * 🎯 Flyagonal Strategy - Default Configuration
 * ====================================================
 * 
 * Default configuration parameters for the Flyagonal strategy.
 * These values provide a good starting point and can be customized per deployment.
 * 
 * @fileoverview Default configuration for Flyagonal strategy
 * @author Steve Guns
 * @version 1.0.0
 * @created 2025-08-30
 */

import { FlyagonalStrategyConfig } from './types';

/**
 * Default configuration for Flyagonal strategy
 * 
 * These parameters have been optimized based on:
 * - Historical backtesting results
 * - Risk management best practices
 * - Market condition analysis
 * - Performance optimization
 * 
 * Modification Guidelines:
 * - Test any changes thoroughly with backtesting
 * - Consider market volatility when adjusting parameters
 * - Maintain proper risk management ratios
 * - Document any changes with reasoning
 */
const defaultConfig: FlyagonalStrategyConfig = {
  /**
   * Flyagonal Strategy-specific parameters
   * 
   * These control the sophisticated Flyagonal algorithm that combines
   * a call broken wing butterfly with a put diagonal spread.
   * Based on Steve Guns' 96-97% win rate strategy.
   */
  parameters: {
    /**
     * Minimum confidence level to generate Flyagonal signals (0-100)
     * 
     * Steve Guns' Flyagonal is HIGHLY SELECTIVE - should only trade in optimal conditions
     * High threshold ensures ~1 trade every 4 days, not multiple per day
     * @default 85
     */
    minConfidence: 85,

    /**
     * Position size as percentage of account (0-1)
     * 
     * Flyagonal is defined risk with high win rate
     * Can use slightly larger position sizes
     * @default 0.03 (3%)
     */
    positionSize: 0.03,

    /**
     * VIX range for optimal Flyagonal conditions
     * 
     * Strategy works best in moderate volatility
     * @default { min: 15, max: 30 }
     */
    optimalVixRange: {
      min: 15,
      max: 30
    },

    /**
     * Days before expiration to initiate trades
     * 
     * Optimal entry timing based on Steve Guns' research
     * @default { min: 8, max: 10 }
     */
    entryTiming: {
      min: 8,
      max: 10
    },

    /**
     * Target holding period in days
     * 
     * Average holding period from backtesting
     * @default 4.5
     */
    targetHoldingDays: 4.5,

    /**
     * Butterfly strike spacing (SPY-adapted from SPX)
     * 
     * Based on Steve Guns' methodology adapted for SPY: 5pt lower wing, 6pt upper wing
     * SPY equivalent of SPX { lower: 50, upper: 60 }
     * @default { lower: 5, upper: 6 }
     */
    butterflyStrikeSpacing: { lower: 5, upper: 6 },

    /**
     * Diagonal strike spacing (SPY-adapted from SPX)
     * 
     * Short put 3% below market, long put 5pts further below (SPY equivalent of SPX 50pts)
     * @default { percentBelow: 3, protection: 5 }
     */
    diagonalStrikeSpacing: { percentBelow: 3, protection: 5 },

    /**
     * Maximum trend strength to allow entry
     * 
     * Avoid strong trending markets
     * @default 0.05 (5% trend maximum)
     */
    maxTrendStrength: 0.05,

    /**
     * Adjustment threshold
     * 
     * Delta threshold that triggers position adjustment
     * @default 0.15 (15 delta)
     */
    adjustmentThreshold: 0.15,

    // TODO: Add your strategy-specific parameters here
    // 
    // Example for RSI-based strategy:
    // /**
    //  * RSI calculation period
    //  * @default 14
    //  */
    // rsiPeriod: 14,
    // 
    // /**
    //  * RSI oversold threshold (buy signal)
    //  * @default 30
    //  */
    // oversoldThreshold: 30,
    // 
    // /**
    //  * RSI overbought threshold (sell signal)
    //  * @default 70
    //  */
    // overboughtThreshold: 70,

    // Example for MACD-based strategy:
    // /**
    //  * MACD fast EMA period
    //  * @default 12
    //  */
    // macdFastPeriod: 12,
    // 
    // /**
    //  * MACD slow EMA period
    //  * @default 26
    //  */
    // macdSlowPeriod: 26,
    // 
    // /**
    //  * MACD signal line period
    //  * @default 9
    //  */
    // macdSignalPeriod: 9,

    // Example for Bollinger Bands strategy:
    // /**
    //  * Bollinger Bands period
    //  * @default 20
    //  */
    // bbPeriod: 20,
    // 
    // /**
    //  * Bollinger Bands standard deviation
    //  * @default 2
    //  */
    // bbStdDev: 2,

    // Example for Moving Average strategy:
    // /**
    //  * Short-term moving average period
    //  * @default 10
    //  */
    // shortMaPeriod: 10,
    // 
    // /**
    //  * Long-term moving average period
    //  * @default 30
    //  */
    // longMaPeriod: 30,
  },

  /**
   * Flyagonal Risk Management Configuration
   * 
   * Based on Steve Guns' actual risk parameters:
   * - Max $500 loss per trade
   * - 4:1 risk/reward ratio ($2000 profit target)
   * - 96-97% win rate strategy with defined risk
   */
  riskManagement: {
    /**
     * Maximum position size as percentage of account (0-1)
     * 
     * Calculated to limit max loss to $500 per trade
     * @default 0.03 (3% maximum)
     */
    maxPositionSize: 0.03,

    /**
     * Stop loss percentage (0-1)
     * 
     * Defined risk strategy - cut at $500 loss
     * @default 1.0 (100% - full premium loss, max $500)
     */
    stopLossPercent: 1.0,

    /**
     * Take profit percentage (CORRECTED: Realistic 1.5:1 risk/reward ratio)
     * 
     * CORRECTION: 4:1 risk/reward with 90% win rate is mathematically impossible
     * Realistic target: $750 profit on $500 risk = 150% (1.5:1 risk/reward)
     * This aligns with actual income strategy performance
     * @default 1.5 (150% - 1.5:1 risk/reward)
     */
    takeProfitPercent: 1.5,

    /**
     * Maximum daily loss limit (in dollars)
     * 
     * Conservative limit: 2-3 max losses per day
     * @default 1500 (3 x $500 max loss per trade)
     */
    maxDailyLoss: 1500,

    /**
     * Maximum trades per day
     * 
     * Steve Guns' Flyagonal is highly selective - typically 1 trade every 4 days
     * This prevents over-trading and maintains strategy discipline
     * @default 1
     */
    maxTradesPerDay: 1,

    /**
     * Maximum number of concurrent Flyagonal positions
     * 
     * Limit complexity and risk concentration
     * @default 3
     */
    maxConcurrentPositions: 3,

    /**
     * Adjustment frequency limit
     * 
     * Maximum adjustments per position (Steve reports <50% need adjustment)
     * @default 1
     */
    maxAdjustmentsPerPosition: 1,
  },

  /**
   * Timeframe Configuration
   * 
   * Flyagonal uses longer timeframes due to 4.5-day average holding period
   * Focus on hourly analysis rather than minute-by-minute
   */
  timeframe: '1Hour', // Primary: '1Hour', Secondary: '4Hour', '1Day'

  /**
   * Strategy Enable/Disable Flag
   * 
   * Allows for easy strategy activation/deactivation without removing configuration.
   * Useful for testing and gradual deployment.
   */
  enabled: true,
};

/**
 * Environment-specific configuration overrides
 * 
 * These allow different settings for different environments
 * (development, staging, production) while maintaining the same codebase.
 */
export const environmentConfigs = {
  /**
   * Development environment configuration
   * - More conservative settings for testing
   * - Enhanced logging and validation
   */
  development: {
    ...defaultConfig,
    parameters: {
      ...defaultConfig.parameters,
      minConfidence: 70, // Higher confidence threshold for testing
      positionSize: 0.01, // Smaller position size for safety
    },
    riskManagement: {
      ...defaultConfig.riskManagement,
      maxDailyLoss: 100, // Lower daily loss limit for testing
    },
  },

  /**
   * Production environment configuration
   * - Optimized settings based on backtesting
   * - Production-ready risk management
   */
  production: {
    ...defaultConfig,
    // Use default configuration for production
  },

  /**
   * Paper trading configuration
   * - Realistic settings for paper trading
   * - Allows for strategy validation without real money
   */
  paper: {
    ...defaultConfig,
    parameters: {
      ...defaultConfig.parameters,
      minConfidence: 55, // Slightly lower threshold for more signals
    },
  },
};

/**
 * Configuration validation rules
 * 
 * These rules ensure that configuration parameters are within acceptable ranges
 * and maintain proper relationships between different settings.
 */
export const configValidationRules = {
  parameters: {
    minConfidence: { min: 0, max: 100 },
    positionSize: { min: 0.001, max: 0.1 }, // 0.1% to 10%
    strikeOffset: { min: -10, max: 10 },
    
    // TODO: Add validation rules for your specific parameters
    // Example:
    // rsiPeriod: { min: 5, max: 50 },
    // oversoldThreshold: { min: 10, max: 40 },
    // overboughtThreshold: { min: 60, max: 90 },
  },
  
  riskManagement: {
    maxPositionSize: { min: 0.001, max: 0.2 }, // 0.1% to 20%
    stopLossPercent: { min: 0.1, max: 1.0 }, // 10% to 100%
    takeProfitPercent: { min: 0.2, max: 5.0 }, // 20% to 500%
    maxDailyLoss: { min: 50, max: 10000 },
  },
  
  // Relationship validations
  relationships: {
    // Position size should be less than max position size
    positionSizeVsMax: (config: FlyagonalStrategyConfig) => 
      config.parameters.positionSize <= config.riskManagement.maxPositionSize,
    
    // Take profit should generally be higher than stop loss for positive expectancy
    takeProfitVsStopLoss: (config: FlyagonalStrategyConfig) =>
      config.riskManagement.takeProfitPercent >= config.riskManagement.stopLossPercent,
  },
};

/**
 * Performance optimization presets
 * 
 * Pre-configured parameter sets optimized for different market conditions
 * and trading objectives.
 */
export const performancePresets = {
  /**
   * Conservative preset - Lower risk, fewer signals
   */
  conservative: {
    ...defaultConfig,
    parameters: {
      ...defaultConfig.parameters,
      minConfidence: 75,
      positionSize: 0.015,
    },
    riskManagement: {
      ...defaultConfig.riskManagement,
      stopLossPercent: 0.4,
      takeProfitPercent: 0.8,
    },
  },

  /**
   * Aggressive preset - Higher risk, more signals
   */
  aggressive: {
    ...defaultConfig,
    parameters: {
      ...defaultConfig.parameters,
      minConfidence: 50,
      positionSize: 0.03,
    },
    riskManagement: {
      ...defaultConfig.riskManagement,
      stopLossPercent: 0.6,
      takeProfitPercent: 1.5,
    },
  },

  /**
   * Scalping preset - Very short-term, quick profits
   */
  scalping: {
    ...defaultConfig,
    parameters: {
      ...defaultConfig.parameters,
      minConfidence: 65,
      positionSize: 0.025,
      strikeOffset: 1, // Closer to ATM for faster movement
    },
    riskManagement: {
      ...defaultConfig.riskManagement,
      stopLossPercent: 0.3,
      takeProfitPercent: 0.6,
    },
    timeframe: '1Min',
  },
};

// Export default configuration
export default defaultConfig;

// Export additional configurations (already exported above)
// Removed duplicate exports to fix TypeScript errors
