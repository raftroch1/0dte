
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import WebSocket from 'ws';
import { EventEmitter } from 'events';
import { MarketData, OptionsChain, Position } from './types';

export interface AlpacaConfig {
  apiKey: string;
  apiSecret: string;
  baseUrl?: string;
  dataUrl?: string;
  streamUrl?: string;
  isPaper?: boolean;
}

export interface OptionContract {
  id: string;
  symbol: string;
  name: string;
  status: string;
  tradable: boolean;
  expiration_date: string;
  root_symbol: string;
  underlying_symbol: string;
  underlying_asset_id: string;
  type: 'call' | 'put';
  style: 'american' | 'european';
  strike_price: string;
  size: string;
  open_interest?: string;
  open_interest_date?: string;
  close_price?: string;
  close_price_date?: string;
}

export interface BarData {
  t: string; // timestamp
  o: number; // open
  h: number; // high
  l: number; // low
  c: number; // close
  v: number; // volume
  n?: number; // trade count
  vw?: number; // volume weighted average price
}

export interface TradeData {
  T: string; // message type
  S: string; // symbol
  p: number; // price
  s: number; // size
  t: string; // timestamp
  c?: string[]; // conditions
  i?: number; // trade id
  x?: string; // exchange
}

export interface QuoteData {
  T: string; // message type
  S: string; // symbol
  bp: number; // bid price
  bs: number; // bid size
  ap: number; // ask price
  as: number; // ask size
  t: string; // timestamp
  c?: string[]; // conditions
  bx?: string; // bid exchange
  ax?: string; // ask exchange
}

interface RateLimitQueue {
  requests: number;
  resetTime: number;
  maxRequests: number;
  windowMs: number;
}

export class AlpacaIntegration extends EventEmitter {
  private config: AlpacaConfig;
  private httpClient: AxiosInstance;
  private dataClient: AxiosInstance;
  private ws: WebSocket | null = null;
  private rateLimitQueue: RateLimitQueue;
  private isConnected = false;
  private isAuthenticated = false;
  private subscriptions: Set<string> = new Set();

  constructor(config: AlpacaConfig) {
    super();
    this.config = {
      baseUrl: config.isPaper ? 'https://paper-api.alpaca.markets' : 'https://api.alpaca.markets',
      dataUrl: 'https://data.alpaca.markets',
      streamUrl: config.isPaper ? 'wss://paper-api.alpaca.markets/stream' : 'wss://api.alpaca.markets/stream',
      ...config
    };

    // Initialize rate limiting (200 RPM for basic plan)
    this.rateLimitQueue = {
      requests: 0,
      resetTime: Date.now() + 60000,
      maxRequests: 200,
      windowMs: 60000
    };

    // Initialize HTTP clients
    this.httpClient = axios.create({
      baseURL: this.config.baseUrl,
      headers: this.getAuthHeaders(),
      timeout: 30000
    });

    this.dataClient = axios.create({
      baseURL: this.config.dataUrl,
      headers: this.getAuthHeaders(),
      timeout: 30000
    });

    // Add request interceptor for rate limiting
    this.dataClient.interceptors.request.use(async (config) => {
      await this.checkRateLimit();
      return config;
    });

    // Add response interceptor for error handling
    this.dataClient.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Alpaca API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  private getAuthHeaders() {
    return {
      'APCA-API-KEY-ID': this.config.apiKey,
      'APCA-API-SECRET-KEY': this.config.apiSecret,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };
  }

  private async checkRateLimit(): Promise<void> {
    const now = Date.now();
    
    // Reset counter if window has passed
    if (now >= this.rateLimitQueue.resetTime) {
      this.rateLimitQueue.requests = 0;
      this.rateLimitQueue.resetTime = now + this.rateLimitQueue.windowMs;
    }

    // Wait if rate limit exceeded
    if (this.rateLimitQueue.requests >= this.rateLimitQueue.maxRequests) {
      const waitTime = this.rateLimitQueue.resetTime - now;
      console.log(`Rate limit exceeded, waiting ${waitTime}ms`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      this.rateLimitQueue.requests = 0;
      this.rateLimitQueue.resetTime = Date.now() + this.rateLimitQueue.windowMs;
    }

    this.rateLimitQueue.requests++;
  }

  // Account and connection methods
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.httpClient.get('/v2/account');
      console.log('✅ Alpaca connection successful');
      return response.status === 200;
    } catch (error) {
      console.error('❌ Alpaca connection failed:', error);
      return false;
    }
  }

  async getAccount(): Promise<any> {
    try {
      const response = await this.httpClient.get('/v2/account');
      return response.data;
    } catch (error) {
      console.error('Error fetching account:', error);
      throw error;
    }
  }

