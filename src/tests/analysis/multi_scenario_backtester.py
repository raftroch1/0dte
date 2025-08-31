#!/usr/bin/env python3
"""
Multi-Scenario Backtester - Test Different Market Conditions
============================================================

COMPREHENSIVE SCENARIO TESTING:
1. Test strategy across different market conditions
2. Compare performance in various scenarios
3. Identify optimal market conditions for strategy
4. Validate robustness across time periods

SCENARIOS TO TEST:
- September Volatility (bear market stress)
- October Earnings (high volatility)
- Election Period (uncertainty)
- December Rally (bull market)
- New Year Start (fresh volatility)
- February Normal (steady trading)
- Recent Period (current conditions)

Location: src/tests/analysis/ (following .cursorrules structure)
Author: Advanced Options Trading System - Multi-Scenario Analysis
"""

import sys
import os
# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Import our optimized backtester
from src.tests.analysis.intraday_high_winrate_backtester import IntradayHighWinRateBacktester

class MultiScenarioAnalyzer:
    """
    Analyze strategy performance across multiple market scenarios
    """
    
    def __init__(self, initial_balance: float = 25000):
        self.initial_balance = initial_balance
        
        # Define test scenarios
        self.test_scenarios = [
            {
                'name': 'SEPTEMBER_VOLATILITY',
                'description': '📉 September market volatility',
                'start_date': datetime(2024, 9, 1),
                'end_date': datetime(2024, 9, 15),
                'expected_regime': 'BEARISH',
                'expected_volatility': 'HIGH'
            },
            {
                'name': 'OCTOBER_EARNINGS',
                'description': '📊 October earnings season',
                'start_date': datetime(2024, 10, 15),
                'end_date': datetime(2024, 10, 30),
                'expected_regime': 'VOLATILE',
                'expected_volatility': 'HIGH'
            },
            {
                'name': 'ELECTION_PERIOD',
                'description': '🗳️ Election uncertainty',
                'start_date': datetime(2024, 11, 1),
                'end_date': datetime(2024, 11, 15),
                'expected_regime': 'UNCERTAIN',
                'expected_volatility': 'HIGH'
            },
            {
                'name': 'DECEMBER_RALLY',
                'description': '🎄 Holiday season trading',
                'start_date': datetime(2024, 12, 1),
                'end_date': datetime(2024, 12, 15),
                'expected_regime': 'BULLISH',
                'expected_volatility': 'LOW'
            },
            {
                'name': 'NEW_YEAR_START',
                'description': '🎆 New Year volatility',
                'start_date': datetime(2025, 1, 2),
                'end_date': datetime(2025, 1, 15),
                'expected_regime': 'VOLATILE',
                'expected_volatility': 'MEDIUM'
            },
            {
                'name': 'FEBRUARY_NORMAL',
                'description': '📈 Normal February trading',
                'start_date': datetime(2025, 2, 1),
                'end_date': datetime(2025, 2, 15),
                'expected_regime': 'NORMAL',
                'expected_volatility': 'MEDIUM'
            },
            {
                'name': 'RECENT_PERIOD',
                'description': '📅 Most recent data',
                'start_date': datetime(2025, 8, 15),
                'end_date': datetime(2025, 8, 29),
                'expected_regime': 'CURRENT',
                'expected_volatility': 'MEDIUM'
            }
        ]
        
        self.scenario_results = {}
    
    def run_multi_scenario_analysis(self) -> Dict:
        """Run backtests across all scenarios"""
        
        print("🚀 MULTI-SCENARIO BACKTESTER")
        print("=" * 90)
        print(f"💰 Account Balance: ${self.initial_balance:,.2f}")
        print(f"🎯 Testing {len(self.test_scenarios)} different market scenarios")
        print(f"📊 Goal: Find optimal conditions for $250/day target")
        print("=" * 90)
        
        overall_results = {
            'analysis_date': datetime.now().isoformat(),
            'initial_balance': self.initial_balance,
            'scenarios_tested': len(self.test_scenarios),
            'scenario_results': {},
            'comparative_analysis': {},
            'recommendations': []
        }
        
        # Run backtest for each scenario
        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"\n🎯 SCENARIO {i}/{len(self.test_scenarios)}: {scenario['name']}")
            print(f"📅 {scenario['description']}")
            print(f"📆 Period: {scenario['start_date'].strftime('%Y-%m-%d')} to {scenario['end_date'].strftime('%Y-%m-%d')}")
            print(f"🌍 Expected: {scenario['expected_regime']} regime, {scenario['expected_volatility']} volatility")
            print("-" * 60)
            
            try:
                # Initialize fresh backtester for each scenario
                backtester = IntradayHighWinRateBacktester(initial_balance=self.initial_balance)
                
                # Run backtest for this scenario
                scenario_result = backtester.run_intraday_high_winrate_backtest(
                    scenario['start_date'], 
                    scenario['end_date'],
                    max_days=15
                )
                
                # Add scenario metadata
                scenario_result['scenario_info'] = scenario
                scenario_result['scenario_performance'] = self._analyze_scenario_performance(scenario_result)
                
                # Store results
                self.scenario_results[scenario['name']] = scenario_result
                overall_results['scenario_results'][scenario['name']] = scenario_result
                
                # Print scenario summary
                self._print_scenario_summary(scenario['name'], scenario_result)
                
            except Exception as e:
                print(f"❌ Error in scenario {scenario['name']}: {e}")
                continue
        
        # Generate comparative analysis
        overall_results['comparative_analysis'] = self._generate_comparative_analysis()
        overall_results['recommendations'] = self._generate_scenario_recommendations()
        
        # Save comprehensive results
        self._save_multi_scenario_results(overall_results)
        
        # Generate final comparative summary
        self._generate_final_comparative_summary(overall_results)
        
        return overall_results
    
    def _analyze_scenario_performance(self, result: Dict) -> Dict:
        """Analyze performance metrics for a single scenario"""
        
        summary = result['backtest_summary']
        intraday = result['intraday_metrics']
        trades = result['trade_statistics']
        
        # Calculate key metrics
        total_return = summary['total_return_pct']
        win_rate = intraday['win_rate_pct']
        trades_per_day = intraday['avg_trades_per_day']
        daily_target_rate = summary['target_achievement_rate']
        
        # Performance scoring (0-100)
        return_score = min(100, max(0, (total_return + 10) * 5))  # -10% to +10% maps to 0-100
        win_rate_score = min(100, max(0, win_rate * 2))  # 0% to 50% maps to 0-100
        frequency_score = min(100, max(0, trades_per_day * 20))  # 0 to 5 trades/day maps to 0-100
        target_score = daily_target_rate  # Already 0-100%
        
        overall_score = (return_score + win_rate_score + frequency_score + target_score) / 4
        
        return {
            'total_return_pct': total_return,
            'win_rate_pct': win_rate,
            'trades_per_day': trades_per_day,
            'target_achievement_rate': daily_target_rate,
            'performance_scores': {
                'return_score': return_score,
                'win_rate_score': win_rate_score,
                'frequency_score': frequency_score,
                'target_score': target_score,
                'overall_score': overall_score
            },
            'grade': self._get_performance_grade(overall_score)
        }
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert performance score to letter grade"""
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    
    def _print_scenario_summary(self, scenario_name: str, result: Dict):
        """Print summary for a single scenario"""
        
        perf = result['scenario_performance']
        
        print(f"📊 SCENARIO RESULTS:")
        print(f"   Return: {perf['total_return_pct']:+.2f}%")
        print(f"   Win Rate: {perf['win_rate_pct']:.1f}%")
        print(f"   Trades/Day: {perf['trades_per_day']:.1f}")
        print(f"   Target Hit: {perf['target_achievement_rate']:.1f}% of days")
        print(f"   Overall Grade: {perf['grade']} ({perf['performance_scores']['overall_score']:.0f}/100)")
    
    def _generate_comparative_analysis(self) -> Dict:
        """Generate comparative analysis across all scenarios"""
        
        if not self.scenario_results:
            return {}
        
        print(f"\n🔍 GENERATING COMPARATIVE ANALYSIS...")
        
        # Collect metrics from all scenarios
        scenario_metrics = {}
        
        for name, result in self.scenario_results.items():
            perf = result['scenario_performance']
            scenario_metrics[name] = {
                'return': perf['total_return_pct'],
                'win_rate': perf['win_rate_pct'],
                'trades_per_day': perf['trades_per_day'],
                'target_rate': perf['target_achievement_rate'],
                'overall_score': perf['performance_scores']['overall_score'],
                'grade': perf['grade']
            }
        
        # Find best and worst performing scenarios
        best_scenario = max(scenario_metrics.keys(), 
                          key=lambda x: scenario_metrics[x]['overall_score'])
        worst_scenario = min(scenario_metrics.keys(), 
                           key=lambda x: scenario_metrics[x]['overall_score'])
        
        # Calculate averages
        avg_return = np.mean([m['return'] for m in scenario_metrics.values()])
        avg_win_rate = np.mean([m['win_rate'] for m in scenario_metrics.values()])
        avg_trades_per_day = np.mean([m['trades_per_day'] for m in scenario_metrics.values()])
        avg_target_rate = np.mean([m['target_rate'] for m in scenario_metrics.values()])
        
        # Identify patterns
        high_performers = [name for name, metrics in scenario_metrics.items() 
                          if metrics['overall_score'] >= 60]
        low_performers = [name for name, metrics in scenario_metrics.items() 
                         if metrics['overall_score'] < 40]
        
        return {
            'scenario_metrics': scenario_metrics,
            'best_scenario': {
                'name': best_scenario,
                'score': scenario_metrics[best_scenario]['overall_score'],
                'metrics': scenario_metrics[best_scenario]
            },
            'worst_scenario': {
                'name': worst_scenario,
                'score': scenario_metrics[worst_scenario]['overall_score'],
                'metrics': scenario_metrics[worst_scenario]
            },
            'averages': {
                'return': avg_return,
                'win_rate': avg_win_rate,
                'trades_per_day': avg_trades_per_day,
                'target_rate': avg_target_rate
            },
            'performance_categories': {
                'high_performers': high_performers,
                'low_performers': low_performers
            }
        }
    
    def _generate_scenario_recommendations(self) -> List[str]:
        """Generate recommendations based on scenario analysis"""
        
        recommendations = []
        
        if not self.scenario_results:
            return ["❌ No scenario data available for recommendations"]
        
        comp_analysis = self._generate_comparative_analysis()
        
        # Best scenario recommendations
        best = comp_analysis['best_scenario']
        recommendations.append(f"✅ BEST PERFORMANCE: {best['name']} (Grade: {best['metrics']['grade']}, Score: {best['score']:.0f})")
        
        # Performance pattern analysis
        high_performers = comp_analysis['performance_categories']['high_performers']
        low_performers = comp_analysis['performance_categories']['low_performers']
        
        if len(high_performers) >= 3:
            recommendations.append(f"✅ CONSISTENT PERFORMER: Strategy works well across {len(high_performers)} scenarios")
        elif len(high_performers) >= 1:
            recommendations.append(f"⚠️ LIMITED SUCCESS: Only {len(high_performers)} scenarios performed well")
        else:
            recommendations.append(f"❌ POOR PERFORMANCE: No scenarios achieved good results")
        
        # Specific recommendations based on averages
        averages = comp_analysis['averages']
        
        if averages['win_rate'] < 40:
            recommendations.append("🔧 CRITICAL: Win rate too low across all scenarios - need better entry criteria")
        elif averages['win_rate'] < 50:
            recommendations.append("🔧 IMPROVE: Win rate needs optimization - adjust ML thresholds")
        else:
            recommendations.append("✅ GOOD: Win rate acceptable across scenarios")
        
        if averages['trades_per_day'] < 2:
            recommendations.append("🔧 CRITICAL: Signal frequency too low - need more aggressive signal generation")
        elif averages['trades_per_day'] < 3:
            recommendations.append("🔧 IMPROVE: Signal frequency below target - optimize entry filters")
        else:
            recommendations.append("✅ GOOD: Signal frequency adequate")
        
        if averages['target_rate'] < 10:
            recommendations.append("🔧 CRITICAL: Daily target rarely achieved - major strategy revision needed")
        elif averages['target_rate'] < 25:
            recommendations.append("🔧 IMPROVE: Daily target achievement low - optimize profit targets")
        else:
            recommendations.append("✅ GOOD: Daily target achievement reasonable")
        
        # Market condition recommendations
        if 'DECEMBER_RALLY' in high_performers:
            recommendations.append("📈 INSIGHT: Strategy performs well in bullish conditions")
        if 'SEPTEMBER_VOLATILITY' in low_performers:
            recommendations.append("📉 INSIGHT: Strategy struggles in high volatility bear markets")
        if 'FEBRUARY_NORMAL' in high_performers:
            recommendations.append("📊 INSIGHT: Strategy works well in normal market conditions")
        
        return recommendations
    
    def _save_multi_scenario_results(self, results: Dict):
        """Save comprehensive multi-scenario results"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON results
        results_file = f"multi_scenario_analysis_{timestamp}.json"
        results_path = os.path.join(os.path.dirname(__file__), results_file)
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Multi-scenario results saved: {results_path}")
    
    def _generate_final_comparative_summary(self, results: Dict):
        """Generate comprehensive final summary"""
        
        print(f"\n" + "=" * 90)
        print(f"🏆 MULTI-SCENARIO ANALYSIS RESULTS")
        print(f"=" * 90)
        
        comp_analysis = results['comparative_analysis']
        
        if not comp_analysis:
            print("❌ No comparative analysis available")
            return
        
        print(f"\n📊 SCENARIO PERFORMANCE RANKING:")
        scenario_metrics = comp_analysis['scenario_metrics']
        
        # Sort scenarios by overall score
        sorted_scenarios = sorted(scenario_metrics.items(), 
                                key=lambda x: x[1]['overall_score'], 
                                reverse=True)
        
        for i, (name, metrics) in enumerate(sorted_scenarios, 1):
            print(f"   {i}. {name:<20} Grade: {metrics['grade']} ({metrics['overall_score']:>3.0f}/100) "
                  f"Return: {metrics['return']:>+5.1f}% WinRate: {metrics['win_rate']:>4.1f}%")
        
        print(f"\n🎯 OVERALL AVERAGES:")
        averages = comp_analysis['averages']
        print(f"   Average Return: {averages['return']:+.2f}%")
        print(f"   Average Win Rate: {averages['win_rate']:.1f}%")
        print(f"   Average Trades/Day: {averages['trades_per_day']:.1f}")
        print(f"   Average Target Rate: {averages['target_rate']:.1f}%")
        
        print(f"\n🏆 BEST vs WORST:")
        best = comp_analysis['best_scenario']
        worst = comp_analysis['worst_scenario']
        print(f"   🥇 BEST: {best['name']} (Grade: {best['metrics']['grade']}, {best['score']:.0f}/100)")
        print(f"   🥉 WORST: {worst['name']} (Grade: {worst['metrics']['grade']}, {worst['score']:.0f}/100)")
        
        print(f"\n📋 KEY RECOMMENDATIONS:")
        recommendations = results['recommendations']
        for rec in recommendations:
            print(f"   {rec}")
        
        print(f"\n🎯 FINAL STRATEGY ASSESSMENT:")
        
        # Overall strategy viability
        high_performers = len(comp_analysis['performance_categories']['high_performers'])
        total_scenarios = len(scenario_metrics)
        success_rate = (high_performers / total_scenarios) * 100
        
        if success_rate >= 70:
            print(f"   🚀 EXCELLENT: Strategy successful in {high_performers}/{total_scenarios} scenarios ({success_rate:.0f}%)")
            print(f"   ✅ READY FOR PAPER TRADING")
        elif success_rate >= 50:
            print(f"   ✅ GOOD: Strategy successful in {high_performers}/{total_scenarios} scenarios ({success_rate:.0f}%)")
            print(f"   🔧 Minor optimizations recommended")
        elif success_rate >= 30:
            print(f"   ⚠️ MIXED: Strategy successful in {high_performers}/{total_scenarios} scenarios ({success_rate:.0f}%)")
            print(f"   🔧 Significant optimization needed")
        else:
            print(f"   ❌ POOR: Strategy successful in {high_performers}/{total_scenarios} scenarios ({success_rate:.0f}%)")
            print(f"   🔄 Major strategy revision required")

def main():
    """Run multi-scenario analysis"""
    
    print("🚀 MULTI-SCENARIO BACKTESTER")
    print("🏗️ Following .cursorrules: Comprehensive scenario testing")
    print("=" * 90)
    
    try:
        analyzer = MultiScenarioAnalyzer(initial_balance=25000)
        results = analyzer.run_multi_scenario_analysis()
        
        print(f"\n🎯 MULTI-SCENARIO ANALYSIS COMPLETE!")
        print(f"=" * 90)
        print(f"✅ Tested {len(analyzer.test_scenarios)} market scenarios")
        print(f"✅ Identified optimal market conditions")
        print(f"✅ Generated strategy recommendations")
        print(f"✅ Comprehensive robustness validation")
        
    except Exception as e:
        print(f"❌ Error in multi-scenario analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
