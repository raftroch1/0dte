/**
 * Unit tests for Flyagonal Strategy
 */

import { FlyagonalStrategy } from '../strategy';

describe('FlyagonalStrategy', () => {
  let strategy: FlyagonalStrategy;

  beforeEach(() => {
    strategy = new FlyagonalStrategy();
  });

  test('should initialize with default config', () => {
    expect(strategy.name).toBe('flyagonal');
    expect(strategy.version).toBe('1.0.0');
    expect(strategy.author).toBe('Steve Guns');
  });

  test('should validate configuration', () => {
    const config = strategy.getDefaultConfig();
    expect(strategy.validateConfig(config)).toBe(true);
  });

  test('should return required indicators', () => {
    const indicators = strategy.getRequiredIndicators();
    expect(Array.isArray(indicators)).toBe(true);
    expect(indicators.length).toBeGreaterThan(0);
  });

  test('should return supported timeframes', () => {
    const timeframes = strategy.getTimeframes();
    expect(Array.isArray(timeframes)).toBe(true);
    expect(timeframes).toContain('1hr');
  });

  test('should return correct risk level', () => {
    expect(strategy.getRiskLevel()).toBe('low');
  });

  // TODO: Add more comprehensive tests
  // - Signal generation with mock data
  // - Risk calculation accuracy
  // - Edge case handling
  // - Performance benchmarks
});
