
// Enhanced types for comprehensive Alpaca integration
export * from './types';

// Alpaca-specific types
export interface AlpacaCredentials {
  apiKey: string;
  apiSecret: string;
  baseUrl?: string;
  dataUrl?: string;
  streamUrl?: string;
  isPaper?: boolean;
}

export interface AlpacaAccount {
  id: string;
  account_number: string;
  status: string;
  currency: string;
  buying_power: string;
  regt_buying_power: string;
  daytrading_buying_power: string;
  cash: string;
  portfolio_value: string;
  pattern_day_trader: boolean;
  trading_blocked: boolean;
  transfers_blocked: boolean;
  account_blocked: boolean;
  created_at: string;
  trade_suspended_by_user: boolean;
  multiplier: string;
  shorting_enabled: boolean;
  equity: string;
  last_equity: string;
  long_market_value: string;
  short_market_value: string;
  initial_margin: string;
  maintenance_margin: string;
  last_maintenance_margin: string;
  sma: string;
  daytrade_count: number;
}

export interface AlpacaOrder {
  id: string;
  client_order_id: string;
  created_at: string;
  updated_at: string;
  submitted_at: string;
  filled_at?: string;
  expired_at?: string;
  canceled_at?: string;
  failed_at?: string;
  replaced_at?: string;
  replaced_by?: string;
  replaces?: string;
  asset_id: string;
  symbol: string;
  asset_class: string;
  notional?: string;
  qty?: string;
  filled_qty: string;
  filled_avg_price?: string;
  order_class: string;
  order_type: string;
  type: string;
  side: string;
  time_in_force: string;
  limit_price?: string;
  stop_price?: string;
  status: string;
  extended_hours: boolean;
  legs?: AlpacaOrder[];
  trail_percent?: string;
  trail_price?: string;
  hwm?: string;
}

export interface AlpacaPosition {
  asset_id: string;
  symbol: string;
  exchange: string;
  asset_class: string;
  avg_entry_price: string;
  qty: string;
  side: string;
  market_value: string;
  cost_basis: string;
  unrealized_pl: string;
  unrealized_plpc: string;
  unrealized_intraday_pl: string;
  unrealized_intraday_plpc: string;
  current_price: string;
  lastday_price: string;
  change_today: string;
  swap_rate?: string;
  avg_entry_swap_rate?: string;
  usd?: string;
  qty_available: string;
}

// Enhanced Greeks and Options types
export interface EnhancedGreeks {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
  lambda?: number; // Leverage
  epsilon?: number; // Dividend sensitivity
  vanna?: number; // Delta sensitivity to volatility
  charm?: number; // Delta decay
  vomma?: number; // Vega sensitivity to volatility
  vera?: number; // Rho sensitivity to volatility
}

export interface OptionPricing {
  theoreticalPrice: number;
  intrinsicValue: number;
  timeValue: number;
  impliedVolatility: number;
  greeks: EnhancedGreeks;
  moneyness: 'ITM' | 'ATM' | 'OTM';
  probabilityITM: number;
  breakeven: number;
  timeDecayRate: number; // Per minute
  gammaRisk: number; // 0-100 scale
}

// Enhanced Market Data types
export interface EnhancedMarketData extends MarketData {
  vwap?: number; // Volume weighted average price
  tradeCount?: number;
  spread?: number; // Bid-ask spread
  spreadPercent?: number;
  volatility?: number; // Realized volatility
  momentum?: number;
  rsi?: number;
  macd?: number;
  bollingerBands?: {
    upper: number;
    middle: number;
    lower: number;
  };
}

export interface OptionsSnapshot {
  underlying: string;
  underlyingPrice: number;
  timestamp: Date;
  impliedVolatility: number;
  historicalVolatility: number;
  vix?: number;
  chain: OptionsChain[];
  atmStrike: number;
  totalVolume: number;
  totalOpenInterest: number;
  putCallRatio: number;
  maxPain: number; // Max pain strike
  gammaExposure: number;
  deltaExposure: number;
}

// Enhanced Trading types
export interface EnhancedTradeSignal extends TradeSignal {
  strategy: string;
  marketRegime: string;
  volatilityEnvironment: 'LOW' | 'MEDIUM' | 'HIGH';
  timeOfDay: 'MORNING' | 'MIDDAY' | 'AFTERNOON' | 'CLOSE';
  expectedProfitTarget: number;
  expectedStopLoss: number;
  expectedHoldTime: number; // minutes
  riskRewardRatio: number;
  probabilityOfSuccess: number;
  maxRisk: number;
  greeksExposure: EnhancedGreeks;
  marketConditions: {
    trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    volatility: 'EXPANDING' | 'CONTRACTING' | 'STABLE';
    volume: 'HIGH' | 'NORMAL' | 'LOW';
    momentum: 'STRONG' | 'WEAK' | 'NEUTRAL';
  };
}

export interface EnhancedPosition extends Position {
  alpacaPositionId?: string;
  orderIds: string[];
  fills: TradeFill[];
  currentGreeks: EnhancedGreeks;
  pricing: OptionPricing;
  riskMetrics: {
    maxLoss: number;
    maxGain: number;
    breakeven: number;
    probabilityProfit: number;
    expectedValue: number;
    sharpeRatio: number;
  };
  timeMetrics: {
    daysToExpiration: number;
    hoursToExpiration: number;
    minutesToExpiration: number;
    timeDecayPerDay: number;
    timeDecayPerHour: number;
    timeDecayPerMinute: number;
  };
  alerts: PositionAlert[];
}

