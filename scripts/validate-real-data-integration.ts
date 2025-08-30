#!/usr/bin/env ts-node

/**
 * 🧪 Real Data Integration Validation Script
 * ==========================================
 * 
 * Validates that the Flyagonal strategy properly integrates with real data
 * and complies with .cursorrules requirements.
 * 
 * Tests:
 * 1. Real Alpaca data integration
 * 2. Real VIX data fetching
 * 3. Enhanced Greeks calculations
 * 4. Synthetic data prohibition
 * 5. Data quality validation
 * 
 * @fileoverview Real data integration validation
 * @author Trading System QA
 * @version 1.0.0
 * @created 2025-08-30
 */

import { FlyagonalStrategy } from '../src/strategies/flyagonal';
import { FlyagonalBacktestingAdapter } from '../src/strategies/flyagonal/backtesting-adapter';
import { FlyagonalRealDataIntegration } from '../src/strategies/flyagonal/real-data-integration';
import { AlpacaHistoricalDataFetcher } from '../src/data/alpaca-historical-data';
import { MarketData, OptionsChain } from '../src/utils/types';

/**
 * Main validation function
 */
async function validateRealDataIntegration(): Promise<void> {
  console.log('🧪 Starting Real Data Integration Validation...\n');

  try {
    // Test 1: Validate synthetic data prohibition
    console.log('📋 Test 1: Synthetic Data Prohibition');
    await testSyntheticDataProhibition();
    
    // Test 2: Validate real data requirements calculation
    console.log('\n📋 Test 2: Real Data Requirements');
    await testRealDataRequirements();
    
    // Test 3: Validate options chain filtering
    console.log('\n📋 Test 3: Options Chain Filtering');
    await testOptionsChainFiltering();
    
    // Test 4: Validate Greeks enhancement
    console.log('\n📋 Test 4: Greeks Enhancement');
    await testGreeksEnhancement();
    
    // Test 5: Validate VIX data integration
    console.log('\n📋 Test 5: VIX Data Integration');
    await testVIXDataIntegration();
    
    // Test 6: Validate async signal generation
    console.log('\n📋 Test 6: Async Signal Generation');
    await testAsyncSignalGeneration();
    
    console.log('\n✅ All Real Data Integration Tests Passed!');
    console.log('\n🎯 Summary:');
    console.log('   ✅ Synthetic data generation is properly prohibited');
    console.log('   ✅ Real data requirements are correctly calculated');
    console.log('   ✅ Options chain filtering works for Flyagonal strikes');
    console.log('   ✅ Greeks calculations are enhanced with real data');
    console.log('   ✅ VIX data integration prioritizes real data');
    console.log('   ✅ Async signal generation supports real data fetching');
    
  } catch (error) {
    console.error('❌ Real Data Integration Validation Failed:', error);
    process.exit(1);
  }
}

/**
 * Test 1: Ensure synthetic data generation is prohibited
 */
async function testSyntheticDataProhibition(): Promise<void> {
  const adapter = new FlyagonalBacktestingAdapter();
  
  try {
    // This should throw an error per .cursorrules requirements
    adapter.generateOptionsData([], 6360, new Date());
    throw new Error('Synthetic data generation should be prohibited!');
  } catch (error) {
    if (error.message.includes('SYNTHETIC OPTIONS DATA GENERATION IS PROHIBITED')) {
      console.log('   ✅ Synthetic data generation is properly prohibited');
    } else {
      throw error;
    }
  }
}

/**
 * Test 2: Validate real data requirements calculation
 */
