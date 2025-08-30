/**
 * 🎯 Flyagonal Trading Strategy
 * ====================================
 * 
 * Call Broken Wing Butterfly (profits from rising markets + falling volatility) + Put Diagonal Spread (profits from falling markets + rising volatility)
 * 
 * Strategy Details:
 * - Type: volatility_balanced (e.g., MOMENTUM, MEAN_REVERSION, BREAKOUT)
 * - Timeframe: 1hr (e.g., 1Min, 5Min)
 * - Risk Level: low (LOW, MEDIUM, HIGH)
 * - Market Conditions: volatile (e.g., TRENDING, SIDEWAYS)
 * 
 * Key Features:
 * - Real-time signal generation
 * - Adaptive risk management
 * - Multi-timeframe analysis
 * 
 * Risk Management:
 * - Maximum position size: {{MAX_POSITION_SIZE}}%
 * - Stop loss: {{STOP_LOSS}}%
 * - Take profit: {{TAKE_PROFIT}}%
 * 
 * @fileoverview Flyagonal strategy implementation
 * @author Steve Guns
 * @version 1.0.0
 * @created 2025-08-30
 */

import {
  TradingStrategy,
  StrategyConfig,
  RiskMetrics
} from '../registry';
import { MarketData, OptionsChain, TradeSignal } from '../../utils/types';
import { TechnicalAnalysis } from '../../data/technical-indicators';
import { FlyagonalStrategyConfig, FlyagonalStrategyParameters } from './types';
import { FlyagonalRealDataIntegration } from './real-data-integration';
import defaultConfig from './config';

/**
 * Flyagonal Trading Strategy Implementation
 * 
 * This strategy implements {{STRATEGY_DESCRIPTION_DETAILED}}
 * 
 * Algorithm Overview:
 * 1. {{STEP_1}}
 * 2. {{STEP_2}}
 * 3. {{STEP_3}}
 * 4. {{STEP_4}}
 * 
 * Entry Conditions:
 * - {{ENTRY_CONDITION_1}}
 * - {{ENTRY_CONDITION_2}}
 * 
 * Exit Conditions:
 * - {{EXIT_CONDITION_1}}
 * - {{EXIT_CONDITION_2}}
 */
export class FlyagonalStrategy implements TradingStrategy {
  // Strategy Metadata - Required by TradingStrategy interface
  readonly name = 'flyagonal';
  readonly description = 'Call Broken Wing Butterfly (profits from rising markets + falling volatility) + Put Diagonal Spread (profits from falling markets + rising volatility)';
  readonly version = '1.0.0';
  readonly author = 'Steve Guns';

  // Strategy Configuration
  private config: FlyagonalStrategyConfig;
  
  // Daily trade tracking for frequency control
  private dailyTradeCount: Map<string, number> = new Map();

  /**
   * Initialize the strategy with configuration
   * @param config Strategy configuration (optional, uses defaults if not provided)
   */
  constructor(config?: Partial<FlyagonalStrategyConfig>) {
    this.config = { ...defaultConfig, ...config };
    this.validateConfig(this.config);
  }

  /**
   * Generate trading signal based on market conditions
   * 
   * This is the core method that analyzes market data and determines
   * whether to generate a buy/sell signal for 0DTE options.
   * 
   * @param data Historical market data (minimum 20 bars required)
   * @param options Available options chain for current timeframe
   * @returns TradeSignal if conditions are met, null otherwise
   */
  async generateSignal(data: MarketData[], options: OptionsChain[]): Promise<TradeSignal | null> {
    // Validate input data
    if (!this.validateInputData(data, options)) {
      return null;
    }

    // Check daily trade limit (Flyagonal is highly selective - max 1 trade per day)
    const currentBar = data[data.length - 1];
    const today = currentBar.timestamp.toISOString().split('T')[0]; // YYYY-MM-DD format
    
    if (!this.dailyTradeCount) {
      this.dailyTradeCount = new Map<string, number>();
    }
    
    const todayTrades = this.dailyTradeCount.get(today) || 0;
    if (todayTrades >= this.config.riskManagement.maxTradesPerDay) {
      console.log(`🚫 Flyagonal: Daily trade limit reached (${todayTrades}/${this.config.riskManagement.maxTradesPerDay}) for ${today}`);
      return null;
    }

    try {
      // Calculate technical indicators
      const indicators = TechnicalAnalysis.calculateAllIndicators(data);
      if (!indicators) {
        console.warn(`${this.name}: Failed to calculate indicators`);
        return null;
      }

      // Get current market state (currentBar already defined above for daily trade check)
      const currentPrice = currentBar.close;
      const currentTime = currentBar.timestamp;

      // Apply strategy logic (now async for real VIX data)
      const signal = await this.analyzeMarketConditions(
        data,
        indicators,
        options,
        currentPrice,
        currentTime
      );

      // Validate generated signal
      if (signal && this.validateSignal(signal)) {
        // Increment daily trade count (Flyagonal is highly selective)
        const today = currentBar.timestamp.toISOString().split('T')[0];
        const currentCount = this.dailyTradeCount.get(today) || 0;
        this.dailyTradeCount.set(today, currentCount + 1);
        
        console.info(`${this.name}: Generated ${signal.action} signal (${currentCount + 1}/${this.config.riskManagement.maxTradesPerDay} today)`, {
          price: currentPrice,
          confidence: signal.confidence,
          reason: signal.reason
        });
        return signal;
      }

      return null;

    } catch (error) {
      console.error(`${this.name}: Error generating signal:`, error);
      return null;
    }
  }

