/**
 * 🎯 {{STRATEGY_NAME}} Strategy - Default Configuration
 * ====================================================
 * 
 * Default configuration parameters for the {{STRATEGY_NAME}} strategy.
 * These values provide a good starting point and can be customized per deployment.
 * 
 * @fileoverview Default configuration for {{STRATEGY_NAME}} strategy
 * @author {{AUTHOR_NAME}}
 * @version {{VERSION}}
 * @created {{DATE}}
 */

import { {{STRATEGY_CLASS_NAME}}Config } from './types';

/**
 * Default configuration for {{STRATEGY_NAME}} strategy
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
const defaultConfig: {{STRATEGY_CLASS_NAME}}Config = {
  /**
   * Strategy-specific parameters
   * 
   * These control the core behavior of the trading algorithm.
   * Adjust carefully as they directly impact signal generation.
   */
  parameters: {
    /**
     * Minimum confidence level to generate signals (0-100)
     * 
     * Higher values = fewer but higher quality signals
     * Lower values = more signals but potentially lower quality
     * 
     * Recommended range: 50-80
     * @default 60
     */
    minConfidence: 60,

    /**
     * Position size as percentage of account (0-1)
     * 
     * This determines how much of the account to risk per trade.
     * For 0DTE options, smaller position sizes are recommended due to high risk.
     * 
     * Recommended range: 0.01-0.05 (1%-5%)
     * @default 0.02 (2%)
     */
    positionSize: 0.02,

    /**
     * Strike price offset from current underlying price
     * 
     * Positive values = Out-of-the-money (OTM) options
     * Negative values = In-the-money (ITM) options
     * Zero = At-the-money (ATM) options
     * 
     * For 0DTE: OTM options are typically preferred for higher leverage
     * @default 2 (2 points OTM)
     */
    strikeOffset: 2,

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
   * Risk Management Configuration
   * 
   * These parameters are critical for protecting capital and managing risk.
   * Conservative settings are recommended for 0DTE options trading.
   */
  riskManagement: {
    /**
     * Maximum position size as percentage of account (0-1)
     * 
     * This is a hard limit that should never be exceeded.
     * Acts as a safety net against parameter misconfiguration.
     * 
     * @default 0.05 (5% maximum)
     */
    maxPositionSize: 0.05,

    /**
     * Stop loss percentage (0-1)
     * 
     * Percentage of premium to lose before closing position.
     * For 0DTE options, tight stop losses are recommended due to rapid time decay.
     * 
     * @default 0.5 (50% of premium)
     */
    stopLossPercent: 0.5,

    /**
     * Take profit percentage (0-1)
     * 
     * Percentage gain to target before closing position.
     * For 0DTE options, taking profits quickly is often wise.
     * 
     * @default 1.0 (100% gain - double the premium)
     */
    takeProfitPercent: 1.0,

    /**
     * Maximum daily loss limit (in dollars)
     * 
     * Total dollar amount that can be lost in a single day.
     * Trading stops when this limit is reached.
     * 
     * @default 500
     */
    maxDailyLoss: 500,
  },

  /**
   * Timeframe Configuration
   * 
   * The timeframe determines the granularity of market data analysis.
   * For 0DTE strategies, shorter timeframes are typically used.
   */
  timeframe: '1Min', // Options: '1Min', '5Min', '15Min', '1Hour'

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
    positionSizeVsMax: (config: {{STRATEGY_CLASS_NAME}}Config) => 
      config.parameters.positionSize <= config.riskManagement.maxPositionSize,
    
    // Take profit should generally be higher than stop loss for positive expectancy
    takeProfitVsStopLoss: (config: {{STRATEGY_CLASS_NAME}}Config) =>
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

// Export additional configurations
export {
  environmentConfigs,
  configValidationRules,
  performancePresets,
};
