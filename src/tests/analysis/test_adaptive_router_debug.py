#!/usr/bin/env python3
"""
🧪 DEBUG ENHANCED ADAPTIVE ROUTER TEST
====================================
Debug version to understand why no trades are executing.
Add verbose logging to see strategy selection decisions.

Following @.cursorrules:
- Located in src/tests/analysis/ (proper test location)
- Uses existing data infrastructure
- Extends existing backtesting framework
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.strategies.adaptive_zero_dte.enhanced_adaptive_router import EnhancedAdaptiveRouter
from src.data.parquet_data_loader import ParquetDataLoader
from datetime import datetime, timedelta
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DebugAdaptiveRouterTest:
    """
    Debug test for Enhanced Adaptive Router
    Shows detailed decision-making process
    """
    
    def __init__(self, initial_balance: float = 25000):
        self.initial_balance = initial_balance
        
        # Initialize data loader
        data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
        self.data_loader = ParquetDataLoader(parquet_path=data_path)
        
        # Initialize Enhanced Adaptive Router
        self.router = EnhancedAdaptiveRouter(account_balance=initial_balance)
        
    def test_single_day_detailed(self, test_date: str = "2024-06-14"):
        """
        Test a single day with detailed logging
        """
        logger.info(f"🔍 DETAILED SINGLE DAY TEST")
        logger.info(f"   Date: {test_date}")
        logger.info(f"   Purpose: Debug strategy selection process")
        
        test_dt = datetime.strptime(test_date, "%Y-%m-%d")
        
        # Load market data for the day
        logger.info(f"📊 Loading options data for {test_date}...")
        options_data = self.data_loader.load_options_for_date(test_dt)
        
        if options_data.empty:
            logger.warning(f"❌ No data available for {test_date}")
            return
        
        logger.info(f"✅ Loaded {len(options_data)} options")
        
        # Get SPY price estimate
        call_strikes = options_data[options_data['option_type'] == 'call']['strike'].unique()
        put_strikes = options_data[options_data['option_type'] == 'put']['strike'].unique()
        all_strikes = sorted(set(call_strikes) | set(put_strikes))
        spy_price = all_strikes[len(all_strikes)//2] if all_strikes else 400.0
        
        logger.info(f"📈 Estimated SPY Price: ${spy_price:.2f}")
        
        # Test different times throughout the day
        test_times = [
            (9, 45),   # Market open
            (10, 30),  # Mid-morning
            (12, 0),   # Noon
            (14, 0),   # Afternoon
            (14, 30),  # Near cutoff
            (15, 0),   # After cutoff
        ]
        
        for hour, minute in test_times:
            market_time = test_dt.replace(hour=hour, minute=minute)
            logger.info(f"\\n⏰ TESTING TIME: {market_time.strftime('%H:%M')}")
            
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
                
                logger.info(f"   🎯 Strategy: {strategy_rec.get('strategy_type', 'UNKNOWN')}")
                logger.info(f"   📊 Confidence: {strategy_rec.get('confidence', 0):.1f}%")
                logger.info(f"   💭 Reason: {strategy_rec.get('reason', 'No reason provided')}")
                
                # Show additional details if available
                if 'market_regime' in strategy_rec:
                    logger.info(f"   🌊 Market Regime: {strategy_rec['market_regime']}")
                if 'risk_level' in strategy_rec:
                    logger.info(f"   ⚠️  Risk Level: {strategy_rec['risk_level']}")
                if 'expected_return' in strategy_rec:
                    logger.info(f"   💰 Expected Return: {strategy_rec['expected_return']:.2f}%")
                
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
                import traceback
                logger.error(f"   📋 Traceback: {traceback.format_exc()}")
    
    def test_multiple_dates(self, start_date: str = "2024-06-10", end_date: str = "2024-06-20"):
        """
        Test multiple dates to find trading opportunities
        """
        logger.info(f"🔍 MULTI-DAY SEARCH FOR TRADING OPPORTUNITIES")
        logger.info(f"   Period: {start_date} to {end_date}")
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get available trading days
        available_dates = self.data_loader.get_available_dates(start_dt, end_dt)
        logger.info(f"   Available Trading Days: {len(available_dates)}")
        
        trade_opportunities = []
        
        for i, trading_date in enumerate(available_dates):
            logger.info(f"\\n📅 DAY {i+1}/{len(available_dates)}: {trading_date.strftime('%Y-%m-%d')}")
            
            try:
                # Load market data
                options_data = self.data_loader.load_options_for_date(trading_date)
                
                if options_data.empty:
                    logger.warning(f"   ❌ No data available")
                    continue
                
                # Get SPY price
                call_strikes = options_data[options_data['option_type'] == 'call']['strike'].unique()
                put_strikes = options_data[options_data['option_type'] == 'put']['strike'].unique()
                all_strikes = sorted(set(call_strikes) | set(put_strikes))
                spy_price = all_strikes[len(all_strikes)//2] if all_strikes else 400.0
                
                # Test optimal trading time (12:00 PM)
                market_time = trading_date.replace(hour=12, minute=0)
                market_data = {
                    'spy_price': spy_price,
                    'timestamp': market_time
                }
                
                # Get strategy recommendation
                strategy_rec = self.router.select_adaptive_strategy(
                    options_data, market_data, market_time
                )
                
                strategy_type = strategy_rec.get('strategy_type', 'NO_TRADE')
                confidence = strategy_rec.get('confidence', 0)
                reason = strategy_rec.get('reason', 'Unknown')
                
                logger.info(f"   🎯 {strategy_type} | Confidence: {confidence:.1f}% | SPY: ${spy_price:.2f}")
                logger.info(f"   💭 {reason}")
                
                if strategy_type != 'NO_TRADE':
                    trade_opportunities.append({
                        'date': trading_date,
                        'strategy': strategy_type,
                        'confidence': confidence,
                        'spy_price': spy_price,
                        'reason': reason
                    })
                    logger.info(f"   ✅ TRADE OPPORTUNITY FOUND!")
                
            except Exception as e:
                logger.error(f"   ❌ Error processing {trading_date}: {e}")
        
        # Summary
        logger.info(f"\\n" + "="*60)
        logger.info(f"🎯 TRADE OPPORTUNITIES SUMMARY")
        logger.info(f"="*60)
        logger.info(f"📊 Total Days Tested: {len(available_dates)}")
        logger.info(f"🎯 Trade Opportunities Found: {len(trade_opportunities)}")
        
        if trade_opportunities:
            logger.info(f"\\n📋 TRADE OPPORTUNITIES:")
            for opp in trade_opportunities:
                logger.info(f"   {opp['date'].strftime('%Y-%m-%d')}: {opp['strategy']} | "
                          f"Confidence: {opp['confidence']:.1f}% | SPY: ${opp['spy_price']:.2f}")
                logger.info(f"      Reason: {opp['reason']}")
        else:
            logger.info(f"\\n❌ NO TRADE OPPORTUNITIES FOUND")
            logger.info(f"   This suggests:")
            logger.info(f"   - Market conditions were not suitable for any strategies")
            logger.info(f"   - Risk management filters are working correctly")
            logger.info(f"   - Time filters may be too restrictive")
            logger.info(f"   - Market regime detection is being conservative")
        
        logger.info(f"="*60)

def main():
    """
    Run debug tests
    """
    tester = DebugAdaptiveRouterTest(initial_balance=25000)
    
    # Test 1: Single day detailed analysis
    logger.info(f"\\n🧪 TEST 1: SINGLE DAY DETAILED ANALYSIS")
    tester.test_single_day_detailed("2024-06-14")  # A specific day from our previous tests
    
    # Test 2: Multi-day search for opportunities
    logger.info(f"\\n🧪 TEST 2: MULTI-DAY OPPORTUNITY SEARCH")
    tester.test_multiple_dates("2024-06-10", "2024-06-20")  # 2-week period

if __name__ == "__main__":
    main()
