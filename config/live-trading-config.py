#!/usr/bin/env python3
"""
Live Trading Configuration
==========================

Configuration settings for the live Iron Condor paper trading system.
Centralizes all trading parameters, risk management settings, and
system configuration in one place.

Location: config/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Configuration Module
"""

import os
from datetime import time
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AlpacaConfig:
    """Alpaca API configuration"""
    api_key: str
    secret_key: str
    base_url: str = "https://paper-api.alpaca.markets"  # Paper trading
    data_url: str = "https://data.alpaca.markets"
    is_paper: bool = True
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls(
            api_key=os.getenv('ALPACA_API_KEY', ''),
            secret_key=os.getenv('ALPACA_SECRET_KEY', ''),
            is_paper=os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
        )

@dataclass
class TradingConfig:
    """Core trading configuration (EXACT MATCH to successful backtesting system)"""
    # Account settings (EXACT MATCH)
    initial_balance: float = 25000.0      # EXACT: $25K account
    daily_profit_target: float = 250.0    # EXACT: $250/day target
    max_daily_loss: float = 500.0         # EXACT: $500 max daily loss
    
    # Position management (EXACT MATCH)
    max_positions: int = 2                # EXACT: max 2 positions
    max_hold_hours: float = 4.0           # EXACT: 4 hour max hold for 0DTE
    max_signals_per_day: int = 3          # Conservative limit (backtesting had 2 max)
    
    # Risk management (EXACT MATCH)
    profit_target_pct: float = 0.50       # EXACT: 50% of max profit
    stop_loss_pct: float = 0.50           # EXACT: 50% of max loss
    max_risk_per_trade_pct: float = 0.02  # EXACT: 2% account risk
    
    # Iron Condor specific (EXACT MATCH)
    iron_condor_min_credit: float = 0.05  # EXACT: $0.05 minimum credit
    iron_condor_max_width: float = 10.0   # EXACT: $10 maximum width
    contracts_per_trade: int = 5          # EXACT: 5 contracts per trade
    
    # Market detection (EXACT MATCH)
    flat_market_pc_ratio_min: float = 0.85  # EXACT: 0.85 P/C ratio minimum
    flat_market_pc_ratio_max: float = 1.15  # EXACT: 1.15 P/C ratio maximum
    flat_market_min_volume: int = 100       # EXACT: 100 minimum volume
    
    # Entry timing (market hours ET)
    entry_times: List[time] = None
    
    def __post_init__(self):
        if self.entry_times is None:
            # EXACT MATCH to backtesting entry times
            self.entry_times = [
                time(10, 0),   # EXACT: Market open momentum
                time(11, 30),  # EXACT: Mid-morning
                time(13, 0),   # EXACT: Lunch time
                time(14, 30)   # EXACT: Afternoon momentum
            ]

@dataclass
class MarketHoursConfig:
    """Market hours configuration"""
    market_open: time = time(9, 30)   # 9:30 AM ET
    market_close: time = time(16, 0)  # 4:00 PM ET
    early_close_warning: time = time(15, 45)  # 15 minutes before close
    
    # Days of week (0=Monday, 6=Sunday)
    trading_days: List[int] = None
    
    def __post_init__(self):
        if self.trading_days is None:
            self.trading_days = [0, 1, 2, 3, 4]  # Monday-Friday

@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    log_directory: str = "logs"
    log_file_prefix: str = "live_iron_condor"
    
    # Performance logging
    log_trades: bool = True
    log_signals: bool = True
    log_positions: bool = True
    log_performance: bool = True

@dataclass
class NotificationConfig:
    """Notification configuration"""
    enable_notifications: bool = False
    
    # Email notifications
    enable_email: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    
    # Slack notifications
    enable_slack: bool = False
    slack_webhook_url: str = ""
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []

