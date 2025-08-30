
import { MarketData, TechnicalIndicators, TradeSignal } from '../utils/types';

/**
 * FIX: NEW - Simple Momentum Strategy for 0DTE Options Trading
 * Implements 5-minute RSI-based entries with VIX filtering and time-based exits
 * Designed specifically for same-day expiration options on SPY
 */
export class SimpleMomentumStrategy {
  
  /**
   * Generate momentum-based trading signal for 0DTE options
   * Uses fast RSI, price velocity, and volume confirmation
   */
  static generateSignal(
    marketData: MarketData[],
    indicators: TechnicalIndicators,
    timeWindow: string,
    vixLevel?: number
  ): TradeSignal | null {
    
    if (marketData.length < 10) {
      return null;
    }
    
    const currentPrice = marketData[marketData.length - 1].close;
    let confidence = 40; // Base confidence for momentum strategy
    let action: 'BUY_CALL' | 'BUY_PUT' | null = null;
    let reason = 'Momentum: ';
    
    // FIX: 5-minute RSI-based momentum detection
    const fastRSI = indicators.fastRSI || indicators.rsi;
    const momentum = indicators.momentum || 0;
    const priceVelocity = indicators.priceVelocity || 0;
    const volumeRatio = indicators.volumeRatio || 1;
    
    console.log(`📈 MOMENTUM ANALYSIS: FastRSI: ${fastRSI.toFixed(1)}, Momentum: ${momentum.toFixed(2)}%, Velocity: ${priceVelocity.toFixed(4)}, Volume: ${volumeRatio.toFixed(1)}x`);
    
    // FIX: VIX-based volatility filtering for momentum trades
    if (vixLevel) {
      if (vixLevel > 40) {
        // High VIX - more conservative momentum thresholds
        confidence -= 10;
        reason += `High VIX (${vixLevel.toFixed(1)}), `;
      } else if (vixLevel < 15) {
        // Low VIX - need stronger momentum signals
        confidence -= 5;
        reason += `Low VIX (${vixLevel.toFixed(1)}), `;
      } else {
        // Optimal VIX range for momentum
        confidence += 5;
        reason += `Optimal VIX (${vixLevel.toFixed(1)}), `;
      }
    }
    
    // FIX: Time-of-day momentum logic
    if (timeWindow === 'MORNING_MOMENTUM') {
      // Morning: Look for breakout momentum
      if (fastRSI < 35 && momentum > 0.1 && priceVelocity > 0) {
        action = 'BUY_CALL';
        confidence += 25;
        reason += 'Morning oversold breakout, ';
      } else if (fastRSI > 65 && momentum < -0.1 && priceVelocity < 0) {
        action = 'BUY_PUT';
        confidence += 25;
        reason += 'Morning overbought breakdown, ';
      }
    } else if (timeWindow === 'AFTERNOON_DECAY') {
      // Afternoon: Look for mean reversion
      if (fastRSI > 70 && momentum > 0.15) {
        action = 'BUY_PUT';
        confidence += 20;
        reason += 'Afternoon overbought reversal, ';
      } else if (fastRSI < 30 && momentum < -0.15) {
        action = 'BUY_CALL';
        confidence += 20;
        reason += 'Afternoon oversold bounce, ';
      }
    } else {
      // Midday: Conservative momentum only
      if (fastRSI < 25 && momentum > 0.2 && priceVelocity > 0.01) {
        action = 'BUY_CALL';
        confidence += 15;
        reason += 'Midday strong oversold, ';
      } else if (fastRSI > 75 && momentum < -0.2 && priceVelocity < -0.01) {
        action = 'BUY_PUT';
        confidence += 15;
        reason += 'Midday strong overbought, ';
      }
    }
    
    // No clear momentum signal
    if (!action) {
      return null;
    }
    
    // FIX: Volume confirmation boost
    if (volumeRatio > 1.5) {
      confidence += 15;
      reason += `High volume (${volumeRatio.toFixed(1)}x), `;
    } else if (volumeRatio < 0.8) {
      confidence -= 10;
      reason += `Low volume (${volumeRatio.toFixed(1)}x), `;
    }
    
    // FIX: MACD confirmation
    if (indicators.macd > indicators.macdSignal && action === 'BUY_CALL') {
      confidence += 10;
      reason += 'MACD bullish, ';
    } else if (indicators.macd < indicators.macdSignal && action === 'BUY_PUT') {
      confidence += 10;
      reason += 'MACD bearish, ';
    }
    
    // FIX: Price action confirmation
    const recentBars = marketData.slice(-3);
    const priceChange = (recentBars[2].close - recentBars[0].close) / recentBars[0].close;
    
    if (action === 'BUY_CALL' && priceChange > 0.001) { // 0.1% positive
      confidence += 8;
      reason += 'Price momentum up, ';
    } else if (action === 'BUY_PUT' && priceChange < -0.001) { // 0.1% negative
      confidence += 8;
      reason += 'Price momentum down, ';
    }
    
    // FIX: Bollinger Bands confirmation
    if (action === 'BUY_CALL' && currentPrice < indicators.bbLower) {
      confidence += 12;
      reason += 'Below BB lower, ';
    } else if (action === 'BUY_PUT' && currentPrice > indicators.bbUpper) {
      confidence += 12;
      reason += 'Above BB upper, ';
    }
    
    reason = reason.slice(0, -2); // Remove trailing comma
    
    // Minimum confidence threshold for momentum trades
    if (confidence < 55) {
      return null;
    }
    
    console.log(`🚀 MOMENTUM SIGNAL: ${action} with ${confidence}% confidence - ${reason}`);
    
    return {
      action,
      confidence: Math.min(95, confidence),
      reason,
      indicators,
      timestamp: new Date(),
      positionSize: 0.02,
      stopLoss: 0.5,
      takeProfit: 1.0
    };
  }
  
