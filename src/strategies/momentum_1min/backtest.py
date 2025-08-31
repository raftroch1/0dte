#!/usr/bin/env python3
"""
🚀 Simple Momentum Strategy - 1-Minute Precision Backtest
======================================================

Adapts the existing SimpleMomentumStrategy.ts to use 1-minute real data
for high-precision 0DTE options trading backtesting.

Features:
- 1-minute RSI and momentum calculations
- Real options pricing from Polygon.io
- Time-window based strategy logic (Morning/Afternoon/Midday)
- VIX-aware position sizing
- Precise entry/exit timing

Author: Advanced Options Trading System
Version: 1.0.0
"""

import os
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
    
    def load_liquid_options_1min_data(self, date: datetime) -> Dict[str, pd.DataFrame]:
        """Load liquid options 1-minute data (ATM and near-ATM only)"""
        try:
            date_str = date.strftime('%Y%m%d')
            options_data = {}
            
            # Focus on liquid options only (based on our analysis)
            liquid_contracts = [
                'O_SPY250902C00655000_1min_20250829.csv',  # ATM+10 Call (196 bars)
                'O_SPY250902P00635000_1min_20250829.csv',  # ATM-10 Put (348 bars)  
                'O_SPY250902P00625000_1min_20250829.csv'   # ATM-20 Put (201 bars)
            ]
            
            for filename in liquid_contracts:
                filepath = f"{self.intraday_data_dir}/{filename}"
                if os.path.exists(filepath):
                    # Extract option ticker from filename
                    option_ticker = filename.replace(f'_1min_{date_str}.csv', '').replace('_', ':')
                    
                    df = pd.read_csv(filepath)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.set_index('timestamp')
                    
                    options_data[option_ticker] = df
            
            print(f"✅ Loaded {len(options_data)} liquid options datasets for {date.strftime('%Y-%m-%d')}")
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

class TechnicalIndicators:
    """Calculate technical indicators for 1-minute data"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_fast_rsi(prices: pd.Series, period: int = 5) -> pd.Series:
        """Calculate fast RSI for momentum detection"""
        return TechnicalIndicators.calculate_rsi(prices, period)
    
    @staticmethod
    def calculate_momentum(prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculate price momentum as percentage change"""
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100
    
    @staticmethod
    def calculate_price_velocity(prices: pd.Series, period: int = 3) -> pd.Series:
        """Calculate price velocity (rate of change)"""
        return prices.pct_change(period)
    
    @staticmethod
    def calculate_volume_ratio(volumes: pd.Series, period: int = 20) -> pd.Series:
        """Calculate volume ratio vs average"""
        avg_volume = volumes.rolling(window=period).mean()
        return volumes / avg_volume
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD and signal line"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower

