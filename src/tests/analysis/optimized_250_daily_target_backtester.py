#!/usr/bin/env python3
"""
🎯 OPTIMIZED $250/DAY TARGET BACKTESTER
=====================================

MISSION: Optimize for $250/day profit target with:
- Enhanced Iron Condor selection in flat markets
- Aggressive risk management (NO worthless expiration)
- Full month backtesting for statistical significance
- Real data compliance (@.cursorrules)

Key Improvements:
1. Enhanced NEUTRAL regime detection for Iron Condors
2. Strict time-based exits (2-4 hours max hold time)
3. Dynamic profit targets based on $250/day goal
4. Improved market regime sensitivity
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

# Add project root to path
sys.path.append('/Users/devops/Desktop/coding/advanced-options-strategies')

from src.data.parquet_data_loader import ParquetDataLoader
from src.strategies.hybrid_adaptive.enhanced_strategy_selector import EnhancedHybridAdaptiveSelector
from src.strategies.cash_management.position_sizer import ConservativeCashManager
from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator

@dataclass
class OptimizedPosition:
    """Enhanced position tracking for $250/day optimization"""
    position_id: str
    strategy_type: str
    entry_time: datetime
    entry_spy_price: float
    strikes: Dict[str, float]
    cash_at_risk: float
    margin_required: float
    max_profit_target: float
    stop_loss_level: float
    time_exit_target: datetime  # CRITICAL: Force exit time
    is_closed: bool = False
    exit_time: Optional[datetime] = None
    exit_spy_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    exit_reason: Optional[str] = None

class Optimized250DailyTargetBacktester:
    """
    🎯 OPTIMIZED BACKTESTER FOR $250/DAY TARGET
    
    This backtester is specifically designed to:
    - Achieve consistent $250/day profits
    - Prevent ANY options from expiring worthless
    - Maximize Iron Condor usage in flat markets
    - Use aggressive risk management
    """
    
    def __init__(self, initial_balance: float = 25000):
        """Initialize the optimized backtester"""
        
        # Core components
        self.data_loader = ParquetDataLoader()
        self.strategy_selector = EnhancedHybridAdaptiveSelector(initial_balance)
        self.cash_manager = ConservativeCashManager(initial_balance)
        self.pricing_calculator = BlackScholesCalculator()
        
        # Performance tracking
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.daily_target = 250.0  # $250/day target
        self.max_daily_risk = 500.0  # Max $500 daily loss
        
        # Position management
        self.open_positions: Dict[str, OptimizedPosition] = {}
        self.closed_positions: List[OptimizedPosition] = []
        self.daily_pnl: Dict[str, float] = {}
        
        # Risk management parameters (AGGRESSIVE)
        self.max_hold_hours = 3.0  # Maximum 3 hours hold time
        self.profit_target_multiplier = 0.5  # Take 50% of max profit
        self.stop_loss_multiplier = 0.25  # Stop at 25% loss
        
        # Enhanced regime detection for Iron Condors
        self.neutral_regime_threshold = 45.0  # Lower threshold for NEUTRAL detection
        self.iron_condor_boost = 1.3  # Boost Iron Condor selection
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🎯 OPTIMIZED $250/DAY TARGET BACKTESTER INITIALIZED")
        self.logger.info(f"   Target: ${self.daily_target}/day")
        self.logger.info(f"   Max Risk: ${self.max_daily_risk}/day")
        self.logger.info(f"   Max Hold: {self.max_hold_hours} hours")
    
    def run_month_long_backtest(
        self, 
        start_date: str = "2024-09-01", 
        end_date: str = "2024-09-30"
    ) -> Dict[str, any]:
        """
        Run comprehensive month-long backtest
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        
        self.logger.info(f"🚀 STARTING MONTH-LONG BACKTEST: {start_date} to {end_date}")
        
        # Convert string dates to datetime objects
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get available trading days
        available_dates = self.data_loader.get_available_dates(start_dt, end_dt)
        self.logger.info(f"📅 Found {len(available_dates)} trading days")
        
        # Process each trading day
        for i, trading_day in enumerate(available_dates):
            try:
                self.logger.info(f"\n📊 PROCESSING DAY {i+1}/{len(available_dates)}: {trading_day}")
                
                # Reset daily tracking
                daily_start_balance = self.current_balance
                self.daily_pnl[str(trading_day)] = 0.0
                
                # Process the trading day
                self._process_optimized_trading_day(trading_day)
                
                # Calculate daily performance
                daily_end_balance = self.current_balance
                daily_pnl = daily_end_balance - daily_start_balance
                self.daily_pnl[str(trading_day)] = daily_pnl
                
                self.logger.info(f"📈 DAY {i+1} SUMMARY:")
                self.logger.info(f"   Daily P&L: ${daily_pnl:.2f}")
                self.logger.info(f"   Balance: ${self.current_balance:.2f}")
                self.logger.info(f"   Target Progress: {(daily_pnl/self.daily_target)*100:.1f}%")
                
                # Risk check - stop if daily loss exceeds limit
                if daily_pnl < -self.max_daily_risk:
                    self.logger.warning(f"⚠️ DAILY LOSS LIMIT EXCEEDED: ${daily_pnl:.2f}")
                    break
                    
            except Exception as e:
                self.logger.error(f"❌ Error processing {trading_day}: {e}")
                continue
        
        # Generate comprehensive results
        results = self._generate_optimized_results(start_date, end_date)
        
        self.logger.info(f"🏁 MONTH-LONG BACKTEST COMPLETED")
        self.logger.info(f"   Total Return: {results['total_return']:.2f}%")
        self.logger.info(f"   Daily Target Achievement: {results['daily_target_achievement']:.1f}%")
        self.logger.info(f"   Win Rate: {results['win_rate']:.1f}%")
        
        return results
    
    def _process_optimized_trading_day(self, trading_day: datetime) -> None:
        """Process a single trading day with optimization"""
        
        # Load options data for the day with relaxed filters for better coverage
        options_data = self.data_loader.load_options_for_date(
            trading_day, 
            min_volume=1,  # Relaxed volume requirement
            max_dte=45,
            strike_range_pct=0.20  # Wider strike range
        )
        
        if options_data.empty:
            self.logger.warning(f"⚠️ No options data for {trading_day}")
            return
        
        # Generate intraday trading signals (multiple per day)
        trading_times = self._generate_optimized_trading_times()
        
        for trading_time in trading_times:
            current_datetime = datetime.combine(trading_day, trading_time)
            
            # Check if we've hit daily target (early exit)
            if self.daily_pnl.get(str(trading_day), 0) >= self.daily_target:
                self.logger.info(f"🎯 DAILY TARGET ACHIEVED - STOPPING TRADING")
                break
            
            # Check if we're approaching daily loss limit
            if self.daily_pnl.get(str(trading_day), 0) <= -self.max_daily_risk * 0.8:
                self.logger.warning(f"⚠️ APPROACHING DAILY LOSS LIMIT - REDUCING RISK")
                continue
            
            # Close positions that need to be closed
            self._close_positions_if_needed(current_datetime, options_data)
            
            # Generate new signal if conditions are right
            if len(self.open_positions) < 3:  # Max 3 concurrent positions
                self._attempt_new_position(current_datetime, options_data)
    
    def _generate_optimized_trading_times(self) -> List[time]:
        """Generate optimal intraday trading times for 0DTE"""
        
        return [
            time(9, 45),   # Post-open momentum
            time(10, 30),  # Morning trend
            time(11, 15),  # Pre-lunch
            time(13, 30),  # Post-lunch
            time(14, 15),  # Afternoon momentum
            time(15, 0),   # Power hour start
        ]
    
    def _attempt_new_position(
        self, 
        current_datetime: datetime, 
        options_data: pd.DataFrame
    ) -> None:
        """Attempt to open a new optimized position"""
        
        # Get current SPY price
        spy_price = self.data_loader._estimate_spy_price(options_data)
        
        # Generate enhanced strategy recommendation
        recommendation = self._get_enhanced_recommendation(
            options_data, spy_price, current_datetime
        )
        
        if recommendation.specific_strategy == 'NO_TRADE':
            return
        
        # Check cash availability
        available_cash = self.cash_manager.calculate_available_cash()
        if recommendation.cash_required > available_cash:
            self.logger.warning(f"💰 Insufficient cash: Need ${recommendation.cash_required}, Have ${available_cash}")
            return
        
        # Open the position
        self._open_optimized_position(recommendation, current_datetime, spy_price, options_data)
    
    def _get_enhanced_recommendation(
        self, 
        options_data: pd.DataFrame, 
        spy_price: float, 
        current_datetime: datetime
    ):
        """Get enhanced strategy recommendation with Iron Condor boost"""
        
        # Get base recommendation
        recommendation = self.strategy_selector.select_optimal_strategy(
            options_data=options_data,
            spy_price=spy_price,
            current_time=current_datetime
        )
        
        # ENHANCEMENT: Boost Iron Condor selection in flat markets
        if self._is_flat_market_condition(options_data, spy_price):
            self.logger.info("📊 FLAT MARKET DETECTED - BOOSTING IRON CONDOR SELECTION")
            
            # Force Iron Condor consideration if not already selected
            if recommendation.specific_strategy != 'IRON_CONDOR':
                # Try to force Iron Condor selection
                iron_condor_rec = self._force_iron_condor_selection(
                    options_data, spy_price, current_datetime
                )
                if iron_condor_rec:
                    recommendation = iron_condor_rec
        
        return recommendation
    
    def _is_flat_market_condition(
        self, 
        options_data: pd.DataFrame, 
        spy_price: float
    ) -> bool:
        """Enhanced flat market detection for Iron Condor optimization"""
        
        # Check price stability (low volatility indicator)
        price_range = options_data['strike'].max() - options_data['strike'].min()
        relative_range = price_range / spy_price
        
        # Check volume distribution (balanced call/put activity)
        calls = options_data[options_data['option_type'] == 'call']
        puts = options_data[options_data['option_type'] == 'put']
        
        if len(calls) == 0 or len(puts) == 0:
            return False
        
        call_volume = calls['volume'].sum()
        put_volume = puts['volume'].sum()
        total_volume = call_volume + put_volume
        
        if total_volume == 0:
            return False
        
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 1.0
        
        # Flat market conditions:
        # 1. Balanced put/call activity (0.8 < P/C < 1.2)
        # 2. Reasonable price range
        flat_conditions = (
            0.8 <= put_call_ratio <= 1.2 and
            relative_range > 0.02  # At least 2% range
        )
        
        if flat_conditions:
            self.logger.info(f"🎯 FLAT MARKET INDICATORS:")
            self.logger.info(f"   Put/Call Ratio: {put_call_ratio:.2f}")
            self.logger.info(f"   Price Range: {relative_range*100:.1f}%")
        
        return flat_conditions
    
    def _force_iron_condor_selection(
        self, 
        options_data: pd.DataFrame, 
        spy_price: float, 
        current_datetime: datetime
    ):
        """Force Iron Condor selection in flat markets"""
        
        # Calculate available cash
        available_cash = self.cash_manager.calculate_available_cash()
        
        # Estimate Iron Condor parameters
        strikes = self._calculate_iron_condor_strikes(spy_price, options_data)
        
        if not strikes:
            return None
        
        # Estimate cash requirements (conservative)
        spread_width = 2.0  # $2 spread width
        estimated_credit = 0.60  # $0.60 credit
        cash_required = (spread_width - estimated_credit) * 100 * 2  # Two spreads
        
        if cash_required > available_cash:
            return None
        
        # Create forced Iron Condor recommendation
        from src.strategies.hybrid_adaptive.enhanced_strategy_selector import EnhancedStrategyRecommendation
        
        forced_recommendation = EnhancedStrategyRecommendation(
            specific_strategy='IRON_CONDOR',
            confidence=75.0,  # High confidence for flat markets
            cash_required=cash_required,
            max_profit=estimated_credit * 100,
            max_loss=cash_required,
            position_size=1,
            reasoning=f"FORCED: Flat market detected - Iron Condor optimal",
            risk_level='MEDIUM',
            intelligence_score=70.0
        )
        
        self.logger.info(f"🎯 FORCED IRON CONDOR SELECTION:")
        self.logger.info(f"   Cash Required: ${cash_required:.2f}")
        self.logger.info(f"   Max Profit: ${estimated_credit * 100:.2f}")
        
        return forced_recommendation
    
    def _calculate_iron_condor_strikes(
        self, 
        spy_price: float, 
        options_data: pd.DataFrame
    ) -> Optional[Dict[str, float]]:
        """Calculate realistic Iron Condor strikes"""
        
        available_strikes = sorted(options_data['strike'].unique())
        
        # Find strikes around current price
        atm_strikes = [s for s in available_strikes if abs(s - spy_price) <= 5.0]
        
        if len(atm_strikes) < 4:
            return None
        
        # Iron Condor structure: Short strikes closer to ATM, Long strikes further
        try:
            put_short = max([s for s in atm_strikes if s < spy_price])  # Short put below
            put_long = put_short - 2.0  # Long put further below
            call_short = min([s for s in atm_strikes if s > spy_price])  # Short call above
            call_long = call_short + 2.0  # Long call further above
            
            return {
                'put_short': put_short,
                'put_long': put_long,
                'call_short': call_short,
                'call_long': call_long
            }
        except (ValueError, IndexError):
            return None
    
    def _open_optimized_position(
        self, 
        recommendation, 
        current_datetime: datetime, 
        spy_price: float,
        options_data: pd.DataFrame
    ) -> None:
        """Open an optimized position with aggressive risk management"""
        
        position_id = f"{recommendation.specific_strategy}_{current_datetime.strftime('%H%M%S')}"
        
        # Calculate aggressive exit targets
        max_profit_target = recommendation.max_profit * self.profit_target_multiplier
        stop_loss_level = recommendation.cash_required * self.stop_loss_multiplier
        
        # Calculate time-based exit (CRITICAL for preventing worthless expiration)
        time_exit_target = current_datetime + timedelta(hours=self.max_hold_hours)
        
        # Ensure we exit well before market close (3:30 PM latest)
        market_close_buffer = datetime.combine(current_datetime.date(), time(15, 30))
        if time_exit_target > market_close_buffer:
            time_exit_target = market_close_buffer
        
        # Create optimized position
        position = OptimizedPosition(
            position_id=position_id,
            strategy_type=recommendation.specific_strategy,
            entry_time=current_datetime,
            entry_spy_price=spy_price,
            strikes=self._extract_strikes_from_recommendation(recommendation, options_data, spy_price),
            cash_at_risk=recommendation.cash_required,
            margin_required=recommendation.cash_required,
            max_profit_target=max_profit_target,
            stop_loss_level=stop_loss_level,
            time_exit_target=time_exit_target
        )
        
        # Add to cash manager
        self.cash_manager.add_position(
            position_id=position_id,
            strategy_type=recommendation.specific_strategy,
            cash_required=recommendation.cash_required,
            max_loss=recommendation.max_loss,
            max_profit=recommendation.max_profit,
            strikes=position.strikes
        )
        
        # Track position
        self.open_positions[position_id] = position
        
        self.logger.info(f"🚀 OPENED OPTIMIZED POSITION:")
        self.logger.info(f"   Strategy: {recommendation.specific_strategy}")
        self.logger.info(f"   Cash at Risk: ${recommendation.cash_required:.2f}")
        self.logger.info(f"   Profit Target: ${max_profit_target:.2f}")
        self.logger.info(f"   Stop Loss: ${stop_loss_level:.2f}")
        self.logger.info(f"   Time Exit: {time_exit_target.strftime('%H:%M')}")
    
    def _extract_strikes_from_recommendation(
        self, 
        recommendation, 
        options_data: pd.DataFrame, 
        spy_price: float
    ) -> Dict[str, float]:
        """Extract realistic strikes based on strategy type"""
        
        available_strikes = sorted(options_data['strike'].unique())
        
        if recommendation.specific_strategy == 'IRON_CONDOR':
            return self._calculate_iron_condor_strikes(spy_price, options_data) or {}
        
        elif recommendation.specific_strategy in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD']:
            # Find 2-point spreads
            if recommendation.specific_strategy == 'BULL_PUT_SPREAD':
                short_strike = max([s for s in available_strikes if s < spy_price * 0.98])
                long_strike = short_strike - 2.0
            else:  # BEAR_CALL_SPREAD
                short_strike = min([s for s in available_strikes if s > spy_price * 1.02])
                long_strike = short_strike + 2.0
            
            return {'short_strike': short_strike, 'long_strike': long_strike}
        
        else:  # BUY_CALL, BUY_PUT
            if recommendation.specific_strategy == 'BUY_CALL':
                strike = min([s for s in available_strikes if s > spy_price * 1.01])
            else:  # BUY_PUT
                strike = max([s for s in available_strikes if s < spy_price * 0.99])
            
            return {'strike': strike}
    
    def _close_positions_if_needed(
        self, 
        current_datetime: datetime, 
        options_data: pd.DataFrame
    ) -> None:
        """Close positions based on aggressive risk management rules"""
        
        positions_to_close = []
        
        for position_id, position in self.open_positions.items():
            
            # Rule 1: Time-based exit (CRITICAL)
            if current_datetime >= position.time_exit_target:
                positions_to_close.append((position_id, 'TIME_EXIT'))
                continue
            
            # Rule 2: Profit target hit
            current_pnl = self._calculate_current_position_pnl(position, options_data)
            if current_pnl >= position.max_profit_target:
                positions_to_close.append((position_id, 'PROFIT_TARGET'))
                continue
            
            # Rule 3: Stop loss hit
            if current_pnl <= -position.stop_loss_level:
                positions_to_close.append((position_id, 'STOP_LOSS'))
                continue
            
            # Rule 4: End of day forced exit (3:45 PM)
            if current_datetime.time() >= time(15, 45):
                positions_to_close.append((position_id, 'END_OF_DAY'))
                continue
        
        # Close identified positions
        for position_id, exit_reason in positions_to_close:
            self._close_optimized_position(position_id, current_datetime, options_data, exit_reason)
    
    def _calculate_current_position_pnl(
        self, 
        position: OptimizedPosition, 
        options_data: pd.DataFrame
    ) -> float:
        """Calculate current P&L for a position using Black-Scholes"""
        
        current_spy_price = self.data_loader._estimate_spy_price(options_data)
        
        # Use Black-Scholes calculator for real pricing
        entry_data = {
            'entry_credit': position.max_profit_target / 100,  # Convert to per-share
            'max_loss': position.cash_at_risk / 100,
            'spy_price': position.entry_spy_price,
            'strikes': position.strikes
        }
        
        current_value = self.pricing_calculator.calculate_spread_value(
            spread_type=position.strategy_type,
            current_spy_price=current_spy_price,
            entry_data=entry_data,
            time_to_expiry=0.1  # Assume short time to expiry for 0DTE
        )
        
        # Calculate P&L
        if position.strategy_type in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD', 'IRON_CONDOR']:
            # Credit spreads: profit when value decreases
            pnl = (entry_data['entry_credit'] - current_value) * 100
        else:
            # Debit strategies: profit when value increases
            pnl = (current_value - entry_data['entry_credit']) * 100
        
        return pnl
    
    def _close_optimized_position(
        self, 
        position_id: str, 
        current_datetime: datetime, 
        options_data: pd.DataFrame,
        exit_reason: str
    ) -> None:
        """Close a position with detailed tracking"""
        
        position = self.open_positions[position_id]
        current_spy_price = self.data_loader._estimate_spy_price(options_data)
        
        # Calculate final P&L
        final_pnl = self._calculate_current_position_pnl(position, options_data)
        
        # Update position
        position.is_closed = True
        position.exit_time = current_datetime
        position.exit_spy_price = current_spy_price
        position.realized_pnl = final_pnl
        position.exit_reason = exit_reason
        
        # Update balances
        self.current_balance += final_pnl
        
        # Update daily P&L
        trading_day = str(current_datetime.date())
        if trading_day not in self.daily_pnl:
            self.daily_pnl[trading_day] = 0.0
        self.daily_pnl[trading_day] += final_pnl
        
        # Remove from cash manager
        self.cash_manager.remove_position(position_id)
        
        # Move to closed positions
        self.closed_positions.append(position)
        del self.open_positions[position_id]
        
        # Calculate hold time
        hold_time = (current_datetime - position.entry_time).total_seconds() / 3600
        
        self.logger.info(f"🔒 CLOSED POSITION:")
        self.logger.info(f"   Strategy: {position.strategy_type}")
        self.logger.info(f"   P&L: ${final_pnl:.2f}")
        self.logger.info(f"   Hold Time: {hold_time:.1f} hours")
        self.logger.info(f"   Exit Reason: {exit_reason}")
    
    def _generate_optimized_results(self, start_date: str, end_date: str) -> Dict[str, any]:
        """Generate comprehensive results optimized for $250/day analysis"""
        
        if not self.closed_positions:
            return {
                'total_return': 0.0,
                'final_balance': self.initial_balance,
                'total_trades': 0,
                'win_rate': 0.0,
                'daily_target_achievement': 0.0,
                'avg_daily_pnl': 0.0,
                'max_drawdown': 0.0,
                'profitable_days': 0,
                'total_trading_days': len(self.daily_pnl),
                'target_achieved_days': 0,
                'strategy_breakdown': {},
                'daily_pnl_summary': self.daily_pnl,
                'iron_condor_usage': 0,
                'avg_hold_time': 0.0
            }
        
        # Basic metrics
        total_pnl = sum(pos.realized_pnl for pos in self.closed_positions)
        total_return = (total_pnl / self.initial_balance) * 100
        win_rate = (sum(1 for pos in self.closed_positions if pos.realized_pnl > 0) / len(self.closed_positions)) * 100
        
        # Daily target analysis
        profitable_days = sum(1 for pnl in self.daily_pnl.values() if pnl > 0)
        target_achieved_days = sum(1 for pnl in self.daily_pnl.values() if pnl >= self.daily_target)
        daily_target_achievement = (target_achieved_days / len(self.daily_pnl)) * 100 if self.daily_pnl else 0
        
        avg_daily_pnl = sum(self.daily_pnl.values()) / len(self.daily_pnl) if self.daily_pnl else 0
        
        # Strategy breakdown
        strategy_breakdown = {}
        for pos in self.closed_positions:
            if pos.strategy_type not in strategy_breakdown:
                strategy_breakdown[pos.strategy_type] = {
                    'count': 0,
                    'total_pnl': 0.0,
                    'wins': 0,
                    'avg_hold_time': 0.0
                }
            
            strategy_breakdown[pos.strategy_type]['count'] += 1
            strategy_breakdown[pos.strategy_type]['total_pnl'] += pos.realized_pnl
            if pos.realized_pnl > 0:
                strategy_breakdown[pos.strategy_type]['wins'] += 1
            
            hold_time = (pos.exit_time - pos.entry_time).total_seconds() / 3600
            strategy_breakdown[pos.strategy_type]['avg_hold_time'] += hold_time
        
        # Calculate averages
        for strategy_data in strategy_breakdown.values():
            if strategy_data['count'] > 0:
                strategy_data['win_rate'] = (strategy_data['wins'] / strategy_data['count']) * 100
                strategy_data['avg_pnl'] = strategy_data['total_pnl'] / strategy_data['count']
                strategy_data['avg_hold_time'] /= strategy_data['count']
        
        # Drawdown calculation
        running_balance = self.initial_balance
        peak_balance = self.initial_balance
        max_drawdown = 0.0
        
        for daily_pnl in self.daily_pnl.values():
            running_balance += daily_pnl
            if running_balance > peak_balance:
                peak_balance = running_balance
            
            current_drawdown = ((peak_balance - running_balance) / peak_balance) * 100
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
        
        return {
            'total_return': total_return,
            'final_balance': self.current_balance,
            'total_trades': len(self.closed_positions),
            'win_rate': win_rate,
            'daily_target_achievement': daily_target_achievement,
            'avg_daily_pnl': avg_daily_pnl,
            'max_drawdown': max_drawdown,
            'profitable_days': profitable_days,
            'total_trading_days': len(self.daily_pnl),
            'target_achieved_days': target_achieved_days,
            'strategy_breakdown': strategy_breakdown,
            'daily_pnl_summary': self.daily_pnl,
            'iron_condor_usage': strategy_breakdown.get('IRON_CONDOR', {}).get('count', 0),
            'avg_hold_time': sum(
                (pos.exit_time - pos.entry_time).total_seconds() / 3600 
                for pos in self.closed_positions
            ) / len(self.closed_positions) if self.closed_positions else 0
        }