  /**
   * Core Flyagonal strategy analysis logic
   * 
   * The Flyagonal combines:
   * 1. Call Broken Wing Butterfly (above current price) - profits from rising markets + falling volatility
   * 2. Put Diagonal Spread (below current price) - profits from falling markets + rising volatility
   * 
   * This creates a volatility-balanced strategy that profits in both directions.
   * 
   * @param data Market data array
   * @param indicators Calculated technical indicators (VIX, etc.)
   * @param options Available options chain
   * @param currentPrice Current underlying price
   * @param currentTime Current timestamp
   * @returns TradeSignal or null
   */
  private async analyzeMarketConditions(
    data: MarketData[],
    indicators: any,
    options: OptionsChain[],
    currentPrice: number,
    currentTime: Date
  ): Promise<TradeSignal | null> {
    
    // 1. Check if we have sufficient options chain for complex strategy
    if (!this.hasValidOptionsChain(options, currentPrice)) {
      return null;
    }

    // 2. Analyze market conditions for Flyagonal entry
    const marketAnalysis = this.analyzeMarketForFlyagonal(data, indicators, currentPrice);
    
    // 3. Check timing conditions (8-10 days before expiration optimal)
    const timingValid = this.checkTimingConditions(options, currentTime);
    
    // 4. Assess volatility environment (now async for real VIX data)
    const volatilityAnalysis = await this.analyzeVolatilityEnvironment(indicators, data);
    
    // 5. Generate Flyagonal signal if conditions are met
    if (marketAnalysis.suitable && timingValid && volatilityAnalysis.suitable) {
      // Combine market and volatility confidence for overall signal strength
      const combinedConfidence = (marketAnalysis.confidence + volatilityAnalysis.confidence) / 2;
      
      // Only proceed if combined confidence meets minimum threshold
      if (combinedConfidence >= this.config.parameters.minConfidence) {
        console.log(`✅ Flyagonal Entry Conditions Met:`);
        console.log(`   📊 Market Analysis: ${marketAnalysis.confidence}% confidence`);
        console.log(`   📈 VIX Analysis: ${volatilityAnalysis.confidence}% confidence`);
        console.log(`   🎯 Combined Confidence: ${combinedConfidence.toFixed(1)}%`);
        
        return this.generateFlyagonalSignal(
          currentPrice,
          currentTime,
          options,
          { ...marketAnalysis, confidence: combinedConfidence },
          volatilityAnalysis
        );
      } else {
        console.log(`❌ Flyagonal: Combined confidence ${combinedConfidence.toFixed(1)}% below minimum ${this.config.parameters.minConfidence}%`);
      }
    } else {
      const reasons = [];
      if (!marketAnalysis.suitable) reasons.push('Market conditions unsuitable');
      if (!timingValid) reasons.push('Timing conditions not met');
      if (!volatilityAnalysis.suitable) reasons.push('Volatility environment unsuitable');
      console.log(`❌ Flyagonal: Entry conditions not met - ${reasons.join(', ')}`);
    }
    
    return null;
  }

  /**
   * Validate options chain has sufficient strikes for Flyagonal construction
   * 
   * @param options Available options chain
   * @param currentPrice Current underlying price
   * @returns true if sufficient options available
   */
  private hasValidOptionsChain(options: OptionsChain[], currentPrice: number): boolean {
    // Need multiple strikes above and below current price for butterfly and diagonal
    const callsAbove = options.filter(opt => 
      opt.type === 'CALL' && opt.strike > currentPrice
    ).length;
    
    const putsBelow = options.filter(opt => 
      opt.type === 'PUT' && opt.strike < currentPrice
    ).length;
    
    // Need at least 3 strikes above for broken wing butterfly
    // Need at least 2 strikes below for diagonal spread
    return callsAbove >= 3 && putsBelow >= 2;
  }

  /**
   * Analyze market conditions for Flyagonal suitability
   * 
   * @param data Market data
   * @param indicators Technical indicators
   * @param currentPrice Current price
   * @returns Market analysis result
   */
  private analyzeMarketForFlyagonal(
    data: MarketData[], 
    indicators: any, 
    currentPrice: number
  ): { suitable: boolean; confidence: number; reason: string } {
    
    // Calculate recent volatility and trend
    const recentBars = data.slice(-20);
    const volatility = this.calculateRealizedVolatility(recentBars);
    const trend = this.calculateTrend(recentBars);
    
    // Flyagonal works best in moderate volatility environments
    // Not too low (no movement) or too high (unpredictable)
    const vixLevel = indicators.vix || 20; // Default if VIX not available
    
    let confidence = 50;
    let reason = 'Neutral market conditions';
    
    // Optimal VIX range: 15-30
    if (vixLevel >= 15 && vixLevel <= 30) {
      confidence += 20;
      reason = 'Optimal volatility environment for Flyagonal';
    } else if (vixLevel < 15) {
      confidence -= 10;
      reason = 'Low volatility may limit profit potential';
    } else if (vixLevel > 30) {
      confidence -= 15;
      reason = 'High volatility increases adjustment risk';
    }
    
    // Prefer sideways to mildly trending markets
    const trendStrength = Math.abs(trend);
    if (trendStrength < 0.02) { // Less than 2% trend
      confidence += 15;
      reason += ' + Sideways market ideal for income strategy';
    } else if (trendStrength > 0.05) { // More than 5% trend
      confidence -= 10;
      reason += ' + Strong trend may challenge strategy';
    }
    
    return {
      suitable: confidence >= 60,
      confidence,
      reason
    };
  }

  /**
   * Check timing conditions for optimal Flyagonal entry
   * 
   * @param options Available options
   * @param currentTime Current timestamp
   * @returns true if timing is optimal
   */
  private checkTimingConditions(options: OptionsChain[], currentTime: Date): boolean {
    if (options.length === 0) return false;
    
    // Find nearest expiration
    const nearestExpiration = options.reduce((nearest, option) => {
      const optionExp = new Date(option.expiration);
      const nearestExp = new Date(nearest.expiration);
      return optionExp < nearestExp ? option : nearest;
    });
    
    const daysToExpiration = this.calculateDaysToExpiration(
      currentTime, 
      new Date(nearestExpiration.expiration)
    );
    
    // Optimal entry: 8-10 days before expiration
    return daysToExpiration >= 8 && daysToExpiration <= 10;
  }

