"""
Enhanced 0DTE Strategy Configuration
===================================

Configuration parameters for the Enhanced 0DTE strategy addressing
key insights from 0DTE trading analysis.
"""

from typing import Dict, Any

# Enhanced confidence thresholds (addressing higher conviction needs)
MIN_CONFIDENCE_THRESHOLDS = {
    'HIGH_VOLATILITY': 70,  # Higher conviction needed in volatile markets
    'HIGH_FEAR': 68,
    'NEUTRAL': 65,
    'BULLISH': 62,
    'LOW_VOLATILITY': 60
}

# Greeks-based filters
DELTA_FILTERS = {
    'min_delta': 0.15,  # Avoid deep OTM with low delta
    'max_delta': 0.85,  # Avoid deep ITM with high delta
    'gamma_risk_threshold': 0.05  # High gamma = high risk for 0DTE
}

# Liquidity filters (addressing slippage concerns)
LIQUIDITY_FILTERS = {
    'min_volume': 10,
    'min_transactions': 2,
    'max_estimated_spread_pct': 15,  # Max 15% spread
    'min_vwap_stability': 0.95  # VWAP vs close price stability
}

# Risk management parameters
RISK_PARAMS = {
    'position_size_base': 0.02,  # 2% of capital per trade
    'max_gamma_exposure': 0.10,  # Max 10% gamma exposure
    'theta_decay_protection': -5,  # Exit if theta > -$5/day
    'delta_hedge_threshold': 0.3  # Hedge if delta > 30%
}

# Market regime parameters
REGIME_PARAMS = {
    'HIGH_VOLATILITY': {
        'prefer_credit_spreads': True,
        'max_dte': 0,  # Only 0DTE in high vol
        'delta_target': 0.3,
        'gamma_limit': 0.03
    },
    'LOW_VOLATILITY': {
        'prefer_credit_spreads': True,
        'max_dte': 1,  # Allow 1DTE
        'delta_target': 0.4,
        'gamma_limit': 0.05
    },
    'NEUTRAL': {
        'prefer_credit_spreads': False,
        'max_dte': 0,
        'delta_target': 0.35,
        'gamma_limit': 0.04
    }
}

def get_strategy_config() -> Dict[str, Any]:
    """Get complete strategy configuration"""
    return {
        'min_confidence_thresholds': MIN_CONFIDENCE_THRESHOLDS,
        'delta_filters': DELTA_FILTERS,
        'liquidity_filters': LIQUIDITY_FILTERS,
        'risk_params': RISK_PARAMS,
        'regime_params': REGIME_PARAMS
    }
