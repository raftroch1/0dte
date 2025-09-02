#!/usr/bin/env python3
"""
🎯 ENHANCED ADAPTIVE STRATEGY ROUTER
===================================
Combines existing Iron Condor system with ZeroDTE spread trading.
Merges user's ZeroDTESpreadTrader concepts with existing infrastructure.

Key Features:
- Market regime-based strategy selection
- Dynamic position sizing with Kelly Criterion
- Real-time risk management
- $200/day profit target optimization
- Unified account management

Following @.cursorrules:
- Extends existing EnhancedHybridAdaptiveSelector
- Uses existing market regime detection
- Integrates with existing Black-Scholes pricing
- Maintains separation from core files

Location: src/strategies/adaptive_zero_dte/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Enhanced Adaptive Router
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
import logging

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import existing infrastructure
try:
    from src.strategies.hybrid_adaptive.enhanced_strategy_selector import EnhancedHybridAdaptiveSelector
    from src.strategies.cash_management.position_sizer import ConservativeCashManager
    from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
    from src.strategies.market_intelligence.intelligence_engine import MarketIntelligenceEngine
    from src.utils.detailed_logger import DetailedLogger
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_AVAILABLE = False

class EnhancedAdaptiveRouter(EnhancedHybridAdaptiveSelector):
    """
    Enhanced Adaptive Strategy Router
    
    Extends existing EnhancedHybridAdaptiveSelector with:
    1. ZeroDTE spread trading optimization
    2. Kelly Criterion position sizing
    3. $200/day profit target management
    4. Dynamic risk adjustment based on performance
    
    Strategy Selection Logic:
    - NEUTRAL markets → Iron Condors (theta decay)
    - BULLISH markets → Bull Put Spreads (directional credit)
    - BEARISH markets → Bear Call Spreads (directional credit)
    - HIGH MOMENTUM → Option buying (when appropriate)
    """
    
    def __init__(self, account_balance: float = 25000):
        # Initialize parent class
        super().__init__(account_balance)
        
        # ZeroDTE-specific parameters (from user's ZeroDTESpreadTrader)
        self.daily_profit_target = 200  # $200/day target
        self.max_daily_loss = -400      # 2x profit target
        self.target_win_rate = 0.75     # 75% win rate target
        
        # Enhanced position sizing
        self.max_risk_per_trade = 0.02  # 2% of account per trade
        self.max_daily_risk = 0.04      # 4% max daily drawdown
        
        # Spread optimization parameters
        self.default_spread_width = 5   # $5 spread width
        self.target_delta_short = 0.20  # 20 delta for short strikes
        self.min_premium_collected = 0.35  # Min $0.35 per spread
        self.max_positions = 4  # Max concurrent positions
        
        # Dynamic risk management
        self.profit_target_pct = 0.50   # Take profit at 50%
        self.stop_loss_multiplier = 2.0 # Stop at 2x premium
        
        # Time management (from user's requirements)
        self.no_entry_before = time(9, 45)   # No trades before 9:45 AM
        self.no_entry_after = time(14, 30)   # No new trades after 2:30 PM
        self.close_all_time = time(15, 30)   # Close all by 3:30 PM
        
        # Performance tracking
        self.daily_pnl = 0
        self.trades_today = []
        self.win_streak = 0
        self.loss_streak = 0
        
        # Market condition thresholds
        self.max_vix_threshold = 25     # Don't trade if VIX > 25
        self.min_volume_threshold = 1000000  # Min SPY volume
        
        self.logger.info("🎯 ENHANCED ADAPTIVE ROUTER INITIALIZED")
        self.logger.info(f"   Daily Target: ${self.daily_profit_target}")
        self.logger.info(f"   Max Daily Loss: ${abs(self.max_daily_loss)}")
        self.logger.info(f"   Target Win Rate: {self.target_win_rate:.1%}")
    
    def calculate_kelly_position_size(self, premium_collected: float, 
                                    max_loss: float, strategy_type: str) -> int:
        """
        Calculate optimal position size using Kelly Criterion
        Enhanced version of user's calculate_position_size method
        """
        # Maximum risk per trade
        max_risk_dollars = self.current_balance * self.max_risk_per_trade
        
        # Kelly Criterion for options (adjusted for credit spreads)
        win_prob = self._get_strategy_win_probability(strategy_type)
        kelly_fraction = (win_prob * premium_collected - 
                         (1 - win_prob) * max_loss) / max_loss
        kelly_fraction = min(kelly_fraction, 0.25)  # Cap at 25% Kelly
        
        # Position size based on risk
        contracts_by_risk = int(max_risk_dollars / (max_loss * 100))
        
        # Position size based on Kelly
        contracts_by_kelly = int((self.current_balance * kelly_fraction) / (max_loss * 100))
        
        # Take the minimum and ensure we don't over-leverage
        optimal_contracts = min(contracts_by_risk, contracts_by_kelly, 10)
        
        # Scale down if we're having a losing day
        if self.daily_pnl < -100:
            optimal_contracts = max(1, optimal_contracts // 2)
            self.logger.info(f"📉 Scaling down position size due to daily loss: {self.daily_pnl}")
        
        return max(1, optimal_contracts)
    
    def _get_strategy_win_probability(self, strategy_type: str) -> float:
        """Get historical win probability for strategy type"""
        win_probabilities = {
            'IRON_CONDOR': 0.65,      # From our backtesting
            'BULL_PUT_SPREAD': 0.75,  # Credit spreads typically higher
            'BEAR_CALL_SPREAD': 0.75,
            'BUY_CALL': 0.45,         # Option buying lower win rate
            'BUY_PUT': 0.45
        }
        return win_probabilities.get(strategy_type, self.target_win_rate)
    
    def check_enhanced_market_conditions(self, market_data: Dict, 
                                       current_time: datetime) -> Tuple[bool, str]:
        """
        Enhanced market condition check combining existing logic with user's requirements
        """
        # Time window check
        current_time_only = current_time.time()
        if current_time_only < self.no_entry_before or current_time_only > self.no_entry_after:
            return False, f"Outside trading hours ({current_time_only})"
        
        # VIX check (user's requirement)
        vix_level = market_data.get('vix', 0)
        if vix_level > self.max_vix_threshold:
            return False, f"VIX too high: {vix_level}"
        
        # Volume check (user's requirement)
        # For backtesting, assume sufficient volume if not provided
        spy_volume = market_data.get('spy_volume', 2000000)  # Default to 2M volume for backtesting
        if spy_volume < self.min_volume_threshold:
            return False, "Insufficient SPY volume"
        
        # Daily P&L checks
        if self.daily_pnl <= self.max_daily_loss:
            return False, "Daily loss limit reached"
        
        # Profit target check (optional - can keep trading but be more selective)
        if self.daily_pnl >= self.daily_profit_target * 1.5:
            return False, "Daily profit target exceeded - preserving gains"
        
        # Position limit check
        if len(self.trades_today) >= self.max_positions:
            return False, "Maximum positions reached"
        
        return True, "Enhanced market conditions favorable"
    
    def select_adaptive_strategy(self, options_data: pd.DataFrame, 
                               market_data: Dict, current_time: datetime) -> Dict:
        """
        Enhanced strategy selection combining regime detection with user's requirements
        """
        # Check enhanced market conditions first
        can_trade, condition_message = self.check_enhanced_market_conditions(market_data, current_time)
        
        if not can_trade:
            return {
                'strategy_type': 'NO_TRADE',
                'reason': condition_message,
                'confidence': 0
            }
        
        # Use existing market intelligence for regime detection
        spy_price = market_data.get('spy_price', 0)
        intelligence = self.intelligence_engine.analyze_market_intelligence(
            options_data=options_data,
            spy_price=spy_price
        )
        
        # Enhanced strategy selection based on regime
        # Extract regime info from MarketIntelligence object
        regime_type = intelligence.primary_regime
        confidence = intelligence.regime_confidence
        
        self.logger.info(f"   🌊 Market Regime: {regime_type} ({confidence:.1f}%)")
        
        # Strategy selection with user's optimization
        if regime_type == 'NEUTRAL' and confidence > 60:
            # Iron Condors for neutral markets (theta decay strategy)
            strategy_type = 'IRON_CONDOR'
            reasoning = "Neutral market - Iron Condor for theta decay"
            
        elif regime_type == 'BULLISH' and confidence > 35:  # Realistic threshold
            # Bull Put Spreads for bullish markets (directional credit)
            strategy_type = 'BULL_PUT_SPREAD'
            reasoning = "Bullish market - Bull Put Spread for directional credit"
            
        elif regime_type == 'BEARISH' and confidence > 35:  # Realistic threshold
            # Bear Call Spreads for bearish markets (directional credit)
            strategy_type = 'BEAR_CALL_SPREAD'
            reasoning = "Bearish market - Bear Call Spread for directional credit"
            
        else:
            # No trade if confidence too low or mixed signals
            strategy_type = 'NO_TRADE'
            reasoning = f"Low confidence ({confidence}%) or mixed signals"
        
        return {
            'strategy_type': strategy_type,
            'reason': reasoning,
            'confidence': confidence,
            'market_regime': regime_type,
            'intelligence': intelligence
        }
    
    def execute_adaptive_trade(self, strategy_selection: Dict, 
                             options_data: pd.DataFrame, market_data: Dict) -> Dict:
        """
        Execute trade using enhanced position sizing and risk management
        """
        strategy_type = strategy_selection['strategy_type']
        
        if strategy_type == 'NO_TRADE':
            return {'status': 'no_trade', 'reason': strategy_selection['reason']}
        
        # Get optimal strikes using existing infrastructure
        spy_price = market_data.get('spy_price', 0)
        strikes = self._calculate_optimal_strikes(strategy_type, spy_price, options_data)
        
        # Calculate premiums using existing Black-Scholes
        premium_data = self._calculate_spread_premiums(strikes, strategy_type, spy_price)
        
        # Check minimum premium requirement
        net_premium = premium_data['net_premium']
        if net_premium < self.min_premium_collected:
            return {'status': 'rejected', 'reason': 'Premium too low'}
        
        # Calculate Kelly-optimized position size
        max_loss = premium_data['max_loss']
        position_size = self.calculate_kelly_position_size(net_premium, max_loss, strategy_type)
        
        # Create enhanced trade record
        trade = self._create_enhanced_trade_record(
            strategy_type, strikes, premium_data, position_size, market_data
        )
        
        # Execute using existing cash management
        cash_check = self.cash_manager.can_open_position(
            strategy_type, strikes['spread_width'], net_premium, position_size
        )
        
        if not cash_check.can_trade:
            return {'status': 'rejected', 'reason': cash_check.reason}
        
        # Add to tracking
        self.trades_today.append(trade)
        
        self.logger.info(f"🎯 ADAPTIVE TRADE EXECUTED:")
        self.logger.info(f"   Strategy: {strategy_type}")
        self.logger.info(f"   Contracts: {position_size}")
        self.logger.info(f"   Premium: ${net_premium * position_size * 100:.2f}")
        self.logger.info(f"   Max Risk: ${max_loss * position_size * 100:.2f}")
        
        return {'status': 'executed', 'trade': trade}
    
    def _calculate_optimal_strikes(self, strategy_type: str, spy_price: float, 
                                 options_data: pd.DataFrame) -> Dict:
        """Calculate optimal strikes based on strategy type and user's delta targets"""
        
        if strategy_type == 'BULL_PUT_SPREAD':
            # Short put at target delta, long put below
            short_strike = spy_price * (1 - self.target_delta_short * 0.05)  # Approx delta to price
            long_strike = short_strike - self.default_spread_width
            
        elif strategy_type == 'BEAR_CALL_SPREAD':
            # Short call at target delta, long call above
            short_strike = spy_price * (1 + self.target_delta_short * 0.05)  # Approx delta to price
            long_strike = short_strike + self.default_spread_width
            
        elif strategy_type == 'IRON_CONDOR':
            # Use existing Iron Condor strike logic
            put_short_strike = spy_price * 0.98
            put_long_strike = put_short_strike - self.default_spread_width
            call_short_strike = spy_price * 1.02
            call_long_strike = call_short_strike + self.default_spread_width
            
            return {
                'put_short_strike': put_short_strike,
                'put_long_strike': put_long_strike,
                'call_short_strike': call_short_strike,
                'call_long_strike': call_long_strike,
                'spread_width': self.default_spread_width
            }
        
        return {
            'short_strike': short_strike,
            'long_strike': long_strike,
            'spread_width': abs(long_strike - short_strike)
        }
    
    def _calculate_spread_premiums(self, strikes: Dict, strategy_type: str, 
                                 spy_price: float) -> Dict:
        """Calculate spread premiums using existing Black-Scholes"""
        
        # Use existing pricing calculator
        time_to_expiry = 1/365  # 0DTE = 1 day
        volatility = 0.20       # Estimate
        
        if strategy_type == 'IRON_CONDOR':
            # Calculate both put and call spread premiums
            put_spread_value = self.pricing_calculator.calculate_spread_value(
                spy_price, strikes['put_long_strike'], strikes['put_short_strike'],
                time_to_expiry, volatility, 'BULL_PUT_SPREAD'
            )
            call_spread_value = self.pricing_calculator.calculate_spread_value(
                spy_price, strikes['call_long_strike'], strikes['call_short_strike'],
                time_to_expiry, volatility, 'BEAR_CALL_SPREAD'
            )
            net_premium = put_spread_value + call_spread_value
            max_loss = strikes['spread_width'] - net_premium
            
        else:
            # Single spread calculation
            spread_value = self.pricing_calculator.calculate_spread_value(
                spy_price, strikes['long_strike'], strikes['short_strike'],
                time_to_expiry, volatility, strategy_type
            )
            net_premium = spread_value
            max_loss = strikes['spread_width'] - net_premium
        
        return {
            'net_premium': net_premium,
            'max_loss': max_loss,
            'max_profit': net_premium
        }
    
    def _create_enhanced_trade_record(self, strategy_type: str, strikes: Dict,
                                    premium_data: Dict, position_size: int,
                                    market_data: Dict) -> Dict:
        """Create enhanced trade record with user's tracking requirements"""
        
        return {
            'timestamp': datetime.now(),
            'strategy_type': strategy_type,
            'strikes': strikes,
            'contracts': position_size,
            'premium_collected': premium_data['net_premium'] * position_size * 100,
            'max_risk': premium_data['max_loss'] * position_size * 100,
            'profit_target': premium_data['net_premium'] * position_size * 100 * self.profit_target_pct,
            'stop_loss': premium_data['net_premium'] * position_size * 100 * self.stop_loss_multiplier,
            'status': 'open',
            'entry_spy_price': market_data.get('spy_price', 0),
            'entry_vix': market_data.get('vix', 0),
            'market_regime': market_data.get('regime', 'UNKNOWN')
        }
    
    def manage_open_positions(self, market_data: Dict, current_time: datetime) -> List[Dict]:
        """
        Enhanced position management with user's dynamic exit logic
        """
        actions = []
        
        for trade in self.trades_today:
            if trade['status'] != 'open':
                continue
            
            # Calculate current P&L using existing pricing
            current_pnl = self._calculate_current_pnl(trade, market_data)
            
            # User's exit conditions
            if current_pnl >= trade['profit_target']:
                self._close_position(trade, current_pnl, 'profit_target')
                actions.append({'action': 'close', 'reason': 'profit_target', 'pnl': current_pnl})
                
            elif current_pnl <= -trade['stop_loss']:
                self._close_position(trade, current_pnl, 'stop_loss')
                actions.append({'action': 'close', 'reason': 'stop_loss', 'pnl': current_pnl})
                
            elif current_time.time() >= self.close_all_time:
                self._close_position(trade, current_pnl, 'time_exit')
                actions.append({'action': 'close', 'reason': 'time_exit', 'pnl': current_pnl})
                
            # Dynamic trailing stop for winning positions
            elif current_pnl > trade['premium_collected'] * 0.25:
                trade['stop_loss'] = 0  # Trail to breakeven
                actions.append({'action': 'adjust', 'reason': 'trail_stop'})
        
        return actions
    
    def _calculate_current_pnl(self, trade: Dict, market_data: Dict) -> float:
        """Calculate current P&L using existing Black-Scholes pricing"""
        
        current_spy_price = market_data.get('spy_price', trade['entry_spy_price'])
        time_elapsed = (datetime.now() - trade['timestamp']).seconds / 3600
        time_to_expiry = max(0.001, (6.5 - time_elapsed) / (365 * 24))  # Remaining time in years
        
        # Use existing pricing calculator for current spread value
        strategy_type = trade['strategy_type']
        strikes = trade['strikes']
        
        if strategy_type == 'IRON_CONDOR':
            # Calculate both spreads
            put_value = self.pricing_calculator.calculate_spread_value(
                current_spy_price, strikes['put_long_strike'], strikes['put_short_strike'],
                time_to_expiry, 0.20, 'BULL_PUT_SPREAD'
            )
            call_value = self.pricing_calculator.calculate_spread_value(
                current_spy_price, strikes['call_long_strike'], strikes['call_short_strike'],
                time_to_expiry, 0.20, 'BEAR_CALL_SPREAD'
            )
            current_spread_value = put_value + call_value
        else:
            current_spread_value = self.pricing_calculator.calculate_spread_value(
                current_spy_price, strikes['long_strike'], strikes['short_strike'],
                time_to_expiry, 0.20, strategy_type
            )
        
        # P&L = Entry Credit - Current Cost to Close
        entry_credit = trade['premium_collected'] / (trade['contracts'] * 100)
        pnl_per_contract = entry_credit - current_spread_value
        total_pnl = pnl_per_contract * trade['contracts'] * 100
        
        return total_pnl
    
    def _close_position(self, trade: Dict, realized_pnl: float, reason: str):
        """Close position and update tracking (user's method enhanced)"""
        
        trade['status'] = 'closed'
        trade['exit_time'] = datetime.now()
        trade['realized_pnl'] = realized_pnl
        trade['exit_reason'] = reason
        
        # Update daily tracking
        self.daily_pnl += realized_pnl
        self.current_balance += realized_pnl
        
        # Update streaks
        if realized_pnl > 0:
            self.win_streak += 1
            self.loss_streak = 0
        else:
            self.loss_streak += 1
            self.win_streak = 0
        
        self.logger.info(f"📊 POSITION CLOSED:")
        self.logger.info(f"   Reason: {reason}")
        self.logger.info(f"   P&L: ${realized_pnl:.2f}")
        self.logger.info(f"   Daily P&L: ${self.daily_pnl:.2f}")
        self.logger.info(f"   Win Streak: {self.win_streak}")
    
    def generate_enhanced_daily_report(self) -> Dict:
        """Generate comprehensive daily report (user's method enhanced)"""
        
        closed_trades = [t for t in self.trades_today if t['status'] == 'closed']
        
        if not closed_trades:
            return {'message': 'No trades executed today'}
        
        wins = sum(1 for t in closed_trades if t['realized_pnl'] > 0)
        losses = len(closed_trades) - wins
        
        # Strategy breakdown
        strategy_breakdown = {}
        for trade in closed_trades:
            strategy = trade['strategy_type']
            if strategy not in strategy_breakdown:
                strategy_breakdown[strategy] = {'count': 0, 'pnl': 0, 'wins': 0}
            strategy_breakdown[strategy]['count'] += 1
            strategy_breakdown[strategy]['pnl'] += trade['realized_pnl']
            if trade['realized_pnl'] > 0:
                strategy_breakdown[strategy]['wins'] += 1
        
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_trades': len(closed_trades),
            'wins': wins,
            'losses': losses,
            'win_rate': wins / len(closed_trades) if closed_trades else 0,
            'daily_pnl': self.daily_pnl,
            'target_achieved': self.daily_pnl >= self.daily_profit_target,
            'account_balance': self.current_balance,
            'return_on_capital': (self.daily_pnl / self.initial_balance) * 100,
            'largest_win': max([t['realized_pnl'] for t in closed_trades], default=0),
            'largest_loss': min([t['realized_pnl'] for t in closed_trades], default=0),
            'average_win': np.mean([t['realized_pnl'] for t in closed_trades if t['realized_pnl'] > 0]) if wins > 0 else 0,
            'average_loss': np.mean([t['realized_pnl'] for t in closed_trades if t['realized_pnl'] < 0]) if losses > 0 else 0,
            'strategy_breakdown': strategy_breakdown,
            'win_streak': self.win_streak,
            'loss_streak': self.loss_streak
        }
        
        return report
    
    def reset_daily_counters(self):
        """Reset daily tracking (user's method)"""
        self.daily_pnl = 0
        self.trades_today = []
        self.win_streak = 0
        self.loss_streak = 0


