/**
 * 🎯 Flyagonal Strategy - Real Data Integration
 * =============================================
 * 
 * Integration layer for real Alpaca historical data and VIX data.
 * Enforces .cursorrules requirement for real data only.
 * 
 * Key Features:
 * - Real Alpaca options chain filtering for Flyagonal requirements
 * - Real VIX data integration
 * - Greeks calculations with real market data
 * - Compliance with .cursorrules data requirements
 * 
 * @fileoverview Real data integration for Flyagonal strategy
 * @author Trading System Architecture
 * @version 1.0.0
 * @created 2025-08-30
 */

import { MarketData, OptionsChain } from '../../utils/types';
import { AlpacaHistoricalDataFetcher } from '../../data/alpaca-historical-data';
import { GreeksSimulator } from '../../data/greeks-simulator';

/**
 * Real data requirements for Flyagonal strategy
 */
export interface FlyagonalDataRequirements {
  /** Current underlying price for strike calculations */
  underlyingPrice: number;
  
  /** Required call strikes for broken wing butterfly (SPY adapted) */
  butterflyStrikes: {
    longLower: number;  // Market + 1pt (SPY equivalent of SPX +10pts)
    short: number;      // Market + 6pts (SPY equivalent of SPX +60pts)
    longUpper: number;  // Market + 12pts (SPY equivalent of SPX +120pts)
  };
  
  /** Required put strikes for diagonal spread (SPY adapted) */
  diagonalStrikes: {
    shortStrike: number; // 3% below market
    longStrike: number;  // Short - 5pts (SPY equivalent of SPX -50pts)
  };
  
  /** Required expirations */
  expirations: {
    shortExpiration: Date;  // 8 days out
    longExpiration: Date;   // 16 days out
  };
}

/**
 * Enhanced options chain with Greeks and real market data
 */
export interface EnhancedOptionsChain extends OptionsChain {
  /** Real Greeks calculated from market data */
  greeks?: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  };
  
  /** Real market metrics */
  realMetrics?: {
    bidAskSpread: number;
    midPrice: number;
    volumeWeightedPrice: number;
    liquidityScore: number; // 0-100 based on volume and OI
  };
}

/**
 * Real Data Integration for Flyagonal Strategy
 * 
 * Handles all real data fetching and processing for the Flyagonal strategy
 * in compliance with .cursorrules requirements.
 */
export class FlyagonalRealDataIntegration {
  
  /**
   * Calculate required strikes and expirations for Flyagonal strategy
   * Based on Steve Guns' methodology with real market data
   */
  static calculateDataRequirements(
    underlyingPrice: number, 
    currentTime: Date
  ): FlyagonalDataRequirements {
    
    // Round to nearest 1 for clean SPY strikes (adapted from SPX)
    const basePrice = Math.ceil(underlyingPrice);
    
    // Call Broken Wing Butterfly (above market) - SPY adapted from SPX
    const butterflyStrikes = {
      longLower: basePrice + 1,    // e.g., 461 when market at 460 (SPY equivalent of SPX +10)
      short: basePrice + 6,        // e.g., 466 (5pt wing + 1pt offset, SPY equivalent of SPX +60)
      longUpper: basePrice + 12    // e.g., 472 (6pt upper wing, SPY equivalent of SPX +120)
    };
    
    // Put Diagonal Spread (below market) - SPY adapted from SPX
    const shortStrike = Math.floor((underlyingPrice * 0.97)); // 3% below, rounded to $1 for SPY
    const diagonalStrikes = {
      shortStrike,
      longStrike: shortStrike - 5 // 5pts protection (SPY equivalent of SPX 50pts)
    };
    
    // Expiration dates based on Steve Guns' timing
    const expirations = {
      shortExpiration: new Date(currentTime.getTime() + 8 * 24 * 60 * 60 * 1000),  // 8 days
      longExpiration: new Date(currentTime.getTime() + 16 * 24 * 60 * 60 * 1000)   // 16 days
    };
    
    return {
      underlyingPrice,
      butterflyStrikes,
      diagonalStrikes,
      expirations
    };
  }
  
