#!/usr/bin/env python3
"""
Hybrid Adaptive Strategy Selector - Dynamic Strategy Selection
============================================================

INTELLIGENT STRATEGY SELECTION:
1. Credit Spreads: When cash available + neutral markets
2. Option Buying: When strong momentum + cash constrained
3. No Trade: When conditions unfavorable

This solves our multi-scenario failure by providing MORE tools, not fewer.

Location: src/strategies/hybrid_adaptive/ (following .cursorrules structure)
Author: Advanced Options Trading System - Hybrid Strategy Selection
"""

import sys
import os
# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Import our cash manager
try:
    from src.strategies.cash_management.position_sizer import ConservativeCashManager
except ImportError:
    from cash_management.position_sizer import ConservativeCashManager

@dataclass
class MarketConditions:
    """Current market condition analysis"""
    regime: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    regime_confidence: float  # 0-100
    volatility_level: str  # 'LOW', 'MEDIUM', 'HIGH'
    momentum_strength: str  # 'STRONG', 'WEAK', 'MIXED'
    trend_direction: str  # 'UP', 'DOWN', 'SIDEWAYS'
    rsi: float
    vix_level: Optional[float] = None

@dataclass
class StrategyRecommendation:
    """Strategy recommendation with reasoning"""
    strategy_type: str  # 'CREDIT_SPREAD', 'BUY_OPTION', 'NO_TRADE'
    specific_strategy: str  # 'BULL_PUT_SPREAD', 'BUY_CALL', etc.
    confidence: float  # 0-100
    position_size: int  # Number of contracts
    reasoning: List[str]
    cash_required: float
    max_profit: float
    max_loss: float
    probability_of_profit: float

