#!/usr/bin/env python3
"""
Credit Spread Optimizer Package
===============================

Professional-grade credit spread trading system targeting $200/day profit
with $25k account using Kelly Criterion position sizing and advanced risk management.

Following @.cursorrules architecture patterns.
"""

from .config import (
    CreditSpreadConfig,
    KellyCriterionConfig, 
    MarketFilterConfig,
    DEFAULT_CONFIG,
    KELLY_CONFIG,
    FILTER_CONFIG,
    get_config_for_account_size,
    validate_config
)

from .kelly_position_sizer import (
    KellyPositionSizer,
    KellyMetrics,
    TradeResult
)

from .profit_manager import (
    ProfitManager,
    Position,
    ExitSignal
)

__version__ = "1.0.0"
__author__ = "Advanced 0DTE Trading System"

# Package exports
__all__ = [
    # Configuration
    "CreditSpreadConfig",
    "KellyCriterionConfig", 
    "MarketFilterConfig",
    "DEFAULT_CONFIG",
    "KELLY_CONFIG", 
    "FILTER_CONFIG",
    "get_config_for_account_size",
    "validate_config",
    
    # Position Sizing
    "KellyPositionSizer",
    "KellyMetrics",
    "TradeResult",
    
    # Profit Management
    "ProfitManager", 
    "Position",
    "ExitSignal"
]