  /**
   * Filter real Alpaca options chain for Flyagonal requirements
   * 
   * @param realOptionsChain Real options data from Alpaca
   * @param requirements Flyagonal data requirements
   * @returns Filtered options chain with only required strikes
   */
  static filterOptionsForFlyagonal(
    realOptionsChain: OptionsChain[], 
    requirements: FlyagonalDataRequirements
  ): {
    flyagonalOptions: OptionsChain[];
    missingStrikes: string[];
    dataQuality: {
      totalRequired: number;
      totalFound: number;
      completeness: number;
      liquidityScore: number;
    };
  } {
    
    const { butterflyStrikes, diagonalStrikes, expirations } = requirements;
    const flyagonalOptions: OptionsChain[] = [];
    const missingStrikes: string[] = [];
    
    // Required strikes for Flyagonal
    const requiredOptions = [
      // Butterfly calls (short expiration)
      { type: 'CALL', strike: butterflyStrikes.longLower, expiration: expirations.shortExpiration },
      { type: 'CALL', strike: butterflyStrikes.short, expiration: expirations.shortExpiration },
      { type: 'CALL', strike: butterflyStrikes.longUpper, expiration: expirations.shortExpiration },
      
      // Diagonal puts (mixed expirations)
      { type: 'PUT', strike: diagonalStrikes.shortStrike, expiration: expirations.shortExpiration },
      { type: 'PUT', strike: diagonalStrikes.longStrike, expiration: expirations.longExpiration }
    ];
    
    let totalLiquidity = 0;
    let foundOptions = 0;
    
    // Find each required option in real data
    for (const required of requiredOptions) {
      const matchingOption = realOptionsChain.find(option => 
        option.type === required.type &&
        option.strike === required.strike &&
        Math.abs(option.expiration.getTime() - required.expiration.getTime()) < 24 * 60 * 60 * 1000 // Same day
      );
      
      if (matchingOption) {
        flyagonalOptions.push(matchingOption);
        foundOptions++;
        
        // Calculate liquidity score
        const volume = matchingOption.volume || 0;
        const openInterest = matchingOption.openInterest || 0;
        const bidAskSpread = (matchingOption.ask || 0) - (matchingOption.bid || 0);
        
        // Liquidity score: volume + OI, penalized by wide spreads
        const liquidityScore = (volume + openInterest * 0.5) / Math.max(1, bidAskSpread * 10);
        totalLiquidity += liquidityScore;
        
      } else {
        missingStrikes.push(`${required.type} ${required.strike} ${required.expiration.toDateString()}`);
      }
    }
    
    const completeness = foundOptions / requiredOptions.length;
    const avgLiquidityScore = foundOptions > 0 ? totalLiquidity / foundOptions : 0;
    
    return {
      flyagonalOptions,
      missingStrikes,
      dataQuality: {
        totalRequired: requiredOptions.length,
        totalFound: foundOptions,
        completeness,
        liquidityScore: avgLiquidityScore
      }
    };
  }
  
  /**
   * Enhance options chain with real Greeks calculations
   * 
   * @param options Filtered options chain
   * @param underlyingPrice Current underlying price
   * @param riskFreeRate Current risk-free rate
   * @returns Enhanced options with Greeks
   */
  static enhanceWithGreeks(
    options: OptionsChain[], 
    underlyingPrice: number,
    riskFreeRate: number = 0.05
  ): EnhancedOptionsChain[] {
    
    return options.map(option => {
      try {
        // Calculate time to expiration in years
        const timeToExpiration = Math.max(0, 
          (option.expiration.getTime() - Date.now()) / (1000 * 60 * 60 * 24 * 365)
        );
        
        // Use implied volatility from real data, or estimate
        const impliedVol = option.impliedVolatility || 0.20;
        
        // Calculate Greeks using real market data
        const greeksResult = GreeksSimulator.calculateOptionPrice({
          underlyingPrice,
          strikePrice: option.strike,
          timeToExpiration,
          riskFreeRate,
          volatility: impliedVol,
          optionType: option.type.toLowerCase() as 'call' | 'put',
          dividendYield: 0
        });
        
        // Calculate real market metrics
        const bidAskSpread = (option.ask || 0) - (option.bid || 0);
        const midPrice = ((option.ask || 0) + (option.bid || 0)) / 2;
        const volumeWeightedPrice = option.last || midPrice;
        
        // Liquidity score based on volume, OI, and spread
        const volume = option.volume || 0;
        const openInterest = option.openInterest || 0;
        const liquidityScore = Math.min(100, 
          (volume * 2 + openInterest) / Math.max(1, bidAskSpread * 100)
        );
        
        const enhanced: EnhancedOptionsChain = {
          ...option,
          greeks: {
            delta: greeksResult.delta,
            gamma: greeksResult.gamma,
            theta: greeksResult.theta,
            vega: greeksResult.vega,
            rho: greeksResult.rho
          },
          realMetrics: {
            bidAskSpread,
            midPrice,
            volumeWeightedPrice,
            liquidityScore
          }
        };
        
        return enhanced;
        
      } catch (error) {
        console.warn(`⚠️ Failed to calculate Greeks for ${option.symbol}:`, error);
        
        // Return original option if Greeks calculation fails
        return {
          ...option,
          realMetrics: {
            bidAskSpread: (option.ask || 0) - (option.bid || 0),
            midPrice: ((option.ask || 0) + (option.bid || 0)) / 2,
            volumeWeightedPrice: option.last || 0,
            liquidityScore: 0
          }
        } as EnhancedOptionsChain;
      }
    });
  }
  
