#!/usr/bin/env python3
"""
Debug Trade Execution
=====================

Test the execute_optimized_trade method directly to see why trades aren't executing.
Following @.cursorrules testing patterns.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.strategies.adaptive_zero_dte.optimized_adaptive_router import OptimizedAdaptiveRouter
from src.data.parquet_data_loader import ParquetDataLoader

def test_trade_execution():
    """Test trade execution directly"""
    
    print("🔍 TESTING TRADE EXECUTION DIRECTLY")
    print("="*60)
    
    # Initialize components
    data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
    data_loader = ParquetDataLoader(parquet_path=data_path)
    router = OptimizedAdaptiveRouter(25000)
    
    # Load data for a day we know should trade
    test_date = datetime.strptime("2024-03-05", "%Y-%m-%d")
    options_data = data_loader.load_options_for_date(test_date)
    spy_price = options_data['strike'].median() if 'strike' in options_data.columns else 515.0
    test_time = test_date.replace(hour=12, minute=0)
    
    market_data = {
        'spy_price': spy_price,
        'timestamp': test_time,
        'spy_volume': 2000000
    }
    
    print(f"📊 Test Setup:")
    print(f"   Date: {test_date.strftime('%Y-%m-%d')}")
    print(f"   SPY Price: ${spy_price:.2f}")
    print(f"   Options Records: {len(options_data)}")
    
    # Reset daily tracking
    router._check_daily_reset(test_time)
    
    # Step 1: Get strategy recommendation
    strategy_rec = router.select_adaptive_strategy(options_data, market_data, test_time)
    
    print(f"\n🎯 Strategy Recommendation:")
    print(f"   Strategy: {strategy_rec['strategy_type']}")
    print(f"   Confidence: {strategy_rec.get('confidence', 0):.1f}%")
    print(f"   Reason: {strategy_rec.get('reason', 'N/A')}")
    
    if strategy_rec['strategy_type'] == 'NO_TRADE':
        print(f"❌ No trade recommended - cannot test execution")
        return
    
    # Step 2: Test trade execution
    print(f"\n💰 Testing Trade Execution:")
    
    try:
        trade_result = router.execute_optimized_trade(
            strategy_rec, options_data, market_data, test_time
        )
        
        print(f"   Execution Result:")
        for key, value in trade_result.items():
            print(f"      {key}: {value}")
        
        if trade_result.get('executed', False):
            print(f"   ✅ TRADE EXECUTED SUCCESSFULLY!")
        else:
            print(f"   ❌ TRADE EXECUTION FAILED")
            print(f"   Reason: {trade_result.get('reason', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION DURING EXECUTION: {e}")
        import traceback
        traceback.print_exc()

def test_multiple_times():
    """Test execution at multiple times during the day"""
    
    print(f"\n🕐 TESTING MULTIPLE TIMES DURING DAY")
    print("="*60)
    
    data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
    data_loader = ParquetDataLoader(parquet_path=data_path)
    router = OptimizedAdaptiveRouter(25000)
    
    test_date = datetime.strptime("2024-03-05", "%Y-%m-%d")
    options_data = data_loader.load_options_for_date(test_date)
    spy_price = options_data['strike'].median() if 'strike' in options_data.columns else 515.0
    
    test_times = [
        test_date.replace(hour=10, minute=0),   # 10:00 AM
        test_date.replace(hour=12, minute=0),   # 12:00 PM  
        test_date.replace(hour=14, minute=0),   # 2:00 PM
    ]
    
    for test_time in test_times:
        print(f"\n⏰ Testing {test_time.strftime('%H:%M')}:")
        
        market_data = {
            'spy_price': spy_price + (test_time.hour - 10) * 0.25,  # Simulate price movement
            'timestamp': test_time,
            'spy_volume': 2000000
        }
        
        # Get strategy recommendation
        strategy_rec = router.select_adaptive_strategy(options_data, market_data, test_time)
        
        print(f"   Strategy: {strategy_rec['strategy_type']}")
        
        if strategy_rec['strategy_type'] != 'NO_TRADE':
            try:
                trade_result = router.execute_optimized_trade(
                    strategy_rec, options_data, market_data, test_time
                )
                
                executed = trade_result.get('executed', False)
                pnl = trade_result.get('pnl', 0.0)
                
                print(f"   Executed: {executed}")
                print(f"   P&L: ${pnl:+.2f}")
                
                if not executed:
                    print(f"   Failure Reason: {trade_result.get('reason', 'Unknown')}")
                    
            except Exception as e:
                print(f"   Exception: {e}")
        else:
            print(f"   No trade recommended")

def main():
    """Run comprehensive trade execution debugging"""
    
    print("🚨 DEBUGGING TRADE EXECUTION ISSUE")
    print("="*70)
    
    # Test 1: Single trade execution
    test_trade_execution()
    
    # Test 2: Multiple times during day
    test_multiple_times()
    
    print(f"\n🎯 SUMMARY:")
    print(f"This should help identify why trades aren't executing in the backtester")

if __name__ == "__main__":
    main()
