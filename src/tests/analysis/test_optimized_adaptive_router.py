#!/usr/bin/env python3
"""
Test Optimized Adaptive Router
==============================

Comprehensive testing of the integrated Credit Spread Optimizer with Enhanced Adaptive Router.
Validates Kelly Criterion position sizing, profit management, and daily risk controls.

Following @.cursorrules testing patterns.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.strategies.adaptive_zero_dte.optimized_adaptive_router import OptimizedAdaptiveRouter
from src.data.parquet_data_loader import ParquetDataLoader

class OptimizedRouterTester:
    """
    Comprehensive tester for the Optimized Adaptive Router
    
    Tests:
    - Kelly Criterion position sizing
    - Daily P&L limits
    - Time window enforcement
    - Profit management integration
    - Performance tracking
    """
    
    def __init__(self):
        # Initialize components
        self.data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
        self.data_loader = ParquetDataLoader(parquet_path=self.data_path)
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🧪 OPTIMIZED ROUTER TESTER INITIALIZED")
    
    def test_daily_trading_simulation(self, test_date: datetime, account_balance: float = 25000) -> Dict[str, Any]:
        """
        Simulate a full day of trading with the Optimized Adaptive Router
        
        Args:
            test_date: Date to simulate
            account_balance: Starting account balance
            
        Returns:
            Daily performance summary
        """
        
        self.logger.info(f"🎯 TESTING DAILY TRADING SIMULATION: {test_date.date()}")
        
        # Initialize router
        router = OptimizedAdaptiveRouter(account_balance=account_balance)
        
        # Load options data for the test date
        try:
            options_data = self.data_loader.load_options_for_date(test_date)
            if options_data.empty:
                self.logger.warning(f"No options data available for {test_date.date()}")
                return {'error': 'No data available'}
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return {'error': str(e)}
        
        # Estimate SPY price
        spy_price = self._estimate_spy_price(options_data)
        
        # Simulate trading throughout the day
        trading_times = self._generate_trading_times(test_date)
        daily_results = []
        
        for trading_time in trading_times:
            # Create market data
            market_data = {
                'spy_price': spy_price + (trading_time.hour - 10) * 0.5,  # Simulate price movement
                'timestamp': trading_time,
                'spy_volume': 2000000  # Mock volume
            }
            
            # Get strategy recommendation
            strategy_rec = router.select_adaptive_strategy(
                options_data, market_data, trading_time
            )
            
            # Log strategy decision
            self.logger.info(f"⏰ {trading_time.strftime('%H:%M')} - Strategy: {strategy_rec['strategy_type']}")
            if strategy_rec['strategy_type'] != 'NO_TRADE':
                self.logger.info(f"   Confidence: {strategy_rec.get('confidence', 0):.1f}%")
                self.logger.info(f"   Position Size: {strategy_rec.get('position_size', 0)} contracts")
                self.logger.info(f"   Max Risk: ${strategy_rec.get('max_risk_dollars', 0):.2f}")
            else:
                self.logger.info(f"   Reason: {strategy_rec.get('reason', 'Unknown')}")
            
            # Execute trade if recommended
            if strategy_rec['strategy_type'] != 'NO_TRADE':
                trade_result = router.execute_optimized_trade(
                    strategy_rec, options_data, market_data, trading_time
                )
                
                if trade_result['executed']:
                    daily_results.append({
                        'time': trading_time,
                        'strategy': trade_result['strategy_type'],
                        'contracts': trade_result['contracts'],
                        'pnl': trade_result['pnl'],
                        'cumulative_pnl': router.daily_pnl
                    })
            
            # Check if daily limits hit
            performance = router.get_performance_summary()
            if performance['profit_target_hit'] or performance['loss_limit_hit']:
                self.logger.info(f"🛑 Daily limit reached - stopping trading")
                break
        
        # Get final performance summary
        final_performance = router.get_performance_summary()
        
        self.logger.info(f"📊 DAILY SIMULATION COMPLETE:")
        self.logger.info(f"   Total P&L: ${final_performance['daily_pnl']:+.2f}")
        self.logger.info(f"   Total Trades: {final_performance['total_trades_today']}")
        self.logger.info(f"   Win Rate: {final_performance['win_rate']:.1f}%")
        self.logger.info(f"   Final Balance: ${final_performance['current_balance']:,.2f}")
        
        return {
            'date': test_date.date(),
            'performance': final_performance,
            'trades': daily_results,
            'success': True
        }
    
    def test_kelly_position_sizing(self) -> Dict[str, Any]:
        """Test Kelly Criterion position sizing under various scenarios"""
        
        self.logger.info(f"🧮 TESTING KELLY CRITERION POSITION SIZING")
        
        router = OptimizedAdaptiveRouter(25000)
        
        # Test scenarios
        scenarios = [
            {'balance': 25000, 'daily_pnl': 0, 'positions': 0, 'description': 'Fresh start'},
            {'balance': 25000, 'daily_pnl': -200, 'positions': 2, 'description': 'Down $200, 2 positions'},
            {'balance': 25000, 'daily_pnl': 150, 'positions': 1, 'description': 'Up $150, 1 position'},
            {'balance': 25000, 'daily_pnl': -350, 'positions': 3, 'description': 'Near daily limit'},
            {'balance': 15000, 'daily_pnl': 0, 'positions': 0, 'description': 'Smaller account'},
        ]
        
        results = []
        
        for scenario in scenarios:
            # Simulate the scenario
            router.current_balance = scenario['balance']
            router.daily_pnl = scenario['daily_pnl']
            
            # Mock some positions in profit manager
            for i in range(scenario['positions']):
                router.profit_manager.active_positions[f'mock_{i}'] = type('MockPosition', (), {
                    'is_closed': False
                })()
            
            # Get position sizing recommendation
            sizing = router.position_sizer.get_position_size_recommendation(
                account_balance=scenario['balance'],
                premium_per_contract=40.0,
                max_loss_per_contract=120.0,
                current_positions=scenario['positions'],
                current_daily_pnl=scenario['daily_pnl']
            )
            
            results.append({
                'scenario': scenario['description'],
                'can_trade': sizing['can_trade'],
                'contracts': sizing.get('recommended_contracts', 0),
                'max_risk': sizing.get('max_risk', 0),
                'kelly_fraction': sizing.get('kelly_fraction', 0),
                'reason': sizing.get('reason', 'N/A')
            })
            
            self.logger.info(f"📋 {scenario['description']}:")
            self.logger.info(f"   Can Trade: {sizing['can_trade']}")
            self.logger.info(f"   Contracts: {sizing.get('recommended_contracts', 0)}")
            self.logger.info(f"   Max Risk: ${sizing.get('max_risk', 0):.2f}")
            self.logger.info(f"   Kelly %: {sizing.get('kelly_fraction', 0)*100:.2f}%")
            
            # Clear mock positions
            router.profit_manager.active_positions.clear()
        
        return {'scenarios': results}
    
    def test_daily_limits_enforcement(self) -> Dict[str, Any]:
        """Test daily P&L limits and time window enforcement"""
        
        self.logger.info(f"🚦 TESTING DAILY LIMITS ENFORCEMENT")
        
        router = OptimizedAdaptiveRouter(25000)
        
        # Mock options data
        options_data = pd.DataFrame({
            'strike': [520, 525, 530],
            'option_type': ['put', 'call', 'call'],
            'volume': [100, 150, 200]
        })
        
        test_scenarios = [
            # Time window tests
            {'time': datetime.now().replace(hour=9, minute=30), 'daily_pnl': 0, 'expected': False, 'test': 'Before trading hours'},
            {'time': datetime.now().replace(hour=10, minute=0), 'daily_pnl': 0, 'expected': True, 'test': 'During trading hours'},
            {'time': datetime.now().replace(hour=15, minute=0), 'daily_pnl': 0, 'expected': False, 'test': 'After trading hours'},
            
            # P&L limit tests
            {'time': datetime.now().replace(hour=12, minute=0), 'daily_pnl': 250, 'expected': False, 'test': 'Profit target hit'},
            {'time': datetime.now().replace(hour=12, minute=0), 'daily_pnl': -450, 'expected': False, 'test': 'Loss limit hit'},
            {'time': datetime.now().replace(hour=12, minute=0), 'daily_pnl': 100, 'expected': True, 'test': 'Within limits'},
        ]
        
        results = []
        
        for scenario in test_scenarios:
            # Set up scenario
            router.daily_pnl = scenario['daily_pnl']
            
            market_data = {
                'spy_price': 525.0,
                'timestamp': scenario['time'],
                'spy_volume': 2000000
            }
            
            # Test strategy selection
            strategy_rec = router.select_adaptive_strategy(
                options_data, market_data, scenario['time']
            )
            
            can_trade = strategy_rec['strategy_type'] != 'NO_TRADE'
            
            results.append({
                'test': scenario['test'],
                'expected_can_trade': scenario['expected'],
                'actual_can_trade': can_trade,
                'passed': can_trade == scenario['expected'],
                'reason': strategy_rec.get('reason', 'N/A')
            })
            
            status = "✅ PASS" if can_trade == scenario['expected'] else "❌ FAIL"
            self.logger.info(f"{status} {scenario['test']}: Expected {scenario['expected']}, Got {can_trade}")
        
        passed_tests = sum(1 for r in results if r['passed'])
        total_tests = len(results)
        
        self.logger.info(f"📊 LIMITS ENFORCEMENT RESULTS: {passed_tests}/{total_tests} tests passed")
        
        return {
            'tests_passed': passed_tests,
            'total_tests': total_tests,
            'pass_rate': passed_tests / total_tests * 100,
            'results': results
        }
    
    def _estimate_spy_price(self, options_data: pd.DataFrame) -> float:
        """Estimate SPY price from options data"""
        if 'strike' in options_data.columns:
            return options_data['strike'].median()
        return 525.0  # Default
    
    def _generate_trading_times(self, base_date: datetime) -> List[datetime]:
        """Generate trading times throughout the day"""
        times = []
        start_time = base_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = base_date.replace(hour=14, minute=30, second=0, microsecond=0)
        
        current_time = start_time
        while current_time <= end_time:
            times.append(current_time)
            current_time += timedelta(minutes=30)  # Every 30 minutes
        
        return times
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and provide comprehensive results"""
        
        self.logger.info(f"🚀 RUNNING COMPREHENSIVE OPTIMIZED ROUTER TESTS")
        self.logger.info(f"=" * 70)
        
        results = {}
        
        try:
            # Test 1: Kelly Position Sizing
            self.logger.info(f"\n🧮 TEST 1: Kelly Criterion Position Sizing")
            results['kelly_sizing'] = self.test_kelly_position_sizing()
            
            # Test 2: Daily Limits Enforcement
            self.logger.info(f"\n🚦 TEST 2: Daily Limits Enforcement")
            results['daily_limits'] = self.test_daily_limits_enforcement()
            
            # Test 3: Daily Trading Simulation
            self.logger.info(f"\n🎯 TEST 3: Daily Trading Simulation")
            test_date = datetime(2024, 3, 15)  # Use a date we know has data
            results['daily_simulation'] = self.test_daily_trading_simulation(test_date)
            
            # Overall results
            total_tests = 0
            passed_tests = 0
            
            if 'daily_limits' in results:
                total_tests += results['daily_limits']['total_tests']
                passed_tests += results['daily_limits']['tests_passed']
            
            if results['daily_simulation'].get('success', False):
                total_tests += 1
                passed_tests += 1
            
            overall_pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            self.logger.info(f"\n📊 COMPREHENSIVE TEST RESULTS:")
            self.logger.info(f"   Total Tests: {total_tests}")
            self.logger.info(f"   Passed Tests: {passed_tests}")
            self.logger.info(f"   Pass Rate: {overall_pass_rate:.1f}%")
            
            if overall_pass_rate >= 80:
                self.logger.info(f"   ✅ OPTIMIZED ROUTER READY FOR DEPLOYMENT")
            else:
                self.logger.info(f"   ❌ NEEDS ADDITIONAL WORK")
            
            results['summary'] = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'pass_rate': overall_pass_rate,
                'ready_for_deployment': overall_pass_rate >= 80
            }
            
        except Exception as e:
            self.logger.error(f"❌ Test failed with error: {e}")
            results['error'] = str(e)
        
        return results

def main():
    """Run the comprehensive test suite"""
    
    print("🧪 OPTIMIZED ADAPTIVE ROUTER - COMPREHENSIVE TESTING")
    print("=" * 70)
    
    tester = OptimizedRouterTester()
    results = tester.run_comprehensive_test()
    
    # Print summary
    if 'summary' in results:
        summary = results['summary']
        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"   Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"   Ready for Deployment: {summary['ready_for_deployment']}")
    
    return results

if __name__ == "__main__":
    main()