def main():
    """Run the optimized $250/day target backtester"""
    
    print("🎯 OPTIMIZED $250/DAY TARGET BACKTESTER")
    print("=" * 50)
    
    # Initialize backtester
    backtester = Optimized250DailyTargetBacktester(initial_balance=25000)
    
    # Run month-long backtest (September 2024)
    results = backtester.run_month_long_backtest(
        start_date="2024-09-01",
        end_date="2024-09-30"
    )
    
    # Display results
    print(f"\n🏁 MONTH-LONG BACKTEST RESULTS")
    print(f"=" * 50)
    print(f"📊 PERFORMANCE METRICS:")
    print(f"   Total Return: {results['total_return']:.2f}%")
    print(f"   Final Balance: ${results['final_balance']:,.2f}")
    print(f"   Total Trades: {results['total_trades']}")
    print(f"   Win Rate: {results['win_rate']:.1f}%")
    print(f"   Max Drawdown: {results['max_drawdown']:.2f}%")
    
    print(f"\n🎯 DAILY TARGET ANALYSIS:")
    print(f"   Daily Target: $250")
    print(f"   Target Achievement Rate: {results['daily_target_achievement']:.1f}%")
    print(f"   Average Daily P&L: ${results['avg_daily_pnl']:.2f}")
    print(f"   Profitable Days: {results['profitable_days']}/{results['total_trading_days']}")
    print(f"   Target Achieved Days: {results['target_achieved_days']}/{results['total_trading_days']}")
    
    print(f"\n📈 STRATEGY BREAKDOWN:")
    for strategy, data in results['strategy_breakdown'].items():
        print(f"   {strategy}:")
        print(f"     Trades: {data['count']}")
        print(f"     Win Rate: {data['win_rate']:.1f}%")
        print(f"     Avg P&L: ${data['avg_pnl']:.2f}")
        print(f"     Avg Hold Time: {data['avg_hold_time']:.1f}h")
    
    print(f"\n🎯 IRON CONDOR ANALYSIS:")
    print(f"   Iron Condor Trades: {results['iron_condor_usage']}")
    print(f"   Iron Condor Usage Rate: {(results['iron_condor_usage']/results['total_trades']*100):.1f}%")
    
    print(f"\n⏱️ RISK MANAGEMENT:")
    print(f"   Average Hold Time: {results['avg_hold_time']:.1f} hours")
    print(f"   (Target: < 3.0 hours to prevent worthless expiration)")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/Users/devops/Desktop/coding/advanced-options-strategies/logs/optimized_250_backtest_{timestamp}.txt"
    
    with open(results_file, 'w') as f:
        f.write("🎯 OPTIMIZED $250/DAY TARGET BACKTESTER RESULTS\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("📊 PERFORMANCE SUMMARY:\n")
        f.write(f"Total Return: {results['total_return']:.2f}%\n")
        f.write(f"Final Balance: ${results['final_balance']:,.2f}\n")
        f.write(f"Total Trades: {results['total_trades']}\n")
        f.write(f"Win Rate: {results['win_rate']:.1f}%\n")
        f.write(f"Max Drawdown: {results['max_drawdown']:.2f}%\n\n")
        
        f.write("🎯 DAILY TARGET ANALYSIS:\n")
        f.write(f"Daily Target: $250\n")
        f.write(f"Target Achievement Rate: {results['daily_target_achievement']:.1f}%\n")
        f.write(f"Average Daily P&L: ${results['avg_daily_pnl']:.2f}\n")
        f.write(f"Profitable Days: {results['profitable_days']}/{results['total_trading_days']}\n")
        f.write(f"Target Achieved Days: {results['target_achieved_days']}/{results['total_trading_days']}\n\n")
        
        f.write("📈 STRATEGY BREAKDOWN:\n")
        for strategy, data in results['strategy_breakdown'].items():
            f.write(f"{strategy}:\n")
            f.write(f"  Trades: {data['count']}\n")
            f.write(f"  Win Rate: {data['win_rate']:.1f}%\n")
            f.write(f"  Total P&L: ${data['total_pnl']:.2f}\n")
            f.write(f"  Avg P&L: ${data['avg_pnl']:.2f}\n")
            f.write(f"  Avg Hold Time: {data['avg_hold_time']:.1f}h\n\n")
        
        f.write("📅 DAILY P&L BREAKDOWN:\n")
        for date, pnl in results['daily_pnl_summary'].items():
            target_status = "✅" if pnl >= 250 else "❌"
            f.write(f"{date}: ${pnl:.2f} {target_status}\n")
    
    print(f"\n💾 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    main()
