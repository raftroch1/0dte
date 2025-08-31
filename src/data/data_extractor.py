#!/usr/bin/env python3
"""
🎯 SPY Options Data Extractor
============================

Extracts and caches 1 year of real historical data from:
- Polygon.io: Options contracts and historical bars (Options Starter Plan)
- Alpaca: Stock data and options chain (backup)
- Yahoo Finance: VIX data

Caches data locally for fast backtesting without API rate limits.

Author: Advanced Options Trading System
Version: 1.0.0
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
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

class DataExtractor:
    """Main data extraction and caching system"""
    
    def __init__(self):
        # API Keys
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        self.alpaca_api_key = os.getenv('ALPACA_API_KEY')
        self.alpaca_secret_key = os.getenv('ALPACA_API_SECRET')
        
        if not all([self.polygon_api_key, self.alpaca_api_key, self.alpaca_secret_key]):
            raise ValueError("Missing API keys in environment variables")
        
        # Initialize Alpaca SDK
        from alpaca.data.historical import StockHistoricalDataClient, OptionHistoricalDataClient
        self.alpaca_stock_client = StockHistoricalDataClient(self.alpaca_api_key, self.alpaca_secret_key)
        self.alpaca_option_client = OptionHistoricalDataClient(self.alpaca_api_key, self.alpaca_secret_key)
        
        # Data storage
        self.data_dir = "cached_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        print(f"🚀 DATA EXTRACTOR INITIALIZED")
        print(f"📁 Cache directory: {self.data_dir}")
        print(f"🔑 APIs: Polygon.io ✅, Alpaca ✅")
    
    def extract_spy_stock_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Extract SPY stock data from Alpaca"""
        print(f"\n📊 EXTRACTING SPY STOCK DATA")
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        try:
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
            
            # Create request
            request_params = StockBarsRequest(
                symbol_or_symbols=['SPY'],
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date
            )
            
            # Get data
            bars = self.alpaca_stock_client.get_stock_bars(request_params)
            
            if bars.data and 'SPY' in bars.data:
                # Convert to DataFrame
                bar_list = []
                for bar in bars.data['SPY']:
                    bar_list.append({
                        'date': bar.timestamp.date(),
                        'timestamp': bar.timestamp,
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume
                    })
                
                df = pd.DataFrame(bar_list)
                df = df.set_index('date')
                
                # Save to cache
                cache_file = f"{self.data_dir}/spy_stock_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                df.to_csv(cache_file)
                
                print(f"✅ Extracted {len(df)} SPY stock bars")
                print(f"💾 Cached to: {cache_file}")
                return df
            else:
                print(f"❌ No SPY stock data received from Alpaca")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error extracting SPY stock data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def extract_vix_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Extract VIX data from Yahoo Finance"""
        print(f"\n📈 EXTRACTING VIX DATA")
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        try:
            # Download VIX data
            vix = yf.download('^VIX', start=start_date, end=end_date + timedelta(days=1), progress=False)
            
            if not vix.empty:
                # Clean and prepare data
                vix_df = vix[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                vix_df.columns = ['open', 'high', 'low', 'close', 'volume']
                vix_df.index.name = 'date'
                
                # Save to cache
                cache_file = f"{self.data_dir}/vix_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                vix_df.to_csv(cache_file)
                
                print(f"✅ Extracted {len(vix_df)} VIX bars")
                print(f"💾 Cached to: {cache_file}")
                return vix_df
            else:
                print(f"❌ No VIX data received from Yahoo Finance")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error extracting VIX data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def extract_polygon_options_contracts(self, symbol: str = 'SPY') -> List[Dict]:
        """Extract ALL available options contracts from Polygon.io"""
        print(f"\n🔍 EXTRACTING OPTIONS CONTRACTS FROM POLYGON.IO")
        print(f"📊 Symbol: {symbol}")
        
        try:
            url = f"https://api.polygon.io/v3/reference/options/contracts"
            params = {
                'underlying_ticker': symbol,
                'limit': 1000,
                'apikey': self.polygon_api_key
            }
            
            all_contracts = []
            next_url = None
            page = 1
            
            while True:
                print(f"📄 Fetching page {page}...")
                
                if next_url:
                    response = requests.get(next_url, timeout=30)
                else:
                    response = requests.get(url, params=params, timeout=30)
                
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    contracts = data['results']
                    all_contracts.extend(contracts)
                    print(f"   📋 Got {len(contracts)} contracts (Total: {len(all_contracts)})")
                    
                    # Check for next page
                    if data.get('next_url'):
                        next_url = data['next_url'] + f"&apikey={self.polygon_api_key}"
                        page += 1
                        time.sleep(0.1)  # Rate limiting
                    else:
                        break
                else:
                    print(f"⚠️ No more contracts: {data.get('status', 'Unknown')}")
                    break
            
            if all_contracts:
                # Save contracts to cache
                cache_file = f"{self.data_dir}/polygon_spy_contracts_{datetime.now().strftime('%Y%m%d')}.json"
                with open(cache_file, 'w') as f:
                    json.dump(all_contracts, f, indent=2)
                
                print(f"✅ Extracted {len(all_contracts)} total options contracts")
                print(f"💾 Cached to: {cache_file}")
                
                # Show sample contracts
                print(f"\n📊 Sample contracts:")
                for i, contract in enumerate(all_contracts[:5]):
                    exp_date = contract.get('expiration_date', 'N/A')
                    strike = contract.get('strike_price', 'N/A')
                    contract_type = contract.get('contract_type', 'N/A')
                    ticker = contract.get('ticker', 'N/A')
                    print(f"   {i+1}. {ticker} - {contract_type.upper()} ${strike} exp {exp_date}")
                
                return all_contracts
            else:
                print(f"❌ No contracts extracted")
                return []
                
        except Exception as e:
            print(f"❌ Error extracting options contracts: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_polygon_options_bars(self, contracts: List[Dict], start_date: datetime, end_date: datetime) -> Dict:
        """Extract historical options bars for contracts"""
        print(f"\n📊 EXTRACTING OPTIONS BARS FROM POLYGON.IO")
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"📋 Contracts: {len(contracts)}")
        
        # Filter contracts by expiration (only get contracts that were active during our period)
        active_contracts = []
        for contract in contracts:
            try:
                exp_date = datetime.strptime(contract['expiration_date'], '%Y-%m-%d')
                if exp_date >= start_date:  # Contract was active during our period
                    active_contracts.append(contract)
            except:
                continue
        
        print(f"📋 Active contracts during period: {len(active_contracts)}")
        
        if not active_contracts:
            print(f"❌ No active contracts found for the period")
            return {}
        
        # Limit to reasonable number for testing
        sample_contracts = active_contracts[:100]  # Start with 100 contracts
        print(f"📋 Sampling {len(sample_contracts)} contracts for extraction")
        
        all_options_data = {}
        
        # Process contracts in batches
        batch_size = 10
        for i in range(0, len(sample_contracts), batch_size):
            batch = sample_contracts[i:i+batch_size]
            print(f"📦 Processing batch {i//batch_size + 1}/{(len(sample_contracts)-1)//batch_size + 1}")
            
            for contract in batch:
                try:
                    ticker = contract['ticker']
                    
                    # Get bars for the entire period
                    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
                    params = {
                        'adjusted': 'true',
                        'sort': 'asc',
                        'apikey': self.polygon_api_key
                    }
                    
                    response = requests.get(url, params=params, timeout=15)
                    data = response.json()
                    
                    if data.get('results') and len(data['results']) > 0:
                        bars_data = []
                        for bar in data['results']:
                            bars_data.append({
                                'date': datetime.fromtimestamp(bar['t'] / 1000).date(),
                                'timestamp': datetime.fromtimestamp(bar['t'] / 1000),
                                'open': bar.get('o', 0),
                                'high': bar.get('h', 0),
                                'low': bar.get('l', 0),
                                'close': bar.get('c', 0),
                                'volume': bar.get('v', 0),
                                'strike': contract['strike_price'],
                                'expiration': contract['expiration_date'],
                                'option_type': contract['contract_type'].upper(),
                                'underlying': contract['underlying_ticker']
                            })
                        
                        all_options_data[ticker] = bars_data
                        print(f"   ✅ {ticker}: {len(bars_data)} bars")
                    else:
                        print(f"   ⚠️ {ticker}: No bars")
                        
                except Exception as e:
                    print(f"   ❌ {contract.get('ticker', 'unknown')}: {e}")
                    continue
            
            # Rate limiting between batches
            time.sleep(0.2)
        
        if all_options_data:
            # Save to cache
            cache_file = f"{self.data_dir}/polygon_spy_options_bars_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
            with open(cache_file, 'w') as f:
                # Convert datetime objects to strings for JSON serialization
                serializable_data = {}
                for ticker, bars in all_options_data.items():
                    serializable_data[ticker] = []
                    for bar in bars:
                        bar_copy = bar.copy()
                        bar_copy['date'] = bar_copy['date'].strftime('%Y-%m-%d')
                        bar_copy['timestamp'] = bar_copy['timestamp'].isoformat()
                        serializable_data[ticker].append(bar_copy)
                
                json.dump(serializable_data, f, indent=2)
            
            print(f"✅ Extracted options bars for {len(all_options_data)} contracts")
            print(f"💾 Cached to: {cache_file}")
            return all_options_data
        else:
            print(f"❌ No options bars extracted")
            return {}
    
    def extract_alpaca_options_chain(self, symbol: str = 'SPY') -> List[Dict]:
        """Extract current options chain from Alpaca as backup"""
        print(f"\n🔄 EXTRACTING OPTIONS CHAIN FROM ALPACA (BACKUP)")
        print(f"📊 Symbol: {symbol}")
        
        try:
            from alpaca.data.requests import OptionChainRequest
            
            # Create request for options chain
            request_params = OptionChainRequest(
                underlying_symbol=symbol
            )
            
            # Get option chain
            chain = self.alpaca_option_client.get_option_chain(request_params)
            
            if chain and hasattr(chain, 'snapshots') and chain.snapshots:
                contract_list = []
                for snapshot in chain.snapshots:
                    try:
                        contract_data = {
                            'symbol': snapshot.underlying_symbol,
                            'underlying_symbol': snapshot.underlying_symbol,
                            'expiration_date': snapshot.expiration_date.strftime('%Y-%m-%d') if snapshot.expiration_date else 'N/A',
                            'strike_price': float(snapshot.strike_price) if snapshot.strike_price else 0,
                            'option_type': snapshot.option_type.value if snapshot.option_type else 'UNKNOWN',
                            'size': 100,
                            'open_interest': int(snapshot.open_interest) if snapshot.open_interest else 0,
                            'last_quote_bid': float(snapshot.latest_quote.bid_price) if snapshot.latest_quote and snapshot.latest_quote.bid_price else 0,
                            'last_quote_ask': float(snapshot.latest_quote.ask_price) if snapshot.latest_quote and snapshot.latest_quote.ask_price else 0,
                            'implied_volatility': float(snapshot.implied_volatility) if snapshot.implied_volatility else 0
                        }
                        contract_list.append(contract_data)
                    except Exception as e:
                        print(f"⚠️ Error processing snapshot: {e}")
                        continue
                
                if contract_list:
                    # Save to cache
                    cache_file = f"{self.data_dir}/alpaca_spy_options_chain_{datetime.now().strftime('%Y%m%d')}.json"
                    with open(cache_file, 'w') as f:
                        json.dump(contract_list, f, indent=2)
                    
                    print(f"✅ Extracted {len(contract_list)} options from Alpaca chain")
                    print(f"💾 Cached to: {cache_file}")
                    return contract_list
                else:
                    print(f"⚠️ No valid options processed from Alpaca chain")
                    return []
            else:
                print(f"⚠️ No option chain data from Alpaca")
                return []
                
        except Exception as e:
            print(f"❌ Alpaca options chain error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def run_full_extraction(self, start_date: datetime, end_date: datetime):
        """Run complete data extraction process"""
        print(f"\n🚀 STARTING FULL DATA EXTRACTION")
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"📊 Target: SPY stock + options + VIX")
        print(f"=" * 60)
        
        # 1. Extract SPY stock data
        spy_stock = self.extract_spy_stock_data(start_date, end_date)
        
        # 2. Extract VIX data
        vix_data = self.extract_vix_data(start_date, end_date)
        
        # 3. Extract options contracts from Polygon.io
        polygon_contracts = self.extract_polygon_options_contracts('SPY')
        
        # 4. Extract options bars from Polygon.io
        polygon_options_bars = {}
        if polygon_contracts:
            polygon_options_bars = self.extract_polygon_options_bars(polygon_contracts, start_date, end_date)
        
        # 5. Extract Alpaca options chain as backup
        alpaca_options = self.extract_alpaca_options_chain('SPY')
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"📊 EXTRACTION SUMMARY")
        print(f"=" * 60)
        print(f"📈 SPY Stock Bars: {len(spy_stock) if not spy_stock.empty else 0}")
        print(f"📊 VIX Bars: {len(vix_data) if not vix_data.empty else 0}")
        print(f"📋 Polygon Contracts: {len(polygon_contracts)}")
        print(f"📊 Polygon Options Bars: {len(polygon_options_bars)} contracts")
        print(f"🔄 Alpaca Options Chain: {len(alpaca_options)} contracts")
        print(f"💾 Cache Directory: {self.data_dir}")
        
        return {
            'spy_stock': spy_stock,
            'vix_data': vix_data,
            'polygon_contracts': polygon_contracts,
            'polygon_options_bars': polygon_options_bars,
            'alpaca_options': alpaca_options
        }

def main():
    """Main execution function"""
    print("🎯 SPY OPTIONS DATA EXTRACTOR")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ['POLYGON_API_KEY', 'ALPACA_API_KEY', 'ALPACA_API_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set them in your .env file")
        return
    
    # Initialize extractor
    extractor = DataExtractor()
    
    # Define extraction period (1 year)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    print(f"\n📅 Extraction Period: {start_date} to {end_date} (1 year)")
    
    try:
        # Run extraction
        results = extractor.run_full_extraction(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.min.time())
        )
        
        print(f"\n🎉 DATA EXTRACTION COMPLETED!")
        print(f"📁 All data cached in: {extractor.data_dir}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrupted by user")
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
