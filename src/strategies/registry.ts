/**
 * 🏗️ STRATEGY REGISTRY
 * ====================
 * Central registry for all trading strategies in the 0DTE system.
 * 
 * This file manages strategy discovery, loading, and metadata.
 * All new strategies MUST be registered here to be available in the system.
 * 
 * @fileoverview Strategy registry and management system
 * @author 0DTE Trading System
 * @version 1.0.0
 */

import { MarketData, OptionsChain, TradeSignal } from '../utils/types';

/**
 * Core interface that ALL trading strategies must implement
 * This ensures consistency and interoperability across all strategies
 */
export interface TradingStrategy {
  /** Unique strategy identifier */
  readonly name: string;
  
  /** Human-readable description of the strategy */
  readonly description: string;
  
  /** Strategy version for tracking changes */
  readonly version: string;
  
  /** Strategy author/maintainer */
  readonly author: string;

  // Core Methods - Required for all strategies
  
  /**
   * Generate trading signal based on market data and options chain
   * @param data Historical market data array (newest last)
   * @param options Available options chain for the current timeframe
   * @returns Promise<TradeSignal> if conditions are met, null otherwise
   * 
   * ENHANCED: Now supports async operations for real data integration
   * (e.g., fetching real VIX data, real options Greeks, etc.)
   */
  generateSignal(data: MarketData[], options: OptionsChain[]): Promise<TradeSignal | null>;

  /**
   * Validate a generated signal before execution
   * @param signal The signal to validate
   * @returns true if signal is valid and safe to execute
   */
  validateSignal(signal: TradeSignal): boolean;

  /**
   * Calculate risk metrics for a given signal
   * @param signal The signal to analyze
   * @returns Risk assessment metrics
   */
  calculateRisk(signal: TradeSignal): RiskMetrics;

  // Configuration Methods
  
  /**
   * Get default configuration for this strategy
   * @returns Default strategy configuration object
   */
  getDefaultConfig(): StrategyConfig;

  /**
   * Validate strategy configuration
   * @param config Configuration to validate
   * @returns true if configuration is valid
   */
  validateConfig(config: StrategyConfig): boolean;

  // Metadata Methods
  
  /**
   * Get list of required technical indicators
   * @returns Array of indicator names (e.g., ['RSI', 'MACD', 'BB'])
   */
  getRequiredIndicators(): string[];

  /**
   * Get supported timeframes for this strategy
   * @returns Array of timeframe strings (e.g., ['1Min', '5Min'])
   */
  getTimeframes(): string[];

  /**
   * Get risk level classification
   * @returns Risk level classification
   */
  getRiskLevel(): 'LOW' | 'MEDIUM' | 'HIGH';
}

/**
 * Strategy configuration interface
 * Each strategy can extend this with specific parameters
 */
export interface StrategyConfig {
  /** Strategy-specific parameters */
  parameters: Record<string, any>;
  
  /** Risk management settings */
  riskManagement: {
    maxPositionSize: number;
    stopLossPercent: number;
    takeProfitPercent: number;
    maxDailyLoss: number;
  };
  
  /** Timeframe settings */
  timeframe: string;
  
  /** Enable/disable strategy */
  enabled: boolean;
}

/**
 * Risk metrics interface for strategy analysis
 */
export interface RiskMetrics {
  /** Estimated probability of profit (0-1) */
  probabilityOfProfit: number;
  
  /** Maximum potential loss */
  maxLoss: number;
  
  /** Maximum potential profit */
  maxProfit: number;
  
  /** Risk/reward ratio */
  riskRewardRatio: number;
  
  /** Time decay risk for options */
  timeDecayRisk: 'LOW' | 'MEDIUM' | 'HIGH';
  
  /** Volatility risk assessment */
  volatilityRisk: 'LOW' | 'MEDIUM' | 'HIGH';
}

/**
 * Strategy metadata for registry management
 */
export interface StrategyMetadata {
  /** Strategy class constructor */
  strategyClass: new () => TradingStrategy;
  
  /** Category classification */
  category: 'MOMENTUM' | 'MEAN_REVERSION' | 'BREAKOUT' | 'SCALPING' | 'SWING' | 'ARBITRAGE';
  
  /** Market conditions where strategy performs best */
  marketConditions: ('TRENDING' | 'SIDEWAYS' | 'VOLATILE' | 'LOW_VOLATILITY')[];
  
  /** Minimum account size recommended */
  minAccountSize: number;
  
  /** Strategy complexity level */
  complexity: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  
  /** Last updated timestamp */
  lastUpdated: Date;
  
  /** Strategy status */
  status: 'ACTIVE' | 'DEPRECATED' | 'EXPERIMENTAL';
}

