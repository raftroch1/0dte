#!/usr/bin/env python3
"""
SPY 1-Minute Data Loader
========================

High-performance loader for SPY 1-minute bar data to support VWAP analysis.
Provides filtered data for specific date ranges and trading hours.

Location: src/data/ (following .cursorrules structure)
Author: Advanced Options Trading System - Data Infrastructure
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from typing import Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)

class SPY1MinuteLoader:
    """
    High-performance SPY 1-minute data loader for VWAP analysis
    
    Features:
    - Efficient date range filtering
    - Trading hours filtering (9:30 AM - 4:00 PM ET)
    - Memory-optimized loading
    - Data validation and cleaning
    """
    
    def __init__(self, data_path: str = "src/data/spy_1minute_data/SPY_1min_20230801_20240930.csv"):
        """Initialize SPY data loader"""
        
        self.data_path = data_path
        self.data_cache = None
        self.cache_start_date = None
        self.cache_end_date = None
        
        # Trading hours (ET)
        self.market_open = time(9, 30)
        self.market_close = time(16, 0)
        
        logger.info("🎯 SPY 1-MINUTE DATA LOADER INITIALIZED")
        logger.info(f"   Data Path: {data_path}")
        
        # Verify file exists
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"SPY data file not found: {data_path}")
        
        # Get file info
        file_size = os.path.getsize(data_path) / (1024 * 1024)  # MB
        logger.info(f"   File Size: {file_size:.1f} MB")
    
    def load_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        trading_hours_only: bool = True
    ) -> pd.DataFrame:
        """
        Load SPY data for specific date range
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            trading_hours_only: Filter to 9:30 AM - 4:00 PM ET only
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        
        logger.info(f"📊 LOADING SPY DATA: {start_date.date()} to {end_date.date()}")
        
        try:
            # Check if we can use cached data
            if (self.data_cache is not None and 
                self.cache_start_date <= start_date and 
                self.cache_end_date >= end_date):
                
                logger.info("   ✅ Using cached data")
                data = self.data_cache.copy()
            else:
                # Load fresh data
                logger.info("   📁 Loading from file...")
                data = pd.read_csv(self.data_path)
                logger.info(f"   📊 Loaded {len(data):,} rows")
                
                # Convert timestamp
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                
                # Cache the data
                self.data_cache = data.copy()
                self.cache_start_date = data['timestamp'].min()
                self.cache_end_date = data['timestamp'].max()
                
                logger.info(f"   📅 Data Range: {self.cache_start_date.date()} to {self.cache_end_date.date()}")
            
            # Filter by date range
            mask = (data['timestamp'].dt.date >= start_date.date()) & (data['timestamp'].dt.date <= end_date.date())
            data = data[mask].copy()
            
            logger.info(f"   🎯 Date Filtered: {len(data):,} rows")
            
            # Filter by trading hours if requested
            if trading_hours_only:
                time_mask = (
                    (data['timestamp'].dt.time >= self.market_open) & 
                    (data['timestamp'].dt.time <= self.market_close)
                )
                data = data[time_mask].copy()
                logger.info(f"   ⏰ Trading Hours Filtered: {len(data):,} rows")
            
            # Data validation and cleaning
            data = self._clean_data(data)
            
            # Set timestamp as index for VWAP calculations
            data.set_index('timestamp', inplace=True)
            
            logger.info(f"   ✅ Final Dataset: {len(data):,} rows")
            logger.info(f"   📊 Price Range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
            logger.info(f"   📈 Volume Range: {data['volume'].min():,.0f} - {data['volume'].max():,.0f}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading SPY data: {e}")
            raise
    
    def load_trading_day(self, date: datetime) -> pd.DataFrame:
        """
        Load SPY data for a specific trading day
        
        Args:
            date: Trading date
            
        Returns:
            DataFrame with intraday 1-minute bars
        """
        
        return self.load_date_range(date, date, trading_hours_only=True)
    
    def get_current_price(self, timestamp: datetime) -> Optional[float]:
        """
        Get SPY price at specific timestamp (or closest available)
        
        Args:
            timestamp: Target timestamp
            
        Returns:
            SPY close price or None if not available
        """
        
        try:
            # Load data around the timestamp
            start_date = timestamp - timedelta(days=1)
            end_date = timestamp + timedelta(days=1)
            
            data = self.load_date_range(start_date, end_date)
            
            if data.empty:
                return None
            
            # Find closest timestamp
            closest_idx = data.index.get_indexer([timestamp], method='nearest')[0]
            
            if closest_idx >= 0 and closest_idx < len(data):
                return float(data.iloc[closest_idx]['close'])
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting current price: {e}")
            return None
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate SPY data"""
        
        initial_rows = len(data)
        
        # Remove rows with missing data
        data = data.dropna()
        
        # Remove rows with zero or negative prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            data = data[data[col] > 0]
        
        # Remove rows with zero volume
        data = data[data['volume'] > 0]
        
        # Validate OHLC relationships
        data = data[
            (data['high'] >= data['open']) &
            (data['high'] >= data['close']) &
            (data['low'] <= data['open']) &
            (data['low'] <= data['close'])
        ]
        
        # Remove extreme outliers (price moves > 10% in 1 minute)
        data['price_change'] = data['close'].pct_change()
        data = data[abs(data['price_change']) <= 0.10]
        data.drop('price_change', axis=1, inplace=True)
        
        cleaned_rows = len(data)
        removed_rows = initial_rows - cleaned_rows
        
        if removed_rows > 0:
            logger.info(f"   🧹 Cleaned Data: Removed {removed_rows:,} invalid rows")
        
        return data
    
    def get_data_summary(self) -> dict:
        """Get summary statistics of available data"""
        
        if self.data_cache is None:
            # Load a sample to get info
            sample_data = pd.read_csv(self.data_path, nrows=1000)
            sample_data['timestamp'] = pd.to_datetime(sample_data['timestamp'])
            
            return {
                'file_path': self.data_path,
                'sample_start': sample_data['timestamp'].min(),
                'sample_end': sample_data['timestamp'].max(),
                'estimated_rows': 'Unknown (not fully loaded)'
            }
        else:
            return {
                'file_path': self.data_path,
                'start_date': self.cache_start_date,
                'end_date': self.cache_end_date,
                'total_rows': len(self.data_cache),
                'price_range': f"${self.data_cache['close'].min():.2f} - ${self.data_cache['close'].max():.2f}",
                'volume_range': f"{self.data_cache['volume'].min():,.0f} - {self.data_cache['volume'].max():,.0f}"
            }

def main():
    """Test the SPY data loader"""
    
    print("🎯 TESTING SPY 1-MINUTE DATA LOADER")
    print("=" * 50)
    
    # Initialize loader
    loader = SPY1MinuteLoader()
    
    # Test loading a specific date range
    start_date = datetime(2024, 1, 2)
    end_date = datetime(2024, 1, 5)
    
    print(f"\n📊 Loading test data: {start_date.date()} to {end_date.date()}")
    
    data = loader.load_date_range(start_date, end_date)
    
    print(f"\n✅ LOADED DATA SUMMARY:")
    print(f"   Rows: {len(data):,}")
    print(f"   Columns: {list(data.columns)}")
    print(f"   Date Range: {data.index.min()} to {data.index.max()}")
    print(f"   Price Range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    print(f"   Volume Range: {data['volume'].min():,.0f} - {data['volume'].max():,.0f}")
    
    # Test single day loading
    print(f"\n📅 Loading single day: {start_date.date()}")
    single_day = loader.load_trading_day(start_date)
    print(f"   Single Day Rows: {len(single_day):,}")
    
    # Test current price lookup
    test_timestamp = datetime(2024, 1, 2, 10, 30)
    current_price = loader.get_current_price(test_timestamp)
    print(f"\n💰 Price at {test_timestamp}: ${current_price:.2f}")
    
    print(f"\n🎯 SPY DATA LOADER TEST COMPLETE!")

if __name__ == "__main__":
    main()