class HybridAdaptiveSelector:
    """
    Dynamic strategy selector that chooses between:
    1. Credit Spreads (when cash allows + neutral markets)
    2. Option Buying (when strong momentum + cash constrained)
    3. No Trade (when conditions unfavorable)
    """
    
    def __init__(self, account_balance: float = 25000):
        self.cash_manager = ConservativeCashManager(account_balance)
        
        # Strategy thresholds
        self.min_cash_for_spreads = 2000  # Need $2K+ for credit spreads
        self.strong_momentum_threshold = 0.7  # 70% confidence for momentum
        self.high_volatility_threshold = 35  # VIX > 35 = high vol
        self.neutral_rsi_range = (40, 60)  # RSI 40-60 = neutral
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"🎯 HYBRID ADAPTIVE SELECTOR INITIALIZED")
        self.logger.info(f"   Account Balance: ${account_balance:,.2f}")
        self.logger.info(f"   Min Cash for Spreads: ${self.min_cash_for_spreads:,.2f}")
    
    def analyze_market_conditions(self, options_data: pd.DataFrame) -> MarketConditions:
        """
        Analyze current market conditions from options data
        
        This is a simplified version - in production, would use more sophisticated analysis
        """
        
        if options_data.empty:
            return MarketConditions(
                regime='NEUTRAL',
                regime_confidence=30,
                volatility_level='MEDIUM',
                momentum_strength='WEAK',
                trend_direction='SIDEWAYS',
                rsi=50.0
            )
        
        # Estimate current price from options data
        current_price = self._estimate_current_price(options_data)
        
        # Simple regime detection based on put/call ratio and price action
        puts = options_data[options_data['option_type'] == 'put']
        calls = options_data[options_data['option_type'] == 'call']
        
        put_call_ratio = len(puts) / max(len(calls), 1)
        
        # Simple momentum from moneyness distribution (available in our data)
        if 'moneyness' in options_data.columns and len(options_data) > 10:
            # Analyze moneyness distribution to infer market sentiment
            avg_moneyness = options_data['moneyness'].mean()
            moneyness_std = options_data['moneyness'].std()
            
            # Strong momentum if options are heavily skewed
            if abs(avg_moneyness) > 0.02:  # 2% average moneyness
                momentum_strength = 'STRONG'
                trend_direction = 'UP' if avg_moneyness > 0 else 'DOWN'
            elif moneyness_std > 0.05:  # High volatility in moneyness
                momentum_strength = 'MIXED'
                trend_direction = 'SIDEWAYS'
            else:
                momentum_strength = 'WEAK'
                trend_direction = 'SIDEWAYS'
        else:
            momentum_strength = 'WEAK'
            trend_direction = 'SIDEWAYS'
        
        # Regime detection
        if put_call_ratio > 1.3:  # More puts = bearish
            regime = 'BEARISH'
            regime_confidence = 70
        elif put_call_ratio < 0.8:  # More calls = bullish
            regime = 'BULLISH'
            regime_confidence = 70
        else:
            regime = 'NEUTRAL'
            regime_confidence = 60
        
        # Volatility estimation (simplified)
        if len(options_data) > 0:
            avg_volume = options_data['volume'].mean() if 'volume' in options_data.columns else 100
            volatility_level = 'HIGH' if avg_volume > 500 else 'LOW' if avg_volume < 50 else 'MEDIUM'
        else:
            volatility_level = 'MEDIUM'
        
        # Estimate RSI (simplified)
        rsi = 50.0  # Default neutral
        if regime == 'BULLISH':
            rsi = 65.0
        elif regime == 'BEARISH':
            rsi = 35.0
        
        return MarketConditions(
            regime=regime,
            regime_confidence=regime_confidence,
            volatility_level=volatility_level,
            momentum_strength=momentum_strength,
            trend_direction=trend_direction,
            rsi=rsi
        )
    
    def select_optimal_strategy(
        self, 
        options_data: pd.DataFrame,
        market_conditions: Optional[MarketConditions] = None
    ) -> StrategyRecommendation:
        """
        Select optimal strategy based on market conditions and cash constraints
        
        Decision Tree:
        1. Check available cash
        2. Analyze market conditions  
        3. Select best strategy type
        4. Calculate position size
        5. Provide recommendation
        """
        
        if market_conditions is None:
            market_conditions = self.analyze_market_conditions(options_data)
        
        available_cash = self.cash_manager.calculate_available_cash()
        current_price = self._estimate_current_price(options_data)
        
        reasoning = []
        reasoning.append(f"Market Regime: {market_conditions.regime} ({market_conditions.regime_confidence}% confidence)")
        reasoning.append(f"Available Cash: ${available_cash:,.2f}")
        reasoning.append(f"Volatility: {market_conditions.volatility_level}")
        reasoning.append(f"Momentum: {market_conditions.momentum_strength}")
        
        self.logger.info(f"🎯 STRATEGY SELECTION ANALYSIS:")
        self.logger.info(f"   Market: {market_conditions.regime} ({market_conditions.regime_confidence}%)")
        self.logger.info(f"   Cash: ${available_cash:,.2f}")
        self.logger.info(f"   Volatility: {market_conditions.volatility_level}")
        self.logger.info(f"   Momentum: {market_conditions.momentum_strength}")
        
        # DECISION TREE: Strategy Selection
        
        # Option 1: Credit Spreads (Preferred when conditions allow)
        if (available_cash >= self.min_cash_for_spreads and 
            market_conditions.volatility_level != 'HIGH' and
            market_conditions.regime_confidence >= 60):
            
            return self._recommend_credit_spread(
                market_conditions, options_data, current_price, reasoning
            )
        
        # Option 2: Buy Options (When strong momentum or cash constrained)
        elif (market_conditions.momentum_strength == 'STRONG' or
              market_conditions.regime_confidence >= 70 or
              available_cash < self.min_cash_for_spreads):
            
            return self._recommend_option_buying(
                market_conditions, options_data, current_price, reasoning
            )
        
        # Option 3: No Trade (Unfavorable conditions)
        else:
            reasoning.append("No favorable conditions for either credit spreads or option buying")
            return StrategyRecommendation(
                strategy_type='NO_TRADE',
                specific_strategy='NO_TRADE',
                confidence=0,
                position_size=0,
                reasoning=reasoning,
                cash_required=0,
                max_profit=0,
                max_loss=0,
                probability_of_profit=0
            )
    
    def _recommend_credit_spread(
        self, 
        conditions: MarketConditions,
        options_data: pd.DataFrame,
        current_price: float,
        reasoning: List[str]
    ) -> StrategyRecommendation:
        """Recommend specific credit spread strategy"""
        
        reasoning.append("✅ Cash available for credit spreads")
        
        # Select spread type based on market regime
        if conditions.regime == 'BULLISH' or (conditions.regime == 'NEUTRAL' and conditions.rsi < 50):
            strategy = 'BULL_PUT_SPREAD'
            reasoning.append("📈 Bull Put Spread: Bullish/neutral bias")
            
            # Conservative parameters for $25K account
            spread_width = 2.0
            target_credit = 0.40
            short_strike = current_price * 0.98  # 2% OTM
            
        elif conditions.regime == 'BEARISH' or (conditions.regime == 'NEUTRAL' and conditions.rsi > 50):
            strategy = 'BEAR_CALL_SPREAD'
            reasoning.append("📉 Bear Call Spread: Bearish/neutral bias")
            
            spread_width = 2.0
            target_credit = 0.35
            short_strike = current_price * 1.02  # 2% OTM
            
        else:  # Neutral market
            strategy = 'IRON_CONDOR'
            reasoning.append("🦅 Iron Condor: Neutral market")
            
            spread_width = 2.0
            target_credit = 0.60
            short_strike = current_price  # ATM
        
        # Check position sizing
        cash_result = self.cash_manager.can_open_position(strategy, spread_width, target_credit, 1)
        
        if not cash_result.can_trade:
            reasoning.append(f"❌ Cannot open {strategy}: {cash_result.reason}")
            return self._recommend_option_buying(conditions, options_data, current_price, reasoning)
        
        # Calculate expected metrics
        max_profit = target_credit * 100
        max_loss = (spread_width - target_credit) * 100
        prob_profit = self._estimate_probability_of_profit(strategy, conditions)
        
        reasoning.append(f"💰 Max Profit: ${max_profit:.2f}, Max Loss: ${max_loss:.2f}")
        reasoning.append(f"📊 Estimated PoP: {prob_profit:.1%}")
        
        return StrategyRecommendation(
            strategy_type='CREDIT_SPREAD',
            specific_strategy=strategy,
            confidence=min(85, conditions.regime_confidence + 10),
            position_size=cash_result.max_contracts,
            reasoning=reasoning,
            cash_required=cash_result.cash_required,
            max_profit=max_profit,
            max_loss=max_loss,
            probability_of_profit=prob_profit
        )
    
    def _recommend_option_buying(
        self,
        conditions: MarketConditions,
        options_data: pd.DataFrame,
        current_price: float,
        reasoning: List[str]
    ) -> StrategyRecommendation:
        """Recommend option buying strategy"""
        
        reasoning.append("🎯 Option buying selected")
        
        # Select option type based on market conditions
        if conditions.regime == 'BULLISH' or conditions.trend_direction == 'UP':
            strategy = 'BUY_CALL'
            reasoning.append("📈 Buy Call: Bullish momentum")
            target_strike = current_price * 1.01  # 1% OTM
            
        elif conditions.regime == 'BEARISH' or conditions.trend_direction == 'DOWN':
            strategy = 'BUY_PUT'
            reasoning.append("📉 Buy Put: Bearish momentum")
            target_strike = current_price * 0.99  # 1% OTM
            
        else:
            # Neutral - pick based on RSI
            if conditions.rsi < 40:
                strategy = 'BUY_CALL'
                reasoning.append("📈 Buy Call: RSI oversold")
                target_strike = current_price * 1.005
            else:
                strategy = 'BUY_PUT'
                reasoning.append("📉 Buy Put: RSI overbought")
                target_strike = current_price * 0.995
        
        # Conservative position sizing for option buying
        available_cash = self.cash_manager.calculate_available_cash()
        max_risk_per_trade = self.cash_manager.account_balance * 0.008  # 0.8% risk
        
        # Estimate option premium (simplified)
        estimated_premium = current_price * 0.01  # ~1% of underlying price
        max_contracts = min(
            int(max_risk_per_trade / (estimated_premium * 100)),
            int(available_cash / (estimated_premium * 100 * 1.1))  # 10% buffer
        )
        max_contracts = max(1, min(max_contracts, 5))  # 1-5 contracts max
        
        cash_required = estimated_premium * 100 * max_contracts
        max_loss = cash_required  # Premium paid
        max_profit = cash_required * 3  # Target 3:1 reward:risk
        prob_profit = self._estimate_probability_of_profit(strategy, conditions)
        
        reasoning.append(f"💰 Premium Est: ${estimated_premium:.2f}, Contracts: {max_contracts}")
        reasoning.append(f"📊 Risk: ${max_loss:.2f}, Target: ${max_profit:.2f}")
        reasoning.append(f"📊 Estimated PoP: {prob_profit:.1%}")
        
        return StrategyRecommendation(
            strategy_type='BUY_OPTION',
            specific_strategy=strategy,
            confidence=conditions.regime_confidence,
            position_size=max_contracts,
            reasoning=reasoning,
            cash_required=cash_required,
            max_profit=max_profit,
            max_loss=max_loss,
            probability_of_profit=prob_profit
        )
    
    def _estimate_current_price(self, options_data: pd.DataFrame) -> float:
        """Estimate current underlying price from options data"""
        if options_data.empty:
            return 640.0  # Default SPY price
        
        # Use the same logic as ParquetDataLoader for consistency
        if 'strike' in options_data.columns and 'moneyness' in options_data.columns:
            # Find ATM options (moneyness closest to 0)
            atm_options = options_data[abs(options_data['moneyness']) < 0.02]  # Within 2%
            
            if not atm_options.empty:
                # Use the strike of the most ATM option
                closest_atm = atm_options.loc[abs(atm_options['moneyness']).idxmin()]
                estimated_price = closest_atm['strike'] / (1 + closest_atm['moneyness'])
                return float(estimated_price)
        
        # Fallback: use median strike as approximation
        if 'strike' in options_data.columns:
            strikes = options_data['strike'].values
            return float(np.median(strikes))
        
        # Last resort - return default
        return 640.0
    
    def _estimate_probability_of_profit(self, strategy: str, conditions: MarketConditions) -> float:
        """Estimate probability of profit for strategy"""
        
        base_prob = 0.5  # 50% base probability
        
        # Adjust based on strategy type
        if strategy in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD']:
            base_prob = 0.65  # Credit spreads have higher PoP
        elif strategy == 'IRON_CONDOR':
            base_prob = 0.70  # Iron condors have highest PoP in neutral markets
        elif strategy in ['BUY_CALL', 'BUY_PUT']:
            base_prob = 0.40  # Option buying has lower PoP but higher reward
        
        # Adjust based on market conditions
        if conditions.regime_confidence > 70:
            base_prob += 0.10  # High confidence adds to PoP
        elif conditions.regime_confidence < 50:
            base_prob -= 0.10  # Low confidence reduces PoP
        
        if conditions.momentum_strength == 'STRONG':
            base_prob += 0.05
        elif conditions.momentum_strength == 'WEAK':
            base_prob -= 0.05
        
        return max(0.1, min(0.9, base_prob))

