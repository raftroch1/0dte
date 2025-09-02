#!/usr/bin/env python3
"""
Credit Spread Optimizer Configuration
====================================

Configuration parameters for the professional-grade credit spread system
targeting $200/day profit with $25k account.

Following @.cursorrules architecture patterns.
"""

from dataclasses import dataclass
from datetime import time
from typing import Dict, List, Optional

@dataclass
class CreditSpreadConfig:
    """
    Configuration for credit spread optimization system
    
    Based on user requirements:
    - $25k account targeting $200/day (0.8% daily return)
    - 75% win rate target
    - 2% max risk per trade
    - Kelly Criterion position sizing
    """
    
    # Account Management
    account_balance: float = 25000.0
    daily_profit_target: float = 200.0      # $200/day target
    daily_loss_limit: float = -400.0        # 2x profit target stop
    max_daily_risk_pct: float = 0.04        # 4% max daily drawdown
    
    # Position Sizing (Kelly Criterion)
    max_risk_per_trade_pct: float = 0.02    # 2% max per trade
    target_win_rate: float = 0.75           # 75% target win rate
    kelly_fraction_limit: float = 0.25      # Cap Kelly at 25%
    
    # Spread Configuration
    spread_width: int = 5                   # $5 wide spreads
    target_delta: float = 0.20              # 20 delta for short strikes
    min_premium_collected: float = 0.35     # Min $0.35 per spread
    max_premium_collected: float = 0.50     # Max $0.50 per spread
    
    # Profit Taking & Risk Management
    profit_target_pct: float = 0.50         # Take profit at 50% of max
    trailing_stop_pct: float = 0.25         # Trail stop at 25% profit
    stop_loss_multiplier: float = 2.0       # Stop at 2x premium collected
    
    # Position Management
    max_concurrent_positions: int = 4        # Max 4 positions at once
    position_correlation_limit: float = 0.7  # Max correlation between positions
    
    # Time Management
    market_open_time: time = time(9, 45)     # No trades before 9:45 AM ET
    market_close_time: time = time(14, 30)   # No new trades after 2:30 PM ET
    force_close_time: time = time(15, 30)    # Force close all by 3:30 PM ET
    
    # Market Filtering
    max_vix_threshold: float = 25.0          # Don't trade if VIX > 25
    min_spy_volume: int = 1000000           # Min SPY volume requirement
    min_options_volume: int = 50            # Min options volume per strike
    
    # Strategy Selection Thresholds
    bullish_confidence_threshold: float = 60.0   # Bull Put Spread threshold
    bearish_confidence_threshold: float = 60.0   # Bear Call Spread threshold
    neutral_preference: bool = False             # Prefer directional over neutral
    
    # Performance Tracking
    track_intraday_pnl: bool = True
    log_all_decisions: bool = True
    export_trade_data: bool = True
    
    # Risk Alerts
    daily_loss_alert_pct: float = 0.02      # Alert at 2% daily loss
    position_size_alert_pct: float = 0.025  # Alert if position > 2.5%
    correlation_alert_threshold: float = 0.8 # Alert if correlation > 80%

@dataclass 
class KellyCriterionConfig:
    """Kelly Criterion specific configuration"""
    
    # Historical Performance Estimates (will be updated dynamically)
    estimated_win_rate: float = 0.75
    estimated_avg_win: float = 60.0         # $60 average win
    estimated_avg_loss: float = 120.0       # $120 average loss
    
    # Kelly Calculation Parameters
    confidence_interval: float = 0.95       # 95% confidence for estimates
    lookback_period_days: int = 30          # Days to calculate recent performance
    min_trades_for_kelly: int = 20          # Min trades before using Kelly
    
    # Safety Limits
    max_kelly_fraction: float = 0.25        # Never risk more than 25% Kelly
    min_kelly_fraction: float = 0.01        # Always risk at least 1%
    kelly_adjustment_factor: float = 0.75   # Conservative Kelly adjustment

@dataclass
class MarketFilterConfig:
    """Market condition filtering configuration"""
    
    # VIX Filtering
    vix_normal_max: float = 20.0            # Normal market VIX ceiling
    vix_elevated_max: float = 25.0          # Elevated VIX ceiling
    vix_crisis_threshold: float = 30.0      # Crisis mode threshold
    
    # Volume Filtering  
    spy_volume_percentile: float = 0.3      # Min 30th percentile volume
    options_volume_multiplier: float = 1.5  # 1.5x average options volume
    
    # Time-of-Day Filtering
    avoid_first_30min: bool = True          # Skip first 30 minutes
    avoid_last_30min: bool = True           # Skip last 30 minutes
    lunch_break_start: time = time(12, 0)   # Reduced activity period
    lunch_break_end: time = time(13, 0)     # Reduced activity period
    
    # Market Regime Filtering
    trending_market_threshold: float = 0.8   # Strong trend confidence
    sideways_market_preference: bool = True  # Prefer sideways markets
    
# Default configuration instance
DEFAULT_CONFIG = CreditSpreadConfig()
KELLY_CONFIG = KellyCriterionConfig()  
FILTER_CONFIG = MarketFilterConfig()

def get_config_for_account_size(account_balance: float) -> CreditSpreadConfig:
    """
    Adjust configuration based on account size
    
    Args:
        account_balance: Current account balance
        
    Returns:
        Adjusted configuration for account size
    """
    config = CreditSpreadConfig()
    config.account_balance = account_balance
    
    # Scale targets proportionally
    base_account = 25000.0
    scale_factor = account_balance / base_account
    
    config.daily_profit_target = 200.0 * scale_factor
    config.daily_loss_limit = -400.0 * scale_factor
    
    # Adjust position limits for smaller accounts
    if account_balance < 10000:
        config.max_concurrent_positions = 2
        config.max_risk_per_trade_pct = 0.015  # More conservative
    elif account_balance < 50000:
        config.max_concurrent_positions = 3
    else:
        config.max_concurrent_positions = 5    # Larger accounts can handle more
    
    return config

def validate_config(config: CreditSpreadConfig) -> List[str]:
    """
    Validate configuration parameters
    
    Args:
        config: Configuration to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Risk validation
    if config.max_risk_per_trade_pct > 0.05:
        errors.append("Max risk per trade should not exceed 5%")
    
    if config.daily_loss_limit > -config.daily_profit_target:
        errors.append("Daily loss limit should be at least 2x profit target")
    
    # Time validation
    if config.market_close_time <= config.market_open_time:
        errors.append("Market close time must be after open time")
    
    # Spread validation
    if config.min_premium_collected >= config.max_premium_collected:
        errors.append("Min premium must be less than max premium")
    
    if config.target_delta < 0.1 or config.target_delta > 0.4:
        errors.append("Target delta should be between 0.1 and 0.4")
    
    return errors

if __name__ == "__main__":
    # Test configuration
    config = DEFAULT_CONFIG
    errors = validate_config(config)
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ Configuration Valid")
        print(f"📊 Target: ${config.daily_profit_target}/day with ${config.account_balance:,.0f} account")
        print(f"⚠️  Max Risk: {config.max_risk_per_trade_pct*100:.1f}% per trade, {config.max_daily_risk_pct*100:.1f}% daily")
        print(f"🎯 Win Rate Target: {config.target_win_rate*100:.0f}%")