  /**
   * FIX: Calculate optimal position size for momentum trades
   * Based on volatility and momentum strength
   */
  static calculateMomentumPositionSize(
    baseSize: number,
    momentum: number,
    volatility: number,
    confidence: number
  ): number {
    
    let adjustedSize = baseSize;
    
    // Adjust for momentum strength
    const momentumStrength = Math.abs(momentum);
    if (momentumStrength > 0.3) {
      adjustedSize = Math.floor(baseSize * 1.2); // Increase for strong momentum
    } else if (momentumStrength < 0.1) {
      adjustedSize = Math.floor(baseSize * 0.8); // Decrease for weak momentum
    }
    
    // Adjust for confidence
    const confidenceMultiplier = confidence / 70; // Base confidence of 70%
    adjustedSize = Math.floor(adjustedSize * confidenceMultiplier);
    
    // Adjust for volatility
    if (volatility > 0.3) {
      adjustedSize = Math.floor(adjustedSize * 0.7); // Reduce for high volatility
    } else if (volatility < 0.15) {
      adjustedSize = Math.floor(adjustedSize * 1.1); // Increase for low volatility
    }
    
    // Ensure reasonable bounds
    return Math.max(1, Math.min(adjustedSize, 8));
  }
  
  /**
   * FIX: Determine exit conditions for momentum trades
   * Time-based exits with profit targets optimized for 0DTE
   */
  static shouldExitMomentumTrade(
    entryPrice: number,
    currentPrice: number,
    entryTime: Date,
    currentTime: Date,
    side: 'CALL' | 'PUT',
    indicators: TechnicalIndicators
  ): { shouldExit: boolean; reason: string } {
    
    const pnlPercent = ((currentPrice - entryPrice) / entryPrice) * 100;
    const holdingMinutes = (currentTime.getTime() - entryTime.getTime()) / (1000 * 60);
    
    // FIX: Time-based exits for 0DTE momentum
    if (holdingMinutes >= 240) { // 4 hours max
      return { shouldExit: true, reason: 'Maximum holding time reached' };
    }
    
    // FIX: Profit targets for momentum trades
    if (pnlPercent >= 40) { // 40% profit target
      return { shouldExit: true, reason: 'Profit target reached' };
    }
    
    // FIX: Stop loss for momentum trades
    if (pnlPercent <= -25) { // 25% stop loss
      return { shouldExit: true, reason: 'Stop loss triggered' };
    }
    
    // FIX: Momentum reversal exits
    const fastRSI = indicators.fastRSI || indicators.rsi;
    
    if (side === 'CALL') {
      // Exit calls if momentum reverses
      if (fastRSI > 75 && indicators.macd < indicators.macdSignal) {
        return { shouldExit: true, reason: 'Bullish momentum exhausted' };
      }
    } else {
      // Exit puts if momentum reverses
      if (fastRSI < 25 && indicators.macd > indicators.macdSignal) {
        return { shouldExit: true, reason: 'Bearish momentum exhausted' };
      }
    }
    
    // FIX: Time decay protection (last 30 minutes of trading)
    const currentHour = currentTime.getHours() + currentTime.getMinutes() / 60;
    if (currentHour >= 15.5 && pnlPercent < 10) { // 3:30 PM ET
      return { shouldExit: true, reason: 'Time decay protection' };
    }
    
    return { shouldExit: false, reason: 'Continue holding' };
  }
}
