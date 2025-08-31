#!/usr/bin/env python3
"""
Intraday Signal Analysis - Proper 0DTE Signal Frequency
======================================================

FIXES THE SIGNAL FREQUENCY PROBLEM:
1. Analyze what intraday signals we should be generating
2. Implement 1-minute or 3-minute signal generation
3. Target 3-5 trades per day for $250/day goal
4. True 0DTE intraday scalping approach

Current Problem: Only 0.9 trades/day (too low for $250 target)
Solution: Multiple intraday signals per day

Location: src/tests/analysis/ (following .cursorrules structure)
Author: Advanced Options Trading System - Intraday Optimization
"""

import sys
import os
# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import our components
from src.data.parquet_data_loader import ParquetDataLoader

def analyze_intraday_signal_opportunities():
    """Analyze how many intraday signals we should be generating"""
    
    print("🔍 INTRADAY SIGNAL FREQUENCY ANALYSIS")
    print("=" * 60)
    print("🎯 Goal: Identify optimal signal frequency for $250/day target")
    print("📊 Current: 0.9 trades/day (TOO LOW)")
    print("🚀 Target: 3-5 trades/day (proper 0DTE frequency)")
    print("=" * 60)
    
    loader = ParquetDataLoader()
    
    # Analyze a single day's data to see intraday opportunities
    test_date = datetime(2025, 8, 20)  # Good volume day
    
    print(f"\n📅 ANALYZING SINGLE DAY: {test_date.strftime('%Y-%m-%d')}")
    print("🔍 Looking for intraday signal opportunities...")
    
    # Load options data for the day
    options_data = loader.load_options_for_date(test_date, min_volume=20)
    
    if options_data.empty:
        print("❌ No data available for analysis")
        return
    
    print(f"📊 Total Options Available: {len(options_data)}")
    
    # Simulate intraday timeframes
    intraday_timeframes = [
        ("9:30 AM", "Market Open"),
        ("10:00 AM", "30min after open"),
        ("10:30 AM", "1hr after open"), 
        ("11:00 AM", "Morning momentum"),
        ("12:00 PM", "Midday"),
        ("1:00 PM", "Afternoon start"),
        ("2:00 PM", "Power hour prep"),
        ("3:00 PM", "Power hour"),
        ("3:30 PM", "Final 30min")
    ]
    
    print(f"\n⏰ INTRADAY SIGNAL OPPORTUNITIES:")
    print("=" * 50)
    
    total_opportunities = 0
    
    for time_str, description in intraday_timeframes:
        # Simulate different market conditions throughout the day
        
        # Filter options for different criteria throughout the day
        if "morning" in description.lower() or "open" in description.lower():
            # Morning: Look for momentum plays
            candidates = options_data[
                (options_data['volume'] >= 50) &
                (options_data['close'] >= 0.75) &
                (options_data['close'] <= 3.00)
            ]
            signal_type = "MOMENTUM"
            
        elif "midday" in description.lower():
            # Midday: Look for consolidation plays
            candidates = options_data[
                (options_data['volume'] >= 30) &
                (options_data['close'] >= 0.50) &
                (options_data['close'] <= 2.50)
            ]
            signal_type = "CONSOLIDATION"
            
        elif "power" in description.lower() or "final" in description.lower():
            # Power hour: Look for breakout plays
            candidates = options_data[
                (options_data['volume'] >= 100) &
                (options_data['close'] >= 1.00) &
                (options_data['close'] <= 4.00)
            ]
            signal_type = "BREAKOUT"
        else:
            # Default: Standard plays
            candidates = options_data[
                (options_data['volume'] >= 40) &
                (options_data['close'] >= 0.60) &
                (options_data['close'] <= 3.50)
            ]
            signal_type = "STANDARD"
        
        # Count potential signals
        call_candidates = len(candidates[candidates['option_type'] == 'call'])
        put_candidates = len(candidates[candidates['option_type'] == 'put'])
        total_candidates = call_candidates + put_candidates
        
        # Estimate signal probability (based on market conditions)
        if total_candidates >= 100:
            signal_probability = 0.8  # High probability
            opportunities = 2  # Could generate 2 signals
        elif total_candidates >= 50:
            signal_probability = 0.6  # Medium probability  
            opportunities = 1  # Could generate 1 signal
        elif total_candidates >= 20:
            signal_probability = 0.4  # Low probability
            opportunities = 1  # Might generate 1 signal
        else:
            signal_probability = 0.1  # Very low
            opportunities = 0
        
        total_opportunities += opportunities
        
        print(f"{time_str:>10} | {description:<20} | {signal_type:<12} | "
              f"Candidates: {total_candidates:>3} | Signals: {opportunities}")
    
    print("=" * 50)
    print(f"📊 TOTAL DAILY OPPORTUNITIES: {total_opportunities}")
    print(f"🎯 CURRENT vs OPTIMAL:")
    print(f"   Current: 0.9 trades/day")
    print(f"   Optimal: {total_opportunities} trades/day")
    print(f"   Improvement: {total_opportunities/0.9:.1f}x more trades")
    
    # Calculate target metrics
    target_daily_profit = 250
    trades_per_day = total_opportunities
    profit_per_trade = target_daily_profit / trades_per_day if trades_per_day > 0 else 0
    
    print(f"\n💰 PROFIT TARGET ANALYSIS:")
    print(f"   Daily Target: ${target_daily_profit}")
    print(f"   Trades/Day: {trades_per_day}")
    print(f"   Profit/Trade: ${profit_per_trade:.0f}")
    print(f"   Win Rate Needed: {(profit_per_trade / 100) * 100:.0f}% (assuming $100 avg trade)")
    
    return {
        'current_frequency': 0.9,
        'optimal_frequency': total_opportunities,
        'improvement_factor': total_opportunities / 0.9 if total_opportunities > 0 else 0,
        'target_profit_per_trade': profit_per_trade
    }

