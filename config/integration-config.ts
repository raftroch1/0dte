
import { LiveTradingConfig } from '../src/trading/live-trading-connector';
import { BacktestConfig } from '../src/core/backtesting-engine';
import { PaperTradingConfig } from '../src/trading/alpaca-paper-trading';
import { Strategy, AccountConfig } from '../src/utils/types';

// Default configurations for different trading scenarios
export class IntegrationConfig {
  
  // Default 0DTE strategy optimized for $35k account targeting $200-250 daily
  static getDefault0DTEStrategy(): Strategy {
    return {
      name: '0DTE_Momentum_Strategy',
      
      // Position sizing for $35k account
      positionSizePercent: 2, // 2% risk per trade
      maxPositions: 3, // Maximum 3 concurrent positions
      
      // Risk management optimized for 0DTE
      stopLossPercent: 30, // 30% stop loss
      takeProfitPercent: 50, // 50% profit target
      maxDailyLoss: 500, // $500 daily loss limit
      dailyProfitTarget: 225, // $225 daily target (middle of $200-250 range)
      
      // Technical indicators
      rsiPeriod: 14,
      rsiOversold: 30,
      rsiOverbought: 70,
      macdFast: 12,
      macdSlow: 26,
      macdSignal: 9,
      bbPeriod: 20,
      bbStdDev: 2,
      
      // 0DTE specific parameters
      maxHoldingTimeMinutes: 240, // 4 hours maximum
      timeDecayExitMinutes: 30, // Exit 30 minutes before close
      momentumThreshold: 0.5, // Minimum momentum for entry
      volumeConfirmation: 1.5, // 1.5x average volume
      vixFilterMax: 50, // Maximum VIX for trading
      vixFilterMin: 10 // Minimum VIX for trading
    };
  }

  // Account configuration for $35k account
  static getDefault35KAccountConfig(): AccountConfig {
    return {
      balance: 35000,
      dailyProfitTarget: 225, // $225 target
      dailyLossLimit: 500, // $500 loss limit
      maxPositionSize: 10, // 10 contracts max
      riskPerTrade: 0.02, // 2% risk per trade
      
      // Trading hours (in decimal hours)
      marketOpen: 9.5, // 9:30 AM
      marketClose: 16, // 4:00 PM
      morningSessionEnd: 11, // 11:00 AM
      afternoonSessionStart: 14 // 2:00 PM
    };
  }

  // Live trading configuration
  static getLiveTradingConfig(
    apiKey: string,
    apiSecret: string,
    isPaper: boolean = true
  ): LiveTradingConfig {
    return {
      alpacaConfig: {
        apiKey,
        apiSecret,
        isPaper
      },
      accountConfig: this.getDefault35KAccountConfig(),
      strategy: this.getDefault0DTEStrategy(),
      underlyingSymbol: 'SPX', // Flyagonal trades SPX index options, not SPY ETF
      enablePaperTrading: isPaper,
      
      riskManagement: {
        maxDailyLoss: 500,
        maxPositionSize: 3500, // $3,500 per position (10% of account)
        maxOpenPositions: 3,
        stopLossPercent: 30,
        takeProfitPercent: 50
      },
      
      notifications: {
        enableSlack: false,
        enableEmail: false
      }
    };
  }

  // Paper trading configuration
  static getPaperTradingConfig(): PaperTradingConfig {
    return {
      initialBalance: 35000,
      commissionPerContract: 0.65, // Typical options commission
      bidAskSpreadPercent: 0.02, // 2% bid-ask spread simulation
      slippagePercent: 0.001, // 0.1% slippage
      maxPositions: 3,
      riskFreeRate: 0.05 // 5% risk-free rate
    };
  }

  // Backtesting configuration
  static getBacktestConfig(
    startDate: Date,
    endDate: Date,
    underlyingSymbol: string = 'SPX'
  ): Omit<BacktestConfig, 'strategy'> {
    return {
      startDate,
      endDate,
      initialBalance: 25000,
      underlyingSymbol,
      commissionPerContract: 0.65,
      slippagePercent: 0.001,
      bidAskSpreadPercent: 0.02,
      riskFreeRate: 0.05
    };
  }

  // Conservative strategy for risk-averse traders
  static getConservativeStrategy(): Strategy {
    const baseStrategy = this.getDefault0DTEStrategy();
    return {
      ...baseStrategy,
      name: '0DTE_Conservative_Strategy',
      positionSizePercent: 1, // 1% risk per trade
      maxPositions: 2, // Only 2 positions
      stopLossPercent: 20, // Tighter stop loss
      takeProfitPercent: 30, // Lower profit target
      dailyProfitTarget: 150, // Lower daily target
      maxDailyLoss: 300, // Lower loss limit
      vixFilterMax: 35, // Lower VIX threshold
      momentumThreshold: 0.7 // Higher momentum requirement
    };
  }

