#!/usr/bin/env python3
"""
Long Iron Condor Strategy Test - Buying Instead of Selling
=========================================================

Test the Long Iron Condor strategy (buying instead of selling) to address
the performance issue where short Iron Condors had high win rate but net losses.

Long Iron Condor Structure:
- Buy Put (higher strike) + Sell Put (lower strike)
- Buy Call (lower strike) + Sell Call (higher strike)
- Net Debit paid (instead of credit received)
- Profits from large moves in either direction
- Limited risk (debit paid)

This should perform better in high volatility environments.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time, date
from typing import Dict, List, Optional, Tuple, Any
import warnings
import random
warnings.filterwarnings('ignore')

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import our components
try:
    from src.data.parquet_data_loader import ParquetDataLoader
    from src.strategies.cash_management.position_sizer import ConservativeCashManager, Position
    from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
    from src.utils.detailed_logger import DetailedLogger, TradeLogEntry, MarketConditionEntry
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_AVAILABLE = False

class LongIronCondorBacktester:
    """
    Backtester specifically for Long Iron Condor strategy
    
    Key Differences from Short Iron Condor:
    1. Pay debit instead of receive credit
    2. Profit from large moves instead of sideways moves
    3. Limited risk (debit paid) instead of large potential loss
    """
    
    def __init__(self, initial_balance: float = 25000):
        if not IMPORTS_AVAILABLE:
            raise ImportError("Required modules not available")
        
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Initialize components
        self.data_loader = ParquetDataLoader(parquet_path="src/data/spy_options_20230830_20240829.parquet")
        self.cash_manager = ConservativeCashManager(initial_balance)
        self.pricing_calculator = BlackScholesCalculator()
        self.logger = DetailedLogger()
        
        # Trading parameters for Long Iron Condor
        self.max_positions = 2
        self.profit_target_pct = 2.0  # 200% of debit paid (aggressive for long strategies)
        self.stop_loss_pct = 0.5     # 50% of debit paid (limit losses)
        
        # Position tracking
        self.open_positions: List[Dict] = []
        self.total_trades = 0
        self.winning_trades = 0
        
        print("🚀 LONG IRON CONDOR BACKTESTER INITIALIZED")
        print(f"   Initial Balance: ${initial_balance:,.2f}")
        print(f"   Strategy: BUY Iron Condors (profit from big moves)")
        print(f"   Profit Target: {self.profit_target_pct*100}% of debit")
        print(f"   Stop Loss: {self.stop_loss_pct*100}% of debit")
    
    def _execute_long_iron_condor(self, options_data: pd.DataFrame, spy_price: float,
                                 trading_date: datetime, entry_time: time) -> bool:
        """Execute Long Iron Condor trade (BUY the spread)"""
        
        if len(self.open_positions) >= self.max_positions:
            return False
        
        # Long Iron Condor strikes (wider spread to ensure net debit)
        # Structure: Buy ATM options, Sell OTM options
        put_long_strike = spy_price - 2   # Buy put (closer to ATM)
        put_short_strike = spy_price - 10 # Sell put (further OTM)
        call_short_strike = spy_price + 10 # Sell call (further OTM)
        call_long_strike = spy_price + 2  # Buy call (closer to ATM)
        
        # Calculate theoretical prices using Black-Scholes
        try:
            # Long positions (we buy these)
            put_long_price = self.pricing_calculator.calculate_option_price(
                spy_price, put_long_strike, 0.0274, 0.25, 'put'
            )
            call_long_price = self.pricing_calculator.calculate_option_price(
                spy_price, call_long_strike, 0.0274, 0.25, 'call'
            )
            
            # Short positions (we sell these)
            put_short_price = self.pricing_calculator.calculate_option_price(
                spy_price, put_short_strike, 0.0274, 0.25, 'put'
            )
            call_short_price = self.pricing_calculator.calculate_option_price(
                spy_price, call_short_strike, 0.0274, 0.25, 'call'
            )
            
            # Net debit = (Long positions) - (Short positions)
            net_debit = (put_long_price + call_long_price) - (put_short_price + call_short_price)
            
            if net_debit <= 0:
                print(f"   ❌ Invalid Long Iron Condor: Net debit = ${net_debit:.2f}")
                return False
                
        except Exception as e:
            print(f"   ❌ Pricing error: {e}")
            return False
        
        # Position sizing
        contracts = 5  # Standard size
        total_debit = net_debit * contracts * 100  # Total cost
        max_profit = (2.0 * 100 * contracts) - total_debit  # Max spread width - debit
        
        # Check if we can afford the position (simplified check)
        available_cash = self.cash_manager.calculate_available_cash()
        if total_debit > available_cash:
            print(f"   ❌ Insufficient cash for Long Iron Condor: Need ${total_debit:.2f}, Have ${available_cash:.2f}")
            return False
        
        # Create trade ID
        trade_id = f"LONG_IC_{trading_date.strftime('%Y%m%d')}_{entry_time.strftime('%H%M%S')}"
        
        # Log the trade entry
        trade_entry = TradeLogEntry(
            trade_id=trade_id,
            strategy_type='LONG_IRON_CONDOR',
            entry_date=trading_date.strftime('%Y-%m-%d'),
            entry_time=entry_time.strftime('%H:%M:%S'),
            spy_price_entry=spy_price,
            market_regime='NEUTRAL',
            volatility_level='HIGH',
            contracts=contracts,
            put_short_strike=put_short_strike,
            put_long_strike=put_long_strike,
            call_short_strike=call_short_strike,
            call_long_strike=call_long_strike,
            entry_debit=total_debit,
            max_risk=total_debit,  # Limited risk = debit paid
            max_profit=max_profit,
            profit_target=total_debit * self.profit_target_pct,
            stop_loss=total_debit * self.stop_loss_pct,
            account_balance_before=self.current_balance,
            account_balance_after=self.current_balance - total_debit,
            cash_used=total_debit,
            selection_reasoning="Long Iron Condor for high volatility - profit from big moves"
        )
        
        # Add to cash manager
        self.cash_manager.add_position(
            position_id=trade_id,
            strategy_type='LONG_IRON_CONDOR',
            cash_requirement=total_debit,
            max_loss=total_debit,
            max_profit=max_profit,
            strikes={
                'put_long': put_long_strike,
                'put_short': put_short_strike,
                'call_short': call_short_strike,
                'call_long': call_long_strike
            }
        )
        
        # Create position tracking
        position = {
            'trade_id': trade_id,
            'strategy_type': 'LONG_IRON_CONDOR',
            'entry_date': trading_date,
            'entry_time': entry_time,
            'contracts': contracts,
            'debit_paid': total_debit,
            'max_risk': total_debit,
            'max_profit': max_profit,
            'profit_target': total_debit * self.profit_target_pct,
            'stop_loss': total_debit * self.stop_loss_pct,
            'spy_price_entry': spy_price,
            'strikes': {
                'put_long': put_long_strike,
                'put_short': put_short_strike,
                'call_short': call_short_strike,
                'call_long': call_long_strike
            }
        }
        
        self.open_positions.append(position)
        
        # Log the trade
        self.logger.log_trade_entry(trade_entry)
        
        # Update balance (pay the debit)
        self.current_balance -= total_debit
        self.logger.log_balance_update(
            timestamp=f"{trading_date.strftime('%Y-%m-%d')} {entry_time.strftime('%H:%M:%S')}",
            balance=self.current_balance,
            change=-total_debit,
            reason=f"LONG_IRON_CONDOR_ENTRY_{trade_id}"
        )
        
        print(f"   ✅ LONG IRON CONDOR OPENED")
        print(f"      Trade ID: {trade_id}")
        print(f"      Debit Paid: ${total_debit:.2f}")
        print(f"      Max Risk: ${total_debit:.2f}")
        print(f"      Max Profit: ${max_profit:.2f}")
        
        return True
    
    def _close_positions(self, trading_date: datetime, spy_price: float) -> None:
        """Close positions based on profit/loss targets or time decay"""
        
        positions_to_close = []
        
        for position in self.open_positions:
            # Calculate current value of the Long Iron Condor
            current_value = self._calculate_position_value(position, spy_price)
            
            # P&L = Current Value - Debit Paid
            pnl = current_value - position['debit_paid']
            
            # Check exit conditions
            exit_reason = None
            
            if pnl >= position['profit_target']:
                exit_reason = 'PROFIT_TARGET'
            elif pnl <= -position['stop_loss']:
                exit_reason = 'STOP_LOSS'
            else:
                # Time-based exit (end of day for 0DTE)
                exit_reason = 'TIME_EXIT'
            
            if exit_reason:
                positions_to_close.append((position, exit_reason, pnl, current_value))
        
        # Close positions
        for position, exit_reason, pnl, current_value in positions_to_close:
            self._close_position(position, exit_reason, pnl, current_value, trading_date, spy_price)
    
    def _calculate_position_value(self, position: Dict, spy_price: float) -> float:
        """Calculate current value of Long Iron Condor position"""
        
        strikes = position['strikes']
        
        try:
            # Calculate current option prices
            put_long_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['put_long'], 0.0137, 0.25, 'put'  # Shorter time
            )
            call_long_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['call_long'], 0.0137, 0.25, 'call'
            )
            put_short_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['put_short'], 0.0137, 0.25, 'put'
            )
            call_short_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['call_short'], 0.0137, 0.25, 'call'
            )
            
            # Current value = (Long positions) - (Short positions)
            current_value = (put_long_price + call_long_price) - (put_short_price + call_short_price)
            current_value *= position['contracts'] * 100
            
            return max(0, current_value)  # Can't be negative
            
        except Exception as e:
            print(f"   ❌ Error calculating position value: {e}")
            return 0
    
    def _close_position(self, position: Dict, exit_reason: str, pnl: float, 
                       current_value: float, trading_date: datetime, spy_price: float) -> None:
        """Close a Long Iron Condor position"""
        
        # Remove from cash manager
        self.cash_manager.remove_position(position['trade_id'])
        
        # Update balance (receive current value)
        self.current_balance += current_value
        
        # Update statistics
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        
        # Log the exit
        return_pct = (pnl / position['debit_paid']) * 100
        
        print(f"   🔚 POSITION CLOSED: {position['trade_id']}")
        print(f"      Exit Reason: {exit_reason}")
        print(f"      P&L: ${pnl:+.2f}")
        print(f"      Return: {return_pct:+.2f}%")
        print(f"      New Balance: ${self.current_balance:.2f}")
        
        # Remove from open positions
        self.open_positions.remove(position)
        
        # Log balance update
        self.logger.log_balance_update(
            timestamp=f"{trading_date.strftime('%Y-%m-%d')} 16:00:00",
            balance=self.current_balance,
            change=pnl,
            reason=f"LONG_IRON_CONDOR_EXIT_{position['trade_id']}"
        )
    
    def run_backtest(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Run Long Iron Condor backtest"""
        
        print("\n🚀 STARTING LONG IRON CONDOR BACKTEST")
        print("="*60)
        print(f"Period: {start_date} to {end_date}")
        print("Strategy: BUY Iron Condors (profit from volatility)")
        print()
        
        # Get trading dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        available_dates = self.data_loader.get_available_dates(start_dt, end_dt)
        
        print(f"📅 Found {len(available_dates)} trading days")
        
        # Process each trading day
        for i, trading_date in enumerate(available_dates, 1):
            print(f"\n📊 PROCESSING DAY {i}/{len(available_dates)}: {trading_date.strftime('%Y-%m-%d')}")
            
            # Load options data
            options_data = self.data_loader.load_options_for_date(trading_date)
            
            if options_data.empty:
                print(f"   ❌ No options data for {trading_date.strftime('%Y-%m-%d')}")
                continue
            
            # Estimate SPY price
            spy_price = float(options_data['strike'].median())
            
            print(f"   📊 SPY Price: ${spy_price:.2f}")
            print(f"   📊 Options Available: {len(options_data):,}")
            
            # Close existing positions first
            if self.open_positions:
                self._close_positions(trading_date, spy_price)
            
            # Open new Long Iron Condor positions (2 per day)
            entry_times = [time(10, 0), time(11, 30)]
            
            for entry_time in entry_times:
                if len(self.open_positions) < self.max_positions:
                    self._execute_long_iron_condor(options_data, spy_price, trading_date, entry_time)
        
        # Close any remaining positions
        if self.open_positions and available_dates:
            final_date = available_dates[-1]
            final_spy = 550.0  # Approximate
            for position in self.open_positions.copy():
                current_value = self._calculate_position_value(position, final_spy)
                pnl = current_value - position['debit_paid']
                self._close_position(position, 'EOD_EXIT', pnl, current_value, final_date, final_spy)
        
        # Generate results
        total_pnl = self.current_balance - self.initial_balance
        total_return_pct = (total_pnl / self.initial_balance) * 100
        win_rate = (self.winning_trades / max(self.total_trades, 1)) * 100
        
        results = {
            'strategy': 'LONG_IRON_CONDOR',
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'log_files': {
                'trades': str(self.logger.trade_log_path),
                'balance': str(self.logger.balance_log_path)
            }
        }
        
        return results

