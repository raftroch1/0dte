// FIX: Test script to verify improved 0DTE system generates trades
import { MarketData, OptionsChain, Strategy } from '../src/utils/types';
import { AdaptiveStrategySelector } from '../src/strategies/adaptive-strategy-selector';
import { SimpleMomentumStrategy } from '../src/strategies/simple-momentum-strategy';

// Mock market data for testing
const mockMarketData: MarketData[] = [
  { timestamp: new Date(), open: 430, high: 432, low: 429, close: 431, volume: 1000000 },
  { timestamp: new Date(), open: 431, high: 433, low: 430, close: 432, volume: 1100000 },
  { timestamp: new Date(), open: 432, high: 434, low: 431, close: 433, volume: 1200000 },
  { timestamp: new Date(), open: 433, high: 435, low: 432, close: 434, volume: 1300000 },
  { timestamp: new Date(), open: 434, high: 436, low: 433, close: 435, volume: 1400000 },
  { timestamp: new Date(), open: 435, high: 437, low: 434, close: 436, volume: 1500000 },
  { timestamp: new Date(), open: 436, high: 438, low: 435, close: 437, volume: 1600000 },
  { timestamp: new Date(), open: 437, high: 439, low: 436, close: 438, volume: 1700000 },
  { timestamp: new Date(), open: 438, high: 440, low: 437, close: 439, volume: 1800000 },
  { timestamp: new Date(), open: 439, high: 441, low: 438, close: 440, volume: 1900000 },
  { timestamp: new Date(), open: 440, high: 442, low: 439, close: 441, volume: 2000000 },
  { timestamp: new Date(), open: 441, high: 443, low: 440, close: 442, volume: 2100000 },
  { timestamp: new Date(), open: 442, high: 444, low: 441, close: 443, volume: 2200000 },
  { timestamp: new Date(), open: 443, high: 445, low: 442, close: 444, volume: 2300000 },
  { timestamp: new Date(), open: 444, high: 446, low: 443, close: 445, volume: 2400000 },
  { timestamp: new Date(), open: 445, high: 447, low: 444, close: 446, volume: 2500000 },
  { timestamp: new Date(), open: 446, high: 448, low: 445, close: 447, volume: 2600000 },
  { timestamp: new Date(), open: 447, high: 449, low: 446, close: 448, volume: 2700000 },
  { timestamp: new Date(), open: 448, high: 450, low: 447, close: 449, volume: 2800000 },
  { timestamp: new Date(), open: 449, high: 451, low: 448, close: 450, volume: 2900000 }
];

// Mock options chain
const mockOptionsChain: OptionsChain[] = [
  { strike: 445, expiration: new Date(), type: 'CALL', bid: 2.50, ask: 2.70, impliedVolatility: 0.25, delta: 0.45, volume: 500, openInterest: 1000 },
  { strike: 450, expiration: new Date(), type: 'CALL', bid: 1.80, ask: 2.00, impliedVolatility: 0.23, delta: 0.35, volume: 800, openInterest: 1500 },
  { strike: 455, expiration: new Date(), type: 'CALL', bid: 1.20, ask: 1.40, impliedVolatility: 0.22, delta: 0.25, volume: 600, openInterest: 1200 },
  { strike: 445, expiration: new Date(), type: 'PUT', bid: 1.30, ask: 1.50, impliedVolatility: 0.24, delta: -0.45, volume: 400, openInterest: 800 },
  { strike: 450, expiration: new Date(), type: 'PUT', bid: 2.10, ask: 2.30, impliedVolatility: 0.26, delta: -0.55, volume: 700, openInterest: 1300 },
  { strike: 455, expiration: new Date(), type: 'PUT', bid: 3.20, ask: 3.50, impliedVolatility: 0.28, delta: -0.65, volume: 300, openInterest: 600 }
];

// Mock strategy configuration optimized for 0DTE
const mockStrategy: Strategy = {
  name: '0DTE_Momentum_Strategy',
  positionSizePercent: 2,
  maxPositions: 3,
  stopLossPercent: 30,
  takeProfitPercent: 50,
  maxDailyLoss: -500,
  dailyProfitTarget: 225,
  rsiPeriod: 14,
  rsiOversold: 35,
  rsiOverbought: 65,
  macdFast: 12,
  macdSlow: 26,
  macdSignal: 9,
  bbPeriod: 20,
  bbStdDev: 2,
  maxHoldingTimeMinutes: 240,
  timeDecayExitMinutes: 30,
  momentumThreshold: 0.1,
  volumeConfirmation: 1.2,
  vixFilterMax: 50,
  vixFilterMin: 10
};

