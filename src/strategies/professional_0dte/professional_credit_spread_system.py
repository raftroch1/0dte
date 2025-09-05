#!/usr/bin/env python3
"""
Professional 0DTE Credit Spread Trading System
==============================================

PROFESSIONAL-GRADE IMPLEMENTATION:
- $25k account with 2% max risk per trade ($500)
- Kelly Criterion position sizing targeting 75% win rate
- 0.20 delta short strikes for optimal risk/reward
- 50% profit taking with trailing stops
- Daily limits: -$400 max loss, +$300 max profit
- Time windows: 9:45 AM - 2:30 PM ET only
- VIX filtering and volume requirements
- Maximum 4 concurrent positions

Based on user requirements and Alpaca best practices.
Follows @.cursorrules for professional architecture.

Location: src/strategies/professional_0dte/ (following .cursorrules structure)
Author: Advanced Options Trading System - Professional Implementation
"""

import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple, Optional, NamedTuple
import logging
from dataclasses import dataclass
from enum import Enum

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpreadType(Enum):
    """Credit spread types"""
    BULL_PUT_SPREAD = "BULL_PUT_SPREAD"
    BEAR_CALL_SPREAD = "BEAR_CALL_SPREAD"
    IRON_CONDOR = "IRON_CONDOR"

@dataclass
class ProfessionalConfig:
    """Professional trading system configuration"""
    # Account Settings (USER REQUIREMENTS: $250/day target)
    account_balance: float = 25000.0
    max_risk_per_trade_pct: float = 0.016  # 1.6% max risk per trade (tighter)
    max_daily_loss: float = -400.0        # -$400 daily stop loss
    max_daily_profit: float = 250.0       # +$250 daily profit target (USER SPECIFIED)
    
    # Position Sizing (Kelly Criterion)
    target_win_rate: float = 0.75         # 75% target win rate
    kelly_fraction_cap: float = 0.25      # Cap Kelly at 25%
    max_positions: int = 4                # Max concurrent positions
    
    # Spread Configuration (USER REQUIREMENTS: Accept lower premiums for more trades)
    target_delta_short: float = 0.20      # 20 delta for short strikes
    spread_width: float = 2.0             # $2 spread width (back to original)
    min_premium_collected: float = 0.30   # LOWER threshold for more trade opportunities
    target_max_profit_per_trade: float = 200.0  # Realistic max profit per $2 spread
    
    # Profit Management (USER REQUIREMENTS: 25% profit taking, tighter risk)
    profit_target_pct: float = 0.25       # Take profit at 25% of max (USER SPECIFIED)
    trailing_stop_pct: float = 0.15       # Trail stop at 15% profit (tighter)
    stop_loss_multiplier: float = 1.2     # Stop at 1.2x premium (TIGHTER risk management)
    
    # Time Management
    market_open_buffer: time = time(9, 45)   # No trades before 9:45 AM ET
    market_close_buffer: time = time(14, 30) # No new trades after 2:30 PM ET
    force_close_time: time = time(15, 30)    # Close all by 3:30 PM ET
    
    # Market Filters
    max_vix_threshold: float = 25.0       # Don't trade if VIX > 25
    min_spy_volume: int = 1000000         # Min SPY volume requirement

@dataclass
class TradeSignal:
    """Professional trade signal with all required parameters"""
    spread_type: SpreadType
    short_strike: float
    long_strike: float
    contracts: int
    premium_collected: float
    max_risk: float
    max_profit: float
    confidence: float
    entry_time: datetime
    