def main():
    """Run Long Iron Condor test"""
    
    print("🧪 LONG IRON CONDOR STRATEGY TEST")
    print("="*50)
    print("Testing BUYING Iron Condors instead of SELLING")
    print("Expected: Better performance in high volatility")
    print()
    
    # Initialize backtester
    backtester = LongIronCondorBacktester(initial_balance=25000)
    
    # Run 1-week test
    results = backtester.run_backtest(
        start_date="2024-07-01",
        end_date="2024-07-05"
    )
    
    print("\n" + "="*60)
    print("📊 LONG IRON CONDOR RESULTS")
    print("="*60)
    
    print(f"\n💰 FINANCIAL PERFORMANCE:")
    print(f"   Initial Balance: ${results['initial_balance']:,.2f}")
    print(f"   Final Balance: ${results['final_balance']:,.2f}")
    print(f"   Total P&L: ${results['total_pnl']:+,.2f}")
    print(f"   Total Return: {results['total_return_pct']:+.2f}%")
    
    print(f"\n📈 TRADING STATISTICS:")
    print(f"   Total Trades: {results['total_trades']}")
    print(f"   Winning Trades: {results['winning_trades']}")
    print(f"   Win Rate: {results['win_rate']:.1f}%")
    
    print(f"\n🎯 STRATEGY COMPARISON:")
    print(f"   Long Iron Condor: Profit from BIG moves")
    print(f"   Short Iron Condor: Profit from SMALL moves")
    print(f"   High Volatility Environment: Long should outperform")
    
    print(f"\n📁 DETAILED LOGS:")
    print(f"   Trade Log: {results['log_files']['trades']}")
    print(f"   Balance Log: {results['log_files']['balance']}")
    
    return results

if __name__ == "__main__":
    main()
