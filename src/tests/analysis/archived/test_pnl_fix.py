#!/usr/bin/env python3
"""
Quick P&L Fix Validation Test
============================

Test to validate the P&L calculation fix.
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tests.analysis.unified_strategy_backtester import UnifiedStrategyBacktester

def main():
    """Run quick P&L validation test"""
    
    print("🧪 P&L CALCULATION FIX VALIDATION")
    print("="*40)
    print("Testing corrected P&L calculation logic")
    print()
    
    # Initialize backtester
    backtester = UnifiedStrategyBacktester(initial_balance=25000)
    
    # Run very short 2-day test
    print("🚀 Running 2-day P&L validation test...")
    results = backtester.run_unified_backtest(
        start_date="2024-01-02",
        end_date="2024-01-03"
    )
    
    # Extract key metrics
    initial_balance = 25000.0
    final_balance = results.get('final_balance', 0)
    reported_pnl = results.get('session_summary', {}).get('performance', {}).get('total_pnl', 0)
    actual_pnl = final_balance - initial_balance
    
    print("\n" + "="*40)
    print("🔍 P&L CALCULATION VALIDATION")
    print("="*40)
    
    print(f"\n💰 BALANCE TRACKING:")
    print(f"   Initial Balance: ${initial_balance:,.2f}")
    print(f"   Final Balance: ${final_balance:,.2f}")
    print(f"   Actual P&L: ${actual_pnl:+,.2f}")
    
    print(f"\n📊 REPORTED METRICS:")
    print(f"   Reported P&L: ${reported_pnl:+,.2f}")
    print(f"   Reported Return: {results.get('total_return_pct', 0):+.2f}%")
    
    print(f"\n🎯 VALIDATION RESULTS:")
    pnl_matches = abs(reported_pnl - actual_pnl) < 0.01  # Allow for rounding
    return_correct = abs(results.get('total_return_pct', 0) - (actual_pnl / initial_balance * 100)) < 0.01
    
    print(f"   P&L Calculation: {'✅ CORRECT' if pnl_matches else '❌ STILL WRONG'}")
    print(f"   Return Calculation: {'✅ CORRECT' if return_correct else '❌ STILL WRONG'}")
    
    if pnl_matches and return_correct:
        print(f"\n🚀 P&L CALCULATION FIX SUCCESSFUL!")
    else:
        print(f"\n⚠️ P&L calculation still needs work")
        print(f"   Expected P&L: ${actual_pnl:+,.2f}")
        print(f"   Reported P&L: ${reported_pnl:+,.2f}")
        print(f"   Difference: ${abs(reported_pnl - actual_pnl):,.2f}")
    
    return results

if __name__ == "__main__":
    main()