  /**
   * Enhanced volatility environment analysis with REAL VIX integration
   * 
   * ENHANCED: Now prioritizes real VIX data over estimation
   * - Attempts to fetch real VIX data first
   * - Falls back to improved estimation if real data unavailable
   * - Complies with .cursorrules preference for real data
   * 
   * Based on Steve Guns' methodology:
   * - Optimal VIX range: 15-30
   * - Avoid extreme volatility environments
   * - Consider volatility term structure
   * 
   * @param indicators Technical indicators
   * @param data Market data
   * @returns Enhanced volatility analysis result
   */
  private async analyzeVolatilityEnvironment(
    indicators: any, 
    data: MarketData[]
  ): Promise<{ suitable: boolean; vixLevel: number; trend: string; volatilityRegime: string; confidence: number; dataSource: 'REAL' | 'ESTIMATED' }> {
    
    // Calculate realized volatility
    const recentVolatility = this.calculateRealizedVolatility(data.slice(-10));
    
    // ENHANCED: Prioritize real VIX data over estimation
    let vixLevel: number;
    let dataSource: 'REAL' | 'ESTIMATED' = 'ESTIMATED';
    
    // 1. Try to get real VIX from technical indicators first
    if (indicators.vix && indicators.vix > 0) {
      vixLevel = indicators.vix;
      dataSource = 'REAL';
      console.log(`📊 Using real VIX from indicators: ${vixLevel.toFixed(1)}`);
    } else {
      // 2. Try to fetch real VIX data directly
      try {
        const currentTime = data[data.length - 1].timestamp;
        const realVix = await FlyagonalRealDataIntegration.fetchRealVIX(currentTime);
        
        if (realVix && realVix > 0) {
          vixLevel = realVix;
          dataSource = 'REAL';
          console.log(`📊 Using real VIX from data provider: ${vixLevel.toFixed(1)}`);
        } else {
          throw new Error('Real VIX data not available');
        }
      } catch (error) {
        // 3. Fall back to improved estimation
        console.warn(`⚠️ Real VIX data unavailable, using estimation: ${error}`);
        dataSource = 'ESTIMATED';
        
        // IMPROVED ESTIMATION: More conservative and realistic
        // Realized volatility is annualized decimal (0.20 = 20%)
        const baseVolatility = recentVolatility * 100; // Convert to percentage
        
        // VIX typically trades at a premium to realized volatility due to fear premium
        // Use more conservative scaling based on market research:
        // - Normal markets: VIX ≈ 1.1-1.3x realized vol
        // - Stressed markets: VIX ≈ 1.5-2.0x realized vol
        
        let vixMultiplier: number;
        if (baseVolatility < 12) {
          vixMultiplier = 1.4; // Low vol environments often have higher VIX premium
        } else if (baseVolatility < 20) {
          vixMultiplier = 1.2; // Normal vol environments
        } else if (baseVolatility < 30) {
          vixMultiplier = 1.1; // High vol environments, VIX premium compresses
        } else {
          vixMultiplier = 1.0; // Very high vol, VIX may trade at or below realized
        }
        
        // Calculate estimated VIX with floor and ceiling
        const estimatedVix = baseVolatility * vixMultiplier;
        
        // Apply realistic bounds: VIX rarely goes below 9 or above 80 in normal markets
        vixLevel = Math.max(9, Math.min(80, estimatedVix));
        
        console.log(`📊 Estimated VIX: ${vixLevel.toFixed(1)} (from ${baseVolatility.toFixed(1)}% realized vol, ${vixMultiplier}x multiplier)`);
        console.warn(`⚠️ Using estimated VIX - consider integrating real VIX data for better accuracy`);
      }
    }
    
    // Enhanced VIX-based volatility regime classification
    let volatilityRegime: string;
    let vixConfidence = 50;
    
    if (vixLevel < 12) {
      volatilityRegime = 'EXTREMELY_LOW';
      vixConfidence = 5; // Extremely low confidence - avoid trading in complacent markets
    } else if (vixLevel >= 12 && vixLevel < 15) {
      volatilityRegime = 'LOW';
      vixConfidence = 25; // Low confidence - limited profit potential
    } else if (vixLevel >= 15 && vixLevel <= 20) {
      volatilityRegime = 'OPTIMAL_LOW';
      vixConfidence = 85; // High confidence - ideal for Flyagonal
    } else if (vixLevel > 20 && vixLevel <= 25) {
      volatilityRegime = 'OPTIMAL_MEDIUM';
      vixConfidence = 90; // Very high confidence - sweet spot
    } else if (vixLevel > 25 && vixLevel <= 30) {
      volatilityRegime = 'OPTIMAL_HIGH';
      vixConfidence = 80; // Good confidence - still workable
    } else if (vixLevel > 30 && vixLevel <= 40) {
      volatilityRegime = 'HIGH';
      vixConfidence = 30; // Low confidence - increased adjustment risk
    } else {
      volatilityRegime = 'EXTREMELY_HIGH';
      vixConfidence = 10; // Very low confidence - avoid trading
    }
    
    // Determine volatility trend with enhanced logic
    let trend = 'stable';
    const vixToRealizedRatio = vixLevel / (recentVolatility * 100);
    
    if (vixToRealizedRatio > 1.3) {
      trend = 'fear_premium'; // VIX elevated relative to realized - good for diagonal
    } else if (vixToRealizedRatio < 0.7) {
      trend = 'complacency'; // VIX low relative to realized - good for butterfly
    } else if (recentVolatility > vixLevel / 100 * 1.2) {
      trend = 'rising';
    } else if (recentVolatility < vixLevel / 100 * 0.8) {
      trend = 'falling';
    }
    
    // Steve Guns' optimal VIX range: 15-30, but be more flexible for multi-day strategy
    const inOptimalRange = vixLevel >= this.config.parameters.optimalVixRange.min && 
                          vixLevel <= this.config.parameters.optimalVixRange.max;
    
    // More flexible range for multi-day Flyagonal - can work in broader VIX range
    const inWorkableRange = vixLevel >= 10 && vixLevel <= 35;
    
    // HARD STOP: Only avoid trading in extreme market conditions
    if (vixLevel < 8 || vixLevel > 50) {
      console.log(`🚫 Flyagonal: VIX ${vixLevel < 8 ? 'too low' : 'too high'} (${vixLevel.toFixed(1)}) - Extreme market conditions, avoiding trades`);
      return {
        suitable: false,
        vixLevel,
        trend,
        volatilityRegime,
        confidence: 0
      };
    }
    
    // Calculate overall volatility confidence
    let volatilityConfidence = vixConfidence;
    
    // Boost confidence for optimal conditions
    if (inOptimalRange) {
      volatilityConfidence = Math.min(95, volatilityConfidence + 15);
    } else if (inWorkableRange) {
      volatilityConfidence = Math.min(80, volatilityConfidence + 5);
    }
    
    // Less harsh penalties for moderate volatility
    if (vixLevel < 10 || vixLevel > 35) {
      volatilityConfidence = Math.max(20, volatilityConfidence - 15);
    }
    
    // Multi-day strategy can be more flexible - lower threshold
    const suitable = inWorkableRange && volatilityConfidence >= 40;
    
    console.log(`📊 VIX Analysis: ${vixLevel.toFixed(1)} (${volatilityRegime}) | Trend: ${trend} | Confidence: ${volatilityConfidence}% | Source: ${dataSource}`);
    
    return { 
      suitable, 
      vixLevel, 
      trend, 
      volatilityRegime,
      confidence: volatilityConfidence,
      dataSource
    };
  }