  // Aggressive strategy for experienced traders
  static getAggressiveStrategy(): Strategy {
    const baseStrategy = this.getDefault0DTEStrategy();
    return {
      ...baseStrategy,
      name: '0DTE_Aggressive_Strategy',
      positionSizePercent: 3, // 3% risk per trade
      maxPositions: 5, // Up to 5 positions
      stopLossPercent: 40, // Wider stop loss
      takeProfitPercent: 75, // Higher profit target
      dailyProfitTarget: 300, // Higher daily target
      maxDailyLoss: 750, // Higher loss limit
      vixFilterMax: 60, // Higher VIX threshold
      momentumThreshold: 0.3, // Lower momentum requirement
      maxHoldingTimeMinutes: 300 // 5 hours maximum
    };
  }

  // Morning momentum strategy
  static getMorningMomentumStrategy(): Strategy {
    const baseStrategy = this.getDefault0DTEStrategy();
    return {
      ...baseStrategy,
      name: '0DTE_Morning_Momentum',
      maxHoldingTimeMinutes: 120, // 2 hours maximum
      momentumThreshold: 0.8, // High momentum requirement
      volumeConfirmation: 2.0, // 2x volume confirmation
      takeProfitPercent: 40, // Quick profit taking
      stopLossPercent: 25 // Tight risk control
    };
  }

  // Afternoon mean reversion strategy
  static getAfternoonMeanReversionStrategy(): Strategy {
    const baseStrategy = this.getDefault0DTEStrategy();
    return {
      ...baseStrategy,
      name: '0DTE_Afternoon_MeanReversion',
      maxHoldingTimeMinutes: 90, // 1.5 hours maximum
      rsiOversold: 25, // More extreme RSI levels
      rsiOverbought: 75,
      takeProfitPercent: 35, // Quick profit taking
      stopLossPercent: 35, // Wider stops for mean reversion
      timeDecayExitMinutes: 45 // Exit earlier due to time decay
    };
  }

  // Scalping strategy for quick trades
  static getScalpingStrategy(): Strategy {
    const baseStrategy = this.getDefault0DTEStrategy();
    return {
      ...baseStrategy,
      name: '0DTE_Scalping_Strategy',
      positionSizePercent: 1.5, // Smaller position size
      maxPositions: 5, // More positions for diversification
      maxHoldingTimeMinutes: 30, // Very short holds
      takeProfitPercent: 20, // Quick profits
      stopLossPercent: 15, // Tight stops
      momentumThreshold: 0.3, // Lower threshold for more trades
      volumeConfirmation: 1.2 // Lower volume requirement
    };
  }

  // Validation methods
  static validateStrategy(strategy: Strategy): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Basic validation
    if (strategy.positionSizePercent <= 0 || strategy.positionSizePercent > 10) {
      errors.push('Position size percent must be between 0 and 10');
    }

    if (strategy.maxPositions <= 0 || strategy.maxPositions > 10) {
      errors.push('Max positions must be between 1 and 10');
    }

    if (strategy.stopLossPercent <= 0 || strategy.stopLossPercent > 100) {
      errors.push('Stop loss percent must be between 0 and 100');
    }

    if (strategy.takeProfitPercent <= 0 || strategy.takeProfitPercent > 200) {
      errors.push('Take profit percent must be between 0 and 200');
    }

    if (strategy.maxDailyLoss <= 0) {
      errors.push('Max daily loss must be positive');
    }

    if (strategy.dailyProfitTarget <= 0) {
      errors.push('Daily profit target must be positive');
    }

    // 0DTE specific validation
    if (strategy.maxHoldingTimeMinutes <= 0 || strategy.maxHoldingTimeMinutes > 390) {
      errors.push('Max holding time must be between 1 and 390 minutes');
    }

    if (strategy.timeDecayExitMinutes < 0 || strategy.timeDecayExitMinutes > 60) {
      errors.push('Time decay exit must be between 0 and 60 minutes');
    }

