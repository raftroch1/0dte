#!/usr/bin/env python3
"""
Phase 3: ML Model Training & Validation
======================================

Train and validate ML models to enhance the AdaptiveStrategySelector's
confidence scoring and strategy selection for 0DTE options trading.

Models trained:
1. XGBoost - Gradient boosting for feature importance and performance
2. Random Forest - Ensemble method for robustness
3. Neural Network - Deep learning for complex pattern recognition
4. Logistic Regression - Baseline linear model for comparison

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
    import xgboost as xgb
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier, MLPRegressor
    from sklearn.model_selection import cross_val_score, GridSearchCV, TimeSeriesSplit
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.impute import SimpleImputer
    import joblib
    ML_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ML libraries not available: {e}")
    print("📦 Install with: pip install xgboost scikit-learn joblib")
    ML_AVAILABLE = False

class MLModelTrainer:
    """
    Phase 3: Train ML models to enhance AdaptiveStrategySelector
    """
    
    def __init__(self):
        if not ML_AVAILABLE:
            raise ImportError("ML libraries required. Install with: pip install xgboost scikit-learn joblib")
        
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.performance_metrics = {}
        
    def load_ml_dataset(self, dataset_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load the ML dataset created in Phase 2"""
        
        print(f"📊 Loading ML dataset from Phase 2...")
        
        # Load the dataset
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"ML dataset not found: {dataset_path}")
        
        df = pd.read_parquet(dataset_path)
        print(f"✅ Loaded dataset: {len(df):,} samples × {len(df.columns)} features")
        
        # Create train/validation/test splits by date (temporal split)
        df_sorted = df.sort_values('date').copy()
        
        total_samples = len(df_sorted)
        train_end = int(total_samples * 0.7)
        val_end = int(total_samples * 0.85)
        
        train_df = df_sorted.iloc[:train_end].copy()
        val_df = df_sorted.iloc[train_end:val_end].copy()
        test_df = df_sorted.iloc[val_end:].copy()
        
        print(f"📊 Train: {len(train_df):,} samples ({len(train_df)/total_samples*100:.1f}%)")
        print(f"📊 Validation: {len(val_df):,} samples ({len(val_df)/total_samples*100:.1f}%)")
        print(f"📊 Test: {len(test_df):,} samples ({len(test_df)/total_samples*100:.1f}%)")
        
        return train_df, val_df, test_df
    
    def prepare_features_and_targets(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare features and target variables for ML training"""
        
        print(f"🔧 Preparing features and targets...")
        
        # Exclude metadata columns and datetime columns
        exclude_cols = ['date', 'spy_price', 'market_regime', 'symbol', 'timestamp', 
                       'underlying', 'expiration', 'option_type', 'datetime', 'expiration_dt']
        
        # Get all columns first
        all_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Separate numeric and non-numeric
        numeric_cols = []
        for col in all_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_cols.append(col)
            else:
                print(f"   Skipping non-numeric column: {col} ({df[col].dtype})")
        
        # Identify target variables (created by MLFeatureEngineer)
        target_cols = [col for col in numeric_cols if col.startswith('target_')]
        feature_cols = [col for col in numeric_cols if not col.startswith('target_')]
        
        print(f"📊 Features: {len(feature_cols)} columns")
        print(f"🎯 Targets: {len(target_cols)} columns")
        
        if len(target_cols) == 0:
            # Create simple targets if not available
            print("⚠️  No target variables found, creating simple targets...")
            
            # Target 1: Profitable trade (price moved in favorable direction)
            if 'close' in df.columns and 'strike' in df.columns and 'option_type' in df.columns:
                df['target_profitable'] = ((df['close'] > df['strike']) & (df['option_type'] == 'call')) | \
                                         ((df['close'] < df['strike']) & (df['option_type'] == 'put'))
                df['target_profitable'] = df['target_profitable'].astype(int)
                target_cols.append('target_profitable')
            
            # Target 2: High confidence signal (volume > median)
            if 'volume' in df.columns:
                median_volume = df['volume'].median()
                df['target_high_confidence'] = (df['volume'] > median_volume).astype(int)
                target_cols.append('target_high_confidence')
            
            # Target 3: High value option (close price > median)
            if 'close' in df.columns:
                median_close = df['close'].median()
                df['target_high_value'] = (df['close'] > median_close).astype(int)
                target_cols.append('target_high_value')
        
        # Use the feature_cols directly (already filtered for numeric)
        print(f"   📊 Using {len(feature_cols)} numeric features")
        
        # Get the actual feature data
        feature_data = df[feature_cols].copy()
        
        # Check for columns with all NaN values and remove them
        valid_features = []
        for col in feature_cols:
            if not feature_data[col].isna().all():
                valid_features.append(col)
            else:
                print(f"   Removing all-NaN column: {col}")
        
        print(f"   📊 Valid features after NaN check: {len(valid_features)}")
        
        # Handle missing values
        imputer = SimpleImputer(strategy='median')
        X_imputed = imputer.fit_transform(feature_data[valid_features])
        
        # Create DataFrame with correct shape
        X = pd.DataFrame(
            X_imputed,
            columns=valid_features,
            index=df.index
        )
        
        y = df[target_cols].copy()
        
        print(f"✅ Prepared {len(X)} samples with {len(valid_features)} features and {len(target_cols)} targets")
        
        return X, y
    
    def train_xgboost_models(self, X_train: pd.DataFrame, y_train: pd.DataFrame,
                           X_val: pd.DataFrame, y_val: pd.DataFrame) -> Dict:
        """Train XGBoost models for each target variable"""
        
        print(f"\n🚀 TRAINING XGBOOST MODELS")
        print(f"=" * 50)
        
        xgb_models = {}
        xgb_performance = {}
        
        for target_col in y_train.columns:
            print(f"\n📊 Training XGBoost for: {target_col}")
            
            # Prepare target
            y_target = y_train[target_col].values
            y_val_target = y_val[target_col].values
            
            # Check if classification or regression
            if len(np.unique(y_target)) <= 10:  # Classification
                model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    eval_metric='logloss'
                )
                
                # Train model
                model.fit(
                    X_train, y_target,
                    eval_set=[(X_val, y_val_target)],
                    verbose=False
                )
                
                # Predictions
                y_pred = model.predict(X_val)
                y_pred_proba = model.predict_proba(X_val)[:, 1] if len(np.unique(y_target)) == 2 else None
                
                # Metrics
                metrics = {
                    'accuracy': accuracy_score(y_val_target, y_pred),
                    'precision': precision_score(y_val_target, y_pred, average='weighted'),
                    'recall': recall_score(y_val_target, y_pred, average='weighted'),
                    'f1': f1_score(y_val_target, y_pred, average='weighted')
                }
                
                if y_pred_proba is not None:
                    metrics['auc'] = roc_auc_score(y_val_target, y_pred_proba)
                
            else:  # Regression
                model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                )
                
                # Train model
                model.fit(
                    X_train, y_target,
                    eval_set=[(X_val, y_val_target)],
                    verbose=False
                )
                
                # Predictions
                y_pred = model.predict(X_val)
                
                # Metrics
                metrics = {
                    'mse': mean_squared_error(y_val_target, y_pred),
                    'mae': mean_absolute_error(y_val_target, y_pred),
                    'r2': r2_score(y_val_target, y_pred)
                }
            
            xgb_models[target_col] = model
            xgb_performance[target_col] = metrics
            
            print(f"   ✅ {target_col}: {list(metrics.keys())[0]} = {list(metrics.values())[0]:.4f}")
        
        return {
            'models': xgb_models,
            'performance': xgb_performance,
            'feature_importance': {
                target: dict(zip(X_train.columns, model.feature_importances_))
                for target, model in xgb_models.items()
            }
        }
    
    def train_random_forest_models(self, X_train: pd.DataFrame, y_train: pd.DataFrame,
                                 X_val: pd.DataFrame, y_val: pd.DataFrame) -> Dict:
        """Train Random Forest models for each target variable"""
        
        print(f"\n🌲 TRAINING RANDOM FOREST MODELS")
        print(f"=" * 50)
        
        rf_models = {}
        rf_performance = {}
        
        for target_col in y_train.columns:
            print(f"\n📊 Training Random Forest for: {target_col}")
            
            # Prepare target
            y_target = y_train[target_col].values
            y_val_target = y_val[target_col].values
            
            # Check if classification or regression
            if len(np.unique(y_target)) <= 10:  # Classification
                model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
                
                # Train model
                model.fit(X_train, y_target)
                
                # Predictions
                y_pred = model.predict(X_val)
                y_pred_proba = model.predict_proba(X_val)[:, 1] if len(np.unique(y_target)) == 2 else None
                
                # Metrics
                metrics = {
                    'accuracy': accuracy_score(y_val_target, y_pred),
                    'precision': precision_score(y_val_target, y_pred, average='weighted'),
                    'recall': recall_score(y_val_target, y_pred, average='weighted'),
                    'f1': f1_score(y_val_target, y_pred, average='weighted')
                }
                
                if y_pred_proba is not None:
                    metrics['auc'] = roc_auc_score(y_val_target, y_pred_proba)
                
            else:  # Regression
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
                
                # Train model
                model.fit(X_train, y_target)
                
                # Predictions
                y_pred = model.predict(X_val)
                
                # Metrics
                metrics = {
                    'mse': mean_squared_error(y_val_target, y_pred),
                    'mae': mean_absolute_error(y_val_target, y_pred),
                    'r2': r2_score(y_val_target, y_pred)
                }
            
            rf_models[target_col] = model
            rf_performance[target_col] = metrics
            
            print(f"   ✅ {target_col}: {list(metrics.keys())[0]} = {list(metrics.values())[0]:.4f}")
        
        return {
            'models': rf_models,
            'performance': rf_performance,
            'feature_importance': {
                target: dict(zip(X_train.columns, model.feature_importances_))
                for target, model in rf_models.items()
            }
        }
    
    def train_neural_network_models(self, X_train: pd.DataFrame, y_train: pd.DataFrame,
                                  X_val: pd.DataFrame, y_val: pd.DataFrame) -> Dict:
        """Train Neural Network models for each target variable"""
        
        print(f"\n🧠 TRAINING NEURAL NETWORK MODELS")
        print(f"=" * 50)
        
        # Scale features for neural networks
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        nn_models = {}
        nn_performance = {}
        
        for target_col in y_train.columns:
            print(f"\n📊 Training Neural Network for: {target_col}")
            
            # Prepare target
            y_target = y_train[target_col].values
            y_val_target = y_val[target_col].values
            
            # Check if classification or regression
            if len(np.unique(y_target)) <= 10:  # Classification
                model = MLPClassifier(
                    hidden_layer_sizes=(100, 50),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    batch_size='auto',
                    learning_rate='constant',
                    learning_rate_init=0.001,
                    max_iter=300,
                    random_state=42
                )
                
                # Train model
                model.fit(X_train_scaled, y_target)
                
                # Predictions
                y_pred = model.predict(X_val_scaled)
                y_pred_proba = model.predict_proba(X_val_scaled)[:, 1] if len(np.unique(y_target)) == 2 else None
                
                # Metrics
                metrics = {
                    'accuracy': accuracy_score(y_val_target, y_pred),
                    'precision': precision_score(y_val_target, y_pred, average='weighted'),
                    'recall': recall_score(y_val_target, y_pred, average='weighted'),
                    'f1': f1_score(y_val_target, y_pred, average='weighted')
                }
                
                if y_pred_proba is not None:
                    metrics['auc'] = roc_auc_score(y_val_target, y_pred_proba)
                
            else:  # Regression
                model = MLPRegressor(
                    hidden_layer_sizes=(100, 50),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    batch_size='auto',
                    learning_rate='constant',
                    learning_rate_init=0.001,
                    max_iter=300,
                    random_state=42
                )
                
                # Train model
                model.fit(X_train_scaled, y_target)
                
                # Predictions
                y_pred = model.predict(X_val_scaled)
                
                # Metrics
                metrics = {
                    'mse': mean_squared_error(y_val_target, y_pred),
                    'mae': mean_absolute_error(y_val_target, y_pred),
                    'r2': r2_score(y_val_target, y_pred)
                }
            
            nn_models[target_col] = model
            nn_performance[target_col] = metrics
            
            print(f"   ✅ {target_col}: {list(metrics.keys())[0]} = {list(metrics.values())[0]:.4f}")
        
        return {
            'models': nn_models,
            'performance': nn_performance,
            'scaler': scaler
        }
    
    def analyze_feature_importance(self, xgb_results: Dict, rf_results: Dict) -> Dict:
        """Analyze and combine feature importance from different models"""
        
        print(f"\n🔍 ANALYZING FEATURE IMPORTANCE")
        print(f"=" * 50)
        
        combined_importance = {}
        
        for target in xgb_results['feature_importance'].keys():
            xgb_importance = xgb_results['feature_importance'][target]
            rf_importance = rf_results['feature_importance'][target]
            
            # Combine importances (average)
            all_features = set(xgb_importance.keys()) | set(rf_importance.keys())
            combined = {}
            
            for feature in all_features:
                xgb_imp = xgb_importance.get(feature, 0)
                rf_imp = rf_importance.get(feature, 0)
                combined[feature] = (xgb_imp + rf_imp) / 2
            
            # Sort by importance
            sorted_importance = dict(sorted(combined.items(), key=lambda x: x[1], reverse=True))
            combined_importance[target] = sorted_importance
            
            # Show top 10 features
            print(f"\n📊 Top 10 features for {target}:")
            for i, (feature, importance) in enumerate(list(sorted_importance.items())[:10], 1):
                print(f"   {i:2d}. {feature}: {importance:.4f}")
        
        return combined_importance
    
    def save_trained_models(self, xgb_results: Dict, rf_results: Dict, nn_results: Dict,
                          feature_importance: Dict, X_train: pd.DataFrame) -> str:
        """Save all trained models and results"""
        
        print(f"\n💾 SAVING TRAINED MODELS")
        print(f"=" * 50)
        
        # Create models directory
        models_dir = os.path.join(os.path.dirname(__file__), 'trained_models')
        os.makedirs(models_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save models
        model_files = {}
        
        # XGBoost models
        for target, model in xgb_results['models'].items():
            filename = f"xgb_{target}_{timestamp}.joblib"
            filepath = os.path.join(models_dir, filename)
            joblib.dump(model, filepath)
            model_files[f'xgb_{target}'] = filepath
        
        # Random Forest models
        for target, model in rf_results['models'].items():
            filename = f"rf_{target}_{timestamp}.joblib"
            filepath = os.path.join(models_dir, filename)
            joblib.dump(model, filepath)
            model_files[f'rf_{target}'] = filepath
        
        # Neural Network models
        for target, model in nn_results['models'].items():
            filename = f"nn_{target}_{timestamp}.joblib"
            filepath = os.path.join(models_dir, filename)
            joblib.dump(model, filepath)
            model_files[f'nn_{target}'] = filepath
        
        # Save scaler
        scaler_file = os.path.join(models_dir, f"scaler_{timestamp}.joblib")
        joblib.dump(nn_results['scaler'], scaler_file)
        model_files['scaler'] = scaler_file
        
        # Save metadata
        metadata = {
            'training_date': datetime.now().isoformat(),
            'model_files': model_files,
            'feature_names': list(X_train.columns),
            'target_variables': list(xgb_results['models'].keys()),
            'performance_metrics': {
                'xgboost': xgb_results['performance'],
                'random_forest': rf_results['performance'],
                'neural_network': nn_results['performance']
            },
            'feature_importance': feature_importance,
            'model_info': {
                'xgboost': 'Gradient boosting for feature importance and performance',
                'random_forest': 'Ensemble method for robustness',
                'neural_network': 'Deep learning for complex pattern recognition'
            }
        }
        
        metadata_file = os.path.join(models_dir, f"ml_models_metadata_{timestamp}.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"✅ Models saved to: {models_dir}")
        print(f"✅ Metadata saved to: {metadata_file}")
        
        return metadata_file
    
    def run_complete_training(self, dataset_path: str) -> Dict:
        """Run complete ML model training pipeline"""
        
        print("🚀 PHASE 3: ML MODEL TRAINING & VALIDATION")
        print("🏗️ Following .cursorrules: src/tests/analysis/")
        print("=" * 80)
        
        try:
            # Load dataset
            train_df, val_df, test_df = self.load_ml_dataset(dataset_path)
            
            # Combine all data to ensure consistent feature selection
            all_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
            
            # Prepare features and targets on combined data to get consistent feature set
            X_all, y_all = self.prepare_features_and_targets(all_df)
            
            # Split back into train/val/test using the same indices
            train_size = len(train_df)
            val_size = len(val_df)
            
            X_train = X_all.iloc[:train_size].copy()
            y_train = y_all.iloc[:train_size].copy()
            
            X_val = X_all.iloc[train_size:train_size+val_size].copy()
            y_val = y_all.iloc[train_size:train_size+val_size].copy()
            
            X_test = X_all.iloc[train_size+val_size:].copy()
            y_test = y_all.iloc[train_size+val_size:].copy()
            
            print(f"\n📊 TRAINING DATA SUMMARY:")
            print(f"   Features: {len(X_train.columns)}")
            print(f"   Targets: {len(y_train.columns)}")
            print(f"   Training samples: {len(X_train):,}")
            print(f"   Validation samples: {len(X_val):,}")
            print(f"   Test samples: {len(X_test):,}")
            
            # Train models
            xgb_results = self.train_xgboost_models(X_train, y_train, X_val, y_val)
            rf_results = self.train_random_forest_models(X_train, y_train, X_val, y_val)
            nn_results = self.train_neural_network_models(X_train, y_train, X_val, y_val)
            
            # Analyze feature importance
            feature_importance = self.analyze_feature_importance(xgb_results, rf_results)
            
            # Save models
            metadata_file = self.save_trained_models(
                xgb_results, rf_results, nn_results, feature_importance, X_train
            )
            
            print(f"\n🎯 PHASE 3 COMPLETE - ML MODELS TRAINED")
            print(f"=" * 80)
            print(f"✅ XGBoost models trained and validated")
            print(f"✅ Random Forest models trained and validated")
            print(f"✅ Neural Network models trained and validated")
            print(f"✅ Feature importance analysis complete")
            print(f"✅ All models saved for Phase 4 integration")
            
            return {
                'xgboost': xgb_results,
                'random_forest': rf_results,
                'neural_network': nn_results,
                'feature_importance': feature_importance,
                'metadata_file': metadata_file,
                'test_data': (X_test, y_test)
            }
            
        except Exception as e:
            print(f"❌ Error in ML model training: {e}")
            import traceback
            traceback.print_exc()
            return {}

def main():
    """Run Phase 3: ML Model Training"""
    
    print("🚀 PHASE 3: ML MODEL TRAINING & VALIDATION")
    print("🏗️ Following .cursorrules: src/tests/analysis/")
    print("=" * 80)
    
    if not ML_AVAILABLE:
        print("❌ ML libraries not available")
        print("📦 Install with: pip install xgboost scikit-learn joblib")
        return
    
    try:
        trainer = MLModelTrainer()
        
        # Use the ML dataset from Phase 2
        dataset_path = "src/tests/analysis/ml_datasets/ml_dataset_20250801_20250829_20250830_232046_full.parquet"
        
        if not os.path.exists(dataset_path):
            print(f"❌ ML dataset not found: {dataset_path}")
            print("🔄 Please run Phase 2 (phase2_ml_feature_preparation.py) first")
            return
        
        # Run complete training
        results = trainer.run_complete_training(dataset_path)
        
        if results:
            print(f"\n📋 NEXT STEPS:")
            print(f"1. 🔄 Phase 4: Integrate best ML models into AdaptiveMLEnhancedStrategy")
            print(f"2. 📊 Phase 5: Compare ML-enhanced vs baseline performance")
            print(f"3. 🚀 Deploy enhanced strategy with ML signal generation")
            print(f"4. 📈 Monitor performance and retrain models as needed")
        
    except Exception as e:
        print(f"❌ Error in Phase 3: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
