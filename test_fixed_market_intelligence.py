#!/usr/bin/env python3
"""
🔧 TEST FIXED MARKET INTELLIGENCE
=================================
Test the fixed market intelligence engine to verify it can detect BULLISH markets
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.strategies.market_intelligence.intelligence_engine import MarketIntelligenceEngine
from src.data.parquet_data_loader import ParquetDataLoader

def test_market_intelligence_fix():
    """Test the fixed market intelligence on known bull market data"""
    
    print("🔧 TESTING FIXED MARKET INTELLIGENCE ENGINE")
    print("=" * 60)
    
    # Initialize components
    data_path = os.path.join(project_root, "src/data/spy_options_20230830_20240829.parquet")
    data_loader = ParquetDataLoader(parquet_path=data_path)
    intelligence_engine = MarketIntelligenceEngine()
    
    # Test on multiple dates during 2024 bull market
    test_dates = [
        datetime(2024, 1, 15),  # Early 2024
        datetime(2024, 3, 15),  # Mid Q1
        datetime(2024, 5, 15),  # Mid year
        datetime(2024, 7, 15),  # Mid Q3
    ]
    
    print(f"\n🧪 TESTING ON {len(test_dates)} DATES FROM 2024 BULL MARKET:")
    print(f"   (SPY went from ~$460 to ~$538 = +17% in 2024)")
    
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    
    for test_date in test_dates:
        try:
            # Load options data
            options_data = data_loader.load_options_for_date(test_date)
            
            if options_data.empty:
                print(f"   ❌ {test_date.strftime('%Y-%m-%d')}: No data available")
                continue
            
            # Estimate SPY price from options
            spy_price = intelligence_engine._estimate_current_price(options_data)
            
            # Run market intelligence
            intelligence = intelligence_engine.analyze_market_intelligence(
                options_data=options_data,
                spy_price=spy_price
            )
            
            # Track results
            if intelligence.primary_regime == 'BULLISH':
                bullish_count += 1
                emoji = "🟢"
            elif intelligence.primary_regime == 'BEARISH':
                bearish_count += 1
                emoji = "🔴"
            else:
                neutral_count += 1
                emoji = "🟡"
            
            print(f"   {emoji} {test_date.strftime('%Y-%m-%d')}: {intelligence.primary_regime} "
                  f"({intelligence.regime_confidence:.1f}%) | SPY: ${spy_price:.2f}")
            
            # Show key factors
            print(f"      Bull: {intelligence.bull_score:.1f} | Bear: {intelligence.bear_score:.1f} | "
                  f"Neutral: {intelligence.neutral_score:.1f}")
            
            # Show P/C analysis
            pc_analysis = intelligence.put_call_analysis
            print(f"      P/C Ratio: {pc_analysis['put_call_ratio']:.2f} ({pc_analysis['interpretation']})")
            
        except Exception as e:
            print(f"   ❌ {test_date.strftime('%Y-%m-%d')}: Error - {e}")
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   🟢 BULLISH: {bullish_count}/{len(test_dates)} ({bullish_count/len(test_dates)*100:.1f}%)")
    print(f"   🔴 BEARISH: {bearish_count}/{len(test_dates)} ({bearish_count/len(test_dates)*100:.1f}%)")
    print(f"   🟡 NEUTRAL: {neutral_count}/{len(test_dates)} ({neutral_count/len(test_dates)*100:.1f}%)")
    
    # Evaluate fix success
    if bullish_count > bearish_count:
        print(f"\n✅ FIX SUCCESSFUL! Market intelligence now detects BULLISH bias in bull market")
    else:
        print(f"\n❌ FIX INCOMPLETE: Still detecting too much bearish bias")
    
    return bullish_count, bearish_count, neutral_count

if __name__ == "__main__":
    test_market_intelligence_fix()
