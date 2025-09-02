#!/usr/bin/env python3
"""
🔍 DEBUG TRADE EXECUTION
========================
Quick debug script to see why trades aren't executing
"""

import sys
import os
from pathlib import Path
from datetime import datetime, time

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.strategies.adaptive_zero_dte.enhanced_adaptive_router import EnhancedAdaptiveRouter
from src.data.parquet_data_loader import ParquetDataLoader

def debug_single_day():
    """Debug a single trading day to see what's blocking trades"""
    
    # Initialize components
    data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
    data_loader = ParquetDataLoader(parquet_path=data_path)
    router = EnhancedAdaptiveRouter(account_balance=25000)
    
    # Test with a recent date
    test_date = datetime(2024, 3, 11)
    print(f"🔍 DEBUGGING TRADE EXECUTION FOR {test_date.strftime('%Y-%m-%d')}")
    
    # Load options data
    options_data = data_loader.load_options_for_date(test_date)
    print(f"✅ Loaded {len(options_data)} options")
    
    # Estimate SPY price
    call_strikes = options_data[options_data['option_type'] == 'call']['strike'].unique()
    put_strikes = options_data[options_data['option_type'] == 'put']['strike'].unique()
    all_strikes = sorted(set(call_strikes) | set(put_strikes))
    spy_price = all_strikes[len(all_strikes)//2] if all_strikes else 400.0
    print(f"📊 Estimated SPY: ${spy_price}")
    
    # Test different times throughout the day
    test_times = [
        test_date.replace(hour=10, minute=30),  # 10:30 AM
        test_date.replace(hour=12, minute=30),  # 12:30 PM  
        test_date.replace(hour=14, minute=0),   # 2:00 PM
    ]
    
    for test_time in test_times:
        print(f"\n⏰ TESTING TIME: {test_time.strftime('%H:%M')}")
        
        # Create market data
        market_data = {
            'spy_price': spy_price,
            'timestamp': test_time,
            'vix': 20.0,  # Normal VIX level
            'spy_volume': 2000000  # 2M volume
        }
        
        # Check market conditions first
        can_trade, condition_message = router.check_enhanced_market_conditions(market_data, test_time)
        print(f"   Market Conditions: {can_trade} - {condition_message}")
        
        if can_trade:
            # Get strategy recommendation
            strategy_rec = router.select_adaptive_strategy(options_data, market_data, test_time)
            print(f"   Strategy: {strategy_rec['strategy_type']}")
            print(f"   Reason: {strategy_rec['reason']}")
            print(f"   Confidence: {strategy_rec.get('confidence', 0):.1f}%")
            
            if strategy_rec['strategy_type'] != 'NO_TRADE':
                print(f"   ✅ TRADE WOULD EXECUTE!")
                break
        else:
            print(f"   ❌ BLOCKED: {condition_message}")
    
    # Check router state
    print(f"\n📊 ROUTER STATE:")
    print(f"   Daily P&L: ${router.daily_pnl}")
    print(f"   Trades Today: {len(router.trades_today)}")
    print(f"   Max Daily Loss: ${router.max_daily_loss}")
    print(f"   Daily Profit Target: ${router.daily_profit_target}")
    print(f"   Max Positions: {router.max_positions}")

if __name__ == "__main__":
    debug_single_day()
