#!/usr/bin/env python3
"""
🦋 CORRECTED FLYAGONAL BACKTEST RUNNER
=====================================
Run real backtest with the corrected Flyagonal strategy based on Steve Guns methodology.

This will test:
1. 8-10 DTE entry timing
2. Broken wing butterfly construction
3. Put diagonal calendar construction
4. Vega balancing in real market conditions
5. 4.5 day average hold period
6. Target 96% win rate validation

Following @.cursorrules:
- Uses real market data, no simulation
- Isolated from Iron Condor system
- Comprehensive logging and reporting

Location: src/strategies/flyagonal_python/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Corrected Flyagonal Backtest
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import traceback
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def create_corrected_flyagonal_backtester():
    """Create backtester for corrected Flyagonal strategy"""
    
    try:
        from corrected_flyagonal_strategy import CorrectedFlyagonalStrategy, CorrectedFlyagonalPosition
        from src.data.parquet_data_loader import ParquetDataLoader
        
        class CorrectedFlyagonalBacktester:
            """Real backtester for corrected Flyagonal strategy"""
            
            def __init__(self, initial_balance: float = 25000):
                self.initial_balance = initial_balance
                self.current_balance = initial_balance
                
                # Initialize data loader
                data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
                self.data_loader = ParquetDataLoader(parquet_path=data_path)
                
                # Initialize corrected Flyagonal strategy
                self.flyagonal_strategy = CorrectedFlyagonalStrategy(initial_balance)
                
                # Tracking
                self.daily_results = []
                self.trade_log = []
                
                print("🦋 CORRECTED FLYAGONAL BACKTESTER INITIALIZED")
                print(f"   Strategy: Steve Guns Methodology")
                print(f"   Initial Balance: ${initial_balance:,.2f}")
                print(f"   Target Win Rate: 96%")
                print(f"   Target Avg Gain: 10%")
            
            def run_backtest(self, start_date: str = "2023-09-01", end_date: str = "2023-09-30") -> dict:
                """Run corrected Flyagonal backtest"""
                
                print(f"\n🦋 STARTING CORRECTED FLYAGONAL BACKTEST")
                print(f"   Period: {start_date} to {end_date}")
                print(f"   Strategy: Steve Guns Methodology")
                print("="*60)
                
                try:
                    # Get trading days
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    trading_days = self.data_loader.get_available_dates(start_dt, end_dt)
                    trading_days = [dt.strftime('%Y-%m-%d') for dt in trading_days]
                    
                    if not trading_days:
                        print(f"❌ No trading days found in range {start_date} to {end_date}")
                        return {'error': 'No trading days found'}
                    
                    print(f"📊 Processing {len(trading_days)} trading days...")
                    
                    # Process each trading day
                    for i, trading_day in enumerate(trading_days):
                        print(f"\n📅 Day {i+1}/{len(trading_days)}: {trading_day}")
                        
                        try:
                            # Load options data
                            trading_day_dt = datetime.strptime(trading_day, '%Y-%m-%d')
                            options_data = self.data_loader.load_options_for_date(trading_day_dt)
                            
                            if options_data.empty:
                                print(f"   ❌ No options data for {trading_day}")
                                continue
                            
                            # Get SPY price estimate
                            spy_price = self._estimate_spy_price(options_data)
                            print(f"   SPY Price: ${spy_price:.2f}")
                            print(f"   Available Options: {len(options_data)}")
                            
                            # Check for entry opportunities
                            if self.flyagonal_strategy.should_enter_flyagonal(options_data, spy_price, trading_day_dt):
                                print(f"   ✅ Entry conditions met")
                                
                                # Execute entry
                                position = self.flyagonal_strategy.execute_flyagonal_entry(
                                    options_data, spy_price, trading_day_dt
                                )
                                
                                if position:
                                    print(f"   📈 Flyagonal position opened: {position.position_id}")
                                    
                                    # Log trade entry
                                    self.trade_log.append({
                                        'date': trading_day,
                                        'action': 'ENTRY',
                                        'position_id': position.position_id,
                                        'spy_price': spy_price,
                                        'butterfly_vega': position.butterfly_vega,
                                        'diagonal_vega': position.diagonal_vega,
                                        'net_vega': position.net_vega,
                                        'max_profit': position.max_profit_potential,
                                        'max_loss': position.max_loss_potential
                                    })
                                else:
                                    print(f"   ❌ Failed to execute entry")
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
                                print(f"      Exit Reason: {exit_reason}")
                                print(f"      Days Held: {position.days_held:.1f}")
                                print(f"      P&L: ${final_pnl:.2f}")
                                
                                # Update balance
                                self.current_balance = self.flyagonal_strategy.current_balance
                                
                                # Log trade exit
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
                    
                    # Force close any remaining positions at end
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    for position in list(self.flyagonal_strategy.open_positions):
                        final_pnl = self.flyagonal_strategy.close_position(
                            position, end_dt, "BACKTEST_END"
                        )
                        self.current_balance = self.flyagonal_strategy.current_balance
                    
                    # Generate comprehensive results
                    return self._generate_results(start_date, end_date)
                    
                except Exception as e:
                    print(f"❌ Backtest error: {e}")
                    traceback.print_exc()
                    return {'error': str(e)}
            
            def _estimate_spy_price(self, options_data: pd.DataFrame) -> float:
                """Estimate SPY price from options data"""
                try:
                    # Use median strike as SPY estimate
                    calls = options_data[options_data['option_type'] == 'call']
                    if not calls.empty:
                        return calls['strike'].median()
                    return 450.0  # Fallback
                except:
                    return 450.0
            
            def _generate_results(self, start_date: str, end_date: str) -> dict:
                """Generate comprehensive backtest results"""
                
                # Get strategy statistics
                strategy_stats = self.flyagonal_strategy.get_strategy_statistics()
                
                # Calculate performance metrics
                total_pnl = self.current_balance - self.initial_balance
                total_return = (total_pnl / self.initial_balance) * 100
                
                # Analyze trades
                winning_trades = self.flyagonal_strategy.winning_trades
                total_trades = self.flyagonal_strategy.total_trades
                win_rate = (winning_trades / max(total_trades, 1)) * 100
                
                # Calculate average hold period
                if self.flyagonal_strategy.closed_positions:
                    avg_hold_days = sum(pos.days_held for pos in self.flyagonal_strategy.closed_positions) / len(self.flyagonal_strategy.closed_positions)
                else:
                    avg_hold_days = 0
                
                # Calculate average gain per trade
                if total_trades > 0:
                    avg_gain_per_trade = total_pnl / total_trades
                    avg_gain_pct = (avg_gain_per_trade / self.initial_balance) * 100
                else:
                    avg_gain_per_trade = 0
                    avg_gain_pct = 0
                
                results = {
                    'backtest_period': f"{start_date} to {end_date}",
                    'strategy': 'Corrected Flyagonal (Steve Guns Methodology)',
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
                    'steve_guns_comparison': {
                        'target_win_rate': 96.0,
                        'actual_win_rate': win_rate,
                        'target_avg_gain': 10.0,
                        'actual_avg_gain': avg_gain_pct,
                        'target_hold_days': 4.5,
                        'actual_hold_days': avg_hold_days,
                        'performance_vs_target': {
                            'win_rate_diff': win_rate - 96.0,
                            'gain_diff': avg_gain_pct - 10.0,
                            'hold_days_diff': avg_hold_days - 4.5
                        }
                    }
                }
                
                # Display results
                self._display_results(results)
                
                return results
            
            def _display_results(self, results: dict):
                """Display comprehensive backtest results"""
                
                print(f"\n🎯 CORRECTED FLYAGONAL BACKTEST COMPLETE")
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
                
                # Steve Guns comparison
                comparison = results['steve_guns_comparison']
                print(f"🦋 STEVE GUNS METHODOLOGY COMPARISON:")
                print(f"   Target Win Rate: {comparison['target_win_rate']:.0f}% | Actual: {comparison['actual_win_rate']:.1f}% | Diff: {comparison['performance_vs_target']['win_rate_diff']:+.1f}%")
                print(f"   Target Avg Gain: {comparison['target_avg_gain']:.0f}% | Actual: {comparison['actual_avg_gain']:.2f}% | Diff: {comparison['performance_vs_target']['gain_diff']:+.2f}%")
                print(f"   Target Hold Days: {comparison['target_hold_days']:.1f} | Actual: {comparison['actual_hold_days']:.1f} | Diff: {comparison['performance_vs_target']['hold_days_diff']:+.1f}")
                print(f"")
                
                # Performance assessment
                if results['win_rate'] >= 80 and results['total_return_pct'] > 0:
                    print(f"✅ PERFORMANCE ASSESSMENT: SUCCESSFUL")
                    print(f"   Strategy shows promise with {results['win_rate']:.1f}% win rate")
                elif results['total_trades'] == 0:
                    print(f"⚠️  PERFORMANCE ASSESSMENT: NO TRADES")
                    print(f"   Strategy needs adjustment for entry conditions")
                else:
                    print(f"❌ PERFORMANCE ASSESSMENT: NEEDS IMPROVEMENT")
                    print(f"   Win rate: {results['win_rate']:.1f}% | Return: {results['total_return_pct']:.2f}%")
        
        return CorrectedFlyagonalBacktester
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None

def run_corrected_flyagonal_backtest():
    """Run the corrected Flyagonal backtest"""
    
    print("🦋 CORRECTED FLYAGONAL STRATEGY BACKTEST")
    print("="*55)
    print("⚠️  IMPORTANT: This uses Steve Guns methodology")
    print("   - 8-10 DTE entry timing")
    print("   - Broken wing butterfly (negative vega)")
    print("   - Put diagonal calendar (positive vega)")
    print("   - Vega balanced portfolio")
    print("   - 4.5 day average hold")
    print("   - Target: 96% win rate, 10% avg gain")
    print("="*55)
    
    # Create backtester
    BacktesterClass = create_corrected_flyagonal_backtester()
    if not BacktesterClass:
        print("❌ Could not create corrected Flyagonal backtester")
        return None
    
    # Initialize and run
    backtester = BacktesterClass(initial_balance=25000)
    
    # Run backtest (start with 2 weeks)
    results = backtester.run_backtest(
        start_date="2023-09-01",
        end_date="2023-09-15"  # 2 weeks to start
    )
    
    if 'error' in results:
        print(f"❌ Backtest failed: {results['error']}")
        return None
    
    # Show trade details if any
    if results['trade_log']:
        print(f"\n📋 TRADE LOG:")
        for trade in results['trade_log'][-10:]:  # Last 10 trades
            if trade['action'] == 'ENTRY':
                print(f"   📈 {trade['date']}: ENTRY {trade['position_id']}")
                print(f"      SPY: ${trade['spy_price']:.2f} | Net Vega: {trade['net_vega']:.1f}")
            else:
                print(f"   🔚 {trade['date']}: EXIT {trade['position_id']} ({trade['exit_reason']})")
                print(f"      Days: {trade['days_held']:.1f} | P&L: ${trade['pnl']:.2f}")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting REAL Corrected Flyagonal Backtest...")
    print("(Steve Guns Methodology - NOT the original flawed version)")
    print()
    
    results = run_corrected_flyagonal_backtest()
    
    if results and 'error' not in results:
        print(f"\n✅ CORRECTED FLYAGONAL BACKTEST COMPLETE")
        print(f"   Strategy: Steve Guns Methodology")
        print(f"   Return: {results['total_return_pct']:.2f}%")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Avg Hold: {results['avg_hold_days']:.1f} days")
        
        # Compare to benchmarks
        if results['win_rate'] >= 80:
            print(f"   🎯 Strong performance vs 96% target")
        else:
            print(f"   📊 Below 96% target - may need optimization")
            
    else:
        print(f"\n❌ CORRECTED FLYAGONAL BACKTEST FAILED")
        print(f"   Need to debug strategy implementation")
    
    print(f"\n🔍 NEXT STEPS:")
    print(f"   1. Analyze these REAL corrected Flyagonal results")
    print(f"   2. Compare to Steve Guns benchmarks")
    print(f"   3. Optimize parameters if needed")
    print(f"   4. Extend backtest period if successful")
