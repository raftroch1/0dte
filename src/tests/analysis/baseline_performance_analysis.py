#!/usr/bin/env python3
"""
Baseline Performance Analysis
============================

Phase 1 of ML workflow: Establish baseline performance of Enhanced 0DTE Strategy
with year-long real data before ML enhancement.

Location: src/tests/analysis/ (following .cursorrules structure)
Author: Advanced Options Trading System
"""

import sys
import os
# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

from src.data.parquet_data_loader import ParquetDataLoader
from src.strategies.enhanced_0dte.strategy import Enhanced0DTEStrategy, Enhanced0DTEBacktester

class BaselinePerformanceAnalyzer:
    """Analyze baseline performance with proper .cursorrules compliance"""
    
    def __init__(self):
        self.loader = ParquetDataLoader()
        self.strategy = Enhanced0DTEStrategy()
        
    def run_baseline_analysis_with_debug(self, start_date: datetime, end_date: datetime,
                                       max_days: int = 10) -> Dict:
        """Run baseline analysis with debug information to understand selectivity"""
        
        print("🎯 BASELINE PERFORMANCE ANALYSIS (Phase 1)")
        print("=" * 70)
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"🏗️ Following .cursorrules structure: src/tests/analysis/")
        print(f"=" * 70)
        
        available_dates = self.loader.get_available_dates(start_date, end_date)
        test_dates = available_dates[:max_days]
        
        analysis_results = {
            'dates_analyzed': len(test_dates),
            'signals_generated': 0,
            'signals_filtered_out': 0,
            'confidence_distribution': [],
            'market_conditions_summary': {},
            'liquidity_analysis': {},
            'daily_analysis': []
        }
        
        print(f"📊 Analyzing {len(test_dates)} trading days...")
        
        for i, test_date in enumerate(test_dates, 1):
            print(f"\n📅 Day {i}/{len(test_dates)}: {test_date.strftime('%Y-%m-%d')}")
            
            # Load data for the day
            options_data = self.loader.load_options_for_date(test_date, min_volume=5)
            market_conditions = self.loader.analyze_market_conditions(test_date)
            
            if options_data.empty:
                print(f"   ⚠️  No options data available")
                continue
            
            spy_price = self.loader._estimate_spy_price(options_data)
            if not spy_price:
                print(f"   ⚠️  Could not estimate SPY price")
                continue
                
            print(f"   📊 {len(options_data)} liquid options, SPY: ${spy_price:.2f}")
            
            # Analyze signal generation process
            day_analysis = self._analyze_signal_generation(
                options_data, market_conditions, spy_price, test_date
            )
            
            analysis_results['daily_analysis'].append(day_analysis)
            analysis_results['signals_generated'] += day_analysis['signals_generated']
            analysis_results['signals_filtered_out'] += day_analysis['signals_filtered_out']
            
            if day_analysis['confidence_scores']:
                analysis_results['confidence_distribution'].extend(day_analysis['confidence_scores'])
        
        # Generate comprehensive analysis
        self._generate_baseline_insights(analysis_results)
        
        # Save results following .cursorrules structure
        self._save_analysis_results(analysis_results, start_date, end_date)
        
        return analysis_results
    
    def _analyze_signal_generation(self, options_data: pd.DataFrame, 
                                 market_conditions: Dict, spy_price: float,
                                 current_date: datetime) -> Dict:
        """Analyze the signal generation process step by step"""
        
        day_analysis = {
            'date': current_date.isoformat(),
            'total_options': len(options_data),
            'market_regime': market_conditions.get('market_regime', 'UNKNOWN'),
            'put_call_ratio': market_conditions.get('put_call_ratio', 1.0),
            'signals_generated': 0,
            'signals_filtered_out': 0,
            'confidence_scores': [],
            'filter_reasons': [],
            'liquidity_stats': {}
        }
        
        # Step 1: Liquidity filtering
        liquid_options = self.strategy._filter_by_liquidity(options_data, spy_price)
        liquidity_filtered = len(options_data) - len(liquid_options)
        
        if liquidity_filtered > 0:
            day_analysis['filter_reasons'].append(f"Liquidity: {liquidity_filtered} options filtered")
        
        if liquid_options.empty:
            print(f"   ❌ All options filtered by liquidity requirements")
            return day_analysis
        
        # Step 2: Add Greeks
        try:
            options_with_greeks = self.strategy._add_greeks_to_options(liquid_options, spy_price)
            print(f"   ✅ Greeks calculated for {len(options_with_greeks)} options")
        except Exception as e:
            print(f"   ❌ Greeks calculation failed: {e}")
            return day_analysis
        
        # Step 3: Greeks filtering
        regime_params = self.strategy.regime_params.get(
            market_conditions.get('market_regime', 'NEUTRAL'), 
            self.strategy.regime_params['NEUTRAL']
        )
        
        greeks_filtered_options = self.strategy._filter_by_greeks(options_with_greeks, regime_params)
        greeks_filtered = len(options_with_greeks) - len(greeks_filtered_options)
        
        if greeks_filtered > 0:
            day_analysis['filter_reasons'].append(f"Greeks: {greeks_filtered} options filtered")
        
        if greeks_filtered_options.empty:
            print(f"   ❌ All options filtered by Greeks requirements")
            return day_analysis
        
        # Step 4: Technical signal generation
        signal = self.strategy._generate_technical_signal(
            greeks_filtered_options, market_conditions, current_date
        )
        
        if signal:
            print(f"   🎯 Technical signal generated: {signal['action']} ({signal['confidence']:.0f}%)")
            
            # Step 5: Enhanced signal with Greeks
            enhanced_signal = self.strategy._enhance_signal_with_greeks(
                signal, greeks_filtered_options, market_conditions
            )
            
            confidence = enhanced_signal['confidence']
            day_analysis['confidence_scores'].append(confidence)
            
            # Check confidence threshold
            market_regime = market_conditions.get('market_regime', 'NEUTRAL')
            min_confidence = self.strategy.min_confidence_thresholds.get(market_regime, 65)
            
            print(f"   📊 Enhanced confidence: {confidence:.1f}% (min required: {min_confidence}%)")
            
            if confidence >= min_confidence:
                day_analysis['signals_generated'] = 1
                print(f"   ✅ Signal ACCEPTED - meets confidence threshold")
            else:
                day_analysis['signals_filtered_out'] = 1
                day_analysis['filter_reasons'].append(f"Confidence: {confidence:.1f}% < {min_confidence}%")
                print(f"   ❌ Signal REJECTED - below confidence threshold")
        else:
            print(f"   ❌ No technical signal generated")
        
        return day_analysis
    
    def _generate_baseline_insights(self, results: Dict):
        """Generate insights from baseline analysis"""
        
        print(f"\n" + "=" * 70)
        print(f"📊 BASELINE ANALYSIS INSIGHTS")
        print(f"=" * 70)
        
        total_signals = results['signals_generated'] + results['signals_filtered_out']
        
        print(f"\n🎯 SIGNAL GENERATION SUMMARY:")
        print(f"   Days Analyzed: {results['dates_analyzed']}")
        print(f"   Signals Generated: {results['signals_generated']}")
        print(f"   Signals Filtered Out: {results['signals_filtered_out']}")
        print(f"   Total Signal Attempts: {total_signals}")
        
        if total_signals > 0:
            acceptance_rate = results['signals_generated'] / total_signals * 100
            print(f"   Signal Acceptance Rate: {acceptance_rate:.1f}%")
        
        # Confidence analysis
        if results['confidence_distribution']:
            confidences = results['confidence_distribution']
            print(f"\n📊 CONFIDENCE DISTRIBUTION:")
            print(f"   Average Confidence: {np.mean(confidences):.1f}%")
            print(f"   Confidence Range: {np.min(confidences):.1f}% - {np.max(confidences):.1f}%")
            print(f"   Median Confidence: {np.median(confidences):.1f}%")
        
        # Filter analysis
        all_filter_reasons = []
        for day in results['daily_analysis']:
            all_filter_reasons.extend(day['filter_reasons'])
        
        if all_filter_reasons:
            print(f"\n🔍 FILTERING ANALYSIS:")
            filter_counts = {}
            for reason in all_filter_reasons:
                filter_type = reason.split(':')[0]
                filter_counts[filter_type] = filter_counts.get(filter_type, 0) + 1
            
            for filter_type, count in filter_counts.items():
                print(f"   {filter_type} Filters: {count} instances")
        
        print(f"\n🎯 BASELINE ASSESSMENT:")
        if results['signals_generated'] == 0:
            print(f"   ⚠️  Strategy is highly selective - no trades executed")
            print(f"   📈 This indicates room for ML enhancement to find more opportunities")
            print(f"   ✅ High standards are working - quality over quantity approach")
        else:
            print(f"   ✅ Strategy generated {results['signals_generated']} trades")
            print(f"   📊 Ready for performance analysis")
    
    def _save_analysis_results(self, results: Dict, start_date: datetime, end_date: datetime):
        """Save analysis results following .cursorrules structure"""
        
        # Save in tests/analysis/ directory as per .cursorrules
        filename = f"baseline_analysis_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        analysis_data = {
            'analysis_date': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'strategy': 'Enhanced 0DTE with Greeks (Baseline Analysis)',
            'location': 'src/tests/analysis/ (following .cursorrules)',
            'results': results
        }
        
        with open(filepath, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"\n💾 Analysis saved to: {filepath}")

