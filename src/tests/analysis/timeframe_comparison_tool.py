#!/usr/bin/env python3
"""
📊 Timeframe Comparison Tool
===========================

Compare momentum strategy performance across different timeframes:
- 1-minute precision (current implementation)
- 5-minute bars (reduced noise)
- 15-minute bars (trend following)

Analyzes:
- Signal frequency vs quality trade-off
- Optimal timeframe for different market conditions
- Risk-adjusted returns by timeframe
- Execution efficiency analysis

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

class TimeframeComparator:
    """Compare strategy performance across different timeframes"""
    
    def __init__(self):
        self.timeframes = ['1min', '5min', '15min']
        self.results = {}
        
    def run_timeframe_comparison(self, test_date: datetime):
        """Run comparison across all timeframes"""
        
        print(f"\n📊 TIMEFRAME COMPARISON ANALYSIS")
        print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"🎯 Comparing: {', '.join(self.timeframes)}")
        print(f"=" * 70)
        
        # Load base data
        spy_1min = self.load_spy_data(test_date)
        if spy_1min.empty:
            print(f"❌ No data available for {test_date.strftime('%Y-%m-%d')}")
            return
        
        # Create different timeframe datasets
        timeframe_data = {
            '1min': spy_1min,
            '5min': spy_1min.resample('5min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min', 
                'close': 'last',
                'volume': 'sum'
            }).dropna(),
            '15min': spy_1min.resample('15min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last', 
                'volume': 'sum'
            }).dropna()
        }
        
        # Run analysis for each timeframe
        for timeframe in self.timeframes:
            print(f"\n🔍 ANALYZING {timeframe.upper()} TIMEFRAME:")
            print(f"-" * 40)
            
            df = timeframe_data[timeframe]
            analysis = self.analyze_timeframe_performance(df, timeframe, test_date)
            self.results[timeframe] = analysis
            
            self.print_timeframe_summary(timeframe, analysis)
        
        # Generate comparison report
        self.generate_comparison_report(test_date)
    
    def load_spy_data(self, date: datetime) -> pd.DataFrame:
        """Load SPY 1-minute data"""
        try:
            date_str = date.strftime('%Y%m%d')
            file_path = f"intraday_data/spy_1min_{date_str}.csv"
            
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return pd.DataFrame()
    
    def analyze_timeframe_performance(self, df: pd.DataFrame, timeframe: str, test_date: datetime) -> Dict:
        """Analyze performance metrics for a specific timeframe"""
        
        # Calculate technical indicators
        df = self.calculate_indicators(df)
        
        # Generate signals
        signals = self.generate_signals(df, timeframe)
        
        # Simulate trades
        trades = self.simulate_trades(df, signals, timeframe)
        
        # Calculate metrics
        metrics = self.calculate_performance_metrics(trades, df, timeframe)
        
        return {
            'timeframe': timeframe,
            'data_points': len(df),
            'signals': signals,
            'trades': trades,
            'metrics': metrics
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Fast RSI
        gain_fast = (delta.where(delta > 0, 0)).rolling(window=5).mean()
        loss_fast = (-delta.where(delta < 0, 0)).rolling(window=5).mean()
        rs_fast = gain_fast / loss_fast
        df['fast_rsi'] = 100 - (100 / (1 + rs_fast))
        
        # Momentum
        df['momentum'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        
        # Volume ratio
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        # MACD
        ema_fast = df['close'].ewm(span=12).mean()
        ema_slow = df['close'].ewm(span=26).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Bollinger Bands
        bb_sma = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = bb_sma + (bb_std * 2)
        df['bb_lower'] = bb_sma - (bb_std * 2)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame, timeframe: str) -> List[Dict]:
        """Generate trading signals for the timeframe"""
        
        signals = []
        
        # Timeframe-specific thresholds
        thresholds = {
            '1min': {'rsi_os': 40, 'rsi_ob': 60, 'momentum': 0.05},
            '5min': {'rsi_os': 35, 'rsi_ob': 65, 'momentum': 0.08},
            '15min': {'rsi_os': 30, 'rsi_ob': 70, 'momentum': 0.12}
        }
        
        thresh = thresholds[timeframe]
        
        for timestamp, row in df.iterrows():
            # Skip if insufficient data
            if pd.isna(row['fast_rsi']) or pd.isna(row['momentum']):
                continue
            
            # Skip non-market hours
            market_time = timestamp.time()
            if not (time(9, 30) <= market_time <= time(16, 0)):
                continue
            
            confidence = 40
            action = None
            reason = f"{timeframe}: "
            
            # Time-based logic
            if time(9, 30) <= market_time <= time(11, 0):  # Morning
                if row['fast_rsi'] < thresh['rsi_os'] and row['momentum'] > thresh['momentum']:
                    action = "BUY_CALL"
                    confidence += 25
                    reason += "Morning oversold breakout, "
                elif row['fast_rsi'] > thresh['rsi_ob'] and row['momentum'] < -thresh['momentum']:
                    action = "BUY_PUT"
                    confidence += 25
                    reason += "Morning overbought breakdown, "
            
            elif time(14, 0) <= market_time <= time(16, 0):  # Afternoon
                if row['fast_rsi'] < thresh['rsi_os'] and row['momentum'] < -thresh['momentum']:
                    action = "BUY_CALL"
                    confidence += 20
                    reason += "Afternoon oversold bounce, "
                elif row['fast_rsi'] > thresh['rsi_ob'] and row['momentum'] > thresh['momentum']:
                    action = "BUY_PUT"
                    confidence += 20
                    reason += "Afternoon overbought reversal, "
            
            if not action:
                continue
            
            # Volume confirmation
            if row['volume_ratio'] > 1.5:
                confidence += 15
                reason += f"High volume ({row['volume_ratio']:.1f}x), "
            
            # MACD confirmation
            if row['macd'] > row['macd_signal'] and action == "BUY_CALL":
                confidence += 10
                reason += "MACD bullish, "
            elif row['macd'] < row['macd_signal'] and action == "BUY_PUT":
                confidence += 10
                reason += "MACD bearish, "
            
            # Bollinger Bands
            if action == "BUY_CALL" and row['close'] < row['bb_lower']:
                confidence += 12
                reason += "Below BB lower, "
            elif action == "BUY_PUT" and row['close'] > row['bb_upper']:
                confidence += 12
                reason += "Above BB upper, "
            
            # Minimum confidence
            if confidence >= 50:
                signals.append({
                    'timestamp': timestamp,
                    'action': action,
                    'confidence': min(95, confidence),
                    'reason': reason.rstrip(', '),
                    'spy_price': row['close'],
                    'indicators': {
                        'fast_rsi': row['fast_rsi'],
                        'momentum': row['momentum'],
                        'volume_ratio': row['volume_ratio']
                    }
                })
        
        return signals
    
    def simulate_trades(self, df: pd.DataFrame, signals: List[Dict], timeframe: str) -> List[Dict]:
        """Simulate trade execution"""
        
        trades = []
        position_open = False
        entry_signal = None
        entry_time = None
        entry_price = 0.10  # Simulated option entry price
        
        # Timeframe-specific holding periods (in bars)
        max_holding = {
            '1min': 240,  # 4 hours
            '5min': 48,   # 4 hours  
            '15min': 16   # 4 hours
        }
        
        for signal in signals:
            if not position_open:
                # Enter position
                position_open = True
                entry_signal = signal
                entry_time = signal['timestamp']
                entry_price = 0.10  # Simulated entry
                
            else:
                # Check exit conditions
                current_time = signal['timestamp']
                bars_held = len(df[entry_time:current_time]) - 1
                
                # Time-based exit
                if bars_held >= max_holding[timeframe]:
                    exit_price = 0.08  # Simulated exit
                    pnl = (exit_price - entry_price) * 100
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_signal': entry_signal,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl_dollars': pnl,
                        'pnl_percent': (pnl / (entry_price * 100)) * 100,
                        'bars_held': bars_held,
                        'exit_reason': 'MAX_TIME'
                    })
                    
                    position_open = False
                    entry_signal = None
                    entry_time = None
        
        return trades
    
    def calculate_performance_metrics(self, trades: List[Dict], df: pd.DataFrame, timeframe: str) -> Dict:
        """Calculate performance metrics"""
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'total_pnl': 0,
                'avg_holding_period': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl_dollars'] > 0]
        win_rate = len(winning_trades) / total_trades * 100
        
        pnls = [t['pnl_dollars'] for t in trades]
        total_pnl = sum(pnls)
        avg_pnl = np.mean(pnls)
        
        holding_periods = [t['bars_held'] for t in trades]
        avg_holding_period = np.mean(holding_periods)
        
        # Risk metrics
        pnl_std = np.std(pnls) if len(pnls) > 1 else 0
        sharpe_ratio = (avg_pnl / pnl_std) if pnl_std > 0 else 0
        
        # Drawdown
        cumulative_pnl = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = cumulative_pnl - running_max
        max_drawdown = abs(min(drawdown)) if len(drawdown) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl,
            'avg_holding_period': avg_holding_period,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'pnl_std': pnl_std
        }
    
    def print_timeframe_summary(self, timeframe: str, analysis: Dict):
        """Print summary for a timeframe"""
        
        signals = analysis['signals']
        trades = analysis['trades']
        metrics = analysis['metrics']
        
        print(f"📊 Data Points: {analysis['data_points']}")
        print(f"📊 Signals Generated: {len(signals)}")
        print(f"📊 Trades Executed: {len(trades)}")
        
        if metrics['total_trades'] > 0:
            print(f"📊 Win Rate: {metrics['win_rate']:.1f}%")
            print(f"📊 Average P&L: ${metrics['avg_pnl']:.2f}")
            print(f"📊 Total P&L: ${metrics['total_pnl']:.2f}")
            print(f"📊 Avg Holding: {metrics['avg_holding_period']:.1f} bars")
            print(f"📊 Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"📊 Max Drawdown: ${metrics['max_drawdown']:.2f}")
        else:
            print(f"❌ No trades executed")
    
    def generate_comparison_report(self, test_date: datetime):
        """Generate comprehensive comparison report"""
        
        print(f"\n" + "=" * 70)
        print(f"📊 TIMEFRAME COMPARISON SUMMARY")
        print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"=" * 70)
        
        # Comparison table
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print(f"{'Timeframe':<10} {'Signals':<8} {'Trades':<7} {'Win%':<6} {'Avg P&L':<8} {'Total P&L':<9} {'Sharpe':<7}")
        print(f"-" * 60)
        
        for timeframe in self.timeframes:
            if timeframe in self.results:
                result = self.results[timeframe]
                metrics = result['metrics']
                
                signals_count = len(result['signals'])
                trades_count = metrics['total_trades']
                win_rate = metrics['win_rate']
                avg_pnl = metrics['avg_pnl']
                total_pnl = metrics['total_pnl']
                sharpe = metrics['sharpe_ratio']
                
                print(f"{timeframe:<10} {signals_count:<8} {trades_count:<7} {win_rate:<6.1f} ${avg_pnl:<7.2f} ${total_pnl:<8.2f} {sharpe:<7.2f}")
        
        # Analysis and recommendations
        print(f"\n📊 ANALYSIS & RECOMMENDATIONS:")
        print(f"-" * 40)
        
        best_timeframe = self.find_best_timeframe()
        if best_timeframe:
            print(f"🏆 Best Overall Timeframe: {best_timeframe['timeframe'].upper()}")
            print(f"   📊 Reason: {best_timeframe['reason']}")
        
        # Signal frequency analysis
        print(f"\n📊 SIGNAL FREQUENCY ANALYSIS:")
        for timeframe in self.timeframes:
            if timeframe in self.results:
                result = self.results[timeframe]
                signal_rate = len(result['signals']) / result['data_points'] * 100
                print(f"   {timeframe}: {signal_rate:.1f}% of bars generate signals")
        
        # Risk-adjusted returns
        print(f"\n📊 RISK-ADJUSTED ANALYSIS:")
        for timeframe in self.timeframes:
            if timeframe in self.results:
                metrics = self.results[timeframe]['metrics']
                if metrics['total_trades'] > 0:
                    risk_adj_return = metrics['total_pnl'] / max(metrics['max_drawdown'], 1)
                    print(f"   {timeframe}: Risk-Adj Return = {risk_adj_return:.2f}")
        
        # Save comparison results
        self.save_comparison_results(test_date)
    
    def find_best_timeframe(self) -> Optional[Dict]:
        """Find the best performing timeframe"""
        
        best_score = -999
        best_timeframe = None
        
        for timeframe, result in self.results.items():
            metrics = result['metrics']
            
            if metrics['total_trades'] == 0:
                continue
            
            # Composite score: Sharpe ratio + win rate + total return
            score = (metrics['sharpe_ratio'] * 0.4 + 
                    metrics['win_rate'] * 0.003 +  # Scale win rate
                    metrics['total_pnl'] * 0.1)    # Scale total PnL
            
            if score > best_score:
                best_score = score
                best_timeframe = {
                    'timeframe': timeframe,
                    'score': score,
                    'reason': f"Best composite score ({score:.2f}): Sharpe {metrics['sharpe_ratio']:.2f}, Win Rate {metrics['win_rate']:.1f}%, Total P&L ${metrics['total_pnl']:.2f}"
                }
        
        return best_timeframe
    
    def save_comparison_results(self, test_date: datetime):
        """Save comparison results to file"""
        
        results_file = f"timeframe_comparison_{test_date.strftime('%Y%m%d')}.json"
        
        # Prepare serializable data
        serializable_results = {}
        for timeframe, result in self.results.items():
            serializable_result = result.copy()
            
            # Convert timestamps to strings
            serializable_signals = []
            for signal in result['signals']:
                signal_copy = signal.copy()
                signal_copy['timestamp'] = signal_copy['timestamp'].isoformat()
                serializable_signals.append(signal_copy)
            
            serializable_trades = []
            for trade in result['trades']:
                trade_copy = trade.copy()
                trade_copy['entry_time'] = trade_copy['entry_time'].isoformat()
                trade_copy['exit_time'] = trade_copy['exit_time'].isoformat()
                if 'entry_signal' in trade_copy and 'timestamp' in trade_copy['entry_signal']:
                    trade_copy['entry_signal']['timestamp'] = trade_copy['entry_signal']['timestamp'].isoformat()
                serializable_trades.append(trade_copy)
            
            serializable_result['signals'] = serializable_signals
            serializable_result['trades'] = serializable_trades
            serializable_results[timeframe] = serializable_result
        
        comparison_data = {
            'test_date': test_date.strftime('%Y-%m-%d'),
            'analysis_type': 'Timeframe Comparison',
            'timeframes_analyzed': self.timeframes,
            'best_timeframe': self.find_best_timeframe(),
            'results': serializable_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        
        print(f"\n💾 Comparison results saved to: {results_file}")

def main():
    """Main execution function"""
    print("📊 TIMEFRAME COMPARISON TOOL")
    print("=" * 70)
    
    # Initialize comparator
    comparator = TimeframeComparator()
    
    # Use the date we have data for
    test_date = datetime(2025, 8, 29)
    
    try:
        # Run comparison
        comparator.run_timeframe_comparison(test_date)
        
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
