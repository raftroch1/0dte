#!/usr/bin/env python3
"""
Phase 1: Baseline Performance Assessment
=======================================

Comprehensive backtest of Enhanced 0DTE Strategy with year-long real data
to establish baseline performance metrics before ML enhancement.

Following .cursorrules: Real data, comprehensive analysis, proper documentation.
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

from src.data.parquet_data_loader import ParquetDataLoader
from src.strategies.enhanced_0dte.strategy import Enhanced0DTEStrategy, Enhanced0DTEBacktester

class BaselineAssessment:
    """Comprehensive baseline assessment of Enhanced 0DTE Strategy"""
    
    def __init__(self):
        self.loader = ParquetDataLoader()
        self.backtester = Enhanced0DTEBacktester(self.loader)
        
    def run_comprehensive_baseline(self, start_date: datetime, end_date: datetime, 
                                 max_days: int = 50) -> Dict:
        """Run comprehensive baseline assessment"""
        
        print("🎯 PHASE 1: BASELINE PERFORMANCE ASSESSMENT")
        print("=" * 80)
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"🎯 Strategy: Enhanced 0DTE with Greeks (Baseline)")
        print(f"📊 Dataset: Year-long SPY options (2.3M records)")
        print(f"=" * 80)
        
        # Run enhanced backtest
        results = self.backtester.run_enhanced_0dte_backtest(
            start_date, end_date, max_days=max_days
        )
        
        # Generate comprehensive metrics
        metrics = self._calculate_comprehensive_metrics(results)
        
        # Save results
        self._save_baseline_results(results, metrics, start_date, end_date)
        
        return {
            'results': results,
            'metrics': metrics,
            'status': 'baseline_complete'
        }
    
    def _calculate_comprehensive_metrics(self, results: Dict) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        trades = results.get('results', [])
        
        if not trades:
            return {'error': 'No trades executed'}
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        winning_pnls = [t['pnl'] for t in trades if t['pnl'] > 0]
        losing_pnls = [t['pnl'] for t in trades if t['pnl'] <= 0]
        
        avg_win = np.mean(winning_pnls) if winning_pnls else 0
        avg_loss = np.mean(losing_pnls) if losing_pnls else 0
        
        # Risk metrics
        pnl_series = pd.Series([t['pnl'] for t in trades])
        cumulative_pnl = pnl_series.cumsum()
        
        # Calculate drawdown
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (simplified)
        returns = pnl_series / 1000  # Normalize to percentage returns
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Greeks utilization analysis
        greeks_trades = len([t for t in trades if t.get('greeks_used', False)])
        greeks_utilization = greeks_trades / total_trades * 100 if total_trades > 0 else 0
        
        # Market regime analysis
        regime_performance = {}
        for trade in trades:
            regime = trade.get('market_regime', 'UNKNOWN')
            if regime not in regime_performance:
                regime_performance[regime] = {'trades': 0, 'pnl': 0, 'wins': 0}
            regime_performance[regime]['trades'] += 1
            regime_performance[regime]['pnl'] += trade['pnl']
            if trade['pnl'] > 0:
                regime_performance[regime]['wins'] += 1
        
        # Calculate regime win rates
        for regime in regime_performance:
            perf = regime_performance[regime]
            perf['win_rate'] = perf['wins'] / perf['trades'] * 100 if perf['trades'] > 0 else 0
            perf['avg_pnl'] = perf['pnl'] / perf['trades'] if perf['trades'] > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'greeks_utilization': greeks_utilization,
            'regime_performance': regime_performance,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else float('inf'),
            'expectancy': avg_pnl,
            'risk_reward_ratio': abs(avg_win / avg_loss) if avg_loss != 0 else 0
        }
    
    def _save_baseline_results(self, results: Dict, metrics: Dict, 
                             start_date: datetime, end_date: datetime):
        """Save baseline results for future comparison"""
        
        baseline_data = {
            'assessment_date': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'strategy': 'Enhanced 0DTE with Greeks (Baseline)',
            'dataset': 'Year-long SPY Options (2.3M records)',
            'results': results,
            'metrics': metrics
        }
        
        # Save to file
        filename = f"baseline_assessment_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(baseline_data, f, indent=2, default=str)
        
        print(f"\n💾 Baseline results saved to: {filename}")
        
    def generate_baseline_report(self, metrics: Dict):
        """Generate comprehensive baseline report"""
        
        print(f"\n" + "=" * 80)
        print(f"📊 BASELINE PERFORMANCE REPORT")
        print(f"=" * 80)
        
        print(f"\n📈 OVERALL PERFORMANCE:")
        print(f"   Total Trades: {metrics['total_trades']}")
        print(f"   Win Rate: {metrics['win_rate']:.1f}% ({metrics['winning_trades']}/{metrics['total_trades']})")
        print(f"   Total P&L: ${metrics['total_pnl']:.2f}")
        print(f"   Average P&L: ${metrics['avg_pnl']:.2f}")
        print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
        
        print(f"\n📊 RISK METRICS:")
        print(f"   Max Drawdown: ${metrics['max_drawdown']:.2f}")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Average Win: ${metrics['avg_win']:.2f}")
        print(f"   Average Loss: ${metrics['avg_loss']:.2f}")
        print(f"   Risk/Reward: {metrics['risk_reward_ratio']:.2f}")
        
        print(f"\n🎯 STRATEGY FEATURES:")
        print(f"   Greeks Utilization: {metrics['greeks_utilization']:.1f}%")
        print(f"   Expectancy: ${metrics['expectancy']:.2f}")
        
        print(f"\n🌍 MARKET REGIME PERFORMANCE:")
        for regime, perf in metrics['regime_performance'].items():
            print(f"   {regime}: {perf['trades']} trades, {perf['win_rate']:.1f}% win rate, ${perf['avg_pnl']:.2f} avg P&L")
        
        print(f"\n🎯 BASELINE ASSESSMENT COMPLETE!")
        print(f"✅ Ready for Phase 2: ML Feature Engineering")
        print(f"✅ Baseline metrics established for ML comparison")

def main():
    """Run baseline assessment"""
    
    try:
        assessment = BaselineAssessment()
        
        # Define assessment period (recent months with rich data)
        end_date = datetime(2025, 8, 29)
        start_date = datetime(2025, 8, 1)  # 1 month for comprehensive analysis
        
        print("🚀 Starting Baseline Performance Assessment...")
        
        # Run comprehensive baseline
        results = assessment.run_comprehensive_baseline(start_date, end_date, max_days=20)
        
        # Generate report
        if 'metrics' in results and 'error' not in results['metrics']:
            assessment.generate_baseline_report(results['metrics'])
        else:
            print("❌ Baseline assessment failed - no trades or data issues")
            
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Review baseline performance metrics")
        print(f"2. Proceed to Phase 2: ML Feature Engineering")
        print(f"3. Train ML models to enhance signal generation")
        print(f"4. Compare ML-enhanced vs baseline performance")
        
    except Exception as e:
        print(f"❌ Error in baseline assessment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
