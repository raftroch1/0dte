
import { MarketData, TechnicalIndicators, TradeSignal, OptionsChain } from '../utils/types';
import { MarketRegimeDetector, MarketRegime } from '../data/market-regime-detector';
import { TechnicalAnalysis } from '../data/technical-indicators';
import { SimpleMomentumStrategy } from './simple-momentum-strategy';

export interface StrategySelection {
  selectedStrategy: 'BUY_CALL' | 'BUY_PUT' | 'BULL_PUT_SPREAD' | 'BEAR_CALL_SPREAD' | 'IRON_CONDOR' | 'MOMENTUM_CALL' | 'MOMENTUM_PUT' | 'NO_TRADE';
  marketRegime: MarketRegime;
  signal: TradeSignal | null;
  reasoning: string[];
}

export class AdaptiveStrategySelector {
  
  /**
   * Check volatility conditions for options trading
   * FIX: Relaxed VIX threshold from 35 to 50 for more trading opportunities
   */
  private static checkVolatilityConditions(
    optionsChain: OptionsChain[], 
    vixLevel?: number
  ): { acceptable: boolean; reason: string } {
    
    if (optionsChain.length === 0) {
      return { acceptable: false, reason: 'No options data available' };
    }
    
    // Calculate average implied volatility across chain
    const validOptions = optionsChain.filter(opt => opt.impliedVolatility && opt.impliedVolatility > 0);
    if (validOptions.length === 0) {
      return { acceptable: false, reason: 'No valid IV data' };
    }
    
    const avgIV = validOptions.reduce((sum, opt) => sum + (opt.impliedVolatility || 0), 0) / validOptions.length;
    
    // FIX: Relaxed volatility filters for 0-DTE trading to generate more trades
    
    // 1. Extreme volatility conditions (avoid trading) - RELAXED from 35 to 50
    if (vixLevel && vixLevel > 50) {
      return { acceptable: false, reason: `VIX too high: ${vixLevel.toFixed(1)} (>50)` };
    }
    
    if (avgIV > 0.8) { // Relaxed from 60% to 80% IV
      return { acceptable: false, reason: `IV too high: ${(avgIV * 100).toFixed(1)}% (>80%)` };
    }
    
    // 2. Very low volatility - RELAXED from 8% to 5%
    if (avgIV < 0.05) { // 5% IV is very low
      return { acceptable: false, reason: `IV too low: ${(avgIV * 100).toFixed(1)}% (<5%)` };
    }
    
    // 3. VIX/IV divergence check - RELAXED from 15% to 25%
    if (vixLevel && Math.abs(vixLevel / 100 - avgIV) > 0.25) { // 25% divergence
      return { acceptable: false, reason: `VIX/IV divergence: VIX ${vixLevel.toFixed(1)}, IV ${(avgIV * 100).toFixed(1)}%` };
    }
    
    // 4. Acceptable volatility range
    const volDescription = avgIV < 0.15 ? 'Low' : avgIV < 0.25 ? 'Normal' : avgIV < 0.4 ? 'Elevated' : 'High';
    return { 
      acceptable: true, 
      reason: `${volDescription} IV ${(avgIV * 100).toFixed(1)}%${vixLevel ? `, VIX ${vixLevel.toFixed(1)}` : ''}` 
    };
  }
  
