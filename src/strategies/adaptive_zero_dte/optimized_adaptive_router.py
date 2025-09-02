#!/usr/bin/env python3
"""
Optimized Adaptive Router
=========================

Enhanced Adaptive Router integrated with Credit Spread Optimizer for professional-grade
$200/day credit spread trading with Kelly Criterion position sizing and advanced risk management.

Following @.cursorrules architecture patterns - extends existing router without breaking changes.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, time, timedelta
import logging
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Import existing Enhanced Adaptive Router
from .enhanced_adaptive_router import EnhancedAdaptiveRouter

# Import Credit Spread Optimizer components
from ..credit_spread_optimizer import (
    CreditSpreadConfig,
    KellyCriterionConfig,
    DEFAULT_CONFIG,
    KELLY_CONFIG,
    KellyPositionSizer,
    ProfitManager,
    get_config_for_account_size,
    validate_config
)

# Import existing components
from ..market_intelligence.intelligence_engine import MarketIntelligenceEngine
from ..real_option_pricing.black_scholes_calculator import BlackScholesCalculator

class OptimizedAdaptiveRouter(EnhancedAdaptiveRouter):
    """
    Professional-grade Enhanced Adaptive Router with Credit Spread Optimization
    
    Extends the existing Enhanced Adaptive Router with:
    - Kelly Criterion position sizing
    - Professional profit management (50% targets, trailing stops)
    - Daily P&L limits and risk controls
    - Time window management
    - Enhanced logging and performance tracking
    
    Maintains full compatibility with existing Enhanced Adaptive Router interface.
    """
    
    def __init__(self, account_balance: float = 25000):
        # Initialize parent Enhanced Adaptive Router
        super().__init__(account_balance)
        
        # Initialize Credit Spread Optimizer components
        self.config = get_config_for_account_size(account_balance)
        self.kelly_config = KELLY_CONFIG
        
        # Validate configuration
        config_errors = validate_config(self.config)
        if config_errors:
            self.logger.error(f"❌ Configuration errors: {config_errors}")
            raise ValueError(f"Invalid configuration: {config_errors}")
        
        # Initialize optimizer components
        self.position_sizer = KellyPositionSizer(self.config, self.kelly_config)
        self.profit_manager = ProfitManager(self.config)
        self.bs_calculator = BlackScholesCalculator()
        
        # Enhanced tracking
        self.daily_pnl = 0.0
        self.daily_trades = []
        self.current_trading_day = None
        self.session_start_balance = account_balance
        
        # Ensure current_balance is available (from parent class)
        if not hasattr(self, 'current_balance'):
            self.current_balance = account_balance
        
        # Override parent's overly restrictive confidence thresholds
        # These are more realistic for 0DTE trading
        self.strategy_thresholds = {
            'high_confidence': 60,      # Reduced from 75
            'medium_confidence': 45,    # Reduced from 60
            'low_confidence': 30,       # Reduced from 45
            'min_intelligence_score': 35  # Reduced from 55
        }
        
        # Performance metrics
        self.total_trades_today = 0
        self.winning_trades_today = 0
        self.daily_profit_target_hit = False
        self.daily_loss_limit_hit = False
        
        self.logger.info("🎯 OPTIMIZED ADAPTIVE ROUTER INITIALIZED")
        self.logger.info(f"   Account Balance: ${account_balance:,.2f}")
        self.logger.info(f"   Daily Profit Target: ${self.config.daily_profit_target:.2f}")
        self.logger.info(f"   Daily Loss Limit: ${self.config.daily_loss_limit:.2f}")
        self.logger.info(f"   Max Risk per Trade: {self.config.max_risk_per_trade_pct*100:.1f}%")
        self.logger.info(f"   Max Concurrent Positions: {self.config.max_concurrent_positions}")
    
    def select_adaptive_strategy(
        self,
        options_data,
        market_data: Dict[str, Any],
        current_time: datetime
    ) -> Dict[str, Any]:
        """
        Enhanced strategy selection with Credit Spread Optimization
        
        Extends parent method with:
        - Daily P&L limit checks
        - Time window enforcement
        - Kelly Criterion position sizing
        - Professional risk management
        """
        
        # Check if we should reset daily tracking
        self._check_daily_reset(current_time)
        
        # Pre-flight checks before strategy selection
        can_trade, reason = self._pre_flight_checks(current_time)
        if not can_trade:
            return {
                'strategy_type': 'NO_TRADE',
                'reason': reason,
                'confidence': 0.0,
                'urgency': 'LOW',
                'market_regime': 'FILTERED_OUT'
            }
        
        # Get base strategy recommendation from parent
        base_recommendation = super().select_adaptive_strategy(
            options_data, market_data, current_time
        )
        
        # If parent says no trade, respect that
        if base_recommendation['strategy_type'] == 'NO_TRADE':
            return base_recommendation
        
        # Enhance recommendation with Credit Spread Optimizer
        enhanced_recommendation = self._enhance_strategy_recommendation(
            base_recommendation, options_data, market_data, current_time
        )
        
        return enhanced_recommendation
    
    def _check_daily_reset(self, current_time: datetime) -> None:
        """Reset daily tracking if new trading day"""
        
        current_date = current_time.date()
        
        if self.current_trading_day != current_date:
            # New trading day - reset daily metrics
            if self.current_trading_day is not None:
                self._log_daily_summary()
            
            self.current_trading_day = current_date
            self.daily_pnl = 0.0
            self.daily_trades = []
            self.total_trades_today = 0
            self.winning_trades_today = 0
            self.daily_profit_target_hit = False  # Reset daily flags
            self.daily_loss_limit_hit = False     # Reset daily flags
            self.session_start_balance = self.current_balance
            
            self.logger.info(f"📅 NEW TRADING DAY: {current_date}")
            self.logger.info(f"   Starting Balance: ${self.session_start_balance:,.2f}")
    
    def _pre_flight_checks(self, current_time: datetime) -> Tuple[bool, str]:
        """
        Comprehensive pre-flight checks before allowing trades
        
        Returns:
            (can_trade, reason)
        """
        
        # 1. Daily P&L limit checks
        if self.daily_pnl <= self.config.daily_loss_limit:
            self.daily_loss_limit_hit = True
            return False, f"Daily loss limit hit: ${self.daily_pnl:.2f} <= ${self.config.daily_loss_limit:.2f}"
        
        # Modified: Allow continued trading after profit target for more opportunities
        # Only stop if we've significantly exceeded target (150% of target)
        profit_stop_threshold = self.config.daily_profit_target * 1.5
        if self.daily_pnl >= profit_stop_threshold:
            self.daily_profit_target_hit = True
            return False, f"Daily profit threshold exceeded: ${self.daily_pnl:.2f} >= ${profit_stop_threshold:.2f}"
        
        # 2. Time window checks
        current_time_only = current_time.time()
        
        if current_time_only < self.config.market_open_time:
            return False, f"Before trading hours: {current_time_only} < {self.config.market_open_time}"
        
        if current_time_only > self.config.market_close_time:
            return False, f"After trading hours: {current_time_only} > {self.config.market_close_time}"
        
        # 3. Position count limits
        active_positions = self.profit_manager.get_position_count()
        if active_positions >= self.config.max_concurrent_positions:
            return False, f"Max positions reached: {active_positions}/{self.config.max_concurrent_positions}"
        
        # 4. Account balance check
        if self.current_balance < 5000:  # Minimum account size
            return False, f"Account balance too low: ${self.current_balance:.2f}"
        
        return True, "All pre-flight checks passed"
    
    def _enhance_strategy_recommendation(
        self,
        base_recommendation: Dict[str, Any],
        options_data,
        market_data: Dict[str, Any],
        current_time: datetime
    ) -> Dict[str, Any]:
        """
        Enhance base recommendation with Credit Spread Optimizer features
        """
        
        strategy_type = base_recommendation['strategy_type']
        
        # Calculate optimal position size using Kelly Criterion
        position_sizing = self._calculate_optimal_position_size(
            strategy_type, options_data, market_data
        )
        
        if not position_sizing['can_trade']:
            return {
                'strategy_type': 'NO_TRADE',
                'reason': position_sizing['reason'],
                'confidence': 0.0,
                'urgency': 'LOW',
                'market_regime': base_recommendation.get('market_regime', 'UNKNOWN')
            }
        
        # Enhance recommendation with optimizer data
        enhanced_recommendation = {
            **base_recommendation,  # Keep all original fields
            
            # Add Credit Spread Optimizer enhancements
            'position_size': position_sizing['recommended_contracts'],
            'max_risk_dollars': position_sizing['max_risk'],
            'kelly_fraction': position_sizing['kelly_fraction'],
            'expected_value': position_sizing['expected_value'],
            'sizing_confidence': position_sizing['confidence'],
            
            # Add risk management parameters
            'profit_target_pct': self.config.profit_target_pct,
            'stop_loss_multiplier': self.config.stop_loss_multiplier,
            
            # Add current status
            'daily_pnl': self.daily_pnl,
            'trades_today': self.total_trades_today,
            'positions_active': self.profit_manager.get_position_count(),
            
            # Enhanced reasoning
            'optimizer_reason': (
                f"Kelly optimal: {position_sizing['recommended_contracts']} contracts "
                f"(${position_sizing['max_risk']:.0f} risk, "
                f"{position_sizing['kelly_fraction']*100:.1f}% Kelly)"
            )
        }
        
        return enhanced_recommendation
    
    def _calculate_optimal_position_size(
        self,
        strategy_type: str,
        options_data,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate optimal position size using Kelly Criterion"""
        
        # Estimate premium and max loss for the strategy
        # This is a simplified calculation - in production, would use actual option pricing
        
        if strategy_type in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD']:
            # Credit spread parameters
            estimated_premium_per_contract = 40.0  # $0.40 premium = $40 per contract
            estimated_max_loss_per_contract = 120.0  # $1.20 max loss = $120 per contract
            
            # Get Kelly recommendation
            recommendation = self.position_sizer.get_position_size_recommendation(
                account_balance=self.current_balance,
                premium_per_contract=estimated_premium_per_contract,
                max_loss_per_contract=estimated_max_loss_per_contract,
                current_positions=self.profit_manager.get_position_count(),
                current_daily_pnl=self.daily_pnl
            )
            
            return recommendation
        
        else:
            # For other strategies, use conservative sizing
            return {
                'can_trade': True,
                'recommended_contracts': 1,
                'max_risk': self.current_balance * 0.01,  # 1% risk
                'kelly_fraction': 0.01,
                'expected_value': 0.0,
                'confidence': 0.5,
                'reason': f"Conservative sizing for {strategy_type}"
            }
    
    def execute_optimized_trade(
        self,
        strategy_recommendation: Dict[str, Any],
        options_data,
        market_data: Dict[str, Any],
        current_time: datetime
    ) -> Dict[str, Any]:
        """
        Execute trade with Credit Spread Optimizer integration
        
        Extends the trade execution with:
        - Kelly Criterion position sizing
        - Profit manager integration
        - Enhanced logging and tracking
        """
        
        strategy_type = strategy_recommendation['strategy_type']
        
        if strategy_type == 'NO_TRADE':
            return {
                'executed': False,
                'reason': strategy_recommendation.get('reason', 'No trade signal'),
                'pnl': 0.0
            }
        
        # Generate unique position ID
        position_id = f"{strategy_type}_{current_time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        # Execute the trade (simplified simulation for now)
        trade_result = self._simulate_trade_execution(
            strategy_recommendation, options_data, market_data, current_time, position_id
        )
        
        if trade_result['executed']:
            # Add position to profit manager
            self._add_position_to_manager(
                position_id, strategy_recommendation, trade_result, current_time
            )
            
            # Update daily tracking
            self._update_daily_tracking(trade_result)
            
            # Add to Kelly position sizer history (for future optimization)
            self.position_sizer.add_trade_result(
                timestamp=current_time,
                strategy_type=strategy_type,
                pnl=trade_result['pnl'],
                premium_collected=trade_result.get('premium_collected', 0.0)
            )
        
        return trade_result
    
    def _simulate_trade_execution(
        self,
        strategy_recommendation: Dict[str, Any],
        options_data,
        market_data: Dict[str, Any],
        current_time: datetime,
        position_id: str
    ) -> Dict[str, Any]:
        """
        Simulate trade execution with realistic P&L calculation
        
        In production, this would interface with actual broker API
        """
        
        strategy_type = strategy_recommendation['strategy_type']
        contracts = strategy_recommendation.get('position_size', 1)
        
        # Simulate realistic trade execution
        if strategy_type in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD']:
            # Credit spread simulation
            premium_per_contract = 40.0  # $0.40 premium
            total_premium = premium_per_contract * contracts
            
            # More realistic win/loss simulation based on strategy type and market conditions
            confidence = strategy_recommendation.get('confidence', 50.0)
            
            # Base win probability on strategy type and confidence
            if strategy_type == 'BULL_PUT_SPREAD':
                # Bull put spreads: higher win rate in bullish markets
                base_win_rate = 0.70 if confidence > 50 else 0.60
            elif strategy_type == 'BEAR_CALL_SPREAD':
                # Bear call spreads: higher win rate in bearish markets  
                base_win_rate = 0.70 if confidence > 50 else 0.60
            else:
                base_win_rate = 0.65
            
            # Adjust for confidence level
            confidence_adjustment = (confidence - 50) / 100 * 0.15  # +/- 15% based on confidence
            win_probability = max(0.45, min(0.80, base_win_rate + confidence_adjustment))
            
            # Simulate trade outcome
            import random
            is_winner = random.random() < win_probability
            
            if is_winner:
                # Profit scenario - close at 50% of max profit
                pnl = total_premium * self.config.profit_target_pct
                exit_reason = "PROFIT_TARGET"
            else:
                # Loss scenario - stop loss at 2x premium
                pnl = -total_premium * self.config.stop_loss_multiplier
                exit_reason = "STOP_LOSS"
            
            return {
                'executed': True,
                'position_id': position_id,
                'strategy_type': strategy_type,
                'contracts': contracts,
                'premium_collected': total_premium,
                'pnl': pnl,
                'exit_reason': exit_reason,
                'win_probability': win_probability,
                'is_winner': is_winner
            }
        
        else:
            # Other strategies - basic simulation
            base_pnl = random.uniform(-50, 100)  # Random P&L for other strategies
            return {
                'executed': True,
                'position_id': position_id,
                'strategy_type': strategy_type,
                'contracts': 1,
                'premium_collected': 0.0,
                'pnl': base_pnl,
                'exit_reason': 'SIMULATED',
                'win_probability': 0.6,
                'is_winner': base_pnl > 0
            }
    
    def _add_position_to_manager(
        self,
        position_id: str,
        strategy_recommendation: Dict[str, Any],
        trade_result: Dict[str, Any],
        current_time: datetime
    ) -> None:
        """Add executed position to profit manager for exit management"""
        
        if trade_result['strategy_type'] in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD']:
            # Add to profit manager for professional exit management
            expiration_time = current_time + timedelta(hours=6)  # 0DTE - 6 hours to expiry
            
            self.profit_manager.add_position(
                position_id=position_id,
                strategy_type=trade_result['strategy_type'],
                entry_time=current_time,
                expiration_date=expiration_time,
                contracts=trade_result['contracts'],
                short_strike=520.0,  # Simplified - would use actual strikes
                long_strike=515.0,   # Simplified - would use actual strikes
                premium_collected=trade_result['premium_collected']
            )
    
    def _update_daily_tracking(self, trade_result: Dict[str, Any]) -> None:
        """Update daily performance tracking"""
        
        pnl = trade_result['pnl']
        self.daily_pnl += pnl
        self.current_balance += pnl
        self.total_trades_today += 1
        
        if trade_result.get('is_winner', False):
            self.winning_trades_today += 1
        
        # Add to daily trades list
        trade_summary = {
            'timestamp': datetime.now(),
            'strategy': trade_result['strategy_type'],
            'contracts': trade_result['contracts'],
            'pnl': pnl,
            'exit_reason': trade_result.get('exit_reason', 'UNKNOWN'),
            'cumulative_daily_pnl': self.daily_pnl
        }
        self.daily_trades.append(trade_summary)
        
        # Log trade execution
        self.logger.info(f"🎯 TRADE EXECUTED: {trade_result['position_id']}")
        self.logger.info(f"   Strategy: {trade_result['strategy_type']}")
        self.logger.info(f"   Contracts: {trade_result['contracts']}")
        self.logger.info(f"   P&L: ${pnl:+.2f}")
        self.logger.info(f"   Daily P&L: ${self.daily_pnl:+.2f}")
        self.logger.info(f"   Balance: ${self.current_balance:,.2f}")
    
    def _log_daily_summary(self) -> None:
        """Log comprehensive daily performance summary"""
        
        if not self.daily_trades:
            return
        
        win_rate = (self.winning_trades_today / self.total_trades_today * 100) if self.total_trades_today > 0 else 0
        avg_pnl = self.daily_pnl / self.total_trades_today if self.total_trades_today > 0 else 0
        
        self.logger.info(f"📊 DAILY SUMMARY: {self.current_trading_day}")
        self.logger.info(f"   Total P&L: ${self.daily_pnl:+.2f}")
        self.logger.info(f"   Total Trades: {self.total_trades_today}")
        self.logger.info(f"   Win Rate: {win_rate:.1f}%")
        self.logger.info(f"   Avg P&L per Trade: ${avg_pnl:+.2f}")
        self.logger.info(f"   Starting Balance: ${self.session_start_balance:,.2f}")
        self.logger.info(f"   Ending Balance: ${self.current_balance:,.2f}")
        
        # Check if targets were met
        if self.daily_pnl >= self.config.daily_profit_target:
            self.logger.info(f"   ✅ PROFIT TARGET ACHIEVED!")
        elif self.daily_pnl <= self.config.daily_loss_limit:
            self.logger.info(f"   ❌ LOSS LIMIT HIT")
        
        self.logger.info(f"=" * 60)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        
        win_rate = (self.winning_trades_today / self.total_trades_today * 100) if self.total_trades_today > 0 else 0
        
        return {
            'current_balance': self.current_balance,
            'daily_pnl': self.daily_pnl,
            'daily_profit_target': self.config.daily_profit_target,
            'daily_loss_limit': self.config.daily_loss_limit,
            'total_trades_today': self.total_trades_today,
            'winning_trades_today': self.winning_trades_today,
            'win_rate': win_rate,
            'active_positions': self.profit_manager.get_position_count(),
            'max_positions': self.config.max_concurrent_positions,
            'profit_target_hit': self.daily_profit_target_hit,
            'loss_limit_hit': self.daily_loss_limit_hit,
            'daily_trades': self.daily_trades
        }