def main():
    """Test the hybrid strategy selector"""
    
    print("🎯 TESTING HYBRID ADAPTIVE STRATEGY SELECTOR")
    print("=" * 70)
    
    # Initialize selector
    selector = HybridAdaptiveSelector(25000)
    
    # Create sample options data
    sample_data = pd.DataFrame({
        'strike': [630, 635, 640, 645, 650],
        'option_type': ['put', 'put', 'call', 'call', 'call'],
        'volume': [100, 150, 200, 120, 80],
        'underlying_price': [640.0] * 5,
        'spy_price': [640.0] * 5
    })
    
    # Test strategy selection
    print(f"\n📊 ANALYZING MARKET CONDITIONS:")
    conditions = selector.analyze_market_conditions(sample_data)
    print(f"   Regime: {conditions.regime} ({conditions.regime_confidence}%)")
    print(f"   Volatility: {conditions.volatility_level}")
    print(f"   Momentum: {conditions.momentum_strength}")
    
    print(f"\n🎯 STRATEGY RECOMMENDATION:")
    recommendation = selector.select_optimal_strategy(sample_data, conditions)
    print(f"   Strategy: {recommendation.specific_strategy}")
    print(f"   Confidence: {recommendation.confidence}%")
    print(f"   Position Size: {recommendation.position_size} contracts")
    print(f"   Cash Required: ${recommendation.cash_required:.2f}")
    print(f"   Max Profit: ${recommendation.max_profit:.2f}")
    print(f"   Max Loss: ${recommendation.max_loss:.2f}")
    print(f"   Prob of Profit: {recommendation.probability_of_profit:.1%}")
    
    print(f"\n📋 REASONING:")
    for reason in recommendation.reasoning:
        print(f"   • {reason}")

if __name__ == "__main__":
    main()
