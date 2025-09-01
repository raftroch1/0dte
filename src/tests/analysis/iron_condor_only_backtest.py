#!/usr/bin/env python3
"""
🎯 IRON CONDOR ONLY BACKTEST
============================
Test ONLY Iron Condors since they were our best performing strategy (33.3% win rate).
This will show us the pure performance of our selling strategy without the terrible
buying strategies dragging down results.

Key Focus:
1. ONLY Iron Condor trades (no BUY_CALL or BUY_PUT)
2. Same period as original backtest for comparison
3. See if 33.3% win rate can be profitable with proper position sizing

Following @.cursorrules: Using existing infrastructure, real data analysis.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use our existing unified backtester but modify strategy selection
from tests.analysis.unified_strategy_backtester import UnifiedStrategyBacktester

class IronCondorOnlyBacktester(UnifiedStrategyBacktester):
    """Modified backtester that ONLY trades Iron Condors"""
    
    def __init__(self, initial_balance: float = 25000):
        super().__init__(initial_balance)
        print(f"🎯 IRON CONDOR ONLY BACKTESTER")
        print(f"   Strategy: ONLY Iron Condors (our best performer)")
        print(f"   Original IC Win Rate: 33.3%")
        print(f"   Goal: See if selling-only strategy is profitable")

    def _get_strategy_recommendation(self, regime: str, spy_price: float) -> str:
        """ALWAYS recommend Iron Condor regardless of market regime"""
        return 'IRON_CONDOR'

    def _determine_volatility_level(self, options_data, spy_price: float) -> str:
        """Always return HIGH volatility to enable Iron Condor execution"""
        return 'HIGH'

def run_iron_condor_comparison():
    """Run Iron Condor only backtest and compare to original results"""
    
    print(f"🎯 IRON CONDOR ONLY STRATEGY TEST")
    print(f"=" * 60)
    print(f"📊 ORIGINAL RESULTS (All Strategies):")
    print(f"   Total Return: -40.14%")
    print(f"   Win Rate: 29.4%")
    print(f"   Iron Condor Win Rate: 33.3% (best)")
    print(f"   BUY_CALL Win Rate: 18.2% (terrible)")
    print(f"   BUY_PUT Win Rate: 31.5% (poor)")
    print(f"")
    print(f"🎯 HYPOTHESIS: Iron Condors alone might be profitable")
    print(f"=" * 60)
    
    # Run Iron Condor only backtest
    backtester = IronCondorOnlyBacktester(initial_balance=25000.0)
    
    try:
        results = backtester.run_unified_backtest("2024-01-02", "2024-06-28")
        session_summary = backtester.logger.generate_session_summary()
        
        print(f"\n🎯 IRON CONDOR ONLY RESULTS:")
        print(f"=" * 60)
        print(f"💰 FINANCIAL PERFORMANCE:")
        print(f"   Initial Balance: ${session_summary['performance']['initial_balance']:,.2f}")
        print(f"   Final Balance: ${session_summary['performance']['final_balance']:,.2f}")
        print(f"   Total P&L: ${session_summary['performance']['total_pnl']:+,.2f}")
        print(f"   Total Return: {session_summary['performance']['total_return_pct']:+.2f}%")
        print(f"   Win Rate: {session_summary['performance']['win_rate_pct']:.1f}%")
        print(f"   Total Trades: {session_summary['performance']['total_trades']}")
        
        print(f"\n📊 COMPARISON:")
        print(f"   Original (All Strategies): -40.14% return, 29.4% win rate")
        print(f"   Iron Condor Only: {session_summary['performance']['total_return_pct']:+.2f}% return, {session_summary['performance']['win_rate_pct']:.1f}% win rate")
        
        improvement = session_summary['performance']['total_return_pct'] - (-40.14)
        
        if session_summary['performance']['total_return_pct'] > -40:
            print(f"   🟢 IRON CONDOR ONLY IS BETTER!")
            print(f"   📈 Improvement: {improvement:+.2f} percentage points")
        elif session_summary['performance']['total_return_pct'] > -20:
            print(f"   🟡 IRON CONDOR ONLY IS MUCH BETTER!")
            print(f"   📈 Significant improvement: {improvement:+.2f} percentage points")
        elif session_summary['performance']['total_return_pct'] > 0:
            print(f"   🟢 IRON CONDOR ONLY IS PROFITABLE!")
            print(f"   🚀 MASSIVE improvement: {improvement:+.2f} percentage points")
        else:
            print(f"   🔴 Still losing, but improvement: {improvement:+.2f} percentage points")
        
        # Strategy breakdown
        if 'strategy_breakdown' in session_summary:
            print(f"\n🎯 STRATEGY BREAKDOWN:")
            for strategy, stats in session_summary['strategy_breakdown'].items():
                win_rate = (stats['wins'] / max(stats['count'], 1)) * 100
                print(f"   {strategy}: {stats['count']} trades, ${stats['total_pnl']:,.2f}, {win_rate:.1f}% win rate")
        
        print(f"\n💡 ANALYSIS:")
        if session_summary['performance']['total_return_pct'] > -10:
            print(f"   ✅ Iron Condors show promise as a selling strategy")
            print(f"   ✅ Much better than buying options")
            print(f"   🎯 Next step: Optimize Iron Condor parameters")
        elif session_summary['performance']['total_return_pct'] > -30:
            print(f"   🟡 Iron Condors are better but need optimization")
            print(f"   🎯 Consider: Better strike selection, different DTE")
        else:
            print(f"   🔴 Even our best strategy struggles")
            print(f"   🎯 Consider: Different time periods, market conditions")
        
        return session_summary
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        return None

if __name__ == "__main__":
    results = run_iron_condor_comparison()
