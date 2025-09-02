#!/usr/bin/env python3
"""
🦋 FLYAGONAL BACKTESTER
======================
Dedicated backtester for the Flyagonal strategy following the same pattern as our successful Iron Condor system.

Extends UnifiedStrategyBacktester to maintain compatibility while implementing Flyagonal-specific logic.

Key Features:
- 6-leg position management (Call Butterfly + Put Diagonal)
- VIX regime optimization
- 200+ point profit zone requirement
- Integration with existing framework components
- Comprehensive logging and analytics

Following @.cursorrules:
- Extends existing successful backtesting framework
- Maintains separation from Iron Condor system
- Uses real data and Black-Scholes pricing
- Professional risk management

Location: src/strategies/flyagonal_python/ (following .cursorrules structure)
Author: Advanced Options Trading Framework - Flyagonal Backtester Module
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, time, timedelta
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import base backtester
sys.path.append(str(Path(__file__).parent.parent.parent / 'tests' / 'analysis'))
from unified_strategy_backtester import UnifiedStrategyBacktester

# Import Flyagonal strategy
from flyagonal_strategy import FlyagonalStrategy, FlyagonalPosition

class FlyagonalBacktester(UnifiedStrategyBacktester):
    """
    Flyagonal Strategy Backtester
    
    Extends UnifiedStrategyBacktester with Flyagonal-specific implementation.
    Maintains compatibility with existing framework while adding complex multi-leg strategy logic.
    """
    
    def __init__(self, initial_balance: float = 25000):
        super().__init__(initial_balance)
        
        # Initialize Flyagonal strategy
        self.flyagonal_strategy = FlyagonalStrategy(initial_balance)
        
        # Override some parameters for Flyagonal
        self.max_positions = 1  # Conservative: complex positions need focus
        self.daily_target = 500.0  # Higher target due to complexity
        self.max_daily_loss = 1000.0  # Higher risk tolerance for complex strategy
        
        # Flyagonal-specific tracking
        self.flyagonal_trades = 0
        self.successful_profit_zones = 0
        self.vix_regime_entries = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        
        print(f"🦋 FLYAGONAL BACKTESTER INITIALIZED")
        print(f"   Base: UnifiedStrategyBacktester (proven framework)")
        print(f"   Strategy: Flyagonal (Call Butterfly + Put Diagonal)")
        print(f"   Max Positions: {self.max_positions}")
        print(f"   Daily Target: ${self.daily_target}")
        print(f"   ✅ 6-LEG POSITION MANAGEMENT")
        print(f"   ✅ VIX REGIME OPTIMIZATION")
        print(f"   ✅ FRAMEWORK INTEGRATION")
    
    def _get_strategy_recommendation(self, regime: str, spy_price: float) -> str:
        """
        Override strategy recommendation to focus on Flyagonal
        
        Flyagonal is suitable for:
        - NEUTRAL markets (best for complex spreads)
        - MEDIUM volatility (not too high, not too low)
        """
        
        # For Flyagonal backtesting, we'll focus on optimal conditions
        if regime in ['NEUTRAL', 'BULLISH']:  # Avoid bearish markets for complex strategies
            return 'FLYAGONAL'
        else:
            return 'NO_TRADE'  # Conservative approach
    
    def _execute_flyagonal(self, options_data: pd.DataFrame, spy_price: float, current_time: datetime, market_conditions: Dict) -> bool:
        """
        Execute Flyagonal strategy entry
        
        This method integrates the Flyagonal strategy with the backtesting framework.
        """
        
        try:
            # Get VIX level from market conditions
            current_vix = market_conditions.get('vix_level', 20.0)  # Default if not available
            
            # Check if we should enter Flyagonal
            if not self.flyagonal_strategy.should_enter_flyagonal(options_data, spy_price, current_vix):
                return False
            
            # Execute entry through Flyagonal strategy
            position = self.flyagonal_strategy.execute_flyagonal_entry(
                options_data, spy_price, current_time, current_vix
            )
            
            if position:
                # Track in backtester
                self.flyagonal_trades += 1
                vix_regime = self.flyagonal_strategy.detect_vix_regime(current_vix)
                self.vix_regime_entries[vix_regime] += 1
                
                # Calculate profit zone for tracking
                profit_zone = self.flyagonal_strategy.calculate_profit_zone(
                    position.call_butterfly, position.put_diagonal, spy_price
                )
                
                if profit_zone['total_profit_zone'] >= self.flyagonal_strategy.min_profit_zone_width:
                    self.successful_profit_zones += 1
                
                # Log market conditions for this entry
                self.logger.log_market_conditions(
                    timestamp=current_time,
                    spy_price=spy_price,
                    vix_level=current_vix,
                    market_regime=vix_regime,
                    put_call_ratio=market_conditions.get('put_call_ratio', 1.0),
                    additional_data={
                        'strategy': 'FLYAGONAL',
                        'profit_zone_width': profit_zone['total_profit_zone'],
                        'call_butterfly_zone': profit_zone['call_butterfly_zone'],
                        'put_diagonal_zone': profit_zone['put_diagonal_zone']
                    }
                )
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error executing Flyagonal: {e}")
            return False
    
    def _manage_flyagonal_positions(self, current_spy_price: float, current_time: datetime) -> None:
        """
        Manage open Flyagonal positions
        
        Checks exit conditions and closes positions as needed.
        """
        
        positions_to_close = []
        
        for position in self.flyagonal_strategy.open_positions:
            should_close, exit_reason = self.flyagonal_strategy.should_close_position(
                position, current_spy_price, current_time
            )
            
            if should_close:
                positions_to_close.append((position, exit_reason))
        
        # Close positions that meet exit criteria
        for position, exit_reason in positions_to_close:
            final_pnl = self.flyagonal_strategy.close_position(
                position, current_spy_price, current_time, exit_reason
            )
            
            # Update backtester balance
            self.current_balance = self.flyagonal_strategy.current_balance
            
            # Update daily P&L tracking
            date_str = current_time.strftime('%Y-%m-%d')
            if date_str not in self.daily_pnl:
                self.daily_pnl[date_str] = 0.0
            self.daily_pnl[date_str] += final_pnl
            
            # Log balance update
            self.logger.log_balance_update(
                timestamp=current_time,
                new_balance=self.current_balance,
                change=final_pnl,
                reason=f"Flyagonal exit: {exit_reason}"
            )
    
    def _process_trading_day(self, trading_day: str) -> Dict[str, Any]:
        """
        Override trading day processing to include Flyagonal logic
        
        Maintains the same structure as parent class while adding Flyagonal-specific processing.
        """
        
        print(f"\n📅 PROCESSING FLYAGONAL TRADING DAY: {trading_day}")
        
        try:
            # Load options data for the day
            options_data = self.data_loader.load_options_for_date(trading_day)
            if options_data.empty:
                print(f"❌ No options data for {trading_day}")
                return {'date': trading_day, 'trades': 0, 'pnl': 0.0}
            
            # Get SPY data
            spy_data = self.data_loader.load_spy_data_for_date(trading_day)
            if spy_data.empty:
                print(f"❌ No SPY data for {trading_day}")
                return {'date': trading_day, 'trades': 0, 'pnl': 0.0}
            
            daily_trades = 0
            daily_pnl = 0.0
            
            # Process intraday signals (same entry times as parent class)
            for entry_time in self.entry_times:
                current_datetime = datetime.combine(
                    datetime.strptime(trading_day, '%Y-%m-%d').date(),
                    entry_time
                )
                
                # Get current SPY price
                spy_price = spy_data['close'].iloc[-1]  # Use last available price
                
                # Detect market conditions
                market_regime = self._detect_market_regime(options_data, spy_price)
                
                # Get strategy recommendation
                strategy = self._get_strategy_recommendation(market_regime, spy_price)
                
                if strategy == 'FLYAGONAL':
                    # Prepare market conditions
                    market_conditions = {
                        'regime': market_regime,
                        'vix_level': self._estimate_vix_from_options(options_data, spy_price),
                        'put_call_ratio': self._calculate_put_call_ratio(options_data)
                    }
                    
                    # Execute Flyagonal entry
                    if self._execute_flyagonal(options_data, spy_price, current_datetime, market_conditions):
                        daily_trades += 1
                
                # Manage existing positions
                self._manage_flyagonal_positions(spy_price, current_datetime)
            
            # End of day position management
            end_of_day = datetime.combine(
                datetime.strptime(trading_day, '%Y-%m-%d').date(),
                time(15, 45)
            )
            
            # Force close any remaining positions at end of day (for 0DTE)
            for position in list(self.flyagonal_strategy.open_positions):
                final_pnl = self.flyagonal_strategy.close_position(
                    position, spy_price, end_of_day, "END_OF_DAY"
                )
                daily_pnl += final_pnl
            
            # Update daily P&L
            if trading_day not in self.daily_pnl:
                self.daily_pnl[trading_day] = 0.0
            self.daily_pnl[trading_day] += daily_pnl
            
            print(f"   Trades: {daily_trades} | P&L: ${daily_pnl:.2f}")
            
            return {
                'date': trading_day,
                'trades': daily_trades,
                'pnl': daily_pnl,
                'balance': self.current_balance
            }
            
        except Exception as e:
            print(f"❌ Error processing {trading_day}: {e}")
            return {'date': trading_day, 'trades': 0, 'pnl': 0.0, 'error': str(e)}
    
    def _estimate_vix_from_options(self, options_data: pd.DataFrame, spy_price: float) -> float:
        """
        Estimate VIX level from options data
        (Simplified calculation for backtesting)
        """
        
        try:
            # Find ATM options
            atm_calls = options_data[
                (options_data['option_type'] == 'call') & 
                (abs(options_data['strike'] - spy_price) <= 2.0)
            ]
            atm_puts = options_data[
                (options_data['option_type'] == 'put') & 
                (abs(options_data['strike'] - spy_price) <= 2.0)
            ]
            
            if not atm_calls.empty and not atm_puts.empty:
                # Estimate implied volatility from straddle price
                straddle_price = atm_calls['close'].iloc[0] + atm_puts['close'].iloc[0]
                estimated_vix = (straddle_price / spy_price) * 100 * 16  # Rough conversion
                return max(10.0, min(50.0, estimated_vix))  # Clamp to reasonable range
            
            return 20.0  # Default VIX level
            
        except Exception:
            return 20.0
    
    def run_flyagonal_backtest(self, start_date: str = "2023-09-01", end_date: str = "2023-09-30") -> Dict[str, Any]:
        """
        Run comprehensive Flyagonal backtest
        
        Returns detailed results including Flyagonal-specific metrics.
        """
        
        print(f"\n🦋 STARTING FLYAGONAL BACKTEST")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Initial Balance: ${self.initial_balance:,.2f}")
        print("="*60)
        
        # Get trading days
        trading_days = self.data_loader.get_trading_days_in_range(start_date, end_date)
        
        if not trading_days:
            print(f"❌ No trading days found in range {start_date} to {end_date}")
            return {}
        
        print(f"📊 Processing {len(trading_days)} trading days...")
        
        # Process each trading day
        daily_results = []
        for trading_day in trading_days:
            result = self._process_trading_day(trading_day)
            daily_results.append(result)
        
        # Generate comprehensive results
        results = self._generate_flyagonal_results(daily_results, start_date, end_date)
        
        # Generate session summary
        session_summary = self.logger.generate_session_summary(
            start_time=datetime.strptime(start_date, '%Y-%m-%d'),
            end_time=datetime.strptime(end_date, '%Y-%m-%d'),
            initial_balance=self.initial_balance,
            final_balance=self.current_balance
        )
        
        # Add Flyagonal-specific metrics
        results['flyagonal_metrics'] = {
            'total_flyagonal_trades': self.flyagonal_trades,
            'successful_profit_zones': self.successful_profit_zones,
            'profit_zone_success_rate': (self.successful_profit_zones / max(self.flyagonal_trades, 1)) * 100,
            'vix_regime_entries': self.vix_regime_entries,
            'strategy_statistics': self.flyagonal_strategy.get_strategy_statistics()
        }
        
        results['session_summary'] = session_summary
        
        print(f"\n🎯 FLYAGONAL BACKTEST COMPLETE")
        print(f"   Final Balance: ${self.current_balance:,.2f}")
        print(f"   Total Return: {((self.current_balance - self.initial_balance) / self.initial_balance) * 100:.2f}%")
        print(f"   Flyagonal Trades: {self.flyagonal_trades}")
        print(f"   Profit Zone Success: {self.successful_profit_zones}/{self.flyagonal_trades}")
        
        return results
    
    def _generate_flyagonal_results(self, daily_results: List[Dict], start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate comprehensive Flyagonal backtest results"""
        
        total_trades = sum(r.get('trades', 0) for r in daily_results)
        total_pnl = self.current_balance - self.initial_balance
        
        return {
            'backtest_period': f"{start_date} to {end_date}",
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance,
            'total_pnl': total_pnl,
            'total_return_pct': (total_pnl / self.initial_balance) * 100,
            'total_trades': total_trades,
            'daily_results': daily_results,
            'strategy_focus': 'FLYAGONAL',
            'max_positions': self.max_positions,
            'daily_target': self.daily_target
        }

def run_flyagonal_backtest_demo():
    """Demo function to run Flyagonal backtest"""
    
    backtester = FlyagonalBacktester(initial_balance=25000)
    
    # Run a short backtest
    results = backtester.run_flyagonal_backtest(
        start_date="2023-09-01",
        end_date="2023-09-15"
    )
    
    return results

if __name__ == "__main__":
    # Run demo backtest
    print("🦋 Running Flyagonal Strategy Backtest Demo...")
    results = run_flyagonal_backtest_demo()
    
    if results:
        print(f"\n📊 DEMO RESULTS:")
        print(f"   Total Return: {results.get('total_return_pct', 0):.2f}%")
        print(f"   Total Trades: {results.get('total_trades', 0)}")
        print(f"   Flyagonal Trades: {results.get('flyagonal_metrics', {}).get('total_flyagonal_trades', 0)}")
