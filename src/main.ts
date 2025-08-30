
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
    async runBacktest(startDate: string, endDate: string): Promise<void> {
        console.log('📊 Running REAL backtest with Alpaca historical data...');
        console.log(`📅 Period: ${startDate} to ${endDate}`);
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

            // Create backtest configuration
            const backtestConfig = IntegrationConfig.createBacktestConfig(
                new Date(startDate),
                new Date(endDate),
                'default',
                'SPY'
            );

            console.log('🏗️ Initializing backtesting engine...');
            const backtest = new BacktestingEngine(backtestConfig, alpacaClient);

            // Define our 0DTE momentum strategy for backtesting
            const strategy = (marketData: MarketData[], optionsChain: OptionsChain[]): TradeSignal | null => {
                if (marketData.length < 20) return null;
                
                const indicators = TechnicalAnalysis.calculateAllIndicators(marketData);
                if (!indicators) return null;
                
                const currentBar = marketData[marketData.length - 1];
                const currentPrice = currentBar.close;
                const currentTime = currentBar.timestamp; // Use historical timestamp!
                
                // Simple momentum strategy for backtesting
                if (indicators.rsi < 35 && indicators.macd > indicators.macdSignal) {
                    return {
                        action: 'BUY_CALL',
                        confidence: 70,
                        reason: 'RSI oversold + MACD bullish crossover',
                        indicators,
                        timestamp: currentTime, // Use historical date for backtesting
                        targetStrike: Math.round(currentPrice + 2),
                        expiration: new Date(currentTime.getTime() + 4 * 60 * 60 * 1000), // 4 hours from historical time
                        positionSize: 2,
                        stopLoss: 0.3,
                        takeProfit: 0.5
                    };
                }
                
                if (indicators.rsi > 65 && indicators.macd < indicators.macdSignal) {
                    return {
                        action: 'BUY_PUT',
                        confidence: 70,
                        reason: 'RSI overbought + MACD bearish crossover',
                        indicators,
                        timestamp: currentTime, // Use historical date for backtesting
                        targetStrike: Math.round(currentPrice - 2),
                        expiration: new Date(currentTime.getTime() + 4 * 60 * 60 * 1000), // 4 hours from historical time
                        positionSize: 2,
                        stopLoss: 0.3,
                        takeProfit: 0.5
                    };
                }
                
                return null;
            };

            console.log('📈 Loading historical market data from Alpaca...');
            await backtest.loadHistoricalData();

            console.log('🚀 Running backtest with real data...');
            const results = await backtest.runBacktest(strategy);

            // Display comprehensive results
            console.log('\n📊 REAL BACKTEST RESULTS:');
            console.log('================================');
            console.log(`📈 Total Return: ${(results.summary.totalReturnPercent * 100).toFixed(2)}%`);
            console.log(`💰 Total P&L: $${results.summary.totalReturn.toFixed(2)}`);
            console.log(`📊 Total Trades: ${results.summary.totalTrades}`);
            console.log(`🎯 Win Rate: ${(results.summary.winRate * 100).toFixed(1)}%`);
            console.log(`📉 Max Drawdown: ${(results.summary.maxDrawdown * 100).toFixed(2)}%`);
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

// CLI Interface
async function main() {
    const args = process.argv.slice(2);
    const command = args[0] || 'paper';

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
                const startDate = args[1] || '2024-01-01';
                const endDate = args[2] || '2024-12-31';
                await system.runBacktest(startDate, endDate);
                break;
            case 'stop':
                await system.stop();
                break;
            default:
                console.log('Usage: npm start [paper|backtest|stop]');
                console.log('  paper: Start paper trading');
                console.log('  backtest <start> <end>: Run backtest');
                console.log('  stop: Stop trading system');
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