def main():
    """Run baseline performance analysis following .cursorrules"""
    
    print("🚀 BASELINE PERFORMANCE ANALYSIS - Phase 1")
    print("🏗️ Following .cursorrules: src/tests/analysis/")
    print("=" * 70)
    
    try:
        analyzer = BaselinePerformanceAnalyzer()
        
        # Analyze recent period with rich data
        end_date = datetime(2025, 8, 29)
        start_date = datetime(2025, 8, 20)  # 10 days for detailed analysis
        
        results = analyzer.run_baseline_analysis_with_debug(start_date, end_date, max_days=10)
        
        print(f"\n🎯 PHASE 1 COMPLETE - READY FOR PHASE 2")
        print(f"=" * 70)
        print(f"✅ Baseline analysis complete")
        print(f"✅ Strategy selectivity understood") 
        print(f"✅ Ready for ML feature engineering (Phase 2)")
        print(f"✅ Following .cursorrules structure")
        
        print(f"\n📋 NEXT STEPS:")
        print(f"1. 🤖 Phase 2: Generate ML features for signal enhancement")
        print(f"2. 🧠 Phase 3: Train ML models to find more opportunities") 
        print(f"3. 🔄 Phase 4: Integrate ML into enhanced strategy")
        print(f"4. 📊 Phase 5: Compare ML-enhanced vs baseline performance")
        
    except Exception as e:
        print(f"❌ Error in baseline analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
