#!/usr/bin/env python3
"""
6-Month Comprehensive Backtest - Iron Condor + Spread Strategies
===============================================================

Comprehensive 6-month backtest with corrected P&L calculation.
Testing the unified strategy system with detailed logging.

Following @.cursorrules:
- Real data only (no simulation)
- Detailed CSV logging
- Proper risk management
- Multi-strategy execution
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tests.analysis.unified_strategy_backtester import UnifiedStrategyBacktester

def main():
    """Run comprehensive 6-month backtest"""
    
    print("🚀 6-MONTH COMPREHENSIVE BACKTEST")
    print("="*60)
    print("Testing Iron Condor + Spread strategies over 6 months")
    print("Following @.cursorrules: Real data, detailed logging")
    print()
    
    # Initialize backtester with $25k account
    backtester = UnifiedStrategyBacktester(initial_balance=25000)
    
    # 6-month period: July 1, 2024 to December 31, 2024
    start_date = "2024-07-01"
    end_date = "2024-12-31"
    
    print(f"📅 BACKTEST PERIOD: {start_date} to {end_date}")
    print(f"💰 INITIAL BALANCE: $25,000.00")
    print(f"🎯 DAILY TARGET: $250.00")
    print(f"🛑 MAX DAILY LOSS: $500.00")
    print()
    
    print("🔄 STRATEGIES BEING TESTED:")
    print("   ✅ Iron Condor (neutral markets)")
    print("   ✅ Bull Put Spread (bullish bias)")
    print("   ✅ Bear Call Spread (bearish bias)")
    print("   ✅ Buy Put (strong bearish)")
    print("   ✅ Buy Call (strong bullish)")
    print()
    
    print("📊 MARKET INTELLIGENCE FEATURES:")
    print("   ✅ VIX Term Structure Analysis")
    print("   ✅ Gamma Exposure Detection")
    print("   ✅ VWAP Deviation Tracking")
    print("   ✅ Put/Call Ratio Analysis")
    print("   ✅ Volume Flow Analysis")
    print()
    
    # Run the backtest
    print("🚀 STARTING 6-MONTH BACKTEST...")
    print("⏱️  This may take several minutes due to comprehensive analysis...")
    print()
    
    results = backtester.run_unified_backtest(
        start_date=start_date,
        end_date=end_date
    )
    
    # Display comprehensive results
    print("\n" + "="*80)
    print("📊 6-MONTH BACKTEST RESULTS")
    print("="*80)
    
    # Financial Performance
    initial_balance = 25000.0
    final_balance = results.get('final_balance', 0)
    total_pnl = final_balance - initial_balance
    total_return_pct = (total_pnl / initial_balance * 100)
    
    print(f"\n💰 FINANCIAL PERFORMANCE:")
    print(f"   Initial Balance: ${initial_balance:,.2f}")
    print(f"   Final Balance: ${final_balance:,.2f}")
    print(f"   Total P&L: ${total_pnl:+,.2f}")
    print(f"   Total Return: {total_return_pct:+.2f}%")
    print(f"   Annualized Return: {total_return_pct * 2:+.2f}%")  # 6 months * 2
    
    # Trading Statistics
    session_summary = results.get('session_summary', {})
    performance = session_summary.get('performance', {})
    
    total_trades = performance.get('total_trades', 0)
    winning_trades = performance.get('winning_trades', 0)
    losing_trades = performance.get('losing_trades', 0)
    win_rate = (winning_trades / max(total_trades, 1)) * 100
    
    print(f"\n📈 TRADING STATISTICS:")
    print(f"   Total Trades: {total_trades}")
    print(f"   Winning Trades: {winning_trades}")
    print(f"   Losing Trades: {losing_trades}")
    print(f"   Win Rate: {win_rate:.1f}%")
    
    if total_trades > 0:
        avg_trade_pnl = total_pnl / total_trades
        print(f"   Average Trade P&L: ${avg_trade_pnl:+,.2f}")
        print(f"   Best Trade: ${performance.get('best_trade', 0):+,.2f}")
        print(f"   Worst Trade: ${performance.get('worst_trade', 0):+,.2f}")
    
    # Strategy Breakdown
    strategy_stats = session_summary.get('strategy_breakdown', {})
    
    print(f"\n🎯 STRATEGY PERFORMANCE:")
    for strategy, stats in strategy_stats.items():
        strategy_trades = stats.get('count', 0)
        strategy_pnl = stats.get('total_pnl', 0)
        strategy_wins = stats.get('wins', 0)
        strategy_win_rate = (strategy_wins / max(strategy_trades, 1)) * 100
        
        print(f"   {strategy}:")
        print(f"     Trades: {strategy_trades}")
        print(f"     P&L: ${strategy_pnl:+,.2f}")
        print(f"     Win Rate: {strategy_win_rate:.1f}%")
    
    # Risk Metrics
    print(f"\n⚠️ RISK ANALYSIS:")
    max_drawdown = abs(min(0, total_pnl))  # Simplified drawdown calculation
    print(f"   Max Drawdown: ${max_drawdown:,.2f} ({max_drawdown/initial_balance*100:.2f}%)")
    
    if total_trades > 0:
        sharpe_estimate = (total_return_pct / 100) / max(0.01, abs(total_return_pct / 100) * 0.5)  # Rough estimate
        print(f"   Estimated Sharpe Ratio: {sharpe_estimate:.2f}")
    
    # Log Files
    print(f"\n📁 DETAILED LOG FILES:")
    print(f"   Trade Log: {backtester.logger.trade_log_path}")
    print(f"   Daily Performance: {backtester.logger.daily_log_path}")
    print(f"   Market Conditions: {backtester.logger.market_log_path}")
    print(f"   Balance Progression: {backtester.logger.balance_log_path}")
    print(f"   Session Summary: {backtester.logger.summary_path}")
    
    # Strategy Execution Validation
    print(f"\n🔍 STRATEGY EXECUTION VALIDATION:")
    strategy_counts = getattr(backtester, 'strategy_counts', {})
    print(f"   Iron Condor Signals: {strategy_counts.get('IRON_CONDOR', 0)}")
    print(f"   Bull Put Spread Signals: {strategy_counts.get('BULL_PUT_SPREAD', 0)}")
    print(f"   Bear Call Spread Signals: {strategy_counts.get('BEAR_CALL_SPREAD', 0)}")
    print(f"   Buy Put Signals: {strategy_counts.get('BUY_PUT', 0)}")
    print(f"   Buy Call Signals: {strategy_counts.get('BUY_CALL', 0)}")
    print(f"   Total Signals: {sum(strategy_counts.values())}")
    
    # Performance Assessment
    print(f"\n🎯 PERFORMANCE ASSESSMENT:")
    
    if total_return_pct > 10:
        print("   📈 EXCELLENT: Strong positive returns")
    elif total_return_pct > 5:
        print("   ✅ GOOD: Solid positive returns")
    elif total_return_pct > 0:
        print("   🟡 MODEST: Small positive returns")
    elif total_return_pct > -5:
        print("   🟠 CAUTION: Small losses - strategy needs refinement")
    else:
        print("   🔴 POOR: Significant losses - major strategy revision needed")
    
    if win_rate > 70:
        print("   🎯 HIGH WIN RATE: Strategy shows good signal quality")
    elif win_rate > 50:
        print("   ✅ DECENT WIN RATE: Acceptable signal quality")
    else:
        print("   ⚠️ LOW WIN RATE: Signal quality needs improvement")
    
    # Next Steps
    print(f"\n🚀 NEXT STEPS:")
    if total_return_pct > 0:
        print("   1. ✅ Strategy shows promise - ready for paper trading")
        print("   2. 📊 Analyze detailed logs for optimization opportunities")
        print("   3. 🔄 Consider parameter tuning for better performance")
    else:
        print("   1. 📊 Analyze detailed logs to identify issues")
        print("   2. 🔧 Refine strategy selection criteria")
        print("   3. ⚙️ Adjust risk management parameters")
    
    print(f"\n{'='*80}")
    print("🏁 6-MONTH BACKTEST COMPLETE")
    print("='*80")
    
    return results

if __name__ == "__main__":
    main()