  /**
   * Validate data quality for Flyagonal strategy
   * 
   * @param dataQuality Data quality metrics
   * @returns Validation result with recommendations
   */
  static validateDataQuality(dataQuality: any): {
    isValid: boolean;
    warnings: string[];
    recommendations: string[];
  } {
    const warnings: string[] = [];
    const recommendations: string[] = [];
    
    // Check completeness
    if (dataQuality.completeness < 1.0) {
      warnings.push(`Missing ${dataQuality.totalRequired - dataQuality.totalFound} required options contracts`);
      recommendations.push('Consider using different expiration dates or strike spacing');
    }
    
    // Check liquidity
    if (dataQuality.liquidityScore < 10) {
      warnings.push('Low liquidity detected in required options');
      recommendations.push('Consider trading during market hours with higher volume');
    }
    
    // Minimum requirements for Flyagonal
    const isValid = dataQuality.completeness >= 0.8 && dataQuality.liquidityScore >= 5;
    
    if (!isValid) {
      recommendations.push('Strategy may not perform optimally with current data quality');
      recommendations.push('Consider waiting for better market conditions or different strikes');
    }
    
    return { isValid, warnings, recommendations };
  }
  
  /**
   * Fetch real VIX data from free providers
   * 
   * IMPLEMENTED: Uses multiple free VIX data sources:
   * 1. Yahoo Finance (no API key needed) - Primary
   * 2. Alpha Vantage (free tier) - Backup
   * 3. FRED (Federal Reserve) - Backup
   * 4. Polygon.io (free tier) - Backup
   * 5. Twelve Data (free tier) - Backup
   * 
   * @param date Date to fetch VIX for
   * @returns Real VIX value or null if unavailable
   */
  static async fetchRealVIX(date: Date): Promise<number | null> {
    try {
      // Import the free VIX provider
      const { FreeVIXDataProvider } = await import('../../data/free-vix-providers');
      
      // Fetch current VIX from free providers
      const vixData = await FreeVIXDataProvider.getCurrentVIX(date);
      
      if (vixData && vixData.value > 0) {
        console.log(`✅ Real VIX data fetched: ${vixData.value.toFixed(2)} from ${vixData.source}`);
        return vixData.value;
      } else {
        console.warn('⚠️ No VIX data available from free providers');
        return null;
      }
      
    } catch (error) {
      console.error('❌ Error fetching real VIX data:', (error as Error).message);
      return null; // Return null to trigger estimation fallback
    }
  }

