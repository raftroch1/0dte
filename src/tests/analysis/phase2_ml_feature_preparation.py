#!/usr/bin/env python3
"""
Phase 2: ML Feature Engineering & Dataset Preparation
====================================================

Generate comprehensive ML features from year-long SPY options dataset
to train models that can enhance the Enhanced 0DTE Strategy.

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
from typing import Dict, List, Optional, Tuple

from src.data.parquet_data_loader import ParquetDataLoader
from src.data.ml_feature_engineering import MLFeatureEngineer

class MLFeaturePreparation:
    """Phase 2: Prepare ML features for enhanced 0DTE strategy"""
    
    def __init__(self):
        self.loader = ParquetDataLoader()
        self.feature_engineer = MLFeatureEngineer()
        
    def prepare_ml_dataset(self, start_date: datetime, end_date: datetime,
                          sample_days: int = 20, sample_size_per_day: int = 500) -> Dict:
        """Prepare comprehensive ML dataset following .cursorrules methodology"""
        
        print("🤖 PHASE 2: ML FEATURE ENGINEERING & DATASET PREPARATION")
        print("=" * 80)
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"🏗️ Following .cursorrules: src/tests/analysis/")
        print(f"📊 Target: {sample_days} days × {sample_size_per_day} options = {sample_days * sample_size_per_day:,} samples")
        print(f"=" * 80)
        
        # Get available dates
        available_dates = self.loader.get_available_dates(start_date, end_date)
        selected_dates = available_dates[:sample_days]
        
        print(f"📊 Processing {len(selected_dates)} trading days...")
        
        all_features = []
        processing_stats = {
            'days_processed': 0,
            'total_options_processed': 0,
            'total_features_generated': 0,
            'feature_categories': {},
            'processing_errors': []
        }
        
        for i, date in enumerate(selected_dates, 1):
            print(f"\n📅 Day {i}/{len(selected_dates)}: {date.strftime('%Y-%m-%d')}")
            
            try:
                # Load options data for the day
                options_data = self.loader.load_options_for_date(date, min_volume=5)
                market_conditions = self.loader.analyze_market_conditions(date)
                
                if options_data.empty:
                    print(f"   ⚠️  No options data available")
                    continue
                
                spy_price = self.loader._estimate_spy_price(options_data)
                if not spy_price:
                    print(f"   ⚠️  Could not estimate SPY price")
                    continue
                
                # Sample options for processing (to manage memory/time)
                sample_size = min(sample_size_per_day, len(options_data))
                options_sample = options_data.sample(n=sample_size, random_state=42).copy()
                
                print(f"   📊 Processing {len(options_sample)} options (SPY: ${spy_price:.2f})")
                
                # Generate comprehensive ML features
                features_df = self.feature_engineer.generate_comprehensive_features(
                    options_sample, spy_price, market_conditions, debug_mode=False
                )
                
                # Add metadata
                features_df['date'] = date
                features_df['spy_price'] = spy_price
                features_df['market_regime'] = market_conditions.get('market_regime', 'NEUTRAL')
                
                all_features.append(features_df)
                
                processing_stats['days_processed'] += 1
                processing_stats['total_options_processed'] += len(options_sample)
                processing_stats['total_features_generated'] = len(features_df.columns)
                
                print(f"   ✅ Generated {len(features_df.columns)} features for {len(options_sample)} options")
                
            except Exception as e:
                error_msg = f"Day {date.strftime('%Y-%m-%d')}: {str(e)}"
                processing_stats['processing_errors'].append(error_msg)
                print(f"   ❌ Error processing day: {e}")
                continue
        
        if not all_features:
            raise ValueError("No features generated - check data availability")
        
        # Combine all features
        print(f"\n🔄 Combining features from {len(all_features)} days...")
        combined_features = pd.concat(all_features, ignore_index=True)
        
        print(f"✅ Combined dataset: {len(combined_features):,} samples × {len(combined_features.columns)} features")
        
        # Analyze feature quality
        feature_analysis = self._analyze_feature_quality(combined_features)
        
        # Create train/validation/test splits
        splits = self._create_data_splits(combined_features)
        
        # Save dataset following .cursorrules structure
        dataset_info = self._save_ml_dataset(combined_features, splits, feature_analysis, 
                                           start_date, end_date, processing_stats)
        
        return {
            'dataset_info': dataset_info,
            'feature_analysis': feature_analysis,
            'splits': splits,
            'processing_stats': processing_stats
        }
    
    def _analyze_feature_quality(self, features_df: pd.DataFrame) -> Dict:
        """Analyze feature quality and importance"""
        
        print(f"\n🔍 ANALYZING FEATURE QUALITY...")
        
        # Basic statistics
        numeric_features = features_df.select_dtypes(include=[np.number]).columns
        
        quality_analysis = {
            'total_features': len(features_df.columns),
            'numeric_features': len(numeric_features),
            'missing_data': {},
            'feature_distributions': {},
            'correlation_analysis': {},
            'feature_categories': {}
        }
        
        # Missing data analysis
        missing_pct = features_df.isnull().mean() * 100
        quality_analysis['missing_data'] = {
            'features_with_missing': len(missing_pct[missing_pct > 0]),
            'max_missing_pct': missing_pct.max(),
            'avg_missing_pct': missing_pct.mean()
        }
        
        # Feature distribution analysis
        for feature in numeric_features[:20]:  # Sample first 20 numeric features
            quality_analysis['feature_distributions'][feature] = {
                'mean': features_df[feature].mean(),
                'std': features_df[feature].std(),
                'min': features_df[feature].min(),
                'max': features_df[feature].max(),
                'unique_values': features_df[feature].nunique()
            }
        
        # Correlation analysis (sample to avoid memory issues)
        sample_features = numeric_features[:50]  # First 50 numeric features
        corr_matrix = features_df[sample_features].corr()
        
        # Find high correlations
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.8:
                    high_corr_pairs.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': corr_val
                    })
        
        quality_analysis['correlation_analysis'] = {
            'high_correlation_pairs': len(high_corr_pairs),
            'sample_pairs': high_corr_pairs[:10]
        }
        
        # Feature categories from MLFeatureEngineer
        analysis = self.feature_engineer.get_feature_importance_analysis(features_df)
        quality_analysis['feature_categories'] = analysis.get('feature_categories', {})
        
        print(f"   📊 {quality_analysis['total_features']} total features")
        print(f"   📊 {quality_analysis['missing_data']['features_with_missing']} features with missing data")
        print(f"   📊 {len(high_corr_pairs)} high correlation pairs found")
        
        return quality_analysis
    
    def _create_data_splits(self, features_df: pd.DataFrame) -> Dict:
        """Create train/validation/test splits by date"""
        
        print(f"\n📊 CREATING DATA SPLITS...")
        
        # Sort by date
        features_df_sorted = features_df.sort_values('date').copy()
        
        # Split by date (temporal split for time series)
        total_samples = len(features_df_sorted)
        train_end = int(total_samples * 0.7)
        val_end = int(total_samples * 0.85)
        
        splits = {
            'train': features_df_sorted.iloc[:train_end].copy(),
            'validation': features_df_sorted.iloc[train_end:val_end].copy(),
            'test': features_df_sorted.iloc[val_end:].copy()
        }
        
        print(f"   📊 Train: {len(splits['train']):,} samples ({len(splits['train'])/total_samples*100:.1f}%)")
        print(f"   📊 Validation: {len(splits['validation']):,} samples ({len(splits['validation'])/total_samples*100:.1f}%)")
        print(f"   📊 Test: {len(splits['test']):,} samples ({len(splits['test'])/total_samples*100:.1f}%)")
        
        return splits
    
    def _save_ml_dataset(self, features_df: pd.DataFrame, splits: Dict, 
                        feature_analysis: Dict, start_date: datetime, 
                        end_date: datetime, processing_stats: Dict) -> Dict:
        """Save ML dataset following .cursorrules structure"""
        
        print(f"\n💾 SAVING ML DATASET...")
        
        # Save in tests/analysis/ directory as per .cursorrules
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"ml_dataset_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{timestamp}"
        
        dataset_dir = os.path.join(os.path.dirname(__file__), 'ml_datasets')
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Save full dataset
        full_dataset_path = os.path.join(dataset_dir, f"{base_filename}_full.parquet")
        features_df.to_parquet(full_dataset_path, index=False)
        
        # Save splits
        split_paths = {}
        for split_name, split_data in splits.items():
            split_path = os.path.join(dataset_dir, f"{base_filename}_{split_name}.parquet")
            split_data.to_parquet(split_path, index=False)
            split_paths[split_name] = split_path
        
        # Save metadata
        metadata = {
            'creation_date': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'dataset_info': {
                'total_samples': len(features_df),
                'total_features': len(features_df.columns),
                'file_path': full_dataset_path
            },
            'splits': {
                'train': {'samples': len(splits['train']), 'path': split_paths['train']},
                'validation': {'samples': len(splits['validation']), 'path': split_paths['validation']},
                'test': {'samples': len(splits['test']), 'path': split_paths['test']}
            },
            'feature_analysis': feature_analysis,
            'processing_stats': processing_stats,
            'strategy': 'Enhanced 0DTE with Greeks - ML Dataset',
            'location': 'src/tests/analysis/ml_datasets/ (following .cursorrules)'
        }
        
        metadata_path = os.path.join(dataset_dir, f"{base_filename}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"   ✅ Full dataset: {full_dataset_path}")
        print(f"   ✅ Train/Val/Test splits: {len(split_paths)} files")
        print(f"   ✅ Metadata: {metadata_path}")
        
        return metadata

def main():
    """Run Phase 2: ML Feature Engineering following .cursorrules"""
    
    print("🚀 PHASE 2: ML FEATURE ENGINEERING & DATASET PREPARATION")
    print("🏗️ Following .cursorrules: src/tests/analysis/")
    print("=" * 80)
    
    try:
        ml_prep = MLFeaturePreparation()
        
        # Process recent period with rich data
        end_date = datetime(2025, 8, 29)
        start_date = datetime(2025, 8, 1)
        
        # Generate ML dataset
        results = ml_prep.prepare_ml_dataset(
            start_date, end_date, 
            sample_days=15,  # 15 days for comprehensive dataset
            sample_size_per_day=300  # 300 options per day = 4,500 total samples
        )
        
        print(f"\n🎯 PHASE 2 COMPLETE - READY FOR PHASE 3")
        print(f"=" * 80)
        print(f"✅ ML dataset prepared: {results['processing_stats']['total_options_processed']:,} samples")
        print(f"✅ Feature engineering complete: {results['processing_stats']['total_features_generated']} features")
        print(f"✅ Train/Val/Test splits created")
        print(f"✅ Following .cursorrules structure")
        
        print(f"\n📋 DATASET SUMMARY:")
        stats = results['processing_stats']
        print(f"   📊 Days processed: {stats['days_processed']}")
        print(f"   📊 Total samples: {stats['total_options_processed']:,}")
        print(f"   📊 Features per sample: {stats['total_features_generated']}")
        print(f"   📊 Processing errors: {len(stats['processing_errors'])}")
        
        print(f"\n📋 NEXT STEPS:")
        print(f"1. 🧠 Phase 3: Train ML models (XGBoost, Random Forest, Neural Networks)")
        print(f"2. 🔄 Phase 4: Integrate best ML model into Enhanced 0DTE Strategy")
        print(f"3. 📊 Phase 5: Compare ML-enhanced vs baseline performance")
        print(f"4. 🚀 Deploy enhanced strategy with ML signal generation")
        
    except Exception as e:
        print(f"❌ Error in ML feature preparation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
