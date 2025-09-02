#!/usr/bin/env python3
"""
🔍 DEBUG FLYAGONAL ENTRY CONDITIONS
==================================
Debug why the corrected Flyagonal strategy isn't finding entry opportunities.

This will check:
1. Expiration date availability (8-10 DTE)
2. Position construction success rates
3. Vega balance requirements
4. Risk/reward filters
5. Entry condition logic

Following @.cursorrules:
- Debug without affecting other systems
- Identify specific blocking conditions

Location: src/strategies/flyagonal_python/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Flyagonal Debug
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def debug_flyagonal_entry_conditions():
    """Debug why Flyagonal isn't finding entries"""
    
    print("🔍 DEBUGGING FLYAGONAL ENTRY CONDITIONS")
    print("="*50)
    
    try:
        from corrected_flyagonal_strategy import CorrectedFlyagonalStrategy
        from src.data.parquet_data_loader import ParquetDataLoader
        
        # Initialize components
        data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
        data_loader = ParquetDataLoader(parquet_path=data_path)
        strategy = CorrectedFlyagonalStrategy()
        
        # Test a specific day
        test_date = datetime(2023, 9, 1)
        print(f"\n📅 Testing Date: {test_date.strftime('%Y-%m-%d')}")
        
        # Load options data
        options_data = data_loader.load_options_for_date(test_date)
        spy_price = 450.0  # Approximate
        
        print(f"📊 Options Available: {len(options_data)}")
        print(f"📊 SPY Price: ${spy_price:.2f}")
        
        # Debug step by step
        print(f"\n🔍 DEBUGGING ENTRY CONDITIONS:")
        
        # 1. Check position limits
        print(f"\n1️⃣ Position Limits:")
        print(f"   Open Positions: {len(strategy.open_positions)}")
        print(f"   Max Positions: {strategy.max_positions}")
        print(f"   ✅ Position limit OK: {len(strategy.open_positions) < strategy.max_positions}")
        
        # 2. Check expiration dates
        print(f"\n2️⃣ Expiration Date Check:")
        short_expiry, long_expiry = strategy.find_suitable_expiration_dates(options_data, test_date)
        print(f"   Short Expiry (8-10 DTE): {short_expiry}")
        print(f"   Long Expiry (~16-20 DTE): {long_expiry}")
        
        if short_expiry and long_expiry:
            short_dte = (datetime.strptime(short_expiry, '%Y-%m-%d') - test_date).days
            long_dte = (datetime.strptime(long_expiry, '%Y-%m-%d') - test_date).days
            print(f"   Short DTE: {short_dte} days")
            print(f"   Long DTE: {long_dte} days")
            print(f"   ✅ Expiration dates OK")
        else:
            print(f"   ❌ No suitable expiration dates found")
            
            # Debug available expirations
            available_expiries = sorted(options_data['expiration'].unique())
            print(f"   Available expirations:")
            for expiry in available_expiries[:10]:  # First 10
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
                dte = (expiry_date - test_date).days
                print(f"      {expiry}: {dte} DTE")
            return False
        
        # 3. Check options availability
        print(f"\n3️⃣ Options Availability:")
        calls = options_data[options_data['option_type'] == 'call']
        puts = options_data[options_data['option_type'] == 'put']
        print(f"   Calls: {len(calls)}")
        print(f"   Puts: {len(puts)}")
        print(f"   ✅ Options availability OK: {len(calls) >= 20 and len(puts) >= 20}")
        
        # 4. Test position construction
        print(f"\n4️⃣ Position Construction:")
        
        # Test butterfly construction
        butterfly = strategy.construct_broken_wing_butterfly(calls, spy_price, short_expiry)
        if butterfly:
            print(f"   ✅ Broken Wing Butterfly: Constructed")
            print(f"      Strikes: {butterfly['lower_strike']:.0f}/{butterfly['middle_strike']:.0f}/{butterfly['upper_strike']:.0f}")
            print(f"      Net Cost: ${butterfly['net_cost']:.2f}")
            print(f"      Max Profit: ${butterfly['max_profit']:.2f}")
            print(f"      Estimated Vega: {butterfly['estimated_vega']:.2f}")
        else:
            print(f"   ❌ Broken Wing Butterfly: Failed to construct")
            return False
        
        # Test diagonal construction
        diagonal = strategy.construct_put_diagonal_calendar(puts, spy_price, short_expiry, long_expiry)
        if diagonal:
            print(f"   ✅ Put Diagonal Calendar: Constructed")
            print(f"      Strikes: {diagonal['short_strike']:.0f}/{diagonal['long_strike']:.0f}")
            print(f"      Net Credit: ${diagonal['net_credit']:.2f}")
            print(f"      Max Profit: ${diagonal['max_profit']:.2f}")
            print(f"      Estimated Vega: {diagonal['estimated_vega']:.2f}")
        else:
            print(f"   ❌ Put Diagonal Calendar: Failed to construct")
            return False
        
        # 5. Check vega balance
        print(f"\n5️⃣ Vega Balance Check:")
        net_vega = butterfly['estimated_vega'] + diagonal['estimated_vega']
        print(f"   Butterfly Vega: {butterfly['estimated_vega']:.2f}")
        print(f"   Diagonal Vega: {diagonal['estimated_vega']:.2f}")
        print(f"   Net Vega: {net_vega:.2f}")
        print(f"   Max Allowed: ±{strategy.max_net_vega:.2f}")
        vega_ok = abs(net_vega) <= strategy.max_net_vega
        print(f"   ✅ Vega balance OK: {vega_ok}")
        
        if not vega_ok:
            print(f"   ❌ Vega balance failed - net vega too high")
            return False
        
        # 6. Check risk/reward
        print(f"\n6️⃣ Risk/Reward Check:")
        total_max_loss = butterfly['max_loss'] + diagonal['max_loss']
        total_max_profit = butterfly['max_profit'] + diagonal['max_profit']
        max_risk_allowed = strategy.initial_balance * (strategy.risk_per_trade_pct / 100)
        
        print(f"   Total Max Loss: ${total_max_loss:.2f}")
        print(f"   Max Risk Allowed: ${max_risk_allowed:.2f}")
        print(f"   Total Max Profit: ${total_max_profit:.2f}")
        
        risk_ok = total_max_loss <= max_risk_allowed
        reward_ratio = total_max_profit / max(total_max_loss, 1)
        reward_ok = reward_ratio >= 0.3
        
        print(f"   Risk OK: {risk_ok}")
        print(f"   Reward/Risk Ratio: {reward_ratio:.2f} (min 0.3)")
        print(f"   Reward OK: {reward_ok}")
        
        if not risk_ok:
            print(f"   ❌ Risk too high")
            return False
        
        if not reward_ok:
            print(f"   ❌ Reward/risk ratio too low")
            return False
        
        # 7. Final entry decision
        print(f"\n7️⃣ Final Entry Decision:")
        should_enter = strategy.should_enter_flyagonal(options_data, spy_price, test_date)
        print(f"   Should Enter: {should_enter}")
        
        if should_enter:
            print(f"   ✅ ALL CONDITIONS MET - SHOULD ENTER")
        else:
            print(f"   ❌ ENTRY BLOCKED - Check logic")
        
        return should_enter
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

def suggest_fixes():
    """Suggest fixes for entry condition issues"""
    
    print(f"\n🔧 SUGGESTED FIXES:")
    print(f"1. Relax DTE requirements (try 5-15 DTE instead of 8-10)")
    print(f"2. Increase max vega tolerance (try ±100 instead of ±50)")
    print(f"3. Lower reward/risk ratio requirement (try 0.2 instead of 0.3)")
    print(f"4. Increase risk per trade (try 3% instead of 2%)")
    print(f"5. Simplify position construction logic")
    print(f"6. Add debug logging to position construction methods")

if __name__ == "__main__":
    print("🔍 Starting Flyagonal Entry Condition Debug...")
    
    success = debug_flyagonal_entry_conditions()
    
    if success:
        print(f"\n✅ ENTRY CONDITIONS WORKING")
        print(f"   Strategy should be finding entries")
        print(f"   May need to run longer backtest period")
    else:
        print(f"\n❌ ENTRY CONDITIONS BLOCKED")
        print(f"   Strategy needs adjustment")
        suggest_fixes()
    
    print(f"\n🎯 CONCLUSION:")
    if success:
        print(f"   Entry logic works - extend backtest period")
    else:
        print(f"   Entry logic too restrictive - needs optimization")
