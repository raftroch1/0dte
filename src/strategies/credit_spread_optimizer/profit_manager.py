#!/usr/bin/env python3
"""
Profit Management System
========================

Professional profit taking and risk management for credit spreads.
Implements 50% profit target, trailing stops, and time-based exits.

Following @.cursorrules architecture patterns.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta, time
import logging
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from .config import CreditSpreadConfig

@dataclass
class Position:
    """Active credit spread position"""
    position_id: str
    strategy_type: str  # 'BULL_PUT_SPREAD' or 'BEAR_CALL_SPREAD'
    entry_time: datetime
    expiration_date: datetime
    contracts: int
    
    # Strike and premium info
    short_strike: float
    long_strike: float
    premium_collected: float  # Total premium collected
    
    # Current status
    current_value: float = 0.0
    unrealized_pnl: float = 0.0
    
    # Exit management
    profit_target: float = 0.0
    stop_loss: float = 0.0
    trailing_stop: float = 0.0
    highest_profit: float = 0.0
    
    # Flags
    is_closed: bool = False
    exit_reason: str = ""
    exit_time: Optional[datetime] = None

@dataclass
class ExitSignal:
    """Exit signal recommendation"""
    should_exit: bool
    exit_reason: str
    exit_type: str  # 'PROFIT_TARGET', 'STOP_LOSS', 'TRAILING_STOP', 'TIME_DECAY', 'FORCE_CLOSE'
    urgency: str    # 'LOW', 'MEDIUM', 'HIGH', 'IMMEDIATE'
    expected_pnl: float
    confidence: float

class ProfitManager:
    """
    Professional profit management system for credit spreads
    
    Features:
    - 50% profit target system
    - Trailing stop loss at 25% profit
    - Time-based exits before expiration
    - Force close before market close
    - Dynamic risk adjustment
    """
    
    def __init__(self, config: CreditSpreadConfig):
        self.config = config
        self.active_positions: Dict[str, Position] = {}
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("💰 PROFIT MANAGER INITIALIZED")
        self.logger.info(f"   Profit Target: {config.profit_target_pct*100:.0f}% of max profit")
        self.logger.info(f"   Trailing Stop: {config.trailing_stop_pct*100:.0f}% profit threshold")
        self.logger.info(f"   Stop Loss: {config.stop_loss_multiplier:.1f}x premium collected")
    
    def add_position(
        self,
        position_id: str,
        strategy_type: str,
        entry_time: datetime,
        expiration_date: datetime,
        contracts: int,
        short_strike: float,
        long_strike: float,
        premium_collected: float
    ) -> None:
        """Add a new position to management"""
        
        # Calculate profit target and stop loss
        max_profit = premium_collected  # For credit spreads, max profit = premium collected
        profit_target = max_profit * self.config.profit_target_pct
        stop_loss = premium_collected * self.config.stop_loss_multiplier
        
        position = Position(
            position_id=position_id,
            strategy_type=strategy_type,
            entry_time=entry_time,
            expiration_date=expiration_date,
            contracts=contracts,
            short_strike=short_strike,
            long_strike=long_strike,
            premium_collected=premium_collected,
            profit_target=profit_target,
            stop_loss=stop_loss
        )
        
        self.active_positions[position_id] = position
        
        self.logger.info(f"📈 NEW POSITION ADDED: {position_id}")
        self.logger.info(f"   Strategy: {strategy_type}")
        self.logger.info(f"   Contracts: {contracts}")
        self.logger.info(f"   Premium Collected: ${premium_collected:.2f}")
        self.logger.info(f"   Profit Target: ${profit_target:.2f}")
        self.logger.info(f"   Stop Loss: ${stop_loss:.2f}")
    
    def update_position_value(
        self,
        position_id: str,
        current_value: float,
        current_time: datetime
    ) -> None:
        """Update the current market value of a position"""
        
        if position_id not in self.active_positions:
            return
        
        position = self.active_positions[position_id]
        position.current_value = current_value
        
        # Calculate unrealized P&L (for credit spreads: collected premium - current value)
        position.unrealized_pnl = position.premium_collected - current_value
        
        # Track highest profit for trailing stop
        if position.unrealized_pnl > position.highest_profit:
            position.highest_profit = position.unrealized_pnl
            
            # Update trailing stop if we've hit the threshold
            if position.highest_profit >= position.premium_collected * self.config.trailing_stop_pct:
                # Set trailing stop at 75% of highest profit achieved
                position.trailing_stop = position.highest_profit * 0.75
                
                self.logger.debug(f"📊 {position_id}: Trailing stop updated to ${position.trailing_stop:.2f}")
    
    def check_exit_conditions(
        self,
        position_id: str,
        current_time: datetime,
        market_data: Optional[Dict] = None
    ) -> ExitSignal:
        """
        Check if position should be exited based on profit/loss/time conditions
        
        Args:
            position_id: Position to check
            current_time: Current market time
            market_data: Optional market data for enhanced decision making
            
        Returns:
            ExitSignal with recommendation
        """
        
        if position_id not in self.active_positions:
            return ExitSignal(False, "Position not found", "", "LOW", 0.0, 0.0)
        
        position = self.active_positions[position_id]
        
        if position.is_closed:
            return ExitSignal(False, "Position already closed", "", "LOW", 0.0, 0.0)
        
        # Check various exit conditions in order of priority
        
        # 1. FORCE CLOSE - Market closing soon
        force_close_signal = self._check_force_close(position, current_time)
        if force_close_signal.should_exit:
            return force_close_signal
        
        # 2. PROFIT TARGET - 50% of max profit achieved
        profit_target_signal = self._check_profit_target(position)
        if profit_target_signal.should_exit:
            return profit_target_signal
        
        # 3. STOP LOSS - 2x premium collected loss
        stop_loss_signal = self._check_stop_loss(position)
        if stop_loss_signal.should_exit:
            return stop_loss_signal
        
        # 4. TRAILING STOP - Profit giving back
        trailing_stop_signal = self._check_trailing_stop(position)
        if trailing_stop_signal.should_exit:
            return trailing_stop_signal
        
        # 5. TIME DECAY - Approaching expiration
        time_decay_signal = self._check_time_decay(position, current_time)
        if time_decay_signal.should_exit:
            return time_decay_signal
        
        # No exit conditions met
        return ExitSignal(
            should_exit=False,
            exit_reason="No exit conditions met",
            exit_type="HOLD",
            urgency="LOW",
            expected_pnl=position.unrealized_pnl,
            confidence=0.8
        )
    
    def _check_force_close(self, position: Position, current_time: datetime) -> ExitSignal:
        """Check if position must be force closed due to market close"""
        
        current_time_only = current_time.time()
        
        # Force close 30 minutes before market close
        if current_time_only >= self.config.force_close_time:
            return ExitSignal(
                should_exit=True,
                exit_reason="Market closing - force exit",
                exit_type="FORCE_CLOSE",
                urgency="IMMEDIATE",
                expected_pnl=position.unrealized_pnl,
                confidence=1.0
            )
        
        # Warning 15 minutes before force close
        warning_time = datetime.combine(
            current_time.date(), 
            self.config.force_close_time
        ) - timedelta(minutes=15)
        
        if current_time >= warning_time:
            return ExitSignal(
                should_exit=False,
                exit_reason="Approaching force close time",
                exit_type="WARNING",
                urgency="HIGH",
                expected_pnl=position.unrealized_pnl,
                confidence=0.9
            )
        
        return ExitSignal(False, "", "", "LOW", 0.0, 0.0)
    
    def _check_profit_target(self, position: Position) -> ExitSignal:
        """Check if 50% profit target has been reached"""
        
        if position.unrealized_pnl >= position.profit_target:
            return ExitSignal(
                should_exit=True,
                exit_reason=f"Profit target reached: ${position.unrealized_pnl:.2f} >= ${position.profit_target:.2f}",
                exit_type="PROFIT_TARGET",
                urgency="MEDIUM",
                expected_pnl=position.unrealized_pnl,
                confidence=0.95
            )
        
        # Check if we're close to profit target (within 10%)
        if position.unrealized_pnl >= position.profit_target * 0.9:
            return ExitSignal(
                should_exit=False,
                exit_reason="Approaching profit target",
                exit_type="NEAR_PROFIT_TARGET",
                urgency="MEDIUM",
                expected_pnl=position.unrealized_pnl,
                confidence=0.8
            )
        
        return ExitSignal(False, "", "", "LOW", 0.0, 0.0)
    
    def _check_stop_loss(self, position: Position) -> ExitSignal:
        """Check if stop loss has been hit"""
        
        # For credit spreads, loss occurs when current value > premium collected
        max_acceptable_loss = position.stop_loss
        
        if position.unrealized_pnl <= -max_acceptable_loss:
            return ExitSignal(
                should_exit=True,
                exit_reason=f"Stop loss hit: ${position.unrealized_pnl:.2f} <= ${-max_acceptable_loss:.2f}",
                exit_type="STOP_LOSS",
                urgency="HIGH",
                expected_pnl=position.unrealized_pnl,
                confidence=0.95
            )
        
        # Warning if approaching stop loss
        if position.unrealized_pnl <= -max_acceptable_loss * 0.8:
            return ExitSignal(
                should_exit=False,
                exit_reason="Approaching stop loss",
                exit_type="NEAR_STOP_LOSS",
                urgency="HIGH",
                expected_pnl=position.unrealized_pnl,
                confidence=0.85
            )
        
        return ExitSignal(False, "", "", "LOW", 0.0, 0.0)
    
    def _check_trailing_stop(self, position: Position) -> ExitSignal:
        """Check if trailing stop has been triggered"""
        
        # Only apply trailing stop if we've achieved the minimum profit threshold
        min_profit_for_trailing = position.premium_collected * self.config.trailing_stop_pct
        
        if position.highest_profit < min_profit_for_trailing:
            return ExitSignal(False, "", "", "LOW", 0.0, 0.0)
        
        # Check if current profit has fallen below trailing stop
        if position.trailing_stop > 0 and position.unrealized_pnl <= position.trailing_stop:
            return ExitSignal(
                should_exit=True,
                exit_reason=f"Trailing stop triggered: ${position.unrealized_pnl:.2f} <= ${position.trailing_stop:.2f}",
                exit_type="TRAILING_STOP",
                urgency="MEDIUM",
                expected_pnl=position.unrealized_pnl,
                confidence=0.9
            )
        
        return ExitSignal(False, "", "", "LOW", 0.0, 0.0)
    
    def _check_time_decay(self, position: Position, current_time: datetime) -> ExitSignal:
        """Check if position should be closed due to time decay considerations"""
        
        # Calculate time to expiration
        time_to_expiry = position.expiration_date - current_time
        hours_to_expiry = time_to_expiry.total_seconds() / 3600
        
        # Close positions with < 2 hours to expiration if not profitable
        if hours_to_expiry < 2 and position.unrealized_pnl < position.profit_target * 0.5:
            return ExitSignal(
                should_exit=True,
                exit_reason=f"Time decay exit: {hours_to_expiry:.1f} hours to expiry",
                exit_type="TIME_DECAY",
                urgency="MEDIUM",
                expected_pnl=position.unrealized_pnl,
                confidence=0.8
            )
        
        # Warning for positions approaching expiration
        if hours_to_expiry < 4:
            return ExitSignal(
                should_exit=False,
                exit_reason=f"Approaching expiration: {hours_to_expiry:.1f} hours remaining",
                exit_type="TIME_WARNING",
                urgency="MEDIUM",
                expected_pnl=position.unrealized_pnl,
                confidence=0.7
            )
        
        return ExitSignal(False, "", "", "LOW", 0.0, 0.0)
    
    def close_position(
        self,
        position_id: str,
        exit_reason: str,
        exit_time: datetime,
        final_pnl: float
    ) -> bool:
        """Close a position and record the final result"""
        
        if position_id not in self.active_positions:
            return False
        
        position = self.active_positions[position_id]
        position.is_closed = True
        position.exit_reason = exit_reason
        position.exit_time = exit_time
        position.unrealized_pnl = final_pnl
        
        self.logger.info(f"🔒 POSITION CLOSED: {position_id}")
        self.logger.info(f"   Exit Reason: {exit_reason}")
        self.logger.info(f"   Final P&L: ${final_pnl:.2f}")
        self.logger.info(f"   Hold Time: {exit_time - position.entry_time}")
        
        return True
    
    def get_active_positions(self) -> Dict[str, Position]:
        """Get all active (non-closed) positions"""
        return {
            pid: pos for pid, pos in self.active_positions.items() 
            if not pos.is_closed
        }
    
    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L across all active positions"""
        return sum(
            pos.unrealized_pnl for pos in self.active_positions.values()
            if not pos.is_closed
        )
    
    def get_position_count(self) -> int:
        """Get count of active positions"""
        return len(self.get_active_positions())
    
    def get_daily_performance_summary(self, target_date: datetime) -> Dict[str, any]:
        """Get performance summary for a specific day"""
        
        day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # Find positions closed on this day
        closed_today = [
            pos for pos in self.active_positions.values()
            if pos.exit_time and day_start <= pos.exit_time < day_end
        ]
        
        # Calculate daily metrics
        total_pnl = sum(pos.unrealized_pnl for pos in closed_today)
        total_trades = len(closed_today)
        winning_trades = len([pos for pos in closed_today if pos.unrealized_pnl > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'date': target_date.date(),
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'avg_pnl_per_trade': total_pnl / total_trades if total_trades > 0 else 0,
            'closed_positions': closed_today
        }

def main():
    """Test the Profit Manager"""
    
    from .config import DEFAULT_CONFIG
    
    print("💰 TESTING PROFIT MANAGER")
    print("=" * 50)
    
    # Initialize manager
    manager = ProfitManager(DEFAULT_CONFIG)
    
    # Add a test position
    entry_time = datetime.now()
    expiration = entry_time + timedelta(hours=6)  # 0DTE
    
    manager.add_position(
        position_id="TEST_001",
        strategy_type="BULL_PUT_SPREAD",
        entry_time=entry_time,
        expiration_date=expiration,
        contracts=5,
        short_strike=520.0,
        long_strike=515.0,
        premium_collected=200.0  # $200 total premium
    )
    
    # Test profit scenarios
    scenarios = [
        (150.0, "Initial position value"),
        (100.0, "Profit building"),
        (75.0, "Approaching profit target"),
        (50.0, "Profit target hit"),
        (60.0, "Profit giving back"),
        (300.0, "Stop loss scenario")
    ]
    
    print(f"\n📊 TESTING EXIT CONDITIONS:")
    
    for current_value, description in scenarios:
        manager.update_position_value("TEST_001", current_value, datetime.now())
        
        exit_signal = manager.check_exit_conditions("TEST_001", datetime.now())
        
        position = manager.active_positions["TEST_001"]
        
        print(f"\n{description}:")
        print(f"   Current Value: ${current_value:.2f}")
        print(f"   Unrealized P&L: ${position.unrealized_pnl:.2f}")
        print(f"   Should Exit: {exit_signal.should_exit}")
        print(f"   Exit Reason: {exit_signal.exit_reason}")
        print(f"   Urgency: {exit_signal.urgency}")
    
    # Test performance summary
    summary = manager.get_daily_performance_summary(datetime.now())
    print(f"\n📈 DAILY PERFORMANCE SUMMARY:")
    for key, value in summary.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main()
