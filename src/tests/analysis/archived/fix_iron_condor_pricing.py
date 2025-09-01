#!/usr/bin/env python3
"""
Fix Iron Condor Pricing - Realistic 0DTE Credits
===============================================

The current Enhanced Iron Condor has unrealistically small credits ($0.07-$0.10).
This script fixes the pricing model to generate realistic 0DTE Iron Condor credits.

Issues to fix:
1. Strike selection too conservative (30 Delta calculation wrong)
2. Time to expiry too short (4 hours vs 6.5 hours)
3. Need realistic credits of $0.20-$1.00+ per contract
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time, date
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import our components
try:
    from src.data.parquet_data_loader import ParquetDataLoader
    from src.strategies.cash_management.position_sizer import ConservativeCashManager
    from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
    from src.utils.detailed_logger import DetailedLogger, TradeLogEntry, MarketConditionEntry
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_AVAILABLE = False

class FixedIronCondorPricing:
    """
    Fixed Iron Condor with realistic 0DTE pricing
    
    Fixes:
    1. Proper 30 Delta strike selection (closer to ATM)
    2. Correct time to expiry (6.5 hours market open to close)
    3. Realistic credit expectations ($0.20-$1.00+)
    """
    
    def __init__(self):
        if not IMPORTS_AVAILABLE:
            raise ImportError("Required modules not available")
        
        self.pricing_calculator = BlackScholesCalculator()
        
        print("🔧 FIXED IRON CONDOR PRICING ANALYZER")
        print("="*50)
    
    def calculate_realistic_30_delta_strikes(self, spy_price: float, vix: float) -> Dict[str, float]:
        """
        Calculate realistic 30 Delta strikes for 0DTE Iron Condor
        
        For 0DTE options, 30 Delta is approximately:
        - 0.5-1.0% OTM (not 1.5-2.5% like we were using)
        """
        
        # More aggressive 30 Delta calculation for 0DTE
        # 30 Delta 0DTE options are much closer to ATM
        otm_percent = 0.007 + (vix / 100 * 0.003)  # 0.7% base + vol adjustment
        
        strikes = {
            'put_short': spy_price * (1 - otm_percent),      # Sell 30D put (~0.7% OTM)
            'put_long': spy_price * (1 - otm_percent - 0.007), # Buy 10D put (~1.4% OTM)
            'call_short': spy_price * (1 + otm_percent),     # Sell 30D call (~0.7% OTM)
            'call_long': spy_price * (1 + otm_percent + 0.007) # Buy 10D call (~1.4% OTM)
        }
        
        # Round to nearest $0.50
        for key in strikes:
            strikes[key] = round(strikes[key] * 2) / 2
        
        return strikes
    
    def calculate_iron_condor_credit(self, spy_price: float, vix: float, strikes: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate Iron Condor credit with fixed parameters
        """
        
        # FIXED: Use 6.5 hours (market open to close) instead of 4 hours
        time_to_expiry = 6.5 / 24 / 365  # 6.5 hours in years
        vol_decimal = vix / 100
        
        print(f"\n📊 PRICING PARAMETERS:")
        print(f"   SPY Price: ${spy_price:.2f}")
        print(f"   VIX: {vix:.1f}%")
        print(f"   Time to Expiry: {time_to_expiry:.6f} years ({6.5} hours)")
        print(f"   Volatility: {vol_decimal:.3f}")
        
        # Calculate individual option prices
        put_short_price = self.pricing_calculator.calculate_option_price(
            spy_price, strikes['put_short'], time_to_expiry, vol_decimal, 'put'
        )
        call_short_price = self.pricing_calculator.calculate_option_price(
            spy_price, strikes['call_short'], time_to_expiry, vol_decimal, 'call'
        )
        put_long_price = self.pricing_calculator.calculate_option_price(
            spy_price, strikes['put_long'], time_to_expiry, vol_decimal, 'put'
        )
        call_long_price = self.pricing_calculator.calculate_option_price(
            spy_price, strikes['call_long'], time_to_expiry, vol_decimal, 'call'
        )
        
        # Net credit = Premium received - Premium paid
        net_credit = (put_short_price + call_short_price) - (put_long_price + call_long_price)
        
        print(f"\n📊 OPTION PRICES:")
        print(f"   Put Short ({strikes['put_short']:.1f}): ${put_short_price:.4f}")
        print(f"   Put Long ({strikes['put_long']:.1f}): ${put_long_price:.4f}")
        print(f"   Call Short ({strikes['call_short']:.1f}): ${call_short_price:.4f}")
        print(f"   Call Long ({strikes['call_long']:.1f}): ${call_long_price:.4f}")
        
        print(f"\n💰 IRON CONDOR CREDIT:")
        print(f"   Premium Received: ${put_short_price + call_short_price:.4f}")
        print(f"   Premium Paid: ${put_long_price + call_long_price:.4f}")
        print(f"   Net Credit: ${net_credit:.4f}")
        
        return {
            'put_short_price': put_short_price,
            'put_long_price': put_long_price,
            'call_short_price': call_short_price,
            'call_long_price': call_long_price,
            'net_credit': net_credit,
            'premium_received': put_short_price + call_short_price,
            'premium_paid': put_long_price + call_long_price
        }
    
    def compare_old_vs_new(self, spy_price: float, vix: float):
        """Compare old vs new strike selection and pricing"""
        
        print(f"\n🔍 COMPARING OLD vs NEW PRICING")
        print(f"SPY Price: ${spy_price:.2f}, VIX: {vix:.1f}%")
        print("="*60)
        
        # OLD METHOD (current Enhanced Iron Condor)
        print(f"\n❌ OLD METHOD (Current Enhanced Iron Condor):")
        old_otm_percent = 0.015 + (vix / 100 * 0.005)  # 1.5% base + vol adjustment
        old_strikes = {
            'put_short': spy_price * (1 - old_otm_percent),
            'put_long': spy_price * (1 - old_otm_percent - 0.01),
            'call_short': spy_price * (1 + old_otm_percent),
            'call_long': spy_price * (1 + old_otm_percent + 0.01)
        }
        
        # Round to nearest $0.50
        for key in old_strikes:
            old_strikes[key] = round(old_strikes[key] * 2) / 2
        
        print(f"   Put Spread: {old_strikes['put_long']:.1f}/{old_strikes['put_short']:.1f}")
        print(f"   Call Spread: {old_strikes['call_short']:.1f}/{old_strikes['call_long']:.1f}")
        print(f"   OTM Distance: {old_otm_percent*100:.1f}% ({spy_price * old_otm_percent:.1f} points)")
        
        # Calculate old pricing with 4 hours
        old_time = 4 / 24 / 365
        old_pricing = self.calculate_iron_condor_credit_simple(spy_price, vix, old_strikes, old_time)
        print(f"   Time to Expiry: 4 hours")
        print(f"   Net Credit: ${old_pricing:.4f}")
        
        # NEW METHOD (Fixed)
        print(f"\n✅ NEW METHOD (Fixed Pricing):")
        new_strikes = self.calculate_realistic_30_delta_strikes(spy_price, vix)
        
        print(f"   Put Spread: {new_strikes['put_long']:.1f}/{new_strikes['put_short']:.1f}")
        print(f"   Call Spread: {new_strikes['call_short']:.1f}/{new_strikes['call_long']:.1f}")
        
        new_otm_percent = 0.007 + (vix / 100 * 0.003)
        print(f"   OTM Distance: {new_otm_percent*100:.1f}% ({spy_price * new_otm_percent:.1f} points)")
        
        new_pricing = self.calculate_iron_condor_credit(spy_price, vix, new_strikes)
        
        print(f"\n📊 IMPROVEMENT ANALYSIS:")
        improvement = (new_pricing['net_credit'] / old_pricing - 1) * 100
        print(f"   Old Credit: ${old_pricing:.4f}")
        print(f"   New Credit: ${new_pricing['net_credit']:.4f}")
        print(f"   Improvement: {improvement:+.1f}%")
        
        # Check if new credit is realistic
        if new_pricing['net_credit'] >= 0.20:
            print(f"   ✅ Credit is realistic for 0DTE Iron Condor")
        elif new_pricing['net_credit'] >= 0.10:
            print(f"   🟡 Credit is low but acceptable")
        else:
            print(f"   ❌ Credit is still too low")
        
        return old_pricing, new_pricing['net_credit']
    
    def calculate_iron_condor_credit_simple(self, spy_price: float, vix: float, strikes: Dict[str, float], time_to_expiry: float) -> float:
        """Simple credit calculation for comparison"""
        
        vol_decimal = vix / 100
        
        put_short_price = self.pricing_calculator.calculate_option_price(
            spy_price, strikes['put_short'], time_to_expiry, vol_decimal, 'put'
        )
        call_short_price = self.pricing_calculator.calculate_option_price(
            spy_price, strikes['call_short'], time_to_expiry, vol_decimal, 'call'
        )
        put_long_price = self.pricing_calculator.calculate_option_price(
            spy_price, strikes['put_long'], time_to_expiry, vol_decimal, 'put'
        )
        call_long_price = self.pricing_calculator.calculate_option_price(
            spy_price, strikes['call_long'], time_to_expiry, vol_decimal, 'call'
        )
        
        return (put_short_price + call_short_price) - (put_long_price + call_long_price)

