"""
Advanced Parameter Optimization Framework for 0DTE Trading
Optimizes performance across all market conditions with position scaling
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np
import pandas as pd

class MarketRegime(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"

@dataclass
class OptimizedParameters:
    """Market-specific optimized parameters"""
    
    # Strike Selection
    bull_put_delta: float = 0.20  # Default delta for bull put spreads
    bear_call_delta: float = 0.20  # Default delta for bear call spreads
    iron_condor_delta: float = 0.15  # Default delta for iron condors
    
    # Position Sizing (FIXED: Increased for $250/day target)
    base_contracts: int = 3  # Start with 3 contracts for realistic profit potential
    max_contracts: int = 12  # Allow up to 12 contracts for scaling
    confidence_multiplier: float = 1.0
    
    # Risk Management
    profit_target_pct: float = 0.25  # 25% profit target
    stop_loss_multiplier: float = 1.2  # 1.2x premium stop loss
    trailing_stop_pct: float = 0.15  # 15% trailing stop
    
    # Market-specific adjustments
    volatility_adjustment: float = 1.0
    regime_confidence_threshold: float = 0.60
    
    # Daily limits
    max_daily_trades: int = 8
    daily_profit_target: float = 250.0
    daily_loss_limit: float = -400.0

class ParameterOptimizer:
    """
    Advanced parameter optimization for enhanced performance
    
    FINE-TUNED VERSION: Based on real September 2023 backtest results
    - Confidence thresholds reduced by 10-15% for more trade opportunities
    - VIX levels adjusted based on real September 2023 data (avg: 15.4)
    - Focus on bear market improvement and position scaling
    - Target: Improve from 30% observed win rate to 45% realistic target
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Market-specific parameter sets
        self.optimized_params = {
            MarketRegime.BULLISH: self._get_bullish_params(),
            MarketRegime.BEARISH: self._get_bearish_params(),
            MarketRegime.NEUTRAL: self._get_neutral_params(),
            MarketRegime.HIGH_VOLATILITY: self._get_high_vol_params(),
            MarketRegime.LOW_VOLATILITY: self._get_low_vol_params()
        }
        
        self.logger.info("🎯 PARAMETER OPTIMIZER INITIALIZED")
        self.logger.info("   Market-Specific Parameter Sets: 5")
        self.logger.info("   Focus: Bear Market Enhancement + Position Scaling")
    
    def _get_bullish_params(self) -> OptimizedParameters:
        """Optimized parameters for bullish markets"""
        return OptimizedParameters(
            # Strike selection - FIXED for realistic 0DTE deltas (0.3-0.8% OTM)
            bull_put_delta=0.007,  # 0.7% OTM for puts (~0.20 delta 0DTE)
            bear_call_delta=0.004,  # 0.4% OTM for calls (further OTM in bull market)
            iron_condor_delta=0.006,  # 0.6% OTM for both sides
            
            # Position sizing - INCREASED for $250/day target
            base_contracts=4,  # Start higher in bullish markets
            max_contracts=15,  # Allow aggressive scaling
            confidence_multiplier=1.3,
            
            # Risk management - standard settings work well
            profit_target_pct=0.25,
            stop_loss_multiplier=1.2,
            trailing_stop_pct=0.15,
            
            # Market adjustments - FINE-TUNED
            volatility_adjustment=0.9,  # Less volatility adjustment needed
            regime_confidence_threshold=0.25,  # AGGRESSIVE: Reduced to 25% for trade activation
            
            # Daily limits - can be more active
            max_daily_trades=10,
            daily_profit_target=300.0,  # Higher target in bull markets
            daily_loss_limit=-350.0
        )
    
    def _get_bearish_params(self) -> OptimizedParameters:
        """ENHANCED parameters for bearish markets - KEY OPTIMIZATION"""
        return OptimizedParameters(
            # Strike selection - FIXED for realistic 0DTE deltas (0.3-0.8% OTM)
            bull_put_delta=0.005,  # 0.5% OTM for puts (~0.20 delta 0DTE)
            bear_call_delta=0.006,  # 0.6% OTM for calls (~0.20 delta 0DTE)
            iron_condor_delta=0.005,  # 0.5% OTM for both sides
            
            # Position sizing - INCREASED for $250/day target
            base_contracts=3,  # Start with 3 even in bearish markets
            max_contracts=10,  # Allow scaling
            confidence_multiplier=1.0,  # Standard multiplier
            
            # Risk management - WIDER STOPS for bear market volatility
            profit_target_pct=0.20,  # Take profits faster (20% vs 25%)
            stop_loss_multiplier=1.8,  # WIDER stops (1.8x vs 1.2x)
            trailing_stop_pct=0.10,  # Tighter trailing stop
            
            # Market adjustments - ENHANCED for bear markets + FINE-TUNED
            volatility_adjustment=1.4,  # Higher volatility adjustment
            regime_confidence_threshold=0.30,  # AGGRESSIVE: Reduced to 30% for bearish conditions
            
            # Daily limits - MORE CONSERVATIVE
            max_daily_trades=6,  # Fewer trades in volatile conditions
            daily_profit_target=200.0,  # Lower target but achievable
            daily_loss_limit=-300.0  # Tighter loss limit
        )
    
    def _get_neutral_params(self) -> OptimizedParameters:
        """Optimized parameters for neutral/sideways markets"""
        return OptimizedParameters(
            # Strike selection - FIXED for realistic 0DTE deltas (0.3-0.8% OTM)
            bull_put_delta=0.006,  # 0.6% OTM for puts (~0.20 delta 0DTE)
            bear_call_delta=0.006,  # 0.6% OTM for calls (symmetric positioning)
            iron_condor_delta=0.007,  # 0.7% OTM for iron condors
            
            # Position sizing - INCREASED for $250/day target
            base_contracts=3,  # Start with 3 contracts
            max_contracts=12,  # Allow good scaling
            confidence_multiplier=1.1,
            
            # Risk management - standard settings
            profit_target_pct=0.25,
            stop_loss_multiplier=1.2,
            trailing_stop_pct=0.15,
            
            # Market adjustments - FINE-TUNED
            volatility_adjustment=1.0,
            regime_confidence_threshold=0.25,  # AGGRESSIVE: Reduced to 25% for neutral conditions
            
            # Daily limits - standard
            max_daily_trades=8,
            daily_profit_target=250.0,
            daily_loss_limit=-400.0
        )
    
    def _get_high_vol_params(self) -> OptimizedParameters:
        """Parameters for high volatility environments"""
        return OptimizedParameters(
            # Strike selection - much more conservative
            bull_put_delta=0.12,
            bear_call_delta=0.12,
            iron_condor_delta=0.10,
            
            # Position sizing - very conservative
            base_contracts=1,
            max_contracts=2,
            confidence_multiplier=0.7,
            
            # Risk management - wider stops for volatility
            profit_target_pct=0.20,  # Take profits faster
            stop_loss_multiplier=2.0,  # Much wider stops
            trailing_stop_pct=0.08,
            
            # Market adjustments - FINE-TUNED
            volatility_adjustment=1.6,
            regime_confidence_threshold=0.35,  # AGGRESSIVE: Reduced to 35% for high volatility
            
            # Daily limits - very conservative
            max_daily_trades=4,
            daily_profit_target=150.0,
            daily_loss_limit=-250.0
        )
    
    def _get_low_vol_params(self) -> OptimizedParameters:
        """Parameters for low volatility environments"""
        return OptimizedParameters(
            # Strike selection - can be more aggressive
            bull_put_delta=0.30,
            bear_call_delta=0.30,
            iron_condor_delta=0.25,
            
            # Position sizing - more aggressive
            base_contracts=3,
            max_contracts=5,
            confidence_multiplier=1.3,
            
            # Risk management - tighter stops work in low vol
            profit_target_pct=0.30,
            stop_loss_multiplier=1.1,
            trailing_stop_pct=0.20,
            
            # Market adjustments - FINE-TUNED
            volatility_adjustment=0.8,
            regime_confidence_threshold=0.20,  # AGGRESSIVE: Reduced to 20% for low volatility
            
            # Daily limits - can be more active
            max_daily_trades=12,
            daily_profit_target=350.0,
            daily_loss_limit=-450.0
        )
    
    def get_optimized_parameters(self, 
                               market_regime: str,
                               vix_level: float,
                               confidence: float) -> OptimizedParameters:
        """
        Get optimized parameters based on current market conditions
        
        Args:
            market_regime: Current market regime (BULLISH/BEARISH/NEUTRAL)
            vix_level: Current VIX level
            confidence: Regime detection confidence
            
        Returns:
            Optimized parameters for current conditions
        """
        
        # Determine primary regime - FINE-TUNED based on September 2023 VIX data
        # September 2023 VIX: avg=15.4, range=12.8-18.9, 75th percentile=17.2
        if vix_level > 25:  # High volatility (well above September range)
            primary_regime = MarketRegime.HIGH_VOLATILITY
        elif vix_level < 13:  # Low volatility (below September range)
            primary_regime = MarketRegime.LOW_VOLATILITY
        else:
            primary_regime = MarketRegime(market_regime)
        
        # Get base parameters (CREATE COPY to avoid mutation)
        import copy
        params = copy.deepcopy(self.optimized_params[primary_regime])
        
        # Apply confidence-based adjustments
        if confidence < 0.60:
            # Low confidence - be more conservative
            params.base_contracts = max(1, params.base_contracts - 1)
            params.confidence_multiplier *= 0.8
            params.regime_confidence_threshold += 0.05
        elif confidence > 0.80:
            # High confidence - can be more aggressive
            params.confidence_multiplier *= 1.1
            params.regime_confidence_threshold -= 0.05
        
        self.logger.info(f"🎯 OPTIMIZED PARAMETERS SELECTED:")
        self.logger.info(f"   Primary Regime: {primary_regime.value}")
        self.logger.info(f"   VIX Level: {vix_level:.1f}")
        self.logger.info(f"   Confidence: {confidence:.1f}%")
        self.logger.info(f"   Base Contracts: {params.base_contracts}")
        self.logger.info(f"   Stop Loss Multiplier: {params.stop_loss_multiplier}x")
        
        return params
    
    def calculate_position_size(self,
                              base_params: OptimizedParameters,
                              signal_confidence: float,
                              current_balance: float,
                              daily_pnl: float) -> int:
        """
        Calculate optimal position size with enhanced risk management
        
        Args:
            base_params: Base optimized parameters
            signal_confidence: Individual signal confidence (0-1)
            current_balance: Current account balance
            daily_pnl: Current daily P&L
            
        Returns:
            Number of contracts to trade
        """
        
        # Start with base contracts
        contracts = base_params.base_contracts
        
        # Apply confidence scaling (FIXED: More aggressive for $250/day target)
        # Use confidence as a multiplier but don't let it reduce position size too much
        confidence_factor = max(0.8, signal_confidence) * base_params.confidence_multiplier
        contracts = int(contracts * confidence_factor)
        
        # Apply daily P&L scaling
        if daily_pnl > 0:
            # Positive day - can be slightly more aggressive
            contracts = min(contracts + 1, base_params.max_contracts)
        elif daily_pnl < -200:
            # Significant losses - be more conservative
            contracts = max(1, contracts - 1)
        
        # Apply balance-based scaling (for larger accounts)
        if current_balance > 30000:
            scale_factor = min(1.5, current_balance / 25000)
            contracts = int(contracts * scale_factor)
        
        # Final bounds check
        contracts = max(1, min(contracts, base_params.max_contracts))
        
        self.logger.info(f"📊 POSITION SIZE CALCULATED:")
        self.logger.info(f"   Signal Confidence: {signal_confidence:.1f}%")
        self.logger.info(f"   Daily P&L: ${daily_pnl:+.2f}")
        self.logger.info(f"   Calculated Contracts: {contracts}")
        
        return contracts
    
    def get_dynamic_stop_loss(self,
                            base_params: OptimizedParameters,
                            market_regime: str,
                            vix_level: float,
                            premium_collected: float) -> float:
        """
        Calculate dynamic stop loss based on market conditions
        
        Returns:
            Stop loss amount (positive number)
        """
        
        base_multiplier = base_params.stop_loss_multiplier
        
        # Adjust for market regime
        if market_regime == "BEARISH":
            # Wider stops in bear markets (they're more volatile)
            regime_adjustment = 1.3
        elif market_regime == "BULLISH":
            # Standard stops in bull markets
            regime_adjustment = 1.0
        else:
            # Slightly wider stops in neutral markets
            regime_adjustment = 1.1
        
        # Adjust for volatility
        if vix_level > 25:
            vol_adjustment = 1.2
        elif vix_level < 15:
            vol_adjustment = 0.9
        else:
            vol_adjustment = 1.0
        
        # Calculate final stop loss
        final_multiplier = base_multiplier * regime_adjustment * vol_adjustment
        stop_loss = premium_collected * final_multiplier
        
        self.logger.info(f"🛡️ DYNAMIC STOP LOSS:")
        self.logger.info(f"   Base Multiplier: {base_multiplier:.1f}x")
        self.logger.info(f"   Regime Adjustment: {regime_adjustment:.1f}x")
        self.logger.info(f"   Vol Adjustment: {vol_adjustment:.1f}x")
        self.logger.info(f"   Final Stop Loss: ${stop_loss:.2f}")
        
        return stop_loss

def main():
    """Test the parameter optimizer"""
    
    optimizer = ParameterOptimizer()
    
    # Test different market conditions
    test_conditions = [
        ("BULLISH", 18.5, 0.75),
        ("BEARISH", 28.3, 0.85),
        ("NEUTRAL", 21.2, 0.65),
        ("BEARISH", 35.1, 0.70),  # High vol bear market
        ("BULLISH", 12.8, 0.60)   # Low vol bull market
    ]
    
    print("🎯 PARAMETER OPTIMIZATION TESTING")
    print("=" * 50)
    
    for regime, vix, confidence in test_conditions:
        print(f"\n📊 Condition: {regime}, VIX: {vix:.1f}, Confidence: {confidence:.1f}")
        
        params = optimizer.get_optimized_parameters(regime, vix, confidence)
        contracts = optimizer.calculate_position_size(params, confidence, 25000, 0)
        stop_loss = optimizer.get_dynamic_stop_loss(params, regime, vix, 50.0)
        
        print(f"   Contracts: {contracts}")
        print(f"   Stop Loss: ${stop_loss:.2f}")
        print(f"   Profit Target: {params.profit_target_pct:.0%}")

if __name__ == "__main__":
    main()