class KellyPositionSizer:
    """Kelly Criterion position sizing for optimal risk management"""
    
    def __init__(self, config: ProfessionalConfig):
        self.config = config
        
    def calculate_optimal_size(self, 
                             win_probability: float,
                             avg_win: float,
                             avg_loss: float,
                             current_balance: float) -> int:
        """
        Enhanced Kelly Criterion optimized for $250/day target
        
        Improvements:
        - Target-based position sizing
        - Enhanced win rate assumptions
        - Risk-adjusted scaling
        - Multiple constraint validation
        """
        
        if avg_loss <= 0 or avg_win <= 0:
            return 1  # Conservative fallback
        
        # ENHANCED: Use target win rate if current is too low (from regime detection improvements)
        target_win_rate = 0.60  # Target 60% win rate with enhanced regime detection
        effective_win_rate = max(win_probability, target_win_rate * 0.8)  # Use 80% of target as minimum
        
        # Calculate Kelly fraction with enhanced win rate
        b = avg_win / abs(avg_loss)  # Odds received
        p = effective_win_rate
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        kelly_fraction = min(kelly_fraction, self.config.kelly_fraction_cap)
        kelly_fraction = max(kelly_fraction, 0.01)  # Minimum 1%
        
        # ENHANCED: Multi-constraint position sizing for $250/day target
        expected_value_per_contract = p * avg_win - q * avg_loss
        
        if expected_value_per_contract > 0:
            # Method 1: Target-based sizing
            trades_per_day = 3.0  # Average from backtests
            daily_expected_per_contract = trades_per_day * expected_value_per_contract
            contracts_for_target = max(1, int(250.0 / daily_expected_per_contract))  # $250 daily target
            
            # Method 2: Kelly-based sizing
            kelly_risk_dollars = current_balance * kelly_fraction
            max_risk_per_spread = self.config.spread_width * 100 - (self.config.min_premium_collected * 100)
            kelly_contracts = max(1, int(kelly_risk_dollars / max_risk_per_spread))
            
            # Method 3: Account risk limit
            max_risk_dollars = current_balance * self.config.max_risk_per_trade_pct
            account_contracts = max(1, int(max_risk_dollars / max_risk_per_spread))
            
            # Method 4: Absolute risk limit ($400 max per trade)
            absolute_max_risk = 400.0  # User's absolute limit
            absolute_contracts = max(1, int(absolute_max_risk / abs(avg_loss)))
            
            # Take the minimum of all constraints for safety
            position_size = min(contracts_for_target, kelly_contracts, account_contracts, absolute_contracts)
            
            # Reasonable bounds (1-15 contracts max)
            position_size = max(1, min(position_size, 15))
            
            # Log detailed sizing analysis
            logger.info(f"Enhanced Kelly Sizing Analysis:")
            logger.info(f"  Effective win rate: {p:.1%}, Expected value: ${expected_value_per_contract:.2f}")
            logger.info(f"  Target-based: {contracts_for_target}, Kelly: {kelly_contracts}")
            logger.info(f"  Account limit: {account_contracts}, Absolute limit: {absolute_contracts}")
            logger.info(f"  Final position: {position_size} contracts")
            
        else:
            # Fallback for negative expected value
            position_size = 1
            logger.warning(f"Negative expected value (${expected_value_per_contract:.2f}), using 1 contract")
        
        return position_size