@dataclass
class LiveTradingSystemConfig:
    """Complete live trading system configuration"""
    alpaca: AlpacaConfig
    trading: TradingConfig
    market_hours: MarketHoursConfig
    logging: LoggingConfig
    notifications: NotificationConfig
    
    # System settings
    update_interval_seconds: int = 60
    position_update_interval_seconds: int = 30
    
    # Safety settings
    enable_circuit_breakers: bool = True
    max_consecutive_losses: int = 3
    emergency_stop_loss_pct: float = 0.10  # 10% account loss
    
    @classmethod
    def create_default(cls):
        """Create default configuration"""
        return cls(
            alpaca=AlpacaConfig.from_env(),
            trading=TradingConfig(),
            market_hours=MarketHoursConfig(),
            logging=LoggingConfig(),
            notifications=NotificationConfig()
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        # Validate Alpaca credentials
        if not self.alpaca.api_key:
            errors.append("ALPACA_API_KEY not set")
        if not self.alpaca.secret_key:
            errors.append("ALPACA_SECRET_KEY not set")
        
        # Validate trading parameters
        if self.trading.initial_balance <= 0:
            errors.append("Initial balance must be positive")
        if self.trading.max_daily_loss <= 0:
            errors.append("Max daily loss must be positive")
        if self.trading.daily_profit_target <= 0:
            errors.append("Daily profit target must be positive")
        
        # Validate risk parameters
        if not 0 < self.trading.profit_target_pct < 1:
            errors.append("Profit target percentage must be between 0 and 1")
        if not 0 < self.trading.stop_loss_pct < 1:
            errors.append("Stop loss percentage must be between 0 and 1")
        
        # Validate Iron Condor parameters
        if self.trading.iron_condor_min_credit <= 0:
            errors.append("Iron Condor minimum credit must be positive")
        if self.trading.contracts_per_trade <= 0:
            errors.append("Contracts per trade must be positive")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'alpaca': {
                'api_key': '***' if self.alpaca.api_key else '',
                'secret_key': '***' if self.alpaca.secret_key else '',
                'base_url': self.alpaca.base_url,
                'is_paper': self.alpaca.is_paper
            },
            'trading': {
                'initial_balance': self.trading.initial_balance,
                'daily_profit_target': self.trading.daily_profit_target,
                'max_daily_loss': self.trading.max_daily_loss,
                'max_positions': self.trading.max_positions,
                'max_hold_hours': self.trading.max_hold_hours,
                'profit_target_pct': self.trading.profit_target_pct,
                'stop_loss_pct': self.trading.stop_loss_pct,
                'iron_condor_min_credit': self.trading.iron_condor_min_credit,
                'contracts_per_trade': self.trading.contracts_per_trade,
                'entry_times': [t.strftime('%H:%M') for t in self.trading.entry_times]
            },
            'market_hours': {
                'market_open': self.market_hours.market_open.strftime('%H:%M'),
                'market_close': self.market_hours.market_close.strftime('%H:%M'),
                'trading_days': self.market_hours.trading_days
            },
            'logging': {
                'log_level': self.logging.log_level,
                'log_to_file': self.logging.log_to_file,
                'log_directory': self.logging.log_directory
            },
            'system': {
                'update_interval_seconds': self.update_interval_seconds,
                'enable_circuit_breakers': self.enable_circuit_breakers,
                'max_consecutive_losses': self.max_consecutive_losses
            }
        }

# Pre-defined configurations for different scenarios

def get_conservative_config() -> LiveTradingSystemConfig:
    """Conservative trading configuration"""
    config = LiveTradingSystemConfig.create_default()
    
    # More conservative settings
    config.trading.max_positions = 1
    config.trading.max_signals_per_day = 2
    config.trading.max_risk_per_trade_pct = 0.015  # 1.5% risk
    config.trading.profit_target_pct = 0.40  # Take profits earlier
    config.trading.stop_loss_pct = 0.40   # Tighter stop loss
    
    return config

def get_aggressive_config() -> LiveTradingSystemConfig:
    """Aggressive trading configuration"""
    config = LiveTradingSystemConfig.create_default()
    
    # More aggressive settings
    config.trading.max_positions = 3
    config.trading.max_signals_per_day = 5
    config.trading.max_risk_per_trade_pct = 0.025  # 2.5% risk
    config.trading.profit_target_pct = 0.60  # Hold for more profit
    config.trading.stop_loss_pct = 0.60   # Wider stop loss
    config.trading.daily_profit_target = 350.0  # Higher target
    
    return config

def get_development_config() -> LiveTradingSystemConfig:
    """Development/testing configuration"""
    config = LiveTradingSystemConfig.create_default()
    
    # Development settings
    config.trading.initial_balance = 10000.0  # Smaller account
    config.trading.daily_profit_target = 100.0
    config.trading.max_daily_loss = 200.0
    config.trading.max_positions = 1
    config.trading.contracts_per_trade = 1
    config.update_interval_seconds = 30  # More frequent updates
    
    # Enhanced logging for development
    config.logging.log_level = "DEBUG"
    config.logging.log_trades = True
    config.logging.log_signals = True
    config.logging.log_positions = True
    
    return config

# Configuration validation and loading
def load_config(config_type: str = "default") -> LiveTradingSystemConfig:
    """Load configuration by type"""
    if config_type == "conservative":
        return get_conservative_config()
    elif config_type == "aggressive":
        return get_aggressive_config()
    elif config_type == "development":
        return get_development_config()
    else:
        return LiveTradingSystemConfig.create_default()

def validate_environment() -> List[str]:
    """Validate environment setup for live trading"""
    errors = []
    
    # Check required environment variables
    required_env_vars = ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY']
    for var in required_env_vars:
        if not os.getenv(var):
            errors.append(f"Environment variable {var} not set")
    
    # Check optional environment variables
    optional_env_vars = {
        'ALPACA_PAPER': 'true',
        'LOG_LEVEL': 'INFO',
        'TRADING_CONFIG_TYPE': 'default'
    }
    
    for var, default in optional_env_vars.items():
        if not os.getenv(var):
            print(f"⚠️ Optional environment variable {var} not set, using default: {default}")
    
    return errors

# Example usage
if __name__ == "__main__":
    # Validate environment
    env_errors = validate_environment()
    if env_errors:
        print("❌ Environment validation errors:")
        for error in env_errors:
            print(f"   - {error}")
        exit(1)
    
    # Load configuration
    config_type = os.getenv('TRADING_CONFIG_TYPE', 'default')
    config = load_config(config_type)
    
    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        print("❌ Configuration validation errors:")
        for error in config_errors:
            print(f"   - {error}")
        exit(1)
    
    print(f"✅ Configuration loaded successfully ({config_type})")
    print(f"   Initial Balance: ${config.trading.initial_balance:,.2f}")
    print(f"   Daily Target: ${config.trading.daily_profit_target}")
    print(f"   Max Daily Loss: ${config.trading.max_daily_loss}")
    print(f"   Paper Trading: {config.alpaca.is_paper}")
    print(f"   Entry Times: {[t.strftime('%H:%M') for t in config.trading.entry_times]}")
