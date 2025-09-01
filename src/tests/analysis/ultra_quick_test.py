#!/usr/bin/env python3
"""
⚡ ULTRA QUICK DYNAMIC RISK TEST
===============================
1-day test to validate dynamic risk management is working
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

def run_ultra_quick_test():
    """Run a 1-day test of dynamic risk management"""
    
    print(f"⚡ ULTRA QUICK DYNAMIC RISK TEST")
    print(f"=" * 40)
    print(f"🎯 TESTING: Dynamic position management")
    print(f"📅 PERIOD: 1 day (2024-01-02)")
    print(f"💰 ACCOUNT: $25,000")
    print(f"=" * 40)
    
    try:
        # Initialize the backtester
        backtester = FixedDynamicRiskBacktester(initial_balance=25000.0)
        
        # Run 1-day backtest
        print(f"\n⚡ RUNNING 1-DAY TEST...")
        results = backtester.run_unified_backtest("2024-01-02", "2024-01-02")
        
        # Get session summary
        session_summary = backtester.logger.generate_session_summary()
        
        print(f"\n🎯 RESULTS:")
        print(f"=" * 40)
        print(f"💰 Initial: ${session_summary['performance']['initial_balance']:,.2f}")
        print(f"💰 Final: ${session_summary['performance']['final_balance']:,.2f}")
        print(f"💰 P&L: ${session_summary['performance']['total_pnl']:+,.2f}")
        print(f"📊 Return: {session_summary['performance']['total_return_pct']:+.2f}%")
        print(f"🎯 Trades: {session_summary['performance']['total_trades']}")
        print(f"🏆 Win Rate: {session_summary['performance']['win_rate_pct']:.1f}%")
        
        if session_summary['performance']['total_trades'] > 0:
            print(f"\n✅ SUCCESS: Dynamic risk management is working!")
            print(f"   Trades executed: {session_summary['performance']['total_trades']}")
            print(f"   Average P&L: ${session_summary['performance']['avg_trade_pnl']:+,.2f}")
        else:
            print(f"\n⚠️  No trades executed - need to investigate")
        
        return session_summary
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = run_ultra_quick_test()