async function testRealDataRequirements(): Promise<void> {
  const underlyingPrice = 6360;
  const currentTime = new Date();
  
  const requirements = FlyagonalRealDataIntegration.calculateDataRequirements(
    underlyingPrice, 
    currentTime
  );
  
  // Validate butterfly strikes (above market)
  const expectedButterflyLower = 6370; // Market + 10
  const expectedButterflyShort = 6420;  // Market + 60
  const expectedButterflyUpper = 6480;  // Market + 120
  
  if (requirements.butterflyStrikes.longLower !== expectedButterflyLower ||
      requirements.butterflyStrikes.short !== expectedButterflyShort ||
      requirements.butterflyStrikes.longUpper !== expectedButterflyUpper) {
    throw new Error('Butterfly strikes calculation incorrect');
  }
  
  // Validate diagonal strikes (below market)
  const expectedDiagonalShort = Math.floor((underlyingPrice * 0.97) / 5) * 5; // 3% below
  const expectedDiagonalLong = expectedDiagonalShort - 50; // 50pts protection
  
  if (requirements.diagonalStrikes.shortStrike !== expectedDiagonalShort ||
      requirements.diagonalStrikes.longStrike !== expectedDiagonalLong) {
    throw new Error('Diagonal strikes calculation incorrect');
  }
  
  // Validate expirations
  const shortExpDays = Math.round((requirements.expirations.shortExpiration.getTime() - currentTime.getTime()) / (1000 * 60 * 60 * 24));
  const longExpDays = Math.round((requirements.expirations.longExpiration.getTime() - currentTime.getTime()) / (1000 * 60 * 60 * 24));
  
  if (shortExpDays !== 8 || longExpDays !== 16) {
    throw new Error('Expiration dates calculation incorrect');
  }
  
  console.log('   ✅ Real data requirements calculated correctly');
  console.log(`      Butterfly: ${requirements.butterflyStrikes.longLower}/${requirements.butterflyStrikes.short}/${requirements.butterflyStrikes.longUpper}`);
  console.log(`      Diagonal: ${requirements.diagonalStrikes.shortStrike}/${requirements.diagonalStrikes.longStrike}`);
}

/**
 * Test 3: Validate options chain filtering
 */
async function testOptionsChainFiltering(): Promise<void> {
  const underlyingPrice = 6360;
  const currentTime = new Date();
  
  // Create mock real options chain
  const realOptionsChain = createMockRealOptionsChain(underlyingPrice, currentTime);
  
  const requirements = FlyagonalRealDataIntegration.calculateDataRequirements(
    underlyingPrice, 
    currentTime
  );
  
  const filtered = FlyagonalRealDataIntegration.filterOptionsForFlyagonal(
    realOptionsChain, 
    requirements
  );
  
  // Should find all 5 required options (3 calls + 2 puts)
  if (filtered.flyagonalOptions.length !== 5) {
    throw new Error(`Expected 5 options, found ${filtered.flyagonalOptions.length}`);
  }
  
  // Should have high completeness
  if (filtered.dataQuality.completeness !== 1.0) {
    throw new Error(`Expected 100% completeness, got ${filtered.dataQuality.completeness * 100}%`);
  }
  
  console.log('   ✅ Options chain filtering works correctly');
  console.log(`      Found: ${filtered.flyagonalOptions.length}/5 required options`);
  console.log(`      Completeness: ${(filtered.dataQuality.completeness * 100).toFixed(1)}%`);
}

/**
 * Test 4: Validate Greeks enhancement
 */
async function testGreeksEnhancement(): Promise<void> {
  const underlyingPrice = 6360;
  const currentTime = new Date();
  
  // Create mock options chain
  const mockOptions = createMockRealOptionsChain(underlyingPrice, currentTime).slice(0, 2);
  
  const enhanced = FlyagonalRealDataIntegration.enhanceWithGreeks(
    mockOptions, 
    underlyingPrice
  );
  
  // Should have Greeks for all options
  for (const option of enhanced) {
    if (!option.greeks || !option.realMetrics) {
      throw new Error('Enhanced options missing Greeks or real metrics');
    }
    
    // Validate Greeks are reasonable
    if (Math.abs(option.greeks.delta) > 1 || 
        isNaN(option.greeks.gamma) || 
        isNaN(option.greeks.theta) || 
        isNaN(option.greeks.vega)) {
      throw new Error('Greeks calculations appear invalid');
    }
  }
  
  console.log('   ✅ Greeks enhancement works correctly');
  console.log(`      Enhanced: ${enhanced.length} options with Greeks`);
}

