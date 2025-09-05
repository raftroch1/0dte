#!/usr/bin/env python3
"""
Automated Risk Management System - Inspired by ChatGPT Micro-Cap Experiment
===========================================================================

COMPREHENSIVE RISK MANAGEMENT FOR 0DTE OPTIONS TRADING:
1. Real-time stop-loss automation (from ChatGPT repo patterns)
2. Position size validation before trades
3. Daily risk limit monitoring ($400 max loss, $250 target)
4. Portfolio concentration checks
5. Cash constraint validation
6. Emergency position management

This system provides the automated risk controls that the ChatGPT repo
demonstrated for stock trading, adapted for 0DTE options strategies.

Location: src/utils/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Risk Management System
Inspired by: ChatGPT Micro-Cap Experiment risk management patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import json

# Import existing types and utilities (following .cursorrules integration)
from .detailed_logger import TradeLogEntry

logger = logging.getLogger(__name__)

@dataclass
class RiskLimits:
    """Risk limit configuration - inspired by ChatGPT repo's risk controls"""
    # Daily Risk Limits (from your system requirements)
    max_daily_loss: float = 400.0          # $400 max daily loss
    max_daily_profit: float = 250.0        # $250 daily target
    max_risk_per_trade_pct: float = 0.016  # 1.6% max risk per trade
    
    # Position Limits
    max_concurrent_positions: int = 4       # Max 4 positions at once
    max_position_concentration: float = 0.25 # 25% max in single position
    
    # Stop Loss Configuration (from ChatGPT repo patterns)
    profit_target_pct: float = 0.25        # 25% profit target
    trailing_stop_pct: float = 0.15        # 15% trailing stop activation
    stop_loss_multiplier: float = 1.2      # 1.2x premium stop loss
    
    # Emergency Limits
    max_account_drawdown: float = 0.20     # 20% max account drawdown
    emergency_stop_loss: float = 0.15      # 15% emergency account stop

@dataclass
class PositionRisk:
    """Position risk metrics - following ChatGPT repo's position tracking"""
    position_id: str
    strategy_type: str
    entry_time: datetime
    current_value: float
    max_risk: float
    max_profit: float
    unrealized_pnl: float
    risk_pct: float
    stop_loss_price: float
    profit_target_price: float
    is_stop_triggered: bool = False
    is_profit_target_hit: bool = False

@dataclass
class RiskMetrics:
    """Real-time risk metrics - inspired by ChatGPT repo's performance tracking"""
    # Daily Metrics
    daily_pnl: float
    daily_trades: int
    daily_win_rate: float
    
    # Account Metrics  
    account_balance: float
    total_exposure: float
    available_cash: float
    account_drawdown: float
    
    # Risk Ratios
    risk_utilization: float     # % of daily risk used
    concentration_risk: float   # Largest position as % of account
    leverage_ratio: float       # Total exposure / account balance
    
    # Status Flags
    daily_limit_reached: bool
    emergency_stop_triggered: bool
    risk_warning_level: str     # 'GREEN', 'YELLOW', 'RED'

