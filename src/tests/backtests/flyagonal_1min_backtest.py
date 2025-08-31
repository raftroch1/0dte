#!/usr/bin/env python3
"""
🎯 Flyagonal Strategy 1-Minute Precision Backtest
===============================================

High-precision backtesting using 1-minute real data from:
- Polygon.io: 1-minute SPY and options bars
- Alpaca: 1-minute SPY bars (validation)
- Real VIX data for volatility analysis

Features:
- Minute-by-minute strategy execution
- Precise entry/exit timing for 0DTE options
- Real market microstructure analysis
- Detailed trade logging with timestamps

Author: Advanced Options Trading System
Version: 1.0.0
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import json
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class DataLoader:
    """Loads cached 1-minute and daily data"""
    
    def __init__(self):
        self.daily_data_dir = "cached_data"
        self.intraday_data_dir = "intraday_data"
        
    def load_spy_1min_data(self, date: datetime) -> pd.DataFrame:
        """Load SPY 1-minute data for a specific date"""
        try:
            date_str = date.strftime('%Y%m%d')
            file_path = f"{self.intraday_data_dir}/spy_1min_{date_str}.csv"
            
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                print(f"✅ Loaded {len(df)} SPY 1-minute bars for {date.strftime('%Y-%m-%d')}")
                return df
            else:
                print(f"❌ No SPY 1-minute data found for {date.strftime('%Y-%m-%d')}")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading SPY 1-minute data: {e}")
            return pd.DataFrame()
    
    def load_options_1min_data(self, date: datetime) -> Dict[str, pd.DataFrame]:
        """Load all available options 1-minute data for a specific date"""
        try:
            date_str = date.strftime('%Y%m%d')
            options_data = {}
            
            # Find all options files for this date
            import glob
            pattern = f"{self.intraday_data_dir}/O_SPY*_1min_{date_str}.csv"
            option_files = glob.glob(pattern)
            
            for file_path in option_files:
                # Extract option ticker from filename
                filename = os.path.basename(file_path)
                option_ticker = filename.replace(f'_1min_{date_str}.csv', '').replace('_', ':')
                
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                
                options_data[option_ticker] = df
            
            print(f"✅ Loaded {len(options_data)} options 1-minute datasets for {date.strftime('%Y-%m-%d')}")
            return options_data
        except Exception as e:
            print(f"❌ Error loading options 1-minute data: {e}")
            return {}
    
    def load_vix_data(self) -> pd.DataFrame:
        """Load cached VIX data"""
        try:
            vix_files = [f for f in os.listdir(self.daily_data_dir) if f.startswith('vix_data_')]
            if vix_files:
                file_path = f"{self.daily_data_dir}/{vix_files[0]}"
                df = pd.read_csv(file_path)
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                print(f"✅ Loaded {len(df)} VIX daily bars")
                return df
            else:
                print(f"❌ No VIX data found")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading VIX data: {e}")
            return pd.DataFrame()

class FlyagonalStrategy:
    """Flyagonal trading strategy with 1-minute precision"""
    
    def __init__(self):
        self.name = "Flyagonal"
        self.version = "1.0.0 (1-min precision)"
        
        # Strategy parameters
        self.min_vix = 12.0  # Minimum VIX for entry
        self.max_vix = 35.0  # Maximum VIX for entry
        self.min_dte = 0     # 0DTE focus
        self.max_dte = 2     # Up to 2 DTE
        
        # Entry timing (market hours)
        self.entry_start_time = time(9, 30)   # 9:30 AM ET
        self.entry_end_time = time(15, 0)     # 3:00 PM ET
        self.exit_time = time(15, 45)         # 3:45 PM ET (before close)
        
        # Risk management
        self.max_loss_percent = 0.50          # 50% max loss
        self.profit_target_percent = 0.30     # 30% profit target
        
    def is_market_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is during market hours"""
        market_time = timestamp.time()
        return self.entry_start_time <= market_time <= time(16, 0)  # 9:30 AM - 4:00 PM ET
    
    def is_entry_window(self, timestamp: datetime) -> bool:
        """Check if timestamp is during entry window"""
        market_time = timestamp.time()
        return self.entry_start_time <= market_time <= self.entry_end_time
    
    def is_exit_time(self, timestamp: datetime) -> bool:
        """Check if it's time to exit positions"""
        market_time = timestamp.time()
        return market_time >= self.exit_time
    
    def analyze_market_conditions(self, spy_price: float, vix_level: float, timestamp: datetime) -> Dict:
        """Analyze market conditions for strategy entry"""
        
        # VIX analysis
        if vix_level < self.min_vix:
            vix_condition = "TOO_LOW"
        elif vix_level > self.max_vix:
            vix_condition = "TOO_HIGH"
        else:
            vix_condition = "OPTIMAL"
        
        # Time analysis
        time_condition = "ENTRY_WINDOW" if self.is_entry_window(timestamp) else "OUTSIDE_WINDOW"
        
        # Overall suitability
        entry_suitable = (
            vix_condition == "OPTIMAL" and
            time_condition == "ENTRY_WINDOW"
        )
        
        return {
            'spy_price': spy_price,
            'vix_level': vix_level,
            'vix_condition': vix_condition,
            'time_condition': time_condition,
            'entry_suitable': entry_suitable,
            'timestamp': timestamp
        }
    
    def find_flyagonal_options(self, spy_price: float, options_data: Dict[str, pd.DataFrame], timestamp: datetime) -> Optional[Dict]:
        """Find suitable options for Flyagonal structure"""
        
        # Calculate ATM strike (round to nearest $5)
        atm_strike = round(spy_price / 5) * 5
        
        # Define Flyagonal structure strikes
        required_strikes = {
            'call_short_1': atm_strike + 10,   # Short call 1
            'call_short_2': atm_strike + 20,   # Short call 2  
            'call_long': atm_strike + 30,      # Long call (broken wing)
            'put_short': atm_strike - 10,      # Short put
            'put_long': atm_strike - 20        # Long put
        }
        
        # Find matching options with data at this timestamp
        available_options = {}
        
        for option_ticker, option_df in options_data.items():
            if timestamp not in option_df.index:
                continue
                
            # Parse option ticker to get strike and type
            # Format: O:SPY250902C00630000 (strike 630, call)
            try:
                # Handle both formats: O:SPY250902C00630000 and O_SPY250902C00630000
                clean_ticker = option_ticker.replace('_', ':')
                
                if 'C' in clean_ticker:
                    parts = clean_ticker.split('C')
                    option_type = 'CALL'
                elif 'P' in clean_ticker:
                    parts = clean_ticker.split('P')
                    option_type = 'PUT'
                else:
                    continue
                
                if len(parts) != 2:
                    continue
                    
                strike_str = parts[1]
                strike = float(strike_str) / 1000  # Convert from 630000 to 630
                
                # Check if this strike matches our requirements
                for leg_name, required_strike in required_strikes.items():
                    if abs(strike - required_strike) < 0.01:  # Match within $0.01
                        expected_type = 'CALL' if 'call' in leg_name else 'PUT'
                        if option_type == expected_type:
                            option_price = option_df.loc[timestamp, 'close']
                            available_options[leg_name] = {
                                'ticker': option_ticker,
                                'strike': strike,
                                'type': option_type,
                                'price': option_price,
                                'data': option_df.loc[timestamp]
                            }
                            print(f"   ✅ Found {leg_name}: {clean_ticker} (${strike}, ${option_price:.2f})")
                            break
                            
            except Exception as e:
                print(f"   ⚠️ Error parsing {option_ticker}: {e}")
                continue
        
        # Check if we have all required legs
        if len(available_options) == len(required_strikes):
            print(f"   🎯 Complete Flyagonal structure found!")
            return {
                'structure': 'flyagonal',
                'atm_strike': atm_strike,
                'legs': available_options,
                'timestamp': timestamp,
                'spy_price': spy_price
            }
        else:
            missing_legs = set(required_strikes.keys()) - set(available_options.keys())
            if len(available_options) > 0:  # Only show if we found some legs
                print(f"   ⚠️ Partial match: Found {list(available_options.keys())}, Missing: {missing_legs}")
            return None
    
    def calculate_flyagonal_metrics(self, flyagonal_setup: Dict) -> Dict:
        """Calculate risk/reward metrics for Flyagonal setup"""
        
        legs = flyagonal_setup['legs']
        
        # Calculate net premium (credit received)
        net_premium = 0
        
        # Broken Wing Butterfly (Calls)
        net_premium += legs['call_short_1']['price']  # Sell call 1
        net_premium += legs['call_short_2']['price']  # Sell call 2
        net_premium -= legs['call_long']['price'] * 2  # Buy 2 long calls
        
        # Put Diagonal Spread
        net_premium += legs['put_short']['price']   # Sell put
        net_premium -= legs['put_long']['price']    # Buy put
        
        # Calculate max profit/loss
        atm_strike = flyagonal_setup['atm_strike']
        
        # Simplified P&L calculation
        max_profit = abs(net_premium) * 0.3  # Estimate 30% of premium
        max_loss = abs(net_premium) * 2.0    # Estimate 200% of premium
        
        return {
            'net_premium': net_premium,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'profit_target': abs(net_premium) * self.profit_target_percent,
            'loss_limit': abs(net_premium) * self.max_loss_percent
        }

