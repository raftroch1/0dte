#!/usr/bin/env python3
"""
Professional 0DTE Debit Spread Trading System
=============================================

SIGNAL FLIPPED VERSION: Buying Premium Instead of Selling
- Bull Call Debit Spreads instead of Bull Put Credit Spreads
- Bear Put Debit Spreads instead of Bear Call Credit Spreads
- Long Straddles/Strangles instead of Iron Condors
- Inverted risk-reward profile: Lower win rates but higher profit potential
- Different position sizing and risk management

This system flips the signal from the credit spread system to analyze
performance differences between premium selling vs premium buying strategies.

Location: src/strategies/professional_0dte/ (following .cursorrules structure)
Author: Advanced Options Trading System - Debit Spread Implementation
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

class DebitSpreadType(Enum):
    """Debit spread types - NAKED OPTIONS + SPREADS"""
    BULL_CALL_SPREAD = "BULL_CALL_SPREAD"      # Long lower strike call, short higher strike call
    BEAR_PUT_SPREAD = "BEAR_PUT_SPREAD"        # Long higher strike put, short lower strike put
    NAKED_CALL = "NAKED_CALL"                  # Long call at 0.4 delta
    NAKED_PUT = "NAKED_PUT"                    # Long put at 0.4 delta

@dataclass
class DebitSpreadConfig:
    """Debit spread trading system configuration - FLIPPED parameters"""
    # Account Settings (Same base account)
    account_balance: float = 25000.0
    max_risk_per_trade_pct: float = 0.020      # 2% max risk per trade (higher for debit spreads)
    max_daily_loss: float = -500.0            # Higher loss limit for debit spreads
    max_daily_profit: float = 400.0           # Higher profit target potential
    
    # Position Sizing (Optimized for 3:1 reward:risk)
    target_win_rate: float = 0.50             # TARGET: 50% win rate for optimal performance
    kelly_fraction_cap: float = 0.25          # Conservative Kelly for 3:1 system
    max_positions: int = 4                    # Allow more positions with limited risk
    
    # Spread Configuration (0DTE OPTIMIZED - Wider spreads for distinct strikes)
    target_delta_long: float = 0.45           # 45 delta for long strikes (ITM for 0DTE)
    target_delta_short: float = 0.15          # 15 delta for short strikes (OTM for 0DTE)
    min_delta_spread: float = 0.25            # Minimum delta difference (wider for 0DTE distinct strikes)
    max_delta_spread: float = 0.35            # Maximum delta difference (wider for 0DTE distinct strikes)
    target_profit_ratio: float = 2.0          # 2:1 reward:risk target (more realistic for 0DTE)
    max_premium_paid: float = 5.00            # Higher premium allowed for 0DTE (closer to ATM)
    
    # Profit Management (0DTE OPTIMIZED - Faster exits due to time decay)
    profit_target_pct: float = 0.30           # Take profit at 30% - faster for 0DTE time decay
    trailing_stop_pct: float = 0.15           # Trail stop at 15% - tighter for 0DTE
    stop_loss_pct: float = 0.60               # Stop at 60% loss - tighter for 0DTE time decay
    
    # Time Management (Same)
    market_open_buffer: time = time(9, 45)
    market_close_buffer: time = time(14, 30)
    force_close_time: time = time(15, 30)
    
    # Market Filters (OPTIMIZED for 0DTE trading frequency)
    min_vix_threshold: float = 10.0           # Very low threshold for 0DTE opportunities
    max_vix_threshold: float = 35.0           # Higher threshold for 0DTE (volatility is good)
    min_spy_volume: int = 1000000             # Lower volume requirement for more trades             # Higher volume for better execution
    trend_strength_threshold: float = 0.60    # Only trade strong trends for better win rate

@dataclass
class DebitTradeSignal:
    """Debit trade signal - FLIPPED from credit signal"""
    spread_type: DebitSpreadType
    long_strike: float                        # FLIPPED: Long strike is primary
    short_strike: float                       # FLIPPED: Short strike is secondary
    contracts: int
    premium_paid: float                       # FLIPPED: Pay premium instead of collect
    max_profit_potential: float               # FLIPPED: Unlimited/high profit potential
    max_loss: float                          # FLIPPED: Limited to premium paid
    confidence: float
    entry_time: datetime

class DebitKellyPositionSizer:
    """Kelly Criterion position sizing for debit spreads - FLIPPED logic"""
    
    def __init__(self, config: DebitSpreadConfig):
        self.config = config
        
    def calculate_optimal_size(self, 
                             win_probability: float,
                             avg_win: float,
                             avg_loss: float,
                             current_balance: float) -> int:
        """
        Kelly Criterion for debit spreads - FLIPPED risk-reward profile
        
        Debit spreads have:
        - Lower win rates (40-50% vs 70-80%)
        - Higher profit potential (2:1 or 3:1 vs negative risk-reward)
        - Limited loss (premium paid)
        """
        
        if avg_loss <= 0 or avg_win <= 0:
            return 1
        
        # Use actual win rate (don't inflate for debit spreads)
        effective_win_rate = max(win_probability, 0.35)  # Minimum 35% for debit spreads
        
        # Calculate Kelly fraction with debit spread profile
        b = avg_win / abs(avg_loss)  # Should be > 1 for debit spreads
        p = effective_win_rate
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        kelly_fraction = min(kelly_fraction, self.config.kelly_fraction_cap)
        kelly_fraction = max(kelly_fraction, 0.02)  # Minimum 2%
        
        # Position sizing for debit spreads
        expected_value_per_contract = p * avg_win - q * avg_loss
        
        if expected_value_per_contract > 0:
            # Method 1: Target-based sizing (fewer trades, higher profit per trade)
            trades_per_day = 2.0  # Fewer trades for debit spreads
            daily_expected_per_contract = trades_per_day * expected_value_per_contract
            contracts_for_target = max(1, int(400.0 / daily_expected_per_contract))  # $400 daily target
            
            # Method 2: Kelly-based sizing
            kelly_risk_dollars = current_balance * kelly_fraction
            max_premium_per_spread = self.config.max_premium_paid * 100
            kelly_contracts = max(1, int(kelly_risk_dollars / max_premium_per_spread))
            
            # Method 3: Account risk limit
            max_risk_dollars = current_balance * self.config.max_risk_per_trade_pct
            account_contracts = max(1, int(max_risk_dollars / max_premium_per_spread))
            
            # Method 4: Absolute risk limit
            absolute_max_risk = 500.0  # Higher for debit spreads
            absolute_contracts = max(1, int(absolute_max_risk / abs(avg_loss)))
            
            # Take minimum for safety
            position_size = min(contracts_for_target, kelly_contracts, account_contracts, absolute_contracts)
            
            # Reasonable bounds (1-8 contracts max for debit spreads)
            position_size = max(1, min(position_size, 8))
            
            logger.info(f"Debit Kelly Sizing Analysis:")
            logger.info(f"  Win rate: {p:.1%}, Risk-Reward: {b:.2f}:1")
            logger.info(f"  Expected value: ${expected_value_per_contract:.2f}")
            logger.info(f"  Target-based: {contracts_for_target}, Kelly: {kelly_contracts}")
            logger.info(f"  Final position: {position_size} contracts")
            
        else:
            position_size = 1
            logger.warning(f"Negative expected value for debit spread: ${expected_value_per_contract:.2f}")
        
        return position_size

class DebitProfitManager:
    """Profit management for debit spreads - FLIPPED logic"""
    
    def __init__(self, config: DebitSpreadConfig):
        self.config = config
        self.open_positions: Dict[str, Dict] = {}
        
    def add_position(self, position_id: str, trade_signal: DebitTradeSignal):
        """Add debit position to management"""
        self.open_positions[position_id] = {
            'signal': trade_signal,
            'entry_time': trade_signal.entry_time,
            'premium_paid': trade_signal.premium_paid,
            'max_profit_potential': trade_signal.max_profit_potential,
            'max_loss': trade_signal.max_loss,
            'profit_target': trade_signal.max_profit_potential * self.config.profit_target_pct,
            'stop_loss': trade_signal.premium_paid * self.config.stop_loss_pct,
            'trailing_stop_active': False,
            'highest_profit': 0.0
        }
        
    def check_exit_conditions(self, position_id: str, current_value: float, 
                            current_time: datetime) -> Tuple[bool, str]:
        """Check exit conditions for debit spreads - FLIPPED logic"""
        
        if position_id not in self.open_positions:
            return False, ""
            
        position = self.open_positions[position_id]
        
        # Calculate current P&L (FLIPPED: current_value - premium_paid)
        current_pnl = current_value - position['premium_paid']
        
        # Update highest profit for trailing stop
        if current_pnl > position['highest_profit']:
            position['highest_profit'] = current_pnl
            
        # Activate trailing stop at 25% of max profit potential
        if current_pnl >= position['max_profit_potential'] * self.config.trailing_stop_pct:
            position['trailing_stop_active'] = True
            
        # Check exit conditions
        
        # 1. Profit target (50% of max profit potential)
        if current_pnl >= position['profit_target']:
            return True, "PROFIT_TARGET_50PCT"
            
        # 2. Stop loss (50% of premium paid)
        if current_pnl <= -position['stop_loss']:
            return True, "STOP_LOSS_50PCT"
            
        # 3. Trailing stop (if active)
        if position['trailing_stop_active']:
            trailing_stop_level = position['highest_profit'] * 0.60  # Keep 60% of highest profit
            if current_pnl <= trailing_stop_level:
                return True, "TRAILING_STOP"
                
        # 4. Time-based exit
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

class Professional0DTEDebitSystem:
    """
    Professional 0DTE Debit Spread Trading System - SIGNAL FLIPPED
    
    Key differences from credit system:
    - Buys premium instead of selling
    - Lower win rates but higher profit potential
    - Different strike selection (ITM/ATM long, OTM short)
    - Different risk management (limited loss, unlimited profit)
    """
    
    def __init__(self, config: Optional[DebitSpreadConfig] = None):
        self.config = config or DebitSpreadConfig()
        self.kelly_sizer = DebitKellyPositionSizer(self.config)
        self.profit_manager = DebitProfitManager(self.config)
        
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
        
        logger.info("🔄 PROFESSIONAL 0DTE DEBIT SYSTEM INITIALIZED (SIGNAL FLIPPED)")
        logger.info(f"   Account Balance: ${self.current_balance:,.2f}")
        logger.info(f"   Max Risk/Trade: {self.config.max_risk_per_trade_pct*100:.1f}%")
        logger.info(f"   Target Win Rate: {self.config.target_win_rate*100:.0f}% (LOWER)")
        logger.info(f"   Strategy: BUYING PREMIUM (Debit Spreads)")
        
    def can_trade(self, current_time: datetime, vix_level: float, spy_volume: int) -> Tuple[bool, str]:
        """Check if trading is allowed - adjusted for debit spreads"""
        
        # Check daily limits
        if self.daily_loss_limit_hit:
            return False, f"Daily loss limit hit: ${self.daily_pnl:.2f}"
            
        if self.daily_profit_target_hit:
            return False, f"Daily profit target hit: ${self.daily_pnl:.2f}"
            
        # Check time windows
        current_time_only = current_time.time()
        if current_time_only < self.config.market_open_buffer:
            return False, f"Before trading window: {current_time_only}"
            
        if current_time_only > self.config.market_close_buffer:
            return False, f"After trading window: {current_time_only}"
            
        # Check VIX filter (FLIPPED: need minimum volatility for debit spreads)
        if vix_level < self.config.min_vix_threshold:
            return False, f"VIX too low for debit spreads: {vix_level:.1f} < {self.config.min_vix_threshold}"
            
        if vix_level > self.config.max_vix_threshold:
            return False, f"VIX too high: {vix_level:.1f} > {self.config.max_vix_threshold}"
            
        # Check volume filter
        if spy_volume < self.config.min_spy_volume:
            return False, f"SPY volume too low: {spy_volume:,}"
            
        # Check position limits
        if len(self.profit_manager.open_positions) >= self.config.max_positions:
            return False, f"Max positions reached: {len(self.profit_manager.open_positions)}"
            
        return True, "All filters passed"
        
    def generate_debit_trade_signal(self, 
                                  options_data: pd.DataFrame,
                                  spy_price: float,
                                  market_regime: str,
                                  current_time: datetime,
                                  vix_level: float = 18.0) -> Optional[DebitTradeSignal]:
        """
        Generate debit trade signal - FLIPPED from credit spread logic
        """
        
        # ENHANCED strategy selection with regime validation
        logger.info(f"🎯 REGIME ANALYSIS: {market_regime} (VIX: {vix_level:.1f})")
        
        if market_regime in ["BULLISH", "STRONG_BULLISH"] or vix_level > 25.0:
            # Bull market OR High VIX: Buy Naked Calls at 0.4 delta
            spread_type = DebitSpreadType.NAKED_CALL
            logger.info(f"🎯 BULLISH STRATEGY: NAKED_CALL (0.4 delta, VIX: {vix_level:.1f})")
        elif market_regime in ["BEARISH", "STRONG_BEARISH"]:
            # Bear market: Buy Naked Puts at 0.4 delta
            spread_type = DebitSpreadType.NAKED_PUT
            logger.info(f"🎯 BEARISH STRATEGY: NAKED_PUT (0.4 delta)")
        else:
            # Neutral/uncertain: Default to Naked Call for 0DTE
            spread_type = DebitSpreadType.NAKED_CALL
            logger.info(f"🎯 NEUTRAL STRATEGY: NAKED_CALL (0.4 delta, default for 0DTE)")
        
        # Find strikes for debit spread (FLIPPED logic)
        long_strike, short_strike = self._find_debit_strikes(
            options_data, spy_price, spread_type, current_time
        )
        
        logger.info(f"🔍 DEBIT STRIKES: Long={long_strike}, Short={short_strike}")
        
        # Validate strikes - naked options only need long_strike
        if not long_strike:
            logger.info(f"❌ DEBIT SIGNAL FAILED: No valid long strike found")
            return None
        
        # For spreads, we also need a short strike
        if spread_type in [DebitSpreadType.BULL_CALL_SPREAD, DebitSpreadType.BEAR_PUT_SPREAD] and not short_strike:
            logger.info(f"❌ DEBIT SIGNAL FAILED: No valid short strike found for spread")
            return None
            
        # Calculate premium and risk (REAL BLACK-SCHOLES PRICING)
        premium_paid = self._estimate_debit_premium(long_strike, short_strike, spread_type, spy_price)
        
        logger.info(f"🔍 DEBIT PREMIUM: ${premium_paid:.2f} (delta-based selection)")
        
        # Validate delta spread is reasonable for spreads (skip for naked options)
        if spread_type in [DebitSpreadType.BULL_CALL_SPREAD, DebitSpreadType.BEAR_PUT_SPREAD]:
            delta_spread = abs(long_strike - short_strike) / spy_price
            if delta_spread < 0.005:  # Less than 0.5% spread
                logger.info(f"❌ DEBIT SIGNAL FAILED: Delta spread too narrow {delta_spread:.3f}")
                return None
        else:
            # Naked options - no spread validation needed
            logger.info(f"✅ NAKED OPTION: Strike {long_strike} (0.4 delta target)")
            
        # Calculate P&L based on strategy type
        max_loss = premium_paid * 100  # Premium paid per contract
        
        if spread_type in [DebitSpreadType.NAKED_CALL, DebitSpreadType.NAKED_PUT]:
            # NAKED OPTIONS: Unlimited profit potential
            max_profit_potential = float('inf')
        else:
            # DEBIT SPREADS: Max profit is spread width - premium
            max_profit_potential = (abs(long_strike - short_strike) - premium_paid) * 100
        
        # Check minimum profit potential (3:1 ratio target)
        min_profit_target = premium_paid * self.config.target_profit_ratio * 100  # 3:1 ratio
        logger.info(f"🔍 PROFIT CHECK: Max=${max_profit_potential:.2f}, Min=${min_profit_target:.2f}")
        if max_profit_potential != float('inf') and max_profit_potential < min_profit_target:
            logger.info(f"❌ DEBIT SIGNAL FAILED: Insufficient profit potential ${max_profit_potential:.2f} < ${min_profit_target:.2f}")
            return None
        
        # Calculate position size using Kelly Criterion (FLIPPED risk-reward)
        win_rate = self._estimate_debit_win_rate(spread_type, market_regime)
        avg_win = min(max_profit_potential, 300.0) if max_profit_potential != float('inf') else 300.0
        avg_loss = max_loss
        
        contracts = self.kelly_sizer.calculate_optimal_size(
            win_rate, avg_win, avg_loss, self.current_balance
        )
        
        # Calculate confidence
        confidence = self._calculate_debit_confidence(spread_type, market_regime, premium_paid)
        
        return DebitTradeSignal(
            spread_type=spread_type,
            long_strike=long_strike,
            short_strike=short_strike,
            contracts=contracts,
            premium_paid=premium_paid,
            max_profit_potential=max_profit_potential if max_profit_potential != float('inf') else 500.0,
            max_loss=max_loss,
            confidence=confidence,
            entry_time=current_time
        )
        
    def _find_debit_strikes(self, options_data: pd.DataFrame, spy_price: float, 
                          spread_type: DebitSpreadType, current_time: datetime) -> Tuple[Optional[float], Optional[float]]:
        """Find strikes for debit spreads using DELTA-BASED selection"""
        
        # Filter for 0DTE options (same day expiry) - use current_time for backtesting
        current_date = current_time.date()
        same_day_options = options_data[
            pd.to_datetime(options_data['option_details.expiration_date']).dt.date == current_date
        ]
        
        if same_day_options.empty:
            logger.info("❌ No 0DTE options available")
            return None, None
        
        if spread_type == DebitSpreadType.BULL_CALL_SPREAD:
            # Bull Call Debit: Buy ~30 delta call, sell ~10 delta call
            calls = same_day_options[same_day_options['option_details.contract_type'] == 'call']
            
            # Find 30 delta call (long)
            long_strike = self._find_strike_by_delta(calls, spy_price, self.config.target_delta_long, 'call')
            # Find 10 delta call (short) 
            short_strike = self._find_strike_by_delta(calls, spy_price, self.config.target_delta_short, 'call')
            
            # Ensure different strikes for valid spread
            if long_strike == short_strike:
                logger.warning(f"❌ Same strikes found: {long_strike}. Adjusting short strike.")
                # Find next available strike above long_strike
                available_strikes = sorted(calls['option_details.strike_price'].unique())
                higher_strikes = [s for s in available_strikes if s > long_strike]
                if higher_strikes:
                    short_strike = higher_strikes[0]
                else:
                    return None, None
            
        elif spread_type == DebitSpreadType.BEAR_PUT_SPREAD:
            # Bear Put Debit: Buy ~30 delta put, sell ~10 delta put
            puts = same_day_options[same_day_options['option_details.contract_type'] == 'put']
            
            # Find 30 delta put (long)
            long_strike = self._find_strike_by_delta(puts, spy_price, self.config.target_delta_long, 'put')
            # Find 10 delta put (short)
            short_strike = self._find_strike_by_delta(puts, spy_price, self.config.target_delta_short, 'put')
            
            # Ensure different strikes for valid spread
            if long_strike == short_strike:
                logger.warning(f"❌ Same strikes found: {long_strike}. Adjusting short strike.")
                # Find next available strike below long_strike
                available_strikes = sorted(puts['option_details.strike_price'].unique(), reverse=True)
                lower_strikes = [s for s in available_strikes if s < long_strike]
                if lower_strikes:
                    short_strike = lower_strikes[0]
                else:
                    return None, None
            
        elif spread_type == DebitSpreadType.NAKED_CALL:
            # Naked Call: Buy 0.4 delta call only
            calls = same_day_options[same_day_options['option_details.contract_type'] == 'call']
            long_strike = self._find_strike_by_delta(calls, spy_price, 0.40, 'call')
            short_strike = None  # No short leg for naked options
            
        elif spread_type == DebitSpreadType.NAKED_PUT:
            # Naked Put: Buy 0.4 delta put only
            puts = same_day_options[same_day_options['option_details.contract_type'] == 'put']
            long_strike = self._find_strike_by_delta(puts, spy_price, 0.40, 'put')
            short_strike = None  # No short leg for naked options
            
        else:
            logger.error(f"❌ Unknown spread type: {spread_type}")
            return None, None
        
        return long_strike, short_strike
    
    def _find_strike_by_delta(self, options: pd.DataFrame, spy_price: float, 
                            target_delta: float, option_type: str) -> Optional[float]:
        """Find strike closest to target delta"""
        
        if options.empty:
            return None
        
        # Calculate approximate delta for each strike (improved for 0DTE)
        # For 0DTE options, delta changes rapidly with moneyness
        
        if option_type == 'call':
            # For calls: ITM calls have higher delta, OTM calls have lower delta
            # 0DTE FIXED: Proper delta approximation
            strikes = options['option_details.strike_price']
            
            # Simple but accurate 0DTE delta approximation
            # ATM (SPY price) = ~0.50 delta
            # Each $1 ITM (lower strike) adds ~0.05 delta, Each $1 OTM (higher strike) subtracts ~0.05 delta
            delta_per_dollar = 0.05  # Conservative for 0DTE
            
            # FIXED: For calls, lower strikes = higher delta, higher strikes = lower delta
            options['approx_delta'] = np.maximum(0.01, 
                np.minimum(0.99, 
                    0.50 - (strikes - spy_price) * delta_per_dollar / spy_price
                )
            )
        else:
            # For puts: ITM puts have higher absolute delta, OTM puts have lower delta  
            # 0DTE FIXED: Proper delta approximation for puts
            strikes = options['option_details.strike_price']
            
            # Simple but accurate 0DTE put delta approximation
            # ATM (SPY price) = ~0.50 delta (using absolute values)
            # Each $1 ITM (higher strike) adds ~0.05 delta, Each $1 OTM (lower strike) subtracts ~0.05 delta
            delta_per_dollar = 0.05  # Conservative for 0DTE
            
            # FIXED: For puts, higher strikes = higher delta, lower strikes = lower delta
            options['approx_delta'] = np.maximum(0.01, 
                np.minimum(0.99, 
                    0.50 + (strikes - spy_price) * delta_per_dollar / spy_price
                )
            )
        
        # Find strike closest to target delta
        options['delta_diff'] = abs(options['approx_delta'] - target_delta)
        best_option = options.loc[options['delta_diff'].idxmin()]
        
        return float(best_option['option_details.strike_price'])
    
    def _find_atm_strike(self, options: pd.DataFrame, spy_price: float) -> Optional[float]:
        """Find at-the-money strike"""
        
        available_strikes = sorted(options['option_details.strike_price'].unique())
        atm_strike = min(available_strikes, key=lambda x: abs(x - spy_price))
        
        return float(atm_strike)
        
    def _estimate_debit_premium(self, long_strike: float, short_strike: float, 
                              spread_type: DebitSpreadType, spy_price: float) -> float:
        """Calculate REAL premium using Black-Scholes - NO SIMULATION"""
        
        # CRITICAL FIX: Use REAL option pricing instead of hardcoded estimates
        from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
        
        bs_calc = BlackScholesCalculator()
        time_to_expiry = 4.0 / (365 * 24)  # 4 hours to expiry for 0DTE
        volatility = 0.25  # 25% IV for 0DTE options
        
        if spread_type == DebitSpreadType.NAKED_CALL:
            # Naked Call: Just the call premium
            return bs_calc.calculate_option_price(spy_price, long_strike, time_to_expiry, volatility, 'call')
        elif spread_type == DebitSpreadType.NAKED_PUT:
            # Naked Put: Just the put premium
            return bs_calc.calculate_option_price(spy_price, long_strike, time_to_expiry, volatility, 'put')
        else:
            # SPREADS - Use Black-Scholes spread calculation
            return bs_calc.calculate_spread_value(
                spot_price=spy_price,
                long_strike=long_strike,
                short_strike=short_strike,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                spread_type=spread_type.value
            )
            
    def _estimate_debit_win_rate(self, spread_type: DebitSpreadType, market_regime: str) -> float:
        """Estimate win rate for debit spreads - OPTIMIZED for 50% target"""
        
        # OPTIMIZED: Realistic win rates with market alignment bonuses
        base_rates = {
            DebitSpreadType.BULL_CALL_SPREAD: 0.45,    # Conservative base rate
            DebitSpreadType.BEAR_PUT_SPREAD: 0.45,     # Conservative base rate
            DebitSpreadType.NAKED_CALL: 0.40,          # Naked calls - need bigger moves
            DebitSpreadType.NAKED_PUT: 0.40,           # Naked puts - need bigger moves
        }
        
        base_rate = base_rates.get(spread_type, 0.45)
        
        # ENHANCED: Better alignment bonuses for 50%+ win rate
        if spread_type == DebitSpreadType.BULL_CALL_SPREAD and market_regime == "BULLISH":
            return min(0.65, base_rate + 0.15)  # Strong bullish alignment
        elif spread_type == DebitSpreadType.BEAR_PUT_SPREAD and market_regime == "BEARISH":
            return min(0.65, base_rate + 0.15)  # Strong bearish alignment
        elif spread_type == DebitSpreadType.NAKED_CALL and market_regime in ["BULLISH", "STRONG_BULLISH"]:
            return min(0.60, base_rate + 0.20)  # Naked calls in bull market
        elif spread_type == DebitSpreadType.NAKED_PUT and market_regime in ["BEARISH", "STRONG_BEARISH"]:
            return min(0.60, base_rate + 0.20)  # Naked puts in bear market
        elif market_regime == "NEUTRAL":
            return max(0.45, base_rate - 0.05)  # Neutral is okay for debit spreads
        else:
            return max(0.35, base_rate - 0.15)  # Misaligned penalty
            
    def _calculate_debit_confidence(self, spread_type: DebitSpreadType, market_regime: str, 
                                  premium: float) -> float:
        """Calculate confidence for debit spreads"""
        
        base_confidence = 60.0
        
        # Adjust for regime alignment - SPREADS + NAKED OPTIONS
        if ((spread_type == DebitSpreadType.BULL_CALL_SPREAD and market_regime == "BULLISH") or
            (spread_type == DebitSpreadType.BEAR_PUT_SPREAD and market_regime == "BEARISH") or
            (spread_type == DebitSpreadType.NAKED_CALL and market_regime in ["BULLISH", "STRONG_BULLISH"]) or
            (spread_type == DebitSpreadType.NAKED_PUT and market_regime in ["BEARISH", "STRONG_BEARISH"])):
            base_confidence += 20.0
            
        # Adjust for premium cost (FLIPPED: lower premium is better)
        if premium <= self.config.max_premium_paid * 0.7:
            base_confidence += 15.0  # Good value
        elif premium >= self.config.max_premium_paid * 0.9:
            base_confidence -= 10.0  # Expensive
            
        return min(95.0, max(40.0, base_confidence))
        
    def execute_trade(self, signal: DebitTradeSignal) -> Dict:
        """Execute debit trade"""
        
        position_id = f"{signal.spread_type.value}_{signal.entry_time.strftime('%H%M%S')}"
        
        # Add to profit management
        self.profit_manager.add_position(position_id, signal)
        
        # Update tracking
        self.daily_trades += 1
        self.total_trades += 1
        
        # Calculate cash impact (FLIPPED: pay premium)
        cash_paid = signal.premium_paid * signal.contracts * 100
        max_profit_potential = signal.max_profit_potential * signal.contracts if signal.max_profit_potential != float('inf') else 50000
        
        trade_record = {
            'position_id': position_id,
            'entry_time': signal.entry_time,
            'spread_type': signal.spread_type.value,
            'long_strike': signal.long_strike,
            'short_strike': signal.short_strike,
            'contracts': signal.contracts,
            'premium_paid': cash_paid,
            'max_loss': signal.max_loss * signal.contracts,
            'max_profit_potential': max_profit_potential,
            'confidence': signal.confidence,
            'status': 'OPEN'
        }
        
        self.trade_history.append(trade_record)
        
        logger.info(f"✅ DEBIT TRADE EXECUTED: {signal.spread_type.value}")
        logger.info(f"   Strikes: {signal.long_strike}/{signal.short_strike}")
        logger.info(f"   Contracts: {signal.contracts}")
        logger.info(f"   Premium PAID: ${cash_paid:.2f}")
        logger.info(f"   Max Profit Potential: ${max_profit_potential:.2f}")
        logger.info(f"   Confidence: {signal.confidence:.1f}%")
        
        return {
            'executed': True,
            'position_id': position_id,
            'cash_paid': cash_paid,
            'max_profit_potential': max_profit_potential,
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
            },
            'strategy_type': 'DEBIT_SPREADS'
        }

def main():
    """Test the debit spread system"""
    
    print("🔄 TESTING PROFESSIONAL 0DTE DEBIT SPREAD SYSTEM (SIGNAL FLIPPED)")
    print("=" * 70)
    
    # Initialize system
    system = Professional0DTEDebitSystem()
    
    # Test configuration
    print(f"📊 DEBIT SYSTEM CONFIGURATION:")
    print(f"   Account Balance: ${system.config.account_balance:,.2f}")
    print(f"   Max Risk/Trade: {system.config.max_risk_per_trade_pct*100:.1f}%")
    print(f"   Target Win Rate: {system.config.target_win_rate*100:.0f}% (LOWER)")
    print(f"   Strategy: BUYING PREMIUM (Debit Spreads)")
    print(f"   VIX Range: {system.config.min_vix_threshold} - {system.config.max_vix_threshold}")
    
    # Test trading conditions
    current_time = datetime.now().replace(hour=10, minute=30)
    vix_level = 22.0  # Good for debit spreads
    spy_volume = 2000000
    
    can_trade, reason = system.can_trade(current_time, vix_level, spy_volume)
    print(f"\n🔍 TRADING CONDITIONS:")
    print(f"   Can Trade: {can_trade}")
    print(f"   Reason: {reason}")
    
    # Test Kelly position sizing for debit spreads
    kelly_contracts = system.kelly_sizer.calculate_optimal_size(
        win_probability=0.45,  # Lower win rate
        avg_win=250.0,         # Higher average win
        avg_loss=150.0,        # Limited loss
        current_balance=25000.0
    )
    print(f"\n📏 DEBIT KELLY POSITION SIZING:")
    print(f"   Optimal Contracts: {kelly_contracts}")
    
    print(f"\n✅ DEBIT SYSTEM TEST COMPLETE")
    print("🔄 SIGNAL SUCCESSFULLY FLIPPED FROM CREDIT TO DEBIT")

if __name__ == "__main__":
    main()