class RiskManager:
    """
    Automated Risk Management System
    
    Implements the sophisticated risk management patterns from the ChatGPT
    Micro-Cap experiment, adapted for 0DTE options trading strategies.
    
    Key Features (from ChatGPT repo):
    - Automated stop-loss execution
    - Real-time position monitoring  
    - Daily risk limit enforcement
    - Cash constraint validation
    - Emergency position management
    """
    
    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        """Initialize risk manager with configuration"""
        self.risk_limits = risk_limits or RiskLimits()
        self.positions: Dict[str, PositionRisk] = {}
        self.daily_trades: List[TradeLogEntry] = []
        self.risk_events: List[Dict[str, Any]] = []
        
        # Daily tracking (reset each trading day)
        self.daily_pnl = 0.0
        self.daily_trade_count = 0
        self.peak_daily_balance = 0.0
        self.starting_balance = 0.0
        
        logger.info("🛡️ AUTOMATED RISK MANAGER INITIALIZED")
        logger.info(f"   Max Daily Loss: ${self.risk_limits.max_daily_loss}")
        logger.info(f"   Daily Target: ${self.risk_limits.max_daily_profit}")
        logger.info(f"   Max Risk/Trade: {self.risk_limits.max_risk_per_trade_pct:.1%}")
        logger.info(f"   Max Positions: {self.risk_limits.max_concurrent_positions}")
    
    def reset_daily_metrics(self, starting_balance: float) -> None:
        """Reset daily tracking metrics - called at market open"""
        self.daily_pnl = 0.0
        self.daily_trade_count = 0
        self.starting_balance = starting_balance
        self.peak_daily_balance = starting_balance
        self.daily_trades.clear()
        
        logger.info(f"📅 Daily risk metrics reset - Starting balance: ${starting_balance:,.2f}")
    
    def validate_new_position(self, 
                            strategy_type: str,
                            contracts: int,
                            premium_collected: float,
                            max_risk: float,
                            current_balance: float) -> Tuple[bool, str]:
        """
        Validate new position against risk limits
        
        Implements the position validation logic from ChatGPT repo's
        cash constraint checking and position sizing validation.
        
        Returns:
            (is_valid, reason)
        """
        
        # 1. Cash constraint check (from ChatGPT repo pattern)
        required_margin = max_risk  # Simplified for 0DTE
        if required_margin > current_balance:
            return False, f"Insufficient cash: need ${required_margin:,.2f}, have ${current_balance:,.2f}"
        
        # 2. Daily risk limit check
        risk_amount = max_risk
        if self.daily_pnl - risk_amount < -self.risk_limits.max_daily_loss:
            return False, f"Would exceed daily loss limit: ${self.risk_limits.max_daily_loss}"
        
        # 3. Per-trade risk limit
        risk_pct = risk_amount / current_balance
        if risk_pct > self.risk_limits.max_risk_per_trade_pct:
            return False, f"Exceeds per-trade risk limit: {risk_pct:.1%} > {self.risk_limits.max_risk_per_trade_pct:.1%}"
        
        # 4. Position count limit
        active_positions = len([p for p in self.positions.values() if not p.is_stop_triggered])
        if active_positions >= self.risk_limits.max_concurrent_positions:
            return False, f"Max concurrent positions reached: {active_positions}/{self.risk_limits.max_concurrent_positions}"
        
        # 5. Concentration limit
        position_size = contracts * premium_collected
        concentration = position_size / current_balance
        if concentration > self.risk_limits.max_position_concentration:
            return False, f"Exceeds concentration limit: {concentration:.1%} > {self.risk_limits.max_position_concentration:.1%}"
        
        return True, "Position validated - all risk checks passed"
    
    def add_position(self,
                    position_id: str,
                    strategy_type: str,
                    contracts: int,
                    premium_collected: float,
                    max_risk: float,
                    max_profit: float,
                    entry_time: Optional[datetime] = None) -> bool:
        """
        Add new position to risk monitoring
        
        Implements position tracking similar to ChatGPT repo's
        portfolio management system.
        """
        
        if entry_time is None:
            entry_time = datetime.now()
        
        # Calculate stop-loss and profit target prices (adapted from ChatGPT repo)
        stop_loss_price = premium_collected * self.risk_limits.stop_loss_multiplier
        profit_target_price = premium_collected * (1 - self.risk_limits.profit_target_pct)
        
        position_risk = PositionRisk(
            position_id=position_id,
            strategy_type=strategy_type,
            entry_time=entry_time,
            current_value=premium_collected * contracts,
            max_risk=max_risk,
            max_profit=max_profit,
            unrealized_pnl=0.0,
            risk_pct=max_risk / (self.starting_balance or 25000),
            stop_loss_price=stop_loss_price,
            profit_target_price=profit_target_price
        )
        
        self.positions[position_id] = position_risk
        self.daily_trade_count += 1
        
        logger.info(f"📊 Position added to risk monitoring: {position_id}")
        logger.info(f"   Strategy: {strategy_type}, Contracts: {contracts}")
        logger.info(f"   Max Risk: ${max_risk:.2f}, Stop Loss: ${stop_loss_price:.2f}")
        
        return True
    
    def update_position_pnl(self, position_id: str, current_pnl: float) -> Optional[str]:
        """
        Update position P&L and check for stop-loss triggers
        
        Implements the automated stop-loss system from ChatGPT repo's
        risk management framework.
        
        Returns:
            Action required ('STOP_LOSS', 'PROFIT_TARGET', 'TRAILING_STOP', None)
        """
        
        if position_id not in self.positions:
            logger.warning(f"Position {position_id} not found in risk monitoring")
            return None
        
        position = self.positions[position_id]
        position.unrealized_pnl = current_pnl
        
        # Update daily P&L
        self.daily_pnl += current_pnl - position.unrealized_pnl
        
        # Check stop-loss trigger (from ChatGPT repo pattern)
        if current_pnl <= -position.max_risk * self.risk_limits.stop_loss_multiplier:
            position.is_stop_triggered = True
            self._log_risk_event("STOP_LOSS_TRIGGERED", position_id, current_pnl)
            logger.warning(f"🚨 STOP LOSS TRIGGERED: {position_id} - Loss: ${current_pnl:.2f}")
            return "STOP_LOSS"
        
        # Check profit target (25% of max profit)
        profit_target = position.max_profit * self.risk_limits.profit_target_pct
        if current_pnl >= profit_target:
            position.is_profit_target_hit = True
            self._log_risk_event("PROFIT_TARGET_HIT", position_id, current_pnl)
            logger.info(f"🎯 PROFIT TARGET HIT: {position_id} - Profit: ${current_pnl:.2f}")
            return "PROFIT_TARGET"
        
        # Check trailing stop (15% profit activation)
        trailing_activation = position.max_profit * self.risk_limits.trailing_stop_pct
        if current_pnl >= trailing_activation:
            # Implement trailing stop logic here if needed
            pass
        
        return None
    
    def check_daily_limits(self) -> Tuple[bool, str]:
        """
        Check if daily risk limits are breached
        
        Implements daily limit monitoring from ChatGPT repo's
        risk management system.
        """
        
        # Check daily loss limit
        if self.daily_pnl <= -self.risk_limits.max_daily_loss:
            self._log_risk_event("DAILY_LOSS_LIMIT", "ACCOUNT", self.daily_pnl)
            return False, f"Daily loss limit exceeded: ${self.daily_pnl:.2f}"
        
        # Check daily profit target (optional stop)
        if self.daily_pnl >= self.risk_limits.max_daily_profit:
            self._log_risk_event("DAILY_TARGET_REACHED", "ACCOUNT", self.daily_pnl)
            return True, f"Daily profit target reached: ${self.daily_pnl:.2f}"
        
        return True, "Within daily limits"
    
    def get_risk_metrics(self, current_balance: float) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics
        
        Provides real-time risk dashboard similar to ChatGPT repo's
        performance tracking system.
        """
        
        # Calculate active exposure
        total_exposure = sum(p.max_risk for p in self.positions.values() 
                           if not p.is_stop_triggered)
        
        # Calculate account drawdown
        account_drawdown = 0.0
        if self.starting_balance > 0:
            account_drawdown = max(0, (self.starting_balance - current_balance) / self.starting_balance)
        
        # Calculate concentration risk (largest position)
        concentration_risk = 0.0
        if self.positions and current_balance > 0:
            max_position_risk = max(p.max_risk for p in self.positions.values())
            concentration_risk = max_position_risk / current_balance
        
        # Determine risk warning level
        warning_level = "GREEN"
        if account_drawdown > 0.10 or abs(self.daily_pnl) > self.risk_limits.max_daily_loss * 0.75:
            warning_level = "YELLOW"
        if account_drawdown > 0.15 or abs(self.daily_pnl) > self.risk_limits.max_daily_loss * 0.90:
            warning_level = "RED"
        
        # Calculate win rate
        completed_trades = [p for p in self.positions.values() 
                          if p.is_stop_triggered or p.is_profit_target_hit]
        winning_trades = [p for p in completed_trades if p.unrealized_pnl > 0]
        daily_win_rate = len(winning_trades) / len(completed_trades) if completed_trades else 0.0
        
        return RiskMetrics(
            daily_pnl=self.daily_pnl,
            daily_trades=self.daily_trade_count,
            daily_win_rate=daily_win_rate,
            account_balance=current_balance,
            total_exposure=total_exposure,
            available_cash=current_balance - total_exposure,
            account_drawdown=account_drawdown,
            risk_utilization=abs(self.daily_pnl) / self.risk_limits.max_daily_loss,
            concentration_risk=concentration_risk,
            leverage_ratio=total_exposure / current_balance if current_balance > 0 else 0.0,
            daily_limit_reached=abs(self.daily_pnl) >= self.risk_limits.max_daily_loss,
            emergency_stop_triggered=account_drawdown >= self.risk_limits.emergency_stop_loss,
            risk_warning_level=warning_level
        )
    
    def close_position(self, position_id: str, final_pnl: float, reason: str) -> bool:
        """
        Close position and update risk tracking
        
        Implements position closure tracking from ChatGPT repo's
        trade logging system.
        """
        
        if position_id not in self.positions:
            logger.warning(f"Cannot close position {position_id}: not found")
            return False
        
        position = self.positions[position_id]
        
        # Update final P&L
        self.daily_pnl += final_pnl - position.unrealized_pnl
        
        # Log the closure
        self._log_risk_event("POSITION_CLOSED", position_id, final_pnl, reason)
        
        # Remove from active monitoring
        del self.positions[position_id]
        
        logger.info(f"📊 Position closed: {position_id}")
        logger.info(f"   Final P&L: ${final_pnl:.2f}, Reason: {reason}")
        logger.info(f"   Daily P&L: ${self.daily_pnl:.2f}")
        
        return True
    
    def emergency_stop_check(self, current_balance: float) -> Tuple[bool, str]:
        """
        Check for emergency stop conditions
        
        Implements emergency risk controls similar to ChatGPT repo's
        portfolio protection system.
        """
        
        # Account drawdown check
        if self.starting_balance > 0:
            drawdown = (self.starting_balance - current_balance) / self.starting_balance
            if drawdown >= self.risk_limits.emergency_stop_loss:
                return True, f"Emergency stop: Account drawdown {drawdown:.1%} >= {self.risk_limits.emergency_stop_loss:.1%}"
        
        # Daily loss check
        if self.daily_pnl <= -self.risk_limits.max_daily_loss:
            return True, f"Emergency stop: Daily loss ${self.daily_pnl:.2f} >= ${self.risk_limits.max_daily_loss}"
        
        return False, "No emergency conditions"
    
    def _log_risk_event(self, event_type: str, position_id: str, 
                       amount: float, reason: str = "") -> None:
        """Log risk management events for audit trail"""
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'position_id': position_id,
            'amount': amount,
            'reason': reason,
            'daily_pnl': self.daily_pnl,
            'active_positions': len(self.positions)
        }
        
        self.risk_events.append(event)
        
        # Log to file for audit trail
        risk_log_path = Path("logs/risk_events.jsonl")
        risk_log_path.parent.mkdir(exist_ok=True)
        
        with open(risk_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")
    
    def get_position_summary(self) -> pd.DataFrame:
        """
        Get summary of all active positions
        
        Provides position overview similar to ChatGPT repo's
        portfolio display system.
        """
        
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for pos_id, position in self.positions.items():
            data.append({
                'Position ID': pos_id,
                'Strategy': position.strategy_type,
                'Entry Time': position.entry_time.strftime('%H:%M:%S'),
                'Current Value': f"${position.current_value:.2f}",
                'Max Risk': f"${position.max_risk:.2f}",
                'Unrealized P&L': f"${position.unrealized_pnl:+.2f}",
                'Risk %': f"{position.risk_pct:.1%}",
                'Stop Loss': f"${position.stop_loss_price:.2f}",
                'Status': 'STOPPED' if position.is_stop_triggered else 'ACTIVE'
            })
        
        return pd.DataFrame(data)
    
    def print_risk_dashboard(self, current_balance: float) -> None:
        """
        Print comprehensive risk dashboard
        
        Displays risk metrics similar to ChatGPT repo's
        daily results system.
        """
        
        metrics = self.get_risk_metrics(current_balance)
        
        print("\n" + "=" * 60)
        print("🛡️  AUTOMATED RISK MANAGEMENT DASHBOARD")
        print("=" * 60)
        
        # Daily Performance
        print(f"\n📊 DAILY PERFORMANCE:")
        print(f"   Daily P&L: ${metrics.daily_pnl:+.2f}")
        print(f"   Daily Target: ${self.risk_limits.max_daily_profit:.2f}")
        print(f"   Target Progress: {(metrics.daily_pnl / self.risk_limits.max_daily_profit * 100):+.1f}%")
        print(f"   Trades Today: {metrics.daily_trades}")
        print(f"   Win Rate: {metrics.daily_win_rate:.1%}")
        
        # Risk Metrics
        print(f"\n🚨 RISK METRICS:")
        print(f"   Risk Utilization: {metrics.risk_utilization:.1%}")
        print(f"   Account Drawdown: {metrics.account_drawdown:.1%}")
        print(f"   Concentration Risk: {metrics.concentration_risk:.1%}")
        print(f"   Warning Level: {metrics.risk_warning_level}")
        
        # Account Status
        print(f"\n💰 ACCOUNT STATUS:")
        print(f"   Balance: ${metrics.account_balance:,.2f}")
        print(f"   Total Exposure: ${metrics.total_exposure:,.2f}")
        print(f"   Available Cash: ${metrics.available_cash:,.2f}")
        print(f"   Active Positions: {len(self.positions)}")
        
        # Risk Limits
        print(f"\n⚠️  RISK LIMITS:")
        print(f"   Daily Loss Limit: ${self.risk_limits.max_daily_loss:.2f}")
        print(f"   Remaining Risk: ${self.risk_limits.max_daily_loss + metrics.daily_pnl:.2f}")
        print(f"   Max Positions: {self.risk_limits.max_concurrent_positions}")
        print(f"   Emergency Stop: {metrics.emergency_stop_triggered}")
        
        # Active Positions
        if self.positions:
            print(f"\n📋 ACTIVE POSITIONS:")
            position_df = self.get_position_summary()
            print(position_df.to_string(index=False))

# Example usage and integration patterns
if __name__ == "__main__":
    """
    Example usage of the Risk Manager
    
    Demonstrates integration patterns from ChatGPT repo
    """
    
    # Initialize risk manager with custom limits
    risk_limits = RiskLimits(
        max_daily_loss=400.0,
        max_daily_profit=250.0,
        max_risk_per_trade_pct=0.016
    )
    
    risk_manager = RiskManager(risk_limits)
    
    # Start of trading day
    starting_balance = 25000.0
    risk_manager.reset_daily_metrics(starting_balance)
    
    # Validate new position
    is_valid, reason = risk_manager.validate_new_position(
        strategy_type="IRON_CONDOR",
        contracts=2,
        premium_collected=100.0,
        max_risk=300.0,
        current_balance=starting_balance
    )
    
    print(f"Position validation: {is_valid} - {reason}")
    
    if is_valid:
        # Add position to monitoring
        risk_manager.add_position(
            position_id="IC_001",
            strategy_type="IRON_CONDOR", 
            contracts=2,
            premium_collected=100.0,
            max_risk=300.0,
            max_profit=200.0
        )
        
        # Simulate P&L update
        action = risk_manager.update_position_pnl("IC_001", -50.0)
        print(f"Risk action required: {action}")
        
        # Display risk dashboard
        risk_manager.print_risk_dashboard(starting_balance - 50)
