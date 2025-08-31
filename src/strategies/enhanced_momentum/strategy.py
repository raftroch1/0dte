#!/usr/bin/env python3
"""
🚀 Enhanced Momentum Strategy - Multi-Timeframe & Liquid Options
==============================================================

Advanced version of the Simple Momentum Strategy with:
- Multiple timeframe analysis (1min, 5min, 15min)
- Expanded liquid options selection
- Dynamic position sizing
- Advanced risk management
- Real-time market regime detection

Features:
- Multi-timeframe RSI convergence
- Volume-weighted momentum signals
- Adaptive strike selection based on volatility
- Dynamic stop-loss and profit targets
- Market microstructure analysis

Author: Advanced Options Trading System
Version: 2.0.0
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import json
from typing import Dict, List, Optional, Tuple, Union
import warnings
warnings.filterwarnings('ignore')

class EnhancedDataLoader:
    """Enhanced data loader with multi-timeframe support"""
    
    def __init__(self):
        self.daily_data_dir = "cached_data"
        self.intraday_data_dir = "intraday_data"
        
    def load_spy_multi_timeframe(self, date: datetime) -> Dict[str, pd.DataFrame]:
        """Load SPY data in multiple timeframes"""
        
        # Load 1-minute data
        spy_1min = self.load_spy_1min_data(date)
        
        if spy_1min.empty:
            return {}
        
        # Resample to different timeframes
        timeframes = {
            '1min': spy_1min,
            '5min': spy_1min.resample('5min').agg({
                'open': 'first',
                'high': 'max', 
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna(),
            '15min': spy_1min.resample('15min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min', 
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        }
        
        print(f"✅ Multi-timeframe SPY data loaded:")
        for tf, df in timeframes.items():
            print(f"   📊 {tf}: {len(df)} bars")
        
        return timeframes
    
    def load_spy_1min_data(self, date: datetime) -> pd.DataFrame:
        """Load SPY 1-minute data for a specific date"""
        try:
            date_str = date.strftime('%Y%m%d')
            file_path = f"{self.intraday_data_dir}/spy_1min_{date_str}.csv"
            
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading SPY 1-minute data: {e}")
            return pd.DataFrame()
    
    def load_expanded_liquid_options(self, date: datetime) -> Dict[str, pd.DataFrame]:
        """Load expanded set of liquid options (ATM ±30)"""
        try:
            date_str = date.strftime('%Y%m%d')
            options_data = {}
            
            # Get all available option files for this date
            option_files = [f for f in os.listdir(self.intraday_data_dir) 
                          if f.endswith(f'_1min_{date_str}.csv') and 'SPY' in f]
            
            print(f"📊 Found {len(option_files)} option files for {date.strftime('%Y-%m-%d')}")
            
            # Load all available options
            for filename in option_files:
                filepath = f"{self.intraday_data_dir}/{filename}"
                
                # Extract option ticker from filename
                option_ticker = filename.replace(f'_1min_{date_str}.csv', '').replace('_', ':')
                
                df = pd.read_csv(filepath)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                
                # Only include options with reasonable data
                if len(df) > 50:  # At least 50 bars of data
                    options_data[option_ticker] = df
            
            print(f"✅ Loaded {len(options_data)} liquid options with sufficient data")
            
            # Analyze option strikes for selection
            self.analyze_option_strikes(options_data)
            
            return options_data
            
        except Exception as e:
            print(f"❌ Error loading expanded options data: {e}")
            return {}
    
    def analyze_option_strikes(self, options_data: Dict[str, pd.DataFrame]):
        """Analyze available option strikes for better selection"""
        
        calls = []
        puts = []
        
        for ticker in options_data.keys():
            try:
                if 'C' in ticker:
                    # Extract call strike
                    c_index = ticker.find('C')
                    if c_index != -1:
                        strike_str = ticker[c_index+1:]
                        if strike_str.isdigit():
                            strike = float(strike_str) / 1000
                            calls.append(strike)
                
                elif 'P' in ticker:
                    # Extract put strike
                    p_index = ticker.find('P')
                    if p_index != -1:
                        strike_str = ticker[p_index+1:]
                        if strike_str.isdigit():
                            strike = float(strike_str) / 1000
                            puts.append(strike)
            except:
                continue
        
        calls.sort()
        puts.sort()
        
        print(f"📊 Available strikes:")
        print(f"   📈 Calls: {len(calls)} strikes from ${min(calls) if calls else 0:.0f} to ${max(calls) if calls else 0:.0f}")
        print(f"   📉 Puts: {len(puts)} strikes from ${min(puts) if puts else 0:.0f} to ${max(puts) if puts else 0:.0f}")
    
    def load_vix_data(self) -> pd.DataFrame:
        """Load cached VIX data"""
        try:
            vix_files = [f for f in os.listdir(self.daily_data_dir) if f.startswith('vix_data_')]
            if vix_files:
                file_path = f"{self.daily_data_dir}/{vix_files[0]}"
                df = pd.read_csv(file_path)
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading VIX data: {e}")
            return pd.DataFrame()

class MultiTimeframeTechnicalIndicators:
    """Advanced technical indicators with multi-timeframe analysis"""
    
    @staticmethod
    def calculate_multi_timeframe_rsi(price_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """Calculate RSI across multiple timeframes"""
        
        rsi_data = {}
        
        for timeframe, df in price_data.items():
            if not df.empty:
                rsi_data[timeframe] = MultiTimeframeTechnicalIndicators.calculate_rsi(df['close'])
        
        return rsi_data
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_volume_weighted_momentum(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """Calculate volume-weighted price momentum"""
        
        # Calculate VWAP over the period
        vwap = (df['close'] * df['volume']).rolling(period).sum() / df['volume'].rolling(period).sum()
        
        # Calculate momentum relative to VWAP
        momentum = ((df['close'] - vwap) / vwap) * 100
        
        return momentum
    
    @staticmethod
    def calculate_volatility_adjusted_momentum(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate volatility-adjusted momentum"""
        
        returns = df['close'].pct_change()
        volatility = returns.rolling(period).std()
        raw_momentum = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
        
        # Adjust momentum by volatility
        vol_adj_momentum = raw_momentum / (volatility * 100)
        
        return vol_adj_momentum
    
    @staticmethod
    def detect_market_regime(df: pd.DataFrame, vix_level: float) -> str:
        """Detect current market regime"""
        
        # Calculate recent price action
        recent_returns = df['close'].pct_change(20).iloc[-1] * 100
        recent_volatility = df['close'].pct_change().rolling(20).std().iloc[-1] * 100
        
        # Regime classification
        if vix_level > 25:
            return "HIGH_VOLATILITY"
        elif vix_level < 12:
            return "LOW_VOLATILITY"
        elif recent_returns > 2:
            return "TRENDING_UP"
        elif recent_returns < -2:
            return "TRENDING_DOWN"
        else:
            return "CONSOLIDATING"

