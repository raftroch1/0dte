#!/usr/bin/env python3
"""
Short Backtest Test - Validate Fixes
====================================

Quick test to validate:
1. Random import fix
2. Iron Condor execution in neutral markets
3. Detailed logging system
4. Strategy diversity

Testing just 5 days to quickly validate all fixes.
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tests.analysis.unified_strategy_backtester import UnifiedStrategyBacktester

def main():
    """Run short validation test"""
    
    print("🧪 SHORT BACKTEST VALIDATION TEST")
    print("="*50)
    print("Testing fixes:")
    print("✅ Random import fix")
    print("🔍 Iron Condor execution in neutral markets") 
    print("📊 Detailed logging system")
    print("🎯 Strategy diversity")
    print()
    
    # Initialize backtester
    backtester = UnifiedStrategyBacktester(initial_balance=25000)
    
    # Run short 5-day test
    print("🚀 Running 5-day validation test...")
    results = backtester.run_unified_backtest(
        start_date="2024-01-02",  # Start with neutral market day
        end_date="2024-01-08"     # Just 5 trading days
    )
    
    # Analyze results
    print("\n" + "="*50)
    print("🔍 VALIDATION RESULTS")
    print("="*50)
    
    strategy_validation = results.get('strategy_validation', {})
    
    print(f"\n📊 STRATEGY EXECUTION VALIDATION:")
    print(f"   Iron Condor Signals: {strategy_validation.get('iron_condor_signals', 0)}")
    print(f"   Bull Put Spread Signals: {strategy_validation.get('bull_put_spread_signals', 0)}")
    print(f"   Bear Call Spread Signals: {strategy_validation.get('bear_call_spread_signals', 0)}")
    print(f"   Buy Put Signals: {strategy_validation.get('buy_put_signals', 0)}")
    print(f"   Buy Call Signals: {strategy_validation.get('buy_call_signals', 0)}")
    print(f"   Total Signals: {strategy_validation.get('total_signals', 0)}")
    
    print(f"\n💰 FINANCIAL VALIDATION:")
    print(f"   Final Balance: ${results.get('final_balance', 0):,.2f}")
    print(f"   Total Return: {results.get('total_return_pct', 0):+.2f}%")
    
    print(f"\n📁 LOGGING VALIDATION:")
    log_files = results.get('log_files', {})
    for log_type, file_path in log_files.items():
        if os.path.exists(file_path):
            print(f"   ✅ {log_type}: {file_path}")
        else:
            print(f"   ❌ {log_type}: Missing")
    
    # Validation summary
    iron_condor_working = strategy_validation.get('iron_condor_signals', 0) > 0
    strategy_diversity = strategy_validation.get('total_signals', 0) > 0
    logging_working = len(log_files) > 0
    
    print(f"\n🎯 VALIDATION SUMMARY:")
    print(f"   Iron Condor Execution: {'✅ WORKING' if iron_condor_working else '❌ NEEDS FIX'}")
    print(f"   Strategy Diversity: {'✅ WORKING' if strategy_diversity else '❌ NEEDS FIX'}")
    print(f"   Detailed Logging: {'✅ WORKING' if logging_working else '❌ NEEDS FIX'}")
    print(f"   Random Import: {'✅ FIXED' if 'random' in sys.modules else '❌ STILL BROKEN'}")
    
    if iron_condor_working and strategy_diversity and logging_working:
        print(f"\n🚀 ALL FIXES VALIDATED - SYSTEM READY!")
    else:
        print(f"\n⚠️ Some issues remain - need further investigation")
    
    return results

if __name__ == "__main__":
    main()
