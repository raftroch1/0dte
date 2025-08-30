
import { Strategy, TechnicalIndicators } from './types';

export interface ExitCondition {
  shouldExit: boolean;
  reason: 'STOP_LOSS' | 'TAKE_PROFIT' | 'EXPIRATION' | 'SIGNAL_EXIT' | 'TIME_DECAY' | 'CIRCUIT_BREAKER';
}

export class StrategyEngine {
  
  /**
   * FIX: Enhanced exit logic optimized for 0DTE options trading
   * Added time-based exits and circuit breakers for same-day expiration
   */
  static shouldExit(
    currentPrice: number,
    entryPrice: number,
    strategy: Strategy,
    indicators: TechnicalIndicators,
    side: 'CALL' | 'PUT',
    entryTime?: Date,
    currentTime?: Date
  ): ExitCondition {
    
    // Calculate P&L percentage
    const pnlPercent = ((currentPrice - entryPrice) / entryPrice) * 100;
    
    // FIX: 0DTE Time-based exit logic (4 hours max holding period)
    if (entryTime && currentTime) {
      const holdingTimeHours = (currentTime.getTime() - entryTime.getTime()) / (1000 * 60 * 60);
      
      // Force exit after 4 hours for 0DTE
      if (holdingTimeHours >= 4) {
        return { shouldExit: true, reason: 'TIME_DECAY' };
      }
      
      // Force exit 30 minutes before market close for 0DTE
      const marketCloseHour = 16; // 4 PM ET
      const currentHour = currentTime.getHours() + currentTime.getMinutes() / 60;
      if (currentHour >= 15.5) { // 3:30 PM ET
        return { shouldExit: true, reason: 'EXPIRATION' };
      }
    }
    
    // FIX: More aggressive take profit for 0DTE (faster moves)
    const takeProfitThreshold = strategy.takeProfitPercent || 50; // Default 50% for 0DTE
    if (pnlPercent >= takeProfitThreshold) {
      return { shouldExit: true, reason: 'TAKE_PROFIT' };
    }
    
    // FIX: Tighter stop loss for 0DTE (preserve capital)
    const stopLossThreshold = -(strategy.stopLossPercent || 30); // Default -30% for 0DTE
    if (pnlPercent <= stopLossThreshold) {
      return { shouldExit: true, reason: 'STOP_LOSS' };
    }
    
    // FIX: Circuit breaker for extreme losses (risk management)
    if (pnlPercent <= -75) { // Emergency exit at -75%
      return { shouldExit: true, reason: 'CIRCUIT_BREAKER' };
    }
    
    // FIX: Enhanced signal-based exit conditions for 0DTE
    if (side === 'CALL') {
      // Exit long calls if RSI becomes extremely overbought OR momentum reverses
      if (indicators.rsi > 80 || (indicators.macd < indicators.macdSignal && indicators.rsi > 60)) {
        return { shouldExit: true, reason: 'SIGNAL_EXIT' };
      }
    } else if (side === 'PUT') {
      // Exit long puts if RSI becomes extremely oversold OR momentum reverses
      if (indicators.rsi < 20 || (indicators.macd > indicators.macdSignal && indicators.rsi < 40)) {
        return { shouldExit: true, reason: 'SIGNAL_EXIT' };
      }
    }
    
    return { shouldExit: false, reason: 'STOP_LOSS' };
  }
  
