#!/usr/bin/env node

/**
 * 🏗️ Strategy Generator Script
 * ===========================
 * 
 * This script creates a new trading strategy from the template,
 * replacing placeholders with user-provided values.
 * 
 * Usage:
 *   node scripts/create-strategy.js
 *   
 * The script will prompt for all required information and generate
 * a complete strategy module following the project's architecture.
 * 
 * @fileoverview Strategy generation script
 * @author 0DTE Trading System
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Utility function to prompt user for input
function prompt(question, defaultValue = '') {
  return new Promise((resolve) => {
    const displayDefault = defaultValue ? ` (${defaultValue})` : '';
    rl.question(`${question}${displayDefault}: `, (answer) => {
      resolve(answer.trim() || defaultValue);
    });
  });
}

// Utility function to convert string to different cases
function toCases(str) {
  const kebabCase = str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const pascalCase = str.replace(/[^a-zA-Z0-9]+(.)/g, (_, char) => char.toUpperCase()).replace(/^(.)/, char => char.toUpperCase());
  const camelCase = pascalCase.charAt(0).toLowerCase() + pascalCase.slice(1);
  
  return { kebabCase, pascalCase, camelCase };
}

// Main strategy generation function
async function generateStrategy() {
  console.log('🎯 0DTE Trading Strategy Generator');
  console.log('==================================\n');
  
  try {
    // Collect strategy information
    const strategyName = await prompt('Strategy name (e.g., "RSI Momentum Strategy")');
    if (!strategyName) {
      console.error('❌ Strategy name is required');
      process.exit(1);
    }

    const cases = toCases(strategyName);
    const strategyId = cases.kebabCase;
    const strategyClass = cases.pascalCase + 'Strategy';

    console.log(`\n📝 Generated identifiers:`);
    console.log(`   Directory: ${strategyId}`);
    console.log(`   Class: ${strategyClass}`);
    console.log(`   ID: ${strategyId}\n`);

    const description = await prompt('Strategy description', `A ${strategyName.toLowerCase()} trading strategy for 0DTE options`);
    const author = await prompt('Author name', 'Trading System Developer');
    const version = await prompt('Version', '1.0.0');
    const strategyType = await prompt('Strategy type (MOMENTUM/MEAN_REVERSION/BREAKOUT/SCALPING/SWING)', 'MOMENTUM');
    const riskLevel = await prompt('Risk level (LOW/MEDIUM/HIGH)', 'MEDIUM');
    const timeframe = await prompt('Primary timeframe (1Min/5Min/15Min)', '1Min');
    const minAccountSize = await prompt('Minimum account size', '25000');

    // Market conditions
    console.log('\n📊 Market conditions (comma-separated):');
    const marketConditions = await prompt('Market conditions', 'TRENDING,VOLATILE');

    // Indicators
    console.log('\n📈 Technical indicators (comma-separated):');
    const indicators = await prompt('Required indicators', 'RSI,MACD,BB');

    // Create strategy directory
    const strategyDir = path.join('src', 'strategies', strategyId);
    
    if (fs.existsSync(strategyDir)) {
      console.error(`❌ Strategy directory already exists: ${strategyDir}`);
      process.exit(1);
    }

    console.log(`\n🏗️ Creating strategy directory: ${strategyDir}`);
    fs.mkdirSync(strategyDir, { recursive: true });
    fs.mkdirSync(path.join(strategyDir, 'tests'), { recursive: true });

    // Template replacements
    const replacements = {
      '{{STRATEGY_NAME}}': strategyName,
      '{{STRATEGY_ID}}': strategyId,
      '{{STRATEGY_CLASS_NAME}}': strategyClass,
      '{{STRATEGY_DESCRIPTION}}': description,
      '{{AUTHOR_NAME}}': author,
      '{{VERSION}}': version,
      '{{DATE}}': new Date().toISOString().split('T')[0],
      '{{STRATEGY_TYPE}}': strategyType,
      '{{RISK_LEVEL}}': riskLevel,
      '{{TIMEFRAME}}': timeframe,
      '{{MIN_ACCOUNT_SIZE}}': minAccountSize,
      '{{MARKET_CONDITIONS}}': marketConditions,
      '{{MIN_DATA_POINTS}}': '20',
      
      // Indicators
      '{{INDICATOR_1}}': indicators.split(',')[0]?.trim() || 'RSI',
      '{{INDICATOR_2}}': indicators.split(',')[1]?.trim() || 'MACD',
      '{{INDICATOR_3}}': indicators.split(',')[2]?.trim() || 'BB',
      
      // Timeframes
      '{{TIMEFRAME_1}}': timeframe,
      '{{TIMEFRAME_2}}': timeframe === '1Min' ? '5Min' : '1Min',
      
      // Placeholder content for README
      '{{STRATEGY_FOCUS}}': 'short-term momentum opportunities',
      '{{MAIN_INDICATORS}}': indicators.toLowerCase(),
      '{{COMPLEXITY_LEVEL}}': 'INTERMEDIATE',
      '{{CALL_CONDITION_1}}': 'RSI indicates oversold conditions (< 30)',
      '{{CALL_CONDITION_2}}': 'MACD shows bullish crossover',
      '{{CALL_CONDITION_3}}': 'Price is above short-term moving average',
      '{{PUT_CONDITION_1}}': 'RSI indicates overbought conditions (> 70)',
      '{{PUT_CONDITION_2}}': 'MACD shows bearish crossover',
      '{{PUT_CONDITION_3}}': 'Price is below short-term moving average',
      '{{TAKE_PROFIT_CONDITION}}': '100% gain on premium',
      '{{STOP_LOSS_CONDITION}}': '50% loss on premium',
      '{{TIME_EXIT_CONDITION}}': '30 minutes before expiration',
      '{{POSITION_SIZING_LOGIC}}': '2% of account per trade',
      '{{MAX_RISK_PER_TRADE}}': '2% of account',
      '{{DAILY_LOSS_LIMIT}}': '$500',
      
      // Default parameter values
      '{{PARAM_1}}': 'rsiPeriod',
      '{{DEFAULT_1}}': '14',
      '{{RANGE_1}}': '5-50',
      '{{DESCRIPTION_1}}': 'RSI calculation period',
      '{{PARAM_2}}': 'macdFast',
      '{{DEFAULT_2}}': '12',
      '{{RANGE_2}}': '5-20',
      '{{DESCRIPTION_2}}': 'MACD fast EMA period',
      '{{PARAM_3}}': 'macdSlow',
      '{{DEFAULT_3}}': '26',
      '{{RANGE_3}}': '20-50',
      '{{DESCRIPTION_3}}': 'MACD slow EMA period',
      
      // Performance metrics placeholders
      '{{BACKTEST_PERIOD}}': 'January 2024',
      '{{TOTAL_RETURN}}': '+15.2',
      '{{RETURN_NOTES}}': 'Based on $25k account',
      '{{WIN_RATE}}': '58.3',
      '{{WIN_RATE_NOTES}}': '35 wins out of 60 trades',
      '{{AVG_TRADE}}': '+42.50',
      '{{AVG_TRADE_NOTES}}': 'Including commissions',
      '{{MAX_DRAWDOWN}}': '-8.7',
      '{{DRAWDOWN_NOTES}}': 'Maximum peak-to-trough loss',
      '{{SHARPE_RATIO}}': '1.34',
      '{{SHARPE_NOTES}}': 'Risk-adjusted return metric',
      '{{PROFIT_FACTOR}}': '1.45',
      '{{PROFIT_FACTOR_NOTES}}': 'Gross profit / Gross loss',
      
      // Market context
      '{{BEST_CONDITION_1}}': 'Trending markets with clear direction',
      '{{CONDITION_1_EXPLANATION}}': 'Strategy works best when markets show sustained momentum',
      '{{BEST_CONDITION_2}}': 'Moderate volatility (VIX 15-25)',
      '{{CONDITION_2_EXPLANATION}}': 'Provides enough movement without excessive noise',
      '{{BEST_CONDITION_3}}': 'High volume periods',
      '{{CONDITION_3_EXPLANATION}}': 'Ensures good option liquidity and tight spreads',
      
      '{{AVOID_CONDITION_1}}': 'Major news events or earnings',
      '{{AVOID_1_EXPLANATION}}': 'Can cause unpredictable price movements',
      '{{AVOID_CONDITION_2}}': 'Very low volatility (VIX < 12)',
      '{{AVOID_2_EXPLANATION}}': 'Insufficient price movement for profitable trades',
      '{{AVOID_CONDITION_3}}': 'Market holidays or low volume periods',
      '{{AVOID_3_EXPLANATION}}': 'Poor liquidity can lead to wide spreads',
      
      '{{BEST_HOURS}}': '10:00 AM - 3:00 PM',
      '{{TIMEZONE}}': 'EST',
      '{{AVOID_HOURS}}': '3:30 PM - 4:00 PM',
      '{{MARKET_OPEN_STRATEGY}}': 'Wait for initial volatility to settle',
      '{{MARKET_CLOSE_STRATEGY}}': 'Close all positions 30 minutes before expiration',
      
      // Risk warnings
      '{{RISK_1}}': 'Rapid time decay in final hours',
      '{{RISK_1_EXPLANATION}}': '0DTE options lose value quickly as expiration approaches',
      '{{RISK_2}}': 'High sensitivity to market volatility',
      '{{RISK_2_EXPLANATION}}': 'Small price movements can cause large percentage changes',
      '{{RISK_3}}': 'Potential for total loss',
      '{{RISK_3_EXPLANATION}}': 'Options can expire worthless if not in-the-money',
      
      // Features and improvements
      '{{FEATURE_1}}': 'Real-time signal generation',
      '{{FEATURE_2}}': 'Adaptive risk management',
      '{{FEATURE_3}}': 'Multi-timeframe analysis',
      '{{IMPROVEMENT_1}}': 'Add machine learning signal filtering',
      '{{IMPROVEMENT_2}}': 'Implement dynamic position sizing',
      '{{IMPROVEMENT_3}}': 'Add market regime detection',
      
      // Signal reasons
      '{{BULLISH_SIGNAL_REASON}}': 'RSI oversold + MACD bullish crossover',
      '{{BEARISH_SIGNAL_REASON}}': 'RSI overbought + MACD bearish crossover',
    };

    // Copy and process template files
    const templateDir = path.join('templates', 'strategy-template');
    const templateFiles = [
      'index.ts',
      'strategy.ts',
      'types.ts',
      'config.ts',
      'README.md'
    ];

    console.log('\n📄 Generating strategy files:');
    
    for (const file of templateFiles) {
      const templatePath = path.join(templateDir, file);
      const targetPath = path.join(strategyDir, file);
      
      console.log(`   Creating ${file}...`);
      
      let content = fs.readFileSync(templatePath, 'utf8');
      
      // Replace all placeholders
      for (const [placeholder, value] of Object.entries(replacements)) {
        content = content.replace(new RegExp(placeholder, 'g'), value);
      }
      
      fs.writeFileSync(targetPath, content);
    }

    // Create basic test file
    console.log('   Creating test files...');
    const testContent = `/**
 * Unit tests for ${strategyName} Strategy
 */

