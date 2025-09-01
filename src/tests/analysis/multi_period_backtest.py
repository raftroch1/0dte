#!/usr/bin/env python3
"""
📅 MULTI-PERIOD BACKTEST ANALYSIS
==================================
Tests the same 0DTE strategy across different 6-month periods to determine
if Jan-June 2024 was anomalously bad or if the strategy is fundamentally flawed.

Following @.cursorrules: Using existing infrastructure, real data analysis.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.analysis.unified_strategy_backtester import UnifiedStrategyBacktester
from data.parquet_data_loader import ParquetDataLoader
import pandas as pd
from datetime import datetime, timedelta
import json

class MultiPeriodAnalyzer:
    def __init__(self):
        self.parquet_path = "src/data/spy_options_20230830_20240829.parquet"
        self.results = {}
        
        # Define test periods (6-month windows)
        self.test_periods = [
            ("2023-08-30", "2024-02-29", "Aug2023-Feb2024"),  # 6 months from start of data
            ("2023-11-01", "2024-04-30", "Nov2023-Apr2024"),  # Shifted 3 months
            ("2024-01-01", "2024-06-30", "Jan2024-Jun2024"),  # Original period (slightly adjusted)
            ("2024-03-01", "2024-08-29", "Mar2024-Aug2024"),  # Latest 6 months
        ]
        
        print(f"🔍 MULTI-PERIOD ANALYSIS SETUP:")
        print(f"   Data Source: {self.parquet_path}")
        print(f"   Test Periods: {len(self.test_periods)}")
        for start, end, name in self.test_periods:
            print(f"     {name}: {start} to {end}")

    def run_period_backtest(self, start_date: str, end_date: str, period_name: str):
        """Run backtest for a specific period"""
        print(f"\n🚀 TESTING PERIOD: {period_name}")
        print(f"   Dates: {start_date} to {end_date}")
        print("=" * 50)
        
        try:
            # Initialize backtester
            backtester = UnifiedStrategyBacktester(initial_balance=25000.0)
            
            # Run backtest
            results = backtester.run_unified_backtest(start_date, end_date)
            
            # Get session summary
            session_summary = backtester.logger.generate_session_summary()
            
            # Store results
            self.results[period_name] = {
                'period': f"{start_date} to {end_date}",
                'initial_balance': session_summary['performance']['initial_balance'],
                'final_balance': session_summary['performance']['final_balance'],
                'total_pnl': session_summary['performance']['total_pnl'],
                'total_return_pct': session_summary['performance']['total_return_pct'],
                'total_trades': session_summary['performance']['total_trades'],
                'win_rate_pct': session_summary['performance']['win_rate_pct'],
                'avg_trade_pnl': session_summary['performance']['avg_trade_pnl'],
                'best_trade': session_summary['performance']['best_trade'],
                'worst_trade': session_summary['performance']['worst_trade'],
                'strategy_breakdown': session_summary['strategy_breakdown'],
                'session_id': backtester.logger.session_id
            }
            
            print(f"✅ PERIOD COMPLETE: {period_name}")
            print(f"   Total Return: {session_summary['performance']['total_return_pct']:.2f}%")
            print(f"   Win Rate: {session_summary['performance']['win_rate_pct']:.1f}%")
            print(f"   Total Trades: {session_summary['performance']['total_trades']}")
            
        except Exception as e:
            print(f"❌ PERIOD FAILED: {period_name}")
            print(f"   Error: {str(e)}")
            self.results[period_name] = {
                'error': str(e),
                'period': f"{start_date} to {end_date}"
            }

    def run_all_periods(self):
        """Run backtests for all defined periods"""
        print("🚀 STARTING MULTI-PERIOD ANALYSIS")
        print("=" * 60)
        
        for start_date, end_date, period_name in self.test_periods:
            self.run_period_backtest(start_date, end_date, period_name)
        
        print(f"\n✅ ALL PERIODS COMPLETE!")
        self.generate_comparative_analysis()

    def generate_comparative_analysis(self):
        """Generate comparative analysis across all periods"""
        print(f"\n📊 COMPARATIVE ANALYSIS ACROSS PERIODS")
        print("=" * 60)
        
        # Create summary table
        successful_results = {k: v for k, v in self.results.items() if 'error' not in v}
        
        if not successful_results:
            print("❌ NO SUCCESSFUL BACKTESTS TO ANALYZE")
            return
        
        print(f"\n📈 PERFORMANCE SUMMARY:")
        print(f"{'Period':<20} {'Return %':<10} {'Win Rate %':<12} {'Trades':<8} {'Avg P&L':<10}")
        print("-" * 70)
        
        total_returns = []
        total_win_rates = []
        
        for period_name, results in successful_results.items():
            return_pct = results['total_return_pct']
            win_rate = results['win_rate_pct']
            trades = results['total_trades']
            avg_pnl = results['avg_trade_pnl']
            
            total_returns.append(return_pct)
            total_win_rates.append(win_rate)
            
            print(f"{period_name:<20} {return_pct:>8.2f}% {win_rate:>10.1f}% {trades:>6} ${avg_pnl:>8.2f}")
        
        # Calculate averages
        avg_return = sum(total_returns) / len(total_returns)
        avg_win_rate = sum(total_win_rates) / len(total_win_rates)
        
        print("-" * 70)
        print(f"{'AVERAGE':<20} {avg_return:>8.2f}% {avg_win_rate:>10.1f}%")
        
        # Strategy consistency analysis
        print(f"\n🎯 STRATEGY CONSISTENCY ANALYSIS:")
        
        # Collect strategy performance across periods
        strategy_performance = {}
        for period_name, results in successful_results.items():
            for strategy, stats in results['strategy_breakdown'].items():
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = {
                        'periods': [],
                        'win_rates': [],
                        'total_pnls': []
                    }
                
                win_rate = (stats['wins'] / max(stats['count'], 1)) * 100
                strategy_performance[strategy]['periods'].append(period_name)
                strategy_performance[strategy]['win_rates'].append(win_rate)
                strategy_performance[strategy]['total_pnls'].append(stats['total_pnl'])
        
        for strategy, data in strategy_performance.items():
            avg_win_rate = sum(data['win_rates']) / len(data['win_rates'])
            avg_pnl = sum(data['total_pnls']) / len(data['total_pnls'])
            periods_tested = len(data['periods'])
            
            print(f"\n{strategy}:")
            print(f"   Periods Tested: {periods_tested}")
            print(f"   Average Win Rate: {avg_win_rate:.1f}%")
            print(f"   Average P&L: ${avg_pnl:,.2f}")
            print(f"   Consistency: {'CONSISTENT' if max(data['win_rates']) - min(data['win_rates']) < 20 else 'INCONSISTENT'}")
        
        # Final verdict
        print(f"\n💡 FINAL VERDICT:")
        if avg_return < -20:
            print(f"   🔴 STRATEGY IS FUNDAMENTALLY FLAWED")
            print(f"   📊 Average return of {avg_return:.1f}% across multiple periods")
            print(f"   📊 Average win rate of {avg_win_rate:.1f}% is far below profitable threshold")
            print(f"   🎯 RECOMMENDATION: Pivot to 1-3 DTE immediately")
        elif avg_return < 0:
            print(f"   🟡 STRATEGY NEEDS MAJOR IMPROVEMENTS")
            print(f"   📊 Consistently losing money across periods")
            print(f"   🎯 RECOMMENDATION: Test 1-3 DTE and fix regime detection")
        else:
            print(f"   🟢 STRATEGY HAS POTENTIAL")
            print(f"   📊 Positive average return across periods")
            print(f"   🎯 RECOMMENDATION: Optimize parameters and test live")
        
        # Save results to file
        results_file = f"logs/multi_period_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📁 RESULTS SAVED: {results_file}")

if __name__ == "__main__":
    analyzer = MultiPeriodAnalyzer()
    analyzer.run_all_periods()
