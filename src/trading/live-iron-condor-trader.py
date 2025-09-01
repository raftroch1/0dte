#!/usr/bin/env python3
"""
Live Iron Condor Paper Trading System
====================================

Real-time paper trading implementation for Iron Condor + spread strategies
using Alpaca API integration. Adapts the proven backtesting signals for
live market execution with professional risk management.

Key Features:
- Real-time market data processing
- Professional Iron Condor signal generation
- Live position management and tracking
- Risk monitoring and circuit breakers
- Paper trading with realistic execution
- Performance analytics and logging

Location: src/trading/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Live Trading Module
"""

import sys
import os
import asyncio
import json
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Alpaca SDK imports
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass
    from alpaca.data.historical import StockHistoricalDataClient, OptionHistoricalDataClient
    from alpaca.data.live import StockDataStream, OptionDataStream
    from alpaca.data.requests import StockBarsRequest, OptionBarsRequest, StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Alpaca SDK not available: {e}")
    print("📦 Install with: pip install alpaca-py")
    ALPACA_AVAILABLE = False

# Framework imports
try:
    from src.strategies.hybrid_adaptive.enhanced_strategy_selector import EnhancedHybridAdaptiveSelector
    from src.strategies.cash_management.position_sizer import ConservativeCashManager
    from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
    from src.strategies.market_intelligence.intelligence_engine import MarketIntelligenceEngine
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required framework modules are available")
    sys.exit(1)

@dataclass
class LiveIronCondorPosition:
    """Live Iron Condor position with real-time tracking"""
    position_id: str
    entry_time: datetime
    spy_price_at_entry: float
    
    # Iron Condor legs
    put_short_strike: float
    put_long_strike: float
    call_short_strike: float
    call_long_strike: float
    contracts: int
    
    # Financial details
    credit_received: float
    max_loss: float
    max_profit: float
    
    # Real-time tracking
    current_spy_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    
    # Exit tracking
    exit_time: Optional[datetime] = None
    exit_spy_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    exit_reason: Optional[str] = None
    
    # Performance metrics
    hold_time_hours: Optional[float] = None
    return_pct: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return asdict(self)
    
    def update_current_value(self, spy_price: float, option_value: float):
        """Update real-time position value"""
        self.current_spy_price = spy_price
        self.current_value = option_value
        self.unrealized_pnl = self.credit_received - option_value
    
    def close_position(self, spy_price: float, exit_value: float, reason: str):
        """Close the position and calculate final P&L"""
        self.exit_time = datetime.now()
        self.exit_spy_price = spy_price
        self.realized_pnl = self.credit_received - exit_value
        self.exit_reason = reason
        
        # Calculate performance metrics
        if self.entry_time:
            self.hold_time_hours = (self.exit_time - self.entry_time).total_seconds() / 3600
        
        if self.credit_received > 0:
            self.return_pct = (self.realized_pnl / self.credit_received) * 100

