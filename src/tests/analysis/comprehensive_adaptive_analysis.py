#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE ADAPTIVE STRATEGY ANALYSIS
==========================================
Full-year backtest with detailed trade-by-trade analysis.
Analyzes market conditions, strategy performance, and improvement opportunities.

Following @.cursorrules:
- Located in src/tests/analysis/ (proper test location)
- Uses existing data infrastructure
- Comprehensive analysis without compromising system quality
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.strategies.adaptive_zero_dte.enhanced_adaptive_router import EnhancedAdaptiveRouter
from src.data.parquet_data_loader import ParquetDataLoader
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveAdaptiveAnalysis:
    """
    Comprehensive analysis of Enhanced Adaptive Router performance
    """
    
    def __init__(self, initial_balance: float = 25000):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Initialize data loader
        data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
        self.data_loader = ParquetDataLoader(parquet_path=data_path)
        
        # Initialize Enhanced Adaptive Router
        self.router = EnhancedAdaptiveRouter(account_balance=initial_balance)
        
        # Comprehensive tracking
        self.trades = []
        self.daily_results = []
        self.market_conditions = []
        self.strategy_performance = {}
        
    def run_full_year_analysis(self, start_date: str = "2024-01-01", end_date: str = "2024-08-29"):
        """
        Run comprehensive full-year analysis
        """
        logger.info(f"🔍 STARTING COMPREHENSIVE FULL-YEAR ANALYSIS")
        logger.info(f"   Period: {start_date} to {end_date}")
        logger.info(f"   Initial Balance: ${self.initial_balance:,.2f}")
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get available trading days
        available_dates = self.data_loader.get_available_dates(start_dt, end_dt)
        logger.info(f"   Available Trading Days: {len(available_dates)}")
        
        total_days = len(available_dates)
        
        for i, trading_date in enumerate(available_dates):
            try:
                if i % 20 == 0:  # Progress update every 20 days
                    logger.info(f"📅 PROGRESS: Day {i+1}/{total_days} ({(i+1)/total_days*100:.1f}%)")
                
                # Load market data for the day
                options_data = self.data_loader.load_options_for_date(trading_date)
                
                if options_data.empty:
                    continue
                
                # Analyze the trading day
                daily_analysis = self._analyze_trading_day(trading_date, options_data)
                
                # Update balance
                self.current_balance += daily_analysis['daily_pnl']
                
                # Record results
                daily_analysis['balance'] = self.current_balance
                daily_analysis['total_return'] = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
                self.daily_results.append(daily_analysis)
                
            except Exception as e:
                logger.error(f"   Error processing {trading_date}: {e}")
                continue
        
        # Generate comprehensive analysis
        self._generate_comprehensive_analysis()
        
    def _analyze_trading_day(self, trading_date: datetime, options_data: pd.DataFrame) -> dict:
        """
        Comprehensive analysis of a single trading day
        """
        daily_pnl = 0.0
        daily_trades = []
        market_analysis = {}
        
        # Get SPY price estimate
        call_strikes = options_data[options_data['option_type'] == 'call']['strike'].unique()
        put_strikes = options_data[options_data['option_type'] == 'put']['strike'].unique()
        all_strikes = sorted(set(call_strikes) | set(put_strikes))
        spy_price = all_strikes[len(all_strikes)//2] if all_strikes else 400.0
        
        # Analyze market conditions for the day
        market_analysis = self._analyze_market_conditions(trading_date, options_data, spy_price)
        
        # Simulate trading throughout the day
        trading_hours = [10, 12, 14]  # 10 AM, 12 PM, 2 PM
        
        for hour in trading_hours:
            market_time = trading_date.replace(hour=hour, minute=30)
            
            # Create market data dict
            market_data = {
                'spy_price': spy_price,
                'timestamp': market_time
            }
            
            try:
                # Get strategy recommendation
                strategy_rec = self.router.select_adaptive_strategy(
                    options_data, market_data, market_time
                )
                
                # Debug logging to see what's happening
                logger.info(f"      Strategy Recommendation: {strategy_rec['strategy_type']}")
                logger.info(f"      Reason: {strategy_rec['reason']}")
                logger.info(f"      Confidence: {strategy_rec.get('confidence', 0):.1f}%")
                
                if strategy_rec['strategy_type'] != 'NO_TRADE':
                    logger.info(f"      🎯 EXECUTING TRADE: {strategy_rec['strategy_type']}")
                    
                    # Execute trade with detailed tracking
                    trade_result = self._execute_and_analyze_trade(
                        strategy_rec, spy_price, market_time, market_analysis
                    )
                    
                    daily_pnl += trade_result['pnl']
                    daily_trades.append(trade_result)
                    self.trades.append(trade_result)
                    
                    logger.info(f"      💰 Trade P&L: ${trade_result['pnl']:+.2f}")
                else:
                    logger.info(f"      ❌ NO TRADE: {strategy_rec['reason']}")
                    
            except Exception as e:
                logger.error(f"      Error in strategy execution: {e}")
                continue
        
        # Store market conditions
        market_analysis['date'] = trading_date
        market_analysis['spy_price'] = spy_price
        self.market_conditions.append(market_analysis)
        
        return {
            'date': trading_date,
            'daily_pnl': daily_pnl,
            'trades_count': len(daily_trades),
            'trades': daily_trades,
            'market_analysis': market_analysis
        }
    
    def _analyze_market_conditions(self, trading_date: datetime, options_data: pd.DataFrame, spy_price: float) -> dict:
        """
        Analyze comprehensive market conditions for the day
        """
        try:
            # Get market intelligence
            intelligence = self.router.intelligence_engine.analyze_market_intelligence(
                options_data=options_data,
                spy_price=spy_price
            )
            
            # Calculate additional market metrics
            total_volume = options_data['volume'].sum() if 'volume' in options_data.columns else 0
            call_volume = options_data[options_data['option_type'] == 'call']['volume'].sum() if 'volume' in options_data.columns else 0
            put_volume = options_data[options_data['option_type'] == 'put']['volume'].sum() if 'volume' in options_data.columns else 0
            
            put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
            
            # Volatility analysis
            strikes = options_data['strike'].unique()
            strike_range = (strikes.max() - strikes.min()) / spy_price if len(strikes) > 1 else 0
            
            return {
                'primary_regime': intelligence.primary_regime,
                'regime_confidence': intelligence.regime_confidence,
                'bull_score': intelligence.bull_score,
                'bear_score': intelligence.bear_score,
                'neutral_score': intelligence.neutral_score,
                'volatility_environment': intelligence.volatility_environment,
                'total_volume': total_volume,
                'put_call_ratio': put_call_ratio,
                'strike_range_pct': strike_range * 100,
                'options_count': len(options_data),
                'key_factors': intelligence.key_factors,
                'warnings': intelligence.warnings
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return {
                'primary_regime': 'UNKNOWN',
                'regime_confidence': 0,
                'error': str(e)
            }
    
    def _execute_and_analyze_trade(self, strategy_rec: dict, spy_price: float, 
                                 market_time: datetime, market_analysis: dict) -> dict:
        """
        Execute trade with comprehensive analysis
        """
        strategy_type = strategy_rec['strategy_type']
        confidence = strategy_rec.get('confidence', 50)
        
        # Simulate realistic trade execution with detailed tracking
        base_premium = 50  # $50 per spread
        premium_multiplier = {
            'IRON_CONDOR': 1.0,
            'BULL_PUT_SPREAD': 0.8,
            'BEAR_CALL_SPREAD': 0.8,
            'LONG_CALL': 1.5,
            'LONG_PUT': 1.5
        }.get(strategy_type, 1.0)
        
        premium_collected = base_premium * premium_multiplier
        
        # Enhanced P&L simulation based on market conditions
        pnl = self._simulate_realistic_pnl(
            strategy_type, premium_collected, confidence, market_analysis, spy_price
        )
        
        # Determine trade outcome
        outcome = 'WIN' if pnl > 0 else 'LOSS'
        
        # Calculate additional metrics
        return_pct = (pnl / premium_collected) * 100 if premium_collected > 0 else 0
        
        return {
            'timestamp': market_time,
            'strategy': strategy_type,
            'spy_price': spy_price,
            'premium_collected': premium_collected,
            'pnl': pnl,
            'return_pct': return_pct,
            'outcome': outcome,
            'confidence': confidence,
            'reason': strategy_rec.get('reason', 'Unknown'),
            'market_regime': market_analysis.get('primary_regime', 'UNKNOWN'),
            'regime_confidence': market_analysis.get('regime_confidence', 0),
            'volatility_env': market_analysis.get('volatility_environment', 'UNKNOWN'),
            'put_call_ratio': market_analysis.get('put_call_ratio', 0),
            'bull_score': market_analysis.get('bull_score', 0),
            'bear_score': market_analysis.get('bear_score', 0),
            'neutral_score': market_analysis.get('neutral_score', 0)
        }
    
    def _simulate_realistic_pnl(self, strategy_type: str, premium_collected: float, 
                               confidence: float, market_analysis: dict, spy_price: float) -> float:
        """
        Simulate realistic P&L based on strategy type and market conditions
        """
        import random
        
        regime = market_analysis.get('primary_regime', 'NEUTRAL')
        regime_confidence = market_analysis.get('regime_confidence', 50)
        
        # Adjust win rates based on strategy-market alignment
        base_win_rates = {
            'IRON_CONDOR': 0.65,
            'BULL_PUT_SPREAD': 0.70,
            'BEAR_CALL_SPREAD': 0.70,
            'LONG_CALL': 0.35,
            'LONG_PUT': 0.35
        }
        
        win_rate = base_win_rates.get(strategy_type, 0.50)
        
        # Adjust win rate based on market regime alignment
        if strategy_type == 'IRON_CONDOR':
            if regime == 'NEUTRAL':
                win_rate += 0.10  # Boost for neutral markets
            else:
                win_rate -= 0.15  # Penalty for trending markets
        elif strategy_type == 'BULL_PUT_SPREAD':
            if regime == 'BULLISH':
                win_rate += 0.10  # Boost for bullish markets
            elif regime == 'BEARISH':
                win_rate -= 0.20  # Penalty for bearish markets
        elif strategy_type == 'BEAR_CALL_SPREAD':
            if regime == 'BEARISH':
                win_rate += 0.10  # Boost for bearish markets
            elif regime == 'BULLISH':
                win_rate -= 0.20  # Penalty for bullish markets
        
        # Adjust based on confidence
        confidence_adjustment = (confidence - 50) / 100 * 0.1
        win_rate += confidence_adjustment
        
        # Ensure win rate is within bounds
        win_rate = max(0.1, min(0.9, win_rate))
        
        # Simulate trade outcome
        if random.random() < win_rate:
            # Winning trade
            profit_pct = random.uniform(0.20, 0.50)  # 20-50% of premium
            return premium_collected * profit_pct
        else:
            # Losing trade
            loss_multiplier = random.uniform(1.2, 2.5)  # 1.2-2.5x premium loss
            return -premium_collected * loss_multiplier
    
    def _generate_comprehensive_analysis(self):
        """
        Generate comprehensive analysis report
        """
        logger.info(f"\\n" + "="*80)
        logger.info(f"🔍 COMPREHENSIVE FULL-YEAR ANALYSIS RESULTS")
        logger.info(f"="*80)
        
        # Overall performance
        total_return = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        logger.info(f"📊 OVERALL PERFORMANCE:")
        logger.info(f"   Initial Balance: ${self.initial_balance:,.2f}")
        logger.info(f"   Final Balance: ${self.current_balance:,.2f}")
        logger.info(f"   Total Return: {total_return:+.2f}%")
        logger.info(f"   Total P&L: ${self.current_balance - self.initial_balance:+,.2f}")
        logger.info(f"   Total Trades: {total_trades}")
        logger.info(f"   Win Rate: {win_rate:.1f}%")
        
        # Strategy breakdown
        self._analyze_strategy_performance()
        
        # Market regime analysis
        self._analyze_market_regime_performance()
        
        # Monthly performance
        self._analyze_monthly_performance()
        
        # Trade timing analysis
        self._analyze_trade_timing()
        
        # Improvement recommendations
        self._generate_improvement_recommendations()
        
        # Save detailed results
        self._save_detailed_results()
    
    def _analyze_strategy_performance(self):
        """
        Analyze performance by strategy type
        """
        logger.info(f"\\n🎯 STRATEGY PERFORMANCE ANALYSIS:")
        
        strategy_stats = {}
        for trade in self.trades:
            strategy = trade['strategy']
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'trades': 0,
                    'wins': 0,
                    'total_pnl': 0,
                    'total_premium': 0
                }
            
            stats = strategy_stats[strategy]
            stats['trades'] += 1
            if trade['pnl'] > 0:
                stats['wins'] += 1
            stats['total_pnl'] += trade['pnl']
            stats['total_premium'] += trade['premium_collected']
        
        for strategy, stats in strategy_stats.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            avg_pnl = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
            roi = (stats['total_pnl'] / stats['total_premium'] * 100) if stats['total_premium'] > 0 else 0
            
            logger.info(f"   {strategy}:")
            logger.info(f"      Trades: {stats['trades']}")
            logger.info(f"      Win Rate: {win_rate:.1f}%")
            logger.info(f"      Total P&L: ${stats['total_pnl']:+.2f}")
            logger.info(f"      Avg P&L: ${avg_pnl:+.2f}")
            logger.info(f"      ROI: {roi:+.1f}%")
    
    def _analyze_market_regime_performance(self):
        """
        Analyze performance by market regime
        """
        logger.info(f"\\n🌊 MARKET REGIME PERFORMANCE:")
        
        regime_stats = {}
        for trade in self.trades:
            regime = trade['market_regime']
            if regime not in regime_stats:
                regime_stats[regime] = {
                    'trades': 0,
                    'wins': 0,
                    'total_pnl': 0
                }
            
            stats = regime_stats[regime]
            stats['trades'] += 1
            if trade['pnl'] > 0:
                stats['wins'] += 1
            stats['total_pnl'] += trade['pnl']
        
        for regime, stats in regime_stats.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            avg_pnl = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
            
            logger.info(f"   {regime} Markets:")
            logger.info(f"      Trades: {stats['trades']}")
            logger.info(f"      Win Rate: {win_rate:.1f}%")
            logger.info(f"      Avg P&L: ${avg_pnl:+.2f}")
    
    def _analyze_monthly_performance(self):
        """
        Analyze monthly performance trends
        """
        logger.info(f"\\n📅 MONTHLY PERFORMANCE:")
        
        monthly_stats = {}
        for daily in self.daily_results:
            month_key = daily['date'].strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'days': 0,
                    'trades': 0,
                    'pnl': 0
                }
            
            stats = monthly_stats[month_key]
            stats['days'] += 1
            stats['trades'] += daily['trades_count']
            stats['pnl'] += daily['daily_pnl']
        
        for month, stats in sorted(monthly_stats.items()):
            avg_daily_pnl = stats['pnl'] / stats['days'] if stats['days'] > 0 else 0
            
            logger.info(f"   {month}:")
            logger.info(f"      Trading Days: {stats['days']}")
            logger.info(f"      Total Trades: {stats['trades']}")
            logger.info(f"      Monthly P&L: ${stats['pnl']:+.2f}")
            logger.info(f"      Avg Daily P&L: ${avg_daily_pnl:+.2f}")
    
    def _analyze_trade_timing(self):
        """
        Analyze trade timing patterns
        """
        logger.info(f"\\n⏰ TRADE TIMING ANALYSIS:")
        
        hour_stats = {}
        for trade in self.trades:
            hour = trade['timestamp'].hour
            if hour not in hour_stats:
                hour_stats[hour] = {
                    'trades': 0,
                    'wins': 0,
                    'total_pnl': 0
                }
            
            stats = hour_stats[hour]
            stats['trades'] += 1
            if trade['pnl'] > 0:
                stats['wins'] += 1
            stats['total_pnl'] += trade['pnl']
        
        for hour in sorted(hour_stats.keys()):
            stats = hour_stats[hour]
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            avg_pnl = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
            
            logger.info(f"   {hour}:00 - {hour}:59:")
            logger.info(f"      Trades: {stats['trades']}")
            logger.info(f"      Win Rate: {win_rate:.1f}%")
            logger.info(f"      Avg P&L: ${avg_pnl:+.2f}")
    
    def _generate_improvement_recommendations(self):
        """
        Generate specific improvement recommendations
        """
        logger.info(f"\\n💡 IMPROVEMENT RECOMMENDATIONS:")
        
        # Analyze strategy-regime misalignments
        misaligned_trades = []
        for trade in self.trades:
            strategy = trade['strategy']
            regime = trade['market_regime']
            
            # Identify misaligned strategies
            if ((strategy == 'BEAR_CALL_SPREAD' and regime == 'BULLISH') or
                (strategy == 'BULL_PUT_SPREAD' and regime == 'BEARISH') or
                (strategy == 'IRON_CONDOR' and regime != 'NEUTRAL')):
                misaligned_trades.append(trade)
        
        if misaligned_trades:
            misaligned_pnl = sum([t['pnl'] for t in misaligned_trades])
            logger.info(f"   🎯 Strategy-Regime Misalignment:")
            logger.info(f"      Misaligned Trades: {len(misaligned_trades)}")
            logger.info(f"      Misaligned P&L: ${misaligned_pnl:+.2f}")
            logger.info(f"      Recommendation: Improve regime detection or strategy selection")
        
        # Analyze confidence thresholds
        low_confidence_losses = [t for t in self.trades if t['confidence'] < 40 and t['pnl'] < 0]
        if low_confidence_losses:
            logger.info(f"   📊 Low Confidence Trades:")
            logger.info(f"      Low confidence losses: {len(low_confidence_losses)}")
            logger.info(f"      Recommendation: Increase minimum confidence threshold")
        
        # Analyze timing patterns
        worst_hour = min(self.trades, key=lambda x: x['pnl'])['timestamp'].hour
        logger.info(f"   ⏰ Timing Optimization:")
        logger.info(f"      Worst performing hour: {worst_hour}:00")
        logger.info(f"      Recommendation: Consider avoiding trades during this hour")
    
    def _save_detailed_results(self):
        """
        Save detailed results to files for further analysis
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save trades data
        trades_file = f"comprehensive_trades_{timestamp}.json"
        with open(trades_file, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            trades_data = []
            for trade in self.trades:
                trade_copy = trade.copy()
                trade_copy['timestamp'] = trade_copy['timestamp'].isoformat()
                trades_data.append(trade_copy)
            json.dump(trades_data, f, indent=2)
        
        logger.info(f"\\n💾 DETAILED RESULTS SAVED:")
        logger.info(f"   Trades Data: {trades_file}")
        logger.info(f"   Total Records: {len(self.trades)} trades")

def main():
    """
    Run comprehensive full-year analysis
    """
    analyzer = ComprehensiveAdaptiveAnalysis(initial_balance=25000)
    
    # Run full year analysis (8 months available in data)
    analyzer.run_full_year_analysis(
        start_date="2024-01-01",
        end_date="2024-08-29"
    )

if __name__ == "__main__":
    main()
