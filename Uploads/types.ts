// FIX: Enhanced types for 0DTE options trading system
// Added new fields for momentum indicators and 0DTE-specific data

export interface MarketData {
  timestamp: Date | string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | string;
}

export interface OptionsChain {
  strike: number;
  expiration: Date | string;
  type: 'CALL' | 'PUT';
  bid: number;
  ask: number;
  impliedVolatility?: number;
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  volume?: number;
  openInterest?: number;
}

// FIX: Enhanced TechnicalIndicators with 0DTE momentum indicators
export interface TechnicalIndicators {
  rsi: number;
  macd: number;
  macdSignal: number;
  macdHistogram: number;
  bbUpper: number;
  bbMiddle: number;
  bbLower: number;
  // FIX: New momentum indicators for 0DTE
  roc?: number;           // Rate of Change
  stochK?: number;        // Stochastic %K
  stochD?: number;        // Stochastic %D
  fastRSI?: number;       // 5-period RSI for quick signals
  momentum?: number;      // 3-bar momentum
  priceVelocity?: number; // Price acceleration
  volumeRatio?: number;   // Current vs average volume
}

export interface TradeSignal {
  action: 'BUY_CALL' | 'BUY_PUT' | 'SELL_CALL' | 'SELL_PUT';
  confidence: number; // 0-100
  reason: string;
  indicators: TechnicalIndicators;
  timestamp: Date;
  // FIX: New fields for 0DTE
  timeWindow?: 'MORNING_MOMENTUM' | 'MIDDAY_CONSOLIDATION' | 'AFTERNOON_DECAY';
  expectedHoldTime?: number; // Minutes
  riskLevel?: 'LOW' | 'MEDIUM' | 'HIGH';
}

// FIX: Enhanced Strategy interface for 0DTE parameters
export interface Strategy {
  name: string;
  
  // Position sizing
  positionSizePercent: number; // Percentage of account to risk
  maxPositions: number;
  
  // Risk management - FIX: Optimized for 0DTE
  stopLossPercent: number;     // Default 30% for 0DTE
  takeProfitPercent: number;   // Default 50% for 0DTE
  maxDailyLoss: number;        // Daily loss limit
  dailyProfitTarget: number;   // Daily profit target ($200-250)
  
  // Technical indicators
  rsiPeriod: number;
  rsiOversold: number;
  rsiOverbought: number;
  macdFast: number;
  macdSlow: number;
  macdSignal: number;
  bbPeriod: number;
  bbStdDev: number;
  
  // FIX: New 0DTE specific parameters
  maxHoldingTimeMinutes: number;  // Max 240 minutes (4 hours)
  timeDecayExitMinutes: number;   // Exit before close (30 minutes)
  momentumThreshold: number;      // Minimum momentum for entry
  volumeConfirmation: number;     // Volume multiplier for confirmation
  vixFilterMax: number;          // Maximum VIX for trading (50)
  vixFilterMin: number;          // Minimum VIX for trading (10)
}

// FIX: Enhanced Position interface for 0DTE tracking
export interface Position {
  id: string;
  symbol: string;
  side: 'CALL' | 'PUT';
  strike: number;
  expiration: Date;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  entryTime: Date;
  
  // P&L tracking
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  
  // Risk metrics
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  
  // FIX: 0DTE specific fields
  is0DTE: boolean;
  timeDecayRisk: 'LOW' | 'MEDIUM' | 'HIGH';
  momentumScore: number;
  exitStrategy: 'TIME_BASED' | 'PROFIT_TARGET' | 'STOP_LOSS' | 'SIGNAL_BASED';
}

// FIX: New interface for daily trading metrics
export interface DailyMetrics {
  date: Date;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnL: number;
  maxDrawdown: number;
  maxProfit: number;
  averageHoldTime: number; // Minutes
  
  // 0DTE specific metrics
  morningTrades: number;
  afternoonTrades: number;
  momentumTrades: number;
  regimeTrades: number;
  
  // Risk metrics
  maxRiskTaken: number;
  riskAdjustedReturn: number;
  sharpeRatio: number;
}

// FIX: Account configuration for $35k account
export interface AccountConfig {
  balance: number;              // $35,000
  dailyProfitTarget: number;    // $200-250
  dailyLossLimit: number;       // -$500
  maxPositionSize: number;      // 10 contracts
  riskPerTrade: number;         // 2% of account
  
  // Trading hours
  marketOpen: number;           // 9.5 (9:30 AM)
  marketClose: number;          // 16 (4:00 PM)
  morningSessionEnd: number;    // 11 (11:00 AM)
  afternoonSessionStart: number; // 14 (2:00 PM)
}

// Export types only - no default export needed for TypeScript interfaces
