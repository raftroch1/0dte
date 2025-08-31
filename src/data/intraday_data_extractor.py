#!/usr/bin/env python3
"""
🎯 SPY Intraday Data Extractor (1-Minute Bars)
==============================================

Extracts 1-minute intraday data from:
- Polygon.io: 1-minute stock and options bars
- Alpaca: 1-minute stock bars (backup)

Author: Advanced Options Trading System
Version: 1.0.0
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add environment variables
from dotenv import load_dotenv
load_dotenv()

class IntradayDataExtractor:
    """Intraday (1-minute) data extraction system"""
    
    def __init__(self):
        # API Keys
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        self.alpaca_api_key = os.getenv('ALPACA_API_KEY')
        self.alpaca_secret_key = os.getenv('ALPACA_API_SECRET')
        
        if not all([self.polygon_api_key, self.alpaca_api_key, self.alpaca_secret_key]):
            raise ValueError("Missing API keys in environment variables")
        
        # Initialize Alpaca SDK
        from alpaca.data.historical import StockHistoricalDataClient
        self.alpaca_stock_client = StockHistoricalDataClient(self.alpaca_api_key, self.alpaca_secret_key)
        
        # Data storage
        self.data_dir = "intraday_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        print(f"🚀 INTRADAY DATA EXTRACTOR INITIALIZED")
        print(f"📁 Cache directory: {self.data_dir}")
        print(f"🔑 APIs: Polygon.io ✅, Alpaca ✅")
        print(f"⏱️ Granularity: 1-minute bars")
    
    def extract_polygon_1min_stock_data(self, symbol: str, date: datetime) -> pd.DataFrame:
        """Extract 1-minute stock bars from Polygon.io for a single day"""
        print(f"\n📊 EXTRACTING 1-MIN STOCK DATA FROM POLYGON.IO")
        print(f"📅 Date: {date.strftime('%Y-%m-%d')}")
        print(f"📈 Symbol: {symbol}")
        
        try:
            date_str = date.strftime('%Y-%m-%d')
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{date_str}/{date_str}"
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 50000,  # Max limit for 1-minute bars
                'apikey': self.polygon_api_key
            }
            
            print(f"🔍 API call: {url}")
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                bars = data['results']
                
                # Convert to DataFrame
                bar_list = []
                for bar in bars:
                    bar_list.append({
                        'timestamp': datetime.fromtimestamp(bar['t'] / 1000),
                        'open': bar.get('o', 0),
                        'high': bar.get('h', 0),
                        'low': bar.get('l', 0),
                        'close': bar.get('c', 0),
                        'volume': bar.get('v', 0),
                        'vwap': bar.get('vw', 0),
                        'transactions': bar.get('n', 0)
                    })
                
                df = pd.DataFrame(bar_list)
                df = df.set_index('timestamp')
                
                # Save to cache
                cache_file = f"{self.data_dir}/{symbol.lower()}_1min_{date.strftime('%Y%m%d')}.csv"
                df.to_csv(cache_file)
                
                print(f"✅ Extracted {len(df)} 1-minute bars for {symbol}")
                print(f"💾 Cached to: {cache_file}")
                print(f"📊 Time range: {df.index[0]} to {df.index[-1]}")
                return df
            else:
                print(f"❌ No 1-minute data: {data.get('status', 'Unknown')} - {data.get('message', '')}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error extracting 1-minute stock data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def extract_polygon_1min_options_data(self, option_ticker: str, date: datetime) -> pd.DataFrame:
        """Extract 1-minute options bars from Polygon.io for a single day"""
        print(f"\n📊 EXTRACTING 1-MIN OPTIONS DATA FROM POLYGON.IO")
        print(f"📅 Date: {date.strftime('%Y-%m-%d')}")
        print(f"📈 Option: {option_ticker}")
        
        try:
            date_str = date.strftime('%Y-%m-%d')
            url = f"https://api.polygon.io/v2/aggs/ticker/{option_ticker}/range/1/minute/{date_str}/{date_str}"
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 50000,
                'apikey': self.polygon_api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                bars = data['results']
                
                # Convert to DataFrame
                bar_list = []
                for bar in bars:
                    bar_list.append({
                        'timestamp': datetime.fromtimestamp(bar['t'] / 1000),
                        'open': bar.get('o', 0),
                        'high': bar.get('h', 0),
                        'low': bar.get('l', 0),
                        'close': bar.get('c', 0),
                        'volume': bar.get('v', 0),
                        'vwap': bar.get('vw', 0),
                        'transactions': bar.get('n', 0)
                    })
                
                df = pd.DataFrame(bar_list)
                df = df.set_index('timestamp')
                
                # Save to cache
                safe_ticker = option_ticker.replace(':', '_')
                cache_file = f"{self.data_dir}/{safe_ticker}_1min_{date.strftime('%Y%m%d')}.csv"
                df.to_csv(cache_file)
                
                print(f"✅ Extracted {len(df)} 1-minute bars for {option_ticker}")
                print(f"💾 Cached to: {cache_file}")
                return df
            else:
                print(f"⚠️ No 1-minute options data: {data.get('status', 'Unknown')}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error extracting 1-minute options data: {e}")
            return pd.DataFrame()
    
    def extract_alpaca_1min_stock_data(self, symbol: str, date: datetime) -> pd.DataFrame:
        """Extract 1-minute stock bars from Alpaca for a single day"""
        print(f"\n📊 EXTRACTING 1-MIN STOCK DATA FROM ALPACA (BACKUP)")
        print(f"📅 Date: {date.strftime('%Y-%m-%d')}")
        print(f"📈 Symbol: {symbol}")
        
        try:
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
            
            # Create request for 1-minute bars
            start_time = datetime.combine(date.date(), datetime.min.time())
            end_time = start_time + timedelta(days=1)
            
            request_params = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Minute,
                start=start_time,
                end=end_time
            )
            
            # Get data
            bars = self.alpaca_stock_client.get_stock_bars(request_params)
            
            if bars.data and symbol in bars.data:
                # Convert to DataFrame
                bar_list = []
                for bar in bars.data[symbol]:
                    bar_list.append({
                        'timestamp': bar.timestamp,
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume
                    })
                
                df = pd.DataFrame(bar_list)
                df = df.set_index('timestamp')
                
                # Save to cache
                cache_file = f"{self.data_dir}/{symbol.lower()}_alpaca_1min_{date.strftime('%Y%m%d')}.csv"
                df.to_csv(cache_file)
                
                print(f"✅ Extracted {len(df)} 1-minute bars from Alpaca")
                print(f"💾 Cached to: {cache_file}")
                return df
            else:
                print(f"❌ No 1-minute data from Alpaca")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error extracting Alpaca 1-minute data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def extract_sample_trading_day(self, date: datetime):
        """Extract a full trading day of 1-minute data"""
        print(f"\n🚀 EXTRACTING FULL TRADING DAY: {date.strftime('%Y-%m-%d')}")
        print(f"=" * 60)
        
        # 1. Extract SPY 1-minute data from Polygon.io
        spy_polygon = self.extract_polygon_1min_stock_data('SPY', date)
        
        # 2. Extract SPY 1-minute data from Alpaca as backup
        spy_alpaca = self.extract_alpaca_1min_stock_data('SPY', date)
        
        # 3. Load some options contracts and extract their 1-minute data
        print(f"\n📋 LOADING OPTIONS CONTRACTS FOR SAMPLING...")
        
        try:
            with open('cached_data/polygon_spy_contracts_20250830.json', 'r') as f:
                contracts = json.load(f)
            
            # Filter for contracts that might have been active on this date
            active_contracts = []
            for contract in contracts:
                try:
                    exp_date = datetime.strptime(contract['expiration_date'], '%Y-%m-%d')
                    if exp_date >= date:  # Contract was active
                        active_contracts.append(contract)
                except:
                    continue
            
            print(f"📊 Found {len(active_contracts)} potentially active contracts")
            
            # Sample a few ATM options for testing
            if spy_polygon.empty:
                print(f"⚠️ No SPY price data, using estimated ATM strikes")
                atm_price = 600  # Estimate
            else:
                atm_price = spy_polygon['close'].iloc[-1]
                print(f"📊 SPY close price: ${atm_price:.2f}")
            
            # Find contracts near ATM
            atm_contracts = []
            for contract in active_contracts[:100]:  # Limit search
                try:
                    strike = float(contract['strike_price'])
                    if abs(strike - atm_price) <= 20:  # Within $20 of ATM
                        atm_contracts.append(contract)
                except:
                    continue
            
            print(f"📊 Found {len(atm_contracts)} near-ATM contracts")
            
            # Extract 1-minute data for a few sample contracts
            sample_contracts = atm_contracts[:5]  # Just 5 for testing
            options_data = {}
            
            for contract in sample_contracts:
                ticker = contract['ticker']
                option_df = self.extract_polygon_1min_options_data(ticker, date)
                if not option_df.empty:
                    options_data[ticker] = option_df
                
                # Rate limiting
                time.sleep(0.1)
            
            print(f"\n📊 EXTRACTION SUMMARY FOR {date.strftime('%Y-%m-%d')}")
            print(f"=" * 60)
            print(f"📈 SPY (Polygon): {len(spy_polygon)} bars")
            print(f"📈 SPY (Alpaca): {len(spy_alpaca)} bars")
            print(f"📊 Options contracts: {len(options_data)} with data")
            
            return {
                'spy_polygon': spy_polygon,
                'spy_alpaca': spy_alpaca,
                'options_data': options_data
            }
            
        except Exception as e:
            print(f"❌ Error in options extraction: {e}")
            return {
                'spy_polygon': spy_polygon,
                'spy_alpaca': spy_alpaca,
                'options_data': {}
            }

def main():
    """Main execution function"""
    print("🎯 SPY INTRADAY (1-MINUTE) DATA EXTRACTOR")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ['POLYGON_API_KEY', 'ALPACA_API_KEY', 'ALPACA_API_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set them in your .env file")
        return
    
    # Initialize extractor
    extractor = IntradayDataExtractor()
    
    # Extract a recent trading day (yesterday or last Friday)
    today = datetime.now().date()
    
    # Find last trading day (not weekend)
    test_date = today - timedelta(days=1)
    while test_date.weekday() >= 5:  # Saturday=5, Sunday=6
        test_date -= timedelta(days=1)
    
    print(f"\n📅 Testing with recent trading day: {test_date}")
    
    try:
        # Extract sample trading day
        results = extractor.extract_sample_trading_day(
            datetime.combine(test_date, datetime.min.time())
        )
        
        print(f"\n🎉 INTRADAY DATA EXTRACTION COMPLETED!")
        print(f"📁 All data cached in: {extractor.data_dir}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrupted by user")
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
