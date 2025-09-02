#!/usr/bin/env python3
"""
1-Month Optimized Router Backtest
=================================

Comprehensive 1-month backtest of the Optimized Adaptive Router with Credit Spread Optimizer.
Tests the integrated system over a full month to validate performance claims.

Following @.cursorrules testing patterns.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import logging
import csv

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.strategies.adaptive_zero_dte.optimized_adaptive_router import OptimizedAdaptiveRouter
from src.data.parquet_data_loader import ParquetDataLoader

class OptimizedRouterBacktester:
    """
    Comprehensive 1-month backtester for the Optimized Adaptive Router
    
    Tests:
    - Daily performance over 1 month
    - Win rate and P&L consistency
    - Risk management effectiveness
    - Kelly Criterion performance
    - Daily limit enforcement
    """
    
    def __init__(self):
        # Initialize components
        self.data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
        self.data_loader = ParquetDataLoader(parquet_path=self.data_path)
        
        # Results tracking
        self.daily_results = []
        self.all_trades = []
        self.performance_metrics = {}
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("📊 1-MONTH OPTIMIZED ROUTER BACKTESTER INITIALIZED")
    
    def run_1_month_backtest(
        self, 
        start_date: str = "2024-03-01", 
        end_date: str = "2024-03-31",
        account_balance: float = 25000
    ) -> Dict[str, Any]:
        """
        Run comprehensive 1-month backtest
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD) 
            account_balance: Starting account balance
            
        Returns:
            Comprehensive backtest results
        """
        
        self.logger.info(f"🚀 STARTING 1-MONTH BACKTEST: {start_date} to {end_date}")
        self.logger.info(f"💰 Starting Balance: ${account_balance:,.2f}")
        
        # Initialize router
        router = OptimizedAdaptiveRouter(account_balance)
        
        # Get trading dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        available_dates = self.data_loader.get_available_dates(start_dt, end_dt)
        
        if not available_dates:
            self.logger.error(f"❌ No trading data available for period {start_date} to {end_date}")
            return {'error': 'No data available'}
        
        self.logger.info(f"📅 Found {len(available_dates)} trading days")
        
        # Track overall performance
        total_starting_balance = account_balance
        current_balance = account_balance
        total_trades = 0
        winning_trades = 0
        total_pnl = 0.0
        
        # Daily tracking
        profitable_days = 0
        loss_days = 0
        max_daily_loss = 0.0
        max_daily_profit = 0.0
        
        # Run backtest day by day
        for i, trading_date in enumerate(available_dates):
            self.logger.info(f"\n📅 DAY {i+1}/{len(available_dates)}: {trading_date.strftime('%Y-%m-%d')}")
            
            # Run daily simulation
            daily_result = self._simulate_trading_day(router, trading_date, current_balance)
            
            if 'error' in daily_result:
                self.logger.warning(f"⚠️  Skipping {trading_date.strftime('%Y-%m-%d')}: {daily_result['error']}")
                continue
            
            # Update tracking
            daily_pnl = daily_result['daily_pnl']
            daily_trades_count = daily_result['trades_count']
            daily_wins = daily_result['winning_trades']
            
            current_balance += daily_pnl
            total_pnl += daily_pnl
            total_trades += daily_trades_count
            winning_trades += daily_wins
            
            # Daily performance tracking
            if daily_pnl > 0:
                profitable_days += 1
                max_daily_profit = max(max_daily_profit, daily_pnl)
            elif daily_pnl < 0:
                loss_days += 1
                max_daily_loss = min(max_daily_loss, daily_pnl)
            
            # Store daily result
            daily_summary = {
                'date': trading_date.strftime('%Y-%m-%d'),
                'daily_pnl': daily_pnl,
                'cumulative_pnl': total_pnl,
                'balance': current_balance,
                'trades_count': daily_trades_count,
                'winning_trades': daily_wins,
                'win_rate': (daily_wins / daily_trades_count * 100) if daily_trades_count > 0 else 0,
                'profit_target_hit': daily_result.get('profit_target_hit', False),
                'loss_limit_hit': daily_result.get('loss_limit_hit', False)
            }
            
            self.daily_results.append(daily_summary)
            
            # Add individual trades to master list
            if 'trades' in daily_result:
                for trade in daily_result['trades']:
                    trade['date'] = trading_date.strftime('%Y-%m-%d')
                    self.all_trades.append(trade)
            
            # Log daily summary
            self.logger.info(f"   Daily P&L: ${daily_pnl:+.2f}")
            self.logger.info(f"   Trades: {daily_trades_count} ({daily_wins} wins)")
            self.logger.info(f"   Balance: ${current_balance:,.2f}")
            
            # Check for major losses
            if daily_pnl < -500:
                self.logger.warning(f"   ⚠️  LARGE DAILY LOSS: ${daily_pnl:.2f}")
        
        # Calculate final metrics
        total_return = (current_balance / total_starting_balance - 1) * 100
        overall_win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_daily_pnl = total_pnl / len(available_dates) if available_dates else 0
        profitable_day_rate = (profitable_days / len(available_dates) * 100) if available_dates else 0
        
        # Compile comprehensive results
        results = {
            'period': f"{start_date} to {end_date}",
            'trading_days': len(available_dates),
            'starting_balance': total_starting_balance,
            'ending_balance': current_balance,
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'overall_win_rate': overall_win_rate,
            'avg_daily_pnl': avg_daily_pnl,
            'profitable_days': profitable_days,
            'loss_days': loss_days,
            'profitable_day_rate': profitable_day_rate,
            'max_daily_profit': max_daily_profit,
            'max_daily_loss': max_daily_loss,
            'daily_results': self.daily_results,
            'all_trades': self.all_trades
        }
        
        # Log final results
        self._log_final_results(results)
        
        # Export detailed results
        self._export_results(results)
        
        return results
    
    def _simulate_trading_day(
        self, 
        router: OptimizedAdaptiveRouter, 
        trading_date: datetime,
        current_balance: float
    ) -> Dict[str, Any]:
        """Simulate a full trading day"""
        
        try:
            # Load options data for the day
            options_data = self.data_loader.load_options_for_date(trading_date)
            if options_data.empty:
                return {'error': 'No options data'}
            
            # Estimate SPY price
            spy_price = self._estimate_spy_price(options_data)
            
            # Reset router for new day
            router.current_balance = current_balance
            router._check_daily_reset(trading_date)
            
            # Generate trading times (every 30 minutes during trading hours)
            trading_times = self._generate_trading_times(trading_date)
            
            daily_trades = []
            daily_pnl = 0.0
            winning_trades = 0
            
            for trading_time in trading_times:
                # Create market data
                market_data = {
                    'spy_price': spy_price + (trading_time.hour - 10) * 0.25,  # Simulate price movement
                    'timestamp': trading_time,
                    'spy_volume': 2000000  # Mock volume
                }
                
                # Get strategy recommendation
                strategy_rec = router.select_adaptive_strategy(
                    options_data, market_data, trading_time
                )
                
                # Execute trade if recommended
                if strategy_rec['strategy_type'] != 'NO_TRADE':
                    trade_result = router.execute_optimized_trade(
                        strategy_rec, options_data, market_data, trading_time
                    )
                    
                    if trade_result['executed']:
                        trade_pnl = trade_result['pnl']
                        daily_pnl += trade_pnl
                        
                        if trade_result.get('is_winner', False):
                            winning_trades += 1
                        
                        # Store trade details
                        daily_trades.append({
                            'time': trading_time.strftime('%H:%M'),
                            'strategy': trade_result['strategy_type'],
                            'contracts': trade_result['contracts'],
                            'pnl': trade_pnl,
                            'exit_reason': trade_result.get('exit_reason', 'UNKNOWN'),
                            'confidence': strategy_rec.get('confidence', 0)
                        })
                
                # Check if daily limits hit
                performance = router.get_performance_summary()
                if performance['profit_target_hit'] or performance['loss_limit_hit']:
                    break
            
            return {
                'daily_pnl': daily_pnl,
                'trades_count': len(daily_trades),
                'winning_trades': winning_trades,
                'trades': daily_trades,
                'profit_target_hit': router.daily_profit_target_hit,
                'loss_limit_hit': router.daily_loss_limit_hit
            }
            
        except Exception as e:
            return {'error': str(e)}
    
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
    
    def _log_final_results(self, results: Dict[str, Any]) -> None:
        """Log comprehensive final results"""
        
        self.logger.info(f"\n" + "="*80)
        self.logger.info(f"📊 1-MONTH BACKTEST RESULTS: {results['period']}")
        self.logger.info(f"="*80)
        
        self.logger.info(f"💰 FINANCIAL PERFORMANCE:")
        self.logger.info(f"   Starting Balance: ${results['starting_balance']:,.2f}")
        self.logger.info(f"   Ending Balance: ${results['ending_balance']:,.2f}")
        self.logger.info(f"   Total P&L: ${results['total_pnl']:+,.2f}")
        self.logger.info(f"   Total Return: {results['total_return_pct']:+.2f}%")
        self.logger.info(f"   Avg Daily P&L: ${results['avg_daily_pnl']:+.2f}")
        
        self.logger.info(f"\n📈 TRADING PERFORMANCE:")
        self.logger.info(f"   Total Trades: {results['total_trades']}")
        self.logger.info(f"   Winning Trades: {results['winning_trades']}")
        self.logger.info(f"   Overall Win Rate: {results['overall_win_rate']:.1f}%")
        self.logger.info(f"   Trading Days: {results['trading_days']}")
        
        self.logger.info(f"\n📅 DAILY PERFORMANCE:")
        self.logger.info(f"   Profitable Days: {results['profitable_days']}")
        self.logger.info(f"   Loss Days: {results['loss_days']}")
        self.logger.info(f"   Profitable Day Rate: {results['profitable_day_rate']:.1f}%")
        self.logger.info(f"   Max Daily Profit: ${results['max_daily_profit']:+.2f}")
        self.logger.info(f"   Max Daily Loss: ${results['max_daily_loss']:+.2f}")
        
        # Performance assessment
        target_daily_pnl = 200.0
        target_win_rate = 75.0
        
        self.logger.info(f"\n🎯 TARGET COMPARISON:")
        self.logger.info(f"   Target Daily P&L: ${target_daily_pnl:.2f}")
        self.logger.info(f"   Actual Daily P&L: ${results['avg_daily_pnl']:+.2f}")
        self.logger.info(f"   Target Win Rate: {target_win_rate:.1f}%")
        self.logger.info(f"   Actual Win Rate: {results['overall_win_rate']:.1f}%")
        
        # Overall assessment
        if results['avg_daily_pnl'] >= target_daily_pnl and results['overall_win_rate'] >= target_win_rate:
            self.logger.info(f"   ✅ TARGETS ACHIEVED!")
        else:
            self.logger.info(f"   ❌ TARGETS NOT MET - NEEDS OPTIMIZATION")
        
        self.logger.info(f"="*80)
    
    def _export_results(self, results: Dict[str, Any]) -> None:
        """Export detailed results to CSV files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export daily results
        daily_filename = f"optimized_router_daily_results_{timestamp}.csv"
        with open(daily_filename, 'w', newline='') as f:
            if results['daily_results']:
                writer = csv.DictWriter(f, fieldnames=results['daily_results'][0].keys())
                writer.writeheader()
                writer.writerows(results['daily_results'])
        
        # Export all trades
        trades_filename = f"optimized_router_all_trades_{timestamp}.csv"
        with open(trades_filename, 'w', newline='') as f:
            if results['all_trades']:
                writer = csv.DictWriter(f, fieldnames=results['all_trades'][0].keys())
                writer.writeheader()
                writer.writerows(results['all_trades'])
        
        # Export summary report
        summary_filename = f"optimized_router_summary_{timestamp}.txt"
        with open(summary_filename, 'w') as f:
            f.write("OPTIMIZED ADAPTIVE ROUTER - 1 MONTH BACKTEST SUMMARY\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Period: {results['period']}\n")
            f.write(f"Trading Days: {results['trading_days']}\n\n")
            
            f.write("FINANCIAL PERFORMANCE:\n")
            f.write(f"  Starting Balance: ${results['starting_balance']:,.2f}\n")
            f.write(f"  Ending Balance: ${results['ending_balance']:,.2f}\n")
            f.write(f"  Total P&L: ${results['total_pnl']:+,.2f}\n")
            f.write(f"  Total Return: {results['total_return_pct']:+.2f}%\n")
            f.write(f"  Avg Daily P&L: ${results['avg_daily_pnl']:+.2f}\n\n")
            
            f.write("TRADING PERFORMANCE:\n")
            f.write(f"  Total Trades: {results['total_trades']}\n")
            f.write(f"  Winning Trades: {results['winning_trades']}\n")
            f.write(f"  Overall Win Rate: {results['overall_win_rate']:.1f}%\n\n")
            
            f.write("DAILY PERFORMANCE:\n")
            f.write(f"  Profitable Days: {results['profitable_days']}\n")
            f.write(f"  Loss Days: {results['loss_days']}\n")
            f.write(f"  Profitable Day Rate: {results['profitable_day_rate']:.1f}%\n")
            f.write(f"  Max Daily Profit: ${results['max_daily_profit']:+.2f}\n")
            f.write(f"  Max Daily Loss: ${results['max_daily_loss']:+.2f}\n")
        
        self.logger.info(f"📁 RESULTS EXPORTED:")
        self.logger.info(f"   Daily Results: {daily_filename}")
        self.logger.info(f"   All Trades: {trades_filename}")
        self.logger.info(f"   Summary Report: {summary_filename}")

def main():
    """Run the 1-month backtest"""
    
    print("📊 OPTIMIZED ADAPTIVE ROUTER - 1 MONTH BACKTEST")
    print("="*70)
    
    backtester = OptimizedRouterBacktester()
    
    # Run March 2024 backtest (known to have good data)
    results = backtester.run_1_month_backtest(
        start_date="2024-03-01",
        end_date="2024-03-31",
        account_balance=25000.0
    )
    
    if 'error' not in results:
        print(f"\n🎯 BACKTEST COMPLETE!")
        print(f"   Total Return: {results['total_return_pct']:+.2f}%")
        print(f"   Win Rate: {results['overall_win_rate']:.1f}%")
        print(f"   Avg Daily P&L: ${results['avg_daily_pnl']:+.2f}")
        print(f"   Total Trades: {results['total_trades']}")
    else:
        print(f"❌ Backtest failed: {results['error']}")
    
    return results

if __name__ == "__main__":
    main()