  /**
   * Check liquidity conditions for options trading
   * FIX: Relaxed bid-ask spread threshold from 25% to 40% for more trading opportunities
   */
  private static checkLiquidityConditions(
    optionsChain: OptionsChain[], 
    currentPrice: number
  ): { acceptable: boolean; reason: string } {
    
    if (optionsChain.length < 10) {
      return { acceptable: false, reason: `Insufficient options: ${optionsChain.length} contracts (<10)` };
    }
    
    // Focus on near-the-money options (most liquid)
    const ntmOptions = optionsChain.filter(opt => 
      Math.abs(opt.strike - currentPrice) <= currentPrice * 0.1 // Within 10% of current price
    );
    
    if (ntmOptions.length < 4) {
      return { acceptable: false, reason: `Insufficient NTM options: ${ntmOptions.length} contracts (<4)` };
    }
    
    // FIX: Relaxed liquidity filters for 0DTE trading
    
    // 1. Bid-ask spread analysis - RELAXED from 25% to 40%
    const spreadAnalysis = ntmOptions.map(opt => {
      const spread = opt.ask - opt.bid;
      const midPrice = (opt.ask + opt.bid) / 2;
      const spreadPercent = midPrice > 0 ? (spread / midPrice) * 100 : 100;
      return { option: opt, spread, spreadPercent };
    });
    
    const avgSpreadPercent = spreadAnalysis.reduce((sum, item) => sum + item.spreadPercent, 0) / spreadAnalysis.length;
    
    // Reject if spreads too wide (poor liquidity) - RELAXED from 25% to 40%
    if (avgSpreadPercent > 40) { // 40% average spread threshold
      return { acceptable: false, reason: `Wide spreads: ${avgSpreadPercent.toFixed(1)}% avg (>40%)` };
    }
    
    // 2. Minimum bid/ask requirements - RELAXED
    const poorPricing = ntmOptions.filter(opt => opt.bid < 0.02 || opt.ask > 100); // More lenient
    if (poorPricing.length > ntmOptions.length * 0.5) { // More than 50% have poor pricing (was 30%)
      return { acceptable: false, reason: `Poor pricing on ${poorPricing.length}/${ntmOptions.length} NTM options` };
    }
    
    // 3. Volume and open interest (if available) - RELAXED
    const volumeData = ntmOptions.filter(opt => opt.volume !== undefined && opt.openInterest !== undefined);
    if (volumeData.length > 0) {
      const avgVolume = volumeData.reduce((sum, opt) => sum + (opt.volume || 0), 0) / volumeData.length;
      const avgOI = volumeData.reduce((sum, opt) => sum + (opt.openInterest || 0), 0) / volumeData.length;
      
      // RELAXED from Vol 10, OI 100 to Vol 5, OI 50
      if (avgVolume < 5 && avgOI < 50) {
        return { acceptable: false, reason: `Low liquidity: Vol ${avgVolume.toFixed(0)}, OI ${avgOI.toFixed(0)}` };
      }
    }
    
    // 4. Delta distribution check - RELAXED
    const deltaOptions = ntmOptions.filter(opt => opt.delta !== undefined);
    if (deltaOptions.length >= 4) {
      const deltas = deltaOptions.map(opt => Math.abs(opt.delta || 0));
      const deltaRange = Math.max(...deltas) - Math.min(...deltas);
      
      // RELAXED from 0.3 to 0.2
      if (deltaRange < 0.2) { // Too narrow delta range
        return { acceptable: false, reason: `Narrow delta range: ${deltaRange.toFixed(2)} (<0.2)` };
      }
    }
    
    // All checks passed
    const liquidityQuality = avgSpreadPercent < 15 ? 'Excellent' : 
                            avgSpreadPercent < 25 ? 'Good' : 
                            avgSpreadPercent < 35 ? 'Fair' : 'Poor';
    
    return { 
      acceptable: true, 
      reason: `${liquidityQuality} liquidity: ${ntmOptions.length} NTM options, ${avgSpreadPercent.toFixed(1)}% avg spread` 
    };
  }
  