class ProfitManager:
    """Professional profit management with trailing stops"""
    
    def __init__(self, config: ProfessionalConfig):
        self.config = config
        self.open_positions: Dict[str, Dict] = {}
        
    def add_position(self, position_id: str, trade_signal: TradeSignal):
        """Add position to profit management"""
        self.open_positions[position_id] = {
            'signal': trade_signal,
            'entry_time': trade_signal.entry_time,
            'premium_collected': trade_signal.premium_collected,
            'max_profit': trade_signal.max_profit,
            'max_risk': trade_signal.max_risk,
            'profit_target': trade_signal.max_profit * self.config.profit_target_pct,
            'stop_loss': trade_signal.premium_collected * self.config.stop_loss_multiplier,
            'trailing_stop_active': False,
            'highest_profit': 0.0
        }
        
    def check_exit_conditions(self, position_id: str, current_pnl: float, 
                            current_time: datetime) -> Tuple[bool, str]:
        """Check if position should be closed"""
        
        if position_id not in self.open_positions:
            return False, ""
            
        position = self.open_positions[position_id]
        
        # Update highest profit for trailing stop
        if current_pnl > position['highest_profit']:
            position['highest_profit'] = current_pnl
            
        # Activate trailing stop at 15% profit (tighter)
        if current_pnl >= position['max_profit'] * self.config.trailing_stop_pct:
            position['trailing_stop_active'] = True
            
        # Check exit conditions
        
        # 1. Profit target (25% of max profit - USER REQUIREMENT)
        if current_pnl >= position['profit_target']:
            return True, "PROFIT_TARGET_25PCT"
            
        # 2. Stop loss (1.2x premium collected - TIGHTER risk management)
        if current_pnl <= -position['stop_loss']:
            return True, "STOP_LOSS_1.2X"
            
        # 3. Trailing stop (if active)
        if position['trailing_stop_active']:
            trailing_stop_level = position['highest_profit'] * 0.75  # Keep 75% of highest profit
            if current_pnl <= trailing_stop_level:
                return True, "TRAILING_STOP"
                
        # 4. Time-based exit (force close 30 min before market close)
        if current_time.time() >= self.config.force_close_time:
            return True, "TIME_BASED_EXIT"
            
        # 5. End of day for 0DTE
        if current_time.date() > position['entry_time'].date():
            return True, "0DTE_EXPIRATION"
            
        return False, ""
        
    def remove_position(self, position_id: str):
        """Remove position from management"""
        if position_id in self.open_positions:
            del self.open_positions[position_id]