  /**
   * Generate Flyagonal signal - combines broken wing butterfly and diagonal spread
   * 
   * @param currentPrice Current underlying price
   * @param currentTime Current timestamp
   * @param options Available options chain
   * @param marketAnalysis Market condition analysis
   * @param volatilityAnalysis Volatility environment analysis
   * @returns TradeSignal for Flyagonal strategy
   */
  private generateFlyagonalSignal(
    currentPrice: number,
    currentTime: Date,
    options: OptionsChain[],
    marketAnalysis: any,
    volatilityAnalysis: any
  ): TradeSignal {
    
    try {
      // Calculate optimal strikes for both components using SPX methodology
      const butterflyStrikes = this.calculateButterflyStrikes(currentPrice, options);
      const diagonalStrikes = this.calculateDiagonalStrikes(currentPrice, options);
      
      // Validate profit zone meets 200+ point requirement
      const profitZone = this.calculateProfitZone(butterflyStrikes, diagonalStrikes, currentPrice);
      if (!profitZone || !profitZone.isValid) {
        console.warn('❌ Flyagonal: Insufficient profit zone, skipping signal');
        throw new Error('Insufficient profit zone for Flyagonal strategy');
      }
      
      // CORRECTED: Realistic risk management with achievable targets
      // Max $500 loss per trade with 1.5:1 risk/reward ratio ($750 profit target)
      const maxLossPerTrade = 500; // Defined max loss per trade
      const targetProfitPerTrade = 750; // CORRECTED: 1.5:1 risk/reward ratio (realistic)
      
      const totalMaxLoss = butterflyStrikes.maxLoss;
      let basePositionSize = Math.min(
        this.config.parameters.positionSize,
        (maxLossPerTrade / totalMaxLoss) // Position size to limit loss to $500
      );
      
      // VIX-based position sizing adjustment
      let vixAdjustment = 1.0;
      if (volatilityAnalysis.volatilityRegime === 'OPTIMAL_MEDIUM') {
        vixAdjustment = 1.1; // Slightly increase position in sweet spot
      } else if (volatilityAnalysis.volatilityRegime === 'OPTIMAL_LOW') {
        vixAdjustment = 1.05; // Small increase in low volatility
      } else if (volatilityAnalysis.volatilityRegime === 'HIGH') {
        vixAdjustment = 0.8; // Reduce position in high volatility
      } else if (volatilityAnalysis.volatilityRegime === 'EXTREMELY_HIGH') {
        vixAdjustment = 0.5; // Significantly reduce in extreme volatility
      }
      
      // Apply VIX adjustment but ensure we don't exceed maxPositionSize
      const adjustedPositionSize = basePositionSize * vixAdjustment;
      const positionSize = Math.min(adjustedPositionSize, this.config.riskManagement.maxPositionSize);
      
      // CORRECTED: Realistic 1.5:1 risk/reward ratio
      const profitTarget = targetProfitPerTrade;
      const profitTargetPercent = (profitTarget / maxLossPerTrade) * 100; // Should be 150%
      
      console.log(`🎯 Flyagonal Signal Generated:`);
      console.log(`   💰 Max Loss: $${maxLossPerTrade}, Profit Target: $${profitTarget} (1.5:1 Risk/Reward)`);
      console.log(`   📏 Profit Zone: ${profitZone.width}pts, Market Position: ${profitZone.marketPosition.toFixed(1)}%`);
      console.log(`   📊 Position Size: ${(positionSize * 100).toFixed(2)}% of account (VIX adj: ${(vixAdjustment * 100).toFixed(0)}%)`);
      console.log(`   🌪️ VIX Regime: ${volatilityAnalysis.volatilityRegime} (${volatilityAnalysis.vixLevel.toFixed(1)})`);
      
      // Create complex signal with both components
      return {
        action: 'FLYAGONAL_COMBO', // Custom action for complex strategy
        confidence: marketAnalysis.confidence,
        reason: `Flyagonal SPX: ${marketAnalysis.reason} | VIX: ${volatilityAnalysis.vixLevel.toFixed(1)} (${volatilityAnalysis.volatilityRegime}) | Zone: ${profitZone.width}pts`,
        indicators: { 
          vix: volatilityAnalysis.vixLevel, 
          vixRegime: volatilityAnalysis.volatilityRegime,
          vixConfidence: volatilityAnalysis.confidence,
          trend: volatilityAnalysis.trend,
          profitZoneWidth: profitZone.width,
          maxLoss: totalMaxLoss,
          profitTarget: profitTarget,
          positionAdjustment: vixAdjustment
        },
        timestamp: currentTime,
        
        // For compatibility, use butterfly short strike as primary
        targetStrike: butterflyStrikes.short,
        expiration: new Date(currentTime.getTime() + 4.5 * 24 * 60 * 60 * 1000), // 4.5 day target hold
        
        positionSize: positionSize,
        stopLoss: 100, // 100% of max loss ($500 defined risk)
        takeProfit: 150, // CORRECTED: 150% profit target (1.5:1 risk/reward = $750)
        
        // Metadata for logging and analysis
        metadata: {
          vixLevel: volatilityAnalysis.vixLevel,
          vixRegime: volatilityAnalysis.volatilityRegime,
          marketAnalysisConfidence: marketAnalysis.confidence,
          volatilityConfidence: volatilityAnalysis.confidence
        },
        
        // Flyagonal-specific data with proper SPX timing
        flyagonalComponents: {
          butterfly: {
            type: 'CALL_BROKEN_WING',
            longLower: butterflyStrikes.longLower,
            short: butterflyStrikes.short,
            longUpper: butterflyStrikes.longUpper,
            expiration: new Date(currentTime.getTime() + 8 * 24 * 60 * 60 * 1000), // 8 days (Steve Guns' timing)
          },
          diagonal: {
            type: 'PUT_DIAGONAL',
            longStrike: diagonalStrikes.long,
            shortStrike: diagonalStrikes.short,
            shortExpiration: new Date(currentTime.getTime() + 8 * 24 * 60 * 60 * 1000), // 8 days
            longExpiration: new Date(currentTime.getTime() + 16 * 24 * 60 * 60 * 1000), // 16 days (double)
          }
        }
      };
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`❌ Flyagonal signal generation failed: ${errorMessage}`);
      throw error; // Re-throw to be handled by calling method
    }
  }

  /**
   * Calculate optimal strikes for broken wing butterfly component (SPX-specific)
   * 
   * Based on Steve Guns' methodology:
   * - Place butterfly ABOVE current market price
   * - Unequal wing spacing: 50pts lower wing, 60pts upper wing
   * - Example: Market 6360 → Strikes: 6370, 6420, 6480
   * 
   * @param currentPrice Current SPX price
   * @param options Available options (for validation)
   * @returns Butterfly strike configuration with profit metrics
   */
  private calculateButterflyStrikes(currentPrice: number, options: OptionsChain[]) {
    // SPX-specific broken wing butterfly calculation
    // Place strikes above current market to benefit from upward movement + volatility drop
    
    // Round current price to nearest 10 for clean strike selection
    const basePrice = Math.ceil(currentPrice / 10) * 10;
    
    // Steve Guns' methodology: Place butterfly above market
    const longLower = basePrice + 10;      // e.g., 6370 when market at 6360
    const short = longLower + 50;          // e.g., 6420 (50pt lower wing)
    const longUpper = short + 60;          // e.g., 6480 (60pt upper wing - asymmetric)
    
    // Validate strikes exist in options chain
    const requiredStrikes = [longLower, short, longUpper];
    const availableCallStrikes = options
      .filter(opt => opt.type === 'CALL')
      .map(opt => opt.strike);
    
    const missingStrikes = requiredStrikes.filter(strike => 
      !availableCallStrikes.includes(strike)
    );
    
    if (missingStrikes.length > 0) {
      throw new Error(`Missing call strikes for butterfly: ${missingStrikes.join(', ')}`);
    }
    
    // Calculate max loss and profit target (10% of max loss)
    const maxLoss = this.calculateButterflyMaxLoss(longLower, short, longUpper);
    const profitTarget = maxLoss * 0.10; // Steve Guns' 10% profit target
    
    console.log(`🦋 Butterfly: ${longLower}/${short}/${longUpper}, Max Loss: $${maxLoss}, Target: $${profitTarget}`);
    
    return { 
      longLower, 
      short, 
      longUpper, 
      maxLoss, 
      profitTarget,
      wingSpacing: { lower: 50, upper: 60 } // Document the asymmetry
    };
  }

  /**
   * Calculate optimal strikes for diagonal spread component (SPX-specific)
   * 
   * Based on Steve Guns' methodology:
   * - Short put 3% below current market price
   * - Long put further below for additional protection
   * - Example: Market 6360 → Short put 6250 (3% below), Long put 6200
   * 
   * @param currentPrice Current SPX price
   * @param options Available options (for validation)
   * @returns Diagonal strike configuration with profit metrics
   */
  private calculateDiagonalStrikes(currentPrice: number, options: OptionsChain[]) {
    // SPX-specific put diagonal calculation
    // Place below current market to benefit from downward movement + volatility spike
    
    // Get all available put strikes, sorted descending
    const availablePutStrikes = options
      .filter(opt => opt.type === 'PUT')
      .map(opt => opt.strike)
      .sort((a, b) => b - a); // Sort descending
    
    if (availablePutStrikes.length < 2) {
      throw new Error(`Insufficient put options available: ${availablePutStrikes.length} (need at least 2)`);
    }
    
    // Target: Short put 3% below market (Steve Guns' methodology)
    const targetShortStrike = Math.floor((currentPrice * 0.97) / 5) * 5; // 3% below, rounded to $5
    
    // Find closest available strike to our target short strike
    const shortStrike = this.findClosestStrike(targetShortStrike, availablePutStrikes);
    
    // Target: Long put 50pts below short strike for protection
    const targetLongStrike = shortStrike - 50;
    
    // Find closest available strike to our target long strike (must be below short strike)
    const availableLongStrikes = availablePutStrikes.filter(strike => strike < shortStrike);
    
    if (availableLongStrikes.length === 0) {
      // Fallback: use the lowest available put strike
      const longStrike = Math.min(...availablePutStrikes.filter(strike => strike !== shortStrike));
      console.warn(`⚠️ Using fallback long strike: ${longStrike} (no strikes below ${shortStrike})`);
      
      return this.buildDiagonalResult(currentPrice, shortStrike, longStrike);
    }
    
    const longStrike = this.findClosestStrike(targetLongStrike, availableLongStrikes);
    
    return this.buildDiagonalResult(currentPrice, shortStrike, longStrike);
  }
  
  /**
   * Find the closest available strike to a target strike
   */
  private findClosestStrike(target: number, availableStrikes: number[]): number {
    return availableStrikes.reduce((closest, current) => {
      return Math.abs(current - target) < Math.abs(closest - target) ? current : closest;
    });
  }
  
  /**
   * Build diagonal result object with validation
   */
  private buildDiagonalResult(currentPrice: number, shortStrike: number, longStrike: number) {
    // Calculate distance from market for validation
    const shortDistance = currentPrice - shortStrike;
    const shortPercentBelow = (shortDistance / currentPrice) * 100;
    const protection = shortStrike - longStrike;
    
    console.log(`📐 Diagonal: Short ${shortStrike} (${shortPercentBelow.toFixed(1)}% below), Long ${longStrike}`);
    console.log(`   Protection width: ${protection}pts`);
    
    // Validate reasonable parameters
    if (shortPercentBelow < 1 || shortPercentBelow > 10) {
      console.warn(`⚠️ Short strike ${shortPercentBelow.toFixed(1)}% below market (target: 3%)`);
    }
    
    if (protection < 10) {
      console.warn(`⚠️ Protection width only ${protection}pts (target: 50pts)`);
    }
    
    return { 
      short: shortStrike, 
      long: longStrike,
      percentBelow: shortPercentBelow,
      protection: protection
    };
  }

  /**
   * Calculate maximum loss for broken wing butterfly
   * 
   * For a broken wing butterfly (Long-Short-Short-Long):
   * Max loss occurs at the short strike
   * 
   * @param longLower Lower long strike
   * @param short Short strike (2 contracts)
   * @param longUpper Upper long strike
   * @returns Maximum loss amount
   */
  private calculateButterflyMaxLoss(longLower: number, short: number, longUpper: number): number {
    // Broken wing butterfly max loss calculation
    // Max loss = (Short strike - Long lower strike) - Net credit received
    // For simplicity, assume net debit of lower wing width
    const lowerWingWidth = short - longLower; // e.g., 6420 - 6370 = 50
    const upperWingWidth = longUpper - short; // e.g., 6480 - 6420 = 60
    
    // Max loss typically occurs at short strike
    // Simplified calculation: use the smaller wing width as max loss
    const maxLoss = Math.min(lowerWingWidth, upperWingWidth) * 100; // Convert to dollars (SPX multiplier)
    
    return maxLoss;
  }

  /**
   * Calculate and validate the wide profit zone (CORRECTED LOGIC)
   * 
   * MATHEMATICAL CORRECTION:
   * The original logic incorrectly added butterfly and diagonal ranges.
   * These are SEPARATE profit zones that don't combine arithmetically.
   * 
   * CORRECT APPROACH:
   * - Butterfly profits in a range ABOVE current market
   * - Diagonal profits in a range BELOW current market  
   * - Total "profit zone" is the span from lowest profitable point to highest
   * 
   * @param butterflyStrikes Butterfly strike configuration
   * @param diagonalStrikes Diagonal strike configuration  
   * @param currentPrice Current market price
   * @returns Profit zone metrics or null if insufficient
   */
  private calculateProfitZone(butterflyStrikes: any, diagonalStrikes: any, currentPrice: number) {
    // CORRECTED LOGIC: Calculate actual profit boundaries
    
    // Butterfly profit zone (above market): profits between long strikes
    const butterflyLowerBound = butterflyStrikes.longLower;  // e.g., 6370
    const butterflyUpperBound = butterflyStrikes.longUpper;  // e.g., 6480
    const butterflyProfitRange = butterflyUpperBound - butterflyLowerBound; // 110pts
    
    // Diagonal profit zone (below market): profits from short put down to breakeven
    const diagonalUpperBound = diagonalStrikes.short;  // e.g., 6250 (short put)
    const diagonalLowerBound = diagonalStrikes.long;   // e.g., 6200 (long put protection)
    const diagonalProfitRange = diagonalUpperBound - diagonalLowerBound; // 50pts
    
    // TOTAL PROFIT ZONE: From lowest profitable point to highest profitable point
    const totalLowerBound = Math.min(diagonalLowerBound, butterflyLowerBound);
    const totalUpperBound = Math.max(diagonalUpperBound, butterflyUpperBound);
    const totalProfitZoneWidth = totalUpperBound - totalLowerBound;
    
    // Calculate market position within total zone
    const marketPosition = ((currentPrice - totalLowerBound) / totalProfitZoneWidth) * 100;
    
    // REALISTIC MINIMUM: Based on SPX typical strike spacing and volatility
    // 150 points is more realistic than 200 for this strategy structure
    const minProfitZone = 150;
    
    // Validate profit zone width
    if (totalProfitZoneWidth < minProfitZone) {
      console.warn(`❌ Flyagonal: Total profit zone too narrow (${totalProfitZoneWidth}pts), minimum ${minProfitZone}pts required`);
      console.warn(`   Butterfly range: ${butterflyLowerBound}-${butterflyUpperBound} (${butterflyProfitRange}pts)`);
      console.warn(`   Diagonal range: ${diagonalLowerBound}-${diagonalUpperBound} (${diagonalProfitRange}pts)`);
      return null;
    }
    
    // Additional validation: Ensure zones don't overlap inappropriately
    if (butterflyLowerBound <= diagonalUpperBound) {
      console.warn(`⚠️ Flyagonal: Butterfly and diagonal zones overlap - this may reduce effectiveness`);
      console.warn(`   Butterfly starts at ${butterflyLowerBound}, diagonal ends at ${diagonalUpperBound}`);
    }
    
    console.log(`🎯 CORRECTED Profit Zone Analysis:`);
    console.log(`   Butterfly Zone: ${butterflyLowerBound}-${butterflyUpperBound} (${butterflyProfitRange}pts)`);
    console.log(`   Diagonal Zone: ${diagonalLowerBound}-${diagonalUpperBound} (${diagonalProfitRange}pts)`);
    console.log(`   Total Zone: ${totalLowerBound}-${totalUpperBound} (${totalProfitZoneWidth}pts)`);
    console.log(`   Market Position: ${currentPrice} (${marketPosition.toFixed(1)}% through zone)`);
    
    return { 
      upperBoundary: totalUpperBound, 
      lowerBoundary: totalLowerBound, 
      width: totalProfitZoneWidth,
      marketPosition: marketPosition,
      isValid: totalProfitZoneWidth >= minProfitZone,
      // Additional metrics for analysis
      butterflyRange: butterflyProfitRange,
      diagonalRange: diagonalProfitRange,
      zonesOverlap: butterflyLowerBound <= diagonalUpperBound
    };
  }

  /**
   * Calculate realized volatility from price data
   * 
   * @param data Market data array
   * @returns Annualized volatility
   */
  private calculateRealizedVolatility(data: MarketData[]): number {
    if (data.length < 2) return 0;
    
    // Calculate daily returns
    const returns = [];
    for (let i = 1; i < data.length; i++) {
      const dailyReturn = Math.log(data[i].close / data[i - 1].close);
      returns.push(dailyReturn);
    }
    
    // Calculate standard deviation
    const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / returns.length;
    const stdDev = Math.sqrt(variance);
    
    // Annualize (assuming 252 trading days)
    return stdDev * Math.sqrt(252) * 100;
  }

  /**
   * Calculate price trend over recent period
   * 
   * @param data Market data array
   * @returns Trend percentage (positive = uptrend, negative = downtrend)
   */
  private calculateTrend(data: MarketData[]): number {
    if (data.length < 2) return 0;
    
    const firstPrice = data[0].close;
    const lastPrice = data[data.length - 1].close;
    
    return (lastPrice - firstPrice) / firstPrice;
  }

  /**
   * Calculate days to expiration
   * 
   * @param currentTime Current timestamp
   * @param expiration Expiration date
   * @returns Days to expiration
   */
  private calculateDaysToExpiration(currentTime: Date, expiration: Date): number {
    const timeDiff = expiration.getTime() - currentTime.getTime();
    return Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
  }

  /**
   * Validate input data quality and completeness
   * 
   * @param data Market data array
   * @param options Options chain
   * @returns true if data is valid for analysis
   */
  private validateInputData(data: MarketData[], options: OptionsChain[]): boolean {
    // Check minimum data requirements
    if (data.length < 20) {
      console.warn(`${this.name}: Insufficient data points (${data.length} < 20)`);
      return false;
    }

    // Check for data gaps or invalid values
    const currentBar = data[data.length - 1];
    if (!currentBar || currentBar.close <= 0) {
      console.warn(`${this.name}: Invalid current bar data`);
      return false;
    }

    // Check options availability
    if (!options || options.length === 0) {
      console.warn(`${this.name}: No options available`);
      return false;
    }

    return true;
  }

  /**
   * Validate generated signal before execution
   * 
   * @param signal Generated trade signal
   * @returns true if signal is valid and safe to execute
   */
  validateSignal(signal: TradeSignal): boolean {
    try {
      // Basic signal validation
      if (!signal || !signal.action || !signal.timestamp) {
        return false;
      }

      // Confidence threshold check
      if (signal.confidence < this.config.parameters.minConfidence) {
        console.warn(`${this.name}: Signal confidence too low (${signal.confidence} < ${this.config.parameters.minConfidence})`);
        return false;
      }

      // Position size validation
      if (signal.positionSize <= 0 || signal.positionSize > this.config.riskManagement.maxPositionSize) {
        console.warn(`${this.name}: Invalid position size: ${signal.positionSize}`);
        return false;
      }

      // Time validation (ensure not too close to expiration)
      if (signal.expiration) {
        const timeToExpiration = signal.expiration.getTime() - signal.timestamp.getTime();
        const minTimeToExpiration = 30 * 60 * 1000; // 30 minutes
        if (timeToExpiration < minTimeToExpiration) {
          console.warn(`${this.name}: Signal too close to expiration`);
          return false;
        }
      }

      return true;

    } catch (error) {
      console.error(`${this.name}: Error validating signal:`, error);
      return false;
    }
  }

  /**
   * Calculate risk metrics for a given signal
   * 
   * @param signal Trade signal to analyze
   * @returns Risk assessment metrics
   */
  calculateRisk(signal: TradeSignal): RiskMetrics {
    try {
      // Calculate basic risk metrics
      const maxLoss = signal.positionSize * (signal.stopLoss || 0.5); // Default 50% max loss
      const maxProfit = signal.positionSize * (signal.takeProfit || 1.0); // Default 100% max profit
      const riskRewardRatio = maxProfit / maxLoss;

      // CORRECTED: Realistic probability of profit estimation
      // Based on actual options income strategy research:
      // - High-confidence signals (85%+): 65-75% probability of profit
      // - Medium-confidence signals (70-85%): 55-65% probability of profit
      // - Lower-confidence signals (<70%): 45-55% probability of profit
      
      let probabilityOfProfit: number;
      if (signal.confidence >= 85) {
        probabilityOfProfit = 0.65 + (signal.confidence - 85) / 100 * 0.10; // 65-75%
      } else if (signal.confidence >= 70) {
        probabilityOfProfit = 0.55 + (signal.confidence - 70) / 15 * 0.10; // 55-65%
      } else {
        probabilityOfProfit = 0.45 + (signal.confidence - 50) / 20 * 0.10; // 45-55%
      }
      
      // Cap at realistic maximum (no strategy has >80% long-term win rate)
      probabilityOfProfit = Math.min(0.75, Math.max(0.45, probabilityOfProfit));

      // Assess time decay risk (higher for shorter time to expiration)
      let timeDecayRisk: 'LOW' | 'MEDIUM' | 'HIGH' = 'MEDIUM';
      if (signal.expiration) {
        const timeToExpiration = signal.expiration.getTime() - signal.timestamp.getTime();
        const hoursToExpiration = timeToExpiration / (1000 * 60 * 60);
        
        if (hoursToExpiration < 2) timeDecayRisk = 'HIGH';
        else if (hoursToExpiration < 4) timeDecayRisk = 'MEDIUM';
        else timeDecayRisk = 'LOW';
      }

      // Assess volatility risk based on recent price action
      let volatilityRisk: 'LOW' | 'MEDIUM' | 'HIGH' = 'MEDIUM'; // Default to medium
      
      return {
        probabilityOfProfit,
        maxLoss,
        maxProfit,
        riskRewardRatio,
        timeDecayRisk,
        volatilityRisk
      };

    } catch (error) {
      console.error(`${this.name}: Error calculating risk:`, error);
      
      // Return conservative risk metrics on error
      return {
        probabilityOfProfit: 0.3,
        maxLoss: signal.positionSize,
        maxProfit: signal.positionSize * 0.5,
        riskRewardRatio: 0.5,
        timeDecayRisk: 'HIGH',
        volatilityRisk: 'HIGH'
      };
    }
  }

  /**
   * Get default configuration for this strategy
   * 
   * @returns Default strategy configuration
   */
  getDefaultConfig(): FlyagonalStrategyConfig {
    return { ...defaultConfig };
  }

  /**
   * Validate strategy configuration
   * 
   * @param config Configuration to validate
   * @returns true if configuration is valid
   */
  validateConfig(config: StrategyConfig): boolean {
    try {
      const typedConfig = config as FlyagonalStrategyConfig;
      
      // Validate required parameters exist
      if (!typedConfig.parameters) {
        console.error(`${this.name}: Missing parameters in config`);
        return false;
      }

      // Validate parameter ranges
      const params = typedConfig.parameters;
      
      // TODO: Add specific parameter validations
      // Example:
      // if (params.rsiPeriod < 5 || params.rsiPeriod > 50) {
      //   console.error(`${this.name}: Invalid RSI period: ${params.rsiPeriod}`);
      //   return false;
      // }

      // Validate risk management settings
      if (!typedConfig.riskManagement) {
        console.error(`${this.name}: Missing risk management config`);
        return false;
      }

      const risk = typedConfig.riskManagement;
      if (risk.maxPositionSize <= 0 || risk.maxPositionSize > 1) {
        console.error(`${this.name}: Invalid max position size: ${risk.maxPositionSize}`);
        return false;
      }

      return true;

    } catch (error) {
      console.error(`${this.name}: Error validating config:`, error);
      return false;
    }
  }

  /**
   * Get list of required technical indicators
   * 
   * @returns Array of indicator names required by this strategy
   */
  getRequiredIndicators(): string[] {
    return [
      'VIX',           // Volatility Index for market fear assessment
      'REALIZED_VOL',  // Realized volatility calculation
      'TREND',         // Price trend analysis
      'VOLUME'         // Volume for liquidity assessment
    ];
  }

  /**
   * Get supported timeframes for this strategy
   * 
   * @returns Array of supported timeframe strings
   */
  getTimeframes(): string[] {
    return [
      '1Hour',   // Primary timeframe for analysis
      '4Hour',   // Secondary timeframe for trend confirmation
      '1Day'     // Daily timeframe for volatility assessment
    ];
  }

  /**
   * Get risk level classification for this strategy
   * 
   * @returns Risk level classification
   */
  getRiskLevel(): 'LOW' | 'MEDIUM' | 'HIGH' {
    return 'MEDIUM'; // CORRECTED: Complex multi-leg strategy with moderate risk
    // Note: While risk is defined ($500 max loss), the complexity and multiple legs
    // make this a MEDIUM risk strategy, not LOW risk as originally claimed
  }

  /**
   * Get strategy performance statistics (optional method)
   * 
   * @returns Performance metrics if available
   */
  getPerformanceStats(): any {
    // TODO: Implement performance tracking if desired
    return {
      totalSignals: 0,
      successfulSignals: 0,
      averageReturn: 0,
      maxDrawdown: 0,
      sharpeRatio: 0
    };
  }
}
