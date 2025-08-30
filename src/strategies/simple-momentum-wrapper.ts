/**
 * 🎯 Simple Momentum Strategy Wrapper
 * ===================================
 * 
 * Wrapper to make the existing SimpleMomentumStrategy compatible with the new
 * TradingStrategy interface and backtesting framework.
 * 
 * @fileoverview Simple Momentum strategy wrapper for new framework
 * @author Trading System Architecture
 * @version 1.0.0
 * @created 2025-08-30
 */

import { TradingStrategy, StrategyConfig, RiskMetrics } from '../strategies/registry';
import { MarketData, OptionsChain, TradeSignal } from '../utils/types';
import { SimpleMomentumStrategy } from './simple-momentum-strategy';
import { TechnicalAnalysis } from '../data/technical-indicators';

/**
 * Simple Momentum Strategy Wrapper
 * 
 * Wraps the existing SimpleMomentumStrategy to work with the new framework
 */
export class SimpleMomentumStrategyWrapper implements TradingStrategy {
  readonly name = 'simple-momentum';
  readonly description = 'Simple momentum strategy using RSI and MACD for 0DTE options';
  readonly version = '1.0.0';
  readonly author = '0DTE Trading System';

  /**
   * Generate trading signal using the wrapped strategy
   */
  generateSignal(data: MarketData[], options: OptionsChain[]): TradeSignal | null {
    if (data.length < 20) return null;
    
    // Calculate technical indicators
    const indicators = TechnicalAnalysis.calculateAllIndicators(data);
    if (!indicators) return null;
    
    const currentBar = data[data.length - 1];
    const currentPrice = currentBar.close;
    
    // Simple momentum strategy logic
    if (indicators.rsi < 35 && indicators.macd > indicators.macdSignal) {
      return {
        action: 'BUY_CALL',
        confidence: 70,
        reason: 'RSI oversold + MACD bullish crossover',
        indicators,
        timestamp: currentBar.timestamp,
        targetStrike: Math.round(currentPrice + 2),
        expiration: new Date(currentBar.timestamp.getTime() + 4 * 60 * 60 * 1000), // 4 hours
        positionSize: 2,
        stopLoss: 0.3,
        takeProfit: 0.5
      };
    }
    
    if (indicators.rsi > 65 && indicators.macd < indicators.macdSignal) {
      return {
        action: 'BUY_PUT',
        confidence: 70,
        reason: 'RSI overbought + MACD bearish crossover',
        indicators,
        timestamp: currentBar.timestamp,
        targetStrike: Math.round(currentPrice - 2),
        expiration: new Date(currentBar.timestamp.getTime() + 4 * 60 * 60 * 1000), // 4 hours
        positionSize: 2,
        stopLoss: 0.3,
        takeProfit: 0.5
      };
    }
    
    return null;
  }

  /**
   * Validate trading signal
   */
  validateSignal(signal: TradeSignal): boolean {
    // Basic validation
    if (!signal.action || !signal.confidence || !signal.timestamp) {
      return false;
    }
    
    // Check confidence level
    if (signal.confidence < 50) {
      return false;
    }
    
    // Check position size
    if (signal.positionSize <= 0 || signal.positionSize > 10) {
      return false;
    }
    
    return true;
  }

  /**
   * Calculate risk metrics for signal
   */
  calculateRisk(signal: TradeSignal): RiskMetrics {
    const maxLoss = signal.positionSize * 100; // Assume $100 per contract max loss
    const maxProfit = maxLoss * (signal.takeProfit || 0.5);
    
    return {
      probabilityOfProfit: signal.confidence / 100,
      maxLoss,
      maxProfit,
      riskRewardRatio: maxProfit / maxLoss,
      timeDecayRisk: 'HIGH', // 0DTE options have high time decay
      volatilityRisk: 'MEDIUM'
    };
  }

  /**
   * Get default configuration
   */
  getDefaultConfig(): StrategyConfig {
    return {
      parameters: {
        rsiPeriod: 14,
        rsiOversold: 35,
        rsiOverbought: 65,
        macdFast: 12,
        macdSlow: 26,
        macdSignal: 9,
        minConfidence: 50
      },
      riskManagement: {
        maxPositionSize: 0.05, // 5% of account
        stopLossPercent: 0.3,   // 30% stop loss
        takeProfitPercent: 0.5, // 50% take profit
        maxDailyLoss: 500
      },
      timeframe: '5Min',
      enabled: true
    };
  }

  /**
   * Validate strategy configuration
   */
  validateConfig(config: StrategyConfig): boolean {
    const params = config.parameters;
    
    // Validate RSI parameters
    if (params.rsiPeriod < 5 || params.rsiPeriod > 50) return false;
    if (params.rsiOversold < 10 || params.rsiOversold > 40) return false;
    if (params.rsiOverbought < 60 || params.rsiOverbought > 90) return false;
    
    // Validate risk management
    const risk = config.riskManagement;
    if (risk.maxPositionSize < 0.01 || risk.maxPositionSize > 0.2) return false;
    if (risk.stopLossPercent < 0.1 || risk.stopLossPercent > 1.0) return false;
    
    return true;
  }

  /**
   * Get required technical indicators
   */
  getRequiredIndicators(): string[] {
    return ['RSI', 'MACD', 'Volume'];
  }

  /**
   * Get supported timeframes
   */
  getTimeframes(): string[] {
    return ['1Min', '5Min'];
  }

  /**
   * Get risk level classification
   */
  getRiskLevel(): 'LOW' | 'MEDIUM' | 'HIGH' {
    return 'MEDIUM';
  }
}

// Export as default for the registry
export default SimpleMomentumStrategyWrapper;
