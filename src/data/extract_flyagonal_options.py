#!/usr/bin/env python3
"""
🎯 Flyagonal-Specific Options Data Extractor
===========================================

Extracts the exact options needed for Flyagonal strategy:
- Call Broken Wing Butterfly: ATM+10, ATM+20, ATM+30 (2x)
- Put Diagonal Spread: ATM-10, ATM-20

Uses Polygon.io Options Starter Plan for real 1-minute data.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import requests
import time
from typing import Dict

# Load environment
from dotenv import load_dotenv
load_dotenv()

class FlyagonalOptionsExtractor:
    """Extract specific options for Flyagonal strategy"""
    
    def __init__(self):
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY not found")
        
        self.data_dir = "intraday_data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_spy_price(self, date: datetime) -> float:
        """Get SPY closing price for ATM calculation"""
        try:
            spy_file = f"{self.data_dir}/spy_1min_{date.strftime('%Y%m%d')}.csv"
            if os.path.exists(spy_file):
                df = pd.read_csv(spy_file)
                return df['close'].iloc[-1]
            else:
                # Fallback: get from Polygon
                date_str = date.strftime('%Y-%m-%d')
                url = f"https://api.polygon.io/v2/aggs/ticker/SPY/range/1/day/{date_str}/{date_str}"
                params = {'apikey': self.polygon_api_key}
                
                response = requests.get(url, params=params, timeout=30)
                data = response.json()
                
                if data.get('results'):
                    return data['results'][0]['c']
                else:
                    return 645.0  # Fallback estimate
        except Exception as e:
            print(f"❌ Error getting SPY price: {e}")
            return 645.0
    
    def find_flyagonal_contracts(self, spy_price: float) -> Dict[str, str]:
        """Find the exact option contracts needed for Flyagonal"""
        
        # Calculate ATM and required strikes
        atm_strike = round(spy_price / 5) * 5
        
        required_strikes = {
            'call_short_1': atm_strike + 10,   # ATM+10 Call (sell)
            'call_short_2': atm_strike + 20,   # ATM+20 Call (sell)
            'call_long': atm_strike + 30,      # ATM+30 Call (buy 2x)
            'put_short': atm_strike - 10,      # ATM-10 Put (sell)
            'put_long': atm_strike - 20        # ATM-20 Put (buy)
        }
        
        print(f"📊 SPY Price: ${spy_price:.2f}")
        print(f"📊 ATM Strike: ${atm_strike}")
        print(f"🎯 Required strikes: {required_strikes}")
        
        # Get all SPY option contracts from Polygon
        url = "https://api.polygon.io/v3/reference/options/contracts"
        params = {
            'underlying_ticker': 'SPY',
            'expiration_date': '2025-09-02',  # Match our test date expiration
            'limit': 1000,
            'apikey': self.polygon_api_key
        }
        
        print(f"🔍 Searching for contracts...")
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if not data.get('results'):
            print(f"❌ No contracts found")
            return {}
        
        contracts = data['results']
        print(f"📋 Found {len(contracts)} total contracts")
        
        # Find matching contracts
        flyagonal_contracts = {}
        
        for contract in contracts:
            strike = float(contract['strike_price'])
            contract_type = contract['contract_type'].upper()
            ticker = contract['ticker']
            
            # Check each required leg
            for leg_name, required_strike in required_strikes.items():
                if abs(strike - required_strike) < 0.01:  # Match strike
                    expected_type = 'CALL' if 'call' in leg_name else 'PUT'
                    if contract_type == expected_type:
                        flyagonal_contracts[leg_name] = ticker
                        print(f"   ✅ {leg_name}: {ticker} ({contract_type} ${strike})")
                        break
        
        print(f"\n📊 Found {len(flyagonal_contracts)}/5 required contracts")
        return flyagonal_contracts
    
    def extract_contract_1min_data(self, ticker: str, date: datetime) -> bool:
        """Extract 1-minute data for a specific contract"""
        try:
            date_str = date.strftime('%Y-%m-%d')
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{date_str}/{date_str}"
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 50000,
                'apikey': self.polygon_api_key
            }
            
            print(f"📊 Extracting {ticker}...")
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
                safe_ticker = ticker.replace(':', '_')
                cache_file = f"{self.data_dir}/{safe_ticker}_1min_{date.strftime('%Y%m%d')}.csv"
                df.to_csv(cache_file)
                
                print(f"   ✅ {len(df)} bars saved to {cache_file}")
                return True
            else:
                print(f"   ⚠️ No data: {data.get('status', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def extract_flyagonal_options_data(self, date: datetime):
        """Extract all options needed for Flyagonal strategy"""
        
        print(f"\n🎯 EXTRACTING FLYAGONAL OPTIONS DATA")
        print(f"📅 Date: {date.strftime('%Y-%m-%d')}")
        print(f"=" * 60)
        
        # Get SPY price
        spy_price = self.get_spy_price(date)
        
        # Find required contracts
        contracts = self.find_flyagonal_contracts(spy_price)
        
        if len(contracts) < 5:
            print(f"❌ Missing contracts for complete Flyagonal strategy")
            print(f"📊 Found: {list(contracts.keys())}")
            missing = set(['call_short_1', 'call_short_2', 'call_long', 'put_short', 'put_long']) - set(contracts.keys())
            print(f"📊 Missing: {missing}")
            return False
        
        # Extract 1-minute data for each contract
        print(f"\n📊 EXTRACTING 1-MINUTE BARS...")
        success_count = 0
        
        for leg_name, ticker in contracts.items():
            if self.extract_contract_1min_data(ticker, date):
                success_count += 1
            time.sleep(0.1)  # Rate limiting
        
        print(f"\n🎉 EXTRACTION COMPLETE!")
        print(f"✅ Successfully extracted {success_count}/{len(contracts)} contracts")
        
        return success_count == len(contracts)

def main():
    """Main execution"""
    print("🎯 FLYAGONAL OPTIONS DATA EXTRACTOR")
    print("=" * 60)
    
    extractor = FlyagonalOptionsExtractor()
    
    # Extract for our test date
    test_date = datetime(2025, 8, 29)
    
    try:
        success = extractor.extract_flyagonal_options_data(test_date)
        
        if success:
            print(f"\n🎉 All Flyagonal options data extracted successfully!")
            print(f"📁 Data cached in: {extractor.data_dir}")
        else:
            print(f"\n⚠️ Partial extraction completed")
            
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