  /**
   * Fetch historical VIX data for backtesting
   * 
   * @param startDate Start date for historical data
   * @param endDate End date for historical data
   * @returns Array of VIX data points
   */
  static async fetchHistoricalVIX(startDate: Date, endDate: Date): Promise<Array<{ date: Date; value: number }>> {
    try {
      const { FreeVIXDataProvider } = await import('../../data/free-vix-providers');
      
      console.log(`📈 Fetching historical VIX data from ${startDate.toDateString()} to ${endDate.toDateString()}`);
      
      const vixHistory = await FreeVIXDataProvider.getHistoricalVIX(startDate, endDate);
      
      if (vixHistory.length > 0) {
        console.log(`✅ Retrieved ${vixHistory.length} historical VIX data points`);
        return vixHistory.map(point => ({
          date: point.date,
          value: point.value
        }));
      } else {
        console.warn('⚠️ No historical VIX data available');
        return [];
      }
      
    } catch (error) {
      console.error('❌ Error fetching historical VIX data:', (error as Error).message);
      return [];
    }
  }
  
  /**
   * Create comprehensive real data report for Flyagonal
   * 
   * @param marketData Real market data
   * @param optionsData Real options data
   * @param requirements Strategy requirements
   * @returns Comprehensive data quality report
   */
  static generateDataQualityReport(
    marketData: MarketData[],
    optionsData: OptionsChain[],
    requirements: FlyagonalDataRequirements
  ): {
    marketDataQuality: any;
    optionsDataQuality: any;
    flyagonalSpecific: any;
    recommendations: string[];
    overallScore: number;
  } {
    
    // Analyze market data quality
    const marketDataQuality = {
      totalBars: marketData.length,
      timespan: marketData.length > 0 ? 
        marketData[marketData.length - 1].timestamp.getTime() - marketData[0].timestamp.getTime() : 0,
      avgVolume: marketData.reduce((sum, bar) => sum + (bar.volume || 0), 0) / marketData.length,
      priceRange: marketData.length > 0 ? 
        Math.max(...marketData.map(bar => bar.high)) - Math.min(...marketData.map(bar => bar.low)) : 0
    };
    
    // Analyze options data quality
    const filteredData = this.filterOptionsForFlyagonal(optionsData, requirements);
    const optionsDataQuality = filteredData.dataQuality;
    
    // Flyagonal-specific analysis
    const flyagonalSpecific = {
      requiredStrikes: requirements.butterflyStrikes,
      diagonalStrikes: requirements.diagonalStrikes,
      missingStrikes: filteredData.missingStrikes,
      dataCompleteness: optionsDataQuality.completeness
    };
    
    // Generate recommendations
    const recommendations: string[] = [];
    
    if (marketDataQuality.totalBars < 20) {
      recommendations.push('Insufficient market data bars - need at least 20 for technical analysis');
    }
    
    if (optionsDataQuality.completeness < 0.8) {
      recommendations.push('Missing critical options strikes - consider alternative expiration dates');
    }
    
    if (optionsDataQuality.liquidityScore < 10) {
      recommendations.push('Low options liquidity - consider trading during peak hours');
    }
    
    // Calculate overall score
    const marketScore = Math.min(100, marketDataQuality.totalBars * 2); // 2 points per bar, max 100
    const optionsScore = optionsDataQuality.completeness * 100;
    const liquidityScore = Math.min(100, optionsDataQuality.liquidityScore * 5);
    
    const overallScore = (marketScore + optionsScore + liquidityScore) / 3;
    
    return {
      marketDataQuality,
      optionsDataQuality,
      flyagonalSpecific,
      recommendations,
      overallScore
    };
  }
}

/**
 * Real data configuration for Flyagonal backtesting
 */
export interface FlyagonalBacktestConfig {
  /** Symbol to backtest (typically SPY or SPX) */
  symbol: string;
  
  /** Start date for backtest */
  startDate: Date;
  
  /** End date for backtest */
  endDate: Date;
  
  /** Timeframe for market data */
  timeframe: string;
  
  /** Whether to include real options data */
  includeOptionsData: boolean;
  
  /** Whether to include real VIX data */
  includeVIXData: boolean;
  
  /** Minimum data quality score required */
  minDataQualityScore: number;
  
  /** Risk-free rate for Greeks calculations */
  riskFreeRate: number;
}

/**
 * Default configuration for Flyagonal real data backtesting
 */
export const DEFAULT_FLYAGONAL_BACKTEST_CONFIG: FlyagonalBacktestConfig = {
  symbol: 'SPY',
  startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
  endDate: new Date(),
  timeframe: '1Hour',
  includeOptionsData: true,
  includeVIXData: true,
  minDataQualityScore: 70,
  riskFreeRate: 0.05
};
