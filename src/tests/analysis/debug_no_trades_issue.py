#!/usr/bin/env python3
"""
Debug No Trades Issue
=====================

Investigate why the Optimized Adaptive Router is not trading on Days 2-5.
Following @.cursorrules testing patterns.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, time
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.strategies.adaptive_zero_dte.optimized_adaptive_router import OptimizedAdaptiveRouter
from src.data.parquet_data_loader import ParquetDataLoader

def debug_specific_day(date_str="2024-03-05"):
    """Debug why no trades are happening on a specific date"""
    
    print(f"🔍 DEBUGGING NO TRADES ON {date_str}")
    print("="*60)
    
    # Initialize components
    data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
    data_loader = ParquetDataLoader(parquet_path=data_path)
    router = OptimizedAdaptiveRouter(25000)
    
    # Load data for the date
    test_date = datetime.strptime(date_str, "%Y-%m-%d")
    options_data = data_loader.load_options_for_date(test_date)
    
    print(f"📊 Options data loaded: {len(options_data)} records")
    
    # Test at different times during the day
    test_times = [
        test_date.replace(hour=10, minute=0),   # 10:00 AM
        test_date.replace(hour=12, minute=0),   # 12:00 PM  
        test_date.replace(hour=14, minute=0),   # 2:00 PM
    ]
    
    spy_price = options_data['strike'].median() if 'strike' in options_data.columns else 515.0
    
    for test_time in test_times:
        print(f"\n⏰ TESTING TIME: {test_time.strftime('%H:%M')}")
        
        # Create market data
        market_data = {
            'spy_price': spy_price,
            'timestamp': test_time,
            'spy_volume': 2000000
        }
        
        # Reset daily tracking
        router._check_daily_reset(test_time)
        
        # Step 1: Check pre-flight conditions
        can_trade, reason = router._pre_flight_checks(test_time)
        print(f"   ✅ Pre-flight Check: {can_trade}")
        if not can_trade:
            print(f"   ❌ Blocked: {reason}")
            continue
        
        # Step 2: Get market intelligence
        intelligence = router.intelligence_engine.analyze_market_intelligence(options_data, spy_price)
        print(f"   🧠 Market Intelligence:")
        print(f"      Regime: {intelligence.primary_regime}")
        print(f"      Confidence: {intelligence.regime_confidence:.1f}%")
        print(f"      Bull Score: {intelligence.bull_score:.1f}")
        print(f"      Bear Score: {intelligence.bear_score:.1f}")
        print(f"      Neutral Score: {intelligence.neutral_score:.1f}")
        
        # Step 3: Check strategy selection
        strategy_rec = router.select_adaptive_strategy(options_data, market_data, test_time)
        print(f"   🎯 Strategy Selection:")
        print(f"      Strategy: {strategy_rec['strategy_type']}")
        print(f"      Confidence: {strategy_rec.get('confidence', 0):.1f}%")
        print(f"      Reason: {strategy_rec.get('reason', 'N/A')}")
        
        # Step 4: Check confidence thresholds
        confidence = strategy_rec.get('confidence', 0)
        regime = intelligence.primary_regime
        
        print(f"   📊 Threshold Analysis:")
        if regime == 'BULLISH':
            threshold = 35  # From enhanced_adaptive_router.py
            print(f"      BULLISH threshold: {threshold}% (Current: {confidence:.1f}%)")
            if confidence > threshold:
                print(f"      ✅ Should trade BULL_PUT_SPREAD")
            else:
                print(f"      ❌ Below threshold")
        elif regime == 'BEARISH':
            threshold = 35
            print(f"      BEARISH threshold: {threshold}% (Current: {confidence:.1f}%)")
            if confidence > threshold:
                print(f"      ✅ Should trade BEAR_CALL_SPREAD")
            else:
                print(f"      ❌ Below threshold")
        elif regime == 'NEUTRAL':
            threshold = 60
            print(f"      NEUTRAL threshold: {threshold}% (Current: {confidence:.1f}%)")
            if confidence > threshold:
                print(f"      ✅ Should trade IRON_CONDOR")
            else:
                print(f"      ❌ Below threshold")
        
        # Step 5: Check position sizing
        if strategy_rec['strategy_type'] != 'NO_TRADE':
            position_result = router.position_sizer.get_position_sizing(0.40, 1.20)
            print(f"   💰 Position Sizing:")
            print(f"      Can Trade: {position_result.can_trade}")
            print(f"      Contracts: {position_result.contracts}")
            print(f"      Max Risk: ${position_result.max_risk_dollars:.2f}")

def compare_trading_vs_non_trading_days():
    """Compare Day 1 (trading) vs Day 2 (no trading) to find differences"""
    
    print(f"\n🔍 COMPARING TRADING DAY 1 vs NON-TRADING DAY 2")
    print("="*60)
    
    data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
    data_loader = ParquetDataLoader(parquet_path=data_path)
    router = OptimizedAdaptiveRouter(25000)
    
    # Compare Day 1 (2024-03-01) vs Day 2 (2024-03-04)
    dates = ["2024-03-01", "2024-03-04"]
    
    for date_str in dates:
        print(f"\n📅 ANALYZING {date_str}:")
        
        test_date = datetime.strptime(date_str, "%Y-%m-%d")
        options_data = data_loader.load_options_for_date(test_date)
        spy_price = options_data['strike'].median() if 'strike' in options_data.columns else 515.0
        test_time = test_date.replace(hour=12, minute=0)
        
        market_data = {
            'spy_price': spy_price,
            'timestamp': test_time,
            'spy_volume': 2000000
        }
        
        # Reset daily tracking
        router._check_daily_reset(test_time)
        
        # Get market intelligence
        intelligence = router.intelligence_engine.analyze_market_intelligence(options_data, spy_price)
        
        print(f"   SPY Price: ${spy_price:.2f}")
        print(f"   Options Records: {len(options_data)}")
        print(f"   Market Regime: {intelligence.primary_regime} ({intelligence.regime_confidence:.1f}%)")
        print(f"   Bull/Bear/Neutral: {intelligence.bull_score:.1f}/{intelligence.bear_score:.1f}/{intelligence.neutral_score:.1f}")
        
        # Check strategy selection
        strategy_rec = router.select_adaptive_strategy(options_data, market_data, test_time)
        print(f"   Strategy: {strategy_rec['strategy_type']}")
        print(f"   Reason: {strategy_rec.get('reason', 'N/A')}")
        
        # Check pre-flight
        can_trade, reason = router._pre_flight_checks(test_time)
        print(f"   Pre-flight: {can_trade} ({reason})")

def test_market_intelligence_sensitivity():
    """Test if market intelligence is too sensitive/restrictive"""
    
    print(f"\n🧠 TESTING MARKET INTELLIGENCE SENSITIVITY")
    print("="*60)
    
    data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
    data_loader = ParquetDataLoader(parquet_path=data_path)
    router = OptimizedAdaptiveRouter(25000)
    
    # Test multiple days to see pattern
    test_dates = ["2024-03-04", "2024-03-05", "2024-03-06", "2024-03-07"]
    
    print(f"Testing {len(test_dates)} consecutive non-trading days:")
    
    for date_str in test_dates:
        test_date = datetime.strptime(date_str, "%Y-%m-%d")
        options_data = data_loader.load_options_for_date(test_date)
        spy_price = options_data['strike'].median() if 'strike' in options_data.columns else 515.0
        test_time = test_date.replace(hour=12, minute=0)
        
        intelligence = router.intelligence_engine.analyze_market_intelligence(options_data, spy_price)
        
        print(f"   {date_str}: {intelligence.primary_regime} ({intelligence.regime_confidence:.1f}%) - Bull:{intelligence.bull_score:.1f} Bear:{intelligence.bear_score:.1f}")
        
        # Check if ANY regime would pass thresholds
        would_trade = False
        if intelligence.primary_regime == 'BULLISH' and intelligence.regime_confidence > 35:
            would_trade = True
        elif intelligence.primary_regime == 'BEARISH' and intelligence.regime_confidence > 35:
            would_trade = True
        elif intelligence.primary_regime == 'NEUTRAL' and intelligence.regime_confidence > 60:
            would_trade = True
        
        print(f"      Would trade: {would_trade}")

def main():
    """Run comprehensive debugging"""
    
    print("🚨 DEBUGGING NO TRADES ISSUE - COMPREHENSIVE ANALYSIS")
    print("="*70)
    
    # Test 1: Debug specific non-trading day
    debug_specific_day("2024-03-05")
    
    # Test 2: Compare trading vs non-trading days
    compare_trading_vs_non_trading_days()
    
    # Test 3: Test market intelligence sensitivity
    test_market_intelligence_sensitivity()
    
    print(f"\n🎯 SUMMARY & RECOMMENDATIONS:")
    print(f"1. Check if market intelligence confidence is too low")
    print(f"2. Consider lowering confidence thresholds further")
    print(f"3. Add fallback trading logic for unclear market conditions")
    print(f"4. Verify daily reset is working properly")

if __name__ == "__main__":
    main()
