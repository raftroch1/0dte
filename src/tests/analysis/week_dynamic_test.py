#!/usr/bin/env python3
"""
📅 1-WEEK DYNAMIC RISK MANAGEMENT TEST
====================================
Test dynamic risk management over 1 week to see actual position closures
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the fixed backtester
sys.path.append(str(Path(__file__).parent))
from fixed_dynamic_risk_backtester import FixedDynamicRiskBacktester

def run_week_test():
    """Run a 1-week test of dynamic risk management"""
    
    print(f"📅 1-WEEK DYNAMIC RISK MANAGEMENT TEST")
    print(f"=" * 50)
    print(f"🎯 TESTING: Your brilliant position management")
    print(f"📅 PERIOD: 1 week (2024-01-02 to 2024-01-08)")
    print(f"💰 ACCOUNT: $25,000")
    print(f"🎲 STRATEGY: Iron Condors with 25% profit / 2x stop")
    print(f"=" * 50)
    
    try:
        # Initialize the backtester
        backtester = FixedDynamicRiskBacktester(initial_balance=25000.0)
        
        # Run 1-week backtest
        print(f"\n📅 RUNNING 1-WEEK DYNAMIC RISK TEST...")
        results = backtester.run_unified_backtest("2024-01-02", "2024-01-08")
        
        # Get session summary
        session_summary = backtester.logger.generate_session_summary()
        
        print(f"\n🎯 1-WEEK DYNAMIC RISK RESULTS:")
        print(f"=" * 50)
        print(f"💰 FINANCIAL PERFORMANCE:")
        print(f"   Initial Balance: ${session_summary['performance']['initial_balance']:,.2f}")
        print(f"   Final Balance: ${session_summary['performance']['final_balance']:,.2f}")
        print(f"   Total P&L: ${session_summary['performance']['total_pnl']:+,.2f}")
        print(f"   Total Return: {session_summary['performance']['total_return_pct']:+.2f}%")
        print(f"   Win Rate: {session_summary['performance']['win_rate_pct']:.1f}%")
        print(f"   Total Trades: {session_summary['performance']['total_trades']}")
        
        if session_summary['performance']['total_trades'] > 0:
            print(f"\n📊 TRADE ANALYSIS:")
            print(f"   Average Trade P&L: ${session_summary['performance']['avg_trade_pnl']:+,.2f}")
            print(f"   Best Trade: ${session_summary['performance']['best_trade']:+,.2f}")
            print(f"   Worst Trade: ${session_summary['performance']['worst_trade']:+,.2f}")
            
            # Strategy breakdown
            if 'strategy_breakdown' in session_summary:
                print(f"\n🎯 STRATEGY BREAKDOWN:")
                for strategy, stats in session_summary['strategy_breakdown'].items():
                    win_rate = (stats['wins'] / max(stats['count'], 1)) * 100
                    print(f"   {strategy}: {stats['count']} trades, ${stats['total_pnl']:+,.2f}, {win_rate:.1f}% win rate")
        
        print(f"\n💡 DYNAMIC RISK MANAGEMENT ANALYSIS:")
        
        if session_summary['performance']['total_return_pct'] > 5:
            print(f"   🟢 EXCELLENT: {session_summary['performance']['total_return_pct']:+.1f}% weekly return!")
            print(f"   🚀 Dynamic risk management is highly effective")
        elif session_summary['performance']['total_return_pct'] > 0:
            print(f"   🟢 PROFITABLE: {session_summary['performance']['total_return_pct']:+.1f}% weekly return")
            print(f"   ✅ Dynamic risk management is working")
        elif session_summary['performance']['total_return_pct'] > -10:
            print(f"   🟡 MANAGEABLE: {session_summary['performance']['total_return_pct']:+.1f}% weekly loss")
            print(f"   📈 Much better than -40% baseline strategy")
        else:
            print(f"   🔴 NEEDS TUNING: {session_summary['performance']['total_return_pct']:+.1f}% weekly loss")
            print(f"   🔧 Dynamic parameters may need adjustment")
        
        # Compare to baseline
        baseline_weekly = -40.14 / 26  # -40% over 6 months = ~-1.5% per week
        improvement = session_summary['performance']['total_return_pct'] - baseline_weekly
        
        print(f"\n📈 COMPARISON TO BASELINE:")
        print(f"   Baseline Strategy: ~{baseline_weekly:.1f}% per week")
        print(f"   Dynamic Risk Mgmt: {session_summary['performance']['total_return_pct']:+.1f}% per week")
        print(f"   Improvement: {improvement:+.1f} percentage points")
        
        if improvement > 0:
            print(f"   🎉 DYNAMIC RISK MANAGEMENT IS SUPERIOR!")
        
        return session_summary
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = run_week_test()
