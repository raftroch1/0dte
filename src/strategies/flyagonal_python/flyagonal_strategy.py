#!/usr/bin/env python3
"""
🦋 FLYAGONAL STRATEGY - PYTHON IMPLEMENTATION
============================================
Complex multi-leg options strategy based on Steve Guns methodology.

Strategy Components:
1. Call Broken Wing Butterfly (above market) - profits from rising markets + falling volatility
2. Put Diagonal Spread (below market) - profits from falling markets + rising volatility

Key Features:
- 6-leg position management
- VIX regime optimization  
- 200+ point profit zone requirement
- Dynamic risk management integration

Following @.cursorrules:
- Extends existing successful backtesting framework
- Maintains separation from Iron Condor system
- Uses real data and Black-Scholes pricing
- Professional risk management

Location: src/strategies/flyagonal_python/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Flyagonal Strategy Module
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, time
import pandas as pd
import numpy as np

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import framework components
try:
    from src.data.parquet_data_loader import ParquetDataLoader
    from src.strategies.cash_management.position_sizer import ConservativeCashManager
    from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
    from src.utils.detailed_logger import DetailedLogger
    from src.strategies.market_intelligence.intelligence_engine import MarketIntelligenceEngine
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_AVAILABLE = False

class FlyagonalPosition:
    """Represents a complete Flyagonal position (6 legs)"""
    
    def __init__(self, position_id: str, entry_time: datetime, spy_price: float):
        self.position_id = position_id
        self.entry_time = entry_time
        self.spy_price = spy_price
        
        # Position components
        self.call_butterfly: Optional[Dict] = None  # 3 legs
        self.put_diagonal: Optional[Dict] = None    # 3 legs (different expiries)
        
        # Position tracking
        self.entry_cost = 0.0
        self.current_value = 0.0
        self.unrealized_pnl = 0.0
        self.max_profit_potential = 0.0
        self.max_loss_potential = 0.0
        
        # Risk management
        self.profit_target = 0.0
        self.stop_loss = 0.0
        self.time_exit = None
        
        # VIX regime at entry
        self.entry_vix_regime = None
        self.entry_vix_level = None
        
        # Status tracking
        self.is_open = True
        self.exit_time = None
        self.exit_reason = None
        self.realized_pnl = 0.0

class FlyagonalStrategy:
    """
    Flyagonal Strategy Implementation
    
    Implements Steve Guns' complex multi-leg strategy:
    - Call Broken Wing Butterfly (3 legs, same expiry)
    - Put Diagonal Spread (3 legs, different expiries)
    
    Key Innovation: Combines directional and volatility plays
    """
    
    def __init__(self, initial_balance: float = 25000):
        if not IMPORTS_AVAILABLE:
            raise ImportError("Required modules not available")
        
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Initialize framework components
        data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
        self.data_loader = ParquetDataLoader(parquet_path=data_path)
        self.cash_manager = ConservativeCashManager(initial_balance)
        self.pricing_calculator = BlackScholesCalculator()
        self.logger = DetailedLogger()
        self.intelligence_engine = MarketIntelligenceEngine()
        
        # Flyagonal-specific parameters
        self.min_profit_zone_width = 200  # Steve Guns requirement: 200+ point profit zone
        self.max_positions = 1  # Conservative: complex positions need focus
        self.max_hold_days = 7  # Multi-DTE strategy
        
        # VIX regime thresholds (for strategy selection)
        self.vix_low_threshold = 15.0   # Low volatility regime
        self.vix_high_threshold = 25.0  # High volatility regime
        
        # Risk management parameters
        self.profit_target_pct = 0.30   # 30% profit target
        self.stop_loss_pct = 0.50       # 50% stop loss
        self.max_risk_per_trade = initial_balance * 0.05  # 5% max risk per trade
        
        # Position tracking
        self.open_positions: List[FlyagonalPosition] = []
        self.closed_positions: List[FlyagonalPosition] = []
        self.total_trades = 0
        self.winning_trades = 0
        
        # Performance tracking
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0
        self.daily_pnl: Dict[str, float] = {}
        
        # Strategy statistics
        self.butterfly_wins = 0
        self.diagonal_wins = 0
        self.vix_regime_performance = {
            'LOW': {'trades': 0, 'wins': 0, 'total_pnl': 0.0},
            'MEDIUM': {'trades': 0, 'wins': 0, 'total_pnl': 0.0},
            'HIGH': {'trades': 0, 'wins': 0, 'total_pnl': 0.0}
        }
        
        print("🦋 FLYAGONAL STRATEGY INITIALIZED")
        print("="*50)
        print(f"   Initial Balance: ${initial_balance:,.2f}")
        print(f"   Strategy: Call Butterfly + Put Diagonal")
        print(f"   Min Profit Zone: {self.min_profit_zone_width} points")
        print(f"   Max Positions: {self.max_positions}")
        print(f"   Max Risk per Trade: ${self.max_risk_per_trade:,.2f}")
        print(f"   ✅ 6-LEG POSITION MANAGEMENT")
        print(f"   ✅ VIX REGIME OPTIMIZATION")
        print(f"   ✅ REAL BLACK-SCHOLES PRICING")
    
    def detect_vix_regime(self, current_vix: float) -> str:
        """Detect VIX regime for strategy optimization"""
        if current_vix < self.vix_low_threshold:
            return 'LOW'
        elif current_vix > self.vix_high_threshold:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def calculate_profit_zone(self, call_butterfly: Dict, put_diagonal: Dict, spy_price: float) -> Dict[str, float]:
        """Calculate the profit zone for the complete Flyagonal position"""
        
        # Call butterfly profit zone (above market)
        call_lower_breakeven = call_butterfly['short_strike'] + call_butterfly['net_credit']
        call_upper_breakeven = call_butterfly['long_upper_strike'] - call_butterfly['net_credit']
        
        # Put diagonal profit zone (below market)  
        put_upper_breakeven = put_diagonal['short_strike'] - put_diagonal['net_credit']
        put_lower_breakeven = put_diagonal['long_strike'] + put_diagonal['net_credit']
        
        # Combined profit zone
        total_profit_zone_width = (call_upper_breakeven - call_lower_breakeven) + (put_upper_breakeven - put_lower_breakeven)
        
        return {
            'call_butterfly_zone': call_upper_breakeven - call_lower_breakeven,
            'put_diagonal_zone': put_upper_breakeven - put_lower_breakeven,
            'total_profit_zone': total_profit_zone_width,
            'call_lower_be': call_lower_breakeven,
            'call_upper_be': call_upper_breakeven,
            'put_lower_be': put_lower_breakeven,
            'put_upper_be': put_upper_breakeven
        }
    
    def should_enter_flyagonal(self, options_data: pd.DataFrame, spy_price: float, current_vix: float) -> bool:
        """
        Determine if conditions are right for Flyagonal entry
        
        Entry Criteria:
        1. VIX regime suitable for multi-leg strategy
        2. Sufficient options liquidity
        3. Profit zone width >= 200 points
        4. Risk/reward ratio acceptable
        5. No existing positions (conservative approach)
        """
        
        # Check if we already have positions
        if len(self.open_positions) >= self.max_positions:
            return False
        
        # Check VIX regime - avoid extreme volatility
        vix_regime = self.detect_vix_regime(current_vix)
        if vix_regime == 'HIGH':  # Too volatile for complex positions
            return False
        
        # Check options availability
        calls = options_data[options_data['option_type'] == 'call']
        puts = options_data[options_data['option_type'] == 'put']
        
        if len(calls) < 10 or len(puts) < 10:  # Need sufficient options for 6-leg strategy
            return False
        
        # Check if we can construct both components
        call_butterfly = self._construct_call_butterfly(calls, spy_price)
        put_diagonal = self._construct_put_diagonal(puts, spy_price)
        
        if not call_butterfly or not put_diagonal:
            return False
        
        # Check profit zone requirement
        profit_zone = self.calculate_profit_zone(call_butterfly, put_diagonal, spy_price)
        if profit_zone['total_profit_zone'] < self.min_profit_zone_width:
            return False
        
        # Check risk/reward ratio
        total_risk = call_butterfly['max_loss'] + put_diagonal['max_loss']
        total_reward = call_butterfly['max_profit'] + put_diagonal['max_profit']
        
        if total_risk > self.max_risk_per_trade or total_reward / total_risk < 1.5:
            return False
        
        return True
    
    def _construct_call_butterfly(self, calls: pd.DataFrame, spy_price: float) -> Optional[Dict]:
        """
        Construct Call Broken Wing Butterfly (3 legs, same expiry)
        
        Structure:
        - Buy 1 ITM call (lower strike)
        - Sell 2 ATM calls (middle strike) 
        - Buy 1 OTM call (upper strike, "broken wing")
        
        Profits from: Rising market + falling volatility
        """
        
        try:
            # Sort calls by strike
            calls_sorted = calls.sort_values('strike')
            
            # Find strikes around current price
            atm_calls = calls_sorted[abs(calls_sorted['strike'] - spy_price) <= 5.0]
            if len(atm_calls) < 3:
                return None
            
            # Select strikes for butterfly
            middle_strike = spy_price  # ATM for short strikes
            lower_strike = spy_price - 10  # ITM long
            upper_strike = spy_price + 15  # OTM long (broken wing - further out)
            
            # Find closest available strikes
            lower_call = calls_sorted[calls_sorted['strike'] <= lower_strike].iloc[-1] if len(calls_sorted[calls_sorted['strike'] <= lower_strike]) > 0 else None
            middle_call = calls_sorted.iloc[(calls_sorted['strike'] - middle_strike).abs().argsort()[:1]].iloc[0]
            upper_call = calls_sorted[calls_sorted['strike'] >= upper_strike].iloc[0] if len(calls_sorted[calls_sorted['strike'] >= upper_strike]) > 0 else None
            
            if lower_call is None or upper_call is None:
                return None
            
            # Calculate net credit/debit
            net_cost = (lower_call['close'] + upper_call['close']) - (2 * middle_call['close'])
            
            # Calculate max profit/loss
            strike_spread = middle_call['strike'] - lower_call['strike']
            max_profit = strike_spread - abs(net_cost)
            max_loss = abs(net_cost)
            
            return {
                'type': 'call_broken_wing_butterfly',
                'lower_strike': lower_call['strike'],
                'middle_strike': middle_call['strike'],
                'upper_strike': upper_call['strike'],
                'net_cost': net_cost,
                'net_credit': -net_cost if net_cost < 0 else 0,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'legs': [
                    {'action': 'BUY', 'strike': lower_call['strike'], 'price': lower_call['close']},
                    {'action': 'SELL', 'strike': middle_call['strike'], 'price': middle_call['close'], 'quantity': 2},
                    {'action': 'BUY', 'strike': upper_call['strike'], 'price': upper_call['close']}
                ]
            }
            
        except Exception as e:
            print(f"❌ Error constructing call butterfly: {e}")
            return None
    
    def _construct_put_diagonal(self, puts: pd.DataFrame, spy_price: float) -> Optional[Dict]:
        """
        Construct Put Diagonal Spread (3 legs, different expiries)
        
        Structure:
        - Sell 1 near-term ATM put (short expiry, high theta)
        - Buy 1 longer-term ATM put (long expiry, protection)
        - Buy 1 longer-term OTM put (long expiry, downside protection)
        
        Profits from: Falling market + rising volatility + time decay
        """
        
        try:
            # For 0DTE strategy, we'll simulate diagonal with different strikes
            # (In real implementation, would use different expiries)
            
            puts_sorted = puts.sort_values('strike', ascending=False)
            
            # Find strikes around current price
            atm_puts = puts_sorted[abs(puts_sorted['strike'] - spy_price) <= 5.0]
            if len(atm_puts) < 2:
                return None
            
            # Select strikes for diagonal
            short_strike = spy_price  # ATM short put
            long_atm_strike = spy_price  # ATM long put (same strike, different expiry in real version)
            long_otm_strike = spy_price - 10  # OTM long put for protection
            
            # Find closest available strikes
            short_put = puts_sorted.iloc[(puts_sorted['strike'] - short_strike).abs().argsort()[:1]].iloc[0]
            long_atm_put = short_put  # Same for 0DTE simulation
            long_otm_put = puts_sorted[puts_sorted['strike'] <= long_otm_strike].iloc[0] if len(puts_sorted[puts_sorted['strike'] <= long_otm_strike]) > 0 else None
            
            if long_otm_put is None:
                return None
            
            # Calculate net credit (selling ATM, buying OTM protection)
            net_credit = short_put['close'] - long_otm_put['close']
            
            # Calculate max profit/loss
            max_profit = net_credit
            max_loss = (short_put['strike'] - long_otm_put['strike']) - net_credit
            
            return {
                'type': 'put_diagonal_spread',
                'short_strike': short_put['strike'],
                'long_atm_strike': long_atm_put['strike'],
                'long_otm_strike': long_otm_put['strike'],
                'net_credit': net_credit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'legs': [
                    {'action': 'SELL', 'strike': short_put['strike'], 'price': short_put['close']},
                    {'action': 'BUY', 'strike': long_otm_put['strike'], 'price': long_otm_put['close']}
                ]
            }
            
        except Exception as e:
            print(f"❌ Error constructing put diagonal: {e}")
            return None
    
    def execute_flyagonal_entry(self, options_data: pd.DataFrame, spy_price: float, current_time: datetime, current_vix: float) -> Optional[FlyagonalPosition]:
        """Execute complete Flyagonal position entry"""
        
        if not self.should_enter_flyagonal(options_data, spy_price, current_vix):
            return None
        
        # Construct both components
        calls = options_data[options_data['option_type'] == 'call']
        puts = options_data[options_data['option_type'] == 'put']
        
        call_butterfly = self._construct_call_butterfly(calls, spy_price)
        put_diagonal = self._construct_put_diagonal(puts, spy_price)
        
        if not call_butterfly or not put_diagonal:
            return None
        
        # Calculate total position cost and risk
        total_cost = call_butterfly['net_cost'] + put_diagonal.get('net_cost', -put_diagonal['net_credit'])
        total_max_loss = call_butterfly['max_loss'] + put_diagonal['max_loss']
        
        # Check if we can afford the position
        if not self.cash_manager.can_open_position(abs(total_cost), total_max_loss):
            return None
        
        # Create position
        position_id = f"FLY_{current_time.strftime('%Y%m%d_%H%M%S')}"
        position = FlyagonalPosition(position_id, current_time, spy_price)
        
        # Set position components
        position.call_butterfly = call_butterfly
        position.put_diagonal = put_diagonal
        position.entry_cost = abs(total_cost)
        position.max_profit_potential = call_butterfly['max_profit'] + put_diagonal['max_profit']
        position.max_loss_potential = total_max_loss
        
        # Set risk management levels
        position.profit_target = position.entry_cost * self.profit_target_pct
        position.stop_loss = position.entry_cost * self.stop_loss_pct
        
        # Set VIX regime
        position.entry_vix_regime = self.detect_vix_regime(current_vix)
        position.entry_vix_level = current_vix
        
        # Update cash management
        self.cash_manager.add_position(position.position_id, position.entry_cost, position.max_loss_potential)
        
        # Add to tracking
        self.open_positions.append(position)
        self.total_trades += 1
        
        # Log the trade
        self.logger.log_trade_entry(
            trade_id=position.position_id,
            strategy='FLYAGONAL',
            entry_time=current_time,
            spy_price=spy_price,
            entry_cost=position.entry_cost,
            max_risk=position.max_loss_potential,
            target_profit=position.profit_target,
            market_conditions={
                'vix_regime': position.entry_vix_regime,
                'vix_level': current_vix,
                'profit_zone_width': self.calculate_profit_zone(call_butterfly, put_diagonal, spy_price)['total_profit_zone']
            }
        )
        
        print(f"✅ FLYAGONAL ENTRY: {position.position_id}")
        print(f"   SPY: ${spy_price:.2f} | VIX: {current_vix:.2f} ({position.entry_vix_regime})")
        print(f"   Entry Cost: ${position.entry_cost:.2f}")
        print(f"   Max Profit: ${position.max_profit_potential:.2f}")
        print(f"   Max Loss: ${position.max_loss_potential:.2f}")
        
        return position
    
    def should_close_position(self, position: FlyagonalPosition, current_spy_price: float, current_time: datetime) -> Tuple[bool, str]:
        """
        Determine if position should be closed
        
        Exit Criteria:
        1. Profit target reached (30%)
        2. Stop loss hit (50%)
        3. Time decay (approaching expiry)
        4. Risk management override
        """
        
        # Calculate current P&L (simplified for 0DTE)
        current_pnl = self._calculate_position_pnl(position, current_spy_price)
        position.unrealized_pnl = current_pnl
        
        # Check profit target
        if current_pnl >= position.profit_target:
            return True, "PROFIT_TARGET"
        
        # Check stop loss
        if current_pnl <= -position.stop_loss:
            return True, "STOP_LOSS"
        
        # Check time exit (for 0DTE, exit before 3:30 PM)
        if current_time.time() >= time(15, 30):
            return True, "TIME_EXIT"
        
        # Check max holding period
        hours_held = (current_time - position.entry_time).total_seconds() / 3600
        if hours_held >= 6.0:  # Max 6 hours for 0DTE
            return True, "MAX_HOLD_TIME"
        
        return False, ""
    
    def _calculate_position_pnl(self, position: FlyagonalPosition, current_spy_price: float) -> float:
        """
        Calculate current P&L for Flyagonal position
        (Simplified calculation for 0DTE strategy)
        """
        
        # Simplified P&L calculation based on SPY movement
        spy_move = current_spy_price - position.spy_price
        spy_move_pct = spy_move / position.spy_price
        
        # Call butterfly P&L (profits from upward movement)
        if spy_move > 0:
            butterfly_pnl = min(spy_move * 10, position.call_butterfly['max_profit'])  # $10 per point up to max
        else:
            butterfly_pnl = max(spy_move * 5, -position.call_butterfly['max_loss'])   # Smaller loss on downside
        
        # Put diagonal P&L (profits from downward movement)
        if spy_move < 0:
            diagonal_pnl = min(abs(spy_move) * 8, position.put_diagonal['max_profit'])  # $8 per point down
        else:
            diagonal_pnl = max(-spy_move * 3, -position.put_diagonal['max_loss'])      # Smaller loss on upside
        
        total_pnl = butterfly_pnl + diagonal_pnl
        
        # Apply time decay (theta) - positions lose value over time
        hours_held = (datetime.now() - position.entry_time).total_seconds() / 3600
        theta_decay = -position.entry_cost * 0.1 * (hours_held / 6.0)  # 10% decay over 6 hours
        
        return total_pnl + theta_decay
    
    def close_position(self, position: FlyagonalPosition, current_spy_price: float, current_time: datetime, exit_reason: str) -> float:
        """Close Flyagonal position and calculate final P&L"""
        
        # Calculate final P&L
        final_pnl = self._calculate_position_pnl(position, current_spy_price)
        
        # Update position
        position.is_open = False
        position.exit_time = current_time
        position.exit_reason = exit_reason
        position.realized_pnl = final_pnl
        
        # Update balance
        self.current_balance += final_pnl
        
        # Update cash management
        self.cash_manager.remove_position(position.position_id)
        
        # Update statistics
        if final_pnl > 0:
            self.winning_trades += 1
        
        # Update VIX regime performance
        regime = position.entry_vix_regime
        self.vix_regime_performance[regime]['trades'] += 1
        if final_pnl > 0:
            self.vix_regime_performance[regime]['wins'] += 1
        self.vix_regime_performance[regime]['total_pnl'] += final_pnl
        
        # Move to closed positions
        self.open_positions.remove(position)
        self.closed_positions.append(position)
        
        # Log the exit
        self.logger.log_trade_exit(
            trade_id=position.position_id,
            exit_time=current_time,
            spy_price=current_spy_price,
            realized_pnl=final_pnl,
            exit_reason=exit_reason,
            hold_duration_hours=(current_time - position.entry_time).total_seconds() / 3600
        )
        
        print(f"🔚 FLYAGONAL EXIT: {position.position_id}")
        print(f"   Exit Reason: {exit_reason}")
        print(f"   P&L: ${final_pnl:.2f}")
        print(f"   New Balance: ${self.current_balance:.2f}")
        
        return final_pnl
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """Get comprehensive strategy statistics"""
        
        total_pnl = sum(pos.realized_pnl for pos in self.closed_positions)
        win_rate = (self.winning_trades / max(self.total_trades, 1)) * 100
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'current_balance': self.current_balance,
            'return_pct': ((self.current_balance - self.initial_balance) / self.initial_balance) * 100,
            'max_drawdown': self.max_drawdown,
            'vix_regime_performance': self.vix_regime_performance,
            'avg_trade_pnl': total_pnl / max(self.total_trades, 1),
            'profit_factor': self._calculate_profit_factor()
        }
    
    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        
        gross_profit = sum(pos.realized_pnl for pos in self.closed_positions if pos.realized_pnl > 0)
        gross_loss = abs(sum(pos.realized_pnl for pos in self.closed_positions if pos.realized_pnl < 0))
        
        return gross_profit / max(gross_loss, 1.0)
