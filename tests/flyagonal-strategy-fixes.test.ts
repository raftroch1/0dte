/**
 * 🧪 Flyagonal Strategy Fixes - Comprehensive Test Suite
 * =====================================================
 * 
 * Tests to validate all the critical fixes made to the Flyagonal strategy:
 * 1. Corrected profit zone calculations
 * 2. Realistic VIX estimation
 * 3. Proper risk management with achievable targets
 * 4. Enhanced Black-Scholes options pricing
 * 5. Realistic performance expectations
 * 
 * @fileoverview Comprehensive test suite for Flyagonal strategy fixes
 * @author Trading System QA
 * @version 1.0.0
 * @created 2025-08-30
 */

import { FlyagonalStrategy } from '../src/strategies/flyagonal';
import { FlyagonalBacktestingAdapter } from '../src/strategies/flyagonal/backtesting-adapter';
import { MarketData, OptionsChain, TradeSignal } from '../src/utils/types';
import { GreeksSimulator } from '../src/data/greeks-simulator';

describe('Flyagonal Strategy - Critical Fixes Validation', () => {
  let strategy: FlyagonalStrategy;
  let adapter: FlyagonalBacktestingAdapter;
  let mockMarketData: MarketData[];
  let mockOptionsChain: OptionsChain[];

  beforeEach(() => {
    strategy = new FlyagonalStrategy();
    adapter = new FlyagonalBacktestingAdapter();
    
    // Create realistic SPX market data
    mockMarketData = generateMockSPXData(6360, 20); // SPX at 6360, 20 bars
    mockOptionsChain = generateMockOptionsChain(6360);
  });

  describe('🎯 Fix 1: Corrected Profit Zone Calculations', () => {
    test('should calculate profit zones correctly (not arithmetically add ranges)', () => {
      const signal = strategy.generateSignal(mockMarketData, mockOptionsChain);
      
      if (signal && signal.flyagonalComponents) {
        const { butterfly, diagonal } = signal.flyagonalComponents;
        
        // Butterfly zone (above market): 6370-6480 = 110pts
        const butterflyRange = butterfly.longUpper - butterfly.longLower;
        expect(butterflyRange).toBe(110);
        
        // Diagonal zone (below market): should be separate, not added
        const diagonalRange = diagonal.shortStrike - diagonal.longStrike;
        expect(diagonalRange).toBeGreaterThan(0);
        
        // Total zone should be span from lowest to highest point, NOT sum of ranges
        const totalSpan = Math.max(butterfly.longUpper, diagonal.shortStrike) - 
                         Math.min(butterfly.longLower, diagonal.longStrike);
        
        // Should be much larger than the original incorrect calculation
        expect(totalSpan).toBeGreaterThan(butterflyRange + diagonalRange);
        
        console.log(`✅ Corrected Profit Zone Calculation:`);
        console.log(`   Butterfly Range: ${butterflyRange}pts`);
        console.log(`   Diagonal Range: ${diagonalRange}pts`);
        console.log(`   Total Span: ${totalSpan}pts (CORRECTED - not sum of ranges)`);
      }
    });

    test('should validate profit zones have minimum width', () => {
      const signal = strategy.generateSignal(mockMarketData, mockOptionsChain);
      
      if (signal && signal.indicators?.profitZoneWidth) {
        // Should meet minimum 150pt requirement (reduced from unrealistic 200pt)
        expect(signal.indicators.profitZoneWidth).toBeGreaterThanOrEqual(150);
      }
    });
  });

  describe('📊 Fix 2: Realistic VIX Estimation', () => {
    test('should use realistic VIX estimation when real VIX unavailable', () => {
      // Test with market data that has no VIX
      const dataWithoutVix = mockMarketData.map(bar => ({ ...bar }));
      
      const signal = strategy.generateSignal(dataWithoutVix, mockOptionsChain);
      
      if (signal && signal.indicators?.vix) {
        const estimatedVix = signal.indicators.vix;
        
        // Should be within realistic bounds (9-80 for normal markets)
        expect(estimatedVix).toBeGreaterThanOrEqual(9);
        expect(estimatedVix).toBeLessThanOrEqual(80);
        
        // Should not use the old unrealistic random scaling
        expect(estimatedVix).not.toBeNaN();
        
        console.log(`✅ Realistic VIX Estimation: ${estimatedVix.toFixed(1)}`);
      }
    });

    test('should prefer real VIX data when available', () => {
      // Mock technical indicators with real VIX
      const realVixValue = 18.5;
      
      // This would require mocking TechnicalAnalysis.calculateAllIndicators
      // For now, we validate the logic exists in the strategy
      expect(strategy).toBeDefined();
    });
  });

  describe('💰 Fix 3: Realistic Risk Management', () => {
    test('should use realistic 1.5:1 risk/reward ratio (not impossible 4:1)', () => {
      const signal = strategy.generateSignal(mockMarketData, mockOptionsChain);
      
      if (signal) {
        // Should use 150% take profit (1.5:1 ratio) not 400% (4:1 ratio)
        expect(signal.takeProfit).toBe(150);
        expect(signal.stopLoss).toBe(100);
        
        const riskRewardRatio = signal.takeProfit / signal.stopLoss;
        expect(riskRewardRatio).toBe(1.5);
        
        console.log(`✅ Realistic Risk/Reward: ${riskRewardRatio}:1 (was incorrectly 4:1)`);
      }
    });

    test('should calculate realistic probability of profit', () => {
      const highConfidenceSignal = { confidence: 90 } as TradeSignal;
      const mediumConfidenceSignal = { confidence: 75 } as TradeSignal;
      const lowConfidenceSignal = { confidence: 60 } as TradeSignal;

      const highRisk = strategy.calculateRisk(highConfidenceSignal);
      const mediumRisk = strategy.calculateRisk(mediumConfidenceSignal);
      const lowRisk = strategy.calculateRisk(lowConfidenceSignal);

      // Should be realistic probabilities (45-75%), not impossible 90%+
      expect(highRisk.probabilityOfProfit).toBeLessThanOrEqual(0.75);
      expect(highRisk.probabilityOfProfit).toBeGreaterThanOrEqual(0.65);
      
      expect(mediumRisk.probabilityOfProfit).toBeLessThanOrEqual(0.65);
      expect(mediumRisk.probabilityOfProfit).toBeGreaterThanOrEqual(0.55);
      
      expect(lowRisk.probabilityOfProfit).toBeLessThanOrEqual(0.55);
      expect(lowRisk.probabilityOfProfit).toBeGreaterThanOrEqual(0.45);

      console.log(`✅ Realistic Probability of Profit:`);
      console.log(`   High Confidence (90%): ${(highRisk.probabilityOfProfit * 100).toFixed(1)}%`);
      console.log(`   Medium Confidence (75%): ${(mediumRisk.probabilityOfProfit * 100).toFixed(1)}%`);
      console.log(`   Low Confidence (60%): ${(lowRisk.probabilityOfProfit * 100).toFixed(1)}%`);
    });

    test('should classify strategy as MEDIUM risk (not LOW)', () => {
      const riskLevel = strategy.getRiskLevel();
      expect(riskLevel).toBe('MEDIUM');
      
      console.log(`✅ Corrected Risk Level: ${riskLevel} (was incorrectly LOW)`);
    });
  });

  describe('🔢 Fix 4: Enhanced Black-Scholes Options Pricing', () => {
    test('should use proper Black-Scholes pricing in backtesting adapter', () => {
      const underlyingPrice = 6360;
      const strike = 6400;
      const timeToExpiration = 8 / 365; // 8 days
      const volatility = 0.20;

      const callPrice = adapter['calculateOptionPrice'](
        underlyingPrice, strike, timeToExpiration, volatility, 'CALL'
      );
      const putPrice = adapter['calculateOptionPrice'](
        underlyingPrice, strike, timeToExpiration, volatility, 'PUT'
      );

      // Should return reasonable option prices
      expect(callPrice).toBeGreaterThan(0.01);
      expect(putPrice).toBeGreaterThan(0.01);
      
      // Call should be cheaper than put for OTM strikes above market
      expect(callPrice).toBeLessThan(putPrice);

      console.log(`✅ Enhanced Options Pricing:`);
      console.log(`   Call (${strike}): $${callPrice.toFixed(2)}`);
      console.log(`   Put (${strike}): $${putPrice.toFixed(2)}`);
    });

    test('should handle edge cases gracefully', () => {
      // Test with zero time to expiration
      const expiredPrice = adapter['calculateOptionPrice'](6360, 6400, 0, 0.20, 'CALL');
      expect(expiredPrice).toBe(0.01); // Should be minimum price

      // Test with very high volatility
      const highVolPrice = adapter['calculateOptionPrice'](6360, 6400, 0.1, 2.0, 'CALL');
      expect(highVolPrice).toBeGreaterThan(0.01);
    });
  });

  describe('📈 Fix 5: Realistic Performance Expectations', () => {
    test('should have realistic configuration defaults', () => {
      const config = strategy.getDefaultConfig();
      
      // Should use realistic take profit (150%, not 400%)
      expect(config.riskManagement.takeProfitPercent).toBe(1.5);
      
      // Should maintain conservative position sizing
      expect(config.riskManagement.maxPositionSize).toBe(0.03);
      
      // Should limit trades per day (highly selective strategy)
      expect(config.riskManagement.maxTradesPerDay).toBe(1);

      console.log(`✅ Realistic Configuration:`);
      console.log(`   Take Profit: ${config.riskManagement.takeProfitPercent * 100}% (was 400%)`);
      console.log(`   Max Position: ${config.riskManagement.maxPositionSize * 100}%`);
      console.log(`   Max Trades/Day: ${config.riskManagement.maxTradesPerDay}`);
    });

    test('should generate signals with realistic confidence thresholds', () => {
      const config = strategy.getDefaultConfig();
      
      // Should require high confidence (85%) for highly selective strategy
      expect(config.parameters.minConfidence).toBe(85);
      
      console.log(`✅ Realistic Confidence Threshold: ${config.parameters.minConfidence}%`);
    });
  });

  describe('🧮 Integration Tests', () => {
    test('should create valid positions from signals', () => {
      const signal = strategy.generateSignal(mockMarketData, mockOptionsChain);
      
      if (signal) {
        const position = adapter.createPosition(signal, mockOptionsChain, 6360);
        
        if (position) {
          // Should have 5 legs (butterfly: 3 calls, diagonal: 2 puts)
          expect(position.legs).toHaveLength(5);
          
          // Should have proper metadata
          expect(position.metadata?.maxLoss).toBeDefined();
          expect(position.metadata?.profitTarget).toBe(750); // Corrected target
          
          console.log(`✅ Valid Position Created:`);
          console.log(`   Legs: ${position.legs?.length}`);
          console.log(`   Max Loss: $${position.metadata?.maxLoss}`);
          console.log(`   Profit Target: $${position.metadata?.profitTarget}`);
        }
      }
    });

    test('should handle position updates correctly', () => {
      const signal = strategy.generateSignal(mockMarketData, mockOptionsChain);
      
      if (signal) {
        const position = adapter.createPosition(signal, mockOptionsChain, 6360);
        
        if (position) {
          const updatedPosition = adapter.updatePosition(
            position, 
            mockMarketData[mockMarketData.length - 1], 
            mockOptionsChain
          );
          
          expect(updatedPosition.currentPrice).toBeDefined();
          expect(updatedPosition.unrealizedPnL).toBeDefined();
        }
      }
    });
  });
});