export interface TradeFill {
  id: string;
  timestamp: Date;
  price: number;
  quantity: number;
  side: 'BUY' | 'SELL';
  commission: number;
  fees: number;
  exchange: string;
  executionId: string;
}

export interface PositionAlert {
  id: string;
  type: 'PROFIT_TARGET' | 'STOP_LOSS' | 'TIME_DECAY' | 'GAMMA_RISK' | 'VOLATILITY_CHANGE';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  timestamp: Date;
  triggered: boolean;
  threshold: number;
  currentValue: number;
}

// Enhanced Strategy types
export interface EnhancedStrategy extends Strategy {
  id: string;
  version: string;
  description: string;
  author: string;
  created: Date;
  lastModified: Date;
  
  // Market conditions
  preferredMarketRegimes: string[];
  volatilityRange: { min: number; max: number };
  timeOfDayPreferences: string[];
  
  // Advanced parameters
  dynamicSizing: boolean;
  adaptiveStops: boolean;
  volatilityAdjustment: boolean;
  regimeAwareness: boolean;
  
  // Greeks management
  deltaTarget?: number;
  gammaLimit?: number;
  thetaTarget?: number;
  vegaLimit?: number;
  
  // Performance tracking
  backtestResults?: BacktestSummary;
  livePerformance?: LivePerformanceMetrics;
  
  // Risk parameters
  maxCorrelatedPositions: number;
  sectorConcentrationLimit: number;
  volatilityScaling: boolean;
  drawdownLimit: number;
}

export interface BacktestSummary {
  period: { start: Date; end: Date };
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  avgHoldTime: number;
  bestTrade: number;
  worstTrade: number;
}

export interface LivePerformanceMetrics {
  startDate: Date;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  totalPnL: number;
  unrealizedPnL: number;
  maxDrawdown: number;
  currentDrawdown: number;
  avgWin: number;
  avgLoss: number;
  largestWin: number;
  largestLoss: number;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  calmarRatio: number;
  lastUpdated: Date;
}

// Enhanced Account and Risk types
export interface EnhancedAccountConfig extends AccountConfig {
  riskModel: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE';
  correlationLimit: number;
  sectorLimits: { [sector: string]: number };
  volatilityScaling: boolean;
  dynamicSizing: boolean;
  
  // Time-based limits
  morningRiskLimit: number;
  afternoonRiskLimit: number;
  closeRiskLimit: number;
  
  // Greeks limits
  portfolioDeltaLimit: number;
  portfolioGammaLimit: number;
  portfolioThetaTarget: number;
  portfolioVegaLimit: number;
  
  // Advanced risk controls
  correlationMatrix: { [symbol: string]: { [symbol: string]: number } };
  stressTestScenarios: StressTestScenario[];
  riskBudget: RiskBudget;
}

export interface StressTestScenario {
  name: string;
  description: string;
  marketMove: number; // Percentage move
  volatilityChange: number; // Volatility shift
  timeDecay: number; // Days forward
  expectedPnL: number;
  worstCasePnL: number;
}

export interface RiskBudget {
  dailyVaR: number; // Value at Risk
  weeklyVaR: number;
  monthlyVaR: number;
  maxLeverage: number;
  concentrationLimit: number;
  correlationLimit: number;
  liquidityRequirement: number;
}

// Enhanced Daily Metrics
export interface EnhancedDailyMetrics extends DailyMetrics {
  volatilityRegime: 'LOW' | 'MEDIUM' | 'HIGH';
  marketRegime: string;
  vixLevel: number;
  underlyingMove: number;
  impliedVolatilityChange: number;
  
  // Greeks P&L attribution
  deltaPnL: number;
  gammaPnL: number;
  thetaPnL: number;
  vegaPnL: number;
  rhoPnL: number;
  
  // Strategy breakdown
  strategyPnL: { [strategy: string]: number };
  timeOfDayPnL: { [timeWindow: string]: number };
  
  // Risk metrics
  portfolioVaR: number;
  maxIntradayDrawdown: number;
  correlationRisk: number;
  concentrationRisk: number;
  
  // Execution quality
  avgSlippage: number;
  avgSpread: number;
  fillRate: number;
  rejectionRate: number;
}

// WebSocket and Streaming types
export interface StreamingConfig {
  reconnectAttempts: number;
  reconnectDelay: number;
  heartbeatInterval: number;
  bufferSize: number;
  compressionEnabled: boolean;
  rateLimitBuffer: number;
}

export interface StreamMessage {
  type: 'TRADE' | 'QUOTE' | 'BAR' | 'ORDER_UPDATE' | 'ACCOUNT_UPDATE' | 'ERROR' | 'HEARTBEAT';
  timestamp: Date;
  symbol?: string;
  data: any;
  sequence?: number;
}

export interface ConnectionStatus {
  connected: boolean;
  authenticated: boolean;
  subscriptions: string[];
  lastHeartbeat: Date;
  reconnectCount: number;
  latency: number;
  messagesReceived: number;
  messagesPerSecond: number;
}

// Notification and Alert types
export interface NotificationConfig {
  enabled: boolean;
  channels: NotificationChannel[];
  filters: NotificationFilter[];
  rateLimiting: {
    maxPerMinute: number;
    maxPerHour: number;
    cooldownPeriod: number;
  };
}

export interface NotificationChannel {
  type: 'EMAIL' | 'SLACK' | 'WEBHOOK' | 'SMS';
  config: any;
  enabled: boolean;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface NotificationFilter {
  type: string;
  condition: string;
  threshold: number;
  enabled: boolean;
}

export interface Alert {
  id: string;
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  message: string;
  timestamp: Date;
  acknowledged: boolean;
  data: any;
  source: string;
}
