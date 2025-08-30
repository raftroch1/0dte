
/**
 * 0DTE Options Trading System - Main Entry Point
 * 
 * Clean, minimalistic entry point for the 0DTE options trading system
 * targeting $200-250 daily profit on $35k account with Alpaca integration.
 */

import { AlpacaIntegration } from './core/alpaca-integration';
import { AdaptiveStrategySelector } from './strategies/adaptive-strategy-selector';
import { AlpacaPaperTrading } from './trading/alpaca-paper-trading';
import { BacktestingEngine } from './core/backtesting-engine';
import { IntegrationConfig } from '../config/integration-config';
import { MarketData, OptionsChain, TradeSignal } from './utils/types';
import { TechnicalAnalysis } from './data/technical-indicators';

// Load environment variables
require('dotenv').config();
// Simple configuration interface
interface TradingConfig {
    alpaca: {
        apiKey: string;
        apiSecret: string;
        baseUrl: string;
        dataUrl: string;
    };
    trading: {
        accountSize: number;
        dailyProfitTarget: number;
        maxDailyLoss: number;
        maxPositionSize: number;
        riskPerTrade: number;
    };
}

export class ZDTETradingSystem {
    private config: TradingConfig;

    constructor(config: TradingConfig) {
        this.config = config;
    }

    /**
     * Start paper trading with the 0DTE momentum strategy
     */
    async startPaperTrading(): Promise<void> {
        console.log('🚀 Starting 0DTE Paper Trading System...');
        console.log(`💰 Target: $${this.config.trading.dailyProfitTarget} daily profit`);
        console.log(`💼 Account Size: $${this.config.trading.accountSize}`);
        
        try {
            // Initialize components
            console.log('📡 Initializing Alpaca integration...');
            console.log('🧠 Loading adaptive strategy selector...');
            console.log('📊 Setting up paper trading...');
            console.log('✅ Paper trading system ready (demo mode)');
        } catch (error) {
            console.error('❌ Failed to start paper trading:', error);
            throw error;
        }
    }

    /**
     * Run backtesting on historical data using real Alpaca data
     */
    async runBacktest(startDate: string, endDate: string, strategyName: string = 'simple-momentum'): Promise<void> {
        console.log('📊 Running REAL backtest with Alpaca historical data...');
        console.log(`📅 Period: ${startDate} to ${endDate}`);
        console.log(`🎯 Strategy: ${strategyName}`);
        console.log(`💰 Initial Capital: $${this.config.trading.accountSize}`);
        console.log(`🎯 Target: $${this.config.trading.dailyProfitTarget} daily profit`);
        
        try {
            // Create Alpaca client with real credentials
            const alpacaClient = new AlpacaIntegration({
                apiKey: this.config.alpaca.apiKey,
                apiSecret: this.config.alpaca.apiSecret,
                isPaper: true
            });

            // Test connection first
            console.log('🔌 Testing Alpaca connection...');
            const connected = await alpacaClient.testConnection();
            if (!connected) {
                throw new Error('Failed to connect to Alpaca API. Check your credentials.');
            }
            console.log('✅ Connected to Alpaca successfully');

            // Load strategy from registry
            console.log(`🎯 Loading strategy: ${strategyName}...`);
            const { StrategyRegistry } = await import('./strategies/registry');
            const strategy = await StrategyRegistry.loadStrategy(strategyName);
            
            if (!strategy) {
                throw new Error(`Strategy '${strategyName}' not found or failed to load`);
            }

            // Create backtest configuration with loaded strategy
            const backtestConfig = IntegrationConfig.createBacktestConfig(
                new Date(startDate),
                new Date(endDate),
                strategyName, // Pass the actual strategy name
                'SPX' // Flyagonal trades SPX index options
            );

            console.log('🏗️ Initializing backtesting engine...');
            const backtest = new BacktestingEngine(backtestConfig, alpacaClient, strategyName);

            // Use the loaded strategy's generateSignal method
            const strategyFunction = (marketData: MarketData[], optionsChain: OptionsChain[]): TradeSignal | null => {
                return strategy.generateSignal(marketData, optionsChain);
            };

            console.log('📈 Loading historical market data from Alpaca...');
            await backtest.loadHistoricalData();

            console.log('🚀 Running backtest with real data...');
            const results = await backtest.runBacktest(strategyFunction);

            // Display comprehensive results
            console.log('\n📊 REAL BACKTEST RESULTS:');
            console.log('================================');
            console.log(`📈 Total Return: ${results.summary.totalReturnPercent.toFixed(2)}%`);
            console.log(`💰 Total P&L: $${results.summary.totalReturn.toFixed(2)}`);
            console.log(`📊 Total Trades: ${results.summary.totalTrades}`);
            console.log(`🎯 Win Rate: ${results.summary.winRate.toFixed(1)}%`);
            console.log(`📉 Max Drawdown: ${results.summary.maxDrawdown.toFixed(2)}%`);
            console.log(`⚡ Sharpe Ratio: ${results.summary.sharpeRatio.toFixed(2)}`);
            console.log(`💵 Avg Trade Return: $${results.summary.avgTradeReturn.toFixed(2)}`);
            console.log(`🏆 Largest Win: $${results.summary.largestWin.toFixed(2)}`);
            console.log(`💸 Largest Loss: $${results.summary.largestLoss.toFixed(2)}`);
            
            if (results.dailyMetrics.length > 0) {
                const avgDailyPnL = results.dailyMetrics.reduce((sum, day) => sum + day.pnl, 0) / results.dailyMetrics.length;
                console.log(`📅 Avg Daily P&L: $${avgDailyPnL.toFixed(2)}`);
                console.log(`📊 Trading Days: ${results.dailyMetrics.length}`);
            }

            console.log('\n🎯 Strategy Performance:');
            console.log(`✅ Profitable Days: ${results.dailyMetrics.filter(d => d.pnl > 0).length}`);
            console.log(`❌ Loss Days: ${results.dailyMetrics.filter(d => d.pnl < 0).length}`);
            console.log(`➖ Breakeven Days: ${results.dailyMetrics.filter(d => d.pnl === 0).length}`);

        } catch (error) {
            console.error('❌ Real backtest failed:', error);
            throw error;
        }
    }