  /**
   * FIX: Enhanced position sizing optimized for $35k account and $200-250 daily target
   * Calculates position size based on 0DTE risk parameters and daily profit goals
   */
  static calculatePositionSize(
    accountBalance: number,
    strategy: Strategy,
    currentPrice: number,
    volatility: number = 0.25,
    dailyProfitTarget: number = 225 // $225 average target
  ): number {
    
    // FIX: 0DTE position sizing for $35k account targeting $200-250 daily
    const maxDailyRisk = accountBalance * 0.02; // 2% max daily risk ($700 on $35k)
    const targetRisk = Math.min(maxDailyRisk, dailyProfitTarget * 1.5); // Risk 1.5x profit target
    
    // Calculate position size based on option premium and stop loss
    const stopLossPercent = strategy.stopLossPercent || 30; // 30% stop loss for 0DTE
    const maxLossPerContract = currentPrice * (stopLossPercent / 100) * 100; // $100 per point for SPY
    
    // Position size to limit total risk
    const maxContracts = Math.floor(targetRisk / maxLossPerContract);
    
    // FIX: Volatility-based position sizing for 0DTE
    // Higher volatility = smaller position size
    const volatilityAdjustment = Math.max(0.3, Math.min(1.2, 0.8 / volatility));
    const adjustedSize = Math.floor(maxContracts * volatilityAdjustment);
    
    // FIX: Ensure reasonable bounds for 0DTE trading
    // Minimum 1 contract, maximum 10 contracts for risk management
    const finalSize = Math.max(1, Math.min(adjustedSize, 10));
    
    console.log(`💰 POSITION SIZING: Account: $${accountBalance.toFixed(0)}, Risk: $${targetRisk.toFixed(0)}, Contracts: ${finalSize}`);
    
    return finalSize;
  }
  
  /**
   * FIX: NEW - Calculate daily P&L and check if daily target/limit reached
   * Essential for 0DTE trading to manage daily risk and profit targets
   */
  static checkDailyLimits(
    currentDailyPnL: number,
    dailyProfitTarget: number = 225,
    dailyLossLimit: number = -500
  ): { shouldStop: boolean; reason: string } {
    
    // Check if daily profit target reached
    if (currentDailyPnL >= dailyProfitTarget) {
      return { 
        shouldStop: true, 
        reason: `Daily profit target reached: $${currentDailyPnL.toFixed(2)} >= $${dailyProfitTarget}` 
      };
    }
    
    // Check if daily loss limit reached
    if (currentDailyPnL <= dailyLossLimit) {
      return { 
        shouldStop: true, 
        reason: `Daily loss limit reached: $${currentDailyPnL.toFixed(2)} <= $${dailyLossLimit}` 
      };
    }
    
    return { shouldStop: false, reason: 'Within daily limits' };
  }
  
  /**
   * FIX: NEW - Check if same-day expiration (0DTE) logic should apply
   * Determines if options expire today and adjusts strategy accordingly
   */
  static is0DTE(expirationDate: Date, currentDate: Date = new Date()): boolean {
    const expiry = new Date(expirationDate);
    const today = new Date(currentDate);
    
    // Check if expiration is today
    return expiry.toDateString() === today.toDateString();
  }
  
  /**
   * FIX: NEW - Get optimal strike selection for 0DTE based on delta and time
   * Helps select the best strike prices for 0DTE momentum trading
   */
  static getOptimal0DTEStrike(
    currentPrice: number,
    side: 'CALL' | 'PUT',
    timeWindow: string,
    volatility: number
  ): { strikeOffset: number; targetDelta: number; reasoning: string } {
    
    let strikeOffset = 0;
    let targetDelta = 0.5;
    let reasoning = '';
    
    if (timeWindow === 'MORNING_MOMENTUM') {
      // Morning: Use closer to ATM for momentum capture
      if (side === 'CALL') {
        strikeOffset = currentPrice * 0.002; // 0.2% OTM
        targetDelta = 0.45;
        reasoning = 'Morning momentum - slightly OTM call';
      } else {
        strikeOffset = -currentPrice * 0.002; // 0.2% OTM
        targetDelta = -0.45;
        reasoning = 'Morning momentum - slightly OTM put';
      }
    } else if (timeWindow === 'AFTERNOON_DECAY') {
      // Afternoon: Use further OTM for decay strategies
      if (side === 'CALL') {
        strikeOffset = currentPrice * 0.005; // 0.5% OTM
        targetDelta = 0.35;
        reasoning = 'Afternoon decay - further OTM call';
      } else {
        strikeOffset = -currentPrice * 0.005; // 0.5% OTM
        targetDelta = -0.35;
        reasoning = 'Afternoon decay - further OTM put';
      }
    } else {
      // Midday: Conservative ATM approach
      strikeOffset = 0;
      targetDelta = side === 'CALL' ? 0.5 : -0.5;
      reasoning = 'Midday consolidation - ATM option';
    }
    
    return { strikeOffset, targetDelta, reasoning };
  }
}

export default StrategyEngine;
