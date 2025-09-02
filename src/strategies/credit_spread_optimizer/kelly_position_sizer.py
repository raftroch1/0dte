#!/usr/bin/env python3
"""
Kelly Criterion Position Sizer
==============================

Professional-grade position sizing using Kelly Criterion for optimal risk allocation.
Designed for credit spread trading with $25k account targeting $200/day.

Following @.cursorrules architecture patterns.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from .config import CreditSpreadConfig, KellyCriterionConfig

@dataclass
class TradeResult:
    """Individual trade result for Kelly calculation"""
    timestamp: datetime
    strategy_type: str
    pnl: float
    premium_collected: float
    was_winner: bool
    hold_time_hours: float

@dataclass
class KellyMetrics:
    """Kelly Criterion calculation results"""
    kelly_fraction: float
    win_rate: float
    avg_win: float
    avg_loss: float
    expected_value: float
    confidence_score: float
    recommended_contracts: int
    max_risk_dollars: float

class KellyPositionSizer:
    """
    Kelly Criterion-based position sizing for credit spreads
    
    Optimizes position size based on:
    - Historical win rate
    - Average win/loss amounts  
    - Current account balance
    - Risk management constraints
    """
    
    def __init__(self, config: CreditSpreadConfig, kelly_config: KellyCriterionConfig):
        self.config = config
        self.kelly_config = kelly_config
        self.trade_history: List[TradeResult] = []
        
        # Performance tracking
        self.current_win_rate = kelly_config.estimated_win_rate
        self.current_avg_win = kelly_config.estimated_avg_win
        self.current_avg_loss = kelly_config.estimated_avg_loss
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🎯 KELLY POSITION SIZER INITIALIZED")
        self.logger.info(f"   Target Win Rate: {self.current_win_rate*100:.1f}%")
        self.logger.info(f"   Estimated Avg Win: ${self.current_avg_win:.2f}")
        self.logger.info(f"   Estimated Avg Loss: ${self.current_avg_loss:.2f}")
    
    def calculate_optimal_position_size(
        self,
        account_balance: float,
        premium_collected: float,
        max_loss: float,
        strategy_type: str = "CREDIT_SPREAD",
        current_daily_pnl: float = 0.0
    ) -> KellyMetrics:
        """
        Calculate optimal position size using Kelly Criterion
        
        Args:
            account_balance: Current account balance
            premium_collected: Premium collected per contract
            max_loss: Maximum loss per contract
            strategy_type: Type of strategy being traded
            current_daily_pnl: Current daily P&L
            
        Returns:
            KellyMetrics with recommended position size
        """
        
        # Update performance metrics from recent trades
        self._update_performance_metrics(strategy_type)
        
        # Calculate Kelly fraction
        kelly_fraction = self._calculate_kelly_fraction(
            self.current_win_rate,
            self.current_avg_win,
            self.current_avg_loss
        )
        
        # Apply safety constraints
        kelly_fraction = self._apply_safety_constraints(
            kelly_fraction, account_balance, current_daily_pnl
        )
        
        # Calculate position size in contracts
        max_risk_dollars = account_balance * self.config.max_risk_per_trade_pct
        kelly_risk_dollars = account_balance * kelly_fraction
        
        # Use the more conservative of Kelly or max risk limit
        actual_risk_dollars = min(max_risk_dollars, kelly_risk_dollars)
        
        # Calculate contracts based on max loss per contract
        if max_loss > 0:
            recommended_contracts = int(actual_risk_dollars / max_loss)
        else:
            recommended_contracts = 1  # Fallback
        
        # Ensure minimum position size
        recommended_contracts = max(1, recommended_contracts)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score()
        
        # Expected value calculation
        expected_value = (
            self.current_win_rate * self.current_avg_win - 
            (1 - self.current_win_rate) * self.current_avg_loss
        )
        
        metrics = KellyMetrics(
            kelly_fraction=kelly_fraction,
            win_rate=self.current_win_rate,
            avg_win=self.current_avg_win,
            avg_loss=self.current_avg_loss,
            expected_value=expected_value,
            confidence_score=confidence_score,
            recommended_contracts=recommended_contracts,
            max_risk_dollars=actual_risk_dollars
        )
        
        self.logger.info(f"🎯 KELLY POSITION SIZING:")
        self.logger.info(f"   Kelly Fraction: {kelly_fraction*100:.2f}%")
        self.logger.info(f"   Recommended Contracts: {recommended_contracts}")
        self.logger.info(f"   Max Risk: ${actual_risk_dollars:.2f}")
        self.logger.info(f"   Expected Value: ${expected_value:.2f}")
        self.logger.info(f"   Confidence: {confidence_score*100:.1f}%")
        
        return metrics
    
    def _calculate_kelly_fraction(
        self, 
        win_rate: float, 
        avg_win: float, 
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly fraction using the formula:
        f = (bp - q) / b
        
        Where:
        - b = odds received on the wager (avg_win / avg_loss)
        - p = probability of winning (win_rate)
        - q = probability of losing (1 - win_rate)
        """
        
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return self.kelly_config.min_kelly_fraction
        
        # Calculate odds (how much you win vs how much you lose)
        odds = avg_win / avg_loss
        
        # Kelly formula
        kelly_fraction = (odds * win_rate - (1 - win_rate)) / odds
        
        # Ensure positive and within bounds
        kelly_fraction = max(0, kelly_fraction)
        kelly_fraction = min(self.kelly_config.max_kelly_fraction, kelly_fraction)
        
        # Apply conservative adjustment
        kelly_fraction *= self.kelly_config.kelly_adjustment_factor
        
        return kelly_fraction
    
    def _apply_safety_constraints(
        self, 
        kelly_fraction: float, 
        account_balance: float,
        current_daily_pnl: float
    ) -> float:
        """Apply additional safety constraints to Kelly fraction"""
        
        # Reduce position size if daily losses are mounting
        if current_daily_pnl < -100:  # If down $100+ today
            daily_loss_factor = max(0.5, 1 + (current_daily_pnl / 400))  # Scale down
            kelly_fraction *= daily_loss_factor
            self.logger.info(f"   📉 Daily Loss Adjustment: {daily_loss_factor:.2f}x")
        
        # Reduce position size if approaching daily limit
        daily_loss_remaining = abs(self.config.daily_loss_limit + current_daily_pnl)
        if daily_loss_remaining < 200:  # Within $200 of daily limit
            limit_factor = daily_loss_remaining / 200
            kelly_fraction *= limit_factor
            self.logger.info(f"   ⚠️  Daily Limit Adjustment: {limit_factor:.2f}x")
        
        # Ensure within absolute bounds
        kelly_fraction = max(self.kelly_config.min_kelly_fraction, kelly_fraction)
        kelly_fraction = min(self.config.max_risk_per_trade_pct, kelly_fraction)
        
        return kelly_fraction
    
    def _update_performance_metrics(self, strategy_type: str) -> None:
        """Update performance metrics from recent trade history"""
        
        if len(self.trade_history) < self.kelly_config.min_trades_for_kelly:
            # Not enough history, use estimates
            return
        
        # Filter recent trades
        cutoff_date = datetime.now() - timedelta(days=self.kelly_config.lookback_period_days)
        recent_trades = [
            trade for trade in self.trade_history 
            if trade.timestamp >= cutoff_date and trade.strategy_type == strategy_type
        ]
        
        if len(recent_trades) < 10:  # Need minimum sample size
            return
        
        # Calculate actual performance metrics
        wins = [trade for trade in recent_trades if trade.was_winner]
        losses = [trade for trade in recent_trades if not trade.was_winner]
        
        if wins and losses:
            self.current_win_rate = len(wins) / len(recent_trades)
            self.current_avg_win = np.mean([trade.pnl for trade in wins])
            self.current_avg_loss = abs(np.mean([trade.pnl for trade in losses]))
            
            self.logger.info(f"📊 UPDATED PERFORMANCE METRICS ({len(recent_trades)} trades):")
            self.logger.info(f"   Win Rate: {self.current_win_rate*100:.1f}%")
            self.logger.info(f"   Avg Win: ${self.current_avg_win:.2f}")
            self.logger.info(f"   Avg Loss: ${self.current_avg_loss:.2f}")
    
    def _calculate_confidence_score(self) -> float:
        """Calculate confidence in the Kelly calculation"""
        
        if len(self.trade_history) < self.kelly_config.min_trades_for_kelly:
            return 0.5  # Low confidence with limited data
        
        # Factors affecting confidence
        sample_size_factor = min(1.0, len(self.trade_history) / 100)  # More trades = higher confidence
        
        # Consistency factor (lower variance = higher confidence)
        recent_pnls = [trade.pnl for trade in self.trade_history[-30:]]  # Last 30 trades
        if len(recent_pnls) > 5:
            pnl_std = np.std(recent_pnls)
            avg_pnl = np.mean([abs(pnl) for pnl in recent_pnls])
            consistency_factor = max(0.3, 1 - (pnl_std / max(avg_pnl, 1)))
        else:
            consistency_factor = 0.5
        
        # Win rate stability factor
        if self.current_win_rate > 0.6 and self.current_win_rate < 0.9:
            win_rate_factor = 1.0  # Reasonable win rate
        else:
            win_rate_factor = 0.7  # Extreme win rates are less reliable
        
        confidence = sample_size_factor * consistency_factor * win_rate_factor
        return min(1.0, confidence)
    
    def add_trade_result(
        self,
        timestamp: datetime,
        strategy_type: str,
        pnl: float,
        premium_collected: float,
        hold_time_hours: float = 0.0
    ) -> None:
        """Add a trade result to the history for Kelly calculation updates"""
        
        trade_result = TradeResult(
            timestamp=timestamp,
            strategy_type=strategy_type,
            pnl=pnl,
            premium_collected=premium_collected,
            was_winner=pnl > 0,
            hold_time_hours=hold_time_hours
        )
        
        self.trade_history.append(trade_result)
        
        # Keep only recent history to avoid memory issues
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-500:]  # Keep last 500 trades
    
    def get_position_size_recommendation(
        self,
        account_balance: float,
        premium_per_contract: float,
        max_loss_per_contract: float,
        current_positions: int = 0,
        current_daily_pnl: float = 0.0
    ) -> Dict[str, any]:
        """
        Get comprehensive position size recommendation
        
        Returns:
            Dictionary with recommendation details
        """
        
        # Check if we can trade (position limits, daily limits, etc.)
        can_trade, reason = self._can_add_position(
            current_positions, current_daily_pnl, account_balance
        )
        
        if not can_trade:
            return {
                'can_trade': False,
                'reason': reason,
                'recommended_contracts': 0,
                'max_risk': 0.0
            }
        
        # Calculate Kelly metrics
        kelly_metrics = self.calculate_optimal_position_size(
            account_balance=account_balance,
            premium_collected=premium_per_contract,
            max_loss=max_loss_per_contract,
            current_daily_pnl=current_daily_pnl
        )
        
        return {
            'can_trade': True,
            'recommended_contracts': kelly_metrics.recommended_contracts,
            'max_risk': kelly_metrics.max_risk_dollars,
            'kelly_fraction': kelly_metrics.kelly_fraction,
            'expected_value': kelly_metrics.expected_value,
            'confidence': kelly_metrics.confidence_score,
            'win_rate': kelly_metrics.win_rate,
            'reason': f"Kelly optimal: {kelly_metrics.recommended_contracts} contracts"
        }
    
    def _can_add_position(
        self, 
        current_positions: int, 
        current_daily_pnl: float,
        account_balance: float
    ) -> Tuple[bool, str]:
        """Check if we can add another position"""
        
        # Position limit check
        if current_positions >= self.config.max_concurrent_positions:
            return False, f"Max positions reached ({self.config.max_concurrent_positions})"
        
        # Daily loss limit check
        if current_daily_pnl <= self.config.daily_loss_limit:
            return False, f"Daily loss limit reached (${self.config.daily_loss_limit})"
        
        # Daily profit target check
        if current_daily_pnl >= self.config.daily_profit_target:
            return False, f"Daily profit target reached (${self.config.daily_profit_target})"
        
        # Account balance check
        if account_balance < 5000:  # Minimum account size
            return False, "Account balance too low for trading"
        
        return True, "All checks passed"