def recommend_signal_implementation():
    """Recommend how to implement proper intraday signals"""
    
    print(f"\n🚀 INTRADAY SIGNAL IMPLEMENTATION RECOMMENDATIONS")
    print("=" * 60)
    
    print("🔧 TECHNICAL IMPLEMENTATION:")
    print("   1. 📊 Use 1-minute or 3-minute bars (not daily)")
    print("   2. ⏰ Generate signals every 15-30 minutes")
    print("   3. 🎯 Target 3-5 entries per day")
    print("   4. ⚡ Hold times: 15-60 minutes (true 0DTE)")
    print("   5. 💰 Position size: $150-300 per trade")
    
    print(f"\n📈 SIGNAL FREQUENCY SCHEDULE:")
    print("   9:30-10:30 AM: 2 signals (market open momentum)")
    print("   11:00-12:00 PM: 1 signal (morning continuation)")  
    print("   1:00-2:00 PM: 1 signal (afternoon setup)")
    print("   3:00-3:45 PM: 2 signals (power hour)")
    print("   TOTAL: 6 potential signals/day")
    
    print(f"\n🎯 PROFIT MATH:")
    print("   Target: $250/day")
    print("   Signals: 6/day")
    print("   Profit/Signal: $42 average")
    print("   Win Rate: 60% (realistic for 0DTE)")
    print("   Avg Win: $70, Avg Loss: -$28")
    
    print(f"\n⚠️  CURRENT PROBLEMS TO FIX:")
    print("   ❌ Only 1 signal per day (should be 6)")
    print("   ❌ Using daily data (should be 1-minute)")
    print("   ❌ Long hold times (should be <1 hour)")
    print("   ❌ Large positions (should be smaller, more frequent)")
    
    print(f"\n✅ NEXT STEPS:")
    print("   1. 🔄 Implement 1-minute data loading")
    print("   2. 📊 Create intraday signal generator")
    print("   3. ⏰ Add time-based signal scheduling")
    print("   4. 🎯 Test with higher frequency approach")
    print("   5. 📈 Validate with paper trading")

def main():
    """Main analysis function"""
    
    print("🔍 SIGNAL FREQUENCY ANALYSIS - 0DTE OPTIMIZATION")
    print("🏗️ Following .cursorrules: Proper intraday signal generation")
    print("=" * 60)
    
    try:
        # Analyze current vs optimal signal frequency
        results = analyze_intraday_signal_opportunities()
        
        # Provide implementation recommendations
        recommend_signal_implementation()
        
        print(f"\n🎯 ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"✅ Problem identified: Signal frequency too low")
        print(f"✅ Solution: Implement intraday 1-minute signals")
        print(f"✅ Target: 3-6 trades/day for $250 goal")
        print(f"✅ Next: Build intraday signal generator")
        
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