import { ${strategyClass} } from '../strategy';

describe('${strategyClass}', () => {
  let strategy: ${strategyClass};

  beforeEach(() => {
    strategy = new ${strategyClass}();
  });

  test('should initialize with default config', () => {
    expect(strategy.name).toBe('${strategyId}');
    expect(strategy.version).toBe('${version}');
    expect(strategy.author).toBe('${author}');
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
    expect(timeframes).toContain('${timeframe}');
  });

  test('should return correct risk level', () => {
    expect(strategy.getRiskLevel()).toBe('${riskLevel}');
  });

  // TODO: Add more comprehensive tests
  // - Signal generation with mock data
  // - Risk calculation accuracy
  // - Edge case handling
  // - Performance benchmarks
});
`;

    fs.writeFileSync(path.join(strategyDir, 'tests', 'unit.test.ts'), testContent);

    // Update strategy registry
    console.log('\n📝 Updating strategy registry...');
    
    const registryPath = path.join('src', 'strategies', 'registry.ts');
    let registryContent = fs.readFileSync(registryPath, 'utf8');
    
    // Add to STRATEGY_REGISTRY
    const registryEntry = `  '${strategyId}': () => import('./${strategyId}'),`;
    registryContent = registryContent.replace(
      /(\s+\/\/ New modular strategies \(add new ones here\))/,
      `$1\n${registryEntry}`
    );
    
    // Add to STRATEGY_METADATA
    const metadataEntry = `  '${strategyId}': {
    category: '${strategyType}',
    marketConditions: [${marketConditions.split(',').map(c => `'${c.trim()}'`).join(', ')}],
    minAccountSize: ${minAccountSize},
    complexity: 'INTERMEDIATE',
    status: 'EXPERIMENTAL',
    lastUpdated: new Date('${new Date().toISOString().split('T')[0]}'),
  },`;
    
    registryContent = registryContent.replace(
      /(export const STRATEGY_METADATA[^}]+)(};)/s,
      `$1\n${metadataEntry}\n$2`
    );
    
    fs.writeFileSync(registryPath, registryContent);

    // Success message
    console.log('\n🎉 Strategy created successfully!');
    console.log('================================\n');
    console.log(`📁 Strategy location: ${strategyDir}`);
    console.log(`🆔 Strategy ID: ${strategyId}`);
    console.log(`📝 Class name: ${strategyClass}`);
    console.log('\n📋 Next steps:');
    console.log('1. Review and customize the generated strategy logic');
    console.log('2. Implement your specific trading algorithm');
    console.log('3. Add comprehensive tests');
    console.log('4. Run backtests to validate performance');
    console.log('5. Update documentation as needed');
    console.log('\n🧪 Testing:');
    console.log(`   npm test src/strategies/${strategyId}/`);
    console.log('\n📊 Backtesting:');
    console.log(`   npm run backtest -- --strategy=${strategyId} --start=2024-01-01 --end=2024-01-31`);
    console.log('\n📚 Documentation:');
    console.log(`   Open ${strategyDir}/README.md for detailed information`);

  } catch (error) {
    console.error('\n❌ Error generating strategy:', error.message);
    process.exit(1);
  } finally {
    rl.close();
  }
}

// Run the generator
if (require.main === module) {
  generateStrategy();
}

module.exports = { generateStrategy };
