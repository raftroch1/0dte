doing so can you run sorry run it agin#!/usr/bin/env python3
"""
Test Bullish Detection Fix - Validate Call Signal Generation
===========================================================

Test to validate that the fixed market regime detection now properly
generates bullish signals and Buy Call trades.
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tests.analysis.unified_strategy_backtester import UnifiedStrategyBacktester

def main():
    """Test the bullish detection fix"""
    
    print("🧪 BULLISH DETECTION FIX VALIDATION")
    print("="*50)
    print("Testing fixed P/C ratio thresholds:")
    print("   OLD: P/C < 0.8 = BULLISH (too restrictive)")
    print("   NEW: P/C < 1.0 = BULLISH (more realistic)")
    print()
    print("Expected: Should now see Buy Call signals!")
    print()
    
    # Initialize backtester
    backtester = UnifiedStrategyBacktester(initial_balance=25000)
    
    # Run short test to validate fix
    print("🚀 Running 1-week validation test...")
    results = backtester.run_unified_backtest(
        start_date="2024-07-01",
        end_date="2024-07-05"
    )
    
    print("\n" + "="*60)
    print("🔍 BULLISH DETECTION VALIDATION RESULTS")
    print("="*60)
    
    # Check strategy execution
    strategy_validation = results.get('strategy_validation', {})
    
    print(f"\n📊 STRATEGY SIGNAL BREAKDOWN:")
    print(f"   Iron Condor Signals: {strategy_validation.get('iron_condor_signals', 0)}")
    print(f"   Bull Put Spread Signals: {strategy_validation.get('bull_put_spread_signals', 0)}")
    print(f"   Bear Call Spread Signals: {strategy_validation.get('bear_call_spread_signals', 0)}")
    print(f"   Bull Call Spread Signals: {strategy_validation.get('bull_call_spread_signals', 0)}")
    print(f"   Bear Put Spread Signals: {strategy_validation.get('bear_put_spread_signals', 0)}")
    print(f"   🎯 Buy Call Signals: {strategy_validation.get('buy_call_signals', 0)}")
    print(f"   Buy Put Signals: {strategy_validation.get('buy_put_signals', 0)}")
    print(f"   Total Signals: {strategy_validation.get('total_signals', 0)}")
    
    # Validation results
    buy_call_signals = strategy_validation.get('buy_call_signals', 0)
    total_strategies = len([k for k, v in strategy_validation.items() if 'signals' in k and v > 0])
    
    print(f"\n🎯 VALIDATION RESULTS:")
    print(f"   Buy Call Detection: {'✅ WORKING' if buy_call_signals > 0 else '❌ STILL NOT WORKING'}")
    print(f"   Strategy Diversity: {'✅ GOOD' if total_strategies >= 3 else '🟡 LIMITED'} ({total_strategies} strategies)")
    
    # Performance summary
    final_balance = results.get('final_balance', 0)
    total_return = results.get('total_return_pct', 0)
    
    print(f"\n💰 PERFORMANCE SUMMARY:")
    print(f"   Final Balance: ${final_balance:,.2f}")
    print(f"   Total Return: {total_return:+.2f}%")
    
    # Recommendations
    print(f"\n🚀 NEXT STEPS:")
    if buy_call_signals > 0:
        print("   ✅ Bullish detection fix SUCCESSFUL!")
        print("   📊 Ready to run full 6-month test with all strategies")
        print("   🔧 Consider Iron Condor performance optimization")
    else:
        print("   ⚠️ Bullish detection still needs work")
        print("   🔍 May need to adjust P/C ratio thresholds further")
        print("   📊 Check market data for actual P/C ratio ranges")
    
    print(f"\n📁 DETAILED LOGS:")
    print(f"   Trade Log: {backtester.logger.trade_log_path}")
    print(f"   Market Log: {backtester.logger.market_log_path}")
    
    return results

if __name__ == "__main__":
    main()