# Example usage combining existing infrastructure with user's requirements
def main():
    """
    Main execution function demonstrating the enhanced adaptive router
    """
    # Initialize enhanced router
    router = EnhancedAdaptiveRouter(account_balance=25000)
    
    # Example market data
    market_data = {
        'spy_price': 450.00,
        'vix': 18.5,
        'spy_volume': 50000000,
        'regime': 'NEUTRAL'
    }
    
    # Example options data (would come from real data loader)
    options_data = pd.DataFrame({
        'strike': [445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455],
        'option_type': ['put'] * 11,
        'bid': [0.50, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05, 0.02],
        'ask': [0.55, 0.50, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05]
    })
    
    current_time = datetime.now()
    
    # Select strategy using enhanced adaptive logic
    strategy_selection = router.select_adaptive_strategy(options_data, market_data, current_time)
    print(f"Strategy Selection: {strategy_selection}")
    
    # Execute trade if recommended
    if strategy_selection['strategy_type'] != 'NO_TRADE':
        trade_result = router.execute_adaptive_trade(strategy_selection, options_data, market_data)
        print(f"Trade Result: {trade_result}")
        
        # Manage positions
        actions = router.manage_open_positions(market_data, current_time)
        print(f"Position Management: {actions}")
    
    # Generate daily report
    daily_report = router.generate_enhanced_daily_report()
    print(f"\nDaily Report: {daily_report}")
    
    return router


if __name__ == "__main__":
    if not IMPORTS_AVAILABLE:
        print("❌ Required modules not available. Please check imports.")
        exit(1)
    
    router = main()