// Test the improved system
function testImprovedSystem() {
  console.log('🧪 TESTING IMPROVED 0DTE SYSTEM...\n');
  
  // Test 1: Strategy Selection
  console.log('📊 TEST 1: Strategy Selection with Relaxed Filters');
  const vixLevel = 25; // Moderate VIX level
  
  const strategySelection = AdaptiveStrategySelector.generateAdaptiveSignal(
    mockMarketData,
    mockOptionsChain,
    mockStrategy,
    vixLevel
  );
  
  console.log(`Selected Strategy: ${strategySelection.selectedStrategy}`);
  console.log(`Market Regime: ${strategySelection.marketRegime.regime} (${strategySelection.marketRegime.confidence}% confidence)`);
  console.log(`Signal Generated: ${strategySelection.signal ? 'YES' : 'NO'}`);
  if (strategySelection.signal) {
    console.log(`Signal Action: ${strategySelection.signal.action} (${strategySelection.signal.confidence}% confidence)`);
    console.log(`Signal Reason: ${strategySelection.signal.reason}`);
  }
  console.log(`Reasoning: ${strategySelection.reasoning.join(', ')}\n`);
  
  // Test 2: Position Sizing for $35k Account
  console.log('💰 TEST 2: Position Sizing for $35k Account');
  const accountBalance = 35000;
  const currentPrice = 2.0; // Option premium
  const volatility = 0.25;
  
  const positionSize = StrategyEngine.calculatePositionSize(
    accountBalance,
    mockStrategy,
    currentPrice,
    volatility
  );
  
  console.log(`Position Size: ${positionSize} contracts`);
  console.log(`Total Risk: $${(positionSize * currentPrice * 100 * 0.3).toFixed(2)} (30% stop loss)`);
  console.log(`Potential Profit: $${(positionSize * currentPrice * 100 * 0.5).toFixed(2)} (50% take profit)\n`);
  
  // Test 3: Daily Limits Check
  console.log('🎯 TEST 3: Daily Limits for Profit Target');
  const dailyPnL = 180; // Current P&L
  const dailyCheck = StrategyEngine.checkDailyLimits(dailyPnL, 225, -500);
  
  console.log(`Current Daily P&L: $${dailyPnL}`);
  console.log(`Should Stop Trading: ${dailyCheck.shouldStop}`);
  console.log(`Reason: ${dailyCheck.reason}\n`);
  
  // Test 4: 0DTE Detection
  console.log('⏰ TEST 4: 0DTE Detection');
  const expirationToday = new Date();
  const expirationTomorrow = new Date();
  expirationTomorrow.setDate(expirationTomorrow.getDate() + 1);
  
  console.log(`Today's expiration is 0DTE: ${StrategyEngine.is0DTE(expirationToday)}`);
  console.log(`Tomorrow's expiration is 0DTE: ${StrategyEngine.is0DTE(expirationTomorrow)}\n`);
  
  // Test 5: Strike Selection
  console.log('🎯 TEST 5: Optimal Strike Selection');
  const currentSpyPrice = 450;
  const timeWindow = 'MORNING_MOMENTUM';
  
  const callStrike = StrategyEngine.getOptimal0DTEStrike(currentSpyPrice, 'CALL', timeWindow, volatility);
  const putStrike = StrategyEngine.getOptimal0DTEStrike(currentSpyPrice, 'PUT', timeWindow, volatility);
  
  console.log(`Call Strike: $${(currentSpyPrice + callStrike.strikeOffset).toFixed(2)} (Target Delta: ${callStrike.targetDelta})`);
  console.log(`Call Reasoning: ${callStrike.reasoning}`);
  console.log(`Put Strike: $${(currentSpyPrice + putStrike.strikeOffset).toFixed(2)} (Target Delta: ${putStrike.targetDelta})`);
  console.log(`Put Reasoning: ${putStrike.reasoning}\n`);
  
  console.log('✅ IMPROVED SYSTEM TEST COMPLETED');
  console.log('🚀 System should now generate more trades with relaxed filters and 0DTE optimizations!');
}

// Run the test
testImprovedSystem();
