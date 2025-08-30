/**
 * 🎯 Flyagonal Strategy - Main Export
 * ==========================================
 * 
 * Entry point for the Flyagonal trading strategy.
 * This file exports the strategy class and related components.
 * 
 * @fileoverview Main export for Flyagonal strategy
 * @author Steve Guns
 * @version 1.0.0
 * @created 2025-08-30
 */

// Export the main strategy class
export { FlyagonalStrategy } from './strategy';

// Export strategy-specific types
export type { FlyagonalStrategyConfig, FlyagonalStrategyParameters } from './types';

// Export default configuration
export { default as defaultConfig } from './config';

// Export the strategy class as default for dynamic imports
export { FlyagonalStrategy as default } from './strategy';