    if (strategy.vixFilterMax <= strategy.vixFilterMin) {
      errors.push('VIX filter max must be greater than VIX filter min');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  static validateAccountConfig(config: AccountConfig): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (config.balance <= 0) {
      errors.push('Account balance must be positive');
    }

    if (config.dailyProfitTarget <= 0) {
      errors.push('Daily profit target must be positive');
    }

    if (config.dailyLossLimit <= 0) {
      errors.push('Daily loss limit must be positive');
    }

    if (config.maxPositionSize <= 0) {
      errors.push('Max position size must be positive');
    }

    if (config.riskPerTrade <= 0 || config.riskPerTrade > 0.1) {
      errors.push('Risk per trade must be between 0 and 10%');
    }

    // Trading hours validation
    if (config.marketOpen >= config.marketClose) {
      errors.push('Market open must be before market close');
    }

    if (config.morningSessionEnd <= config.marketOpen || config.morningSessionEnd >= config.afternoonSessionStart) {
      errors.push('Morning session end must be between market open and afternoon session start');
    }

    if (config.afternoonSessionStart >= config.marketClose) {
      errors.push('Afternoon session start must be before market close');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  // Helper method to create a complete backtest config with strategy
  static createBacktestConfig(
    startDate: Date,
    endDate: Date,
    strategyType: 'default' | 'conservative' | 'aggressive' | 'morning' | 'afternoon' | 'scalping' | string = 'default',
    underlyingSymbol: string = 'SPX'
  ): BacktestConfig {
    const baseConfig = this.getBacktestConfig(startDate, endDate, underlyingSymbol);
    
    let strategy: Strategy;
    
    // Handle new strategy names from registry
    if (!['default', 'conservative', 'aggressive', 'morning', 'afternoon', 'scalping'].includes(strategyType)) {
      // Create a minimal strategy object with just the name for the new framework
      strategy = {
        name: strategyType,
        positionSizePercent: 2,
        maxPositions: 3,
        stopLossPercent: 30,
        takeProfitPercent: 50,
        maxDailyLoss: 500,
        dailyProfitTarget: 225,
        rsiPeriod: 14,
        rsiOversold: 30,
        rsiOverbought: 70,
        macdFast: 12,
        macdSlow: 26,
        macdSignal: 9,
        bbPeriod: 20,
        bbStdDev: 2,
        maxHoldingTimeMinutes: 240,
        timeDecayExitMinutes: 30,
        momentumThreshold: 0.5,
        volumeConfirmation: 1.5,
        vixFilterMax: 50,
        vixFilterMin: 10
      };
    } else {
      // Handle legacy strategy types
      switch (strategyType) {
        case 'conservative':
          strategy = this.getConservativeStrategy();
          break;
        case 'aggressive':
          strategy = this.getAggressiveStrategy();
          break;
        case 'morning':
          strategy = this.getMorningMomentumStrategy();
          break;
        case 'afternoon':
          strategy = this.getAfternoonMeanReversionStrategy();
          break;
        case 'scalping':
          strategy = this.getScalpingStrategy();
          break;
        default:
          strategy = this.getDefault0DTEStrategy();
      }
    }

    return {
      ...baseConfig,
      strategy
    };
  }

  // Method to get recommended settings based on account size
  static getRecommendedSettings(accountSize: number): {
    strategy: Strategy;
    accountConfig: AccountConfig;
    riskLevel: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE';
  } {
    let riskLevel: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE';
    let strategy: Strategy;
    let accountConfig: AccountConfig;

    if (accountSize < 25000) {
      // Small account - conservative approach
      riskLevel = 'CONSERVATIVE';
      strategy = this.getConservativeStrategy();
      accountConfig = {
        ...this.getDefault35KAccountConfig(),
        balance: accountSize,
        dailyProfitTarget: Math.floor(accountSize * 0.005), // 0.5% daily target
        dailyLossLimit: Math.floor(accountSize * 0.015), // 1.5% daily loss limit
        maxPositionSize: Math.floor(accountSize * 0.1), // 10% max position
        riskPerTrade: 0.01 // 1% risk per trade
      };
    } else if (accountSize < 100000) {
      // Medium account - moderate approach
      riskLevel = 'MODERATE';
      strategy = this.getDefault0DTEStrategy();
      accountConfig = {
        ...this.getDefault35KAccountConfig(),
        balance: accountSize,
        dailyProfitTarget: Math.floor(accountSize * 0.006), // 0.6% daily target
        dailyLossLimit: Math.floor(accountSize * 0.02), // 2% daily loss limit
        maxPositionSize: Math.floor(accountSize * 0.1), // 10% max position
        riskPerTrade: 0.02 // 2% risk per trade
      };
    } else {
      // Large account - can be more aggressive
      riskLevel = 'AGGRESSIVE';
      strategy = this.getAggressiveStrategy();
      accountConfig = {
        ...this.getDefault35KAccountConfig(),
        balance: accountSize,
        dailyProfitTarget: Math.floor(accountSize * 0.008), // 0.8% daily target
        dailyLossLimit: Math.floor(accountSize * 0.025), // 2.5% daily loss limit
        maxPositionSize: Math.floor(accountSize * 0.15), // 15% max position
        riskPerTrade: 0.03 // 3% risk per trade
      };
    }

    return {
      strategy,
      accountConfig,
      riskLevel
    };
  }
}

// Export default configurations for easy access
export const DEFAULT_CONFIGS = {
  strategy: IntegrationConfig.getDefault0DTEStrategy(),
  accountConfig: IntegrationConfig.getDefault35KAccountConfig(),
  paperTrading: IntegrationConfig.getPaperTradingConfig(),
  
  // Strategy variants
  strategies: {
    default: IntegrationConfig.getDefault0DTEStrategy(),
    conservative: IntegrationConfig.getConservativeStrategy(),
    aggressive: IntegrationConfig.getAggressiveStrategy(),
    morning: IntegrationConfig.getMorningMomentumStrategy(),
    afternoon: IntegrationConfig.getAfternoonMeanReversionStrategy(),
    scalping: IntegrationConfig.getScalpingStrategy()
  }
};
