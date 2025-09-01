#!/usr/bin/env python3
"""
Test Reorganized Project Structure
=================================

Tests that all imports work correctly after reorganization.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_data_imports():
    """Test data module imports"""
    print("🔄 Testing data module imports...")
    
    try:
        from src.data.parquet_data_loader import ParquetDataLoader
        print("✅ ParquetDataLoader import successful")
        
        from src.data.ml_feature_engineering import MLFeatureEngineer
        print("✅ MLFeatureEngineer import successful")
        
        # Test initialization
        loader = ParquetDataLoader()
        engineer = MLFeatureEngineer()
        print("✅ Data module initialization successful")
        
        return True
    except Exception as e:
        print(f"❌ Data module import failed: {e}")
        return False

def test_strategy_imports():
    """Test strategy module imports"""
    print("\n🔄 Testing strategy module imports...")
    
    try:
        from src.strategies.enhanced_0dte.strategy import Enhanced0DTEStrategy, Enhanced0DTEBacktester
        print("✅ Enhanced 0DTE strategy import successful")
        
        # Test initialization
        strategy = Enhanced0DTEStrategy()
        print("✅ Enhanced 0DTE strategy initialization successful")
        
        return True
    except Exception as e:
        print(f"❌ Strategy module import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_package_imports():
    """Test package-level imports"""
    print("\n🔄 Testing package-level imports...")
    
    try:
        from src.data import ParquetDataLoader, MLFeatureEngineer
        print("✅ Package-level data imports successful")
        
        from src.strategies.enhanced_0dte import Enhanced0DTEStrategy
        print("✅ Package-level strategy imports successful")
        
        return True
    except Exception as e:
        print(f"❌ Package-level imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 TESTING REORGANIZED PROJECT STRUCTURE")
    print("=" * 60)
    
    tests = [
        test_data_imports,
        test_strategy_imports, 
        test_package_imports
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    if passed == total:
        print("🎉 All imports working correctly!")
        print("✅ Project reorganization successful")
        print("✅ Following .cursorrules structure")
    else:
        print("❌ Some imports still need fixing")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
