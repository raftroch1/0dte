#!/usr/bin/env python3
"""
Test Improved Router
====================

Test the improved OptimizedAdaptiveRouter with:
1. Fixed daily profit target logic (150% threshold)
2. More realistic win/loss simulation
3. Better trade frequency

Following @.cursorrules testing patterns.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.tests.analysis.run_optimized_router_1month_backtest import OptimizedRouterBacktester

def main():
    print("🧪 TESTING IMPROVED ROUTER - 1 WEEK VALIDATION")
    print("="*60)
    
    backtester = OptimizedRouterBacktester()
    
    # Run 1 week backtest to validate improvements
    results = backtester.run_1_month_backtest(
        start_date="2024-03-01",
        end_date="2024-03-07",  # 1 week
        account_balance=25000.0
    )
    
    if 'error' not in results:
        print(f"\n🎯 IMPROVED ROUTER RESULTS:")
        print(f"   Total Trades: {results['total_trades']}")
        print(f"   Win Rate: {results['overall_win_rate']:.1f}%")
        print(f"   Total P&L: ${results['total_pnl']:+.2f}")
        print(f"   Avg Daily P&L: ${results['avg_daily_pnl']:+.2f}")
        print(f"   Profitable Days: {results['profitable_days']}/{results['trading_days']}")
        
        # Assessment
        if results['total_trades'] >= 10:
            print(f"   ✅ GOOD: Trade frequency improved")
        else:
            print(f"   ⚠️  STILL LOW: Need more trades per day")
            
        if 60 <= results['overall_win_rate'] <= 80:
            print(f"   ✅ GOOD: Realistic win rate")
        else:
            print(f"   ⚠️  WIN RATE: {results['overall_win_rate']:.1f}% may be unrealistic")
            
        if results['avg_daily_pnl'] > 0:
            print(f"   ✅ GOOD: Positive daily P&L")
        else:
            print(f"   ❌ BAD: Negative daily P&L")
            
        # Ready for full month test?
        if (results['total_trades'] >= 10 and 
            60 <= results['overall_win_rate'] <= 80 and 
            results['avg_daily_pnl'] > 0):
            print(f"\n   🚀 READY FOR FULL MONTH BACKTEST!")
        else:
            print(f"\n   🔧 NEEDS MORE OPTIMIZATION")
            
    else:
        print(f"❌ Test failed: {results['error']}")

if __name__ == "__main__":
    main()