/**
 * 🎯 STRATEGY REGISTRY
 * ====================
 * 
 * Register all available strategies here using dynamic imports for lazy loading.
 * This pattern allows strategies to be loaded only when needed, improving startup time.
 * 
 * NAMING CONVENTION:
 * - Key: kebab-case strategy identifier
 * - Import: matches directory name in src/strategies/
 * 
 * ADDING NEW STRATEGIES:
 * 1. Create strategy directory: src/strategies/[strategy-name]/
 * 2. Implement TradingStrategy interface
 * 3. Add entry to STRATEGY_REGISTRY below
 * 4. Add metadata to STRATEGY_METADATA below
 * 5. Update documentation
 */
export const STRATEGY_REGISTRY = {
  // Existing strategies (legacy - will be refactored to new pattern)
  'adaptive-momentum': () => import('./adaptive-strategy-selector'),
  'simple-momentum': () => import('./simple-momentum-wrapper'),
  
  // New modular strategies (add new ones here)
  'flyagonal': () => import('./flyagonal'),
  // 'mean-reversion-rsi': () => import('./mean-reversion-rsi'),
  // 'breakout-bollinger': () => import('./breakout-bollinger'),
  // 'scalping-ema': () => import('./scalping-ema'),
  // 'swing-macd': () => import('./swing-macd'),
} as const;

/**
 * 🎯 STRATEGY BACKTESTING ADAPTER REGISTRY
 * ========================================
 * 
 * Maps strategy names to their corresponding backtesting adapters.
 * This enables strategy-specific backtesting behavior while maintaining
 * the core real data fetching and account management.
 * 
 * Each adapter customizes:
 * - Options data generation (strategy-specific strikes/expirations)
 * - Position management (single-leg vs multi-leg)
 * - Exit conditions (strategy-specific logic)
 * - Performance metrics (VIX regime, profit zone efficiency, etc.)
 */
export const BACKTESTING_ADAPTER_REGISTRY = {
  'simple-momentum': () => import('./simple-momentum-backtesting-adapter').then(m => m.SimpleMomentumBacktestingAdapter),
  'flyagonal': () => import('./flyagonal/backtesting-adapter').then(m => m.FlyagonalBacktestingAdapter),
  // Future adapters will be added here as strategies are created
} as const;

/**
 * Strategy metadata registry
 * Provides additional information about each strategy without loading the code
 */
export const STRATEGY_METADATA: Record<keyof typeof STRATEGY_REGISTRY, Partial<StrategyMetadata>> = {
  'adaptive-momentum': {
    category: 'MOMENTUM',
    marketConditions: ['TRENDING', 'VOLATILE'],
    minAccountSize: 25000,
    complexity: 'INTERMEDIATE',
    status: 'ACTIVE',
    lastUpdated: new Date('2024-02-01'),
  },
  
  'simple-momentum': {
    category: 'MOMENTUM', 
    marketConditions: ['TRENDING'],
    minAccountSize: 10000,
    complexity: 'BEGINNER',
    status: 'ACTIVE',
    lastUpdated: new Date('2024-02-01'),
  },

  'flyagonal': {
    category: 'ARBITRAGE',
    marketConditions: ['VOLATILE'],
    minAccountSize: 25000,
    complexity: 'ADVANCED',
    status: 'EXPERIMENTAL',
    lastUpdated: new Date('2025-08-30'),
  },
};

/**
 * Strategy registry management class
 * Provides methods to discover, load, and manage strategies
 */
export class StrategyRegistry {
  private static loadedStrategies = new Map<string, TradingStrategy>();

  /**
   * Get list of all available strategy names
   */
  static getAvailableStrategies(): string[] {
    return Object.keys(STRATEGY_REGISTRY);
  }

  /**
   * Get strategy metadata without loading the strategy
   */
  static getStrategyMetadata(strategyName: string): Partial<StrategyMetadata> | null {
    return STRATEGY_METADATA[strategyName as keyof typeof STRATEGY_REGISTRY] || null;
  }

