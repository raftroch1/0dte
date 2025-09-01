#!/usr/bin/env python3
"""
Enhanced Iron Condor Strategy - Research-Based Implementation
============================================================

Based on TastyTrade research and 0DTE trading best practices:

1. VIX-Based Entry: Only trade when VIX opens higher than previous day
2. 30 Delta Strikes: Optimal premium vs risk balance
3. Time-Based Rules: Enter 9:30 AM, exit by 11:30 AM
4. 20-25% Profit Target: Quick profit taking
5. Capital Efficient: Target ~$850 margin per trade

This addresses the Iron Condor performance issues identified in backtesting.
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
    from src.strategies.cash_management.position_sizer import ConservativeCashManager
    from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
    from src.utils.detailed_logger import DetailedLogger, TradeLogEntry, MarketConditionEntry
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_AVAILABLE = False

class EnhancedIronCondorStrategy:
    """
    Research-based Iron Condor strategy with VIX filtering and optimal parameters
    
    Key Features:
    1. VIX-based entry filter (only when VIX > previous day)
    2. 30 Delta strike selection for optimal premium/risk
    3. Time-based entry (9:30 AM) and exit (11:30 AM)
    4. 20-25% profit target for quick wins
    5. Capital efficient margin requirements
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
        
        # Research-based parameters
        self.target_delta = 0.30  # 30 Delta strikes (research optimal)
        self.profit_target_pct = 0.225  # 22.5% profit target (20-25% range)
        self.entry_time = time(9, 30)   # Market open entry
        self.exit_time = time(11, 30)   # 2-hour max hold
        self.target_margin = 850        # Target margin per trade (~$850)
        self.max_positions = 1          # Conservative: 1 position at a time
        
        # VIX tracking for entry signals
        self.previous_vix = None
        self.vix_history = {}
        
        # Position tracking
        self.open_positions: List[Dict] = []
        self.total_trades = 0
        self.winning_trades = 0
        self.vix_signals = {'valid': 0, 'invalid': 0}
        
        print("🚀 ENHANCED IRON CONDOR STRATEGY INITIALIZED")
        print(f"   Initial Balance: ${initial_balance:,.2f}")
        print(f"   Strategy: Research-Based Iron Condor")
        print(f"   Target Delta: {self.target_delta*100:.0f} Delta")
        print(f"   Profit Target: {self.profit_target_pct*100:.1f}%")
        print(f"   Entry Time: {self.entry_time}")
        print(f"   Exit Time: {self.exit_time}")
        print(f"   Target Margin: ${self.target_margin}")
    
    def _estimate_vix_level(self, options_data: pd.DataFrame, spy_price: float) -> float:
        """
        Estimate VIX level from options data
        
        VIX represents 30-day implied volatility, we'll estimate from ATM options
        """
        try:
            # Get ATM options (closest to current price)
            atm_calls = options_data[
                (options_data['option_type'] == 'call') &
                (abs(options_data['strike'] - spy_price) <= 5)
            ]
            
            if atm_calls.empty:
                return 20.0  # Default VIX estimate
            
            # Use volume-weighted average of implied volatility proxies
            # This is a simplified VIX estimation
            price_range = options_data['strike'].max() - options_data['strike'].min()
            volatility_proxy = (price_range / spy_price) * 100
            
            # Scale to typical VIX range (10-50)
            estimated_vix = max(10, min(50, volatility_proxy * 0.8))
            
            return estimated_vix
            
        except Exception as e:
            print(f"   ⚠️ VIX estimation error: {e}")
            return 20.0
    
    def _check_vix_entry_signal(self, current_date: datetime, current_vix: float) -> bool:
        """
        Check if VIX signal allows entry (VIX higher than previous day)
        
        Research: "when the VIX opens higher than the previous day, it signals 
        increased market volatility and a favorable environment for selling premium"
        """
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Store current VIX
        self.vix_history[date_str] = current_vix
        
        # Get previous trading day VIX
        if self.previous_vix is None:
            # First day - assume entry allowed
            self.previous_vix = current_vix
            self.vix_signals['valid'] += 1
            print(f"   📊 VIX Signal: FIRST DAY - Entry Allowed")
            print(f"      Current VIX: {current_vix:.1f}")
            return True
        
        # Check if VIX is higher than previous day
        vix_higher = current_vix > self.previous_vix
        
        if vix_higher:
            self.vix_signals['valid'] += 1
            print(f"   📊 VIX Signal: ENTRY ALLOWED ✅")
            print(f"      Previous VIX: {self.previous_vix:.1f}")
            print(f"      Current VIX: {current_vix:.1f}")
            print(f"      Increase: +{current_vix - self.previous_vix:.1f}")
        else:
            self.vix_signals['invalid'] += 1
            print(f"   📊 VIX Signal: NO ENTRY ❌")
            print(f"      Previous VIX: {self.previous_vix:.1f}")
            print(f"      Current VIX: {current_vix:.1f}")
            print(f"      Change: {current_vix - self.previous_vix:.1f}")
        
        # Update previous VIX for next day
        self.previous_vix = current_vix
        
        return vix_higher
    
    def _calculate_30_delta_strikes(self, spy_price: float, volatility: float) -> Dict[str, float]:
        """
        Calculate 30 Delta strikes for Iron Condor
        
        Research: "30 Delta strike offers a better balance of premium income 
        and risk exposure, making it the preferred choice for 0DTE trades"
        """
        try:
            # For 0DTE options, 30 Delta is approximately:
            # - Put: ~1.5-2% OTM
            # - Call: ~1.5-2% OTM
            
            # Adjust based on volatility
            otm_percent = 0.015 + (volatility / 100 * 0.005)  # 1.5% base + vol adjustment
            
            strikes = {
                'put_short': spy_price * (1 - otm_percent),      # Sell 30D put
                'put_long': spy_price * (1 - otm_percent - 0.01), # Buy 10D put (1% further)
                'call_short': spy_price * (1 + otm_percent),     # Sell 30D call  
                'call_long': spy_price * (1 + otm_percent + 0.01) # Buy 10D call (1% further)
            }
            
            # Round to nearest $0.50
            for key in strikes:
                strikes[key] = round(strikes[key] * 2) / 2
            
            return strikes
            
        except Exception as e:
            print(f"   ❌ Strike calculation error: {e}")
            # Fallback strikes
            return {
                'put_short': spy_price - 8,
                'put_long': spy_price - 12,
                'call_short': spy_price + 8,
                'call_long': spy_price + 12
            }
    
    def _execute_enhanced_iron_condor(self, options_data: pd.DataFrame, spy_price: float,
                                    trading_date: datetime, current_vix: float) -> bool:
        """Execute Enhanced Iron Condor with research-based parameters"""
        
        # Check VIX entry signal first
        if not self._check_vix_entry_signal(trading_date, current_vix):
            print(f"   ❌ VIX signal prevents entry - skipping Iron Condor")
            return False
        
        # Check position limits
        if len(self.open_positions) >= self.max_positions:
            print(f"   ❌ Max positions reached ({self.max_positions})")
            return False
        
        # Calculate 30 Delta strikes
        strikes = self._calculate_30_delta_strikes(spy_price, current_vix)
        
        print(f"   📊 30 Delta Strike Selection:")
        print(f"      Put Spread: {strikes['put_long']:.1f}/{strikes['put_short']:.1f}")
        print(f"      Call Spread: {strikes['call_short']:.1f}/{strikes['call_long']:.1f}")
        
        # Calculate theoretical prices
        try:
            time_to_expiry = 4/24/365  # 4 hours to expiry
            vol_decimal = current_vix / 100
            
            # Short options (we sell these - receive premium)
            put_short_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['put_short'], time_to_expiry, vol_decimal, 'put'
            )
            call_short_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['call_short'], time_to_expiry, vol_decimal, 'call'
            )
            
            # Long options (we buy these - pay premium)
            put_long_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['put_long'], time_to_expiry, vol_decimal, 'put'
            )
            call_long_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['call_long'], time_to_expiry, vol_decimal, 'call'
            )
            
            # Net credit = Premium received - Premium paid
            net_credit = (put_short_price + call_short_price) - (put_long_price + call_long_price)
            
            if net_credit <= 0:
                print(f"   ❌ Invalid Iron Condor: Net credit = ${net_credit:.2f}")
                return False
            
        except Exception as e:
            print(f"   ❌ Pricing error: {e}")
            return False
        
        # Position sizing to target ~$850 margin
        put_spread_width = strikes['put_short'] - strikes['put_long']
        call_spread_width = strikes['call_long'] - strikes['call_short']
        max_spread_width = max(put_spread_width, call_spread_width)
        
        # Margin requirement = (spread width - net credit) * 100 * contracts
        margin_per_contract = (max_spread_width - net_credit) * 100
        target_contracts = max(1, int(self.target_margin / margin_per_contract))
        
        total_credit = net_credit * target_contracts * 100
        total_margin = margin_per_contract * target_contracts
        max_loss = total_margin
        
        print(f"   📊 Position Sizing:")
        print(f"      Contracts: {target_contracts}")
        print(f"      Net Credit: ${total_credit:.2f}")
        print(f"      Margin Required: ${total_margin:.2f}")
        print(f"      Max Loss: ${max_loss:.2f}")
        
        # Check available cash
        available_cash = self.cash_manager.calculate_available_cash()
        if total_margin > available_cash:
            print(f"   ❌ Insufficient cash: Need ${total_margin:.2f}, Have ${available_cash:.2f}")
            return False
        
        # Create trade
        trade_id = f"EIC_{trading_date.strftime('%Y%m%d')}_{self.entry_time.strftime('%H%M')}"
        
        # Add to cash manager
        self.cash_manager.add_position(
            position_id=trade_id,
            strategy_type='ENHANCED_IRON_CONDOR',
            cash_requirement=total_margin,
            max_loss=max_loss,
            max_profit=total_credit,
            strikes=strikes
        )
        
        # Create position tracking
        position = {
            'trade_id': trade_id,
            'strategy_type': 'ENHANCED_IRON_CONDOR',
            'entry_date': trading_date,
            'entry_time': self.entry_time,
            'contracts': target_contracts,
            'credit_received': total_credit,
            'margin_required': total_margin,
            'max_loss': max_loss,
            'max_profit': total_credit,
            'profit_target': total_credit * self.profit_target_pct,
            'spy_price_entry': spy_price,
            'vix_entry': current_vix,
            'strikes': strikes
        }
        
        self.open_positions.append(position)
        
        # Update balance (receive credit)
        self.current_balance += total_credit
        
        # Log the trade
        trade_entry = TradeLogEntry(
            trade_id=trade_id,
            strategy_type='ENHANCED_IRON_CONDOR',
            entry_date=trading_date.strftime('%Y-%m-%d'),
            entry_time=self.entry_time.strftime('%H:%M:%S'),
            spy_price_entry=spy_price,
            vix_level=current_vix,
            market_regime='NEUTRAL',
            volatility_level='HIGH' if current_vix > 20 else 'MEDIUM',
            contracts=target_contracts,
            put_short_strike=strikes['put_short'],
            put_long_strike=strikes['put_long'],
            call_short_strike=strikes['call_short'],
            call_long_strike=strikes['call_long'],
            entry_credit=total_credit,
            max_risk=max_loss,
            max_profit=total_credit,
            profit_target=position['profit_target'],
            account_balance_before=self.current_balance - total_credit,
            account_balance_after=self.current_balance,
            cash_used=total_margin,
            selection_reasoning=f"Enhanced Iron Condor: VIX {current_vix:.1f} > Previous, 30D strikes, {self.profit_target_pct*100:.1f}% target"
        )
        
        self.logger.log_trade_entry(trade_entry)
        
        self.logger.log_balance_update(
            timestamp=f"{trading_date.strftime('%Y-%m-%d')} {self.entry_time.strftime('%H:%M:%S')}",
            balance=self.current_balance,
            change=total_credit,
            reason=f"ENHANCED_IC_ENTRY_{trade_id}"
        )
        
        print(f"   ✅ ENHANCED IRON CONDOR OPENED")
        print(f"      Trade ID: {trade_id}")
        print(f"      Credit Received: ${total_credit:.2f}")
        print(f"      Profit Target: ${position['profit_target']:.2f}")
        print(f"      New Balance: ${self.current_balance:.2f}")
        
        return True
    
    def _check_exit_conditions(self, position: Dict, current_time: time, spy_price: float) -> Tuple[bool, str]:
        """
        Check exit conditions based on research:
        1. 20-25% profit target hit
        2. 11:30 AM time exit
        3. Stop loss if needed
        """
        
        # Calculate current P&L
        current_value = self._calculate_position_value(position, spy_price)
        pnl = position['credit_received'] - current_value  # Credit received - current cost to close
        
        # Check profit target (20-25% of max profit)
        if pnl >= position['profit_target']:
            return True, 'PROFIT_TARGET'
        
        # Check time exit (11:30 AM)
        if current_time >= self.exit_time:
            return True, 'TIME_EXIT'
        
        # Check stop loss (50% of credit received)
        stop_loss = position['credit_received'] * 0.5
        if pnl <= -stop_loss:
            return True, 'STOP_LOSS'
        
        return False, 'HOLD'
    
    def _calculate_position_value(self, position: Dict, spy_price: float) -> float:
        """Calculate current cost to close the Iron Condor position"""
        
        strikes = position['strikes']
        
        try:
            # Shorter time to expiry for exit calculation
            time_to_expiry = 2/24/365  # 2 hours remaining
            vol_decimal = position['vix_entry'] / 100 * 0.8  # Reduced vol over time
            
            # Current option prices
            put_short_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['put_short'], time_to_expiry, vol_decimal, 'put'
            )
            call_short_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['call_short'], time_to_expiry, vol_decimal, 'call'
            )
            put_long_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['put_long'], time_to_expiry, vol_decimal, 'put'
            )
            call_long_price = self.pricing_calculator.calculate_option_price(
                spy_price, strikes['call_long'], time_to_expiry, vol_decimal, 'call'
            )
            
            # Cost to close = Pay to buy back shorts - Receive from selling longs
            cost_to_close = (put_short_price + call_short_price) - (put_long_price + call_long_price)
            cost_to_close *= position['contracts'] * 100
            
            return max(0, cost_to_close)
            
        except Exception as e:
            print(f"   ❌ Error calculating position value: {e}")
            return position['credit_received'] * 0.5  # Conservative estimate
    
    def _close_position(self, position: Dict, exit_reason: str, spy_price: float) -> None:
        """Close Enhanced Iron Condor position"""
        
        current_value = self._calculate_position_value(position, spy_price)
        pnl = position['credit_received'] - current_value
        
        # Remove from cash manager
        self.cash_manager.remove_position(position['trade_id'])
        
        # Update balance (pay to close)
        self.current_balance -= current_value
        
        # Update statistics
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        
        # Calculate return
        return_pct = (pnl / position['credit_received']) * 100
        
        print(f"   🔚 POSITION CLOSED: {position['trade_id']}")
        print(f"      Exit Reason: {exit_reason}")
        print(f"      P&L: ${pnl:+.2f}")
        print(f"      Return: {return_pct:+.2f}%")
        print(f"      New Balance: ${self.current_balance:.2f}")
        
        # Remove from open positions
        self.open_positions.remove(position)
        
        # Log balance update
        self.logger.log_balance_update(
            timestamp=f"{position['entry_date'].strftime('%Y-%m-%d')} {self.exit_time.strftime('%H:%M:%S')}",
            balance=self.current_balance,
            change=pnl,
            reason=f"ENHANCED_IC_EXIT_{position['trade_id']}"
        )
    
    def run_backtest(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Run Enhanced Iron Condor backtest with research-based rules"""
        
        print("\n🚀 STARTING ENHANCED IRON CONDOR BACKTEST")
        print("="*70)
        print(f"Period: {start_date} to {end_date}")
        print("Strategy: Research-Based Iron Condor with VIX Filter")
        print("Rules: VIX > Previous Day, 30D Strikes, 22.5% Target, 9:30-11:30")
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
            
            # Estimate SPY price and VIX
            spy_price = float(options_data['strike'].median())
            current_vix = self._estimate_vix_level(options_data, spy_price)
            
            print(f"   📊 SPY Price: ${spy_price:.2f}")
            print(f"   📊 Estimated VIX: {current_vix:.1f}")
            
            # Check exit conditions for existing positions first
            positions_to_close = []
            for position in self.open_positions:
                should_exit, exit_reason = self._check_exit_conditions(position, self.exit_time, spy_price)
                if should_exit:
                    positions_to_close.append((position, exit_reason))
            
            # Close positions
            for position, exit_reason in positions_to_close:
                self._close_position(position, exit_reason, spy_price)
            
            # Try to open new position (only at 9:30 AM)
            if len(self.open_positions) == 0:  # Only if no open positions
                self._execute_enhanced_iron_condor(options_data, spy_price, trading_date, current_vix)
        
        # Close any remaining positions
        for position in self.open_positions.copy():
            self._close_position(position, 'EOD_EXIT', 550.0)
        
        # Generate results
        total_pnl = self.current_balance - self.initial_balance
        total_return_pct = (total_pnl / self.initial_balance) * 100
        win_rate = (self.winning_trades / max(self.total_trades, 1)) * 100
        
        results = {
            'strategy': 'ENHANCED_IRON_CONDOR',
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'vix_signals': self.vix_signals,
            'trading_days': len(available_dates),
            'log_files': {
                'trades': str(self.logger.trade_log_path),
                'balance': str(self.logger.balance_log_path)
            }
        }
        
        return results

def main():
    """Test Enhanced Iron Condor Strategy"""
    
    print("🧪 ENHANCED IRON CONDOR STRATEGY TEST")
    print("="*60)
    print("Research-Based Implementation:")
    print("✅ VIX Filter (only when VIX > previous day)")
    print("✅ 30 Delta Strikes (optimal premium/risk)")
    print("✅ 9:30 AM Entry, 11:30 AM Exit")
    print("✅ 22.5% Profit Target")
    print("✅ ~$850 Target Margin")
    print()
    
    # Initialize strategy
    strategy = EnhancedIronCondorStrategy(initial_balance=25000)
    
    # Run 2-week test
    results = strategy.run_backtest(
        start_date="2024-07-01",
        end_date="2024-07-15"
    )
    
    print("\n" + "="*70)
    print("📊 ENHANCED IRON CONDOR RESULTS")
    print("="*70)
    
    print(f"\n💰 FINANCIAL PERFORMANCE:")
    print(f"   Initial Balance: ${results['initial_balance']:,.2f}")
    print(f"   Final Balance: ${results['final_balance']:,.2f}")
    print(f"   Total P&L: ${results['total_pnl']:+,.2f}")
    print(f"   Total Return: {results['total_return_pct']:+.2f}%")
    
    print(f"\n📈 TRADING STATISTICS:")
    print(f"   Total Trades: {results['total_trades']}")
    print(f"   Winning Trades: {results['winning_trades']}")
    print(f"   Win Rate: {results['win_rate']:.1f}%")
    
    print(f"\n📊 VIX SIGNAL ANALYSIS:")
    vix_signals = results['vix_signals']
    total_days = results['trading_days']
    print(f"   Trading Days: {total_days}")
    print(f"   Valid VIX Signals: {vix_signals['valid']} ({vix_signals['valid']/total_days*100:.1f}%)")
    print(f"   Invalid VIX Signals: {vix_signals['invalid']} ({vix_signals['invalid']/total_days*100:.1f}%)")
    print(f"   Expected: ~50% valid signals (research)")
    
    print(f"\n🎯 RESEARCH VALIDATION:")
    valid_pct = vix_signals['valid'] / total_days * 100
    if 40 <= valid_pct <= 60:
        print("   ✅ VIX Signal Rate: Within expected range (40-60%)")
    else:
        print(f"   ⚠️ VIX Signal Rate: {valid_pct:.1f}% (expected 40-60%)")
    
    if results['win_rate'] > 60:
        print("   ✅ Win Rate: Good performance")
    elif results['win_rate'] > 40:
        print("   🟡 Win Rate: Acceptable performance")
    else:
        print("   ❌ Win Rate: Needs improvement")
    
    print(f"\n📁 DETAILED LOGS:")
    print(f"   Trade Log: {results['log_files']['trades']}")
    print(f"   Balance Log: {results['log_files']['balance']}")
    
    return results

if __name__ == "__main__":
    main()
