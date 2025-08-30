/**
 * 🎯 {{STRATEGY_NAME}} Strategy - Main Export
 * ==========================================
 * 
 * Entry point for the {{STRATEGY_NAME}} trading strategy.
 * This file exports the strategy class and related components.
 * 
 * @fileoverview Main export for {{STRATEGY_NAME}} strategy
 * @author {{AUTHOR_NAME}}
 * @version {{VERSION}}
 * @created {{DATE}}
 */

// Export the main strategy class
export { {{STRATEGY_CLASS_NAME}} } from './strategy';

// Export strategy-specific types
export type { {{STRATEGY_CLASS_NAME}}Config, {{STRATEGY_CLASS_NAME}}Parameters } from './types';

// Export default configuration
export { default as defaultConfig } from './config';

// Export the strategy class as default for dynamic imports
export { {{STRATEGY_CLASS_NAME}} as default } from './strategy';
