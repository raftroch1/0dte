
import { MarketData, TechnicalIndicators } from './types';
import { TechnicalAnalysis } from './technical-indicators_improved';

export interface MarketRegime {
  regime: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number; // 0-100
  signals: {
    trend: 'UP' | 'DOWN' | 'SIDEWAYS';
    volatility: 'LOW' | 'MEDIUM' | 'HIGH';
    momentum: 'STRONG' | 'WEAK' | 'MIXED';
    intradayRegime: 'MORNING_MOMENTUM' | 'MIDDAY_CONSOLIDATION' | 'AFTERNOON_DECAY';
  };
  reasoning: string[];
}

export class MarketRegimeDetector {
  
  /**
   * FIX: Enhanced regime detection with intraday volatility regimes and time-of-day logic
   * Improved for 0DTE trading with volume-based confirmation
   */
  static detectRegime(
    marketData: MarketData[], 
    optionsChain: any[] = [],
    vixLevel?: number
  ): MarketRegime {
    if (marketData.length < 20) { // Reduced from 50 for faster detection
      return this.getDefaultRegime('Insufficient data for regime detection');
    }

    const indicators = TechnicalAnalysis.calculateAllIndicators(marketData, 14, 12, 26, 9, 20, 2);
    if (!indicators) {
      return this.getDefaultRegime('Technical indicators unavailable');
    }

    const reasoning: string[] = [];
    
    // FIX: Enhanced regime detection with multiple timeframes
    const currentPrice = marketData[marketData.length - 1].close;
    const sma5 = this.calculateSMA(marketData, 5);   // Short-term trend
    const sma20 = this.calculateSMA(marketData, 20); // Medium-term trend
    const sma50 = this.calculateSMA(marketData, Math.min(50, marketData.length - 1)); // Long-term trend
    
    // FIX: Intraday regime detection based on time of day
    const intradayRegime = this.detectIntradayRegime();
    
    // FIX: Volume analysis for confirmation
    const volumeAnalysis = this.analyzeVolume(marketData);
    
    // FIX: Volatility regime detection
    const volatilityRegime = this.detectVolatilityRegime(marketData, vixLevel);
    
    // FIX: Multi-factor regime scoring
    let bullishScore = 0;
    let bearishScore = 0;
    let confidence = 30; // Base confidence
    
    // 1. Price vs Moving Averages (40% weight)
    if (currentPrice > sma5 && sma5 > sma20) {
      bullishScore += 40;
      reasoning.push(`Price above SMA5 (${sma5.toFixed(2)}) and SMA20 (${sma20.toFixed(2)})`);
    } else if (currentPrice < sma5 && sma5 < sma20) {
      bearishScore += 40;
      reasoning.push(`Price below SMA5 (${sma5.toFixed(2)}) and SMA20 (${sma20.toFixed(2)})`);
    }
    
    // 2. RSI Analysis (25% weight)
    if (indicators.rsi > 55) {
      bullishScore += Math.min(25, (indicators.rsi - 55) * 1.25);
      reasoning.push(`RSI bullish: ${indicators.rsi.toFixed(1)}`);
    } else if (indicators.rsi < 45) {
      bearishScore += Math.min(25, (45 - indicators.rsi) * 1.25);
      reasoning.push(`RSI bearish: ${indicators.rsi.toFixed(1)}`);
    }
    
    // 3. MACD Analysis (20% weight)
    if (indicators.macd > indicators.macdSignal && indicators.macdHistogram > 0) {
      bullishScore += 20;
      reasoning.push('MACD bullish crossover');
    } else if (indicators.macd < indicators.macdSignal && indicators.macdHistogram < 0) {
      bearishScore += 20;
      reasoning.push('MACD bearish crossover');
    }
    
    // 4. Volume Confirmation (15% weight)
    if (volumeAnalysis.trend === 'INCREASING' && volumeAnalysis.strength > 1.2) {
      const volumeBoost = 15;
      if (bullishScore > bearishScore) {
        bullishScore += volumeBoost;
        reasoning.push(`Volume confirms bullish trend: ${volumeAnalysis.strength.toFixed(1)}x avg`);
      } else if (bearishScore > bullishScore) {
        bearishScore += volumeBoost;
        reasoning.push(`Volume confirms bearish trend: ${volumeAnalysis.strength.toFixed(1)}x avg`);
      }
    }
    
    // FIX: Determine regime based on scores
    let regime: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    const scoreDifference = Math.abs(bullishScore - bearishScore);
    
    if (bullishScore > bearishScore && scoreDifference > 20) {
      regime = 'BULLISH';
      confidence = Math.min(85, 50 + scoreDifference);
    } else if (bearishScore > bullishScore && scoreDifference > 20) {
      regime = 'BEARISH';
      confidence = Math.min(85, 50 + scoreDifference);
    } else {
      regime = 'NEUTRAL';
      confidence = Math.max(25, 50 - scoreDifference); // Lower confidence for neutral
    }
    
    // FIX: Adjust confidence based on intraday regime
    if (intradayRegime === 'MORNING_MOMENTUM' || intradayRegime === 'AFTERNOON_DECAY') {
      confidence += 10; // Higher confidence during active periods
    }
    
    reasoning.push(`Intraday regime: ${intradayRegime}`);
    reasoning.push(`Volume trend: ${volumeAnalysis.trend} (${volumeAnalysis.strength.toFixed(1)}x)`);
    reasoning.push(`Volatility: ${volatilityRegime}`);
    
    return {
      regime,
      confidence: Math.min(90, confidence),
      signals: {
        trend: bullishScore > bearishScore + 10 ? 'UP' : bearishScore > bullishScore + 10 ? 'DOWN' : 'SIDEWAYS',
        volatility: volatilityRegime,
        momentum: scoreDifference > 30 ? 'STRONG' : scoreDifference > 15 ? 'WEAK' : 'MIXED',
        intradayRegime
      },
      reasoning
    };
  }
  