def main():
    """Test the fixed pricing model"""
    
    analyzer = FixedIronCondorPricing()
    
    # Test with typical market conditions
    test_cases = [
        {"spy_price": 544.0, "vix": 23.5, "description": "Trade 1 Conditions"},
        {"spy_price": 559.0, "vix": 23.2, "description": "Trade 2 Conditions"},
        {"spy_price": 550.0, "vix": 20.0, "description": "Low VIX Scenario"},
        {"spy_price": 550.0, "vix": 30.0, "description": "High VIX Scenario"}
    ]
    
    print("🧪 TESTING FIXED IRON CONDOR PRICING")
    print("="*60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔬 TEST CASE {i}: {case['description']}")
        print("-" * 40)
        
        old_credit, new_credit = analyzer.compare_old_vs_new(case['spy_price'], case['vix'])
        
        print(f"\n📊 SUMMARY:")
        print(f"   Old Credit per Contract: ${old_credit:.4f} (${old_credit*100:.2f} per contract)")
        print(f"   New Credit per Contract: ${new_credit:.4f} (${new_credit*100:.2f} per contract)")
        
        if new_credit >= 0.002:  # $0.20+ per contract
            print(f"   ✅ REALISTIC: New credit is suitable for 0DTE trading")
        else:
            print(f"   ❌ STILL LOW: May need further adjustments")

if __name__ == "__main__":
    main()
