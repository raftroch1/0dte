#!/usr/bin/env python3
"""
🤖 Machine Learning Feature Engineering for 0DTE Options Trading
==============================================================

Prepares comprehensive ML features from your year-long SPY options dataset
for advanced pattern recognition and strategy optimization.

Features Generated:
1. 📊 Market Microstructure Features
2. 🎯 Greeks-based Risk Features  
3. 📈 Technical Indicator Features
4. 🌍 Market Regime Features
5. ⏰ Temporal Pattern Features
6. 💧 Liquidity & Flow Features
7. 🔄 Cross-Asset Features
8. 📊 Volatility Surface Features

Designed for: Multi-year dataset expansion & ML model training
Author: Advanced Options Trading System
Version: 1.0.0 - ML Ready
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
# Handle imports for both direct execution and module import
import sys
import os

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from .parquet_data_loader import ParquetDataLoader
except ImportError:
    from src.data.parquet_data_loader import ParquetDataLoader

# Import BlackScholesGreeks from the enhanced strategy
try:
    from ..strategies.enhanced_0dte.strategy import BlackScholesGreeks
except ImportError:
    from src.strategies.enhanced_0dte.strategy import BlackScholesGreeks
import warnings
warnings.filterwarnings('ignore')

class MLFeatureEngineer:
    """Comprehensive feature engineering for ML-based 0DTE trading"""
    
    def __init__(self):
        self.feature_categories = {
            'market_microstructure': [],
            'greeks_features': [],
            'technical_indicators': [],
            'market_regime': [],
            'temporal_patterns': [],
            'liquidity_flow': [],
            'cross_asset': [],
            'volatility_surface': []
        }
        
    def generate_comprehensive_features(self, options_data: pd.DataFrame, 
                                      spy_price: float, 
                                      market_conditions: Dict,
                                      lookback_periods: List[int] = [5, 10, 20, 60],
                                      debug_mode: bool = False) -> pd.DataFrame:
        """Generate comprehensive ML features from options data"""
        
        print(f"🤖 Generating ML features for {len(options_data)} options...")
        
        # Start with base data
        features_df = options_data.copy()
        
        try:
            # 1. Market Microstructure Features
            print("🔄 Adding microstructure features...")
            features_df = self._add_microstructure_features(features_df, spy_price)
            if debug_mode:
                features_df.to_csv('debug_microstructure.csv', index=False)
            
            # 2. Greeks-based Features
            print("🔄 Adding Greeks features...")
            features_df = self._add_greeks_features(features_df, spy_price)
            if debug_mode:
                features_df.to_csv('debug_greeks.csv', index=False)
            
            # 3. Technical Indicator Features
            print("🔄 Adding technical features...")
            features_df = self._add_technical_features(features_df, lookback_periods)
            if debug_mode:
                features_df.to_csv('debug_technical.csv', index=False)
            
            # 4. Market Regime Features
            print("🔄 Adding regime features...")
            features_df = self._add_regime_features(features_df, market_conditions)
            if debug_mode:
                features_df.to_csv('debug_regime.csv', index=False)
            
            # 5. Temporal Pattern Features
            print("🔄 Adding temporal features...")
            features_df = self._add_temporal_features(features_df)
            if debug_mode:
                features_df.to_csv('debug_temporal.csv', index=False)
            
            # 6. Liquidity & Flow Features
            print("🔄 Adding liquidity features...")
            features_df = self._add_liquidity_features(features_df)
            if debug_mode:
                features_df.to_csv('debug_liquidity.csv', index=False)
            
            # 7. Cross-Asset Features
            print("🔄 Adding cross-asset features...")
            features_df = self._add_cross_asset_features(features_df, market_conditions)
            if debug_mode:
                features_df.to_csv('debug_cross_asset.csv', index=False)
            
            # 8. Volatility Surface Features
            print("🔄 Adding volatility surface features...")
            features_df = self._add_volatility_surface_features(features_df, spy_price)
            if debug_mode:
                features_df.to_csv('debug_volatility_surface.csv', index=False)
            
            # 9. Target Variables for ML Training
            print("🔄 Adding target variables...")
            features_df = self._add_target_variables(features_df)
            if debug_mode:
                features_df.to_csv('debug_targets.csv', index=False)
                
        except Exception as e:
            print(f"❌ Error in feature generation: {e}")
            print(f"📊 Current dataframe shape: {features_df.shape}")
            print(f"📊 Current columns: {list(features_df.columns)}")
            raise
        
        print(f"✅ Generated {len(features_df.columns)} total features")
        
        return features_df
    
    def _add_microstructure_features(self, df: pd.DataFrame, spy_price: float) -> pd.DataFrame:
        """Add market microstructure features with safety checks"""
        
        # Safety checks for required columns
        required_cols = ['strike', 'option_type', 'expiration', 'timestamp', 'close', 'high', 'low', 'open']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"⚠️  Missing required columns: {missing_cols}")
            return df
        
        # Price-based features
        df['moneyness'] = np.where(
            df['option_type'] == 'call',
            df['strike'] / spy_price,
            spy_price / df['strike']
        )
        
        df['log_moneyness'] = np.log(df['moneyness'])
        df['abs_log_moneyness'] = np.abs(df['log_moneyness'])
        
        # Time to expiration features
        df['expiration_dt'] = pd.to_datetime(df['expiration'])
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['dte_hours'] = (df['expiration_dt'] - df['timestamp_dt']).dt.total_seconds() / 3600
        df['dte_days'] = df['dte_hours'] / 24
        df['is_0dte'] = (df['dte_days'] < 1).astype(int)
        df['is_same_day'] = (df['dte_days'] < 0.5).astype(int)
        
        # Price efficiency features
        df['price_efficiency'] = df['close'] / df['vwap']
        df['intraday_range'] = (df['high'] - df['low']) / df['close']
        df['price_impact'] = np.abs(df['close'] - df['open']) / df['open']
        
        # Volume features (with safety checks)
        df['volume_per_transaction'] = df['volume'] / np.maximum(df.get('transactions', 1), 1)
        df['log_volume'] = np.log1p(df['volume'])
        df['log_transactions'] = np.log1p(df.get('transactions', 1))
        
        self.feature_categories['market_microstructure'].extend([
            'moneyness', 'log_moneyness', 'abs_log_moneyness',
            'dte_hours', 'dte_days', 'is_0dte', 'is_same_day',
            'price_efficiency', 'intraday_range', 'price_impact',
            'volume_per_transaction', 'log_volume', 'log_transactions'
        ])
        
        return df
    
    def _add_greeks_features(self, df: pd.DataFrame, spy_price: float) -> pd.DataFrame:
        """Add Greeks-based features (vectorized for performance)"""
        
        print("🔄 Calculating Greeks (vectorized)...")
        
        # Vectorized time to expiration calculation
        expiration_dt = pd.to_datetime(df['expiration'])
        timestamp_dt = pd.to_datetime(df['timestamp'], unit='ms')
        tte_seconds = (expiration_dt - timestamp_dt).dt.total_seconds()
        tte_years = np.maximum(tte_seconds / (365.25 * 24 * 3600), 1/365/24)
        
        # Vectorized IV estimation
        base_iv = 0.20
        log_moneyness = np.log(df['strike'] / spy_price)
        moneyness_adj = np.abs(log_moneyness) * 0.5
        tte_adj = np.maximum(0.1, np.sqrt(tte_years)) * 0.3
        estimated_iv = base_iv + moneyness_adj + tte_adj
        
        # Vectorized Greeks calculation
        S = spy_price
        K = df['strike'].values
        T = tte_years.values
        r = 0.05
        sigma = estimated_iv.values
        
        # Calculate d1 and d2 vectorized
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Handle 0DTE case
        zero_dte_mask = T <= 0
        
        from scipy.stats import norm
        
        # Standard normal CDF and PDF
        N_d1 = norm.cdf(d1)
        N_d2 = norm.cdf(d2)
        n_d1 = norm.pdf(d1)
        
        # Initialize arrays
        prices = np.zeros_like(K)
        deltas = np.zeros_like(K)
        gammas = np.zeros_like(K)
        thetas = np.zeros_like(K)
        vegas = np.zeros_like(K)
        rhos = np.zeros_like(K)
        
        # Non-zero DTE calculations
        non_zero_mask = ~zero_dte_mask
        
        if np.any(non_zero_mask):
            # Call options
            call_mask = (df['option_type'] == 'call').values & non_zero_mask
            if np.any(call_mask):
                prices[call_mask] = S * N_d1[call_mask] - K[call_mask] * np.exp(-r * T[call_mask]) * N_d2[call_mask]
                deltas[call_mask] = N_d1[call_mask]
                thetas[call_mask] = (-S * n_d1[call_mask] * sigma[call_mask] / (2 * np.sqrt(T[call_mask])) - 
                                   r * K[call_mask] * np.exp(-r * T[call_mask]) * N_d2[call_mask]) / 365
                rhos[call_mask] = (K[call_mask] * T[call_mask] * np.exp(-r * T[call_mask]) * N_d2[call_mask]) / 100
            
            # Put options
            put_mask = (df['option_type'] == 'put').values & non_zero_mask
            if np.any(put_mask):
                prices[put_mask] = K[put_mask] * np.exp(-r * T[put_mask]) * norm.cdf(-d2[put_mask]) - S * norm.cdf(-d1[put_mask])
                deltas[put_mask] = N_d1[put_mask] - 1
                thetas[put_mask] = (-S * n_d1[put_mask] * sigma[put_mask] / (2 * np.sqrt(T[put_mask])) + 
                                  r * K[put_mask] * np.exp(-r * T[put_mask]) * norm.cdf(-d2[put_mask])) / 365
                rhos[put_mask] = -(K[put_mask] * T[put_mask] * np.exp(-r * T[put_mask]) * norm.cdf(-d2[put_mask])) / 100
            
            # Common Greeks for non-zero DTE
            gammas[non_zero_mask] = n_d1[non_zero_mask] / (S * sigma[non_zero_mask] * np.sqrt(T[non_zero_mask]))
            vegas[non_zero_mask] = S * n_d1[non_zero_mask] * np.sqrt(T[non_zero_mask]) / 100
        
        # Handle 0DTE case (intrinsic value only)
        if np.any(zero_dte_mask):
            call_0dte = (df['option_type'] == 'call').values & zero_dte_mask
            put_0dte = (df['option_type'] == 'put').values & zero_dte_mask
            
            prices[call_0dte] = np.maximum(0, S - K[call_0dte])
            prices[put_0dte] = np.maximum(0, K[put_0dte] - S)
            
            deltas[call_0dte & (S > K)] = 1.0
            deltas[put_0dte & (S < K)] = -1.0
        
        # Add Greeks to dataframe
        df['greeks_price'] = np.maximum(0, prices)
        df['greeks_delta'] = deltas
        df['greeks_gamma'] = gammas
        df['greeks_theta'] = thetas
        df['greeks_vega'] = vegas
        df['greeks_rho'] = rhos
        df['greeks_implied_vol'] = estimated_iv
        
        # Derived Greeks features
        df['abs_delta'] = np.abs(df['greeks_delta'])
        df['gamma_dollar'] = df['greeks_gamma'] * spy_price * spy_price / 100
        df['theta_dollar'] = df['greeks_theta']
        df['vega_dollar'] = df['greeks_vega']
        
        # Greeks ratios and combinations
        df['gamma_theta_ratio'] = np.abs(df['greeks_gamma'] / np.maximum(np.abs(df['greeks_theta']), 0.01))
        df['delta_gamma_product'] = df['abs_delta'] * df['greeks_gamma']
        df['vega_theta_ratio'] = np.abs(df['greeks_vega'] / np.maximum(np.abs(df['greeks_theta']), 0.01))
        
        # Risk metrics
        df['gamma_risk_score'] = df['greeks_gamma'] * df['dte_hours']  # Gamma risk increases near expiry
        df['time_decay_rate'] = np.abs(df['greeks_theta']) / np.maximum(df['greeks_price'], 0.01)
        
        self.feature_categories['greeks_features'].extend([
            'greeks_price', 'greeks_delta', 'greeks_gamma', 'greeks_theta', 'greeks_vega', 'greeks_rho',
            'abs_delta', 'gamma_dollar', 'theta_dollar', 'vega_dollar',
            'gamma_theta_ratio', 'delta_gamma_product', 'vega_theta_ratio',
            'gamma_risk_score', 'time_decay_rate'
        ])
        
        return df
    
    def _add_technical_features(self, df: pd.DataFrame, lookback_periods: List[int]) -> pd.DataFrame:
        """Add technical indicator features"""
        
        # Sort by timestamp for rolling calculations
        df = df.sort_values('timestamp')
        
        # Price-based technical indicators
        for period in lookback_periods:
            # Rolling statistics
            df[f'price_sma_{period}'] = df['close'].rolling(period, min_periods=1).mean()
            df[f'price_std_{period}'] = df['close'].rolling(period, min_periods=1).std()
            df[f'price_zscore_{period}'] = (df['close'] - df[f'price_sma_{period}']) / np.maximum(df[f'price_std_{period}'], 0.01)
            
            # Momentum features
            df[f'momentum_{period}'] = df['close'].pct_change(period)
            df[f'momentum_rank_{period}'] = df['close'].rolling(period).rank(pct=True)
            
            # Volume features
            df[f'volume_sma_{period}'] = df['volume'].rolling(period, min_periods=1).mean()
            df[f'volume_ratio_{period}'] = df['volume'] / np.maximum(df[f'volume_sma_{period}'], 1)
            df[f'volume_zscore_{period}'] = (df['volume'] - df[f'volume_sma_{period}']) / np.maximum(df['volume'].rolling(period).std(), 1)
            
            # Volatility features
            df[f'realized_vol_{period}'] = df['close'].pct_change().rolling(period).std() * np.sqrt(252)
            df[f'price_range_{period}'] = (df['high'].rolling(period).max() - df['low'].rolling(period).min()) / df['close']
        
        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=1).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        
        # MACD
        ema_fast = df['close'].ewm(span=12).mean()
        ema_slow = df['close'].ewm(span=26).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        df['macd_bullish'] = (df['macd'] > df['macd_signal']).astype(int)
        
        # Bollinger Bands
        bb_sma = df['close'].rolling(20, min_periods=1).mean()
        bb_std = df['close'].rolling(20, min_periods=1).std()
        df['bb_upper'] = bb_sma + (bb_std * 2)
        df['bb_lower'] = bb_sma - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / np.maximum(df['bb_upper'] - df['bb_lower'], 0.01)
        df['bb_squeeze'] = (bb_std / bb_sma < 0.1).astype(int)
        
        # Add to feature categories
        tech_features = ['rsi', 'rsi_oversold', 'rsi_overbought', 'macd', 'macd_signal', 
                        'macd_histogram', 'macd_bullish', 'bb_position', 'bb_squeeze']
        
        for period in lookback_periods:
            tech_features.extend([
                f'price_sma_{period}', f'price_std_{period}', f'price_zscore_{period}',
                f'momentum_{period}', f'momentum_rank_{period}',
                f'volume_sma_{period}', f'volume_ratio_{period}', f'volume_zscore_{period}',
                f'realized_vol_{period}', f'price_range_{period}'
            ])
        
        self.feature_categories['technical_indicators'].extend(tech_features)
        
        return df
    
    def _add_regime_features(self, df: pd.DataFrame, market_conditions: Dict) -> pd.DataFrame:
        """Add market regime features"""
        
        # Market regime indicators
        regime = market_conditions.get('market_regime', 'NEUTRAL')
        df['regime_high_fear'] = int(regime == 'HIGH_FEAR')
        df['regime_bearish'] = int(regime == 'BEARISH')
        df['regime_bullish'] = int(regime == 'BULLISH')
        df['regime_high_vol'] = int(regime == 'HIGH_VOLATILITY')
        df['regime_low_vol'] = int(regime == 'LOW_VOLATILITY')
        df['regime_neutral'] = int(regime == 'NEUTRAL')
        
        # Put/Call ratio features
        pcr = market_conditions.get('put_call_ratio', 1.0)
        df['put_call_ratio'] = pcr
        df['pcr_extreme_fear'] = (pcr > 1.5).astype(int)
        df['pcr_fear'] = ((pcr > 1.2) & (pcr <= 1.5)).astype(int)
        df['pcr_neutral'] = ((pcr >= 0.8) & (pcr <= 1.2)).astype(int)
        df['pcr_greed'] = ((pcr >= 0.5) & (pcr < 0.8)).astype(int)
        df['pcr_extreme_greed'] = (pcr < 0.5).astype(int)
        
        # Volatility environment
        total_vol = market_conditions.get('total_volume', 0)
        df['market_volume'] = total_vol
        df['high_volume_day'] = (total_vol > 500000).astype(int)
        df['low_volume_day'] = (total_vol < 100000).astype(int)
        
        self.feature_categories['market_regime'].extend([
            'regime_high_fear', 'regime_bearish', 'regime_bullish', 'regime_high_vol', 'regime_low_vol', 'regime_neutral',
            'put_call_ratio', 'pcr_extreme_fear', 'pcr_fear', 'pcr_neutral', 'pcr_greed', 'pcr_extreme_greed',
            'market_volume', 'high_volume_day', 'low_volume_day'
        ])
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal pattern features"""
        
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Time-based features
        df['hour'] = df['datetime'].dt.hour
        df['minute'] = df['datetime'].dt.minute
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['day_of_month'] = df['datetime'].dt.day
        df['month'] = df['datetime'].dt.month
        df['quarter'] = df['datetime'].dt.quarter
        
        # Market session features
        df['market_open'] = ((df['hour'] == 9) & (df['minute'] >= 30)).astype(int)
        df['morning_session'] = ((df['hour'] >= 9) & (df['hour'] < 11)).astype(int)
        df['midday_session'] = ((df['hour'] >= 11) & (df['hour'] < 14)).astype(int)
        df['afternoon_session'] = ((df['hour'] >= 14) & (df['hour'] < 16)).astype(int)
        df['market_close'] = ((df['hour'] == 15) & (df['minute'] >= 45)).astype(int)
        
        # Time to market close (important for 0DTE)
        market_close_time = df['datetime'].dt.normalize() + pd.Timedelta(hours=16)
        df['minutes_to_close'] = (market_close_time - df['datetime']).dt.total_seconds() / 60
        df['hours_to_close'] = df['minutes_to_close'] / 60
        
        # Expiration timing features
        df['minutes_to_expiry'] = (df['expiration_dt'] - df['datetime']).dt.total_seconds() / 60
        # Fix datetime accessor issues - use normalize() instead of .dt.date
        df['expiry_today'] = (df['expiration_dt'].dt.normalize() == df['datetime'].dt.normalize()).astype(int)
        df['expiry_tomorrow'] = ((df['expiration_dt'].dt.normalize() - df['datetime'].dt.normalize()).dt.days == 1).astype(int)
        
        # Cyclical encoding for time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        self.feature_categories['temporal_patterns'].extend([
            'hour', 'minute', 'day_of_week', 'day_of_month', 'month', 'quarter',
            'market_open', 'morning_session', 'midday_session', 'afternoon_session', 'market_close',
            'minutes_to_close', 'hours_to_close', 'minutes_to_expiry', 'expiry_today', 'expiry_tomorrow',
            'hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos'
        ])
        
        return df
    
    def _add_liquidity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add liquidity and flow features with safety checks"""
        
        # Basic liquidity metrics (with safety for missing columns)
        transactions = df.get('transactions', pd.Series(1, index=df.index))
        vwap = df.get('vwap', df['close'])  # Fallback to close if no VWAP
        
        df['transaction_size'] = df['volume'] / np.maximum(transactions, 1)
        df['price_volume_product'] = df['close'] * df['volume']
        df['vwap_deviation'] = np.abs(df['close'] - vwap) / vwap
        
        # Estimated bid-ask spread (since we don't have real bid-ask)
        df['estimated_spread_bps'] = np.where(
            df['close'] < 0.50, 500,  # 5% for cheap options
            np.where(df['close'] < 2.0, 200,  # 2% for mid-priced
                    np.where(df['close'] < 5.0, 100, 50))  # 1% for expensive, 0.5% for very expensive
        )
        
        # Adjust spread based on volume
        volume_factor = np.minimum(df['volume'] / 100, 1.0)
        df['adjusted_spread_bps'] = df['estimated_spread_bps'] * (1 - volume_factor * 0.3)
        
        # Liquidity scoring
        df['volume_score'] = np.minimum(df['volume'] / 50, 2.0)  # Cap at 2x
        df['transaction_score'] = np.minimum(df['transactions'] / 10, 2.0)  # Cap at 2x
        df['liquidity_score'] = (df['volume_score'] + df['transaction_score']) / 2 * 50
        
        # Market impact estimation
        df['market_impact_score'] = df['volume'] / (df['close'] * 1000)  # Simplified market impact
        
        self.feature_categories['liquidity_flow'].extend([
            'transaction_size', 'price_volume_product', 'vwap_deviation',
            'estimated_spread_bps', 'adjusted_spread_bps', 'volume_score', 
            'transaction_score', 'liquidity_score', 'market_impact_score'
        ])
        
        return df
    
    def _add_cross_asset_features(self, df: pd.DataFrame, market_conditions: Dict) -> pd.DataFrame:
        """Add cross-asset and macro features"""
        
        # VIX-related features (estimated)
        estimated_vix = 20.0  # Default VIX level
        df['vix_level'] = estimated_vix
        df['vix_high'] = int(estimated_vix > 25)
        df['vix_low'] = int(estimated_vix < 15)
        df['vix_spike'] = int(estimated_vix > 30)
        
        # Term structure features (estimated)
        df['term_structure_slope'] = 0.05  # Placeholder for VIX9D/VIX ratio
        df['backwardation'] = (df['term_structure_slope'] < 0).astype(int)
        df['contango'] = (df['term_structure_slope'] > 0.1).astype(int)
        
        # Market stress indicators  
        pcr_values = df['put_call_ratio'].values if 'put_call_ratio' in df.columns else [1.0] * len(df)
        df['market_stress'] = (pd.Series(pcr_values) > 1.3).astype(int)
        df['fear_greed_index'] = 50 - (df['put_call_ratio'] - 1) * 50  # Simplified fear/greed
        
        self.feature_categories['cross_asset'].extend([
            'vix_level', 'vix_high', 'vix_low', 'vix_spike',
            'term_structure_slope', 'backwardation', 'contango',
            'market_stress', 'fear_greed_index'
        ])
        
        return df
    
    def _add_volatility_surface_features(self, df: pd.DataFrame, spy_price: float) -> pd.DataFrame:
        """Add volatility surface features"""
        
        # Moneyness buckets for volatility surface analysis
        df['moneyness_bucket'] = pd.cut(
            df['moneyness'], 
            bins=[0, 0.9, 0.95, 1.05, 1.1, 2.0],
            labels=['deep_otm', 'otm', 'atm', 'itm', 'deep_itm']
        )
        
        # Skew indicators
        df['call_option'] = (df['option_type'] == 'call').astype(int)
        df['put_option'] = (df['option_type'] == 'put').astype(int)
        
        # Implied volatility estimates based on moneyness
        df['iv_estimate'] = 0.20 + np.abs(df['log_moneyness']) * 0.3
        df['iv_rank'] = df.groupby(['datetime'])['iv_estimate'].rank(pct=True)
        df['iv_percentile'] = df['iv_rank'] * 100
        
        # Volatility surface position
        df['vol_surface_position'] = np.where(
            df['moneyness'] < 1.0,
            'put_wing',
            np.where(df['moneyness'] > 1.0, 'call_wing', 'atm_straddle')
        )
        
        self.feature_categories['volatility_surface'].extend([
            'moneyness_bucket', 'call_option', 'put_option',
            'iv_estimate', 'iv_rank', 'iv_percentile', 'vol_surface_position'
        ])
        
        return df
    
    def _add_target_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add target variables for ML training"""
        
        # Forward returns (for supervised learning)
        df = df.sort_values(['symbol', 'timestamp'])
        
        # Calculate forward returns at different horizons
        for horizon in [5, 15, 30, 60]:  # minutes
            df[f'forward_return_{horizon}m'] = df.groupby('symbol')['close'].pct_change(horizon).shift(-horizon)
            df[f'forward_return_{horizon}m_binary'] = (df[f'forward_return_{horizon}m'] > 0).astype(int)
            df[f'forward_return_{horizon}m_strong'] = (np.abs(df[f'forward_return_{horizon}m']) > 0.1).astype(int)
        
        # Volume surge prediction
        df['volume_surge_next'] = (df.groupby('symbol')['volume'].shift(-1) > df['volume'] * 2).astype(int)
        
        # Volatility expansion
        df['vol_expansion_next'] = (df.groupby('symbol')['realized_vol_5'].shift(-1) > df['realized_vol_5'] * 1.5).astype(int)
        
        return df
    
    def get_feature_importance_analysis(self, df: pd.DataFrame) -> Dict:
        """Analyze feature importance and correlations"""
        
        # Feature correlation analysis
        numeric_features = df.select_dtypes(include=[np.number]).columns
        correlation_matrix = df[numeric_features].corr()
        
        # High correlation pairs (potential multicollinearity)
        high_corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr = correlation_matrix.iloc[i, j]
                if abs(corr) > 0.8:
                    high_corr_pairs.append({
                        'feature1': correlation_matrix.columns[i],
                        'feature2': correlation_matrix.columns[j],
                        'correlation': corr
                    })
        
        # Feature statistics
        feature_stats = {}
        for category, features in self.feature_categories.items():
            available_features = [f for f in features if f in df.columns]
            if available_features:
                feature_stats[category] = {
                    'count': len(available_features),
                    'features': available_features,
                    'missing_rate': df[available_features].isnull().mean().mean()
                }
        
        return {
            'total_features': len(numeric_features),
            'feature_categories': feature_stats,
            'high_correlation_pairs': high_corr_pairs[:10],  # Top 10
            'correlation_matrix_shape': correlation_matrix.shape
        }