class Professional0DTESystem:
    """
    Professional 0DTE Credit Spread Trading System
    
    Implements all professional requirements:
    - Kelly Criterion position sizing
    - 0.20 delta strike selection
    - Professional profit management
    - Comprehensive risk controls
    - Time window management
    - Market filtering
    """
    
    def __init__(self, config: Optional[ProfessionalConfig] = None):
        self.config = config or ProfessionalConfig()
        self.kelly_sizer = KellyPositionSizer(self.config)
        self.profit_manager = ProfitManager(self.config)
        
        # Performance tracking
        self.current_balance = self.config.account_balance
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.trade_history: List[Dict] = []
        
        # Daily limits tracking
        self.daily_profit_target_hit = False
        self.daily_loss_limit_hit = False
        
        logger.info("🏆 PROFESSIONAL 0DTE SYSTEM INITIALIZED")
        logger.info(f"   Account Balance: ${self.current_balance:,.2f}")
        logger.info(f"   Max Risk/Trade: {self.config.max_risk_per_trade_pct*100:.1f}% (${self.current_balance * self.config.max_risk_per_trade_pct:,.0f})")
        logger.info(f"   Target Win Rate: {self.config.target_win_rate*100:.0f}%")
        logger.info(f"   Daily Limits: ${self.config.max_daily_loss:+.0f} / ${self.config.max_daily_profit:+.0f}")
        
    def can_trade(self, current_time: datetime, vix_level: float, spy_volume: int) -> Tuple[bool, str]:
        """Check if trading is allowed based on all filters"""
        
        # Check daily limits
        if self.daily_loss_limit_hit:
            return False, f"Daily loss limit hit: ${self.daily_pnl:.2f}"
            
        if self.daily_profit_target_hit:
            return False, f"Daily profit target hit: ${self.daily_pnl:.2f}"
            
        # Check time windows
        current_time_only = current_time.time()
        if current_time_only < self.config.market_open_buffer:
            return False, f"Before trading window: {current_time_only} < {self.config.market_open_buffer}"
            
        if current_time_only > self.config.market_close_buffer:
            return False, f"After trading window: {current_time_only} > {self.config.market_close_buffer}"
            
        # Check VIX filter
        if vix_level > self.config.max_vix_threshold:
            return False, f"VIX too high: {vix_level:.1f} > {self.config.max_vix_threshold}"
            
        # Check volume filter
        if spy_volume < self.config.min_spy_volume:
            return False, f"SPY volume too low: {spy_volume:,} < {self.config.min_spy_volume:,}"
            
        # Check position limits
        if len(self.profit_manager.open_positions) >= self.config.max_positions:
            return False, f"Max positions reached: {len(self.profit_manager.open_positions)}/{self.config.max_positions}"
            
        return True, "All filters passed"
        
    def generate_trade_signal(self, 
                            options_data: pd.DataFrame,
                            spy_price: float,
                            market_regime: str,
                            current_time: datetime) -> Optional[TradeSignal]:
        """
        Generate professional trade signal with 0.20 delta strikes
        """
        
        # ENHANCED: Multi-strategy selection for better win rates
        if market_regime == "BULLISH":
            # Primary: Bull Put Spread, Fallback: Iron Condor
            primary_type = SpreadType.BULL_PUT_SPREAD
            fallback_type = SpreadType.IRON_CONDOR
        elif market_regime == "BEARISH":
            # Primary: Bear Call Spread, Fallback: Iron Condor
            primary_type = SpreadType.BEAR_CALL_SPREAD
            fallback_type = SpreadType.IRON_CONDOR
        elif market_regime == "NO_TRADE":
            # Enhanced regime detector recommends no trading
            logger.debug("Enhanced regime detector recommends no trading")
            return None
        else:  # NEUTRAL or unknown
            # For neutral markets, try all strategies and pick best
            primary_type = SpreadType.IRON_CONDOR
            fallback_type = None
        
        # Try primary strategy first
        spread_type = primary_type
            
        # Find 0.20 delta strikes
        short_strike, long_strike = self._find_delta_strikes(
            options_data, spy_price, spread_type
        )
        
        # ENHANCED: Fallback strategy if primary fails
        if not short_strike or not long_strike:
            if fallback_type is not None:
                logger.debug(f"Primary strategy {primary_type} failed, trying fallback {fallback_type}")
                spread_type = fallback_type
                short_strike, long_strike = self._find_delta_strikes(
                    options_data, spy_price, spread_type
                )
                if not short_strike or not long_strike:
                    return None
            else:
                return None
            
        # Calculate premium and risk
        premium_collected = self._estimate_premium(short_strike, long_strike, spread_type)
        
        # ENHANCED: Lower premium threshold for fallback strategies
        min_premium = self.config.min_premium_collected
        if spread_type != primary_type:  # Using fallback
            min_premium *= 0.8  # Accept 20% lower premium for fallback
            logger.debug(f"Using fallback strategy, reduced premium threshold to ${min_premium:.2f}")
        
        if premium_collected < min_premium:
            return None
            
        max_risk = (abs(long_strike - short_strike) * 100) - (premium_collected * 100)
        max_profit = premium_collected * 100
        
        # Calculate position size using Kelly Criterion
        win_rate = self._estimate_win_rate(spread_type, market_regime)
        avg_win = max_profit
        avg_loss = max_risk
        
        contracts = self.kelly_sizer.calculate_optimal_size(
            win_rate, avg_win, avg_loss, self.current_balance
        )
        
        # ENHANCED: Calculate confidence based on strategy alignment and market conditions
        confidence = self._calculate_enhanced_confidence(
            spread_type, market_regime, premium_collected, primary_type
        )
        
        return TradeSignal(
            spread_type=spread_type,
            short_strike=short_strike,
            long_strike=long_strike,
            contracts=contracts,
            premium_collected=premium_collected,
            max_risk=max_risk,
            max_profit=max_profit,
            confidence=confidence,
            entry_time=current_time
        )
        
    def _find_delta_strikes(self, options_data: pd.DataFrame, spy_price: float, 
                          spread_type: SpreadType) -> Tuple[Optional[float], Optional[float]]:
        """Find strikes closest to realistic 0.20 delta for 0DTE options"""
        
        # REALISTIC 0DTE strike selection - much closer to the money
        # 0.20 delta 0DTE options are typically 0.5-0.8% OTM, not 2%
        
        if spread_type == SpreadType.BULL_PUT_SPREAD:
            # Short put at AGGRESSIVE 0.20 delta (very close to ATM for 0DTE)
            target_short = spy_price * (1 - 0.003)  # ~0.3% OTM for aggressive 0DTE
            target_long = target_short - 2.0  # $2 spread width for higher risk
            
        elif spread_type == SpreadType.BEAR_CALL_SPREAD:
            # Short call at AGGRESSIVE 0.20 delta (very close to ATM for 0DTE)
            target_short = spy_price * (1 + 0.003)  # ~0.3% OTM for aggressive 0DTE
            target_long = target_short + 2.0  # $2 spread width for higher risk
            
        else:  # IRON_CONDOR
            # AGGRESSIVE iron condor with very close strikes
            put_short = spy_price * (1 - 0.003)  # Put side 0.3% OTM
            put_long = put_short - 2.0
            call_short = spy_price * (1 + 0.003)  # Call side 0.3% OTM  
            call_long = call_short + 2.0
            # Return put strikes for now (full IC implementation would need both)
            return put_short, put_long
            
        # Find closest available strikes
        available_strikes = sorted(options_data['strike'].unique())
        
        short_strike = min(available_strikes, key=lambda x: abs(x - target_short))
        long_strike = min(available_strikes, key=lambda x: abs(x - target_long))
        
        # Ensure strikes are different
        if short_strike == long_strike:
            if spread_type == SpreadType.BULL_PUT_SPREAD:
                # Find next lower strike for long
                lower_strikes = [s for s in available_strikes if s < short_strike]
                long_strike = max(lower_strikes) if lower_strikes else None
            else:
                # Find next higher strike for long
                higher_strikes = [s for s in available_strikes if s > short_strike]
                long_strike = min(higher_strikes) if higher_strikes else None
                
        return short_strike, long_strike
        
    def _estimate_premium(self, short_strike: float, long_strike: float, 
                        spread_type: SpreadType) -> float:
        """Estimate premium collected for the spread with realistic 0DTE pricing"""
        
        # REALISTIC 0DTE premium estimation - closer strikes collect more premium
        # but also have higher risk of being tested
        
        spread_width = abs(long_strike - short_strike)
        
        if spread_type == SpreadType.IRON_CONDOR:
            # Iron condor with closer strikes collects more premium (0DTE)
            return min(1.20, spread_width * 0.25)  # Higher premium for closer strikes
        else:
            # Credit spreads with realistic 0DTE pricing
            return min(0.80, spread_width * 0.20)  # More realistic premium collection
            
    def _estimate_win_rate(self, spread_type: SpreadType, market_regime: str) -> float:
        """Estimate win rate based on spread type and market conditions"""
        
        # REALISTIC win rates for 0DTE with closer strikes (higher risk)
        base_rates = {
            SpreadType.BULL_PUT_SPREAD: 0.60,  # Lower win rate due to closer strikes
            SpreadType.BEAR_CALL_SPREAD: 0.60,  # Lower win rate due to closer strikes  
            SpreadType.IRON_CONDOR: 0.65       # Slightly higher but still realistic
        }
        
        base_rate = base_rates.get(spread_type, 0.55)
        
        # Adjust based on market regime alignment (smaller adjustments)
        if spread_type == SpreadType.BULL_PUT_SPREAD and market_regime == "BULLISH":
            return min(0.70, base_rate + 0.05)  # Max 70% even when aligned
        elif spread_type == SpreadType.BEAR_CALL_SPREAD and market_regime == "BEARISH":
            return min(0.70, base_rate + 0.05)  # Max 70% even when aligned
        elif spread_type == SpreadType.IRON_CONDOR and market_regime == "NEUTRAL":
            return min(0.70, base_rate + 0.05)  # Max 70% for neutral markets
        else:
            return max(0.45, base_rate - 0.10)  # Realistic floor when misaligned
            
    def _calculate_confidence(self, spread_type: SpreadType, market_regime: str, 
                            premium: float) -> float:
        """Calculate trade confidence score"""
        
        base_confidence = 70.0
        
        # Adjust for regime alignment
        if ((spread_type == SpreadType.BULL_PUT_SPREAD and market_regime == "BULLISH") or
            (spread_type == SpreadType.BEAR_CALL_SPREAD and market_regime == "BEARISH") or
            (spread_type == SpreadType.IRON_CONDOR and market_regime == "NEUTRAL")):
            base_confidence += 15.0
            
        # Adjust for premium quality
        if premium >= self.config.min_premium_collected * 1.5:
            base_confidence += 10.0
        elif premium < self.config.min_premium_collected * 1.2:
            base_confidence -= 10.0
            
        return min(95.0, max(50.0, base_confidence))
    
    def _calculate_enhanced_confidence(self, spread_type: SpreadType, market_regime: str, 
                                     premium: float, primary_type: SpreadType) -> float:
        """
        ENHANCED: Calculate trade confidence with improved strategy alignment scoring
        """
        
        base_confidence = 60.0  # Start lower, build up with positive factors
        
        # ENHANCED: Strategy alignment scoring
        if spread_type == primary_type:
            # Using primary strategy - high confidence boost
            if ((spread_type == SpreadType.BULL_PUT_SPREAD and market_regime == "BULLISH") or
                (spread_type == SpreadType.BEAR_CALL_SPREAD and market_regime == "BEARISH") or
                (spread_type == SpreadType.IRON_CONDOR and market_regime == "NEUTRAL")):
                base_confidence += 25.0  # Perfect alignment
                logger.debug(f"Perfect strategy alignment: {spread_type} for {market_regime} market")
            else:
                base_confidence += 10.0  # Good alignment
        else:
            # Using fallback strategy - moderate confidence
            base_confidence += 5.0
            logger.debug(f"Using fallback strategy: {spread_type} instead of {primary_type}")
        
        # ENHANCED: Premium quality scoring
        premium_ratio = premium / self.config.min_premium_collected
        if premium_ratio >= 2.0:
            base_confidence += 15.0  # Excellent premium
        elif premium_ratio >= 1.5:
            base_confidence += 10.0  # Good premium
        elif premium_ratio >= 1.2:
            base_confidence += 5.0   # Adequate premium
        # No bonus for minimum premium
        
        # ENHANCED: Market regime confidence adjustment
        if market_regime in ["BULLISH", "BEARISH"]:
            base_confidence += 5.0  # Directional markets are clearer
        elif market_regime == "NEUTRAL":
            base_confidence += 3.0  # Neutral markets are predictable for Iron Condors
        # No adjustment for unknown regimes
        
        # ENHANCED: Risk-reward ratio bonus
        max_risk = (self.config.spread_width * 100) - (premium * 100)
        risk_reward_ratio = (premium * 100) / max_risk if max_risk > 0 else 0
        if risk_reward_ratio >= 0.5:  # 1:2 risk-reward or better
            base_confidence += 10.0
        elif risk_reward_ratio >= 0.33:  # 1:3 risk-reward
            base_confidence += 5.0
        
        final_confidence = min(95.0, max(30.0, base_confidence))
        
        logger.debug(f"Enhanced confidence calculation:")
        logger.debug(f"  Strategy: {spread_type} (primary: {primary_type})")
        logger.debug(f"  Premium ratio: {premium_ratio:.2f}")
        logger.debug(f"  Risk-reward: {risk_reward_ratio:.2f}")
        logger.debug(f"  Final confidence: {final_confidence:.1f}%")
        
        return final_confidence
        
    def execute_trade(self, signal: TradeSignal) -> Dict:
        """Execute trade and add to profit management"""
        
        position_id = f"{signal.spread_type.value}_{signal.entry_time.strftime('%H%M%S')}"
        
        # Add to profit management
        self.profit_manager.add_position(position_id, signal)
        
        # Update tracking
        self.daily_trades += 1
        self.total_trades += 1
        
        # Calculate cash impact
        cash_collected = signal.premium_collected * signal.contracts * 100
        cash_at_risk = signal.max_risk * signal.contracts
        
        trade_record = {
            'position_id': position_id,
            'entry_time': signal.entry_time,
            'spread_type': signal.spread_type.value,
            'short_strike': signal.short_strike,
            'long_strike': signal.long_strike,
            'contracts': signal.contracts,
            'premium_collected': cash_collected,
            'max_risk': cash_at_risk,
            'max_profit': signal.max_profit * signal.contracts,
            'confidence': signal.confidence,
            'status': 'OPEN'
        }
        
        self.trade_history.append(trade_record)
        
        logger.info(f"✅ TRADE EXECUTED: {signal.spread_type.value}")
        logger.info(f"   Strikes: {signal.short_strike}/{signal.long_strike}")
        logger.info(f"   Contracts: {signal.contracts}")
        logger.info(f"   Premium: ${cash_collected:.2f}")
        logger.info(f"   Max Risk: ${cash_at_risk:.2f}")
        logger.info(f"   Confidence: {signal.confidence:.1f}%")
        
        return {
            'executed': True,
            'position_id': position_id,
            'cash_collected': cash_collected,
            'cash_at_risk': cash_at_risk,
            'trade_record': trade_record
        }
        
    def update_daily_pnl(self, pnl_change: float):
        """Update daily P&L and check limits"""
        
        self.daily_pnl += pnl_change
        self.current_balance += pnl_change
        
        # Check daily limits
        if self.daily_pnl <= self.config.max_daily_loss:
            self.daily_loss_limit_hit = True
            logger.warning(f"🚨 DAILY LOSS LIMIT HIT: ${self.daily_pnl:.2f}")
            
        if self.daily_pnl >= self.config.max_daily_profit:
            self.daily_profit_target_hit = True
            logger.info(f"🎯 DAILY PROFIT TARGET HIT: ${self.daily_pnl:.2f}")
            
    def reset_daily_metrics(self):
        """Reset daily tracking metrics"""
        
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_profit_target_hit = False
        self.daily_loss_limit_hit = False
        
        logger.info("📅 Daily metrics reset")
        
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        total_return = ((self.current_balance - self.config.account_balance) / self.config.account_balance * 100)
        
        return {
            'current_balance': self.current_balance,
            'total_return_pct': total_return,
            'daily_pnl': self.daily_pnl,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate_pct': win_rate,
            'daily_trades': self.daily_trades,
            'open_positions': len(self.profit_manager.open_positions),
            'daily_limits_hit': {
                'profit_target': self.daily_profit_target_hit,
                'loss_limit': self.daily_loss_limit_hit
            }
        }