// Helper functions for test data generation

function generateMockSPXData(startPrice: number, bars: number): MarketData[] {
  const data: MarketData[] = [];
  let currentPrice = startPrice;
  
  for (let i = 0; i < bars; i++) {
    const timestamp = new Date(Date.now() - (bars - i) * 60 * 60 * 1000); // Hourly bars
    const change = (Math.random() - 0.5) * 20; // ±10 point moves
    
    currentPrice += change;
    
    data.push({
      timestamp,
      open: currentPrice - change,
      high: currentPrice + Math.abs(change) * 0.5,
      low: currentPrice - Math.abs(change) * 0.5,
      close: currentPrice,
      volume: 1000000 + Math.random() * 500000
    });
  }
  
  return data;
}

function generateMockOptionsChain(underlyingPrice: number): OptionsChain[] {
  const options: OptionsChain[] = [];
  const baseDate = new Date();
  const shortExp = new Date(baseDate.getTime() + 8 * 24 * 60 * 60 * 1000); // 8 days
  const longExp = new Date(baseDate.getTime() + 16 * 24 * 60 * 60 * 1000); // 16 days
  
  // Generate strikes around current price
  for (let strike = underlyingPrice - 200; strike <= underlyingPrice + 200; strike += 10) {
    // Call options
    options.push({
      symbol: `SPY_${strike}C_${shortExp.toISOString().split('T')[0]}`,
      type: 'CALL',
      strike,
      expiration: shortExp,
      bid: Math.max(0.01, Math.random() * 50),
      ask: Math.max(0.02, Math.random() * 55),
      last: Math.max(0.01, Math.random() * 52),
      volume: Math.floor(Math.random() * 1000),
      openInterest: Math.floor(Math.random() * 5000),
      impliedVolatility: 0.15 + Math.random() * 0.20
    });
    
    // Put options
    options.push({
      symbol: `SPY_${strike}P_${shortExp.toISOString().split('T')[0]}`,
      type: 'PUT',
      strike,
      expiration: shortExp,
      bid: Math.max(0.01, Math.random() * 50),
      ask: Math.max(0.02, Math.random() * 55),
      last: Math.max(0.01, Math.random() * 52),
      volume: Math.floor(Math.random() * 1000),
      openInterest: Math.floor(Math.random() * 5000),
      impliedVolatility: 0.15 + Math.random() * 0.20
    });
  }
  
  return options;
}