def main():
    """Main execution function"""
    print("🤖 ML FEATURE ENGINEERING FOR 0DTE OPTIONS TRADING")
    print("=" * 80)
    
    try:
        # Initialize components
        loader = ParquetDataLoader()
        feature_engineer = MLFeatureEngineer()
        
        # Load sample data for feature engineering (smaller sample for testing)
        test_date = datetime(2025, 8, 29)
        print(f"📊 Loading options data for {test_date.strftime('%Y-%m-%d')}...")
        
        options_data = loader.load_options_for_date(test_date, min_volume=5)
        market_conditions = loader.analyze_market_conditions(test_date)
        spy_price = loader._estimate_spy_price(options_data)
        
        if options_data.empty or not spy_price:
            print("❌ No data available for feature engineering demo")
            return
        
        # Use smaller sample for testing (first 1000 rows)
        sample_size = min(1000, len(options_data))
        options_sample = options_data.head(sample_size).copy()
        
        print(f"📊 Processing {len(options_sample)} options for feature engineering...")
        print(f"📊 Dataset columns: {list(options_sample.columns)}")
        print(f"📊 SPY price estimate: ${spy_price:.2f}")
        
        # Generate comprehensive features with debug mode
        features_df = feature_engineer.generate_comprehensive_features(
            options_sample, spy_price, market_conditions, debug_mode=True
        )
        
        # Analyze feature importance
        analysis = feature_engineer.get_feature_importance_analysis(features_df)
        
        print(f"\n📊 FEATURE ENGINEERING RESULTS:")
        print(f"=" * 50)
        print(f"📊 Total Features Generated: {analysis['total_features']}")
        
        print(f"\n📊 FEATURES BY CATEGORY:")
        for category, stats in analysis['feature_categories'].items():
            print(f"   {category}: {stats['count']} features ({stats['missing_rate']:.1%} missing)")
        
        print(f"\n📊 HIGH CORRELATION PAIRS (potential multicollinearity):")
        for pair in analysis['high_correlation_pairs'][:5]:
            print(f"   {pair['feature1']} ↔ {pair['feature2']}: {pair['correlation']:.3f}")
        
        # Save sample features for inspection
        sample_features = features_df.head(100)
        sample_features.to_csv('ml_features_sample.csv', index=False)
        print(f"\n💾 Sample features saved to: ml_features_sample.csv")
        
        print(f"\n🎉 ML FEATURE ENGINEERING COMPLETE!")
        print(f"✅ Ready for multi-year dataset processing")
        print(f"✅ {analysis['total_features']} features available for ML models")
        print(f"✅ Comprehensive feature categories implemented")
        print(f"✅ Target variables prepared for supervised learning")
        
        print(f"\n🚀 NEXT STEPS FOR ML INTEGRATION:")
        print(f"   1. Process full multi-year dataset with these features")
        print(f"   2. Train ML models (XGBoost, Random Forest, Neural Networks)")
        print(f"   3. Feature selection and dimensionality reduction")
        print(f"   4. Cross-validation and backtesting integration")
        print(f"   5. Real-time feature pipeline for live trading")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
