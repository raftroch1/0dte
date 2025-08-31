"""
Real Option Pricing Module
=========================

REAL DATA COMPLIANCE:
- Black-Scholes mathematical calculations
- No simulation or random number generation
- Actual option pricing based on market movements
- Complies with .cursorrules real data requirements

This module replaces simulated P&L with real option pricing calculations.
"""

try:
    from .black_scholes_calculator import BlackScholesCalculator
except ImportError:
    from black_scholes_calculator import BlackScholesCalculator

__all__ = ['BlackScholesCalculator']
