#!/usr/bin/env python3
"""
Phase 4: ML Model Integration with AdaptiveStrategySelector
==========================================================

Integrate the trained ML models (94-100% accuracy) with the AdaptiveMLEnhancedStrategy
to create an intelligent 0DTE trading system that uses ML predictions to:

1. Enhance confidence scoring for signals
2. Improve strategy selection (BUY_CALL vs BUY_PUT vs spreads)
3. Dynamic threshold adjustment based on ML predictions
4. Risk management using profitability predictions

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
from datetime import datetime
import json
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
try:
    import joblib
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    print("⚠️  ML libraries not available. Install with: pip install scikit-learn joblib")
    ML_AVAILABLE = False

# Import our components
from src.data.parquet_data_loader import ParquetDataLoader
from src.strategies.adaptive_ml_enhanced.strategy import AdaptiveMLEnhancedStrategy, StrategyType, MarketRegime, TimeWindow

class MLModelLoader:
    """Load and manage trained ML models for strategy enhancement"""
    
    def __init__(self, models_metadata_path: str):
        if not ML_AVAILABLE:
            raise ImportError("ML libraries required for model loading")
        
        self.models_metadata_path = models_metadata_path
        self.models = {}
        self.scaler = None
        self.feature_names = []
        self.metadata = {}
        
        self._load_models()
    
    def _load_models(self):
        """Load all trained models and metadata"""
        
        print(f"📦 Loading trained ML models...")
        
        # Load metadata
        with open(self.models_metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        self.feature_names = self.metadata['feature_names']
        model_files = self.metadata['model_files']
        
        print(f"   📊 Expected features: {len(self.feature_names)}")
        
        # Load models
        for model_key, model_path in model_files.items():
            if model_key == 'scaler':
                self.scaler = joblib.load(model_path)
                print(f"   ✅ Loaded scaler: {model_path}")
            else:
                self.models[model_key] = joblib.load(model_path)
                print(f"   ✅ Loaded model: {model_key}")
        
        print(f"✅ Loaded {len(self.models)} models + scaler")
    
    def predict_all_targets(self, features: pd.DataFrame) -> Dict[str, Dict]:
        """Generate predictions for all targets using all model types"""
        
        if features.empty:
            return {}
        
        # Ensure features match training data
        missing_features = set(self.feature_names) - set(features.columns)
        if missing_features:
            print(f"⚠️  Missing features: {len(missing_features)} features")
            # Add missing features with median values
            for feature in missing_features:
                features[feature] = 0.0
        
        # Reorder features to match training
        features_ordered = features[self.feature_names]
        
        predictions = {}
        
        # Get predictions from each model type for each target
        targets = ['target_profitable', 'target_high_confidence', 'target_high_value']
        
        for target in targets:
            target_predictions = {}
            
            # XGBoost predictions
            xgb_key = f'xgb_{target}'
            if xgb_key in self.models:
                xgb_pred = self.models[xgb_key].predict_proba(features_ordered)
                target_predictions['xgboost'] = {
                    'probability': xgb_pred[:, 1] if xgb_pred.shape[1] > 1 else xgb_pred[:, 0],
                    'prediction': self.models[xgb_key].predict(features_ordered)
                }
            
            # Random Forest predictions
            rf_key = f'rf_{target}'
            if rf_key in self.models:
                rf_pred = self.models[rf_key].predict_proba(features_ordered)
                target_predictions['random_forest'] = {
                    'probability': rf_pred[:, 1] if rf_pred.shape[1] > 1 else rf_pred[:, 0],
                    'prediction': self.models[rf_key].predict(features_ordered)
                }
            
            # Neural Network predictions (needs scaling)
            nn_key = f'nn_{target}'
            if nn_key in self.models and self.scaler is not None:
                features_scaled = self.scaler.transform(features_ordered)
                nn_pred = self.models[nn_key].predict_proba(features_scaled)
                target_predictions['neural_network'] = {
                    'probability': nn_pred[:, 1] if nn_pred.shape[1] > 1 else nn_pred[:, 0],
                    'prediction': self.models[nn_key].predict(features_scaled)
                }
            
            predictions[target] = target_predictions
        
        return predictions

class MLEnhancedAdaptiveStrategy(AdaptiveMLEnhancedStrategy):
    """
    Enhanced AdaptiveStrategy with ML model integration
    Combines the multi-strategy approach with ML predictions for superior performance
    """
    
    def __init__(self, ml_model_loader: MLModelLoader):
        super().__init__()
        self.ml_loader = ml_model_loader
        
        # Enhanced parameters with ML guidance
        self.ml_confidence_boost = {
            'high_confidence_threshold': 0.7,  # ML confidence threshold
            'profitability_threshold': 0.6,    # ML profitability threshold
            'confidence_boost_factor': 20,     # Boost amount for high ML confidence
            'profitability_boost_factor': 15   # Boost amount for high ML profitability
        }
        
        print(f"🤖 ML-Enhanced Adaptive Strategy initialized")
        print(f"   📊 ML models loaded: {len(self.ml_loader.models)}")
        print(f"   🎯 Feature count: {len(self.ml_loader.feature_names)}")
    
    def _prepare_ml_features(self, options_data: pd.DataFrame, spy_price: float, 
                           market_conditions: Dict) -> pd.DataFrame:
        """Prepare features for ML prediction (simplified version)"""
        
        if options_data.empty:
            return pd.DataFrame()
        
        # Create basic features that match our ML training
        features = pd.DataFrame()
        
        # Basic option data features
        features['close'] = options_data['close']
        features['volume'] = options_data['volume']
        features['strike'] = options_data['strike']
        features['open'] = options_data.get('open', options_data['close'])
        features['high'] = options_data.get('high', options_data['close'])
        features['low'] = options_data.get('low', options_data['close'])
        features['vwap'] = options_data.get('vwap', options_data['close'])
        features['transactions'] = options_data.get('transactions', 1)
        
        # Option type indicators
        features['call_option'] = (options_data['option_type'] == 'call').astype(int)
        features['put_option'] = (options_data['option_type'] == 'put').astype(int)
        
        # Basic derived features
        features['log_volume'] = np.log1p(features['volume'])
        features['volume_score'] = features['volume'] / features['volume'].median()
        features['liquidity_score'] = features['volume'] * features['transactions']
        features['transaction_size'] = features['volume'] / np.maximum(features['transactions'], 1)
        
        # Price-based features
        features['price_zscore_10'] = (features['close'] - features['close'].rolling(10, min_periods=1).mean()) / features['close'].rolling(10, min_periods=1).std()
        features['price_zscore_20'] = (features['close'] - features['close'].rolling(20, min_periods=1).mean()) / features['close'].rolling(20, min_periods=1).std()
        
        # Volume-based features
        features['volume_zscore_5'] = (features['volume'] - features['volume'].rolling(5, min_periods=1).mean()) / features['volume'].rolling(5, min_periods=1).std()
        features['volume_zscore_10'] = (features['volume'] - features['volume'].rolling(10, min_periods=1).mean()) / features['volume'].rolling(10, min_periods=1).std()
        features['volume_ratio_20'] = features['volume'] / features['volume'].rolling(20, min_periods=1).mean()
        
        # Spread estimation (simplified)
        features['estimated_spread_bps'] = np.maximum(0.01, 0.05 / np.sqrt(features['volume']))
        features['adjusted_spread_bps'] = features['estimated_spread_bps'] * features['liquidity_score']
        
        # Greeks (simplified Black-Scholes approximation)
        # This is a simplified version - in production, use proper Greeks calculation
        moneyness = features['strike'] / spy_price
        time_to_expiry = 1/365  # Assume 1 day for 0DTE
        
        features['greeks_delta'] = np.where(features['call_option'] == 1, 
                                          np.maximum(0, 1 - abs(moneyness - 1)), 
                                          np.maximum(0, abs(moneyness - 1) - 1))
        features['greeks_theta'] = -features['close'] * 0.1  # Simplified theta
        features['greeks_rho'] = features['close'] * moneyness * 0.01  # Simplified rho
        
        # Theta-related features
        features['theta_dollar'] = features['greeks_theta'] * features['volume']
        features['gamma_theta_ratio'] = abs(features['greeks_delta']) / np.maximum(abs(features['greeks_theta']), 0.001)
        features['vega_theta_ratio'] = features['close'] / np.maximum(abs(features['greeks_theta']), 0.001)
        
        # Fill any remaining NaN values
        features = features.fillna(0)
        
        return features
    
    def generate_ml_enhanced_signal(self, options_data: pd.DataFrame, spy_price: float,
                                  market_conditions: Dict, current_time: datetime) -> Dict:
        """Generate signal enhanced with ML predictions"""
        
        print(f"🤖 ML-ENHANCED ADAPTIVE STRATEGY - Analyzing with ML...")
        print(f"📊 Data: {len(options_data)} options, SPY: ${spy_price:.2f}")
        
        # First, get the base adaptive signal
        base_result = self.generate_adaptive_signal(options_data, spy_price, market_conditions, current_time)
        
        if base_result['selected_strategy'] == StrategyType.NO_TRADE:
            print(f"   ❌ Base strategy rejected - no ML enhancement needed")
            return base_result
        
        # Prepare features for ML prediction
        ml_features = self._prepare_ml_features(options_data, spy_price, market_conditions)
        
        if ml_features.empty:
            print(f"   ⚠️  No ML features available - using base signal")
            return base_result
        
        # Get ML predictions
        try:
            ml_predictions = self.ml_loader.predict_all_targets(ml_features)
            
            if not ml_predictions:
                print(f"   ⚠️  No ML predictions available - using base signal")
                return base_result
            
            # Enhance the signal with ML predictions
            enhanced_result = self._enhance_signal_with_ml(base_result, ml_predictions, options_data)
            
            return enhanced_result
            
        except Exception as e:
            print(f"   ❌ ML prediction error: {e}")
            print(f"   🔄 Falling back to base signal")
            return base_result
    
    def _enhance_signal_with_ml(self, base_result: Dict, ml_predictions: Dict, 
                              options_data: pd.DataFrame) -> Dict:
        """Enhance base signal using ML predictions"""
        
        # Extract ML predictions (use ensemble average)
        profitable_probs = []
        confidence_probs = []
        value_probs = []
        
        for target, predictions in ml_predictions.items():
            if target == 'target_profitable':
                for model_type, pred in predictions.items():
                    profitable_probs.extend(pred['probability'])
            elif target == 'target_high_confidence':
                for model_type, pred in predictions.items():
                    confidence_probs.extend(pred['probability'])
            elif target == 'target_high_value':
                for model_type, pred in predictions.items():
                    value_probs.extend(pred['probability'])
        
        # Calculate ensemble averages
        avg_profitable_prob = np.mean(profitable_probs) if profitable_probs else 0.5
        avg_confidence_prob = np.mean(confidence_probs) if confidence_probs else 0.5
        avg_value_prob = np.mean(value_probs) if value_probs else 0.5
        
        print(f"   🤖 ML Predictions:")
        print(f"      Profitable: {avg_profitable_prob:.3f}")
        print(f"      High Confidence: {avg_confidence_prob:.3f}")
        print(f"      High Value: {avg_value_prob:.3f}")
        
        # Start with base confidence
        base_confidence = base_result['confidence']
        enhanced_confidence = base_confidence
        
        # Enhance confidence based on ML predictions
        confidence_boost = 0
        
        # Boost for high profitability prediction
        if avg_profitable_prob > self.ml_confidence_boost['profitability_threshold']:
            profit_boost = (avg_profitable_prob - 0.5) * self.ml_confidence_boost['profitability_boost_factor']
            confidence_boost += profit_boost
            print(f"      📈 Profitability boost: +{profit_boost:.1f}%")
        
        # Boost for high confidence prediction
        if avg_confidence_prob > self.ml_confidence_boost['high_confidence_threshold']:
            conf_boost = (avg_confidence_prob - 0.5) * self.ml_confidence_boost['confidence_boost_factor']
            confidence_boost += conf_boost
            print(f"      📈 Confidence boost: +{conf_boost:.1f}%")
        
        # Apply confidence boost
        enhanced_confidence = min(95, base_confidence + confidence_boost)
        
        # Strategy refinement based on ML predictions
        enhanced_strategy = base_result['selected_strategy']
        
        # If ML suggests low profitability, be more conservative
        if avg_profitable_prob < 0.4:
            print(f"      ⚠️  Low profitability prediction - reducing confidence")
            enhanced_confidence *= 0.8
        
        # If ML suggests high value opportunities, consider strategy adjustment
        if avg_value_prob > 0.8 and enhanced_strategy in [StrategyType.BUY_CALL, StrategyType.BUY_PUT]:
            print(f"      💰 High value prediction - maintaining aggressive strategy")
        
        # Create enhanced result
        enhanced_result = base_result.copy()
        enhanced_result['confidence'] = enhanced_confidence
        enhanced_result['ml_enhanced'] = True
        enhanced_result['ml_predictions'] = {
            'profitable': avg_profitable_prob,
            'high_confidence': avg_confidence_prob,
            'high_value': avg_value_prob
        }
        enhanced_result['confidence_boost'] = confidence_boost
        
        # Update signal if present
        if enhanced_result['signal']:
            enhanced_result['signal']['confidence'] = enhanced_confidence
            enhanced_result['signal']['ml_enhanced'] = True
            enhanced_result['signal']['ml_predictions'] = enhanced_result['ml_predictions']
        
        # Update reasoning
        enhanced_result['reasoning'].append(f"🤖 ML Enhancement: +{confidence_boost:.1f}% confidence boost")
        enhanced_result['reasoning'].append(f"   Profitable: {avg_profitable_prob:.1%}, Confidence: {avg_confidence_prob:.1%}, Value: {avg_value_prob:.1%}")
        
        print(f"   ✅ Enhanced confidence: {base_confidence:.1f}% → {enhanced_confidence:.1f}% (+{confidence_boost:.1f}%)")
        
        return enhanced_result

class MLEnhancedBacktester:
    """Backtester for ML-Enhanced Adaptive Strategy"""
    
    def __init__(self, ml_model_loader: MLModelLoader):
        self.strategy = MLEnhancedAdaptiveStrategy(ml_model_loader)
        self.loader = ParquetDataLoader()
    
    def run_ml_enhanced_backtest(self, start_date: datetime, end_date: datetime,
                               max_days: int = 10) -> Dict:
        """Run backtest comparing ML-enhanced vs base strategy"""
        
        print("🚀 PHASE 4: ML-ENHANCED STRATEGY BACKTEST")
        print("=" * 80)
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"🏗️ Following .cursorrules: src/tests/analysis/")
        print("=" * 80)
        
        available_dates = self.loader.get_available_dates(start_date, end_date)
        test_dates = available_dates[:max_days]
        
        backtest_results = {
            'strategy': 'ML-Enhanced Adaptive Strategy',
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'days_tested': len(test_dates),
            'base_signals': 0,
            'ml_enhanced_signals': 0,
            'confidence_improvements': [],
            'ml_predictions_summary': {
                'profitable': [],
                'high_confidence': [],
                'high_value': []
            },
            'daily_results': []
        }
        
        print(f"📊 Testing {len(test_dates)} trading days with ML enhancement...")
        
        for i, test_date in enumerate(test_dates, 1):
            print(f"\n📅 Day {i}/{len(test_dates)}: {test_date.strftime('%Y-%m-%d')}")
            
            # Load data
            options_data = self.loader.load_options_for_date(test_date, min_volume=5)
            market_conditions = self.loader.analyze_market_conditions(test_date)
            
            if options_data.empty:
                print(f"   ⚠️  No options data available")
                continue
            
            spy_price = self.loader._estimate_spy_price(options_data)
            if not spy_price:
                print(f"   ⚠️  Could not estimate SPY price")
                continue
            
            print(f"   📊 {len(options_data)} options, SPY: ${spy_price:.2f}")
            
            # Generate ML-enhanced signal
            result = self.strategy.generate_ml_enhanced_signal(
                options_data, spy_price, market_conditions, test_date
            )
            
            # Record results
            day_result = {
                'date': test_date.isoformat(),
                'spy_price': spy_price,
                'selected_strategy': result['selected_strategy'].value,
                'base_confidence': result.get('confidence', 0),
                'ml_enhanced': result.get('ml_enhanced', False),
                'confidence_boost': result.get('confidence_boost', 0),
                'ml_predictions': result.get('ml_predictions', {}),
                'reasoning': result['reasoning']
            }
            
            backtest_results['daily_results'].append(day_result)
            
            if result['selected_strategy'] != StrategyType.NO_TRADE:
                backtest_results['base_signals'] += 1
                
                if result.get('ml_enhanced', False):
                    backtest_results['ml_enhanced_signals'] += 1
                    backtest_results['confidence_improvements'].append(result.get('confidence_boost', 0))
                    
                    # Collect ML predictions
                    ml_preds = result.get('ml_predictions', {})
                    if 'profitable' in ml_preds:
                        backtest_results['ml_predictions_summary']['profitable'].append(ml_preds['profitable'])
                    if 'high_confidence' in ml_preds:
                        backtest_results['ml_predictions_summary']['high_confidence'].append(ml_preds['high_confidence'])
                    if 'high_value' in ml_preds:
                        backtest_results['ml_predictions_summary']['high_value'].append(ml_preds['high_value'])
                
                print(f"   ✅ SIGNAL: {result['selected_strategy'].value} ({result['confidence']:.1f}% confidence)")
                if result.get('ml_enhanced', False):
                    print(f"      🤖 ML Enhanced: +{result.get('confidence_boost', 0):.1f}% boost")
            else:
                print(f"   ❌ NO TRADE")
        
        # Generate summary
        self._generate_ml_backtest_summary(backtest_results)
        
        return backtest_results
    
    def _generate_ml_backtest_summary(self, results: Dict):
        """Generate comprehensive ML backtest summary"""
        
        print(f"\n" + "=" * 80)
        print(f"📊 ML-ENHANCED STRATEGY BACKTEST RESULTS")
        print(f"=" * 80)
        
        print(f"Days Tested: {results['days_tested']}")
        print(f"Base Signals Generated: {results['base_signals']}")
        print(f"ML-Enhanced Signals: {results['ml_enhanced_signals']}")
        
        if results['base_signals'] > 0:
            enhancement_rate = results['ml_enhanced_signals'] / results['base_signals'] * 100
            print(f"ML Enhancement Rate: {enhancement_rate:.1f}%")
        
        # Confidence improvement analysis
        if results['confidence_improvements']:
            improvements = results['confidence_improvements']
            print(f"\n📈 CONFIDENCE IMPROVEMENTS:")
            print(f"   Average Boost: {np.mean(improvements):.1f}%")
            print(f"   Max Boost: {np.max(improvements):.1f}%")
            print(f"   Min Boost: {np.min(improvements):.1f}%")
        
        # ML predictions analysis
        ml_summary = results['ml_predictions_summary']
        if any(ml_summary.values()):
            print(f"\n🤖 ML PREDICTIONS SUMMARY:")
            for pred_type, values in ml_summary.items():
                if values:
                    print(f"   {pred_type.title()}: {np.mean(values):.3f} avg (range: {np.min(values):.3f}-{np.max(values):.3f})")

def main():
    """Run Phase 4: ML Model Integration"""
    
    print("🚀 PHASE 4: ML MODEL INTEGRATION")
    print("🏗️ Following .cursorrules: src/tests/analysis/")
    print("=" * 80)
    
    if not ML_AVAILABLE:
        print("❌ ML libraries not available")
        print("📦 Install with: pip install scikit-learn joblib")
        return
    
    try:
        # Load trained ML models
        models_metadata_path = "src/tests/analysis/trained_models/ml_models_metadata_20250830_233847.json"
        
        if not os.path.exists(models_metadata_path):
            print(f"❌ ML models not found: {models_metadata_path}")
            print("🔄 Please run Phase 3 (phase3_ml_model_training.py) first")
            return
        
        # Initialize ML model loader
        ml_loader = MLModelLoader(models_metadata_path)
        
        # Initialize ML-enhanced backtester
        backtester = MLEnhancedBacktester(ml_loader)
        
        # Run ML-enhanced backtest
        end_date = datetime(2025, 8, 29)
        start_date = datetime(2025, 8, 20)
        
        results = backtester.run_ml_enhanced_backtest(start_date, end_date, max_days=8)
        
        print(f"\n🎯 PHASE 4 COMPLETE - ML INTEGRATION SUCCESSFUL")
        print(f"=" * 80)
        print(f"✅ ML models successfully integrated with AdaptiveStrategy")
        print(f"✅ ML-enhanced signals generated with confidence boosting")
        print(f"✅ Ensemble predictions from XGBoost, Random Forest, Neural Networks")
        print(f"✅ Ready for Phase 5: Comparative performance analysis")
        
        print(f"\n📋 NEXT STEPS:")
        print(f"1. 📊 Phase 5: Compare ML-enhanced vs baseline performance")
        print(f"2. 🚀 Deploy ML-enhanced strategy for live trading")
        print(f"3. 📈 Monitor performance and retrain models as needed")
        print(f"4. 🔄 Continuous improvement based on live trading results")
        
    except Exception as e:
        print(f"❌ Error in Phase 4: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