class EnhancedMomentumStrategy:
    """Enhanced momentum strategy with multi-timeframe analysis"""
    
    def __init__(self):
        self.name = "Enhanced Momentum"
        self.version = "2.0.0"
        
        # Multi-timeframe parameters
        self.timeframes = ['1min', '5min', '15min']
        self.rsi_periods = {'1min': 5, '5min': 14, '15min': 21}
        
        # Adaptive thresholds based on market regime
        self.regime_thresholds = {
            'HIGH_VOLATILITY': {'rsi_os': 45, 'rsi_ob': 55, 'momentum': 0.03},
            'LOW_VOLATILITY': {'rsi_os': 35, 'rsi_ob': 65, 'momentum': 0.08},
            'TRENDING_UP': {'rsi_os': 40, 'rsi_ob': 70, 'momentum': 0.05},
            'TRENDING_DOWN': {'rsi_os': 30, 'rsi_ob': 60, 'momentum': 0.05},
            'CONSOLIDATING': {'rsi_os': 35, 'rsi_ob': 65, 'momentum': 0.06}
        }
        
        # Time windows
        self.morning_start = time(9, 30)
        self.morning_end = time(11, 0)
        self.afternoon_start = time(14, 0)
        self.market_close = time(16, 0)
        
        # Enhanced risk management
        self.base_stop_loss = 0.30
        self.base_profit_target = 0.50
        self.max_holding_minutes = 180  # 3 hours
        
    def calculate_multi_timeframe_indicators(self, spy_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Calculate indicators across all timeframes"""
        
        indicators = {}
        
        for timeframe, df in spy_data.items():
            if df.empty:
                continue
                
            df_copy = df.copy()
            
            # RSI with timeframe-specific period
            rsi_period = self.rsi_periods.get(timeframe, 14)
            df_copy['rsi'] = MultiTimeframeTechnicalIndicators.calculate_rsi(df_copy['close'], rsi_period)
            
            # Fast RSI for quick signals
            df_copy['fast_rsi'] = MultiTimeframeTechnicalIndicators.calculate_rsi(df_copy['close'], 5)
            
            # Volume-weighted momentum
            df_copy['vw_momentum'] = MultiTimeframeTechnicalIndicators.calculate_volume_weighted_momentum(df_copy)
            
            # Volatility-adjusted momentum
            df_copy['vol_adj_momentum'] = MultiTimeframeTechnicalIndicators.calculate_volatility_adjusted_momentum(df_copy)
            
            # Price velocity
            df_copy['price_velocity'] = df_copy['close'].pct_change(3)
            
            # Volume ratio
            df_copy['volume_ratio'] = df_copy['volume'] / df_copy['volume'].rolling(20).mean()
            
            # MACD
            ema_fast = df_copy['close'].ewm(span=12).mean()
            ema_slow = df_copy['close'].ewm(span=26).mean()
            df_copy['macd'] = ema_fast - ema_slow
            df_copy['macd_signal'] = df_copy['macd'].ewm(span=9).mean()
            
            # Bollinger Bands
            bb_sma = df_copy['close'].rolling(20).mean()
            bb_std = df_copy['close'].rolling(20).std()
            df_copy['bb_upper'] = bb_sma + (bb_std * 2)
            df_copy['bb_lower'] = bb_sma - (bb_std * 2)
            df_copy['bb_middle'] = bb_sma
            
            indicators[timeframe] = df_copy
        
        return indicators
    
    def generate_enhanced_signal(self, spy_indicators: Dict[str, pd.DataFrame], timestamp: datetime, vix_level: float) -> Optional[Dict]:
        """Generate enhanced signal using multi-timeframe analysis"""
        
        # Get current data for 1-minute timeframe
        if '1min' not in spy_indicators or timestamp not in spy_indicators['1min'].index:
            return None
        
        current_1min = spy_indicators['1min'].loc[timestamp]
        current_price = current_1min['close']
        
        # Detect market regime
        regime = MultiTimeframeTechnicalIndicators.detect_market_regime(
            spy_indicators['1min'], vix_level
        )
        
        # Get regime-specific thresholds
        thresholds = self.regime_thresholds[regime]
        
        # Multi-timeframe RSI analysis
        rsi_signals = self.analyze_multi_timeframe_rsi(spy_indicators, timestamp)
        
        # Initialize signal
        confidence = 40
        action = None
        reason = f"Enhanced [{regime}]: "
        
        # Time window analysis
        time_window = self.get_time_window(timestamp)
        
        # VIX-based confidence adjustment
        if vix_level > 30:
            confidence -= 15
            reason += f"High VIX ({vix_level:.1f}), "
        elif vix_level < 12:
            confidence -= 5
            reason += f"Low VIX ({vix_level:.1f}), "
        else:
            confidence += 10
            reason += f"Normal VIX ({vix_level:.1f}), "
        
        # Multi-timeframe RSI convergence
        if rsi_signals['convergence_bullish']:
            action = "BUY_CALL"
            confidence += 30
            reason += f"Multi-TF bullish convergence, "
        elif rsi_signals['convergence_bearish']:
            action = "BUY_PUT"
            confidence += 30
            reason += f"Multi-TF bearish convergence, "
        
        # Single timeframe signals if no convergence
        if not action:
            fast_rsi = current_1min['fast_rsi']
            vw_momentum = current_1min['vw_momentum']
            
            if time_window == "MORNING_MOMENTUM":
                if fast_rsi < thresholds['rsi_os'] and vw_momentum > thresholds['momentum']:
                    action = "BUY_CALL"
                    confidence += 20
                    reason += "Morning oversold breakout, "
                elif fast_rsi > thresholds['rsi_ob'] and vw_momentum < -thresholds['momentum']:
                    action = "BUY_PUT"
                    confidence += 20
                    reason += "Morning overbought breakdown, "
            
            elif time_window == "AFTERNOON_DECAY":
                if fast_rsi < thresholds['rsi_os'] and vw_momentum < -thresholds['momentum']:
                    action = "BUY_CALL"
                    confidence += 25
                    reason += "Afternoon oversold bounce, "
                elif fast_rsi > thresholds['rsi_ob'] and vw_momentum > thresholds['momentum']:
                    action = "BUY_PUT"
                    confidence += 25
                    reason += "Afternoon overbought reversal, "
        
        if not action:
            return None
        
        # Volume confirmation
        volume_ratio = current_1min['volume_ratio']
        if volume_ratio > 1.5:
            confidence += 15
            reason += f"High volume ({volume_ratio:.1f}x), "
        elif volume_ratio < 0.8:
            confidence -= 10
            reason += f"Low volume ({volume_ratio:.1f}x), "
        
        # MACD confirmation
        macd = current_1min['macd']
        macd_signal = current_1min['macd_signal']
        if macd > macd_signal and action == "BUY_CALL":
            confidence += 12
            reason += "MACD bullish, "
        elif macd < macd_signal and action == "BUY_PUT":
            confidence += 12
            reason += "MACD bearish, "
        
        # Bollinger Bands confirmation
        if action == "BUY_CALL" and current_price < current_1min['bb_lower']:
            confidence += 15
            reason += "Below BB lower, "
        elif action == "BUY_PUT" and current_price > current_1min['bb_upper']:
            confidence += 15
            reason += "Above BB upper, "
        
        # Minimum confidence threshold
        if confidence < 55:
            return None
        
        reason = reason.rstrip(', ')
        
        return {
            'action': action,
            'confidence': min(95, confidence),
            'reason': reason,
            'timestamp': timestamp,
            'spy_price': current_price,
            'regime': regime,
            'rsi_signals': rsi_signals,
            'indicators': {
                'fast_rsi': current_1min['fast_rsi'],
                'vw_momentum': current_1min['vw_momentum'],
                'vol_adj_momentum': current_1min['vol_adj_momentum'],
                'volume_ratio': volume_ratio,
                'vix': vix_level
            }
        }
    
    def analyze_multi_timeframe_rsi(self, spy_indicators: Dict[str, pd.DataFrame], timestamp: datetime) -> Dict:
        """Analyze RSI across multiple timeframes for convergence"""
        
        rsi_analysis = {
            'convergence_bullish': False,
            'convergence_bearish': False,
            'timeframe_signals': {}
        }
        
        # Get RSI values for each timeframe
        for timeframe in self.timeframes:
            if timeframe not in spy_indicators:
                continue
                
            df = spy_indicators[timeframe]
            
            # Find the closest timestamp for this timeframe
            if timeframe == '1min':
                if timestamp in df.index:
                    rsi_value = df.loc[timestamp, 'fast_rsi']
                else:
                    continue
            else:
                # For higher timeframes, find the most recent bar
                available_times = df.index[df.index <= timestamp]
                if len(available_times) == 0:
                    continue
                latest_time = available_times[-1]
                rsi_value = df.loc[latest_time, 'rsi']
            
            if pd.isna(rsi_value):
                continue
                
            rsi_analysis['timeframe_signals'][timeframe] = rsi_value
        
        # Check for convergence
        rsi_values = list(rsi_analysis['timeframe_signals'].values())
        
        if len(rsi_values) >= 2:
            # Bullish convergence: all timeframes oversold
            if all(rsi < 35 for rsi in rsi_values):
                rsi_analysis['convergence_bullish'] = True
            
            # Bearish convergence: all timeframes overbought  
            elif all(rsi > 65 for rsi in rsi_values):
                rsi_analysis['convergence_bearish'] = True
        
        return rsi_analysis
    
    def get_time_window(self, timestamp: datetime) -> str:
        """Determine current time window"""
        market_time = timestamp.time()
        
        if self.morning_start <= market_time <= self.morning_end:
            return "MORNING_MOMENTUM"
        elif self.afternoon_start <= market_time <= self.market_close:
            return "AFTERNOON_DECAY"
        else:
            return "MIDDAY_CONSOLIDATION"

class EnhancedOptionSelector:
    """Enhanced option selection with multiple strikes and dynamic selection"""
    
    def __init__(self):
        self.preferred_delta_range = (0.3, 0.7)  # Prefer options with 30-70% delta
        self.max_spread_percent = 35  # Maximum bid-ask spread
        
    def find_optimal_option(self, action: str, spy_price: float, options_data: Dict[str, pd.DataFrame], 
                          timestamp: datetime, vix_level: float) -> Optional[Dict]:
        """Find optimal option based on multiple criteria"""
        
        candidates = []
        
        for option_ticker, option_df in options_data.items():
            if timestamp not in option_df.index:
                continue
            
            option_info = self.parse_option_ticker(option_ticker, spy_price)
            if not option_info:
                continue
            
            # Filter by option type
            if (action == "BUY_CALL" and option_info['type'] != 'CALL') or \
               (action == "BUY_PUT" and option_info['type'] != 'PUT'):
                continue
            
            option_price = option_df.loc[timestamp, 'close']
            
            # Calculate selection score
            score = self.calculate_option_score(option_info, option_price, spy_price, vix_level)
            
            if score > 0:
                candidates.append({
                    'ticker': option_ticker,
                    'strike': option_info['strike'],
                    'type': option_info['type'],
                    'price': option_price,
                    'moneyness': option_info['moneyness'],
                    'score': score
                })
        
        if not candidates:
            return None
        
        # Select best candidate
        best_option = max(candidates, key=lambda x: x['score'])
        
        print(f"   📊 Selected from {len(candidates)} candidates: ${best_option['strike']:.0f} {best_option['type']} (Score: {best_option['score']:.1f})")
        
        return best_option
    
    def parse_option_ticker(self, ticker: str, spy_price: float) -> Optional[Dict]:
        """Parse option ticker and calculate moneyness"""
        
        try:
            clean_ticker = ticker.replace('_', ':')
            
            if 'C' in clean_ticker:
                c_index = clean_ticker.find('C')
                strike_str = clean_ticker[c_index+1:]
                if strike_str.isdigit():
                    strike = float(strike_str) / 1000
                    moneyness = (strike - spy_price) / spy_price
                    return {
                        'strike': strike,
                        'type': 'CALL',
                        'moneyness': moneyness
                    }
            
            elif 'P' in clean_ticker:
                p_index = clean_ticker.find('P')
                strike_str = clean_ticker[p_index+1:]
                if strike_str.isdigit():
                    strike = float(strike_str) / 1000
                    moneyness = (spy_price - strike) / spy_price
                    return {
                        'strike': strike,
                        'type': 'PUT',
                        'moneyness': moneyness
                    }
        except:
            pass
        
        return None
    
    def calculate_option_score(self, option_info: Dict, option_price: float, spy_price: float, vix_level: float) -> float:
        """Calculate option selection score"""
        
        score = 50  # Base score
        
        # Moneyness scoring (prefer slightly OTM)
        moneyness = abs(option_info['moneyness'])
        
        if 0.01 <= moneyness <= 0.05:  # 1-5% OTM - optimal
            score += 30
        elif 0.005 <= moneyness <= 0.01:  # 0.5-1% OTM - good
            score += 20
        elif moneyness <= 0.005:  # ATM - acceptable
            score += 10
        elif 0.05 < moneyness <= 0.1:  # 5-10% OTM - less preferred
            score += 5
        else:  # Too far OTM
            score -= 20
        
        # Price scoring (prefer reasonable premium)
        if 0.05 <= option_price <= 2.0:  # $0.05 - $2.00 - good range
            score += 20
        elif 0.02 <= option_price < 0.05:  # $0.02 - $0.05 - acceptable
            score += 10
        elif option_price < 0.02:  # Too cheap - likely illiquid
            score -= 30
        elif option_price > 5.0:  # Too expensive
            score -= 20
        
        # VIX-based adjustment
        if vix_level > 25:  # High volatility - prefer closer to ATM
            if moneyness < 0.02:
                score += 15
        elif vix_level < 15:  # Low volatility - can go further OTM
            if 0.02 <= moneyness <= 0.08:
                score += 10
        
        return score

class EnhancedMomentumBacktester:
    """Enhanced backtester with multi-timeframe analysis"""
    
    def __init__(self):
        self.data_loader = EnhancedDataLoader()
        self.strategy = EnhancedMomentumStrategy()
        self.option_selector = EnhancedOptionSelector()
        
        # Backtest state
        self.initial_capital = 35000
        self.current_capital = self.initial_capital
        self.positions = []
        self.trades = []
        
    def run_enhanced_backtest(self, test_date: datetime):
        """Run enhanced multi-timeframe momentum backtest"""
        
        print(f"\n🚀 ENHANCED MOMENTUM STRATEGY BACKTEST")
        print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"💰 Initial Capital: ${self.initial_capital:,}")
        print(f"🎯 Strategy: {self.strategy.name} {self.strategy.version}")
        print(f"=" * 70)
        
        # Load multi-timeframe data
        spy_multi_tf = self.data_loader.load_spy_multi_timeframe(test_date)
        options_data = self.data_loader.load_expanded_liquid_options(test_date)
        vix_daily = self.data_loader.load_vix_data()
        
        if not spy_multi_tf:
            print(f"❌ No SPY data available for {test_date.strftime('%Y-%m-%d')}")
            return
        
        if not options_data:
            print(f"❌ No options data available for {test_date.strftime('%Y-%m-%d')}")
            return
        
        # Get VIX level
        test_date_only = test_date.date()
        if test_date_only in vix_daily.index.date:
            vix_level = vix_daily.loc[vix_daily.index.date == test_date_only, 'close'].iloc[0]
        else:
            vix_level = 20.0
        
        print(f"📊 VIX Level: {vix_level:.2f}")
        print(f"📊 Available options: {len(options_data)}")
        
        # Calculate multi-timeframe indicators
        spy_indicators = self.strategy.calculate_multi_timeframe_indicators(spy_multi_tf)
        
        # Track positions
        position_opened = False
        entry_time = None
        entry_option = None
        entry_price = None
        entry_signal = None
        
        signal_count = 0
        
        # Process each minute during market hours
        for timestamp, spy_row in spy_indicators['1min'].iterrows():
            # Skip if not market hours
            market_time = timestamp.time()
            if not (time(9, 30) <= market_time <= time(16, 0)):
                continue
            
            spy_price = spy_row['close']
            
            if not position_opened:
                # Look for enhanced signal
                signal = self.strategy.generate_enhanced_signal(spy_indicators, timestamp, vix_level)
                
                if signal:
                    signal_count += 1
                    
                    # Find optimal option
                    best_option = self.option_selector.find_optimal_option(
                        signal['action'], spy_price, options_data, timestamp, vix_level
                    )
                    
                    if best_option:
                        # Enter position
                        position_opened = True
                        entry_time = timestamp
                        entry_option = best_option
                        entry_price = best_option['price']
                        entry_signal = signal
                        
                        print(f"\n🎯 ENTRY: {timestamp.strftime('%H:%M:%S')}")
                        print(f"   📊 Signal: {signal['action']} ({signal['confidence']:.0f}% confidence)")
                        print(f"   📊 Regime: {signal['regime']}")
                        print(f"   📊 SPY: ${spy_price:.2f}")
                        print(f"   📊 Option: ${best_option['strike']:.0f} {best_option['type']} @ ${best_option['price']:.2f}")
                        print(f"   📊 Moneyness: {best_option['moneyness']:.1%}")
                        print(f"   📊 Reason: {signal['reason']}")
            
            else:
                # Manage open position
                if entry_option['ticker'] in options_data and timestamp in options_data[entry_option['ticker']].index:
                    current_option_price = options_data[entry_option['ticker']].loc[timestamp, 'close']
                    
                    # Calculate P&L
                    pnl_percent = ((current_option_price - entry_price) / entry_price) * 100
                    holding_minutes = (timestamp - entry_time).total_seconds() / 60
                    
                    # Dynamic exit conditions based on regime
                    should_exit, exit_reason = self.check_enhanced_exit_conditions(
                        entry_price, current_option_price, entry_time, timestamp,
                        entry_signal, spy_indicators['1min'].loc[timestamp]
                    )
                    
                    if should_exit:
                        # Exit position
                        pnl_dollars = (current_option_price - entry_price) * 100
                        
                        print(f"\n🚪 EXIT: {timestamp.strftime('%H:%M:%S')} ({exit_reason})")
                        print(f"   📊 Duration: {holding_minutes:.0f} minutes")
                        print(f"   📊 P&L: ${pnl_dollars:.2f} ({pnl_percent:.1f}%)")
                        print(f"   📊 Option: ${entry_price:.2f} → ${current_option_price:.2f}")
                        
                        # Log trade
                        trade = {
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'signal': entry_signal,
                            'option': entry_option,
                            'entry_price': entry_price,
                            'exit_price': current_option_price,
                            'pnl_dollars': pnl_dollars,
                            'pnl_percent': pnl_percent,
                            'duration_minutes': holding_minutes,
                            'exit_reason': exit_reason
                        }
                        
                        self.trades.append(trade)
                        self.current_capital += pnl_dollars
                        
                        # Reset for next trade
                        position_opened = False
                        entry_time = None
                        entry_option = None
                        entry_price = None
                        entry_signal = None
        
        # Generate results
        self.generate_enhanced_results(test_date, signal_count)
    
    def check_enhanced_exit_conditions(self, entry_price: float, current_price: float, 
                                     entry_time: datetime, current_time: datetime,
                                     entry_signal: Dict, current_indicators: pd.Series) -> Tuple[bool, str]:
        """Enhanced exit conditions based on market regime and signal strength"""
        
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        holding_minutes = (current_time - entry_time).total_seconds() / 60
        
        # Base exit conditions
        if holding_minutes >= self.strategy.max_holding_minutes:
            return True, "MAX_TIME"
        
        # Dynamic profit targets based on signal confidence
        confidence = entry_signal['confidence']
        regime = entry_signal['regime']
        
        # Adjust targets based on confidence and regime
        if confidence > 80:
            profit_target = 60  # Higher target for high confidence
            stop_loss = 25
        elif confidence > 70:
            profit_target = 45
            stop_loss = 30
        else:
            profit_target = 35
            stop_loss = 35
        
        # Regime-based adjustments
        if regime == "HIGH_VOLATILITY":
            profit_target *= 1.2  # Higher targets in volatile markets
            stop_loss *= 0.8      # Tighter stops
        elif regime == "LOW_VOLATILITY":
            profit_target *= 0.8  # Lower targets in calm markets
            stop_loss *= 1.2      # Wider stops
        
        # Check exit conditions
        if pnl_percent >= profit_target:
            return True, "PROFIT_TARGET"
        
        if pnl_percent <= -stop_loss:
            return True, "STOP_LOSS"
        
        # Time-based exits
        market_time = current_time.time()
        if market_time >= time(15, 45):  # 3:45 PM ET
            return True, "EOD_EXIT"
        
        # Signal reversal exits
        action = entry_signal['action']
        current_rsi = current_indicators['fast_rsi']
        
        if action == "BUY_CALL" and current_rsi > 75:
            return True, "SIGNAL_REVERSAL"
        elif action == "BUY_PUT" and current_rsi < 25:
            return True, "SIGNAL_REVERSAL"
        
        return False, "CONTINUE"
    
    def generate_enhanced_results(self, test_date: datetime, signal_count: int):
        """Generate enhanced results with detailed analysis"""
        
        print(f"\n" + "=" * 70)
        print(f"📊 ENHANCED MOMENTUM STRATEGY RESULTS")
        print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
        print(f"=" * 70)
        
        print(f"📊 Total Signals Generated: {signal_count}")
        print(f"📊 Total Trades Executed: {len(self.trades)}")
        
        if not self.trades:
            print(f"❌ No trades executed")
            return
        
        # Calculate enhanced metrics
        total_pnl = sum(trade['pnl_dollars'] for trade in self.trades)
        winning_trades = [t for t in self.trades if t['pnl_dollars'] > 0]
        losing_trades = [t for t in self.trades if t['pnl_dollars'] < 0]
        
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        avg_win = np.mean([t['pnl_dollars'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_dollars'] for t in losing_trades]) if losing_trades else 0
        avg_duration = np.mean([t['duration_minutes'] for t in self.trades])
        
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        
        # Regime analysis
        regime_performance = {}
        for trade in self.trades:
            regime = trade['signal']['regime']
            if regime not in regime_performance:
                regime_performance[regime] = {'trades': 0, 'pnl': 0}
            regime_performance[regime]['trades'] += 1
            regime_performance[regime]['pnl'] += trade['pnl_dollars']
        
        print(f"💰 Total P&L: ${total_pnl:,.2f}")
        print(f"📈 Total Return: {total_return:.2f}%")
        print(f"🎯 Win Rate: {win_rate:.1f}% ({len(winning_trades)}/{len(self.trades)})")
        print(f"🏆 Average Win: ${avg_win:.2f}")
        print(f"💸 Average Loss: ${avg_loss:.2f}")
        print(f"⏱️ Average Duration: {avg_duration:.1f} minutes")
        print(f"💵 Final Capital: ${self.current_capital:,.2f}")
        
        # Regime performance
        print(f"\n📊 PERFORMANCE BY MARKET REGIME:")
        for regime, perf in regime_performance.items():
            avg_pnl = perf['pnl'] / perf['trades'] if perf['trades'] > 0 else 0
            print(f"   {regime}: {perf['trades']} trades, ${perf['pnl']:.2f} total (${avg_pnl:.2f} avg)")
        
        # Save results
        results_file = f"enhanced_momentum_backtest_{test_date.strftime('%Y%m%d')}.json"
        
        # Prepare serializable data
        serializable_trades = []
        for trade in self.trades:
            trade_copy = trade.copy()
            trade_copy['entry_time'] = trade_copy['entry_time'].isoformat()
            trade_copy['exit_time'] = trade_copy['exit_time'].isoformat()
            if 'signal' in trade_copy and 'timestamp' in trade_copy['signal']:
                trade_copy['signal']['timestamp'] = trade_copy['signal']['timestamp'].isoformat()
            serializable_trades.append(trade_copy)
        
        results_data = {
            'test_date': test_date.strftime('%Y-%m-%d'),
            'strategy': f"{self.strategy.name} {self.strategy.version}",
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_pnl': total_pnl,
            'total_return_percent': total_return,
            'total_signals': signal_count,
            'total_trades': len(self.trades),
            'win_rate_percent': win_rate,
            'average_win': avg_win,
            'average_loss': avg_loss,
            'average_duration_minutes': avg_duration,
            'regime_performance': regime_performance,
            'trades': serializable_trades
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Enhanced results saved to: {results_file}")

def main():
    """Main execution function"""
    print("🚀 ENHANCED MOMENTUM STRATEGY - MULTI-TIMEFRAME BACKTEST")
    print("=" * 70)
    
    # Initialize enhanced backtest
    backtest = EnhancedMomentumBacktester()
    
    # Use the date we have data for
    test_date = datetime(2025, 8, 29)
    
    try:
        # Run enhanced backtest
        backtest.run_enhanced_backtest(test_date)
        
    except KeyboardInterrupt:
        print("\n⚠️ Backtest interrupted by user")
    except Exception as e:
        print(f"❌ Backtest error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