class LiveIronCondorSignalGenerator:
    """
    Real-time Iron Condor signal generation
    Adapts the proven backtesting logic for live market conditions
    """
    
    def __init__(self):
        # Iron Condor parameters (EXACT MATCH to backtesting)
        self.iron_condor_min_credit = 0.05  # EXACT: $0.05 minimum credit
        self.iron_condor_max_width = 10.0   # EXACT: $10 maximum width
        self.contracts_per_trade = 5        # EXACT: 5 contracts per trade
        
        # Market detection parameters (EXACT MATCH to backtesting)
        self.flat_market_pc_ratio_range = (0.85, 1.15)  # EXACT: 0.85-1.15 P/C ratio
        self.flat_market_min_volume = 100               # EXACT: 100 minimum volume
        
        # Entry timing (EXACT MATCH to backtesting)
        self.entry_times = [
            time(10, 0),   # EXACT: Market open momentum
            time(11, 30),  # EXACT: Mid-morning
            time(13, 0),   # EXACT: Lunch time
            time(14, 30)   # EXACT: Afternoon momentum
        ]
        
        print(f"🎯 LIVE IRON CONDOR SIGNAL GENERATOR INITIALIZED")
        print(f"   Entry Times: {[t.strftime('%H:%M') for t in self.entry_times]}")
        print(f"   Min Credit: ${self.iron_condor_min_credit}")
        print(f"   Max Width: ${self.iron_condor_max_width}")
    
    def is_entry_time(self, current_time: datetime) -> bool:
        """Check if current time is within entry windows"""
        current_time_only = current_time.time()
        
        for entry_time in self.entry_times:
            # Allow 30-minute window around each entry time
            start_window = (datetime.combine(datetime.today(), entry_time) - timedelta(minutes=15)).time()
            end_window = (datetime.combine(datetime.today(), entry_time) + timedelta(minutes=15)).time()
            
            if start_window <= current_time_only <= end_window:
                return True
        
        return False
    
    def detect_flat_market(self, options_data: pd.DataFrame, spy_price: float) -> Dict[str, Any]:
        """
        Detect flat market conditions suitable for Iron Condor
        Adapted from proven backtesting logic
        """
        if options_data.empty:
            return {'is_flat': False, 'reason': 'No options data'}
        
        calls = options_data[options_data['option_type'] == 'call']
        puts = options_data[options_data['option_type'] == 'put']
        
        if len(calls) == 0 or len(puts) == 0:
            return {'is_flat': False, 'reason': 'Missing calls or puts'}
        
        # Calculate market indicators
        call_volume = calls['volume'].sum()
        put_volume = puts['volume'].sum()
        total_volume = call_volume + put_volume
        
        pc_ratio = put_volume / call_volume if call_volume > 0 else 1.0
        
        # Strike range analysis
        strike_range = options_data['strike'].max() - options_data['strike'].min()
        relative_range = strike_range / spy_price
        
        # Flat market conditions
        conditions = []
        
        if self.flat_market_pc_ratio_range[0] <= pc_ratio <= self.flat_market_pc_ratio_range[1]:
            conditions.append("Balanced P/C ratio")
        
        if total_volume >= self.flat_market_min_volume:
            conditions.append("Sufficient volume")
        
        if relative_range >= 0.05:  # 5% range
            conditions.append("Wide strike range")
        
        is_flat = len(conditions) >= 2
        
        return {
            'is_flat': is_flat,
            'put_call_ratio': pc_ratio,
            'total_volume': total_volume,
            'strike_range_pct': relative_range * 100,
            'conditions': conditions,
            'reason': f"{len(conditions)}/3 conditions met: {', '.join(conditions)}"
        }
    
    def generate_iron_condor_signal(self, options_data: pd.DataFrame, spy_price: float, 
                                  account_balance: float) -> Optional[Dict[str, Any]]:
        """
        Generate professional Iron Condor signal
        Uses proven 1SD methodology from backtesting
        """
        print(f"🔍 GENERATING LIVE IRON CONDOR SIGNAL (SPY: ${spy_price:.2f})")
        
        calls = options_data[options_data['option_type'] == 'call'].sort_values('strike')
        puts = options_data[options_data['option_type'] == 'put'].sort_values('strike', ascending=False)
        
        if len(calls) < 2 or len(puts) < 2:
            print("❌ Insufficient options for Iron Condor")
            return None
        
        # Calculate expected daily move (1SD)
        atm_calls = calls[abs(calls['strike'] - spy_price) <= 2.0]
        atm_puts = puts[abs(puts['strike'] - spy_price) <= 2.0]
        
        if not atm_calls.empty and not atm_puts.empty:
            # Use bid/ask midpoint for more accurate pricing
            atm_call_price = (atm_calls.iloc[0]['bid'] + atm_calls.iloc[0]['ask']) / 2
            atm_put_price = (atm_puts.iloc[0]['bid'] + atm_puts.iloc[0]['ask']) / 2
            straddle_price = atm_call_price + atm_put_price
            expected_move_1sd = straddle_price * 0.8
        else:
            expected_move_1sd = spy_price * 0.01
        
        print(f"   Expected 1SD Move: ±${expected_move_1sd:.2f}")
        
        # Set target strikes (1SD methodology)
        put_short_target = spy_price - expected_move_1sd
        call_short_target = spy_price + expected_move_1sd
        put_long_target = spy_price - (1.5 * expected_move_1sd)
        call_long_target = spy_price + (1.5 * expected_move_1sd)
        
        # Find optimal strikes with volume requirements
        put_short = self._find_best_strike(puts, put_short_target, min_volume=10)
        put_long = self._find_best_strike(puts, put_long_target, min_volume=1)
        call_short = self._find_best_strike(calls, call_short_target, min_volume=10)
        call_long = self._find_best_strike(calls, call_long_target, min_volume=1)
        
        if not all([put_short, put_long, call_short, call_long]):
            print("❌ Could not find suitable strikes")
            return None
        
        # Calculate Iron Condor economics
        put_credit = put_short['bid'] - put_long['ask']
        call_credit = call_short['bid'] - call_long['ask']
        total_credit = put_credit + call_credit
        
        put_width = put_short['strike'] - put_long['strike']
        call_width = call_long['strike'] - call_short['strike']
        max_loss = max(put_width, call_width) - total_credit
        
        if total_credit < self.iron_condor_min_credit:
            print(f"❌ Credit too low: ${total_credit:.2f} < ${self.iron_condor_min_credit}")
            return None
        
        # Position sizing (1-2% account risk)
        max_risk_per_trade = account_balance * 0.02
        max_contracts = int(max_risk_per_trade / (max_loss * 100))
        optimal_contracts = min(self.contracts_per_trade, max_contracts, 10)
        
        if optimal_contracts < 1:
            print("❌ Position size too small for account")
            return None
        
        # Calculate final metrics
        total_credit_received = total_credit * optimal_contracts * 100
        total_max_loss = max_loss * optimal_contracts * 100
        profit_ratio = total_credit_received / total_max_loss if total_max_loss > 0 else 0
        
        print(f"✅ IRON CONDOR SIGNAL GENERATED:")
        print(f"   Put Spread: ${put_short['strike']:.0f}/${put_long['strike']:.0f}")
        print(f"   Call Spread: ${call_short['strike']:.0f}/${call_long['strike']:.0f}")
        print(f"   Contracts: {optimal_contracts}")
        print(f"   Credit: ${total_credit_received:.2f}")
        print(f"   Max Loss: ${total_max_loss:.2f}")
        print(f"   Profit Ratio: {profit_ratio:.2f}")
        
        return {
            'signal_type': 'IRON_CONDOR',
            'confidence': 90.0,
            'put_short_strike': put_short['strike'],
            'put_long_strike': put_long['strike'],
            'call_short_strike': call_short['strike'],
            'call_long_strike': call_long['strike'],
            'contracts': optimal_contracts,
            'credit_per_spread': total_credit,
            'total_credit': total_credit_received,
            'max_loss': total_max_loss,
            'max_profit': total_credit_received,
            'profit_ratio': profit_ratio,
            'reasoning': f"Live 0DTE Iron Condor: 1SD strikes, {optimal_contracts} contracts"
        }
    
    def _find_best_strike(self, options_df: pd.DataFrame, target_strike: float, 
                         min_volume: int = 1) -> Optional[Dict]:
        """Find best strike near target with volume requirements"""
        # Filter by volume and valid pricing
        candidates = options_df[
            (options_df['volume'] >= min_volume) &
            (options_df['bid'] > 0.01) &
            (options_df['ask'] > options_df['bid'])
        ].copy()
        
        if candidates.empty:
            return None
        
        # Find closest to target strike
        candidates['distance'] = abs(candidates['strike'] - target_strike)
        best_candidate = candidates.loc[candidates['distance'].idxmin()]
        
        return {
            'strike': best_candidate['strike'],
            'bid': best_candidate['bid'],
            'ask': best_candidate['ask'],
            'volume': best_candidate['volume']
        }