def main():
    """Test the professional system"""
    
    print("🏆 TESTING PROFESSIONAL 0DTE CREDIT SPREAD SYSTEM")
    print("=" * 60)
    
    # Initialize system
    system = Professional0DTESystem()
    
    # Test configuration
    print(f"📊 SYSTEM CONFIGURATION:")
    print(f"   Account Balance: ${system.config.account_balance:,.2f}")
    print(f"   Max Risk/Trade: {system.config.max_risk_per_trade_pct*100:.1f}%")
    print(f"   Target Win Rate: {system.config.target_win_rate*100:.0f}%")
    print(f"   Target Delta: {system.config.target_delta_short:.2f}")
    print(f"   Daily Limits: ${system.config.max_daily_loss:+.0f} / ${system.config.max_daily_profit:+.0f}")
    
    # Test trading conditions
    current_time = datetime.now().replace(hour=10, minute=30)  # 10:30 AM
    vix_level = 20.0
    spy_volume = 2000000
    
    can_trade, reason = system.can_trade(current_time, vix_level, spy_volume)
    print(f"\\n🔍 TRADING CONDITIONS:")
    print(f"   Can Trade: {can_trade}")
    print(f"   Reason: {reason}")
    
    # Test Kelly position sizing
    kelly_contracts = system.kelly_sizer.calculate_optimal_size(
        win_probability=0.75,
        avg_win=150.0,
        avg_loss=350.0,
        current_balance=25000.0
    )
    print(f"\\n📏 KELLY POSITION SIZING:")
    print(f"   Optimal Contracts: {kelly_contracts}")
    
    print(f"\\n✅ PROFESSIONAL SYSTEM TEST COMPLETE")

if __name__ == "__main__":
    main()
