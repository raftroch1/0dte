"""
Enhanced Professional 0DTE System with Parameter Optimization
Integrates market-specific parameters and position scaling for target profits
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

from ..optimization.parameter_optimizer import ParameterOptimizer, OptimizedParameters
from .professional_credit_spread_system import (
    Professional0DTESystem, ProfessionalConfig, TradeSignal, SpreadType
)
from ..market_intelligence.intelligence_engine import MarketIntelligenceEngine

class EnhancedProfessionalConfig(ProfessionalConfig):
    """Enhanced configuration with optimization features"""
    
    def __init__(self):
        super().__init__()
        
        # Enhanced features
        self.enable_parameter_optimization = True
        self.enable_position_scaling = True
        self.enable_dynamic_stops = True
        
        # Performance tracking
        self.track_regime_performance = True
        self.adaptive_learning = True
        
        # Enhanced daily limits for scaling
        self.max_daily_profit = 400.0  # Increased for position scaling
        self.max_daily_loss = -500.0   # Adjusted for larger positions
        self.max_concurrent_positions = 6  # Increased for scaling

class EnhancedProfessional0DTESystem(Professional0DTESystem):
    """
    Enhanced Professional 0DTE System with:
    - Market-specific parameter optimization
    - Dynamic position scaling
    - Adaptive risk management
    - Bear market performance improvements
    """
    
    def __init__(self, config: Optional[EnhancedProfessionalConfig] = None):
        # Initialize with enhanced config
        if config is None:
            config = EnhancedProfessionalConfig()
        
        super().__init__(config)
        
        # Initialize optimizer and intelligence engine
        self.optimizer = ParameterOptimizer()
        self.intelligence_engine = MarketIntelligenceEngine()
        
        # Performance tracking
        self.regime_performance = {
            'BULLISH': {'trades': 0, 'wins': 0, 'total_pnl': 0.0},
            'BEARISH': {'trades': 0, 'wins': 0, 'total_pnl': 0.0},
            'NEUTRAL': {'trades': 0, 'wins': 0, 'total_pnl': 0.0}
        }
        
        # Current market state
        self.current_regime = "NEUTRAL"
        self.current_vix = 20.0
        self.regime_confidence = 0.60
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🚀 ENHANCED PROFESSIONAL 0DTE SYSTEM INITIALIZED")
        self.logger.info("   Parameter Optimization: ENABLED")
        self.logger.info("   Position Scaling: ENABLED")
        self.logger.info("   Dynamic Risk Management: ENABLED")
    
    def analyze_market_conditions(self, 
                                options_data: pd.DataFrame,
                                spy_price: float,
                                vix_level: float,
                                historical_prices: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Enhanced market analysis with intelligence engine integration
        """
        
        # Get comprehensive market intelligence
        intelligence = self.intelligence_engine.analyze_market_intelligence(
            options_data=options_data,
            spy_price=spy_price,
            vix_data=None,  # VIX level provided directly
            historical_prices=historical_prices
        )
        
        # Update current market state
        self.current_regime = intelligence.primary_regime
        self.current_vix = vix_level
        self.regime_confidence = intelligence.regime_confidence / 100.0
        
        # Get optimized parameters for current conditions
        optimized_params = self.optimizer.get_optimized_parameters(
            market_regime=self.current_regime,
            vix_level=self.current_vix,
            confidence=self.regime_confidence
        )
        
        return {
            'intelligence': intelligence,
            'optimized_params': optimized_params,
            'market_regime': self.current_regime,
            'vix_level': self.current_vix,
            'confidence': self.regime_confidence
        }
    
    def generate_enhanced_trade_signal(self,
                                     options_data: pd.DataFrame,
                                     spy_price: float,
                                     vix_level: float,
                                     historical_prices: Optional[pd.DataFrame] = None) -> Optional[TradeSignal]:
        """
        Generate trade signal with enhanced optimization
        """
        
        # Analyze market conditions
        market_analysis = self.analyze_market_conditions(
            options_data, spy_price, vix_level, historical_prices
        )
        
        intelligence = market_analysis['intelligence']
        optimized_params = market_analysis['optimized_params']
        
        # Check if we should trade based on optimized thresholds
        if intelligence.regime_confidence < (optimized_params.regime_confidence_threshold * 100):
            self.logger.info(f"🚫 Confidence too low: {intelligence.regime_confidence:.1f}% < {optimized_params.regime_confidence_threshold*100:.1f}%")
            return None
        
        # Determine strategy based on regime and optimized parameters
        spread_type = self._select_optimized_strategy(intelligence.primary_regime, optimized_params)
        
        if spread_type is None:
            return None
        
        # Calculate optimized strikes
        strikes = self._calculate_optimized_strikes(
            spy_price, spread_type, optimized_params, vix_level
        )
        
        if strikes is None:
            return None
        
        short_strike, long_strike = strikes
        
        # Calculate position size with optimization (FIXED: confidence already in 0-1 range)
        contracts = self.optimizer.calculate_position_size(
            base_params=optimized_params,
            signal_confidence=intelligence.regime_confidence / 100.0,  # Convert 40.4% to 0.404
            current_balance=self.current_balance,
            daily_pnl=self.daily_pnl
        )
        
        # Estimate premium and risk (FIXED: Apply 100-share multiplier consistently)
        premium_per_share = self._estimate_premium(short_strike, long_strike, spread_type)
        premium_collected = premium_per_share * 100 * contracts  # FIXED: 100 shares per contract
        max_risk = abs(long_strike - short_strike) * 100 * contracts - premium_collected
        max_profit = premium_collected
        
        # Enhanced confidence calculation
        enhanced_confidence = self._calculate_enhanced_confidence(
            spread_type, intelligence, optimized_params, vix_level
        )
        
        signal = TradeSignal(
            spread_type=spread_type,
            short_strike=short_strike,
            long_strike=long_strike,
            contracts=contracts,
            premium_collected=premium_collected,
            max_risk=max_risk,
            max_profit=max_profit,
            confidence=enhanced_confidence,
            entry_time=datetime.now()
        )
        
        self.logger.info(f"🎯 ENHANCED SIGNAL GENERATED:")
        self.logger.info(f"   Strategy: {spread_type.value}")
        self.logger.info(f"   Contracts: {contracts} (SCALED)")
        self.logger.info(f"   Strikes: {short_strike}/{long_strike}")
        self.logger.info(f"   Premium: ${premium_collected:.2f}")
        self.logger.info(f"   Enhanced Confidence: {enhanced_confidence:.1f}%")
        
        return signal
    
    def _select_optimized_strategy(self, 
                                 regime: str, 
                                 params: OptimizedParameters) -> Optional[SpreadType]:
        """
        Select strategy based on regime and optimized parameters
        """
        
        # Enhanced strategy selection with performance tracking
        regime_perf = self.regime_performance.get(regime, {})
        
        if regime == "BULLISH":
            # In bull markets, prefer bull put spreads
            # But check recent performance
            if regime_perf.get('trades', 0) > 5:
                win_rate = regime_perf.get('wins', 0) / regime_perf.get('trades', 1)
                if win_rate < 0.40:  # Poor recent performance
                    return SpreadType.IRON_CONDOR  # Switch to neutral strategy
            return SpreadType.BULL_PUT_SPREAD
            
        elif regime == "BEARISH":
            # ENHANCED: Better bear market strategy selection
            # Check if bear call spreads have been working
            if regime_perf.get('trades', 0) > 3:
                win_rate = regime_perf.get('wins', 0) / regime_perf.get('trades', 1)
                if win_rate < 0.30:  # Very poor performance
                    # Switch to iron condors with wide strikes
                    return SpreadType.IRON_CONDOR
            return SpreadType.BEAR_CALL_SPREAD
            
        else:  # NEUTRAL
            return SpreadType.IRON_CONDOR
    
    def _calculate_optimized_strikes(self,
                                   spy_price: float,
                                   spread_type: SpreadType,
                                   params: OptimizedParameters,
                                   vix_level: float) -> Optional[tuple]:
        """
        Calculate strikes using optimized parameters
        """
        
        # Get optimized deltas based on spread type
        if spread_type == SpreadType.BULL_PUT_SPREAD:
            target_delta = params.bull_put_delta
        elif spread_type == SpreadType.BEAR_CALL_SPREAD:
            target_delta = params.bear_call_delta
        else:  # IRON_CONDOR
            target_delta = params.iron_condor_delta
        
        # Adjust delta based on volatility
        vol_adjustment = params.volatility_adjustment
        if vix_level > 25:
            # Higher volatility - go further OTM
            adjusted_delta = target_delta * 0.8 * vol_adjustment
        elif vix_level < 15:
            # Lower volatility - can go closer to money
            adjusted_delta = target_delta * 1.2 * vol_adjustment
        else:
            adjusted_delta = target_delta * vol_adjustment
        
        # Calculate strikes based on adjusted delta
        if spread_type == SpreadType.BULL_PUT_SPREAD:
            # Put spread - strikes below current price
            short_strike = spy_price * (1 - adjusted_delta)
            long_strike = short_strike - 2.0  # $2 wide spread
            
        elif spread_type == SpreadType.BEAR_CALL_SPREAD:
            # Call spread - strikes above current price
            short_strike = spy_price * (1 + adjusted_delta)
            long_strike = short_strike + 2.0  # $2 wide spread
            
        else:  # IRON_CONDOR
            # Iron condor - strikes on both sides
            put_short = spy_price * (1 - adjusted_delta)
            put_long = put_short - 2.0
            call_short = spy_price * (1 + adjusted_delta)
            call_long = call_short + 2.0
            
            # For simplicity, return put side (system will handle both sides)
            short_strike = put_short
            long_strike = put_long
        
        # Round to nearest 0.50
        short_strike = round(short_strike * 2) / 2
        long_strike = round(long_strike * 2) / 2
        
        return (short_strike, long_strike)
    
    def _calculate_enhanced_confidence(self,
                                     spread_type: SpreadType,
                                     intelligence: Any,
                                     params: OptimizedParameters,
                                     vix_level: float) -> float:
        """
        Calculate enhanced confidence score
        """
        
        base_confidence = intelligence.regime_confidence
        
        # Adjust based on regime alignment
        if spread_type == SpreadType.BULL_PUT_SPREAD and intelligence.primary_regime == "BULLISH":
            alignment_bonus = 10.0
        elif spread_type == SpreadType.BEAR_CALL_SPREAD and intelligence.primary_regime == "BEARISH":
            alignment_bonus = 10.0
        elif spread_type == SpreadType.IRON_CONDOR and intelligence.primary_regime == "NEUTRAL":
            alignment_bonus = 5.0
        else:
            alignment_bonus = -5.0  # Misalignment penalty
        
        # Adjust based on volatility environment
        if vix_level > 30:
            vol_adjustment = -10.0  # High vol reduces confidence
        elif vix_level < 15:
            vol_adjustment = 5.0   # Low vol increases confidence
        else:
            vol_adjustment = 0.0
        
        # Historical performance adjustment
        regime = intelligence.primary_regime
        if regime in self.regime_performance:
            perf = self.regime_performance[regime]
            if perf['trades'] > 5:
                win_rate = perf['wins'] / perf['trades']
                if win_rate > 0.60:
                    perf_adjustment = 5.0
                elif win_rate < 0.40:
                    perf_adjustment = -10.0
                else:
                    perf_adjustment = 0.0
            else:
                perf_adjustment = 0.0
        else:
            perf_adjustment = 0.0
        
        # Calculate final confidence
        final_confidence = base_confidence + alignment_bonus + vol_adjustment + perf_adjustment
        final_confidence = max(0.0, min(100.0, final_confidence))
        
        return final_confidence
    
    def update_performance_tracking(self, 
                                  regime: str, 
                                  trade_pnl: float, 
                                  was_winner: bool):
        """
        Update performance tracking for adaptive learning
        """
        
        if regime not in self.regime_performance:
            self.regime_performance[regime] = {'trades': 0, 'wins': 0, 'total_pnl': 0.0}
        
        perf = self.regime_performance[regime]
        perf['trades'] += 1
        perf['total_pnl'] += trade_pnl
        
        if was_winner:
            perf['wins'] += 1
        
        # Log performance update
        win_rate = perf['wins'] / perf['trades'] * 100
        avg_pnl = perf['total_pnl'] / perf['trades']
        
        self.logger.info(f"📊 PERFORMANCE UPDATE - {regime}:")
        self.logger.info(f"   Trades: {perf['trades']}")
        self.logger.info(f"   Win Rate: {win_rate:.1f}%")
        self.logger.info(f"   Avg P&L: ${avg_pnl:+.2f}")
    
    def get_dynamic_exit_levels(self, 
                              signal: TradeSignal, 
                              params: OptimizedParameters) -> Dict[str, float]:
        """
        Calculate dynamic exit levels based on optimized parameters
        """
        
        # Dynamic stop loss
        stop_loss = self.optimizer.get_dynamic_stop_loss(
            base_params=params,
            market_regime=self.current_regime,
            vix_level=self.current_vix,
            premium_collected=signal.premium_collected / signal.contracts
        )
        
        # Dynamic profit target
        profit_target = signal.premium_collected * params.profit_target_pct
        
        # Trailing stop
        trailing_stop = signal.premium_collected * params.trailing_stop_pct
        
        return {
            'stop_loss': stop_loss * signal.contracts,
            'profit_target': profit_target,
            'trailing_stop': trailing_stop
        }