def main():
    """Test the Optimized Adaptive Router"""
    
    print("🎯 TESTING OPTIMIZED ADAPTIVE ROUTER")
    print("=" * 60)
    
    # Initialize router
    router = OptimizedAdaptiveRouter(account_balance=25000.0)
    
    # Test strategy selection
    from datetime import datetime
    import pandas as pd
    
    # Mock options data
    options_data = pd.DataFrame({
        'strike': [520, 525, 530],
        'option_type': ['put', 'call', 'call'],
        'volume': [100, 150, 200]
    })
    
    market_data = {
        'spy_price': 525.0,
        'timestamp': datetime.now()
    }
    
    # Test strategy selection
    strategy_rec = router.select_adaptive_strategy(
        options_data, market_data, datetime.now()
    )
    
    print(f"📊 STRATEGY RECOMMENDATION:")
    for key, value in strategy_rec.items():
        print(f"   {key}: {value}")
    
    # Test trade execution if strategy is recommended
    if strategy_rec['strategy_type'] != 'NO_TRADE':
        trade_result = router.execute_optimized_trade(
            strategy_rec, options_data, market_data, datetime.now()
        )
        
        print(f"\n🎯 TRADE EXECUTION RESULT:")
        for key, value in trade_result.items():
            print(f"   {key}: {value}")
    
    # Get performance summary
    performance = router.get_performance_summary()
    print(f"\n📈 PERFORMANCE SUMMARY:")
    for key, value in performance.items():
        if key != 'daily_trades':  # Skip detailed trades list
            print(f"   {key}: {value}")

if __name__ == "__main__":
    main()