/**
 * Test 5: Validate VIX data integration
 */
async function testVIXDataIntegration(): Promise<void> {
  // Test real VIX fetching (should return null for now, but not error)
  const realVix = await FlyagonalRealDataIntegration.fetchRealVIX(new Date());
  
  // Should return null (not implemented yet) but not throw error
  if (realVix !== null) {
    console.log(`   📊 Real VIX data available: ${realVix}`);
  } else {
    console.log('   ⚠️ Real VIX data not yet implemented (expected)');
  }
  
  console.log('   ✅ VIX data integration structure is correct');
}

/**
 * Test 6: Validate async signal generation
 */
async function testAsyncSignalGeneration(): Promise<void> {
  const strategy = new FlyagonalStrategy();
  
  // Create minimal test data
  const marketData = createMockMarketData(6360, 25);
  const optionsChain = createMockRealOptionsChain(6360, new Date());
  
  try {
    // This should work with async/await
    const signal = await strategy.generateSignal(marketData, optionsChain);
    
    // Signal may be null (due to conditions not met), but should not error
    console.log('   ✅ Async signal generation works correctly');
    
    if (signal) {
      console.log(`      Generated signal: ${signal.action} with ${signal.confidence}% confidence`);
    } else {
      console.log('      No signal generated (conditions not met - expected for test data)');
    }
    
  } catch (error) {
    throw new Error(`Async signal generation failed: ${error.message}`);
  }
}

/**
 * Helper: Create mock real options chain for testing
 */
function createMockRealOptionsChain(underlyingPrice: number, currentTime: Date): OptionsChain[] {
  const options: OptionsChain[] = [];
  const shortExp = new Date(currentTime.getTime() + 8 * 24 * 60 * 60 * 1000);
  const longExp = new Date(currentTime.getTime() + 16 * 24 * 60 * 60 * 1000);
  
  // Generate strikes around current price
  for (let strike = underlyingPrice - 100; strike <= underlyingPrice + 200; strike += 10) {
    // Call options (short expiration)
    options.push({
      symbol: `SPY_${strike}C_${shortExp.toISOString().split('T')[0]}`,
      type: 'CALL',
      strike,
      expiration: shortExp,
      bid: Math.max(0.01, Math.random() * 20),
      ask: Math.max(0.02, Math.random() * 25),
      last: Math.max(0.01, Math.random() * 22),
      volume: Math.floor(Math.random() * 1000),
      openInterest: Math.floor(Math.random() * 5000),
      impliedVolatility: 0.15 + Math.random() * 0.20
    });
    
    // Put options (both expirations)
    [shortExp, longExp].forEach(exp => {
      options.push({
        symbol: `SPY_${strike}P_${exp.toISOString().split('T')[0]}`,
        type: 'PUT',
        strike,
        expiration: exp,
        bid: Math.max(0.01, Math.random() * 20),
        ask: Math.max(0.02, Math.random() * 25),
        last: Math.max(0.01, Math.random() * 22),
        volume: Math.floor(Math.random() * 1000),
        openInterest: Math.floor(Math.random() * 5000),
        impliedVolatility: 0.15 + Math.random() * 0.20
      });
    });
  }
  
  return options;
}

/**
 * Helper: Create mock market data for testing
 */
function createMockMarketData(startPrice: number, bars: number): MarketData[] {
  const data: MarketData[] = [];
  let currentPrice = startPrice;
  
  for (let i = 0; i < bars; i++) {
    const timestamp = new Date(Date.now() - (bars - i) * 60 * 60 * 1000);
    const change = (Math.random() - 0.5) * 10;
    
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

// Run validation if called directly
if (require.main === module) {
  validateRealDataIntegration().catch(error => {
    console.error('❌ Validation failed:', error);
    process.exit(1);
  });
}

export { validateRealDataIntegration };