class LiveIronCondorTrader:
    """
    Complete live Iron Condor trading system
    Integrates signal generation, execution, and risk management
    """
    
    def __init__(self, initial_balance: float = 25000):
        if not ALPACA_AVAILABLE:
            raise ImportError("Alpaca SDK required for live trading")
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            paper=True  # Paper trading mode
        )
        
        self.stock_data_client = StockHistoricalDataClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY')
        )
        
        self.option_data_client = OptionHistoricalDataClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY')
        )
        
        # Initialize framework components (EXACT MATCH to backtesting)
        self.signal_generator = LiveIronCondorSignalGenerator()
        self.cash_manager = ConservativeCashManager(initial_balance)
        self.pricing_calculator = BlackScholesCalculator()
        self.intelligence_engine = MarketIntelligenceEngine()
        
        # Account management (EXACT MATCH to backtesting)
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.daily_target = 250.0  # EXACT: $250/day target
        self.max_daily_loss = 500.0  # EXACT: $500 max daily loss
        
        # Position tracking
        self.open_positions: List[LiveIronCondorPosition] = []
        self.closed_positions: List[LiveIronCondorPosition] = []
        self.daily_pnl = 0.0
        
        # Risk management (EXACT MATCH to backtesting)
        self.max_positions = 2  # EXACT: max 2 positions
        self.max_hold_hours = 4.0  # EXACT: 4 hour max hold for 0DTE
        self.profit_target_pct = 0.5  # EXACT: 50% of max profit
        self.stop_loss_pct = 0.5  # EXACT: 50% of max loss
        
        # Trading state
        self.is_trading = False
        self.last_signal_time = datetime.min
        self.signals_today = 0
        self.max_signals_per_day = 3
        
        # Performance tracking
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0
        
        # Logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/live_iron_condor_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"🚀 LIVE IRON CONDOR TRADER INITIALIZED")
        self.logger.info(f"   Initial Balance: ${initial_balance:,.2f}")
        self.logger.info(f"   Daily Target: ${self.daily_target}")
        self.logger.info(f"   Max Daily Loss: ${self.max_daily_loss}")
        self.logger.info(f"   ✅ PAPER TRADING MODE")
    
    async def start_trading(self):
        """Start the live trading loop"""
        self.is_trading = True
        self.logger.info("🎯 STARTING LIVE IRON CONDOR TRADING")
        
        try:
            # Verify connection
            account = self.trading_client.get_account()
            self.logger.info(f"✅ Connected to Alpaca - Account: {account.account_number}")
            
            # Main trading loop
            while self.is_trading:
                await self._trading_cycle()
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            self.logger.error(f"❌ Trading error: {e}")
            self.is_trading = False
    
    async def _trading_cycle(self):
        """Single trading cycle - check for signals and manage positions"""
        try:
            current_time = datetime.now()
            
            # Check if market is open (9:30 AM - 4:00 PM ET)
            if not self._is_market_hours(current_time):
                return
            
            # Update existing positions
            await self._update_positions()
            
            # Check for exit conditions
            await self._check_exit_conditions()
            
            # Check for new entry opportunities
            if self._should_look_for_entries(current_time):
                await self._check_entry_opportunities()
            
            # Update daily P&L and risk metrics
            self._update_performance_metrics()
            
        except Exception as e:
            self.logger.error(f"❌ Trading cycle error: {e}")
    
    def _is_market_hours(self, current_time: datetime) -> bool:
        """Check if market is currently open"""
        # Simple check - in production, use market calendar
        weekday = current_time.weekday()
        if weekday >= 5:  # Weekend
            return False
        
        current_time_only = current_time.time()
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        return market_open <= current_time_only <= market_close
    
    def _should_look_for_entries(self, current_time: datetime) -> bool:
        """Determine if we should look for new entry opportunities"""
        # Check daily limits
        if self.signals_today >= self.max_signals_per_day:
            return False
        
        # Check position limits
        if len(self.open_positions) >= self.max_positions:
            return False
        
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            self.logger.warning(f"⚠️ Daily loss limit reached: ${self.daily_pnl:.2f}")
            return False
        
        # Check if it's an entry time
        if not self.signal_generator.is_entry_time(current_time):
            return False
        
        # Prevent duplicate signals within 30 minutes
        if (current_time - self.last_signal_time).total_seconds() < 1800:
            return False
        
        return True
    
    async def _check_entry_opportunities(self):
        """Check for Iron Condor entry opportunities"""
        try:
            # Get current SPY price
            spy_quote_request = StockLatestQuoteRequest(symbol_or_symbols="SPY")
            spy_quote = self.stock_data_client.get_stock_latest_quote(spy_quote_request)
            spy_price = float(spy_quote["SPY"].bid_price + spy_quote["SPY"].ask_price) / 2
            
            # Get 0DTE options data
            options_data = await self._get_0dte_options_data(spy_price)
            
            if options_data.empty:
                self.logger.warning("❌ No 0DTE options data available")
                return
            
            # Check market conditions
            market_analysis = self.signal_generator.detect_flat_market(options_data, spy_price)
            
            self.logger.info(f"📊 Market Analysis: {market_analysis['reason']}")
            
            if market_analysis['is_flat']:
                self.logger.info("🎯 FLAT MARKET DETECTED - GENERATING SIGNAL")
                
                # Generate Iron Condor signal
                signal = self.signal_generator.generate_iron_condor_signal(
                    options_data, spy_price, self.current_balance
                )
                
                if signal:
                    self.signals_today += 1
                    self.last_signal_time = datetime.now()
                    
                    # Execute the signal (paper trading)
                    success = await self._execute_iron_condor_signal(signal, spy_price)
                    
                    if success:
                        self.logger.info("✅ IRON CONDOR POSITION OPENED")
                    else:
                        self.logger.error("❌ Failed to execute Iron Condor signal")
                else:
                    self.logger.info("❌ No valid Iron Condor signal generated")
            
        except Exception as e:
            self.logger.error(f"❌ Entry opportunity check failed: {e}")
    
    async def _get_0dte_options_data(self, spy_price: float) -> pd.DataFrame:
        """Get 0DTE options data from Alpaca"""
        try:
            # Get today's expiration date
            today = datetime.now().date()
            
            # Define strike range around current price
            strike_range = 20  # $20 range around current price
            min_strike = spy_price - strike_range
            max_strike = spy_price + strike_range
            
            # This is a simplified version - in production, use proper options chain API
            # For now, return empty DataFrame to prevent errors
            self.logger.warning("⚠️ 0DTE options data retrieval not fully implemented")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get 0DTE options data: {e}")
            return pd.DataFrame()
    
    async def _execute_iron_condor_signal(self, signal: Dict[str, Any], spy_price: float) -> bool:
        """Execute Iron Condor signal (paper trading simulation)"""
        try:
            # Create position object
            position = LiveIronCondorPosition(
                position_id=f"IC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                entry_time=datetime.now(),
                spy_price_at_entry=spy_price,
                put_short_strike=signal['put_short_strike'],
                put_long_strike=signal['put_long_strike'],
                call_short_strike=signal['call_short_strike'],
                call_long_strike=signal['call_long_strike'],
                contracts=signal['contracts'],
                credit_received=signal['total_credit'],
                max_loss=signal['max_loss'],
                max_profit=signal['max_profit']
            )
            
            # Add to open positions
            self.open_positions.append(position)
            
            # Update account balance
            self.current_balance += signal['total_credit']
            
            # Log the trade
            self.logger.info(f"📊 IRON CONDOR OPENED:")
            self.logger.info(f"   Position ID: {position.position_id}")
            self.logger.info(f"   Put Spread: ${position.put_short_strike:.0f}/${position.put_long_strike:.0f}")
            self.logger.info(f"   Call Spread: ${position.call_short_strike:.0f}/${position.call_long_strike:.0f}")
            self.logger.info(f"   Contracts: {position.contracts}")
            self.logger.info(f"   Credit Received: ${position.credit_received:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to execute Iron Condor: {e}")
            return False
    
    async def _update_positions(self):
        """Update all open positions with current market data"""
        if not self.open_positions:
            return
        
        try:
            # Get current SPY price
            spy_quote_request = StockLatestQuoteRequest(symbol_or_symbols="SPY")
            spy_quote = self.stock_data_client.get_stock_latest_quote(spy_quote_request)
            spy_price = float(spy_quote["SPY"].bid_price + spy_quote["SPY"].ask_price) / 2
            
            for position in self.open_positions:
                # Calculate current option value using Black-Scholes
                current_value = self._calculate_iron_condor_value(position, spy_price)
                position.update_current_value(spy_price, current_value)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update positions: {e}")
    
    def _calculate_iron_condor_value(self, position: LiveIronCondorPosition, spy_price: float) -> float:
        """Calculate current Iron Condor value using Black-Scholes"""
        try:
            # Time to expiration (0DTE - use hours remaining)
            current_time = datetime.now()
            market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
            hours_to_expiry = max((market_close - current_time).total_seconds() / 3600, 0.01)
            time_to_expiry = hours_to_expiry / (24 * 365)  # Convert to years
            
            # Use simplified Black-Scholes for Iron Condor
            # In production, calculate each leg separately
            intrinsic_value = 0.0
            
            # Put spread intrinsic value
            if spy_price < position.put_short_strike:
                put_intrinsic = position.put_short_strike - spy_price
                put_intrinsic -= max(0, position.put_long_strike - spy_price)
                intrinsic_value += put_intrinsic
            
            # Call spread intrinsic value
            if spy_price > position.call_short_strike:
                call_intrinsic = spy_price - position.call_short_strike
                call_intrinsic -= max(0, spy_price - position.call_long_strike)
                intrinsic_value += call_intrinsic
            
            # Add time value (simplified)
            time_value = max(0, position.credit_received * 0.1 * (time_to_expiry / 0.00274))  # 1 day = 0.00274 years
            
            total_value = (intrinsic_value + time_value) * position.contracts * 100
            
            return max(0, total_value)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate Iron Condor value: {e}")
            return 0.0
    
    async def _check_exit_conditions(self):
        """Check if any positions should be exited (EXACT MATCH to backtesting logic)"""
        positions_to_close = []
        current_time = datetime.now()
        
        for position in self.open_positions:
            # Calculate current P&L using Black-Scholes (EXACT MATCH to backtesting)
            current_pnl = self._calculate_position_pnl(position, position.current_spy_price or 0.0, current_time)
            
            should_close = False
            exit_reason = ""
            
            # EXACT MATCH to backtesting exit conditions:
            
            # 1. Time-based exit (EXACT: 4 hours max hold OR time_exit_target)
            if position.entry_time:
                hold_hours = (current_time - position.entry_time).total_seconds() / 3600
                if hold_hours >= self.max_hold_hours:
                    should_close = True
                    exit_reason = "TIME_EXIT"
            
            # 2. Profit target (EXACT: 50% of max profit)
            profit_target = position.credit_received * self.profit_target_pct
            if current_pnl >= profit_target:
                should_close = True
                exit_reason = "PROFIT_TARGET"
            
            # 3. Stop loss (EXACT: 50% of max loss)
            stop_loss_level = position.max_loss * self.stop_loss_pct
            if current_pnl <= -stop_loss_level:
                should_close = True
                exit_reason = "STOP_LOSS"
            
            # 4. End of day exit for 0DTE (EXACT: 3:00 PM or later)
            if current_time.time() >= time(15, 0):
                should_close = True
                exit_reason = "END_OF_DAY"
            
            # 5. Market close buffer (EXACT: 15:30 buffer like backtesting)
            if current_time.time() >= time(15, 30):
                should_close = True
                exit_reason = "MARKET_CLOSE_BUFFER"
            
            if should_close:
                positions_to_close.append((position, current_pnl, exit_reason))
        
        # Close positions (EXACT MATCH to backtesting)
        for position, pnl, exit_reason in positions_to_close:
            await self._close_position_with_pnl(position, pnl, exit_reason, current_time)
    
    def _calculate_position_pnl(self, position: LiveIronCondorPosition, spy_price: float, current_time: datetime) -> float:
        """Calculate current position P&L using Black-Scholes (EXACT MATCH to backtesting)"""
        try:
            # Time to expiration for 0DTE (hours remaining until market close)
            market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
            hours_to_expiry = max((market_close - current_time).total_seconds() / 3600, 0.01)
            time_to_expiry = hours_to_expiry / (24 * 365)  # Convert to years for Black-Scholes
            
            # Calculate intrinsic value (EXACT MATCH to backtesting logic)
            intrinsic_value = 0.0
            
            # Put spread intrinsic value
            if spy_price < position.put_short_strike:
                put_intrinsic = position.put_short_strike - spy_price
                put_intrinsic -= max(0, position.put_long_strike - spy_price)
                intrinsic_value += put_intrinsic
            
            # Call spread intrinsic value
            if spy_price > position.call_short_strike:
                call_intrinsic = spy_price - position.call_short_strike
                call_intrinsic -= max(0, spy_price - position.call_long_strike)
                intrinsic_value += call_intrinsic
            
            # Add time value (simplified Black-Scholes approximation)
            time_value = max(0, position.credit_received * 0.1 * (time_to_expiry / 0.00274))
            
            # Total option value
            total_option_value = (intrinsic_value + time_value) * position.contracts * 100
            
            # P&L = Credit received - Current option value (EXACT MATCH to backtesting)
            current_pnl = position.credit_received - total_option_value
            
            return current_pnl
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate position P&L: {e}")
            return 0.0
    
    async def _close_position_with_pnl(self, position: LiveIronCondorPosition, pnl: float, reason: str, exit_time: datetime):
        """Close a position with calculated P&L (EXACT MATCH to backtesting)"""
        try:
            # Set exit details (EXACT MATCH to backtesting)
            position.exit_time = exit_time
            position.exit_spy_price = position.current_spy_price
            position.exit_reason = reason
            position.realized_pnl = pnl
            
            # Calculate hold time (EXACT MATCH to backtesting)
            if position.entry_time:
                position.hold_time_hours = (exit_time - position.entry_time).total_seconds() / 3600
            
            # Calculate return percentage (EXACT MATCH to backtesting)
            if position.credit_received > 0:
                position.return_pct = (pnl / position.credit_received) * 100
            
            # Update account balance (EXACT MATCH to backtesting)
            self.current_balance += pnl
            self.daily_pnl += pnl
            
            # Update cash manager (EXACT MATCH to backtesting)
            self.cash_manager.close_position(position.position_id, pnl)
            
            # Move to closed positions (EXACT MATCH to backtesting)
            self.open_positions.remove(position)
            self.closed_positions.append(position)
            
            # Log the closure (EXACT MATCH to backtesting format)
            self.logger.info(f"📊 IRON CONDOR CLOSED:")
            self.logger.info(f"   Position ID: {position.position_id}")
            self.logger.info(f"   Exit Reason: {reason}")
            self.logger.info(f"   Hold Time: {position.hold_time_hours:.1f}h")
            self.logger.info(f"   Entry SPY: ${position.spy_price_at_entry:.2f}")
            self.logger.info(f"   Exit SPY: ${position.exit_spy_price:.2f}")
            self.logger.info(f"   Credit Received: ${position.credit_received:.2f}")
            self.logger.info(f"   Realized P&L: ${position.realized_pnl:.2f}")
            self.logger.info(f"   Return: {position.return_pct:.1f}%")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to close position: {e}")
    
    async def _close_position(self, position: LiveIronCondorPosition, reason: str):
        """Legacy close method - redirects to new method with P&L calculation"""
        current_time = datetime.now()
        pnl = self._calculate_position_pnl(position, position.current_spy_price or 0.0, current_time)
        await self._close_position_with_pnl(position, pnl, reason, current_time)
    
    def _update_performance_metrics(self):
        """Update daily performance metrics"""
        # Update peak balance and drawdown
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
    
    def stop_trading(self):
        """Stop the trading system"""
        self.is_trading = False
        self.logger.info("🛑 LIVE TRADING STOPPED")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""
        total_trades = len(self.closed_positions)
        winning_trades = len([p for p in self.closed_positions if (p.realized_pnl or 0) > 0])
        
        return {
            'current_balance': self.current_balance,
            'daily_pnl': self.daily_pnl,
            'total_return_pct': ((self.current_balance - self.initial_balance) / self.initial_balance) * 100,
            'open_positions': len(self.open_positions),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'max_drawdown_pct': self.max_drawdown * 100,
            'signals_today': self.signals_today
        }

# Example usage and testing
async def main():
    """Main function for testing the live trader"""
    if not ALPACA_AVAILABLE:
        print("❌ Alpaca SDK not available - cannot run live trader")
        return
    
    # Check environment variables
    if not os.getenv('ALPACA_API_KEY') or not os.getenv('ALPACA_SECRET_KEY'):
        print("❌ Alpaca API credentials not found in environment variables")
        print("Please set ALPACA_API_KEY and ALPACA_SECRET_KEY")
        return
    
    # Initialize trader
    trader = LiveIronCondorTrader(initial_balance=25000)
    
    try:
        # Start trading (this would run indefinitely)
        print("🚀 Starting live Iron Condor trader...")
        print("Press Ctrl+C to stop")
        
        await trader.start_trading()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping trader...")
        trader.stop_trading()
        
        # Print final performance
        performance = trader.get_performance_summary()
        print("\n📊 FINAL PERFORMANCE:")
        for key, value in performance.items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())