  /**
   * FIX: NEW - Detect intraday regime based on time of day
   * Essential for 0DTE trading strategy selection
   */
  private static detectIntradayRegime(): 'MORNING_MOMENTUM' | 'MIDDAY_CONSOLIDATION' | 'AFTERNOON_DECAY' {
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const currentTime = hour + minute / 60;
    
    // Market hours: 9:30 AM - 4:00 PM ET
    if (currentTime >= 9.5 && currentTime <= 11) {
      return 'MORNING_MOMENTUM';
    } else if (currentTime > 11 && currentTime < 14) {
      return 'MIDDAY_CONSOLIDATION';
    } else if (currentTime >= 14 && currentTime <= 16) {
      return 'AFTERNOON_DECAY';
    } else {
      return 'MIDDAY_CONSOLIDATION'; // Default for after hours
    }
  }
  
  /**
   * FIX: NEW - Analyze volume patterns for trend confirmation
   * Volume analysis helps confirm the strength of price movements
   */
  private static analyzeVolume(marketData: MarketData[]): { 
    trend: 'INCREASING' | 'DECREASING' | 'STABLE'; 
    strength: number; 
    avgVolume: number 
  } {
    if (marketData.length < 10) {
      return { trend: 'STABLE', strength: 1, avgVolume: 0 };
    }
    
    const recentVolumes = marketData.slice(-5).map(d => Number(d.volume || 0));
    const historicalVolumes = marketData.slice(-20, -5).map(d => Number(d.volume || 0));
    
    const recentAvg = recentVolumes.reduce((sum, vol) => sum + vol, 0) / recentVolumes.length;
    const historicalAvg = historicalVolumes.reduce((sum, vol) => sum + vol, 0) / historicalVolumes.length;
    
    const strength = historicalAvg > 0 ? recentAvg / historicalAvg : 1;
    
    let trend: 'INCREASING' | 'DECREASING' | 'STABLE';
    if (strength > 1.3) {
      trend = 'INCREASING';
    } else if (strength < 0.7) {
      trend = 'DECREASING';
    } else {
      trend = 'STABLE';
    }
    
    return { trend, strength, avgVolume: historicalAvg };
  }
  
  /**
   * FIX: NEW - Detect volatility regime for position sizing
   * Helps determine appropriate position sizes and risk management
   */
  private static detectVolatilityRegime(
    marketData: MarketData[], 
    vixLevel?: number
  ): 'LOW' | 'MEDIUM' | 'HIGH' {
    
    // Calculate recent price volatility
    const recentPrices = marketData.slice(-10).map(d => d.close);
    const returns = [];
    for (let i = 1; i < recentPrices.length; i++) {
      returns.push((recentPrices[i] - recentPrices[i-1]) / recentPrices[i-1]);
    }
    
    const avgReturn = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - avgReturn, 2), 0) / returns.length;
    const volatility = Math.sqrt(variance) * Math.sqrt(252); // Annualized
    
    // Use VIX if available, otherwise use calculated volatility
    const volLevel = vixLevel ? vixLevel / 100 : volatility;
    
    if (volLevel < 0.15) {
      return 'LOW';
    } else if (volLevel < 0.25) {
      return 'MEDIUM';
    } else {
      return 'HIGH';
    }
  }

  private static calculateSMA(marketData: MarketData[], period: number): number {
    if (marketData.length < period) return marketData[marketData.length - 1].close;
    
    const recentPrices = marketData.slice(-period).map(d => d.close);
    return recentPrices.reduce((sum, price) => sum + price, 0) / period;
  }

  private static getDefaultRegime(reason: string): MarketRegime {
    return {
      regime: 'NEUTRAL',
      confidence: 25, // Reduced from 30 to allow more trading
      signals: { 
        trend: 'SIDEWAYS', 
        volatility: 'MEDIUM', 
        momentum: 'MIXED',
        intradayRegime: 'MIDDAY_CONSOLIDATION'
      },
      reasoning: [reason]
    };
  }
}