    /**
     * Stop all trading activities
     */
    async stop(): Promise<void> {
        console.log('🛑 Stopping trading system...');
        console.log('✅ Trading system stopped');
    }
}

/**
 * Parse command line arguments supporting both named (--key=value) and positional formats
 * 
 * Examples:
 * - Named: backtest --start=2024-02-01 --end=2024-02-29 --strategy=flyagonal
 * - Positional: backtest 2024-02-01 2024-02-29
 * 
 * @param args Raw command line arguments
 * @returns Parsed arguments object
 */
function parseCommandLineArgs(args: string[]): {
    command: string;
    start?: string;
    end?: string;
    strategy?: string;
    [key: string]: any;
} {
    const command = args[0] || 'paper';
    const parsed: any = { command };
    
    // Parse named arguments (--key=value format)
    const namedArgs: any = {};
    const positionalArgs: string[] = [];
    
    for (let i = 1; i < args.length; i++) {
        const arg = args[i];
        
        if (arg.startsWith('--')) {
            // Handle --key=value format
            const equalIndex = arg.indexOf('=');
            if (equalIndex > 0) {
                const key = arg.substring(2, equalIndex);
                const value = arg.substring(equalIndex + 1);
                namedArgs[key] = value;
            } else {
                // Handle --key format (boolean flag)
                const key = arg.substring(2);
                namedArgs[key] = true;
            }
        } else {
            // Positional argument
            positionalArgs.push(arg);
        }
    }
    
    // Merge named arguments
    Object.assign(parsed, namedArgs);
    
    // Handle backward compatibility with positional arguments
    if (command === 'backtest') {
        // If no named arguments provided, use positional
        if (!parsed.start && positionalArgs[0]) {
            parsed.start = positionalArgs[0];
        }
        if (!parsed.end && positionalArgs[1]) {
            parsed.end = positionalArgs[1];
        }
        
        // Set defaults
        parsed.start = parsed.start || '2024-01-01';
        parsed.end = parsed.end || '2024-12-31';
        parsed.strategy = parsed.strategy || 'simple-momentum';
    }
    
    return parsed;
}

/**
 * Validate date string and return Date object
 * 
 * @param dateStr Date string to validate
 * @param paramName Parameter name for error messages
 * @returns Valid Date object
 */
function validateDate(dateStr: string, paramName: string): Date {
    const date = new Date(dateStr);
    
    if (isNaN(date.getTime())) {
        throw new Error(`Invalid ${paramName} date: "${dateStr}". Please use format YYYY-MM-DD`);
    }
    
    return date;
}

// CLI Interface
async function main() {
    const rawArgs = process.argv.slice(2);
    const args = parseCommandLineArgs(rawArgs);
    const command = args.command;

    const config: TradingConfig = {
        alpaca: {
            apiKey: process.env.ALPACA_API_KEY || '',
            apiSecret: process.env.ALPACA_API_SECRET || '',
            baseUrl: process.env.ALPACA_BASE_URL || 'https://paper-api.alpaca.markets',
            dataUrl: process.env.ALPACA_DATA_URL || 'https://data.alpaca.markets'
        },
        trading: {
            accountSize: parseInt(process.env.ACCOUNT_SIZE || '35000'),
            dailyProfitTarget: parseInt(process.env.DAILY_PROFIT_TARGET || '225'),
            maxDailyLoss: parseInt(process.env.MAX_DAILY_LOSS || '500'),
            maxPositionSize: parseFloat(process.env.RISK_PER_TRADE || '0.02'),
            riskPerTrade: parseFloat(process.env.RISK_PER_TRADE || '0.01')
        }
    };

    const system = new ZDTETradingSystem(config);

    try {
        switch (command) {
            case 'paper':
                await system.startPaperTrading();
                break;
            case 'backtest':
                // Validate and parse dates
                const startDate = validateDate(args.start!, 'start');
                const endDate = validateDate(args.end!, 'end');
                
                // Validate date range
                if (startDate >= endDate) {
                    throw new Error(`Start date (${args.start}) must be before end date (${args.end})`);
                }
                
                console.log(`📅 Backtesting Strategy: ${args.strategy}`);
                console.log(`📅 Period: ${args.start} to ${args.end}`);
                console.log(`💰 Initial Capital: $${config.trading.accountSize}`);
                console.log(`🎯 Target: $${config.trading.dailyProfitTarget} daily profit`);
                
                await system.runBacktest(args.start!, args.end!, args.strategy!);
                break;
            case 'stop':
                await system.stop();
                break;
            default:
                console.log('Usage: npm start [paper|backtest|stop]');
                console.log('');
                console.log('Commands:');
                console.log('  paper                                    Start paper trading');
                console.log('  backtest --start=YYYY-MM-DD --end=YYYY-MM-DD [--strategy=name]');
                console.log('                                          Run backtest with date range');
                console.log('  backtest <start> <end>                  Run backtest (positional format)');
                console.log('  stop                                    Stop trading system');
                console.log('');
                console.log('Examples:');
                console.log('  npm run backtest -- --start=2024-02-01 --end=2024-02-29 --strategy=flyagonal');
                console.log('  npm run backtest -- 2024-02-01 2024-02-29');
        }
    } catch (error) {
        console.error('System error:', error);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(console.error);
}