  /**
   * FIX: Check if current time is within 0DTE trading hours
   * 0DTE options should be traded during specific market hours for optimal results
   */
  private static check0DTETradingHours(): { acceptable: boolean; reason: string; timeWindow: string } {
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const currentTime = hour + minute / 60;
    
    // Market opens at 9:30 AM ET, closes at 4:00 PM ET
    const marketOpen = 9.5; // 9:30 AM
    const marketClose = 16; // 4:00 PM
    const morningMomentumEnd = 11; // 11:00 AM
    const afternoonDecayStart = 14; // 2:00 PM
    
    if (currentTime < marketOpen || currentTime > marketClose) {
      return { 
        acceptable: false, 
        reason: 'Market closed', 
        timeWindow: 'CLOSED' 
      };
    }
    
    // Morning momentum window (9:30-11:00 AM)
    if (currentTime >= marketOpen && currentTime <= morningMomentumEnd) {
      return { 
        acceptable: true, 
        reason: 'Morning momentum window', 
        timeWindow: 'MORNING_MOMENTUM' 
      };
    }
    
    // Afternoon decay window (2:00-4:00 PM)
    if (currentTime >= afternoonDecayStart && currentTime <= marketClose) {
      return { 
        acceptable: true, 
        reason: 'Afternoon decay window', 
        timeWindow: 'AFTERNOON_DECAY' 
      };
    }
    
    // Midday consolidation (11:00 AM - 2:00 PM) - less favorable for 0DTE
    return { 
      acceptable: true, 
      reason: 'Midday consolidation - reduced activity', 
      timeWindow: 'MIDDAY_CONSOLIDATION' 
    };
  }
  
  // Alias for backward compatibility
  static selectStrategy = this.generateAdaptiveSignal;

