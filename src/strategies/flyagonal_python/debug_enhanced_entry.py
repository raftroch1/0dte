#!/usr/bin/env python3
"""
🔍 DEBUG ENHANCED FLYAGONAL ENTRY CONDITIONS
===========================================
Debug why the enhanced Flyagonal strategy isn't executing trades.

This will check step-by-step:
1. Basic position limits
2. Expiration date availability
3. Position construction success
4. Vega balance requirements
5. Risk management filters
6. Enhanced entry logic

Following @.cursorrules:
- Debug without affecting other systems
- Identify specific blocking conditions

Location: src/strategies/flyagonal_python/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Enhanced Flyagonal Debug
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

def debug_enhanced_flyagonal_entry():
    """Debug enhanced Flyagonal entry conditions step by step"""
    
    print("🔍 DEBUGGING ENHANCED FLYAGONAL ENTRY CONDITIONS")
    print("="*60)
    
    try:
        from enhanced_flyagonal_strategy import EnhancedFlyagonalStrategy
        from src.data.parquet_data_loader import ParquetDataLoader
        
        # Initialize components
        data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
        data_loader = ParquetDataLoader(parquet_path=data_path)
        strategy = EnhancedFlyagonalStrategy()
        
        # Test multiple dates
        test_dates = [
            datetime(2023, 9, 5),
            datetime(2023, 9, 7),
            datetime(2023, 9, 12)
        ]
        
        for test_date in test_dates:
            print(f"\n📅 TESTING DATE: {test_date.strftime('%Y-%m-%d')}")
            print("-" * 50)
            
            # Load options data
            options_data = data_loader.load_options_for_date(test_date)
            spy_price = 450.0
            
            print(f"📊 Options Available: {len(options_data)}")
            print(f"📊 SPY Price: ${spy_price:.2f}")
            
            # Step-by-step debugging
            print(f"\n🔍 STEP-BY-STEP ANALYSIS:")
            
            # 1. Position limits
            print(f"\n1️⃣ Position Limits:")
            print(f"   Open Positions: {len(strategy.open_positions)}")
            print(f"   Max Positions: {strategy.max_positions}")
            position_limit_ok = len(strategy.open_positions) < strategy.max_positions
            print(f"   ✅ Position Limit OK: {position_limit_ok}")
            
            if not position_limit_ok:
                print(f"   ❌ BLOCKED: Too many open positions")
                continue
            
            # 2. Expiration dates
            print(f"\n2️⃣ Expiration Date Check:")
            short_expiry, long_expiry = strategy.find_flexible_expiration_dates(options_data, test_date)
            print(f"   Short Expiry: {short_expiry}")
            print(f"   Long Expiry: {long_expiry}")
            
            if short_expiry and long_expiry:
                short_dte = (datetime.strptime(short_expiry, '%Y-%m-%d') - test_date).days
                long_dte = (datetime.strptime(long_expiry, '%Y-%m-%d') - test_date).days
                print(f"   Short DTE: {short_dte} days")
                print(f"   Long DTE: {long_dte} days")
                print(f"   ✅ Expiration Dates OK")
            else:
                print(f"   ❌ BLOCKED: No suitable expiration dates")
                
                # Show available expirations
                available_expiries = sorted(options_data['expiration'].unique())
                print(f"   Available expirations:")
                for expiry in available_expiries[:8]:
                    expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
                    dte = (expiry_date - test_date).days
                    print(f"      {expiry}: {dte} DTE")
                continue
            
            # 3. Options availability
            print(f"\n3️⃣ Options Availability:")
            calls = options_data[options_data['option_type'] == 'call']
            puts = options_data[options_data['option_type'] == 'put']
            print(f"   Calls: {len(calls)}")
            print(f"   Puts: {len(puts)}")
            options_ok = len(calls) >= 10 and len(puts) >= 10
            print(f"   ✅ Options Availability OK: {options_ok}")
            
            if not options_ok:
                print(f"   ❌ BLOCKED: Insufficient options")
                continue
            
            # 4. Position construction
            print(f"\n4️⃣ Position Construction:")
            
            # Test butterfly
            butterfly = strategy.construct_enhanced_butterfly(calls, spy_price, short_expiry)
            if butterfly:
                print(f"   ✅ Enhanced Butterfly: Constructed")
                print(f"      Strikes: {butterfly['lower_strike']:.0f}/{butterfly['middle_strike']:.0f}/{butterfly['upper_strike']:.0f}")
                print(f"      Net Cost: ${butterfly['net_cost']:.2f}")
                print(f"      Max Profit: ${butterfly['max_profit']:.2f}")
                print(f"      Max Loss: ${butterfly['max_loss']:.2f}")
                print(f"      Vega: {butterfly['estimated_vega']:.2f}")
            else:
                print(f"   ❌ BLOCKED: Enhanced butterfly construction failed")
                
                # Debug butterfly construction
                print(f"   Debug butterfly construction:")
                butterfly_calls = calls[
                    (calls['expiration'] == short_expiry) &
                    (calls['strike'] >= spy_price - 10) &
                    (calls['strike'] <= spy_price + 40)
                ].sort_values('strike')
                print(f"      Filtered calls: {len(butterfly_calls)}")
                if len(butterfly_calls) > 0:
                    print(f"      Strike range: {butterfly_calls['strike'].min():.0f} - {butterfly_calls['strike'].max():.0f}")
                continue
            
            # Test diagonal
            diagonal = strategy.construct_enhanced_diagonal(puts, spy_price, short_expiry, long_expiry)
            if diagonal:
                print(f"   ✅ Enhanced Diagonal: Constructed")
                print(f"      Short Strike: {diagonal['short_strike']:.0f} ({short_expiry})")
                print(f"      Long Strike: {diagonal['long_strike']:.0f} ({long_expiry})")
                print(f"      Net Credit: ${diagonal['net_credit']:.2f}")
                print(f"      Max Profit: ${diagonal['max_profit']:.2f}")
                print(f"      Max Loss: ${diagonal['max_loss']:.2f}")
                print(f"      Vega: {diagonal['estimated_vega']:.2f}")
            else:
                print(f"   ❌ BLOCKED: Enhanced diagonal construction failed")
                continue
            
            # 5. Vega balance
            print(f"\n5️⃣ Vega Balance Check:")
            net_vega = butterfly['estimated_vega'] + diagonal['estimated_vega']
            print(f"   Butterfly Vega: {butterfly['estimated_vega']:.2f}")
            print(f"   Diagonal Vega: {diagonal['estimated_vega']:.2f}")
            print(f"   Net Vega: {net_vega:.2f}")
            print(f"   Max Allowed: ±{strategy.max_net_vega:.2f}")
            vega_ok = abs(net_vega) <= strategy.max_net_vega
            print(f"   ✅ Vega Balance OK: {vega_ok}")
            
            if not vega_ok:
                print(f"   ❌ BLOCKED: Net vega too high")
                continue
            
            # 6. Risk management
            print(f"\n6️⃣ Risk Management Check:")
            total_max_loss = butterfly['max_loss'] + diagonal['max_loss']
            max_risk_allowed = strategy.initial_balance * (strategy.risk_per_trade_pct / 100)
            
            print(f"   Total Max Loss: ${total_max_loss:.2f}")
            print(f"   Max Risk Allowed: ${max_risk_allowed:.2f}")
            print(f"   Risk Per Trade: {strategy.risk_per_trade_pct:.1f}%")
            
            risk_ok = total_max_loss <= max_risk_allowed
            print(f"   ✅ Risk Management OK: {risk_ok}")
            
            if not risk_ok:
                print(f"   ❌ BLOCKED: Risk too high")
                print(f"      Suggestion: Increase risk_per_trade_pct from {strategy.risk_per_trade_pct}% to {(total_max_loss/strategy.initial_balance)*100:.1f}%")
                continue
            
            # 7. Final entry test
            print(f"\n7️⃣ Final Entry Test:")
            position = strategy.execute_enhanced_flyagonal_entry(options_data, spy_price, test_date)
            
            if position:
                print(f"   ✅ SUCCESS: Position created!")
                print(f"      Position ID: {position.position_id}")
                print(f"      Entry Cost: ${position.entry_cost:.2f}")
                print(f"      Net Credit: ${position.net_credit:.2f}")
                print(f"      Profit Target: ${position.profit_target:.2f}")
                print(f"      Stop Loss: ${position.stop_loss:.2f}")
                
                # Clean up for next test
                strategy.open_positions.remove(position)
                strategy.total_trades -= 1
                
                return True
            else:
                print(f"   ❌ BLOCKED: execute_enhanced_flyagonal_entry failed")
                print(f"      This shouldn't happen if all checks passed!")
        
        return False
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

def suggest_enhanced_fixes():
    """Suggest fixes for enhanced entry issues"""
    
    print(f"\n🔧 SUGGESTED ENHANCED FIXES:")
    print(f"1. Increase risk_per_trade_pct from 3% to 5-10%")
    print(f"2. Relax butterfly construction requirements")
    print(f"3. Relax diagonal construction requirements")
    print(f"4. Increase max_net_vega tolerance")
    print(f"5. Simplify position construction logic further")
    print(f"6. Add more debug logging to construction methods")
    print(f"7. Test with different SPY price levels")

if __name__ == "__main__":
    print("🔍 Starting Enhanced Flyagonal Entry Debug...")
    
    success = debug_enhanced_flyagonal_entry()
    
    if success:
        print(f"\n✅ ENHANCED ENTRY CONDITIONS WORKING")
        print(f"   Strategy should be finding entries")
        print(f"   Issue may be with specific market conditions")
    else:
        print(f"\n❌ ENHANCED ENTRY CONDITIONS BLOCKED")
        print(f"   Strategy needs further optimization")
        suggest_enhanced_fixes()
    
    print(f"\n🎯 CONCLUSION:")
    if success:
        print(f"   Enhanced entry logic works - may need different test period")
    else:
        print(f"   Enhanced entry logic too restrictive - needs relaxation")
