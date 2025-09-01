#!/usr/bin/env python3
"""
Analyze P/C Ratios in Dataset
============================

Analyze the actual Put/Call ratio ranges in our dataset to determine
realistic thresholds for bullish/bearish/neutral detection.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.parquet_data_loader import ParquetDataLoader

def analyze_pc_ratios():
    """Analyze Put/Call ratios across the dataset"""
    
    print("📊 ANALYZING PUT/CALL RATIOS IN DATASET")
    print("="*50)
    
    # Load data
    loader = ParquetDataLoader(parquet_path="src/data/spy_options_20230830_20240829.parquet")
    
    # Sample dates to analyze
    sample_dates = [
        "2024-01-15", "2024-02-15", "2024-03-15", "2024-04-15",
        "2024-05-15", "2024-06-15", "2024-07-15", "2024-08-15"
    ]
    
    pc_ratios = []
    
    print("🔍 Sampling P/C ratios across different dates...")
    
    for date_str in sample_dates:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            options_data = loader.load_options_for_date(date_obj)
            if options_data is not None and len(options_data) > 0:
                
                # Calculate P/C ratio
                puts = options_data[options_data['option_type'] == 'put']
                calls = options_data[options_data['option_type'] == 'call']
                
                put_volume = puts['volume'].sum()
                call_volume = calls['volume'].sum()
                
                if call_volume > 0:
                    pc_ratio = put_volume / call_volume
                    pc_ratios.append(pc_ratio)
                    print(f"   {date_str}: P/C = {pc_ratio:.3f}")
                else:
                    print(f"   {date_str}: No call volume")
            else:
                print(f"   {date_str}: No data")
        except Exception as e:
            print(f"   {date_str}: Error - {e}")
    
    if pc_ratios:
        pc_array = np.array(pc_ratios)
        
        print(f"\n📈 PUT/CALL RATIO STATISTICS:")
        print(f"   Sample Size: {len(pc_ratios)} dates")
        print(f"   Minimum P/C: {pc_array.min():.3f}")
        print(f"   Maximum P/C: {pc_array.max():.3f}")
        print(f"   Mean P/C: {pc_array.mean():.3f}")
        print(f"   Median P/C: {np.median(pc_array):.3f}")
        print(f"   25th Percentile: {np.percentile(pc_array, 25):.3f}")
        print(f"   75th Percentile: {np.percentile(pc_array, 75):.3f}")
        
        print(f"\n🎯 RECOMMENDED THRESHOLDS:")
        
        # Calculate realistic thresholds based on data
        low_threshold = np.percentile(pc_array, 33)  # Bottom 33% = Bullish
        high_threshold = np.percentile(pc_array, 67)  # Top 33% = Bearish
        
        print(f"   BULLISH (Low P/C): < {low_threshold:.3f}")
        print(f"   NEUTRAL (Mid P/C): {low_threshold:.3f} - {high_threshold:.3f}")
        print(f"   BEARISH (High P/C): > {high_threshold:.3f}")
        
        print(f"\n🔧 CURRENT THRESHOLDS (NEED FIXING):")
        print(f"   BULLISH: < 1.000 (too restrictive)")
        print(f"   NEUTRAL: 1.000 - 1.150")
        print(f"   BEARISH: > 1.150")
        
        print(f"\n✅ SUGGESTED FIX:")
        print(f"   BULLISH: < {low_threshold:.3f}")
        print(f"   NEUTRAL: {low_threshold:.3f} - {high_threshold:.3f}")
        print(f"   BEARISH: > {high_threshold:.3f}")
        
        return {
            'min': pc_array.min(),
            'max': pc_array.max(),
            'mean': pc_array.mean(),
            'bullish_threshold': low_threshold,
            'bearish_threshold': high_threshold
        }
    else:
        print("❌ No P/C ratios found in sample")
        return None

if __name__ == "__main__":
    analyze_pc_ratios()
