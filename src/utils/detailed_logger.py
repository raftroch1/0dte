#!/usr/bin/env python3
"""
Detailed Logging System - Comprehensive Trade and Performance Tracking
=====================================================================

COMPREHENSIVE LOGGING FOR:
1. Trade-by-trade detailed logs (CSV format)
2. Market condition analysis logging
3. Strategy selection reasoning
4. Real-time balance progression
5. P&L breakdown by strategy type
6. Performance metrics with timestamps

This addresses the user's request for detailed log files and clear results.

Location: src/utils/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Detailed Logging System
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
import os
import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class TradeLogEntry:
    """Comprehensive trade log entry with all details"""
    # Trade Identification
    trade_id: str
    strategy_type: str  # 'IRON_CONDOR', 'BULL_PUT_SPREAD', etc.
    entry_date: str
    entry_time: str
    exit_date: Optional[str] = None
    exit_time: Optional[str] = None
    
    # Market Conditions at Entry
    spy_price_entry: float = 0.0
    vix_level: Optional[float] = None
    market_regime: str = "UNKNOWN"  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    volatility_level: str = "UNKNOWN"  # 'LOW', 'MEDIUM', 'HIGH'
    put_call_ratio: Optional[float] = None
    total_volume: Optional[int] = None
    
    # Position Details
    contracts: int = 0
    
    # Iron Condor Specific
    put_short_strike: Optional[float] = None
    put_long_strike: Optional[float] = None
    call_short_strike: Optional[float] = None
    call_long_strike: Optional[float] = None
    
    # Spread Specific (for Bull/Bear spreads)
    short_strike: Optional[float] = None
    long_strike: Optional[float] = None
    spread_type: Optional[str] = None  # 'PUT', 'CALL'
    
    # Financial Details
    entry_credit: float = 0.0
    entry_debit: float = 0.0
    max_risk: float = 0.0
    max_profit: float = 0.0
    profit_target: float = 0.0
    stop_loss: float = 0.0
    
    # Exit Details
    exit_reason: Optional[str] = None  # 'PROFIT_TARGET', 'STOP_LOSS', 'TIME_EXIT', 'EOD_EXIT'
    spy_price_exit: Optional[float] = None
    exit_credit: Optional[float] = None
    exit_debit: Optional[float] = None
    
    # Performance
    realized_pnl: float = 0.0
    return_pct: float = 0.0
    hold_time_hours: float = 0.0
    
    # Account Impact
    account_balance_before: float = 0.0
    account_balance_after: float = 0.0
    cash_used: float = 0.0
    
    # Strategy Selection Reasoning
    selection_confidence: float = 0.0
    selection_reasoning: str = ""
    intelligence_score: Optional[float] = None

@dataclass
class DailyPerformanceEntry:
    """Daily performance summary"""
    date: str
    starting_balance: float
    ending_balance: float
    daily_pnl: float
    daily_return_pct: float
    trades_opened: int
    trades_closed: int
    winning_trades: int
    losing_trades: int
    total_volume_traded: int
    max_intraday_drawdown: float
    strategies_used: List[str]
    market_conditions: str

@dataclass
class MarketConditionEntry:
    """Market condition analysis log"""
    timestamp: str
    spy_price: float
    vix_level: Optional[float]
    put_call_ratio: Optional[float]
    total_volume: Optional[int]
    detected_regime: str
    regime_confidence: float
    volatility_level: str
    momentum_strength: str
    trend_direction: str
    flat_market_detected: bool
    reasoning: str
    strategies_recommended: List[str]
    intelligence_score: Optional[float]

class DetailedLogger:
    """
    Comprehensive logging system for trading operations
    
    Features:
    1. CSV trade logs with complete details
    2. Daily performance summaries
    3. Market condition analysis logs
    4. Real-time balance tracking
    5. Strategy selection reasoning
    6. Performance analytics
    """
    
    def __init__(self, log_directory: str = "logs"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        
        # Initialize log files
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Trade log
        self.trade_log_path = self.log_directory / f"trades_{self.session_id}.csv"
        self.trade_log_entries: List[TradeLogEntry] = []
        
        # Daily performance log
        self.daily_log_path = self.log_directory / f"daily_performance_{self.session_id}.csv"
        self.daily_entries: List[DailyPerformanceEntry] = []
        
        # Market condition log
        self.market_log_path = self.log_directory / f"market_conditions_{self.session_id}.csv"
        self.market_entries: List[MarketConditionEntry] = []
        
        # Balance tracking
        self.balance_log_path = self.log_directory / f"balance_progression_{self.session_id}.csv"
        self.balance_entries: List[Dict] = []
        
        # Session summary
        self.summary_path = self.log_directory / f"session_summary_{self.session_id}.json"
        
        print(f"📊 DETAILED LOGGER INITIALIZED")
        print(f"   Session ID: {self.session_id}")
        print(f"   Log Directory: {self.log_directory}")
        print(f"   Trade Log: {self.trade_log_path.name}")
        print(f"   Daily Log: {self.daily_log_path.name}")
        print(f"   Market Log: {self.market_log_path.name}")
        print(f"   Balance Log: {self.balance_log_path.name}")
    
    def log_trade_entry(self, trade_entry: TradeLogEntry):
        """Log a new trade entry"""
        self.trade_log_entries.append(trade_entry)
        self._write_trade_to_csv(trade_entry)
        
        print(f"📝 TRADE LOGGED: {trade_entry.trade_id}")
        print(f"   Strategy: {trade_entry.strategy_type}")
        print(f"   Entry: {trade_entry.entry_date} {trade_entry.entry_time}")
        print(f"   Contracts: {trade_entry.contracts}")
        print(f"   Max Risk: ${trade_entry.max_risk:,.2f}")
        print(f"   Max Profit: ${trade_entry.max_profit:,.2f}")
    
    def log_trade_exit(self, trade_id: str, exit_data: Dict[str, Any]):
        """Update trade with exit information"""
        # Find and update the trade entry
        for entry in self.trade_log_entries:
            if entry.trade_id == trade_id:
                entry.exit_date = exit_data.get('exit_date')
                entry.exit_time = exit_data.get('exit_time')
                entry.exit_reason = exit_data.get('exit_reason')
                entry.spy_price_exit = exit_data.get('spy_price_exit')
                entry.exit_credit = exit_data.get('exit_credit')
                entry.exit_debit = exit_data.get('exit_debit')
                entry.realized_pnl = exit_data.get('realized_pnl', 0.0)
                entry.return_pct = exit_data.get('return_pct', 0.0)
                entry.hold_time_hours = exit_data.get('hold_time_hours', 0.0)
                entry.account_balance_after = exit_data.get('account_balance_after', 0.0)
                
                # Rewrite the CSV with updated data
                self._rewrite_trade_csv()
                
                print(f"📝 TRADE EXIT LOGGED: {trade_id}")
                print(f"   Exit Reason: {entry.exit_reason}")
                print(f"   P&L: ${entry.realized_pnl:+,.2f}")
                print(f"   Return: {entry.return_pct:+.2f}%")
                print(f"   Hold Time: {entry.hold_time_hours:.1f} hours")
                break
    
    def log_market_conditions(self, market_entry: MarketConditionEntry):
        """Log market condition analysis"""
        self.market_entries.append(market_entry)
        self._write_market_to_csv(market_entry)
        
        print(f"🌍 MARKET CONDITIONS LOGGED: {market_entry.timestamp}")
        print(f"   Regime: {market_entry.detected_regime} ({market_entry.regime_confidence:.1f}%)")
        print(f"   Volatility: {market_entry.volatility_level}")
        print(f"   Strategies: {', '.join(market_entry.strategies_recommended)}")
    
    def log_balance_update(self, timestamp: str, balance: float, change: float, reason: str):
        """Log balance progression"""
        balance_entry = {
            'timestamp': timestamp,
            'balance': balance,
            'change': change,
            'reason': reason,
            'cumulative_return': ((balance - self.get_initial_balance()) / self.get_initial_balance() * 100) if self.get_initial_balance() > 0 else 0
        }
        
        self.balance_entries.append(balance_entry)
        self._write_balance_to_csv(balance_entry)
        
        print(f"💰 BALANCE UPDATE: ${balance:,.2f} ({change:+.2f}) - {reason}")
    
    def log_daily_performance(self, daily_entry: DailyPerformanceEntry):
        """Log daily performance summary"""
        self.daily_entries.append(daily_entry)
        self._write_daily_to_csv(daily_entry)
        
        print(f"📈 DAILY PERFORMANCE: {daily_entry.date}")
        print(f"   P&L: ${daily_entry.daily_pnl:+,.2f} ({daily_entry.daily_return_pct:+.2f}%)")
        print(f"   Trades: {daily_entry.trades_opened} opened, {daily_entry.trades_closed} closed")
        print(f"   Win Rate: {(daily_entry.winning_trades / max(daily_entry.trades_closed, 1) * 100):.1f}%")
    
    def generate_session_summary(self) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        
        if not self.trade_log_entries:
            return {"error": "No trades logged"}
        
        # 🚨 FIX: PROPER P&L CALCULATION
        # Calculate performance metrics from COMPLETED trades only
        completed_trades = [t for t in self.trade_log_entries if t.realized_pnl != 0 and t.exit_date]
        total_trades = len(completed_trades)
        winning_trades = len([t for t in completed_trades if t.realized_pnl > 0])
        losing_trades = len([t for t in completed_trades if t.realized_pnl < 0])
        
        initial_balance = self.get_initial_balance()
        final_balance = self.get_final_balance()
        
        # P&L from balance difference (the TRUTH)
        actual_pnl = final_balance - initial_balance
        
        # 🚨 FIX: PROPER P&L VALIDATION
        # P&L from individual trades (these are NET P&L already)
        trade_pnl_sum = sum(t.realized_pnl for t in completed_trades)
        
        # Use actual P&L (balance difference) as the authoritative source
        total_pnl = actual_pnl
        total_return = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0
        
        # 🚨 CORRECTED VALIDATION: Both values should match since both are NET P&L
        pnl_discrepancy = abs(actual_pnl - trade_pnl_sum)
        if pnl_discrepancy > 1.0:
            print(f"⚠️  P&L DISCREPANCY: Actual ${actual_pnl:+.2f} vs Trade Sum ${trade_pnl_sum:+.2f} (Diff: ${pnl_discrepancy:+.2f})")
            print(f"   NOTE: Both values are NET P&L and should match exactly")
        else:
            print(f"✅ P&L VALIDATION PASSED: Actual ${actual_pnl:+.2f} matches Trade Sum ${trade_pnl_sum:+.2f}")
        
        # Strategy breakdown (completed trades only)
        strategy_stats = {}
        for trade in completed_trades:  # Use completed_trades instead of all trades
            if trade.strategy_type not in strategy_stats:
                strategy_stats[trade.strategy_type] = {
                    'count': 0, 'total_pnl': 0, 'wins': 0, 'losses': 0
                }
            strategy_stats[trade.strategy_type]['count'] += 1
            strategy_stats[trade.strategy_type]['total_pnl'] += trade.realized_pnl
            if trade.realized_pnl > 0:
                strategy_stats[trade.strategy_type]['wins'] += 1
            elif trade.realized_pnl < 0:
                strategy_stats[trade.strategy_type]['losses'] += 1
        
        summary = {
            'session_id': self.session_id,
            'start_time': self.trade_log_entries[0].entry_date if self.trade_log_entries else None,
            'end_time': datetime.now().isoformat(),
            'performance': {
                'initial_balance': initial_balance,
                'final_balance': final_balance,
                'total_pnl': total_pnl,
                'total_return_pct': total_return,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate_pct': (winning_trades / max(total_trades, 1) * 100),
                'avg_trade_pnl': trade_pnl_sum / max(total_trades, 1),  # Use trade sum for average
                'trade_pnl_sum': trade_pnl_sum,  # Add for validation
                'pnl_discrepancy': pnl_discrepancy,  # Add for debugging
                'pnl_validation_passed': pnl_discrepancy <= 1.0,  # Add validation flag
                'best_trade': max((t.realized_pnl for t in completed_trades), default=0),
                'worst_trade': min((t.realized_pnl for t in completed_trades), default=0)
            },
            'strategy_breakdown': strategy_stats,
            'files_generated': {
                'trade_log': str(self.trade_log_path),
                'daily_log': str(self.daily_log_path),
                'market_log': str(self.market_log_path),
                'balance_log': str(self.balance_log_path)
            }
        }
        
        # Save summary to JSON
        with open(self.summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return summary
    
    def get_initial_balance(self) -> float:
        """Get initial balance from first balance entry (INITIAL_BALANCE)"""
        # 🚨 FIX: Look for INITIAL_BALANCE entry, not first trade balance
        for entry in self.balance_entries:
            if entry.get('reason') == 'INITIAL_BALANCE':
                return entry['balance']
        
        # Fallback: use first balance entry
        if self.balance_entries:
            return self.balance_entries[0]['balance']
        
        # Last resort: use account_balance_before from first trade + cash used
        if self.trade_log_entries:
            first_trade = self.trade_log_entries[0]
            return first_trade.account_balance_before + first_trade.cash_used
        
        return 25000.0  # Default
    
    def get_final_balance(self) -> float:
        """Get final balance from last trade or balance entry"""
        if self.balance_entries:
            return self.balance_entries[-1]['balance']
        elif self.trade_log_entries:
            return max((t.account_balance_after for t in self.trade_log_entries if t.account_balance_after > 0), default=25000.0)
        return 25000.0  # Default
    
    def _write_trade_to_csv(self, trade_entry: TradeLogEntry):
        """Write trade entry to CSV"""
        file_exists = self.trade_log_path.exists()
        
        with open(self.trade_log_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(trade_entry).keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(asdict(trade_entry))
    
    def _rewrite_trade_csv(self):
        """Rewrite entire trade CSV with updated data"""
        if not self.trade_log_entries:
            return
        
        with open(self.trade_log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(self.trade_log_entries[0]).keys()))
            writer.writeheader()
            for entry in self.trade_log_entries:
                writer.writerow(asdict(entry))
    
    def _write_market_to_csv(self, market_entry: MarketConditionEntry):
        """Write market condition entry to CSV"""
        file_exists = self.market_log_path.exists()
        
        # Convert list fields to strings for CSV
        entry_dict = asdict(market_entry)
        entry_dict['strategies_recommended'] = ','.join(market_entry.strategies_recommended)
        
        with open(self.market_log_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(entry_dict.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(entry_dict)
    
    def _write_daily_to_csv(self, daily_entry: DailyPerformanceEntry):
        """Write daily performance entry to CSV"""
        file_exists = self.daily_log_path.exists()
        
        # Convert list fields to strings for CSV
        entry_dict = asdict(daily_entry)
        entry_dict['strategies_used'] = ','.join(daily_entry.strategies_used)
        
        with open(self.daily_log_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(entry_dict.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(entry_dict)
    
    def _write_balance_to_csv(self, balance_entry: Dict):
        """Write balance entry to CSV"""
        file_exists = self.balance_log_path.exists()
        
        with open(self.balance_log_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(balance_entry.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(balance_entry)
    
    def print_session_summary(self):
        """Print comprehensive session summary"""
        summary = self.generate_session_summary()
        
        print("\n" + "="*80)
        print("📊 DETAILED SESSION SUMMARY")
        print("="*80)
        
        perf = summary.get('performance', {})
        print(f"\n💰 FINANCIAL PERFORMANCE:")
        print(f"   Initial Balance: ${perf.get('initial_balance', 0):,.2f}")
        print(f"   Final Balance: ${perf.get('final_balance', 0):,.2f}")
        print(f"   Total P&L: ${perf.get('total_pnl', 0):+,.2f}")
        print(f"   Total Return: {perf.get('total_return_pct', 0):+.2f}%")
        
        print(f"\n📈 TRADING STATISTICS:")
        print(f"   Total Trades: {perf.get('total_trades', 0)}")
        print(f"   Winning Trades: {perf.get('winning_trades', 0)}")
        print(f"   Losing Trades: {perf.get('losing_trades', 0)}")
        print(f"   Win Rate: {perf.get('win_rate_pct', 0):.1f}%")
        print(f"   Average Trade P&L: ${perf.get('avg_trade_pnl', 0):+,.2f}")
        print(f"   Best Trade: ${perf.get('best_trade', 0):+,.2f}")
        print(f"   Worst Trade: ${perf.get('worst_trade', 0):+,.2f}")
        
        print(f"\n🎯 STRATEGY BREAKDOWN:")
        for strategy, stats in summary.get('strategy_breakdown', {}).items():
            win_rate = (stats['wins'] / max(stats['count'], 1) * 100)
            print(f"   {strategy}:")
            print(f"     Trades: {stats['count']}")
            print(f"     P&L: ${stats['total_pnl']:+,.2f}")
            print(f"     Win Rate: {win_rate:.1f}%")
        
        print(f"\n📁 LOG FILES GENERATED:")
        for file_type, file_path in summary.get('files_generated', {}).items():
            print(f"   {file_type}: {file_path}")
        
        print("\n" + "="*80)
        print("📊 SESSION SUMMARY COMPLETE")
        print("="*80)