  /**
   * Load a strategy by name (lazy loading)
   */
  static async loadStrategy(strategyName: string): Promise<TradingStrategy | null> {
    // Check if already loaded
    if (this.loadedStrategies.has(strategyName)) {
      return this.loadedStrategies.get(strategyName)!;
    }

    // Check if strategy exists in registry
    const strategyLoader = STRATEGY_REGISTRY[strategyName as keyof typeof STRATEGY_REGISTRY];
    if (!strategyLoader) {
      console.error(`Strategy '${strategyName}' not found in registry`);
      return null;
    }

    try {
      // Dynamically import and instantiate strategy
      const strategyModule = await strategyLoader();
      
      // Handle different export patterns
      let StrategyClass;
      if ('default' in strategyModule) {
        StrategyClass = strategyModule.default;
      } else {
        // Find the first class that implements TradingStrategy
        const exports = Object.values(strategyModule);
        StrategyClass = exports.find(exp => 
          typeof exp === 'function' && 
          exp.prototype && 
          'generateSignal' in exp.prototype
        );
      }

      if (!StrategyClass) {
        throw new Error(`No valid strategy class found in module '${strategyName}'`);
      }

      // Instantiate and cache
      const strategy = new StrategyClass();
      
      // Type check - ensure strategy implements TradingStrategy interface
      if (!this.isValidTradingStrategy(strategy)) {
        throw new Error(`Strategy '${strategyName}' does not implement the TradingStrategy interface properly`);
      }
      
      this.loadedStrategies.set(strategyName, strategy);
      
      console.log(`✅ Loaded strategy: ${strategy.name} v${strategy.version}`);
      return strategy;

    } catch (error) {
      console.error(`❌ Failed to load strategy '${strategyName}':`, error);
      return null;
    }
  }

  /**
   * Get strategies by category
   */
  static getStrategiesByCategory(category: StrategyMetadata['category']): string[] {
    return Object.entries(STRATEGY_METADATA)
      .filter(([_, metadata]) => metadata.category === category)
      .map(([name]) => name);
  }

  /**
   * Get strategies suitable for account size
   */
  static getStrategiesForAccountSize(accountSize: number): string[] {
    return Object.entries(STRATEGY_METADATA)
      .filter(([_, metadata]) => (metadata.minAccountSize || 0) <= accountSize)
      .map(([name]) => name);
  }

  /**
   * Check if an object implements the TradingStrategy interface
   */
  private static isValidTradingStrategy(obj: any): obj is TradingStrategy {
    return obj &&
      typeof obj.name === 'string' &&
      typeof obj.description === 'string' &&
      typeof obj.version === 'string' &&
      typeof obj.author === 'string' &&
      typeof obj.generateSignal === 'function' &&
      typeof obj.validateSignal === 'function' &&
      typeof obj.calculateRisk === 'function' &&
      typeof obj.getDefaultConfig === 'function' &&
      typeof obj.validateConfig === 'function' &&
      typeof obj.getRequiredIndicators === 'function' &&
      typeof obj.getTimeframes === 'function' &&
      typeof obj.getRiskLevel === 'function';
  }

  /**
   * Load a backtesting adapter by strategy name
   */
  static async loadBacktestingAdapter(strategyName: string): Promise<any | null> {
    const adapterLoader = BACKTESTING_ADAPTER_REGISTRY[strategyName as keyof typeof BACKTESTING_ADAPTER_REGISTRY];
    if (!adapterLoader) {
      console.warn(`No backtesting adapter found for strategy '${strategyName}', using default behavior`);
      return null;
    }

    try {
      const AdapterClass = await adapterLoader();
      const adapter = new AdapterClass();
      console.log(`✅ Loaded backtesting adapter for: ${strategyName}`);
      return adapter;
    } catch (error) {
      console.error(`❌ Failed to load backtesting adapter for '${strategyName}':`, error);
      return null;
    }
  }

  /**
   * Validate strategy implementation
   */
  static async validateStrategy(strategyName: string): Promise<boolean> {
    const strategy = await this.loadStrategy(strategyName);
    if (!strategy) return false;

    try {
      // Check required methods exist
      const requiredMethods = [
        'generateSignal', 'validateSignal', 'calculateRisk',
        'getDefaultConfig', 'validateConfig', 'getRequiredIndicators',
        'getTimeframes', 'getRiskLevel'
      ];

      for (const method of requiredMethods) {
        if (typeof strategy[method as keyof TradingStrategy] !== 'function') {
          console.error(`Strategy '${strategyName}' missing required method: ${method}`);
          return false;
        }
      }

      // Check required properties
      const requiredProps = ['name', 'description', 'version', 'author'];
      for (const prop of requiredProps) {
        if (!strategy[prop as keyof TradingStrategy]) {
          console.error(`Strategy '${strategyName}' missing required property: ${prop}`);
          return false;
        }
      }

      console.log(`✅ Strategy '${strategyName}' validation passed`);
      return true;

    } catch (error) {
      console.error(`❌ Strategy '${strategyName}' validation failed:`, error);
      return false;
    }
  }
}

/**
 * Export types for external use
 */
export type StrategyName = keyof typeof STRATEGY_REGISTRY;
// Individual type exports are already declared above in their respective interfaces