class SimpleMomentumStrategy:
    """1-minute precision momentum strategy for 0DTE options"""
    
    def __init__(self):
        self.name = "Simple Momentum (1-min)"
        self.version = "1.0.0"
        
        # Strategy parameters (adjusted for real market conditions)
        self.rsi_oversold = 40  # Relaxed from 35
        self.rsi_overbought = 60  # Relaxed from 65
        self.momentum_threshold = 0.05  # Relaxed from 0.1
        self.velocity_threshold = 0.0005  # Relaxed from 0.001
        self.volume_threshold = 1.2  # Relaxed from 1.5
        
        # Time windows
        self.morning_start = time(9, 30)   # 9:30 AM ET
        self.morning_end = time(11, 0)     # 11:00 AM ET
        self.afternoon_start = time(14, 0) # 2:00 PM ET
        self.market_close = time(16, 0)    # 4:00 PM ET
        
        # Risk management
        self.max_loss_percent = 0.25      # 25% stop loss
        self.profit_target_percent = 0.40 # 40% profit target
        self.max_holding_minutes = 240    # 4 hours max
    
    def get_time_window(self, timestamp: datetime) -> str:
        """Determine current time window"""
        market_time = timestamp.time()
        
        if self.morning_start <= market_time <= self.morning_end:
            return "MORNING_MOMENTUM"
        elif self.afternoon_start <= market_time <= self.market_close:
            return "AFTERNOON_DECAY"
        else:
            return "MIDDAY_CONSOLIDATION"
    
    def calculate_indicators(self, spy_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for SPY data"""
        
        # Calculate indicators
        spy_data['rsi'] = TechnicalIndicators.calculate_rsi(spy_data['close'])
        spy_data['fast_rsi'] = TechnicalIndicators.calculate_fast_rsi(spy_data['close'], 5)
        spy_data['momentum'] = TechnicalIndicators.calculate_momentum(spy_data['close'])
        spy_data['price_velocity'] = TechnicalIndicators.calculate_price_velocity(spy_data['close'])
        spy_data['volume_ratio'] = TechnicalIndicators.calculate_volume_ratio(spy_data['volume'])
        
        # MACD
        macd, macd_signal = TechnicalIndicators.calculate_macd(spy_data['close'])
        spy_data['macd'] = macd
        spy_data['macd_signal'] = macd_signal
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.calculate_bollinger_bands(spy_data['close'])
        spy_data['bb_upper'] = bb_upper
        spy_data['bb_middle'] = bb_middle
        spy_data['bb_lower'] = bb_lower
        
        return spy_data
    
    def generate_signal(self, spy_data: pd.DataFrame, timestamp: datetime, vix_level: float) -> Optional[Dict]:
        """Generate momentum signal based on 1-minute data"""
        
        if timestamp not in spy_data.index:
            return None
        
        # Get current data
        current_data = spy_data.loc[timestamp]
        current_price = current_data['close']
        
        # Check if we have enough data for indicators
        if pd.isna(current_data['fast_rsi']) or pd.isna(current_data['momentum']):
            return None
        
        # Get time window
        time_window = self.get_time_window(timestamp)
        
        # Initialize signal
        confidence = 40  # Base confidence
        action = None
        reason = "Momentum: "
        
        # Extract indicators
        fast_rsi = current_data['fast_rsi']
        momentum = current_data['momentum']
        price_velocity = current_data['price_velocity']
        volume_ratio = current_data['volume_ratio']
        macd = current_data['macd']
        macd_signal = current_data['macd_signal']
        
        # VIX-based volatility filtering
        if vix_level > 40:
            confidence -= 10
            reason += f"High VIX ({vix_level:.1f}), "
        elif vix_level < 15:
            confidence -= 5
            reason += f"Low VIX ({vix_level:.1f}), "
        else:
            confidence += 5
            reason += f"Optimal VIX ({vix_level:.1f}), "
        
        # Time-based momentum logic (adjusted for real market conditions)
        if time_window == "MORNING_MOMENTUM":
            # Morning: Look for breakout momentum
            if fast_rsi < self.rsi_oversold and momentum > self.momentum_threshold and price_velocity > 0:
                action = "BUY_CALL"
                confidence += 25
                reason += "Morning oversold breakout, "
            elif fast_rsi > self.rsi_overbought and momentum < -self.momentum_threshold and price_velocity < 0:
                action = "BUY_PUT"
                confidence += 25
                reason += "Morning overbought breakdown, "
        
        elif time_window == "AFTERNOON_DECAY":
            # Afternoon: Look for mean reversion
            if fast_rsi > 65 and momentum > 0.08:  # Slightly relaxed
                action = "BUY_PUT"
                confidence += 20
                reason += "Afternoon overbought reversal, "
            elif fast_rsi < 35 and momentum < -0.08:  # Slightly relaxed
                action = "BUY_CALL"
                confidence += 20
                reason += "Afternoon oversold bounce, "
        
        else:  # MIDDAY_CONSOLIDATION
            # Midday: Conservative momentum only
            if fast_rsi < 30 and momentum > 0.08 and price_velocity > 0.005:  # Relaxed
                action = "BUY_CALL"
                confidence += 15
                reason += "Midday strong oversold, "
            elif fast_rsi > 70 and momentum < -0.08 and price_velocity < -0.005:  # Relaxed
                action = "BUY_PUT"
                confidence += 15
                reason += "Midday strong overbought, "
        
        # No clear signal
        if not action:
            return None
        
        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 15
            reason += f"High volume ({volume_ratio:.1f}x), "
        elif volume_ratio < 0.8:
            confidence -= 10
            reason += f"Low volume ({volume_ratio:.1f}x), "
        
        # MACD confirmation
        if macd > macd_signal and action == "BUY_CALL":
            confidence += 10
            reason += "MACD bullish, "
        elif macd < macd_signal and action == "BUY_PUT":
            confidence += 10
            reason += "MACD bearish, "
        
        # Bollinger Bands confirmation
        if action == "BUY_CALL" and current_price < current_data['bb_lower']:
            confidence += 12
            reason += "Below BB lower, "
        elif action == "BUY_PUT" and current_price > current_data['bb_upper']:
            confidence += 12
            reason += "Above BB upper, "
        
        # Minimum confidence threshold (relaxed for testing)
        if confidence < 50:
            return None
        
        reason = reason.rstrip(', ')
        
        return {
            'action': action,
            'confidence': min(95, confidence),
            'reason': reason,
            'timestamp': timestamp,
            'spy_price': current_price,
            'indicators': {
                'fast_rsi': fast_rsi,
                'momentum': momentum,
                'price_velocity': price_velocity,
                'volume_ratio': volume_ratio,
                'vix': vix_level
            }
        }

class MomentumBacktester:
    """1-minute precision backtesting for momentum strategy"""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.strategy = SimpleMomentumStrategy()
        
        # Backtest state
        self.initial_capital = 35000
        self.current_capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.minute_by_minute_pnl = []
    
    def find_best_option(self, action: str, spy_price: float, options_data: Dict[str, pd.DataFrame], timestamp: datetime) -> Optional[Dict]:
        """Find the best liquid option for the signal"""
        
        best_option = None
        
        for option_ticker, option_df in options_data.items():
            if timestamp not in option_df.index:
                continue
            
            # Parse option details - handle format O_SPY250902C00655000
            clean_ticker = option_ticker.replace('_', ':')
            
            try:
                if action == "BUY_CALL" and 'C' in clean_ticker:
                    # Look for calls - format O:SPY250902C00655000
                    # Find the 'C' and extract strike after it
                    c_index = clean_ticker.find('C')
                    if c_index != -1:
                        strike_str = clean_ticker[c_index+1:]  # Everything after 'C'
                        if strike_str.isdigit():
                            strike = float(strike_str) / 1000
                            # Accept any available call for now
                            option_price = option_df.loc[timestamp, 'close']
                            best_option = {
                                'ticker': option_ticker,
                                'strike': strike,
                                'type': 'CALL',
                                'price': option_price
                            }
                            break
                
                elif action == "BUY_PUT" and 'P' in clean_ticker:
                    # Look for puts - format O:SPY250902P00635000
                    # Find the 'P' and extract strike after it
                    p_index = clean_ticker.find('P')
                    if p_index != -1:
                        strike_str = clean_ticker[p_index+1:]  # Everything after 'P'
                        if strike_str.isdigit():
                            strike = float(strike_str) / 1000
                            # Accept any available put for now
                            option_price = option_df.loc[timestamp, 'close']
                            best_option = {
                                'ticker': option_ticker,
                                'strike': strike,
                                'type': 'PUT',
                                'price': option_price
                            }
                            break
            except Exception as e:
                print(f"   ⚠️ Error parsing option {option_ticker}: {e}")
                continue
        
        return best_option
    
    def run_momentum_backtest(self, test_date: datetime):
        """Run 1-minute momentum backtest"""
        
        print(f"\n🚀 SIMPLE MOMENTUM 1-MINUTE BACKTEST")
        print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"💰 Initial Capital: ${self.initial_capital:,}")
        print(f"🎯 Strategy: {self.strategy.name} {self.strategy.version}")
        print(f"=" * 70)
        
        # Load data
        spy_1min = self.data_loader.load_spy_1min_data(test_date)
        options_1min = self.data_loader.load_liquid_options_1min_data(test_date)
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
        
        print(f"📊 VIX Level: {vix_level:.2f}")
        print(f"📊 SPY bars: {len(spy_1min)}")
        print(f"📊 Liquid options: {len(options_1min)}")
        
        # Calculate indicators
        spy_with_indicators = self.strategy.calculate_indicators(spy_1min.copy())
        
        # Track positions
        position_opened = False
        entry_time = None
        entry_option = None
        entry_price = None
        entry_signal = None
        
        signal_count = 0
        
        # Process each minute during market hours
        for timestamp, spy_row in spy_with_indicators.iterrows():
            # Skip if not market hours (9:30 AM - 4:00 PM ET)
            market_time = timestamp.time()
            if not (time(9, 30) <= market_time <= time(16, 0)):
                continue
            
            spy_price = spy_row['close']
            
            if not position_opened:
                # Look for entry signal
                signal = self.strategy.generate_signal(spy_with_indicators, timestamp, vix_level)
                
                if signal:
                    signal_count += 1
                    
                    # Find best option for this signal
                    best_option = self.find_best_option(signal['action'], spy_price, options_1min, timestamp)
                    
                    if best_option:
                        # Enter position
                        position_opened = True
                        entry_time = timestamp
                        entry_option = best_option
                        entry_price = best_option['price']
                        entry_signal = signal
                        
                        print(f"\n🎯 ENTRY: {timestamp.strftime('%H:%M:%S')}")
                        print(f"   📊 Signal: {signal['action']} ({signal['confidence']:.0f}% confidence)")
                        print(f"   📊 SPY: ${spy_price:.2f}")
                        print(f"   📊 Option: {best_option['ticker']} @ ${best_option['price']:.2f}")
                        print(f"   📊 Reason: {signal['reason']}")
            
            else:
                # Manage open position
                if entry_option['ticker'] in options_1min and timestamp in options_1min[entry_option['ticker']].index:
                    current_option_price = options_1min[entry_option['ticker']].loc[timestamp, 'close']
                    
                    # Calculate P&L
                    pnl_percent = ((current_option_price - entry_price) / entry_price) * 100
                    holding_minutes = (timestamp - entry_time).total_seconds() / 60
                    
                    # Check exit conditions
                    should_exit = False
                    exit_reason = ""
                    
                    # Profit target
                    if pnl_percent >= self.strategy.profit_target_percent * 100:
                        should_exit = True
                        exit_reason = "PROFIT_TARGET"
                    
                    # Stop loss
                    elif pnl_percent <= -self.strategy.max_loss_percent * 100:
                        should_exit = True
                        exit_reason = "STOP_LOSS"
                    
                    # Time-based exit
                    elif holding_minutes >= self.strategy.max_holding_minutes:
                        should_exit = True
                        exit_reason = "MAX_TIME"
                    
                    # End of day exit
                    elif market_time >= time(15, 45):  # 3:45 PM ET
                        should_exit = True
                        exit_reason = "EOD_EXIT"
                    
                    if should_exit:
                        # Exit position
                        pnl_dollars = (current_option_price - entry_price) * 100  # $100 per contract
                        
                        print(f"\n🚪 EXIT: {timestamp.strftime('%H:%M:%S')} ({exit_reason})")
                        print(f"   📊 Duration: {holding_minutes:.0f} minutes")
                        print(f"   📊 P&L: ${pnl_dollars:.2f} ({pnl_percent:.1f}%)")
                        print(f"   📊 Option: ${entry_price:.2f} → ${current_option_price:.2f}")
                        
                        # Log trade
                        trade = {
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'signal': entry_signal,
                            'option': entry_option,
                            'entry_price': entry_price,
                            'exit_price': current_option_price,
                            'pnl_dollars': pnl_dollars,
                            'pnl_percent': pnl_percent,
                            'duration_minutes': holding_minutes,
                            'exit_reason': exit_reason
                        }
                        
                        self.trades.append(trade)
                        self.current_capital += pnl_dollars
                        
                        # Reset for next trade
                        position_opened = False
                        entry_time = None
                        entry_option = None
                        entry_price = None
                        entry_signal = None
        
        # Generate results
        self.generate_momentum_results(test_date, signal_count)
    
    def generate_momentum_results(self, test_date: datetime, signal_count: int):
        """Generate detailed momentum backtest results"""
        
        print(f"\n" + "=" * 70)
        print(f"📊 MOMENTUM STRATEGY RESULTS")
        print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"=" * 70)
        
        print(f"📊 Total Signals Generated: {signal_count}")
        print(f"📊 Total Trades Executed: {len(self.trades)}")
        
        if not self.trades:
            print(f"❌ No trades executed")
            return
        
        # Calculate metrics
        total_pnl = sum(trade['pnl_dollars'] for trade in self.trades)
        winning_trades = [t for t in self.trades if t['pnl_dollars'] > 0]
        losing_trades = [t for t in self.trades if t['pnl_dollars'] < 0]
        
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        avg_win = np.mean([t['pnl_dollars'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_dollars'] for t in losing_trades]) if losing_trades else 0
        avg_duration = np.mean([t['duration_minutes'] for t in self.trades])
        
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        
        print(f"💰 Total P&L: ${total_pnl:,.2f}")
        print(f"📈 Total Return: {total_return:.2f}%")
        print(f"🎯 Win Rate: {win_rate:.1f}% ({len(winning_trades)}/{len(self.trades)})")
        print(f"🏆 Average Win: ${avg_win:.2f}")
        print(f"💸 Average Loss: ${avg_loss:.2f}")
        print(f"⏱️ Average Duration: {avg_duration:.1f} minutes")
        print(f"💵 Final Capital: ${self.current_capital:,.2f}")
        
        # Detailed trade log
        print(f"\n📋 DETAILED TRADE LOG:")
        print(f"=" * 70)
        
        for i, trade in enumerate(self.trades, 1):
            entry_time = trade['entry_time'].strftime('%H:%M')
            exit_time = trade['exit_time'].strftime('%H:%M')
            duration = trade['duration_minutes']
            pnl = trade['pnl_dollars']
            pnl_pct = trade['pnl_percent']
            reason = trade['exit_reason']
            
            status_emoji = "🟢" if pnl > 0 else "🔴"
            
            print(f"{status_emoji} Trade {i}: {entry_time}-{exit_time} ({duration:.0f}min)")
            print(f"   {trade['signal']['action']} {trade['option']['type']} ${trade['option']['strike']}")
            print(f"   P&L: ${pnl:.2f} ({pnl_pct:.1f}%) | Exit: {reason}")
        
        # Save results
        results_file = f"momentum_1min_backtest_{test_date.strftime('%Y%m%d')}.json"
        
        # Prepare serializable data
        serializable_trades = []
        for trade in self.trades:
            trade_copy = trade.copy()
            trade_copy['entry_time'] = trade_copy['entry_time'].isoformat()
            trade_copy['exit_time'] = trade_copy['exit_time'].isoformat()
            # Fix signal timestamp serialization
            if 'signal' in trade_copy and 'timestamp' in trade_copy['signal']:
                trade_copy['signal']['timestamp'] = trade_copy['signal']['timestamp'].isoformat()
            serializable_trades.append(trade_copy)
        
        results_data = {
            'test_date': test_date.strftime('%Y-%m-%d'),
            'strategy': f"{self.strategy.name} {self.strategy.version}",
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_pnl': total_pnl,
            'total_return_percent': total_return,
            'total_signals': signal_count,
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
    print("🚀 SIMPLE MOMENTUM STRATEGY - 1-MINUTE BACKTEST")
    print("=" * 70)
    
    # Initialize backtest
    backtest = MomentumBacktester()
    
    # Use the date we have 1-minute data for
    test_date = datetime(2025, 8, 29)
    
    try:
        # Run backtest
        backtest.run_momentum_backtest(test_date)
        
    except KeyboardInterrupt:
        print("\n⚠️ Backtest interrupted by user")
    except Exception as e:
        print(f"❌ Backtest error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