  static generateAdaptiveSignal(
    marketData: MarketData[], 
    optionsChain: OptionsChain[], 
    strategy: any, // Strategy object needed for parameters
    vixLevel?: number
  ): StrategySelection {
    
    const currentPrice = marketData[marketData.length - 1].close;
    
    console.log(`🎯 ADAPTIVE STRATEGY - Analyzing market for 0DTE strategy selection...`);
    console.log(`📊 Data: ${marketData.length} bars, ${optionsChain.length} options, SPY: $${currentPrice.toFixed(2)}`);
    
    // FIX: Check 0DTE trading hours first
    const timeCheck = this.check0DTETradingHours();
    console.log(`⏰ TIME CHECK: ${timeCheck.reason} (${timeCheck.timeWindow})`);
    
    // 1. DETECT MARKET REGIME
    const marketRegime = MarketRegimeDetector.detectRegime(marketData, optionsChain, vixLevel);
    
    console.log(`🌍 REGIME DETECTED: ${marketRegime.regime} (${marketRegime.confidence}% confidence)`);
    
    const reasoning: string[] = [
      `Market regime: ${marketRegime.regime} (${marketRegime.confidence}% confidence)`,
      `Trading window: ${timeCheck.reason}`,
      ...marketRegime.reasoning
    ];
    
    // 2. STRATEGY SELECTION BASED ON REGIME
    let selectedStrategy: 'BUY_CALL' | 'BUY_PUT' | 'BULL_PUT_SPREAD' | 'BEAR_CALL_SPREAD' | 'IRON_CONDOR' | 'MOMENTUM_CALL' | 'MOMENTUM_PUT' | 'NO_TRADE';
    let signal: TradeSignal | null = null;
    
    // FIX: Relaxed minimum confidence threshold from 40% to 25%
    if (marketRegime.confidence < 25) {
      reasoning.push('Regime confidence too low - NO TRADE');
      return {
        selectedStrategy: 'NO_TRADE',
        marketRegime,
        signal: null,
        reasoning
      };
    }
    
    // ENHANCED: Volatility and Liquidity Filters
    const volatilityFilters = this.checkVolatilityConditions(optionsChain, vixLevel);
    const liquidityFilters = this.checkLiquidityConditions(optionsChain, currentPrice);
    
    if (!volatilityFilters.acceptable) {
      reasoning.push(`Volatility filter failed: ${volatilityFilters.reason}`);
      return {
        selectedStrategy: 'NO_TRADE',
        marketRegime,
        signal: null,
        reasoning
      };
    }
    
    if (!liquidityFilters.acceptable) {
      reasoning.push(`Liquidity filter failed: ${liquidityFilters.reason}`);
      return {
        selectedStrategy: 'NO_TRADE',
        marketRegime,
        signal: null,
        reasoning
      };
    }
    
    reasoning.push(`✅ Volatility: ${volatilityFilters.reason}`);
    reasoning.push(`✅ Liquidity: ${liquidityFilters.reason}`);
    
    // FIX: NEW 5-MINUTE MOMENTUM STRATEGY FOR 0DTE
    // Calculate 5-minute technical indicators for momentum trading
    const indicators = TechnicalAnalysis.calculateAllIndicators(
      marketData,
      strategy.rsiPeriod || 14,
      strategy.macdFast || 12,
      strategy.macdSlow || 26,
      strategy.macdSignal || 9,
      strategy.bbPeriod || 20,
      strategy.bbStdDev || 2
    );
    
    if (!indicators) {
      selectedStrategy = 'NO_TRADE';
      reasoning.push('Technical indicators calculation failed');
      signal = null;
    } else {
      // FIX: NEW MOMENTUM STRATEGY IMPLEMENTATION
      const momentumSignal = SimpleMomentumStrategy.generateSignal(
        marketData, 
        indicators, 
        timeCheck.timeWindow,
        vixLevel
      );
      
      if (momentumSignal && momentumSignal.confidence > 60) {
        // Use momentum strategy if high confidence
        selectedStrategy = momentumSignal.action === 'BUY_CALL' ? 'MOMENTUM_CALL' : 'MOMENTUM_PUT';
        signal = momentumSignal;
        reasoning.push(`🚀 MOMENTUM STRATEGY: ${momentumSignal.reason}`);
      } else {
        // Fall back to regime-based naked options
        switch (marketRegime.regime) {
          case 'BULLISH':
            selectedStrategy = 'BUY_CALL';
            reasoning.push('BULLISH regime → Buy Call (naked option)');
            signal = this.generateNakedCallSignal(indicators, marketData, strategy);
            break;
          
          case 'BEARISH':
            selectedStrategy = 'BUY_PUT';
            reasoning.push('BEARISH regime → Buy Put (naked option)');
            signal = this.generateNakedPutSignal(indicators, marketData, strategy);
            break;
          
          case 'NEUTRAL':
            // FIX: More aggressive RSI thresholds for 0DTE
            if (indicators.rsi < 35) { // Was 30
              selectedStrategy = 'BUY_CALL';
              reasoning.push('NEUTRAL regime + RSI oversold → Buy Call');
              signal = this.generateNakedCallSignal(indicators, marketData, strategy);
            } else if (indicators.rsi > 65) { // Was 70
              selectedStrategy = 'BUY_PUT';
              reasoning.push('NEUTRAL regime + RSI overbought → Buy Put');
              signal = this.generateNakedPutSignal(indicators, marketData, strategy);
            } else {
              selectedStrategy = 'NO_TRADE';
              reasoning.push('NEUTRAL regime - no RSI extreme');
              signal = null;
            }
            break;
          
          default:
            selectedStrategy = 'NO_TRADE';
            reasoning.push('Unknown regime - NO TRADE');
            signal = null;
            break;
        }
      }
    }
    
    console.log(`🎯 STRATEGY SELECTED: ${selectedStrategy}`);
    if (signal) {
      console.log(`✅ SIGNAL GENERATED: ${signal.action} with ${signal.confidence}% confidence`);
    } else {
      console.log(`❌ NO SIGNAL: Strategy not implemented or conditions not met`);
    }
    
    return {
      selectedStrategy,
      marketRegime,
      signal,
      reasoning
    };
  }
  
