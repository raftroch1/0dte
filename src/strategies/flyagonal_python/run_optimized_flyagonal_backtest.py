#!/usr/bin/env python3
"""
🦋 OPTIMIZED FLYAGONAL BACKTEST RUNNER
=====================================
Run backtest with the optimized Flyagonal strategy that works with real data constraints.

Key Optimizations Tested:
1. Flexible DTE requirements (5-15 DTE)
2. Adaptive expiration pairing
3. Relaxed vega tolerance (±100)
4. Realistic risk/reward ratios
5. Simplified position construction

Following @.cursorrules:
- Uses real market data constraints
- Isolated from other strategies
- Comprehensive performance tracking

Location: src/strategies/flyagonal_python/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Optimized Flyagonal Backtest
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import traceback

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def create_optimized_flyagonal_backtester():
    """Create backtester for optimized Flyagonal strategy"""
    
    try:
        from optimized_flyagonal_strategy import OptimizedFlyagonalStrategy, OptimizedFlyagonalPosition
        from src.data.parquet_data_loader import ParquetDataLoader
        
        class OptimizedFlyagonalBacktester:
            """Backtester for optimized Flyagonal strategy"""
            
            def __init__(self, initial_balance: float = 25000):
                self.initial_balance = initial_balance
                self.current_balance = initial_balance
                
                # Initialize data loader
                data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
                self.data_loader = ParquetDataLoader(parquet_path=data_path)
                
                # Initialize optimized strategy
                self.flyagonal_strategy = OptimizedFlyagonalStrategy(initial_balance)
                
                # Tracking
                self.daily_results = []
                self.trade_log = []
                
                print("🦋 OPTIMIZED FLYAGONAL BACKTESTER INITIALIZED")
                print(f"   Strategy: Data-Driven Optimized")
                print(f"   Initial Balance: ${initial_balance:,.2f}")
                print(f"   Target Win Rate: 80%")
                print(f"   DTE Range: 5-15 days")
            
            def run_backtest(self, start_date: str = "2023-09-01", end_date: str = "2023-09-30") -> dict:
                """Run optimized Flyagonal backtest"""
                
                print(f"\n🦋 STARTING OPTIMIZED FLYAGONAL BACKTEST")
                print(f"   Period: {start_date} to {end_date}")
                print(f"   Strategy: Data-Driven Optimized")
                print("="*60)
                
                try:
                    # Get trading days
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    trading_days = self.data_loader.get_available_dates(start_dt, end_dt)
                    trading_days = [dt.strftime('%Y-%m-%d') for dt in trading_days]
                    
                    if not trading_days:
                        print(f"❌ No trading days found")
                        return {'error': 'No trading days found'}
                    
                    print(f"📊 Processing {len(trading_days)} trading days...")
                    
                    # Process each day
                    for i, trading_day in enumerate(trading_days):
                        print(f"\n📅 Day {i+1}/{len(trading_days)}: {trading_day}")
                        
                        try:
                            # Load options data
                            trading_day_dt = datetime.strptime(trading_day, '%Y-%m-%d')
                            options_data = self.data_loader.load_options_for_date(trading_day_dt)
                            
                            if options_data.empty:
                                print(f"   ❌ No options data")
                                continue
                            
                            # Get SPY price
                            spy_price = self._estimate_spy_price(options_data)
                            print(f"   SPY: ${spy_price:.2f} | Options: {len(options_data)}")
                            
                            # Check for entry
                            if self.flyagonal_strategy.should_enter_optimized_flyagonal(options_data, spy_price, trading_day_dt):
                                print(f"   ✅ Entry conditions met")
                                
                                position = self.flyagonal_strategy.execute_optimized_flyagonal_entry(
                                    options_data, spy_price, trading_day_dt
                                )
                                
                                if position:
                                    print(f"   📈 Position opened: {position.position_id}")
                                    
                                    self.trade_log.append({
                                        'date': trading_day,
                                        'action': 'ENTRY',
                                        'position_id': position.position_id,
                                        'spy_price': spy_price,
                                        'net_vega': position.net_vega,
                                        'max_profit': position.max_profit_potential,
                                        'max_loss': position.max_loss_potential
                                    })
                                else:
                                    print(f"   ❌ Entry failed")
                            else:
                                print(f"   ⏭️  No entry signal")
                            
                            # Manage existing positions
                            positions_to_close = []
                            for position in list(self.flyagonal_strategy.open_positions):
                                should_close, exit_reason = self.flyagonal_strategy.should_close_position(
                                    position, trading_day_dt
                                )
                                
                                if should_close:
                                    positions_to_close.append((position, exit_reason))
                            
                            # Close positions
                            for position, exit_reason in positions_to_close:
                                final_pnl = self.flyagonal_strategy.close_position(
                                    position, trading_day_dt, exit_reason
                                )
                                
                                print(f"   🔚 Position closed: {position.position_id}")
                                print(f"      Reason: {exit_reason} | Days: {position.days_held:.1f} | P&L: ${final_pnl:.2f}")
                                
                                self.current_balance = self.flyagonal_strategy.current_balance
                                
                                self.trade_log.append({
                                    'date': trading_day,
                                    'action': 'EXIT',
                                    'position_id': position.position_id,
                                    'exit_reason': exit_reason,
                                    'days_held': position.days_held,
                                    'pnl': final_pnl,
                                    'balance': self.current_balance
                                })
                            
                            # Store daily result
                            daily_pnl = self.current_balance - self.initial_balance
                            self.daily_results.append({
                                'date': trading_day,
                                'balance': self.current_balance,
                                'daily_pnl': daily_pnl,
                                'open_positions': len(self.flyagonal_strategy.open_positions),
                                'total_trades': self.flyagonal_strategy.total_trades
                            })
                            
                        except Exception as e:
                            print(f"   ❌ Error processing {trading_day}: {e}")
                            continue
                    
                    # Force close remaining positions
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    for position in list(self.flyagonal_strategy.open_positions):
                        final_pnl = self.flyagonal_strategy.close_position(
                            position, end_dt, "BACKTEST_END"
                        )
                        self.current_balance = self.flyagonal_strategy.current_balance
                    
                    # Generate results
                    return self._generate_results(start_date, end_date)
                    
                except Exception as e:
                    print(f"❌ Backtest error: {e}")
                    traceback.print_exc()
                    return {'error': str(e)}
            
            def _estimate_spy_price(self, options_data) -> float:
                """Estimate SPY price from options data"""
                try:
                    calls = options_data[options_data['option_type'] == 'call']
                    if not calls.empty:
                        return calls['strike'].median()
                    return 450.0
                except:
                    return 450.0
            
            def _generate_results(self, start_date: str, end_date: str) -> dict:
                """Generate comprehensive results"""
                
                strategy_stats = self.flyagonal_strategy.get_strategy_statistics()
                
                total_pnl = self.current_balance - self.initial_balance
                total_return = (total_pnl / self.initial_balance) * 100
                
                winning_trades = self.flyagonal_strategy.winning_trades
                total_trades = self.flyagonal_strategy.total_trades
                win_rate = (winning_trades / max(total_trades, 1)) * 100
                
                if self.flyagonal_strategy.closed_positions:
                    avg_hold_days = sum(pos.days_held for pos in self.flyagonal_strategy.closed_positions) / len(self.flyagonal_strategy.closed_positions)
                else:
                    avg_hold_days = 0
                
                if total_trades > 0:
                    avg_gain_per_trade = total_pnl / total_trades
                    avg_gain_pct = (avg_gain_per_trade / self.initial_balance) * 100
                else:
                    avg_gain_per_trade = 0
                    avg_gain_pct = 0
                
                results = {
                    'backtest_period': f"{start_date} to {end_date}",
                    'strategy': 'Optimized Flyagonal (Data-Driven)',
                    'initial_balance': self.initial_balance,
                    'final_balance': self.current_balance,
                    'total_pnl': total_pnl,
                    'total_return_pct': total_return,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': total_trades - winning_trades,
                    'win_rate': win_rate,
                    'avg_hold_days': avg_hold_days,
                    'avg_gain_per_trade': avg_gain_per_trade,
                    'avg_gain_pct': avg_gain_pct,
                    'daily_results': self.daily_results,
                    'trade_log': self.trade_log,
                    'strategy_stats': strategy_stats,
                    'optimization_comparison': {
                        'target_win_rate': 80.0,
                        'actual_win_rate': win_rate,
                        'target_monthly_return': 15.0,
                        'actual_return': total_return,
                        'dte_flexibility': '5-15 DTE (vs 8-10)',
                        'vega_tolerance': '±100 (vs ±50)',
                        'performance_assessment': self._assess_performance(win_rate, total_return, total_trades)
                    }
                }
                
                self._display_results(results)
                return results
            
            def _assess_performance(self, win_rate: float, total_return: float, total_trades: int) -> str:
                """Assess strategy performance"""
                
                if total_trades == 0:
                    return "NO_TRADES_EXECUTED"
                elif win_rate >= 70 and total_return > 5:
                    return "EXCELLENT"
                elif win_rate >= 60 and total_return > 2:
                    return "GOOD"
                elif win_rate >= 50 and total_return > 0:
                    return "ACCEPTABLE"
                else:
                    return "NEEDS_IMPROVEMENT"
            
            def _display_results(self, results: dict):
                """Display comprehensive results"""
                
                print(f"\n🎯 OPTIMIZED FLYAGONAL BACKTEST COMPLETE")
                print("="*55)
                print(f"Strategy: {results['strategy']}")
                print(f"Period: {results['backtest_period']}")
                print(f"")
                
                print(f"💰 FINANCIAL PERFORMANCE:")
                print(f"   Initial Balance: ${results['initial_balance']:,.2f}")
                print(f"   Final Balance: ${results['final_balance']:,.2f}")
                print(f"   Total P&L: ${results['total_pnl']:,.2f}")
                print(f"   Total Return: {results['total_return_pct']:.2f}%")
                print(f"")
                
                print(f"📈 TRADING STATISTICS:")
                print(f"   Total Trades: {results['total_trades']}")
                print(f"   Winning Trades: {results['winning_trades']}")
                print(f"   Losing Trades: {results['losing_trades']}")
                print(f"   Win Rate: {results['win_rate']:.1f}%")
                print(f"   Average Hold: {results['avg_hold_days']:.1f} days")
                print(f"   Avg Gain/Trade: ${results['avg_gain_per_trade']:.2f} ({results['avg_gain_pct']:.2f}%)")
                print(f"")
                
                # Optimization comparison
                comparison = results['optimization_comparison']
                print(f"🔧 OPTIMIZATION RESULTS:")
                print(f"   Target Win Rate: {comparison['target_win_rate']:.0f}% | Actual: {comparison['actual_win_rate']:.1f}%")
                print(f"   DTE Flexibility: {comparison['dte_flexibility']}")
                print(f"   Vega Tolerance: {comparison['vega_tolerance']}")
                print(f"   Performance: {comparison['performance_assessment']}")
                print(f"")
                
                # Performance assessment
                assessment = comparison['performance_assessment']
                if assessment == "NO_TRADES_EXECUTED":
                    print(f"⚠️  ASSESSMENT: NO TRADES EXECUTED")
                    print(f"   Strategy still too restrictive - needs further optimization")
                elif assessment in ["EXCELLENT", "GOOD"]:
                    print(f"✅ ASSESSMENT: {assessment}")
                    print(f"   Strategy shows strong performance")
                elif assessment == "ACCEPTABLE":
                    print(f"⚡ ASSESSMENT: {assessment}")
                    print(f"   Strategy works but could be improved")
                else:
                    print(f"❌ ASSESSMENT: {assessment}")
                    print(f"   Strategy needs significant optimization")
        
        return OptimizedFlyagonalBacktester
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None

def run_optimized_flyagonal_backtest():
    """Run the optimized Flyagonal backtest"""
    
    print("🦋 OPTIMIZED FLYAGONAL STRATEGY BACKTEST")
    print("="*55)
    print("⚡ OPTIMIZATIONS APPLIED:")
    print("   - Flexible DTE: 5-15 days (vs 8-10)")
    print("   - Relaxed Vega: ±100 (vs ±50)")
    print("   - Higher Risk: 3% (vs 2%)")
    print("   - Realistic Win Rate: 80% (vs 96%)")
    print("   - Simplified Construction")
    print("="*55)
    
    # Create backtester
    BacktesterClass = create_optimized_flyagonal_backtester()
    if not BacktesterClass:
        print("❌ Could not create optimized backtester")
        return None
    
    # Initialize and run
    backtester = BacktesterClass(initial_balance=25000)
    
    # Run backtest (2 weeks)
    results = backtester.run_backtest(
        start_date="2023-09-01",
        end_date="2023-09-15"
    )
    
    if 'error' in results:
        print(f"❌ Backtest failed: {results['error']}")
        return None
    
    # Show recent trades
    if results['trade_log']:
        print(f"\n📋 RECENT TRADES:")
        for trade in results['trade_log'][-6:]:  # Last 6 trades
            if trade['action'] == 'ENTRY':
                print(f"   📈 {trade['date']}: ENTRY {trade['position_id']}")
                print(f"      SPY: ${trade['spy_price']:.2f} | Vega: {trade['net_vega']:.1f}")
            else:
                print(f"   🔚 {trade['date']}: EXIT {trade['position_id']} ({trade['exit_reason']})")
                print(f"      Days: {trade['days_held']:.1f} | P&L: ${trade['pnl']:.2f}")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting OPTIMIZED Flyagonal Backtest...")
    print("(Data-Driven Approach - Realistic Parameters)")
    print()
    
    results = run_optimized_flyagonal_backtest()
    
    if results and 'error' not in results:
        print(f"\n✅ OPTIMIZED FLYAGONAL BACKTEST COMPLETE")
        print(f"   Strategy: Data-Driven Optimized")
        print(f"   Return: {results['total_return_pct']:.2f}%")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Assessment: {results['optimization_comparison']['performance_assessment']}")
        
        if results['total_trades'] > 0:
            print(f"   🎯 SUCCESS: Strategy is executing trades!")
        else:
            print(f"   ⚠️  Still no trades - need more optimization")
            
    else:
        print(f"\n❌ OPTIMIZED FLYAGONAL BACKTEST FAILED")
    
    print(f"\n🔍 NEXT STEPS:")
    if results and results.get('total_trades', 0) > 0:
        print(f"   1. ✅ Strategy working - analyze performance")
        print(f"   2. Extend backtest period")
        print(f"   3. Fine-tune parameters")
        print(f"   4. Compare to Iron Condor results")
    else:
        print(f"   1. Further relax entry conditions")
        print(f"   2. Debug position construction")
        print(f"   3. Consider alternative approach")
