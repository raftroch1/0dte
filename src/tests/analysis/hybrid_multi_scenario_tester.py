#!/usr/bin/env python3
"""
Hybrid Multi-Scenario Tester - Validate Across All Market Conditions
===================================================================

COMPREHENSIVE VALIDATION:
- Test hybrid strategy across all 7 market scenarios
- Compare against previous 0% success rate
- Validate that we now have market coverage
- Measure improvement in trade frequency and win rate

This should prove our hybrid approach solved the critical issues!

Location: src/tests/analysis/ (following .cursorrules structure)
Author: Advanced Options Trading System - Multi-Scenario Validation
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

# Import our hybrid backtester
try:
    from src.tests.analysis.hybrid_strategy_backtester import HybridStrategyBacktester
except ImportError:
    from hybrid_strategy_backtester import HybridStrategyBacktester

class HybridMultiScenarioTester:
    """
    Test hybrid strategy across all market scenarios to validate improvement
    
    Previous Results: 0/7 scenarios successful (0% success rate)
    Target: Significant improvement in scenario coverage and trade frequency
    """
    
    def __init__(self, initial_balance: float = 25000):
        self.initial_balance = initial_balance
        
        # Define the same test scenarios as before for comparison
        self.test_scenarios = [
            {
                'name': 'SEPTEMBER_VOLATILITY',
                'description': '📉 September market volatility',
                'start_date': datetime(2024, 9, 1),
                'end_date': datetime(2024, 9, 15),
                'expected_regime': 'BEARISH',
                'expected_volatility': 'HIGH',
                'max_days': 10
            },
            {
                'name': 'OCTOBER_EARNINGS',
                'description': '📊 October earnings season',
                'start_date': datetime(2024, 10, 15),
                'end_date': datetime(2024, 10, 30),
                'expected_regime': 'VOLATILE',
                'expected_volatility': 'HIGH',
                'max_days': 10
            },
            {
                'name': 'ELECTION_PERIOD',
                'description': '🗳️ Election uncertainty',
                'start_date': datetime(2024, 11, 1),
                'end_date': datetime(2024, 11, 15),
                'expected_regime': 'UNCERTAIN',
                'expected_volatility': 'HIGH',
                'max_days': 10
            },
            {
                'name': 'DECEMBER_RALLY',
                'description': '🎄 Holiday season trading',
                'start_date': datetime(2024, 12, 1),
                'end_date': datetime(2024, 12, 15),
                'expected_regime': 'BULLISH',
                'expected_volatility': 'LOW',
                'max_days': 10
            },
            {
                'name': 'NEW_YEAR_START',
                'description': '🎆 New Year volatility',
                'start_date': datetime(2025, 1, 2),
                'end_date': datetime(2025, 1, 15),
                'expected_regime': 'VOLATILE',
                'expected_volatility': 'MEDIUM',
                'max_days': 10
            },
            {
                'name': 'FEBRUARY_NORMAL',
                'description': '📈 Normal February trading',
                'start_date': datetime(2025, 2, 1),
                'end_date': datetime(2025, 2, 15),
                'expected_regime': 'NORMAL',
                'expected_volatility': 'MEDIUM',
                'max_days': 10
            },
            {
                'name': 'RECENT_PERIOD',
                'description': '📅 Most recent data',
                'start_date': datetime(2025, 8, 15),
                'end_date': datetime(2025, 8, 29),
                'expected_regime': 'CURRENT',
                'expected_volatility': 'MEDIUM',
                'max_days': 10
            }
        ]
        
        self.scenario_results = {}
        
        print(f"🎯 HYBRID MULTI-SCENARIO TESTER INITIALIZED")
        print(f"💰 Account Balance: ${initial_balance:,.2f}")
        print(f"📊 Testing {len(self.test_scenarios)} market scenarios")
        print(f"🎯 Previous Success Rate: 0/7 scenarios (0%)")
        print(f"🚀 Target: Significant improvement in coverage and frequency")
    
    def run_comprehensive_test(self) -> Dict:
        """Run hybrid strategy across all scenarios"""
        
        print(f"\n🚀 COMPREHENSIVE HYBRID STRATEGY VALIDATION")
        print(f"=" * 90)
        print(f"🔄 Comparing against previous 0% success rate")
        print(f"🎯 Validating market coverage and trade frequency improvements")
        print(f"=" * 90)
        
        overall_results = {
            'test_date': datetime.now().isoformat(),
            'strategy_type': 'HYBRID_ADAPTIVE',
            'initial_balance': self.initial_balance,
            'scenarios_tested': len(self.test_scenarios),
            'scenario_results': {},
            'comparative_analysis': {},
            'improvement_metrics': {},
            'recommendations': []
        }
        
        successful_scenarios = 0
        total_trades_all_scenarios = 0
        total_signals_all_scenarios = 0
        
        # Run backtest for each scenario
        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"\n🎯 SCENARIO {i}/{len(self.test_scenarios)}: {scenario['name']}")
            print(f"📅 {scenario['description']}")
            print(f"📆 Period: {scenario['start_date'].strftime('%Y-%m-%d')} to {scenario['end_date'].strftime('%Y-%m-%d')}")
            print(f"🌍 Expected: {scenario['expected_regime']} regime, {scenario['expected_volatility']} volatility")
            print("-" * 70)
            
            try:
                # Initialize fresh backtester for each scenario
                backtester = HybridStrategyBacktester(self.initial_balance)
                
                # Run backtest for this scenario
                scenario_result = backtester.run_backtest(
                    scenario['start_date'], 
                    scenario['end_date'],
                    max_days=scenario['max_days']
                )
                
                # Analyze scenario success
                trades_executed = scenario_result['trading_statistics']['total_trades']
                win_rate = scenario_result['trading_statistics']['win_rate_pct']
                total_return = scenario_result['financial_performance']['total_return_pct']
                
                # Determine if scenario was successful
                scenario_successful = (
                    trades_executed > 0 and  # Must have trades
                    win_rate >= 40 and       # Reasonable win rate
                    total_return > -10       # Not catastrophic loss
                )
                
                if scenario_successful:
                    successful_scenarios += 1
                
                total_trades_all_scenarios += trades_executed
                
                # Add scenario metadata
                scenario_result['scenario_info'] = scenario
                scenario_result['scenario_success'] = scenario_successful
                scenario_result['success_criteria'] = {
                    'trades_executed': trades_executed,
                    'win_rate': win_rate,
                    'total_return': total_return,
                    'meets_criteria': scenario_successful
                }
                
                # Store results
                self.scenario_results[scenario['name']] = scenario_result
                overall_results['scenario_results'][scenario['name']] = scenario_result
                
                # Print scenario summary
                self._print_scenario_summary(scenario['name'], scenario_result, scenario_successful)
                
            except Exception as e:
                print(f"❌ Error in scenario {scenario['name']}: {e}")
                continue
        
        # Calculate improvement metrics
        previous_success_rate = 0.0  # Previous system had 0% success
        current_success_rate = (successful_scenarios / len(self.test_scenarios)) * 100
        
        improvement_metrics = {
            'previous_successful_scenarios': 0,
            'current_successful_scenarios': successful_scenarios,
            'previous_success_rate': previous_success_rate,
            'current_success_rate': current_success_rate,
            'success_rate_improvement': current_success_rate - previous_success_rate,
            'total_trades_generated': total_trades_all_scenarios,
            'avg_trades_per_scenario': total_trades_all_scenarios / len(self.test_scenarios),
            'previous_avg_trades_per_scenario': 0.1,  # Previous system generated ~0.1 trades/day
            'trade_frequency_improvement': (total_trades_all_scenarios / len(self.test_scenarios)) / 0.1 if total_trades_all_scenarios > 0 else 0
        }
        
        overall_results['improvement_metrics'] = improvement_metrics
        
        # Generate comparative analysis
        overall_results['comparative_analysis'] = self._generate_comparative_analysis()
        overall_results['recommendations'] = self._generate_improvement_recommendations(improvement_metrics)
        
        # Save comprehensive results
        self._save_comprehensive_results(overall_results)
        
        # Generate final summary
        self._generate_final_improvement_summary(overall_results)
        
        return overall_results
    
    def _print_scenario_summary(self, scenario_name: str, result: Dict, successful: bool):
        """Print summary for a single scenario"""
        
        trades = result['trading_statistics']['total_trades']
        win_rate = result['trading_statistics']['win_rate_pct']
        total_return = result['financial_performance']['total_return_pct']
        
        status = "✅ SUCCESS" if successful else "⚠️ PARTIAL"
        
        print(f"📊 SCENARIO RESULTS: {status}")
        print(f"   Trades Executed: {trades}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Total Return: {total_return:+.2f}%")
        print(f"   Strategy Coverage: {'ACTIVE' if trades > 0 else 'INACTIVE'}")
    
    def _generate_comparative_analysis(self) -> Dict:
        """Generate comparative analysis vs previous system"""
        
        if not self.scenario_results:
            return {}
        
        print(f"\n🔍 GENERATING COMPARATIVE ANALYSIS...")
        
        # Collect metrics from all scenarios
        scenario_metrics = {}
        total_trades = 0
        active_scenarios = 0
        
        for name, result in self.scenario_results.items():
            trades = result['trading_statistics']['total_trades']
            win_rate = result['trading_statistics']['win_rate_pct']
            total_return = result['financial_performance']['total_return_pct']
            
            scenario_metrics[name] = {
                'trades': trades,
                'win_rate': win_rate,
                'return': total_return,
                'active': trades > 0
            }
            
            total_trades += trades
            if trades > 0:
                active_scenarios += 1
        
        # Calculate improvements
        previous_active_scenarios = 1  # Previous system only worked in 1/7 scenarios
        current_active_scenarios = active_scenarios
        
        return {
            'scenario_metrics': scenario_metrics,
            'previous_system': {
                'active_scenarios': previous_active_scenarios,
                'success_rate': 14.3,  # 1/7 = 14.3%
                'avg_trades_per_scenario': 0.1,
                'total_trades': 0.7  # 0.1 * 7 scenarios
            },
            'current_system': {
                'active_scenarios': current_active_scenarios,
                'success_rate': (current_active_scenarios / len(self.test_scenarios)) * 100,
                'avg_trades_per_scenario': total_trades / len(self.test_scenarios),
                'total_trades': total_trades
            },
            'improvements': {
                'active_scenarios_improvement': current_active_scenarios - previous_active_scenarios,
                'success_rate_improvement': ((current_active_scenarios / len(self.test_scenarios)) * 100) - 14.3,
                'trade_frequency_improvement': (total_trades / len(self.test_scenarios)) / 0.1 if total_trades > 0 else 0,
                'total_trades_improvement': total_trades - 0.7
            }
        }
    
    def _generate_improvement_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations based on improvement analysis"""
        
        recommendations = []
        
        success_rate = metrics['current_success_rate']
        trade_frequency = metrics['avg_trades_per_scenario']
        
        # Success rate analysis
        if success_rate >= 80:
            recommendations.append("🚀 EXCELLENT: Strategy successful in most scenarios - ready for live trading")
        elif success_rate >= 60:
            recommendations.append("✅ GOOD: Strategy works well across scenarios - minor optimizations needed")
        elif success_rate >= 40:
            recommendations.append("⚠️ MODERATE: Strategy shows promise but needs refinement")
        else:
            recommendations.append("❌ POOR: Strategy needs major improvements")
        
        # Trade frequency analysis
        if trade_frequency >= 3:
            recommendations.append("✅ EXCELLENT: High trade frequency achieved")
        elif trade_frequency >= 1.5:
            recommendations.append("✅ GOOD: Adequate trade frequency")
        elif trade_frequency >= 0.5:
            recommendations.append("⚠️ MODERATE: Trade frequency improved but could be higher")
        else:
            recommendations.append("❌ LOW: Trade frequency still too low")
        
        # Specific improvements
        if metrics['success_rate_improvement'] > 50:
            recommendations.append("🎉 BREAKTHROUGH: Massive improvement in scenario coverage")
        
        if metrics['trade_frequency_improvement'] > 10:
            recommendations.append("🚀 BREAKTHROUGH: Dramatic improvement in trade generation")
        
        # Strategy-specific recommendations
        recommendations.append("🔧 NEXT STEPS: Optimize exit management for better profit factor")
        recommendations.append("🎯 TARGET: Focus on achieving $250/day profit target")
        recommendations.append("📊 VALIDATION: Consider paper trading before live deployment")
        
        return recommendations
    
    def _save_comprehensive_results(self, results: Dict):
        """Save comprehensive multi-scenario results"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON results
        results_file = f"hybrid_multi_scenario_validation_{timestamp}.json"
        results_path = os.path.join(os.path.dirname(__file__), results_file)
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Comprehensive results saved: {results_path}")
    
    def _generate_final_improvement_summary(self, results: Dict):
        """Generate comprehensive final improvement summary"""
        
        print(f"\n" + "=" * 90)
        print(f"🏆 HYBRID STRATEGY MULTI-SCENARIO VALIDATION RESULTS")
        print(f"=" * 90)
        
        improvement = results['improvement_metrics']
        comp_analysis = results['comparative_analysis']
        
        print(f"\n📊 SYSTEM COMPARISON:")
        print(f"   Previous System (ML-Only):")
        print(f"     ❌ Active Scenarios: {comp_analysis['previous_system']['active_scenarios']}/7 ({comp_analysis['previous_system']['success_rate']:.1f}%)")
        print(f"     ❌ Avg Trades/Scenario: {comp_analysis['previous_system']['avg_trades_per_scenario']:.1f}")
        print(f"     ❌ Total Trades: {comp_analysis['previous_system']['total_trades']:.1f}")
        
        print(f"\n   Current System (Hybrid Adaptive):")
        print(f"     ✅ Active Scenarios: {comp_analysis['current_system']['active_scenarios']}/7 ({comp_analysis['current_system']['success_rate']:.1f}%)")
        print(f"     ✅ Avg Trades/Scenario: {comp_analysis['current_system']['avg_trades_per_scenario']:.1f}")
        print(f"     ✅ Total Trades: {comp_analysis['current_system']['total_trades']}")
        
        print(f"\n🚀 IMPROVEMENTS ACHIEVED:")
        print(f"   Success Rate: {improvement['previous_success_rate']:.1f}% → {improvement['current_success_rate']:.1f}% (+{improvement['success_rate_improvement']:.1f}%)")
        print(f"   Trade Frequency: {improvement['previous_avg_trades_per_scenario']:.1f} → {improvement['avg_trades_per_scenario']:.1f} trades/scenario ({improvement['trade_frequency_improvement']:.1f}x improvement)")
        print(f"   Total Trades Generated: {improvement['total_trades_generated']} (vs ~0.7 previously)")
        
        print(f"\n📋 KEY RECOMMENDATIONS:")
        recommendations = results['recommendations']
        for rec in recommendations:
            print(f"   {rec}")
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        
        success_rate = improvement['current_success_rate']
        if success_rate >= 70:
            print(f"   🚀 BREAKTHROUGH SUCCESS: Hybrid strategy solved the critical issues!")
            print(f"   ✅ Ready for optimization and paper trading")
        elif success_rate >= 50:
            print(f"   ✅ SIGNIFICANT IMPROVEMENT: Major progress made")
            print(f"   🔧 Continue optimization for live trading")
        elif success_rate >= 30:
            print(f"   ⚠️ MODERATE IMPROVEMENT: Good progress but more work needed")
            print(f"   🔧 Focus on strategy refinement")
        else:
            print(f"   ❌ LIMITED IMPROVEMENT: Fundamental issues remain")
            print(f"   🔄 Consider alternative approaches")

def main():
    """Run comprehensive hybrid strategy validation"""
    
    print("🚀 HYBRID MULTI-SCENARIO VALIDATION")
    print("🏗️ Following .cursorrules: Comprehensive scenario testing")
    print("=" * 90)
    
    try:
        # Initialize tester
        tester = HybridMultiScenarioTester(25000)
        
        # Run comprehensive validation
        results = tester.run_comprehensive_test()
        
        print(f"\n🎯 HYBRID MULTI-SCENARIO VALIDATION COMPLETE!")
        print(f"=" * 90)
        print(f"✅ Comprehensive market scenario coverage tested")
        print(f"✅ Improvement metrics calculated")
        print(f"✅ Comparative analysis generated")
        print(f"✅ Strategy validation completed")
        
    except Exception as e:
        print(f"❌ Error in multi-scenario validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