def main():
    """Test the enhanced professional system"""
    
    print("🚀 ENHANCED PROFESSIONAL 0DTE SYSTEM TEST")
    print("=" * 60)
    
    # Initialize system
    config = EnhancedProfessionalConfig()
    system = EnhancedProfessional0DTESystem(config)
    
    # Test with sample data
    import numpy as np
    
    # Create sample options data
    strikes = np.arange(460, 480, 1)
    n_strikes = len(strikes)
    
    options_data = pd.DataFrame({
        'strike': np.concatenate([strikes, strikes]),
        'option_type': ['call'] * n_strikes + ['put'] * n_strikes,
        'volume': np.random.randint(100, 1000, n_strikes * 2),
        'open_interest': np.random.randint(1000, 5000, n_strikes * 2),
        'bid': np.random.uniform(0.5, 10.0, n_strikes * 2),
        'ask': np.random.uniform(0.6, 11.0, n_strikes * 2)
    })
    
    # Test different market conditions
    test_conditions = [
        (470.0, 18.5, "Bull Market"),
        (470.0, 28.3, "Bear Market"),
        (470.0, 35.1, "High Vol Bear"),
        (470.0, 12.8, "Low Vol Bull")
    ]
    
    for spy_price, vix, description in test_conditions:
        print(f"\n📊 Testing: {description} (SPY: ${spy_price}, VIX: {vix})")
        
        signal = system.generate_enhanced_trade_signal(
            options_data=options_data,
            spy_price=spy_price,
            vix_level=vix
        )
        
        if signal:
            print(f"   ✅ Signal Generated:")
            print(f"      Strategy: {signal.spread_type.value}")
            print(f"      Contracts: {signal.contracts}")
            print(f"      Premium: ${signal.premium_collected:.2f}")
            print(f"      Confidence: {signal.confidence:.1f}%")
        else:
            print(f"   🚫 No signal generated")

if __name__ == "__main__":
    main()
