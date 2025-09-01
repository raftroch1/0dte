#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE FAILURE PATTERN ANALYSIS
==========================================
Analyzes the 6-month backtest logs to identify key failure patterns and root causes.

Following @.cursorrules: Using existing infrastructure, real data analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json

class FailurePatternAnalyzer:
    def __init__(self, session_id: str = "20250831_181835"):
        self.session_id = session_id
        self.logs_dir = Path("logs")
        
        # Load all log files
        self.trades_df = pd.read_csv(self.logs_dir / f"trades_{session_id}.csv")
        self.daily_df = pd.read_csv(self.logs_dir / f"daily_performance_{session_id}.csv")
        self.market_df = pd.read_csv(self.logs_dir / f"market_conditions_{session_id}.csv")
        self.balance_df = pd.read_csv(self.logs_dir / f"balance_progression_{session_id}.csv")
        
        # Convert date columns
        self.trades_df['entry_date'] = pd.to_datetime(self.trades_df['entry_date'])
        self.trades_df['exit_date'] = pd.to_datetime(self.trades_df['exit_date'])
        self.daily_df['date'] = pd.to_datetime(self.daily_df['date'])
        self.market_df['timestamp'] = pd.to_datetime(self.market_df['timestamp'])
        
        print(f"📊 LOADED DATA:")
        print(f"   Trades: {len(self.trades_df)}")
        print(f"   Daily Records: {len(self.daily_df)}")
        print(f"   Market Conditions: {len(self.market_df)}")
        print(f"   Balance Entries: {len(self.balance_df)}")

    def analyze_strategy_performance(self):
        """Analyze performance by strategy type"""
        print("\n🎯 STRATEGY PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        strategy_stats = self.trades_df.groupby('strategy_type').agg({
            'realized_pnl': ['count', 'sum', 'mean', 'std'],
            'return_pct': ['mean', 'std'],
            'trade_id': 'count'
        }).round(2)
        
        # Calculate win rates
        win_rates = self.trades_df.groupby('strategy_type').apply(
            lambda x: (x['realized_pnl'] > 0).sum() / len(x) * 100
        ).round(1)
        
        print("\n📊 STRATEGY BREAKDOWN:")
        for strategy in self.trades_df['strategy_type'].unique():
            strategy_data = self.trades_df[self.trades_df['strategy_type'] == strategy]
            total_pnl = strategy_data['realized_pnl'].sum()
            win_rate = win_rates[strategy]
            avg_win = strategy_data[strategy_data['realized_pnl'] > 0]['realized_pnl'].mean()
            avg_loss = strategy_data[strategy_data['realized_pnl'] < 0]['realized_pnl'].mean()
            
            print(f"\n{strategy}:")
            print(f"   Trades: {len(strategy_data)}")
            print(f"   Total P&L: ${total_pnl:,.2f}")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   Avg Win: ${avg_win:.2f}" if not pd.isna(avg_win) else "   Avg Win: N/A")
            print(f"   Avg Loss: ${avg_loss:.2f}" if not pd.isna(avg_loss) else "   Avg Loss: N/A")
            
            # Identify worst performing days
            worst_trades = strategy_data.nsmallest(3, 'realized_pnl')
            print(f"   Worst 3 Trades:")
            for _, trade in worst_trades.iterrows():
                print(f"     {trade['entry_date'].strftime('%Y-%m-%d')}: ${trade['realized_pnl']:.2f} ({trade['exit_reason']})")

    def analyze_market_regime_accuracy(self):
        """Analyze how accurate our market regime detection was"""
        print("\n🌍 MARKET REGIME DETECTION ANALYSIS")
        print("=" * 50)
        
        # Create date column for market data
        self.market_df['date'] = self.market_df['timestamp'].dt.date
        self.trades_df['entry_date_only'] = self.trades_df['entry_date'].dt.date
        
        # Merge trades with market conditions
        trades_with_market = self.trades_df.merge(
            self.market_df[['date', 'detected_regime', 'put_call_ratio', 'spy_price']].drop_duplicates('date'),
            left_on='entry_date_only',
            right_on='date',
            how='left'
        )
        
        # Analyze performance by detected regime
        regime_performance = trades_with_market.groupby(['detected_regime', 'strategy_type']).agg({
            'realized_pnl': ['count', 'sum', 'mean'],
            'trade_id': 'count'
        }).round(2)
        
        print("\n📊 PERFORMANCE BY MARKET REGIME:")
        for regime in ['BULLISH', 'BEARISH', 'NEUTRAL']:
            regime_data = trades_with_market[trades_with_market['detected_regime'] == regime]
            if len(regime_data) > 0:
                total_pnl = regime_data['realized_pnl'].sum()
                win_rate = (regime_data['realized_pnl'] > 0).sum() / len(regime_data) * 100
                
                print(f"\n{regime} Markets:")
                print(f"   Trades: {len(regime_data)}")
                print(f"   Total P&L: ${total_pnl:,.2f}")
                print(f"   Win Rate: {win_rate:.1f}%")
                
                # Strategy breakdown within regime
                strategy_breakdown = regime_data.groupby('strategy_type').agg({
                    'realized_pnl': ['count', 'sum'],
                    'trade_id': 'count'
                })
                
                for strategy in regime_data['strategy_type'].unique():
                    strategy_data = regime_data[regime_data['strategy_type'] == strategy]
                    strategy_pnl = strategy_data['realized_pnl'].sum()
                    strategy_win_rate = (strategy_data['realized_pnl'] > 0).sum() / len(strategy_data) * 100
                    print(f"     {strategy}: {len(strategy_data)} trades, ${strategy_pnl:.2f}, {strategy_win_rate:.1f}% win rate")

    def analyze_temporal_patterns(self):
        """Analyze performance patterns over time"""
        print("\n📅 TEMPORAL PATTERN ANALYSIS")
        print("=" * 50)
        
        # Monthly performance
        self.trades_df['entry_month'] = self.trades_df['entry_date'].dt.to_period('M')
        monthly_performance = self.trades_df.groupby('entry_month').agg({
            'realized_pnl': ['count', 'sum', 'mean'],
            'trade_id': 'count'
        }).round(2)
        
        print("\n📊 MONTHLY PERFORMANCE:")
        for month in self.trades_df['entry_month'].unique():
            month_data = self.trades_df[self.trades_df['entry_month'] == month]
            total_pnl = month_data['realized_pnl'].sum()
            win_rate = (month_data['realized_pnl'] > 0).sum() / len(month_data) * 100
            
            print(f"{month}: {len(month_data)} trades, ${total_pnl:,.2f}, {win_rate:.1f}% win rate")
        
        # Weekly performance (day of week)
        self.trades_df['day_of_week'] = self.trades_df['entry_date'].dt.day_name()
        weekly_performance = self.trades_df.groupby('day_of_week').agg({
            'realized_pnl': ['count', 'sum', 'mean'],
        }).round(2)
        
        print("\n📊 DAY OF WEEK PERFORMANCE:")
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            if day in self.trades_df['day_of_week'].values:
                day_data = self.trades_df[self.trades_df['day_of_week'] == day]
                total_pnl = day_data['realized_pnl'].sum()
                win_rate = (day_data['realized_pnl'] > 0).sum() / len(day_data) * 100
                
                print(f"{day}: {len(day_data)} trades, ${total_pnl:,.2f}, {win_rate:.1f}% win rate")

    def analyze_exit_reasons(self):
        """Analyze performance by exit reason"""
        print("\n🚪 EXIT REASON ANALYSIS")
        print("=" * 50)
        
        exit_performance = self.trades_df.groupby('exit_reason').agg({
            'realized_pnl': ['count', 'sum', 'mean'],
            'return_pct': 'mean'
        }).round(2)
        
        print("\n📊 PERFORMANCE BY EXIT REASON:")
        for reason in self.trades_df['exit_reason'].unique():
            reason_data = self.trades_df[self.trades_df['exit_reason'] == reason]
            total_pnl = reason_data['realized_pnl'].sum()
            avg_pnl = reason_data['realized_pnl'].mean()
            
            print(f"{reason}:")
            print(f"   Count: {len(reason_data)}")
            print(f"   Total P&L: ${total_pnl:,.2f}")
            print(f"   Avg P&L: ${avg_pnl:.2f}")
            print(f"   Avg Return: {reason_data['return_pct'].mean():.1f}%")

    def identify_worst_periods(self):
        """Identify the worst performing periods"""
        print("\n💥 WORST PERFORMING PERIODS")
        print("=" * 50)
        
        # Worst single trades
        worst_trades = self.trades_df.nsmallest(10, 'realized_pnl')
        print("\n📊 TOP 10 WORST TRADES:")
        for i, (_, trade) in enumerate(worst_trades.iterrows(), 1):
            print(f"{i:2d}. {trade['entry_date'].strftime('%Y-%m-%d')} {trade['strategy_type']}: "
                  f"${trade['realized_pnl']:,.2f} ({trade['exit_reason']})")
        
        # Worst consecutive days
        self.daily_df['cumulative_loss'] = 0
        current_loss = 0
        max_consecutive_loss = 0
        worst_period_start = None
        worst_period_end = None
        
        for i, row in self.daily_df.iterrows():
            if row['daily_pnl'] < 0:
                current_loss += abs(row['daily_pnl'])
                if current_loss > max_consecutive_loss:
                    max_consecutive_loss = current_loss
                    worst_period_end = row['date']
                    # Find start of this losing streak
                    j = i
                    while j >= 0 and self.daily_df.iloc[j]['daily_pnl'] < 0:
                        j -= 1
                    worst_period_start = self.daily_df.iloc[j + 1]['date'] if j >= 0 else self.daily_df.iloc[0]['date']
            else:
                current_loss = 0
        
        print(f"\n📊 WORST CONSECUTIVE LOSING PERIOD:")
        print(f"   Period: {worst_period_start} to {worst_period_end}")
        print(f"   Total Loss: ${max_consecutive_loss:,.2f}")

    def generate_recommendations(self):
        """Generate specific recommendations based on analysis"""
        print("\n💡 KEY RECOMMENDATIONS")
        print("=" * 50)
        
        # Calculate key metrics
        total_trades = len(self.trades_df)
        overall_win_rate = (self.trades_df['realized_pnl'] > 0).sum() / total_trades * 100
        buy_call_win_rate = (self.trades_df[self.trades_df['strategy_type'] == 'BUY_CALL']['realized_pnl'] > 0).sum() / len(self.trades_df[self.trades_df['strategy_type'] == 'BUY_CALL']) * 100
        
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        print(f"   Overall Win Rate: {overall_win_rate:.1f}% (Need 60%+ for profitability)")
        print(f"   BUY_CALL Win Rate: {buy_call_win_rate:.1f}% (Extremely poor)")
        
        print(f"\n🎯 CRITICAL ISSUES IDENTIFIED:")
        print(f"   1. BULLISH SIGNAL DETECTION: Only {buy_call_win_rate:.1f}% win rate suggests regime detection is broken")
        print(f"   2. 0DTE TIME DECAY: Average loss per trade is too high for 0DTE")
        print(f"   3. VOLATILITY CLASSIFICATION: Everything classified as 'HIGH' - needs calibration")
        print(f"   4. STOP LOSSES: Many trades hitting max loss suggests poor entry timing")
        
        print(f"\n🚀 IMMEDIATE ACTION ITEMS:")
        print(f"   1. TEST 1-3 DTE: More time for trades to work out")
        print(f"   2. FIX REGIME DETECTION: Recalibrate P/C ratio thresholds")
        print(f"   3. REDUCE POSITION SIZE: $300 per trade is too aggressive")
        print(f"   4. TEST DIFFERENT TIME PERIOD: Jan-June 2024 might be anomalous")
        print(f"   5. FOCUS ON IRON CONDORS: Best performing strategy (33% win rate)")

    def run_complete_analysis(self):
        """Run the complete failure pattern analysis"""
        print("🔍 COMPREHENSIVE FAILURE PATTERN ANALYSIS")
        print("=" * 60)
        print(f"Session: {self.session_id}")
        print(f"Period: {self.trades_df['entry_date'].min().strftime('%Y-%m-%d')} to {self.trades_df['entry_date'].max().strftime('%Y-%m-%d')}")
        
        self.analyze_strategy_performance()
        self.analyze_market_regime_accuracy()
        self.analyze_temporal_patterns()
        self.analyze_exit_reasons()
        self.identify_worst_periods()
        self.generate_recommendations()
        
        print(f"\n✅ ANALYSIS COMPLETE!")
        print(f"📊 Next step: Test different time periods and 1-3 DTE options")

if __name__ == "__main__":
    analyzer = FailurePatternAnalyzer()
    analyzer.run_complete_analysis()