class HighPrecisionBacktester:
    """1-minute precision backtesting engine"""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.strategy = FlyagonalStrategy()
        
        # Backtest state
        self.initial_capital = 35000
        self.current_capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.minute_by_minute_pnl = []
        
    def run_1min_backtest(self, test_date: datetime):
        """Run 1-minute precision backtest for a single day"""
        
        print(f"\n🚀 FLYAGONAL 1-MINUTE PRECISION BACKTEST")
        print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"💰 Initial Capital: ${self.initial_capital:,}")
        print(f"🎯 Strategy: {self.strategy.name} {self.strategy.version}")
        print(f"=" * 70)
        
        # Load data
        spy_1min = self.data_loader.load_spy_1min_data(test_date)
        options_1min = self.data_loader.load_options_1min_data(test_date)
        vix_daily = self.data_loader.load_vix_data()
        
        if spy_1min.empty:
            print(f"❌ No SPY data available for {test_date.strftime('%Y-%m-%d')}")
            return
        
        if not options_1min:
            print(f"❌ No options data available for {test_date.strftime('%Y-%m-%d')}")
            return
        
        # Get VIX for this date
        test_date_only = test_date.date()
        if test_date_only in vix_daily.index.date:
            vix_level = vix_daily.loc[vix_daily.index.date == test_date_only, 'close'].iloc[0]
        else:
            vix_level = 20.0  # Default VIX
            print(f"⚠️ Using default VIX: {vix_level}")
        
        print(f"📊 VIX Level: {vix_level:.2f}")
        print(f"📊 SPY bars: {len(spy_1min)}")
        print(f"📊 Options contracts: {len(options_1min)}")
        
        # Process each minute
        position_opened = False
        entry_time = None
        entry_setup = None
        
        for timestamp, spy_row in spy_1min.iterrows():
            spy_price = spy_row['close']
            
            # Skip if not market hours
            if not self.strategy.is_market_hours(timestamp):
                continue
            
            # Market condition analysis
            market_analysis = self.strategy.analyze_market_conditions(spy_price, vix_level, timestamp)
            
            # Position management
            if not position_opened:
                # Look for entry opportunity
                if market_analysis['entry_suitable']:
                    flyagonal_setup = self.strategy.find_flyagonal_options(spy_price, options_1min, timestamp)
                    
                    if flyagonal_setup:
                        # Calculate metrics
                        metrics = self.strategy.calculate_flyagonal_metrics(flyagonal_setup)
                        
                        # Enter position
                        position_opened = True
                        entry_time = timestamp
                        entry_setup = flyagonal_setup
                        entry_metrics = metrics
                        
                        print(f"\n🎯 ENTRY SIGNAL: {timestamp.strftime('%H:%M:%S')}")
                        print(f"   📊 SPY: ${spy_price:.2f}")
                        print(f"   📊 ATM Strike: ${flyagonal_setup['atm_strike']}")
                        print(f"   💰 Net Premium: ${metrics['net_premium']:.2f}")
                        print(f"   🎯 Profit Target: ${metrics['profit_target']:.2f}")
                        print(f"   🛑 Loss Limit: ${metrics['loss_limit']:.2f}")
                        
                        # Log trade entry
                        trade_entry = {
                            'entry_time': timestamp,
                            'entry_spy_price': spy_price,
                            'entry_vix': vix_level,
                            'flyagonal_setup': flyagonal_setup,
                            'entry_metrics': metrics,
                            'status': 'OPEN'
                        }
                        
            else:
                # Manage open position
                if entry_setup and timestamp in spy_1min.index:
                    # Calculate current P&L
                    current_pnl = self.calculate_position_pnl(entry_setup, options_1min, timestamp, entry_metrics)
                    
                    # Check exit conditions
                    exit_reason = None
                    
                    # Profit target hit
                    if current_pnl >= entry_metrics['profit_target']:
                        exit_reason = "PROFIT_TARGET"
                    
                    # Loss limit hit
                    elif current_pnl <= -entry_metrics['loss_limit']:
                        exit_reason = "STOP_LOSS"
                    
                    # Time-based exit
                    elif self.strategy.is_exit_time(timestamp):
                        exit_reason = "TIME_EXIT"
                    
                    # Execute exit
                    if exit_reason:
                        print(f"\n🚪 EXIT SIGNAL: {timestamp.strftime('%H:%M:%S')} ({exit_reason})")
                        print(f"   📊 SPY: ${spy_price:.2f}")
                        print(f"   💰 P&L: ${current_pnl:.2f}")
                        
                        # Log completed trade
                        completed_trade = {
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'entry_spy_price': trade_entry['entry_spy_price'],
                            'exit_spy_price': spy_price,
                            'entry_vix': vix_level,
                            'duration_minutes': (timestamp - entry_time).total_seconds() / 60,
                            'pnl': current_pnl,
                            'exit_reason': exit_reason,
                            'flyagonal_setup': entry_setup,
                            'entry_metrics': entry_metrics
                        }
                        
                        self.trades.append(completed_trade)
                        self.current_capital += current_pnl
                        
                        # Reset for next opportunity
                        position_opened = False
                        entry_time = None
                        entry_setup = None
                        
            # Track minute-by-minute capital
            self.minute_by_minute_pnl.append({
                'timestamp': timestamp,
                'spy_price': spy_price,
                'capital': self.current_capital,
                'position_open': position_opened
            })
        
        # Generate results
        self.generate_results(test_date)
    
    def calculate_position_pnl(self, entry_setup: Dict, options_data: Dict, current_time: datetime, entry_metrics: Dict) -> float:
        """Calculate current P&L of open position"""
        try:
            current_pnl = 0
            
            for leg_name, leg_info in entry_setup['legs'].items():
                ticker = leg_info['ticker']
                entry_price = leg_info['price']
                
                if ticker in options_data and current_time in options_data[ticker].index:
                    current_price = options_data[ticker].loc[current_time, 'close']
                    
                    # Calculate P&L based on position direction
                    if 'short' in leg_name:
                        # Short position: profit when price decreases
                        leg_pnl = (entry_price - current_price) * 100  # $100 per contract
                    else:
                        # Long position: profit when price increases
                        leg_pnl = (current_price - entry_price) * 100
                    
                    # Handle multiple contracts (broken wing has 2 long calls)
                    if leg_name == 'call_long':
                        leg_pnl *= 2  # 2 contracts
                    
                    current_pnl += leg_pnl
            
            return current_pnl
            
        except Exception as e:
            print(f"⚠️ Error calculating P&L: {e}")
            return 0
    
    def generate_results(self, test_date: datetime):
        """Generate detailed backtest results"""
        
        print(f"\n" + "=" * 70)
        print(f"📊 FLYAGONAL 1-MINUTE BACKTEST RESULTS")
        print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"=" * 70)
        
        if not self.trades:
            print(f"❌ No trades executed")
            return
        
        # Calculate metrics
        total_pnl = sum(trade['pnl'] for trade in self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        avg_duration = np.mean([t['duration_minutes'] for t in self.trades])
        
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        
        print(f"💰 Total P&L: ${total_pnl:,.2f}")
        print(f"📈 Total Return: {total_return:.2f}%")
        print(f"📊 Total Trades: {len(self.trades)}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print(f"🏆 Average Win: ${avg_win:.2f}")
        print(f"💸 Average Loss: ${avg_loss:.2f}")
        print(f"⏱️ Average Duration: {avg_duration:.1f} minutes")
        print(f"💵 Final Capital: ${self.current_capital:,.2f}")
        
        # Detailed trade log
        print(f"\n📋 DETAILED TRADE LOG:")
        print(f"=" * 70)
        
        for i, trade in enumerate(self.trades, 1):
            entry_time = trade['entry_time'].strftime('%H:%M:%S')
            exit_time = trade['exit_time'].strftime('%H:%M:%S')
            duration = trade['duration_minutes']
            pnl = trade['pnl']
            reason = trade['exit_reason']
            
            status_emoji = "🟢" if pnl > 0 else "🔴"
            
            print(f"{status_emoji} Trade {i}: {entry_time} → {exit_time} ({duration:.0f}min)")
            print(f"   P&L: ${pnl:.2f} | Exit: {reason}")
            print(f"   SPY: ${trade['entry_spy_price']:.2f} → ${trade['exit_spy_price']:.2f}")
        
        # Save results
        results_file = f"flyagonal_1min_backtest_{test_date.strftime('%Y%m%d')}.json"
        
        # Prepare serializable data
        serializable_trades = []
        for trade in self.trades:
            trade_copy = trade.copy()
            trade_copy['entry_time'] = trade_copy['entry_time'].isoformat()
            trade_copy['exit_time'] = trade_copy['exit_time'].isoformat()
            serializable_trades.append(trade_copy)
        
        results_data = {
            'test_date': test_date.strftime('%Y-%m-%d'),
            'strategy': f"{self.strategy.name} {self.strategy.version}",
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_pnl': total_pnl,
            'total_return_percent': total_return,
            'total_trades': len(self.trades),
            'win_rate_percent': win_rate,
            'average_win': avg_win,
            'average_loss': avg_loss,
            'average_duration_minutes': avg_duration,
            'trades': serializable_trades
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")

def main():
    """Main execution function"""
    print("🎯 FLYAGONAL 1-MINUTE PRECISION BACKTEST")
    print("=" * 70)
    
    # Initialize backtest
    backtest = HighPrecisionBacktester()
    
    # Use the date we have 1-minute data for
    test_date = datetime(2025, 8, 29)
    
    try:
        # Run backtest
        backtest.run_1min_backtest(test_date)
        
    except KeyboardInterrupt:
        print("\n⚠️ Backtest interrupted by user")
    except Exception as e:
        print(f"❌ Backtest error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