def main():
    """Test the Kelly Position Sizer"""
    
    from .config import DEFAULT_CONFIG, KELLY_CONFIG
    
    print("🎯 TESTING KELLY POSITION SIZER")
    print("=" * 50)
    
    # Initialize sizer
    sizer = KellyPositionSizer(DEFAULT_CONFIG, KELLY_CONFIG)
    
    # Test position sizing
    recommendation = sizer.get_position_size_recommendation(
        account_balance=25000.0,
        premium_per_contract=40.0,  # $0.40 premium = $40 per contract
        max_loss_per_contract=120.0,  # $1.20 max loss = $120 per contract
        current_positions=1,
        current_daily_pnl=-50.0
    )
    
    print(f"📊 POSITION SIZE RECOMMENDATION:")
    for key, value in recommendation.items():
        print(f"   {key}: {value}")
    
    # Simulate some trades to test adaptation
    print(f"\n🔄 SIMULATING TRADE HISTORY:")
    
    # Add some winning trades
    for i in range(15):
        sizer.add_trade_result(
            timestamp=datetime.now() - timedelta(days=i),
            strategy_type="CREDIT_SPREAD",
            pnl=50.0,  # $50 win
            premium_collected=40.0
        )
    
    # Add some losing trades
    for i in range(5):
        sizer.add_trade_result(
            timestamp=datetime.now() - timedelta(days=i+15),
            strategy_type="CREDIT_SPREAD", 
            pnl=-100.0,  # $100 loss
            premium_collected=40.0
        )
    
    # Test updated recommendation
    updated_recommendation = sizer.get_position_size_recommendation(
        account_balance=25000.0,
        premium_per_contract=40.0,
        max_loss_per_contract=120.0,
        current_positions=1,
        current_daily_pnl=-50.0
    )
    
    print(f"\n📊 UPDATED RECOMMENDATION (after trade history):")
    for key, value in updated_recommendation.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main()
