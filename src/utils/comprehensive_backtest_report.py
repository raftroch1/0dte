#!/usr/bin/env python3
"""
COMPREHENSIVE BACKTEST REPORT GENERATOR
======================================

Following @.cursorrules - Create PROPER, EASY-TO-UNDERSTAND log files
This generates a complete, human-readable report after each backtest
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class ComprehensiveBacktestReport:
    """Generate comprehensive, easy-to-understand backtest reports"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log_dir = Path("logs")
        
    def generate_complete_report(self) -> str:
        """Generate a complete, human-readable backtest report"""
        
        # Load all log files
        trades_df = pd.read_csv(f"logs/trades_{self.session_id}.csv")
        balance_df = pd.read_csv(f"logs/balance_progression_{self.session_id}.csv")
        
        # Generate report
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("🚀 COMPREHENSIVE BACKTEST REPORT")
        report_lines.append("=" * 100)
        report_lines.append(f"Session ID: {self.session_id}")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 1. EXECUTIVE SUMMARY
        report_lines.extend(self._generate_executive_summary(trades_df, balance_df))
        
        # 2. FINANCIAL PERFORMANCE
        report_lines.extend(self._generate_financial_performance(trades_df, balance_df))
        
        # 3. TRADING STATISTICS
        report_lines.extend(self._generate_trading_statistics(trades_df))
        
        # 4. STRATEGY BREAKDOWN
        report_lines.extend(self._generate_strategy_breakdown(trades_df))
        
        # 5. TRADE-BY-TRADE DETAILS
        report_lines.extend(self._generate_trade_details(trades_df))
        
        # 6. DAILY PERFORMANCE
        report_lines.extend(self._generate_daily_performance(trades_df, balance_df))
        
        # 7. RISK ANALYSIS
        report_lines.extend(self._generate_risk_analysis(trades_df, balance_df))
        
        # 8. ACCOUNTING VALIDATION
        report_lines.extend(self._generate_accounting_validation(trades_df, balance_df))
        
        # Save report
        report_content = "\n".join(report_lines)
        report_path = f"logs/BACKTEST_REPORT_{self.session_id}.txt"
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"📊 COMPREHENSIVE REPORT GENERATED: {report_path}")
        return report_path
    
    def _generate_executive_summary(self, trades_df: pd.DataFrame, balance_df: pd.DataFrame) -> list:
        """Generate executive summary"""
        lines = []
        lines.append("📊 EXECUTIVE SUMMARY")
        lines.append("=" * 50)
        
        # Basic metrics
        initial_balance = 25000.0
        final_balance = balance_df['balance'].iloc[-1]
        total_pnl = final_balance - initial_balance
        total_return = (total_pnl / initial_balance) * 100
        
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['realized_pnl'] > 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Determine performance
        if total_return > 15:
            performance = "🔥 EXCELLENT"
        elif total_return > 5:
            performance = "✅ GOOD"
        elif total_return > 0:
            performance = "📈 POSITIVE"
        elif total_return > -5:
            performance = "⚠️ SLIGHT LOSS"
        else:
            performance = "❌ SIGNIFICANT LOSS"
        
        lines.append(f"Performance Rating: {performance}")
        lines.append(f"Total Return: {total_return:+.2f}%")
        lines.append(f"Total P&L: ${total_pnl:+,.2f}")
        lines.append(f"Win Rate: {win_rate:.1f}%")
        lines.append(f"Total Trades: {total_trades}")
        lines.append("")
        
        return lines
    
    def _generate_financial_performance(self, trades_df: pd.DataFrame, balance_df: pd.DataFrame) -> list:
        """Generate financial performance section"""
        lines = []
        lines.append("💰 FINANCIAL PERFORMANCE")
        lines.append("=" * 50)
        
        initial_balance = 25000.0
        final_balance = balance_df['balance'].iloc[-1]
        total_pnl = final_balance - initial_balance
        total_return = (total_pnl / initial_balance) * 100
        
        # Calculate period
        start_date = trades_df['entry_date'].min() if len(trades_df) > 0 else "N/A"
        end_date = trades_df['exit_date'].max() if len(trades_df) > 0 else "N/A"
        
        lines.append(f"Backtest Period: {start_date} to {end_date}")
        lines.append(f"Initial Balance: ${initial_balance:,.2f}")
        lines.append(f"Final Balance: ${final_balance:,.2f}")
        lines.append(f"Total P&L: ${total_pnl:+,.2f}")
        lines.append(f"Total Return: {total_return:+.2f}%")
        
        # Annualized return (rough estimate)
        if len(trades_df) > 0:
            try:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                days = (end_dt - start_dt).days
                if days > 0:
                    annualized_return = ((final_balance / initial_balance) ** (365 / days) - 1) * 100
                    lines.append(f"Annualized Return: {annualized_return:+.2f}%")
            except:
                pass
        
        lines.append("")
        return lines
    
    def _generate_trading_statistics(self, trades_df: pd.DataFrame) -> list:
        """Generate trading statistics"""
        lines = []
        lines.append("📈 TRADING STATISTICS")
        lines.append("=" * 50)
        
        if len(trades_df) == 0:
            lines.append("No trades executed")
            lines.append("")
            return lines
        
        total_trades = len(trades_df)
        completed_trades = trades_df[trades_df['realized_pnl'] != 0]
        winning_trades = completed_trades[completed_trades['realized_pnl'] > 0]
        losing_trades = completed_trades[completed_trades['realized_pnl'] < 0]
        
        win_rate = (len(winning_trades) / len(completed_trades)) * 100 if len(completed_trades) > 0 else 0
        avg_win = winning_trades['realized_pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['realized_pnl'].mean() if len(losing_trades) > 0 else 0
        avg_trade = completed_trades['realized_pnl'].mean() if len(completed_trades) > 0 else 0
        
        best_trade = completed_trades['realized_pnl'].max() if len(completed_trades) > 0 else 0
        worst_trade = completed_trades['realized_pnl'].min() if len(completed_trades) > 0 else 0
        
        lines.append(f"Total Trades: {total_trades}")
        lines.append(f"Completed Trades: {len(completed_trades)}")
        lines.append(f"Winning Trades: {len(winning_trades)}")
        lines.append(f"Losing Trades: {len(losing_trades)}")
        lines.append(f"Win Rate: {win_rate:.1f}%")
        lines.append(f"Average Trade P&L: ${avg_trade:+,.2f}")
        lines.append(f"Average Win: ${avg_win:+,.2f}")
        lines.append(f"Average Loss: ${avg_loss:+,.2f}")
        lines.append(f"Best Trade: ${best_trade:+,.2f}")
        lines.append(f"Worst Trade: ${worst_trade:+,.2f}")
        
        # Profit factor
        total_wins = winning_trades['realized_pnl'].sum() if len(winning_trades) > 0 else 0
        total_losses = abs(losing_trades['realized_pnl'].sum()) if len(losing_trades) > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        lines.append(f"Profit Factor: {profit_factor:.2f}")
        
        lines.append("")
        return lines
    
    def _generate_strategy_breakdown(self, trades_df: pd.DataFrame) -> list:
        """Generate strategy breakdown"""
        lines = []
        lines.append("🎯 STRATEGY BREAKDOWN")
        lines.append("=" * 50)
        
        if len(trades_df) == 0:
            lines.append("No strategies executed")
            lines.append("")
            return lines
        
        completed_trades = trades_df[trades_df['realized_pnl'] != 0]
        
        for strategy in completed_trades['strategy_type'].unique():
            strategy_trades = completed_trades[completed_trades['strategy_type'] == strategy]
            strategy_wins = strategy_trades[strategy_trades['realized_pnl'] > 0]
            
            total_pnl = strategy_trades['realized_pnl'].sum()
            win_rate = (len(strategy_wins) / len(strategy_trades)) * 100 if len(strategy_trades) > 0 else 0
            avg_pnl = strategy_trades['realized_pnl'].mean()
            
            lines.append(f"{strategy}:")
            lines.append(f"  Trades: {len(strategy_trades)}")
            lines.append(f"  Total P&L: ${total_pnl:+,.2f}")
            lines.append(f"  Win Rate: {win_rate:.1f}%")
            lines.append(f"  Avg P&L: ${avg_pnl:+,.2f}")
            lines.append("")
        
        return lines
    
    def _generate_trade_details(self, trades_df: pd.DataFrame) -> list:
        """Generate detailed trade log"""
        lines = []
        lines.append("📋 DETAILED TRADE LOG")
        lines.append("=" * 50)
        
        if len(trades_df) == 0:
            lines.append("No trades to display")
            lines.append("")
            return lines
        
        # Header
        lines.append(f"{'#':<3} {'Trade ID':<25} {'Strategy':<12} {'Entry':<12} {'Exit':<12} {'P&L':<12} {'Return':<8} {'Reason':<15}")
        lines.append("-" * 100)
        
        # Trade details
        for i, (_, trade) in enumerate(trades_df.iterrows(), 1):
            trade_id = trade['trade_id']
            strategy = trade['strategy_type']
            entry_date = trade['entry_date']
            exit_date = trade.get('exit_date', 'OPEN')
            pnl = trade['realized_pnl']
            return_pct = trade.get('return_pct', 0)
            exit_reason = trade.get('exit_reason', 'N/A')
            
            lines.append(f"{i:<3} {trade_id:<25} {strategy:<12} {entry_date:<12} {exit_date:<12} ${pnl:+8.2f} {return_pct:+6.1f}% {exit_reason:<15}")
        
        lines.append("")
        return lines
    
    def _generate_daily_performance(self, trades_df: pd.DataFrame, balance_df: pd.DataFrame) -> list:
        """Generate daily performance summary"""
        lines = []
        lines.append("📅 DAILY PERFORMANCE")
        lines.append("=" * 50)
        
        if len(trades_df) == 0:
            lines.append("No daily data to display")
            lines.append("")
            return lines
        
        # Group by date
        daily_trades = trades_df.groupby('entry_date').agg({
            'realized_pnl': ['count', 'sum', 'mean'],
            'strategy_type': lambda x: ', '.join(x.unique())
        }).round(2)
        
        lines.append(f"{'Date':<12} {'Trades':<7} {'P&L':<12} {'Avg P&L':<10} {'Strategies':<30}")
        lines.append("-" * 80)
        
        for date, row in daily_trades.iterrows():
            trade_count = int(row[('realized_pnl', 'count')])
            daily_pnl = row[('realized_pnl', 'sum')]
            avg_pnl = row[('realized_pnl', 'mean')]
            strategies = row[('strategy_type', '<lambda>')]
            
            lines.append(f"{date:<12} {trade_count:<7} ${daily_pnl:+8.2f} ${avg_pnl:+8.2f} {strategies:<30}")
        
        lines.append("")
        return lines
    
    def _generate_risk_analysis(self, trades_df: pd.DataFrame, balance_df: pd.DataFrame) -> list:
        """Generate risk analysis"""
        lines = []
        lines.append("🛡️ RISK ANALYSIS")
        lines.append("=" * 50)
        
        if len(trades_df) == 0:
            lines.append("No risk data to analyze")
            lines.append("")
            return lines
        
        completed_trades = trades_df[trades_df['realized_pnl'] != 0]
        
        if len(completed_trades) == 0:
            lines.append("No completed trades for risk analysis")
            lines.append("")
            return lines
        
        # Calculate drawdown
        balance_df['running_max'] = balance_df['balance'].cummax()
        balance_df['drawdown'] = balance_df['balance'] - balance_df['running_max']
        max_drawdown = balance_df['drawdown'].min()
        max_drawdown_pct = (max_drawdown / balance_df['running_max'].max()) * 100
        
        # Risk metrics
        largest_loss = completed_trades['realized_pnl'].min()
        largest_win = completed_trades['realized_pnl'].max()
        
        # Consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        for pnl in completed_trades['realized_pnl']:
            if pnl < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        lines.append(f"Maximum Drawdown: ${max_drawdown:+,.2f} ({max_drawdown_pct:+.2f}%)")
        lines.append(f"Largest Single Loss: ${largest_loss:+,.2f}")
        lines.append(f"Largest Single Win: ${largest_win:+,.2f}")
        lines.append(f"Max Consecutive Losses: {max_consecutive_losses}")
        lines.append(f"Risk per Trade: 1.0% ($250 max)")
        lines.append(f"Position Limit: 2 concurrent positions")
        
        lines.append("")
        return lines
    
    def _generate_accounting_validation(self, trades_df: pd.DataFrame, balance_df: pd.DataFrame) -> list:
        """Generate accounting validation"""
        lines = []
        lines.append("🔍 ACCOUNTING VALIDATION")
        lines.append("=" * 50)
        
        # Calculate totals
        initial_balance = 25000.0
        final_balance = balance_df['balance'].iloc[-1]
        actual_pnl = final_balance - initial_balance
        
        completed_trades = trades_df[trades_df['realized_pnl'] != 0]
        trade_pnl_sum = completed_trades['realized_pnl'].sum() if len(completed_trades) > 0 else 0
        
        discrepancy = abs(actual_pnl - trade_pnl_sum)
        
        lines.append(f"Initial Balance: ${initial_balance:,.2f}")
        lines.append(f"Final Balance: ${final_balance:,.2f}")
        lines.append(f"Actual P&L (Balance): ${actual_pnl:+,.2f}")
        lines.append(f"Trade P&L Sum: ${trade_pnl_sum:+,.2f}")
        lines.append(f"Discrepancy: ${discrepancy:+,.2f}")
        
        if discrepancy < 1.0:
            lines.append("✅ ACCOUNTING VALIDATION: PASSED")
            lines.append("   Perfect P&L reconciliation")
        else:
            lines.append("❌ ACCOUNTING VALIDATION: FAILED")
            lines.append(f"   Discrepancy of ${discrepancy:+,.2f} requires investigation")
        
        lines.append("")
        lines.append("📁 LOG FILES GENERATED:")
        lines.append(f"   Trade Log: logs/trades_{self.session_id}.csv")
        lines.append(f"   Balance Log: logs/balance_progression_{self.session_id}.csv")
        lines.append(f"   Daily Log: logs/daily_performance_{self.session_id}.csv")
        lines.append(f"   Market Log: logs/market_conditions_{self.session_id}.csv")
        lines.append(f"   Report: logs/BACKTEST_REPORT_{self.session_id}.txt")
        
        lines.append("")
        lines.append("=" * 100)
        lines.append("END OF REPORT")
        lines.append("=" * 100)
        
        return lines

def generate_backtest_report(session_id: str) -> str:
    """Generate comprehensive backtest report"""
    reporter = ComprehensiveBacktestReport(session_id)
    return reporter.generate_complete_report()

if __name__ == "__main__":
    # Test with latest session
    import sys
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        # Find latest session
        import glob
        trade_files = glob.glob("logs/trades_*.csv")
        if trade_files:
            latest_file = max(trade_files)
            session_id = latest_file.split("_")[1].split(".")[0]
        else:
            print("No trade files found")
            sys.exit(1)
    
    report_path = generate_backtest_report(session_id)
    print(f"Report generated: {report_path}")