  /**
   * Generate naked call signal (bullish)
   * FIX: Enhanced for 0DTE with more aggressive confidence scoring
   */
  private static generateNakedCallSignal(
    indicators: any,
    marketData: MarketData[],
    strategy: any
  ): TradeSignal | null {
    
    const currentPrice = marketData[marketData.length - 1].close;
    let confidence = 50;
    let reason = 'Naked Call: ';
    
    // FIX: More aggressive RSI thresholds for 0DTE
    if (indicators.rsi < 35) { // Was 30
      confidence += 20; // Increased from 15
      reason += `RSI oversold (${indicators.rsi.toFixed(1)}), `;
    }
    
    // MACD bullish
    if (indicators.macd > indicators.macdSignal) {
      confidence += 15; // Increased from 10
      reason += 'MACD bullish, ';
    }
    
    // Price below BB lower band (oversold)
    if (currentPrice < indicators.bbLower) {
      confidence += 15; // Increased from 10
      reason += 'Price below BB lower, ';
    }
    
    // Volume confirmation (if available)
    const currentVolume = Number(marketData[marketData.length - 1].volume || 0);
    const avgVolume = marketData.slice(-20).reduce((sum, bar) => sum + Number(bar.volume || 0), 0) / 20;
    if (currentVolume > avgVolume * 1.2) {
      confidence += 10; // Increased from 5
      reason += 'High volume, ';
    }
    
    // FIX: Add momentum confirmation for 0DTE
    const recentBars = marketData.slice(-3);
    const priceChange = (recentBars[2].close - recentBars[0].close) / recentBars[0].close;
    if (priceChange > 0.002) { // 0.2% positive momentum
      confidence += 10;
      reason += 'Positive momentum, ';
    }
    
    reason = reason.slice(0, -2); // Remove trailing comma
    
    return {
      action: 'BUY_CALL',
      confidence: Math.min(90, confidence), // Increased max from 85
      reason,
      indicators,
      timestamp: new Date(),
      positionSize: 0.02,
      stopLoss: 0.5,
      takeProfit: 1.0
    };
  }
  
  /**
   * Generate naked put signal (bearish)
   * FIX: Enhanced for 0DTE with more aggressive confidence scoring
   */
  private static generateNakedPutSignal(
    indicators: any,
    marketData: MarketData[],
    strategy: any
  ): TradeSignal | null {
    
    const currentPrice = marketData[marketData.length - 1].close;
    let confidence = 50;
    let reason = 'Naked Put: ';
    
    // FIX: More aggressive RSI thresholds for 0DTE
    if (indicators.rsi > 65) { // Was 70
      confidence += 20; // Increased from 15
      reason += `RSI overbought (${indicators.rsi.toFixed(1)}), `;
    }
    
    // MACD bearish
    if (indicators.macd < indicators.macdSignal) {
      confidence += 15; // Increased from 10
      reason += 'MACD bearish, ';
    }
    
    // Price above BB upper band (overbought)
    if (currentPrice > indicators.bbUpper) {
      confidence += 15; // Increased from 10
      reason += 'Price above BB upper, ';
    }
    
    // Volume confirmation (if available)
    const currentVolume = Number(marketData[marketData.length - 1].volume || 0);
    const avgVolume = marketData.slice(-20).reduce((sum, bar) => sum + Number(bar.volume || 0), 0) / 20;
    if (currentVolume > avgVolume * 1.2) {
      confidence += 10; // Increased from 5
      reason += 'High volume, ';
    }
    
    // FIX: Add momentum confirmation for 0DTE
    const recentBars = marketData.slice(-3);
    const priceChange = (recentBars[2].close - recentBars[0].close) / recentBars[0].close;
    if (priceChange < -0.002) { // 0.2% negative momentum
      confidence += 10;
      reason += 'Negative momentum, ';
    }
    
    reason = reason.slice(0, -2); // Remove trailing comma
    
    return {
      action: 'BUY_PUT',
      confidence: Math.min(90, confidence), // Increased max from 85
      reason,
      indicators,
      timestamp: new Date(),
      positionSize: 0.02,
      stopLoss: 0.5,
      takeProfit: 1.0
    };
  }
}
