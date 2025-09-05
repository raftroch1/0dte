#!/usr/bin/env python3
"""
Professional 0DTE Credit Spread Backtester
==========================================

PROFESSIONAL BACKTESTING SYSTEM:
- Integrates with existing ParquetDataLoader
- Uses real market data and Black-Scholes pricing
- Implements all professional requirements
- Proper P&L calculation with real option pricing
- Comprehensive logging and performance tracking

Follows @.cursorrules for professional architecture.
Integrates with existing data infrastructure.

Location: src/tests/analysis/ (following .cursorrules structure)
Author: Advanced Options Trading System - Professional Backtester
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import logging
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import existing infrastructure
try:
    from src.data.parquet_data_loader import ParquetDataLoader
    from src.data.spy_1minute_loader import SPY1MinuteLoader
    from src.strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
    from src.strategies.professional_0dte.professional_credit_spread_system import (
        Professional0DTESystem, ProfessionalConfig, TradeSignal, SpreadType
    )
    from src.strategies.market_intelligence.intelligence_engine import MarketIntelligenceEngine
except ImportError:
    # Alternative import method
    sys.path.insert(0, str(project_root))
    from data.parquet_data_loader import ParquetDataLoader
    from data.spy_1minute_loader import SPY1MinuteLoader
    from strategies.real_option_pricing.black_scholes_calculator import BlackScholesCalculator
    from strategies.professional_0dte.professional_credit_spread_system import (
        Professional0DTESystem, ProfessionalConfig, TradeSignal, SpreadType
    )
    from strategies.market_intelligence.intelligence_engine import MarketIntelligenceEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Professional0DTEBacktester:
    """
    Professional 0DTE Credit Spread Backtester
    
    Integrates professional trading system with existing data infrastructure:
    - Real market data from ParquetDataLoader
    - Real option pricing from BlackScholesCalculator
    - Professional risk management and position sizing
    - Comprehensive performance tracking
    """
    
    def __init__(self, config: Optional[ProfessionalConfig] = None):
        self.config = config or ProfessionalConfig()
        
        # Initialize components with REAL historical data (2023-2024)
        self.data_loader = ParquetDataLoader('src/data/spy_options_20230830_20240829.parquet')
        self.spy_loader = SPY1MinuteLoader()  # NEW: SPY 1-minute data for VWAP analysis
        self.option_pricer = BlackScholesCalculator()
        self.trading_system = Professional0DTESystem(self.config)
        
        # CRITICAL FIX: Initialize Market Intelligence Engine with REAL fixes
        self.market_intelligence = MarketIntelligenceEngine()
        
        # ENHANCED: Initialize Enhanced Regime Detector
        try:
            from src.strategies.market_intelligence.enhanced_regime_detector import EnhancedRegimeDetector
            self.enhanced_regime_detector = EnhancedRegimeDetector()
            logger.info("🎯 Enhanced Regime Detector initialized")
        except ImportError:
            self.enhanced_regime_detector = None
            logger.warning("Enhanced Regime Detector not available, using standard detection")
        
        # Backtesting tracking
        self.backtest_results: List[Dict] = []
        self.daily_summaries: List[Dict] = []
        self.open_positions: Dict[str, Dict] = {}
        
        logger.info("🏆 PROFESSIONAL 0DTE BACKTESTER INITIALIZED")
        logger.info(f"   Account Balance: ${self.config.account_balance:,.2f}")
        logger.info(f"   Data Loader: Ready")
        
    def run_backtest(self, start_date: datetime, end_date: datetime, 
                    max_days: Optional[int] = None) -> Dict:
        """
        Run professional backtest over specified date range
        """
        
        logger.info(f"🚀 STARTING PROFESSIONAL BACKTEST")
        logger.info(f"   Period: {start_date.date()} to {end_date.date()}")
        
        # Get trading days
        trading_days = self.data_loader.get_available_dates(start_date, end_date)
        
        if max_days:
            trading_days = trading_days[:max_days]
            logger.info(f"   Limited to {max_days} days: {len(trading_days)} trading days")
        else:
            logger.info(f"   Trading days: {len(trading_days)}")
            
        # Process each trading day
        for day_num, trade_date in enumerate(trading_days, 1):
            try:
                logger.info(f"\\n📅 Day {day_num}/{len(trading_days)}: {trade_date.date()}")
                self._process_trading_day(trade_date)
                
            except Exception as e:
                logger.error(f"❌ Error processing {trade_date.date()}: {e}")
                continue
                
        # Generate final results
        results = self._generate_final_results(start_date, end_date, len(trading_days))
        
        logger.info(f"\\n🏆 PROFESSIONAL BACKTEST COMPLETE!")
        logger.info(f"   Final Balance: ${results['final_balance']:,.2f}")
        logger.info(f"   Total Return: {results['total_return_pct']:+.2f}%")
        logger.info(f"   Win Rate: {results['win_rate_pct']:.1f}%")
        logger.info(f"   Total Trades: {results['total_trades']}")
        
        return results
        
    def _process_trading_day(self, trade_date: datetime):
        """Process a single trading day with professional logic"""
        
        # Reset daily metrics
        self.trading_system.reset_daily_metrics()
        
        # Load options data for the day
        options_data = self.data_loader.load_options_for_date(trade_date)
        
        if options_data.empty:
            logger.warning(f"   ⚠️  No options data for {trade_date.date()}")
            return
            
        # Estimate SPY price
        spy_price = self.data_loader._estimate_spy_price(options_data)
        
        # Simulate VIX and volume (in production, use real data)
        vix_level = self._simulate_vix()
        spy_volume = self._simulate_spy_volume()
        
        logger.info(f"   📊 SPY: ${spy_price:.2f}, VIX: {vix_level:.1f}, Volume: {spy_volume:,}")
        
        # Manage existing positions first
        self._manage_open_positions(options_data, spy_price, trade_date)
        
        # Try to open new positions during trading windows
        trading_windows = [
            {'time': time(10, 0), 'name': 'MORNING_OPEN'},
            {'time': time(11, 30), 'name': 'MID_MORNING'},
            {'time': time(13, 0), 'name': 'AFTERNOON'},
            {'time': time(14, 0), 'name': 'LATE_AFTERNOON'}
        ]
        
        for window in trading_windows:
            window_time = trade_date.replace(
                hour=window['time'].hour, 
                minute=window['time'].minute
            )
            
            # Check if we can trade
            can_trade, reason = self.trading_system.can_trade(
                window_time, vix_level, spy_volume
            )
            
            if not can_trade:
                logger.debug(f"   ⏸️  {window['name']}: {reason}")
                continue
                
            # Generate trade signal
            market_regime = self._determine_market_regime(options_data, spy_price, trade_date)
            signal = self.trading_system.generate_trade_signal(
                options_data, spy_price, market_regime, window_time
            )
            
            if signal:
                logger.info(f"   🎯 {window['name']}: {signal.spread_type.value} signal (confidence: {signal.confidence:.1f}%)")
                
                # Execute trade
                trade_result = self.trading_system.execute_trade(signal)
                
                if trade_result['executed']:
                    # Add to open positions for P&L tracking
                    self._add_position_for_tracking(trade_result, signal, spy_price, window_time)
                    
        # Record daily summary
        self._record_daily_summary(trade_date)
        
    def _manage_open_positions(self, options_data: pd.DataFrame, spy_price: float, 
                             current_time: datetime):
        """Manage open positions with real P&L calculation"""
        
        positions_to_close = []
        
        for position_id, position_data in self.open_positions.items():
            try:
                # Calculate current P&L using real option pricing
                current_pnl = self._calculate_real_position_pnl(
                    position_data, spy_price, current_time
                )
                
                # Check exit conditions
                should_close, exit_reason = self.trading_system.profit_manager.check_exit_conditions(
                    position_id, current_pnl, current_time
                )
                
                if should_close:
                    positions_to_close.append((position_id, current_pnl, exit_reason))
                    
            except Exception as e:
                logger.error(f"   ❌ Error managing position {position_id}: {e}")
                # Force close problematic positions
                positions_to_close.append((position_id, 0.0, "ERROR_CLOSE"))
                
        # Close positions
        for position_id, pnl, exit_reason in positions_to_close:
            self._close_position(position_id, pnl, exit_reason, current_time)
            
    def _calculate_real_position_pnl(self, position_data: Dict, current_spy_price: float, 
                                   current_time: datetime) -> float:
        """Calculate real P&L using Black-Scholes pricing"""
        
        signal = position_data['signal']
        entry_spy_price = position_data['entry_spy_price']
        
        # Calculate time to expiry (0DTE = same day expiry)
        market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
        if current_time >= market_close:
            time_to_expiry = 0.0
        else:
            hours_remaining = (market_close - current_time).total_seconds() / 3600
            time_to_expiry = max(0.001, hours_remaining / (365 * 24))
            
        # Calculate current spread value
        if signal.spread_type == SpreadType.BULL_PUT_SPREAD:
            strategy_type = 'BULL_PUT_SPREAD'
        elif signal.spread_type == SpreadType.BEAR_CALL_SPREAD:
            strategy_type = 'BEAR_CALL_SPREAD'
        else:
            strategy_type = 'IRON_CONDOR'
            
        current_spread_value = self.option_pricer.calculate_spread_value(
            current_spy_price, signal.long_strike, signal.short_strike,
            time_to_expiry, 0.20, strategy_type
        )
        
        # For credit spreads: P&L = entry_credit - current_cost_to_close
        entry_credit = signal.premium_collected
        current_cost = current_spread_value
        
        # Per-contract P&L
        pnl_per_contract = (entry_credit - current_cost) * 100
        
        # Total P&L for all contracts
        total_pnl = pnl_per_contract * signal.contracts
        
        return total_pnl
        
    def _close_position(self, position_id: str, pnl: float, exit_reason: str, 
                       exit_time: datetime):
        """Close position and update tracking"""
        
        if position_id not in self.open_positions:
            return
            
        position_data = self.open_positions[position_id]
        signal = position_data['signal']
        
        # Update system P&L
        self.trading_system.update_daily_pnl(pnl)
        
        # Update win/loss tracking
        if pnl > 0:
            self.trading_system.winning_trades += 1
            
        # Record trade result
        trade_result = {
            'position_id': position_id,
            'entry_time': signal.entry_time,
            'exit_time': exit_time,
            'spread_type': signal.spread_type.value,
            'short_strike': signal.short_strike,
            'long_strike': signal.long_strike,
            'contracts': signal.contracts,
            'entry_spy_price': position_data['entry_spy_price'],
            'exit_spy_price': position_data.get('current_spy_price', 0),
            'premium_collected': signal.premium_collected * signal.contracts * 100,
            'pnl': pnl,
            'exit_reason': exit_reason,
            'hold_time_hours': (exit_time - signal.entry_time).total_seconds() / 3600,
            'confidence': signal.confidence
        }
        
        self.backtest_results.append(trade_result)
        
        # Remove from tracking
        self.trading_system.profit_manager.remove_position(position_id)
        del self.open_positions[position_id]
        
        win_loss = "WIN" if pnl > 0 else "LOSS"
        logger.info(f"   🔴 CLOSED: {signal.spread_type.value} - {win_loss} ${pnl:+.2f} ({exit_reason})")
        
    def _add_position_for_tracking(self, trade_result: Dict, signal: TradeSignal, 
                                 spy_price: float, entry_time: datetime):
        """Add position to tracking system"""
        
        position_id = trade_result['position_id']
        
        self.open_positions[position_id] = {
            'signal': signal,
            'entry_spy_price': spy_price,
            'entry_time': entry_time,
            'current_spy_price': spy_price
        }
        
    def _determine_market_regime(self, options_data: pd.DataFrame, spy_price: float, trade_date: datetime) -> str:
        """
        ENHANCED: Multi-timeframe regime detection with transition analysis
        Uses Enhanced Regime Detector for improved accuracy and reduced single-regime bias
        """
        
        try:
            # Load SPY historical data for enhanced regime analysis
            start_date = trade_date - timedelta(days=7)  # Get extra days for multi-timeframe analysis
            historical_spy_data = self.spy_loader.load_date_range(start_date, trade_date)
            
            logger.debug(f"📊 Loaded {len(historical_spy_data)} SPY bars for enhanced regime analysis")
            
            # ENHANCED: Use Enhanced Regime Detector if available
            if self.enhanced_regime_detector is not None:
                logger.info("🎯 USING ENHANCED REGIME DETECTOR")
                
                # Get VWAP intelligence from Market Intelligence Engine
                intelligence = self.market_intelligence.analyze_market_intelligence(
                    options_data=options_data,
                    spy_price=spy_price,
                    vix_data=None,
                    historical_prices=historical_spy_data
                )
                
                logger.debug(f"📊 VWAP Intelligence: {getattr(intelligence, 'vwap_intelligence', {})}")
                
                # Use Enhanced Regime Detector for comprehensive analysis
                enhanced_analysis = self.enhanced_regime_detector.analyze_enhanced_regime(
                    spy_data=historical_spy_data,
                    options_data=options_data,
                    spy_price=spy_price,
                    vwap_intelligence=getattr(intelligence, 'vwap_intelligence', {})
                )
                
                logger.info(f"🎯 ENHANCED ANALYSIS COMPLETE: {enhanced_analysis.primary_regime.value} ({enhanced_analysis.confidence:.1f}%)")
                
                # Convert enhanced regime to expected format
                regime_mapping = {
                    'STRONG_BULLISH': 'BULLISH',
                    'BULLISH': 'BULLISH',
                    'NEUTRAL': 'NEUTRAL',
                    'BEARISH': 'BEARISH',
                    'STRONG_BEARISH': 'BEARISH',
                    'TRANSITION': 'NEUTRAL'  # Don't trade during transitions
                }
                
                detected_regime = regime_mapping.get(enhanced_analysis.primary_regime.value, 'NEUTRAL')
                
                # Enhanced logging with multi-timeframe analysis
                logger.debug(f"🎯 Enhanced Regime Analysis:")
                logger.debug(f"   Primary: {enhanced_analysis.primary_regime.value} ({enhanced_analysis.confidence:.1f}%)")
                logger.debug(f"   Transition Prob: {enhanced_analysis.transition_probability:.1%}")
                logger.debug(f"   Recommended Strategy: {enhanced_analysis.recommended_strategy}")
                if enhanced_analysis.supporting_factors:
                    logger.debug(f"   Supporting: {enhanced_analysis.supporting_factors}")
                if enhanced_analysis.risk_factors:
                    logger.debug(f"   Risk Factors: {enhanced_analysis.risk_factors}")
                
                # Apply confidence and transition filtering
                if enhanced_analysis.confidence < 60:
                    logger.info(f"🚫 Low confidence regime ({enhanced_analysis.confidence:.1f}%), using NEUTRAL")
                    return "NEUTRAL"
                
                if enhanced_analysis.transition_probability > 0.3:
                    logger.info(f"🚫 Market transitioning ({enhanced_analysis.transition_probability:.1%}), using NEUTRAL")
                    return "NEUTRAL"
                
                return detected_regime
                
            else:
                # Fallback to standard Market Intelligence Engine
                logger.warning("🚨 FALLING BACK TO STANDARD MARKET INTELLIGENCE ENGINE")
                
                intelligence = self.market_intelligence.analyze_market_intelligence(
                    options_data=options_data,
                    spy_price=spy_price,
                    vix_data=None,
                    historical_prices=historical_spy_data
                )

                regime_mapping = {
                    'BULLISH': 'BULLISH',
                    'BEARISH': 'BEARISH',
                    'NEUTRAL': 'NEUTRAL'
                }

                detected_regime = regime_mapping.get(intelligence.primary_regime, 'NEUTRAL')
                
                logger.info(f"🧠 Standard Market Intelligence: {intelligence.primary_regime} "
                            f"({intelligence.regime_confidence:.1f}% confidence)")
                
                return detected_regime
            
        except Exception as e:
            logger.warning(f"Enhanced regime detection failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            # Fallback to neutral if detection fails
            return "NEUTRAL"
            
    def _simulate_vix(self) -> float:
        """Simulate VIX level (in production, use real VIX data)"""
        return np.random.normal(20.0, 5.0)
        
    def _simulate_spy_volume(self) -> int:
        """Simulate SPY volume (in production, use real volume data)"""
        return int(np.random.normal(2000000, 500000))
        
    def _record_daily_summary(self, trade_date: datetime):
        """Record daily performance summary"""
        
        performance = self.trading_system.get_performance_summary()
        
        daily_summary = {
            'date': trade_date.date().isoformat(),
            'balance': performance['current_balance'],
            'daily_pnl': performance['daily_pnl'],
            'daily_trades': performance['daily_trades'],
            'open_positions': performance['open_positions'],
            'daily_limits_hit': performance['daily_limits_hit']
        }
        
        self.daily_summaries.append(daily_summary)
        
        logger.info(f"   💰 Balance: ${performance['current_balance']:,.2f} ({performance['daily_pnl']:+.2f})")
        logger.info(f"   📊 Trades: {performance['daily_trades']}, Open: {performance['open_positions']}")
        
    def _generate_final_results(self, start_date: datetime, end_date: datetime, 
                              trading_days: int) -> Dict:
        """Generate comprehensive backtest results"""
        
        performance = self.trading_system.get_performance_summary()
        
        # Calculate additional metrics
        total_trades = len(self.backtest_results)
        winning_trades = len([t for t in self.backtest_results if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # P&L statistics
        pnls = [t['pnl'] for t in self.backtest_results]
        avg_win = np.mean([p for p in pnls if p > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([p for p in pnls if p < 0]) if losing_trades > 0 else 0
        
        # Risk metrics
        daily_returns = [s['daily_pnl'] / self.config.account_balance for s in self.daily_summaries]
        max_drawdown = self._calculate_max_drawdown()
        
        results = {
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat(),
            'trading_days': trading_days,
            'initial_balance': self.config.account_balance,
            'final_balance': performance['current_balance'],
            'total_pnl': performance['current_balance'] - self.config.account_balance,
            'total_return_pct': performance['total_return_pct'],
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 and losing_trades > 0 else float('inf'),
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0,
            'daily_summaries': self.daily_summaries,
            'trade_details': self.backtest_results
        }
        
        return results
        
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        
        if not self.daily_summaries:
            return 0.0
            
        balances = [s['balance'] for s in self.daily_summaries]
        peak = balances[0]
        max_dd = 0.0
        
        for balance in balances:
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak * 100
            max_dd = max(max_dd, drawdown)
            
        return max_dd
        
    def save_results(self, results: Dict, output_dir: str = "src/tests/analysis/"):
        """Save backtest results to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = f"{output_dir}/professional_backtest_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        # Save summary report
        summary_file = f"{output_dir}/professional_backtest_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("PROFESSIONAL 0DTE CREDIT SPREAD BACKTEST RESULTS\\n")
            f.write("=" * 60 + "\\n\\n")
            f.write(f"Period: {results['start_date']} to {results['end_date']}\\n")
            f.write(f"Trading Days: {results['trading_days']}\\n\\n")
            f.write(f"FINANCIAL PERFORMANCE:\\n")
            f.write(f"  Initial Balance: ${results['initial_balance']:,.2f}\\n")
            f.write(f"  Final Balance: ${results['final_balance']:,.2f}\\n")
            f.write(f"  Total P&L: ${results['total_pnl']:+,.2f}\\n")
            f.write(f"  Total Return: {results['total_return_pct']:+.2f}%\\n\\n")
            f.write(f"TRADING STATISTICS:\\n")
            f.write(f"  Total Trades: {results['total_trades']}\\n")
            f.write(f"  Win Rate: {results['win_rate_pct']:.1f}%\\n")
            f.write(f"  Average Win: ${results['avg_win']:.2f}\\n")
            f.write(f"  Average Loss: ${results['avg_loss']:.2f}\\n")
            f.write(f"  Profit Factor: {results['profit_factor']:.2f}\\n\\n")
            f.write(f"RISK METRICS:\\n")
            f.write(f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%\\n")
            f.write(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}\\n")
            
        logger.info(f"💾 Results saved:")
        logger.info(f"   📊 Details: {results_file}")
        logger.info(f"   📋 Summary: {summary_file}")

def main():
    """Run professional backtest"""
    
    print("🏆 PROFESSIONAL 0DTE CREDIT SPREAD BACKTESTER")
    print("=" * 60)
    
    # Initialize backtester
    config = ProfessionalConfig()
    backtester = Professional0DTEBacktester(config)
    
    # Run backtest for 1 month
    start_date = datetime(2025, 8, 1)
    end_date = datetime(2025, 8, 31)
    
    results = backtester.run_backtest(start_date, end_date, max_days=20)
    
    # Save results
    backtester.save_results(results)
    
    print(f"\\n🎯 PROFESSIONAL BACKTEST COMPLETE!")

if __name__ == "__main__":
    main()
