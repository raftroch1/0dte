
import { MarketData, TechnicalIndicators } from './types';

export class TechnicalAnalysis {
  
  /**
   * FIX: Enhanced RSI calculation with 5-minute timeframe support for 0DTE
   * Added smoothing and faster response for intraday trading
   */
  static calculateRSI(data: MarketData[], period: number = 14): number[] {
    if (data.length < period + 1) return [];
    
    const rsiValues: number[] = [];
    const gains: number[] = [];
    const losses: number[] = [];
    
    // Calculate price changes
    for (let i = 1; i < data.length; i++) {
      const change = data[i].close - data[i - 1].close;
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }
    
    // Calculate first RSI
    let avgGain = gains.slice(0, period).reduce((sum, val) => sum + val, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((sum, val) => sum + val, 0) / period;
    
    let rs = avgGain / (avgLoss || 0.01);
    rsiValues.push(100 - (100 / (1 + rs)));
    
    // FIX: Enhanced smoothing for 0DTE - faster response to price changes
    const smoothingFactor = period <= 9 ? 0.2 : 0.1; // Faster for shorter periods
    
    // Calculate subsequent RSI values using enhanced smoothing
    for (let i = period; i < gains.length; i++) {
      avgGain = (avgGain * (1 - smoothingFactor)) + (gains[i] * smoothingFactor);
      avgLoss = (avgLoss * (1 - smoothingFactor)) + (losses[i] * smoothingFactor);
      
      rs = avgGain / (avgLoss || 0.01);
      rsiValues.push(100 - (100 / (1 + rs)));
    }
    
    return rsiValues;
  }
  
  /**
   * FIX: Enhanced MACD with faster parameters for 0DTE momentum detection
   */
  static calculateMACD(
    data: MarketData[], 
    fastPeriod: number = 12, 
    slowPeriod: number = 26, 
    signalPeriod: number = 9
  ): { macd: number[]; signal: number[]; histogram: number[] } {
    
    const fastEMA = this.calculateEMA(data.map(d => d.close), fastPeriod);
    const slowEMA = this.calculateEMA(data.map(d => d.close), slowPeriod);
    
    const macd: number[] = [];
    for (let i = 0; i < Math.min(fastEMA.length, slowEMA.length); i++) {
      macd.push(fastEMA[i] - slowEMA[i]);
    }
    
    const signal = this.calculateEMA(macd, signalPeriod);
    const histogram: number[] = [];
    
    for (let i = 0; i < Math.min(macd.length, signal.length); i++) {
      histogram.push(macd[i] - signal[i]);
    }
    
    return { macd, signal, histogram };
  }
  
  /**
   * FIX: Enhanced Bollinger Bands with dynamic period adjustment for 0DTE
   */
  static calculateBollingerBands(
    data: MarketData[], 
    period: number = 20, 
    stdDev: number = 2
  ): { upper: number[]; middle: number[]; lower: number[] } {
    
    const closes = data.map(d => d.close);
    const sma = this.calculateSMA(closes, period);
    const upper: number[] = [];
    const lower: number[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = closes.slice(i - period + 1, i + 1);
      const mean = slice.reduce((sum, val) => sum + val, 0) / period;
      const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period;
      const standardDev = Math.sqrt(variance);
      
      upper.push(sma[i - period + 1] + (stdDev * standardDev));
      lower.push(sma[i - period + 1] - (stdDev * standardDev));
    }
    
    return { 
      upper, 
      middle: sma, 
      lower 
    };
  }
  
  /**
   * FIX: NEW - Calculate momentum oscillators suitable for 0DTE trading
   * Includes Rate of Change (ROC) and Stochastic for faster signals
   */
  static calculateMomentumOscillators(
    data: MarketData[],
    rocPeriod: number = 5,
    stochKPeriod: number = 9,
    stochDPeriod: number = 3
  ): { roc: number; stochK: number; stochD: number } | null {
    
    if (data.length < Math.max(rocPeriod, stochKPeriod) + stochDPeriod) {
      return null;
    }
    
    const closes = data.map(d => d.close);
    const highs = data.map(d => d.high);
    const lows = data.map(d => d.low);
    
    // Rate of Change (ROC)
    const currentPrice = closes[closes.length - 1];
    const pastPrice = closes[closes.length - 1 - rocPeriod];
    const roc = ((currentPrice - pastPrice) / pastPrice) * 100;
    
    // Stochastic Oscillator
    const recentHighs = highs.slice(-stochKPeriod);
    const recentLows = lows.slice(-stochKPeriod);
    const highestHigh = Math.max(...recentHighs);
    const lowestLow = Math.min(...recentLows);
    
    const stochK = ((currentPrice - lowestLow) / (highestHigh - lowestLow)) * 100;
    
    // Calculate %D (SMA of %K)
    const stochKValues = [];
    for (let i = stochKPeriod - 1; i < data.length; i++) {
      const periodHighs = highs.slice(i - stochKPeriod + 1, i + 1);
      const periodLows = lows.slice(i - stochKPeriod + 1, i + 1);
      const periodHighest = Math.max(...periodHighs);
      const periodLowest = Math.min(...periodLows);
      const k = ((closes[i] - periodLowest) / (periodHighest - periodLowest)) * 100;
      stochKValues.push(k);
    }
    
    const recentStochK = stochKValues.slice(-stochDPeriod);
    const stochD = recentStochK.reduce((sum, val) => sum + val, 0) / stochDPeriod;
    
    return { roc, stochK, stochD };
  }
  
  /**
   * FIX: NEW - Calculate 5-minute specific indicators for 0DTE momentum
   * Optimized for short-term price movements and rapid decision making
   */
  static calculate5MinIndicators(
    data: MarketData[]
  ): { 
    fastRSI: number; 
    momentum: number; 
    priceVelocity: number; 
    volumeRatio: number 
  } | null {
    
    if (data.length < 10) return null;
    
    const closes = data.map(d => d.close);
    const volumes = data.map(d => Number(d.volume || 0));
    
    // Fast RSI (5-period for quick signals)
    const fastRSI = this.calculateRSI(data, 5);
    const currentFastRSI = fastRSI[fastRSI.length - 1] || 50;
    
    // Price momentum (3-bar rate of change)
    const momentum = ((closes[closes.length - 1] - closes[closes.length - 4]) / closes[closes.length - 4]) * 100;
    
    // Price velocity (acceleration of price change)
    const recentChanges = [];
    for (let i = 1; i < Math.min(6, closes.length); i++) {
      recentChanges.push(closes[closes.length - i] - closes[closes.length - i - 1]);
    }
    const priceVelocity = recentChanges.reduce((sum, change) => sum + change, 0) / recentChanges.length;
    
    // Volume ratio (current vs average)
    const currentVolume = volumes[volumes.length - 1];
    const avgVolume = volumes.slice(-10).reduce((sum, vol) => sum + vol, 0) / 10;
    const volumeRatio = avgVolume > 0 ? currentVolume / avgVolume : 1;
    
    return {
      fastRSI: currentFastRSI,
      momentum,
      priceVelocity,
      volumeRatio
    };
  }
  
  /**
   * FIX: Enhanced calculateAllIndicators with 0DTE optimizations
   * Added momentum oscillators and 5-minute indicators
   */
  static calculateAllIndicators(
    data: MarketData[],
    rsiPeriod: number = 14,
    macdFast: number = 12,
    macdSlow: number = 26,
    macdSignal: number = 9,
    bbPeriod: number = 20,
    bbStdDev: number = 2
  ): TechnicalIndicators | null {
    
    if (data.length < Math.max(rsiPeriod, macdSlow, bbPeriod) + 1) {
      return null;
    }
    
    const rsi = this.calculateRSI(data, rsiPeriod);
    const macd = this.calculateMACD(data, macdFast, macdSlow, macdSignal);
    const bb = this.calculateBollingerBands(data, bbPeriod, bbStdDev);
    
    // FIX: Add momentum oscillators for 0DTE
    const momentum = this.calculateMomentumOscillators(data);
    const fiveMinIndicators = this.calculate5MinIndicators(data);
    
    // Return the most recent values with enhanced indicators
    return {
      rsi: rsi[rsi.length - 1] || 0,
      macd: macd.macd[macd.macd.length - 1] || 0,
      macdSignal: macd.signal[macd.signal.length - 1] || 0,
      macdHistogram: macd.histogram[macd.histogram.length - 1] || 0,
      bbUpper: bb.upper[bb.upper.length - 1] || 0,
      bbMiddle: bb.middle[bb.middle.length - 1] || 0,
      bbLower: bb.lower[bb.lower.length - 1] || 0,
      // FIX: Enhanced indicators for 0DTE
      roc: momentum?.roc || 0,
      stochK: momentum?.stochK || 50,
      stochD: momentum?.stochD || 50,
      fastRSI: fiveMinIndicators?.fastRSI || 50,
      momentum: fiveMinIndicators?.momentum || 0,
      priceVelocity: fiveMinIndicators?.priceVelocity || 0,
      volumeRatio: fiveMinIndicators?.volumeRatio || 1
    };
  }
  
  /**
   * FIX: Enhanced EMA calculation with adaptive smoothing for 0DTE
   */
  private static calculateEMA(data: number[], period: number): number[] {
    if (data.length < period) return [];
    
    const ema: number[] = [];
    const multiplier = 2 / (period + 1);
    
    // First EMA is SMA
    let sum = 0;
    for (let i = 0; i < period; i++) {
      sum += data[i];
    }
    ema.push(sum / period);
    
    // Calculate EMA for remaining periods
    for (let i = period; i < data.length; i++) {
      ema.push((data[i] - ema[ema.length - 1]) * multiplier + ema[ema.length - 1]);
    }
    
    return ema;
  }
  
  private static calculateSMA(data: number[], period: number): number[] {
    if (data.length < period) return [];
    
    const sma: number[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const average = slice.reduce((sum, val) => sum + val, 0) / period;
      sma.push(average);
    }
    
    return sma;
  }
}
