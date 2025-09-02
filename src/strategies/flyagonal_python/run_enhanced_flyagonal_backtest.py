#!/usr/bin/env python3
"""
🦋 ENHANCED FLYAGONAL BACKTEST RUNNER
====================================
Run backtest with enhanced Flyagonal strategy featuring:
1. Real Black-Scholes P&L calculation
2. Proper 4.5-day hold period management
3. Dynamic exit conditions
4. Comprehensive position tracking

This addresses the issues found in the previous backtest:
- No more immediate exits
- Real P&L instead of random simulation
- Proper hold periods matching Steve Guns methodology

Following @.cursorrules:
- Uses real market pricing
- Professional position management
- Comprehensive performance analysis

Location: src/strategies/flyagonal_python/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Enhanced Flyagonal Backtest
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

def create_enhanced_flyagonal_backtester():
    """Create enhanced backtester with real P&L and position management"""
    
    try:
        from enhanced_flyagonal_strategy import EnhancedFlyagonalStrategy, EnhancedFlyagonalPosition
        from src.data.parquet_data_loader import ParquetDataLoader
        
        class EnhancedFlyagonalBacktester:
            """Enhanced backtester with real P&L calculation and position management"""
            
            def __init__(self, initial_balance: float = 25000):
                self.initial_balance = initial_balance
                self.current_balance = initial_balance
                
                # Initialize data loader
                data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
                self.data_loader = ParquetDataLoader(parquet_path=data_path)
                
                # Initialize enhanced strategy
                self.flyagonal_strategy = EnhancedFlyagonalStrategy(initial_balance)
                
                # Enhanced tracking
                self.daily_results = []
                self.trade_log = []
                self.position_tracking = []
                
                print("🦋 ENHANCED FLYAGONAL BACKTESTER INITIALIZED")
                print(f"   Strategy: Enhanced with Real P&L & Position Management")
                print(f"   Initial Balance: ${initial_balance:,.2f}")
                print(f"   Target Hold: 4.5 days (Steve Guns)")
                print(f"   Min Hold: 1 day (no same-day exits)")
                print(f"   ✅ Real Black-Scholes P&L")
                print(f"   ✅ Dynamic Exit Conditions")
            
            def run_backtest(self, start_date: str = "2023-09-01", end_date: str = "2023-09-30") -> dict:
                """Run enhanced Flyagonal backtest with real P&L tracking"""
                
                print(f"\n🦋 STARTING ENHANCED FLYAGONAL BACKTEST")
                print(f"   Period: {start_date} to {end_date}")
                print(f"   Strategy: Enhanced with Real P&L")
                print("="*65)
                
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
                    
                    # Process each trading day
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
                            
                            # Update existing positions with real P&L
                            for position in self.flyagonal_strategy.open_positions:
                                self.flyagonal_strategy.update_position_pnl(
                                    position, options_data, spy_price, trading_day_dt
                                )
                                
                                print(f"   📊 {position.position_id}: Days {position.days_held:.1f} | P&L ${position.unrealized_pnl:.2f}")
                            
                            # Check for new entries
                            position = self.flyagonal_strategy.execute_enhanced_flyagonal_entry(
                                options_data, spy_price, trading_day_dt
                            )
                            
                            if position:
                                print(f"   📈 NEW POSITION: {position.position_id}")
                                
                                # Log entry
                                self.trade_log.append({
                                    'date': trading_day,
                                    'action': 'ENTRY',
                                    'position_id': position.position_id,
                                    'spy_price': spy_price,
                                    'net_vega': position.net_vega,
                                    'max_profit': position.max_profit_potential,
                                    'max_loss': position.max_loss_potential,
                                    'profit_target': position.profit_target,
                                    'stop_loss': position.stop_loss
                                })
                            
                            # Check for exits using enhanced conditions
                            positions_to_close = []
                            for position in list(self.flyagonal_strategy.open_positions):
                                should_close, exit_reason = self.flyagonal_strategy.should_close_position_enhanced(
                                    position, trading_day_dt
                                )
                                
                                if should_close:
                                    positions_to_close.append((position, exit_reason))
                            
                            # Close positions
                            for position, exit_reason in positions_to_close:
                                final_pnl = self.flyagonal_strategy.close_enhanced_position(
                                    position, trading_day_dt, exit_reason
                                )
                                
                                print(f"   🔚 POSITION CLOSED: {position.position_id}")
                                print(f"      Reason: {exit_reason}")
                                print(f"      Days Held: {position.days_held:.1f}")
                                print(f"      Final P&L: ${final_pnl:.2f}")
                                
                                # Update balance
                                self.current_balance = self.flyagonal_strategy.current_balance
                                
                                # Log exit
                                self.trade_log.append({
                                    'date': trading_day,
                                    'action': 'EXIT',
                                    'position_id': position.position_id,
                                    'exit_reason': exit_reason,
                                    'days_held': position.days_held,
                                    'realized_pnl': final_pnl,
                                    'max_profit_seen': position.max_unrealized_profit,
                                    'max_loss_seen': position.max_unrealized_loss,
                                    'balance': self.current_balance
                                })
                            
                            # Store daily result
                            daily_pnl = self.current_balance - self.initial_balance
                            open_positions_pnl = sum(pos.unrealized_pnl for pos in self.flyagonal_strategy.open_positions)
                            
                            self.daily_results.append({
                                'date': trading_day,
                                'balance': self.current_balance,
                                'daily_pnl': daily_pnl,
                                'open_positions': len(self.flyagonal_strategy.open_positions),
                                'open_positions_pnl': open_positions_pnl,
                                'total_trades': self.flyagonal_strategy.total_trades,
                                'spy_price': spy_price
                            })
                            
                            # Track position details
                            for position in self.flyagonal_strategy.open_positions:
                                self.position_tracking.append({
                                    'date': trading_day,
                                    'position_id': position.position_id,
                                    'days_held': position.days_held,
                                    'unrealized_pnl': position.unrealized_pnl,
                                    'spy_price': spy_price,
                                    'target_exit_date': position.target_exit_date.strftime('%Y-%m-%d')
                                })
                            
                        except Exception as e:
                            print(f"   ❌ Error processing {trading_day}: {e}")
                            continue
                    
                    # Force close remaining positions at end
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    for position in list(self.flyagonal_strategy.open_positions):
                        # Update final P&L
                        if hasattr(position, 'unrealized_pnl'):
                            final_pnl = self.flyagonal_strategy.close_enhanced_position(
                                position, end_dt, "BACKTEST_END"
                            )
                        else:
                            final_pnl = 0  # Fallback
                        
                        self.current_balance = self.flyagonal_strategy.current_balance
                    
                    # Generate comprehensive results
                    return self._generate_enhanced_results(start_date, end_date)
                    
                except Exception as e:
                    print(f"❌ Enhanced backtest error: {e}")
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
            
            def _generate_enhanced_results(self, start_date: str, end_date: str) -> dict:
                """Generate comprehensive enhanced results"""
                
                strategy_stats = self.flyagonal_strategy.get_enhanced_strategy_statistics()
                
                total_pnl = self.current_balance - self.initial_balance
                total_return = (total_pnl / self.initial_balance) * 100
                
                winning_trades = self.flyagonal_strategy.winning_trades
                total_trades = self.flyagonal_strategy.total_trades
                win_rate = (winning_trades / max(total_trades, 1)) * 100
                
                # Enhanced statistics
                if self.flyagonal_strategy.closed_positions:
                    avg_hold_days = sum(pos.days_held for pos in self.flyagonal_strategy.closed_positions) / len(self.flyagonal_strategy.closed_positions)
                    
                    # Profit/Loss analysis
                    winners = [pos for pos in self.flyagonal_strategy.closed_positions if pos.realized_pnl > 0]
                    losers = [pos for pos in self.flyagonal_strategy.closed_positions if pos.realized_pnl <= 0]
                    
                    avg_winner = sum(pos.realized_pnl for pos in winners) / max(len(winners), 1)
                    avg_loser = sum(pos.realized_pnl for pos in losers) / max(len(losers), 1)
                    
                    # Hold period analysis
                    hold_periods = [pos.days_held for pos in self.flyagonal_strategy.closed_positions]
                    min_hold = min(hold_periods) if hold_periods else 0
                    max_hold = max(hold_periods) if hold_periods else 0
                    
                else:
                    avg_hold_days = 0
                    avg_winner = 0
                    avg_loser = 0
                    min_hold = 0
                    max_hold = 0
                
                if total_trades > 0:
                    avg_gain_per_trade = total_pnl / total_trades
                    avg_gain_pct = (avg_gain_per_trade / self.initial_balance) * 100
                else:
                    avg_gain_per_trade = 0
                    avg_gain_pct = 0
                
                results = {
                    'backtest_period': f"{start_date} to {end_date}",
                    'strategy': 'Enhanced Flyagonal (Real P&L + Position Management)',
                    'initial_balance': self.initial_balance,
                    'final_balance': self.current_balance,
                    'total_pnl': total_pnl,
                    'total_return_pct': total_return,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': total_trades - winning_trades,
                    'win_rate': win_rate,
                    'avg_hold_days': avg_hold_days,
                    'min_hold_days': min_hold,
                    'max_hold_days': max_hold,
                    'avg_gain_per_trade': avg_gain_per_trade,
                    'avg_gain_pct': avg_gain_pct,
                    'avg_winner': avg_winner,
                    'avg_loser': avg_loser,
                    'profit_factor': abs(avg_winner / avg_loser) if avg_loser != 0 else 0,
                    'daily_results': self.daily_results,
                    'trade_log': self.trade_log,
                    'position_tracking': self.position_tracking,
                    'strategy_stats': strategy_stats,
                    'enhancement_comparison': {
                        'steve_guns_target_hold': 4.5,
                        'actual_avg_hold': avg_hold_days,
                        'steve_guns_target_win_rate': 96.0,
                        'actual_win_rate': win_rate,
                        'enhancement_features': [
                            'Real Black-Scholes P&L calculation',
                            'Proper hold period management (1-8 days)',
                            'Dynamic exit conditions',
                            'Enhanced position tracking',
                            'Market-based profit/loss targets'
                        ],
                        'performance_assessment': self._assess_enhanced_performance(win_rate, total_return, total_trades, avg_hold_days)
                    }
                }
                
                self._display_enhanced_results(results)
                return results
            
            def _assess_enhanced_performance(self, win_rate: float, total_return: float, total_trades: int, avg_hold_days: float) -> str:
                """Assess enhanced strategy performance"""
                
                if total_trades == 0:
                    return "NO_TRADES_EXECUTED"
                
                # Check if hold period is reasonable (1-8 days)
                hold_period_ok = 1.0 <= avg_hold_days <= 8.0
                
                # Performance tiers
                if win_rate >= 80 and total_return > 10 and hold_period_ok:
                    return "EXCELLENT"
                elif win_rate >= 70 and total_return > 5 and hold_period_ok:
                    return "VERY_GOOD"
                elif win_rate >= 60 and total_return > 2 and hold_period_ok:
                    return "GOOD"
                elif win_rate >= 50 and total_return > 0:
                    return "ACCEPTABLE"
                elif total_trades >= 3:  # At least some trades executed
                    return "NEEDS_OPTIMIZATION"
                else:
                    return "INSUFFICIENT_DATA"
            
            def _display_enhanced_results(self, results: dict):
                """Display comprehensive enhanced results"""
                
                print(f"\n🎯 ENHANCED FLYAGONAL BACKTEST COMPLETE")
                print("="*65)
                print(f"Strategy: {results['strategy']}")
                print(f"Period: {results['backtest_period']}")
                print(f"")
                
                print(f"💰 FINANCIAL PERFORMANCE:")
                print(f"   Initial Balance: ${results['initial_balance']:,.2f}")
                print(f"   Final Balance: ${results['final_balance']:,.2f}")
                print(f"   Total P&L: ${results['total_pnl']:,.2f}")
                print(f"   Total Return: {results['total_return_pct']:.2f}%")
                print(f"")
                
                print(f"📈 ENHANCED TRADING STATISTICS:")
                print(f"   Total Trades: {results['total_trades']}")
                print(f"   Winning Trades: {results['winning_trades']}")
                print(f"   Losing Trades: {results['losing_trades']}")
                print(f"   Win Rate: {results['win_rate']:.1f}%")
                print(f"   Average Hold: {results['avg_hold_days']:.1f} days")
                print(f"   Hold Range: {results['min_hold_days']:.1f} - {results['max_hold_days']:.1f} days")
                print(f"   Avg Gain/Trade: ${results['avg_gain_per_trade']:.2f} ({results['avg_gain_pct']:.2f}%)")
                print(f"")
                
                print(f"🔍 PROFIT/LOSS ANALYSIS:")
                print(f"   Average Winner: ${results['avg_winner']:.2f}")
                print(f"   Average Loser: ${results['avg_loser']:.2f}")
                print(f"   Profit Factor: {results['profit_factor']:.2f}")
                print(f"")
                
                # Enhancement comparison
                comparison = results['enhancement_comparison']
                print(f"🦋 STEVE GUNS METHODOLOGY COMPARISON:")
                print(f"   Target Hold: {comparison['steve_guns_target_hold']:.1f} days | Actual: {comparison['actual_avg_hold']:.1f} days")
                print(f"   Target Win Rate: {comparison['steve_guns_target_win_rate']:.0f}% | Actual: {comparison['actual_win_rate']:.1f}%")
                print(f"")
                
                print(f"⚡ ENHANCEMENT FEATURES:")
                for feature in comparison['enhancement_features']:
                    print(f"   ✅ {feature}")
                print(f"")
                
                # Performance assessment
                assessment = comparison['performance_assessment']
                if assessment == "NO_TRADES_EXECUTED":
                    print(f"⚠️  ASSESSMENT: NO TRADES EXECUTED")
                    print(f"   Strategy needs further optimization")
                elif assessment in ["EXCELLENT", "VERY_GOOD"]:
                    print(f"✅ ASSESSMENT: {assessment}")
                    print(f"   Enhanced strategy performing well!")
                elif assessment in ["GOOD", "ACCEPTABLE"]:
                    print(f"⚡ ASSESSMENT: {assessment}")
                    print(f"   Enhanced strategy shows promise")
                else:
                    print(f"❌ ASSESSMENT: {assessment}")
                    print(f"   Enhanced strategy needs more work")
        
        return EnhancedFlyagonalBacktester
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None

def run_enhanced_flyagonal_backtest():
    """Run the enhanced Flyagonal backtest"""
    
    print("🦋 ENHANCED FLYAGONAL STRATEGY BACKTEST")
    print("="*65)
    print("🚀 ENHANCEMENTS APPLIED:")
    print("   ✅ Real Black-Scholes P&L calculation")
    print("   ✅ Proper hold period management (1-8 days)")
    print("   ✅ Dynamic exit conditions")
    print("   ✅ Enhanced position tracking")
    print("   ✅ Market-based profit/loss targets")
    print("   ✅ No more same-day exits")
    print("="*65)
    
    # Create enhanced backtester
    BacktesterClass = create_enhanced_flyagonal_backtester()
    if not BacktesterClass:
        print("❌ Could not create enhanced backtester")
        return None
    
    # Initialize and run
    backtester = BacktesterClass(initial_balance=25000)
    
    # Run enhanced backtest (3 weeks for better data)
    results = backtester.run_backtest(
        start_date="2023-09-01",
        end_date="2023-09-22"  # 3 weeks
    )
    
    if 'error' in results:
        print(f"❌ Enhanced backtest failed: {results['error']}")
        return None
    
    # Show detailed trade analysis
    if results['trade_log']:
        print(f"\n📋 DETAILED TRADE ANALYSIS:")
        entries = [t for t in results['trade_log'] if t['action'] == 'ENTRY']
        exits = [t for t in results['trade_log'] if t['action'] == 'EXIT']
        
        print(f"   Entries: {len(entries)}")
        print(f"   Exits: {len(exits)}")
        
        if exits:
            print(f"\n   Recent Exits:")
            for exit_trade in exits[-3:]:  # Last 3 exits
                print(f"   🔚 {exit_trade['date']}: {exit_trade['position_id']}")
                print(f"      Reason: {exit_trade['exit_reason']}")
                print(f"      Days: {exit_trade['days_held']:.1f} | P&L: ${exit_trade['realized_pnl']:.2f}")
                print(f"      Max Profit Seen: ${exit_trade['max_profit_seen']:.2f}")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting ENHANCED Flyagonal Backtest...")
    print("(Real P&L + Position Management + Proper Hold Periods)")
    print()
    
    results = run_enhanced_flyagonal_backtest()
    
    if results and 'error' not in results:
        print(f"\n✅ ENHANCED FLYAGONAL BACKTEST COMPLETE")
        print(f"   Strategy: Enhanced with Real P&L")
        print(f"   Return: {results['total_return_pct']:.2f}%")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Avg Hold: {results['avg_hold_days']:.1f} days")
        print(f"   Assessment: {results['enhancement_comparison']['performance_assessment']}")
        
        # Success criteria
        if results['total_trades'] > 0 and results['avg_hold_days'] > 1:
            print(f"   🎯 SUCCESS: Real P&L + Proper Hold Periods!")
        else:
            print(f"   ⚠️  Still needs optimization")
            
    else:
        print(f"\n❌ ENHANCED FLYAGONAL BACKTEST FAILED")
    
    print(f"\n🔍 NEXT STEPS:")
    if results and results.get('total_trades', 0) > 0:
        if results.get('avg_hold_days', 0) > 1:
            print(f"   1. ✅ Enhanced strategy working properly!")
            print(f"   2. Extend backtest to longer period")
            print(f"   3. Compare to Iron Condor performance")
            print(f"   4. Consider parameter optimization")
        else:
            print(f"   1. Hold periods still too short")
            print(f"   2. Review exit condition logic")
    else:
        print(f"   1. Strategy still not executing trades")
        print(f"   2. Further debugging needed")