  // Options data methods
  async getOptionContracts(underlyingSymbol: string, expiration?: string): Promise<OptionContract[]> {
    try {
      const params: any = {
        underlying_symbols: underlyingSymbol,
        limit: 1000
      };

      if (expiration) {
        params.expiration_date = expiration;
      }

      const response = await this.httpClient.get('/v2/options/contracts', { params });
      return response.data.option_contracts || [];
    } catch (error) {
      console.error('Error fetching option contracts:', error);
      throw error;
    }
  }

  async getOptionContract(symbolOrId: string): Promise<OptionContract | null> {
    try {
      const response = await this.httpClient.get(`/v2/options/contracts/${symbolOrId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching option contract:', error);
      return null;
    }
  }

  // Market data methods
  async getStockBars(
    symbol: string,
    timeframe: '1Min' | '5Min' | '15Min' | '1Hour' | '1Day',
    start: Date,
    end: Date,
    limit: number = 1000
  ): Promise<BarData[]> {
    try {
      const response = await this.dataClient.get(`/v2/stocks/${symbol}/bars`, {
        params: {
          timeframe,
          start: start.toISOString(),
          end: end.toISOString(),
          limit,
          adjustment: 'raw'
        }
      });

      return response.data.bars || [];
    } catch (error) {
      console.error('Error fetching stock bars:', error);
      throw error;
    }
  }

  async getOptionBars(
    symbol: string,
    timeframe: '1Min' | '5Min' | '15Min' | '1Hour' | '1Day',
    start: Date,
    end: Date,
    limit: number = 1000
  ): Promise<BarData[]> {
    try {
      const response = await this.dataClient.get(`/v2/options/bars`, {
        params: {
          symbols: symbol,
          timeframe,
          start: start.toISOString(),
          end: end.toISOString(),
          limit
        }
      });

      return response.data.bars?.[symbol] || [];
    } catch (error) {
      console.error('Error fetching option bars:', error);
      throw error;
    }
  }

  async getLatestQuote(symbol: string): Promise<QuoteData | null> {
    try {
      const response = await this.dataClient.get(`/v2/stocks/${symbol}/quotes/latest`);
      return response.data.quote;
    } catch (error) {
      console.error('Error fetching latest quote:', error);
      return null;
    }
  }

  async getOptionQuotes(symbols: string[]): Promise<{ [symbol: string]: QuoteData }> {
    try {
      const response = await this.dataClient.get('/v2/options/quotes/latest', {
        params: {
          symbols: symbols.join(',')
        }
      });

      return response.data.quotes || {};
    } catch (error) {
      console.error('Error fetching option quotes:', error);
      return {};
    }
  }

  // WebSocket streaming methods
  async connectStream(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${this.config.streamUrl}`);

        this.ws.on('open', () => {
          console.log('✅ WebSocket connected');
          this.isConnected = true;
          this.authenticate();
        });

        this.ws.on('message', (data: Buffer) => {
          try {
            const message = JSON.parse(data.toString());
            this.handleWebSocketMessage(message);
            
            if (message.stream === 'authorization' && message.data?.status === 'authorized') {
              this.isAuthenticated = true;
              resolve();
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        });

        this.ws.on('error', (error) => {
          console.error('WebSocket error:', error);
          this.isConnected = false;
          this.isAuthenticated = false;
          reject(error);
        });

        this.ws.on('close', () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          this.isAuthenticated = false;
          this.emit('disconnected');
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  private authenticate(): void {
    if (this.ws && this.isConnected) {
      const authMessage = {
        action: 'auth',
        key: this.config.apiKey,
        secret: this.config.apiSecret
      };
      this.ws.send(JSON.stringify(authMessage));
    }
  }

  private handleWebSocketMessage(message: any): void {
    switch (message.stream) {
      case 'authorization':
        if (message.data?.status === 'authorized') {
          console.log('✅ WebSocket authenticated');
          this.emit('authenticated');
        } else {
          console.error('❌ WebSocket authentication failed');
          this.emit('auth_failed');
        }
        break;

      case 'listening':
        console.log('✅ Subscribed to streams:', message.data?.streams);
        this.emit('subscribed', message.data?.streams);
        break;

      case 'trade_updates':
        this.emit('trade_update', message.data);
        break;

      default:
        this.emit('message', message);
        break;
    }
  }

  async subscribeToTradeUpdates(): Promise<void> {
    if (!this.isAuthenticated) {
      throw new Error('WebSocket not authenticated');
    }

    const subscribeMessage = {
      action: 'listen',
      data: {
        streams: ['trade_updates']
      }
    };

    this.ws?.send(JSON.stringify(subscribeMessage));
  }

  // Market data streaming (separate WebSocket)
  async connectMarketDataStream(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const marketDataUrl = 'wss://stream.data.alpaca.markets/v2/sip';
        this.ws = new WebSocket(marketDataUrl, {
          headers: this.getAuthHeaders()
        });

        this.ws.on('open', () => {
          console.log('✅ Market data stream connected');
          this.authenticateMarketData();
        });

        this.ws.on('message', (data: Buffer) => {
          try {
            const messages = JSON.parse(data.toString());
            if (Array.isArray(messages)) {
              messages.forEach(msg => this.handleMarketDataMessage(msg));
            }
            
            // Check for authentication success
            const authMsg = messages.find((m: any) => m.T === 'success' && m.msg === 'authenticated');
            if (authMsg) {
              resolve();
            }
          } catch (error) {
            console.error('Error parsing market data message:', error);
          }
        });

        this.ws.on('error', (error) => {
          console.error('Market data stream error:', error);
          reject(error);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  private authenticateMarketData(): void {
    if (this.ws) {
      const authMessage = {
        action: 'auth',
        key: this.config.apiKey,
        secret: this.config.apiSecret
      };
      this.ws.send(JSON.stringify(authMessage));
    }
  }

  private handleMarketDataMessage(message: any): void {
    switch (message.T) {
      case 'success':
        if (message.msg === 'authenticated') {
          console.log('✅ Market data stream authenticated');
          this.emit('market_data_authenticated');
        }
        break;

      case 'subscription':
        console.log('✅ Market data subscriptions:', message);
        this.emit('market_data_subscribed', message);
        break;

      case 't': // Trade
        this.emit('trade', message);
        break;

      case 'q': // Quote
        this.emit('quote', message);
        break;

      case 'b': // Bar
        this.emit('bar', message);
        break;

      case 'error':
        console.error('Market data error:', message);
        this.emit('market_data_error', message);
        break;

      default:
        this.emit('market_data_message', message);
        break;
    }
  }

  async subscribeToMarketData(symbols: string[], dataTypes: ('trades' | 'quotes' | 'bars')[] = ['trades', 'quotes']): Promise<void> {
    if (!this.ws) {
      throw new Error('Market data stream not connected');
    }

    const subscription: any = { action: 'subscribe' };
    
    if (dataTypes.includes('trades')) {
      subscription.trades = symbols;
    }
    if (dataTypes.includes('quotes')) {
      subscription.quotes = symbols;
    }
    if (dataTypes.includes('bars')) {
      subscription.bars = symbols;
    }

    this.ws.send(JSON.stringify(subscription));
    
    // Track subscriptions
    symbols.forEach(symbol => {
      dataTypes.forEach(type => {
        this.subscriptions.add(`${type}:${symbol}`);
      });
    });
  }

  // Trading methods
  async placeOrder(order: {
    symbol: string;
    qty: number;
    side: 'buy' | 'sell';
    type: 'market' | 'limit' | 'stop' | 'stop_limit';
    time_in_force: 'day' | 'gtc' | 'ioc' | 'fok';
    limit_price?: number;
    stop_price?: number;
    extended_hours?: boolean;
  }): Promise<any> {
    try {
      const response = await this.httpClient.post('/v2/orders', order);
      return response.data;
    } catch (error) {
      console.error('Error placing order:', error);
      throw error;
    }
  }

  async getPositions(): Promise<Position[]> {
    try {
      const response = await this.httpClient.get('/v2/positions');
      return response.data.map((pos: any) => this.mapToPosition(pos));
    } catch (error) {
      console.error('Error fetching positions:', error);
      throw error;
    }
  }

  private mapToPosition(alpacaPosition: any): Position {
    return {
      id: alpacaPosition.asset_id,
      symbol: alpacaPosition.symbol,
      side: alpacaPosition.side === 'long' ? 'CALL' : 'PUT', // Simplified mapping
      strike: 0, // Would need to parse from option symbol
      expiration: new Date(), // Would need to parse from option symbol
      quantity: parseInt(alpacaPosition.qty),
      entryPrice: parseFloat(alpacaPosition.avg_entry_price),
      currentPrice: parseFloat(alpacaPosition.market_value) / parseInt(alpacaPosition.qty),
      entryTime: new Date(alpacaPosition.created_at),
      unrealizedPnL: parseFloat(alpacaPosition.unrealized_pl),
      unrealizedPnLPercent: parseFloat(alpacaPosition.unrealized_plpc) * 100,
      is0DTE: false, // Would need to calculate based on expiration
      timeDecayRisk: 'MEDIUM',
      momentumScore: 0,
      exitStrategy: 'SIGNAL_BASED'
    };
  }

  // Cleanup
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.isAuthenticated = false;
    this.subscriptions.clear();
  }

  // Utility methods
  isMarketOpen(): boolean {
    const now = new Date();
    const marketOpen = new Date(now);
    marketOpen.setHours(9, 30, 0, 0);
    const marketClose = new Date(now);
    marketClose.setHours(16, 0, 0, 0);

    return now >= marketOpen && now <= marketClose && now.getDay() >= 1 && now.getDay() <= 5;
  }

  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }
}
