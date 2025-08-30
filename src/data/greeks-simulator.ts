
import { create, all } from 'mathjs';

const math = create(all);

export interface GreeksResult {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
  impliedVolatility?: number;
}

export interface OptionPricingInputs {
  underlyingPrice: number;
  strikePrice: number;
  timeToExpiration: number; // in years
  riskFreeRate: number; // annual rate (e.g., 0.05 for 5%)
  volatility: number; // annual volatility (e.g., 0.20 for 20%)
  optionType: 'call' | 'put';
  dividendYield?: number; // annual dividend yield
}

export interface OptionPriceResult extends GreeksResult {
  theoreticalPrice: number;
  intrinsicValue: number;
  timeValue: number;
  moneyness: 'ITM' | 'ATM' | 'OTM';
}

export class GreeksSimulator {
  private static readonly TRADING_DAYS_PER_YEAR = 252;
  private static readonly HOURS_PER_TRADING_DAY = 6.5;
  private static readonly MINUTES_PER_TRADING_DAY = 390;

  /**
   * Calculate option price and Greeks using Black-Scholes model
   */
  static calculateOptionPrice(inputs: OptionPricingInputs): OptionPriceResult {
    const {
      underlyingPrice: S,
      strikePrice: K,
      timeToExpiration: T,
      riskFreeRate: r,
      volatility: sigma,
      optionType,
      dividendYield: q = 0
    } = inputs;

    // Validate inputs
    if (S <= 0 || K <= 0 || T < 0 || sigma <= 0) {
      throw new Error('Invalid option pricing inputs');
    }

    // Handle edge case where time to expiration is 0
    if (T === 0) {
      const intrinsicValue = optionType === 'call' 
        ? Math.max(S - K, 0) 
        : Math.max(K - S, 0);
      
      return {
        theoreticalPrice: intrinsicValue,
        intrinsicValue,
        timeValue: 0,
        delta: optionType === 'call' ? (S > K ? 1 : 0) : (S < K ? -1 : 0),
        gamma: 0,
        theta: 0,
        vega: 0,
        rho: 0,
        moneyness: this.getMoneyness(S, K, optionType)
      };
    }

    // Calculate d1 and d2
    const d1 = (Math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T));
    const d2 = d1 - sigma * Math.sqrt(T);

    // Standard normal CDF and PDF
    const N = (x: number) => 0.5 * (1 + math.erf(x / Math.sqrt(2)));
    const n = (x: number) => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);

    // Calculate option price
    let theoreticalPrice: number;
    if (optionType === 'call') {
      theoreticalPrice = S * Math.exp(-q * T) * N(d1) - K * Math.exp(-r * T) * N(d2);
    } else {
      theoreticalPrice = K * Math.exp(-r * T) * N(-d2) - S * Math.exp(-q * T) * N(-d1);
    }

    // Calculate Greeks
    const delta = this.calculateDelta(S, K, T, r, sigma, q, optionType, d1);
    const gamma = this.calculateGamma(S, T, sigma, q, d1);
    const theta = this.calculateTheta(S, K, T, r, sigma, q, optionType, d1, d2);
    const vega = this.calculateVega(S, T, sigma, q, d1);
    const rho = this.calculateRho(K, T, r, optionType, d2);

    // Calculate intrinsic and time value
    const intrinsicValue = optionType === 'call' 
      ? Math.max(S - K, 0) 
      : Math.max(K - S, 0);
    const timeValue = Math.max(theoreticalPrice - intrinsicValue, 0);

    return {
      theoreticalPrice,
      intrinsicValue,
      timeValue,
      delta,
      gamma,
      theta,
      vega,
      rho,
      moneyness: this.getMoneyness(S, K, optionType)
    };
  }

  /**
   * Calculate Delta (price sensitivity to underlying price changes)
   */
  private static calculateDelta(
    S: number, K: number, T: number, r: number, sigma: number, q: number,
    optionType: 'call' | 'put', d1: number
  ): number {
    const N = (x: number) => 0.5 * (1 + math.erf(x / Math.sqrt(2)));
    
    if (optionType === 'call') {
      return Math.exp(-q * T) * N(d1);
    } else {
      return -Math.exp(-q * T) * N(-d1);
    }
  }

  /**
   * Calculate Gamma (rate of change of Delta)
   */
  private static calculateGamma(S: number, T: number, sigma: number, q: number, d1: number): number {
    const n = (x: number) => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
    return Math.exp(-q * T) * n(d1) / (S * sigma * Math.sqrt(T));
  }

  /**
   * Calculate Theta (time decay)
   */
  private static calculateTheta(
    S: number, K: number, T: number, r: number, sigma: number, q: number,
    optionType: 'call' | 'put', d1: number, d2: number
  ): number {
    const N = (x: number) => 0.5 * (1 + math.erf(x / Math.sqrt(2)));
    const n = (x: number) => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);

    const term1 = -Math.exp(-q * T) * S * n(d1) * sigma / (2 * Math.sqrt(T));
    
    if (optionType === 'call') {
      const term2 = q * S * Math.exp(-q * T) * N(d1);
      const term3 = -r * K * Math.exp(-r * T) * N(d2);
      return (term1 - term2 + term3) / 365; // Convert to daily theta
    } else {
      const term2 = -q * S * Math.exp(-q * T) * N(-d1);
      const term3 = r * K * Math.exp(-r * T) * N(-d2);
      return (term1 + term2 + term3) / 365; // Convert to daily theta
    }
  }

  /**
   * Calculate Vega (sensitivity to volatility changes)
   */
  private static calculateVega(S: number, T: number, sigma: number, q: number, d1: number): number {
    const n = (x: number) => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
    return S * Math.exp(-q * T) * n(d1) * Math.sqrt(T) / 100; // Divide by 100 for 1% vol change
  }

  /**
   * Calculate Rho (sensitivity to interest rate changes)
   */
  private static calculateRho(K: number, T: number, r: number, optionType: 'call' | 'put', d2: number): number {
    const N = (x: number) => 0.5 * (1 + math.erf(x / Math.sqrt(2)));
    
    if (optionType === 'call') {
      return K * T * Math.exp(-r * T) * N(d2) / 100; // Divide by 100 for 1% rate change
    } else {
      return -K * T * Math.exp(-r * T) * N(-d2) / 100; // Divide by 100 for 1% rate change
    }
  }

  /**
   * Calculate implied volatility using Newton-Raphson method
   */
  static calculateImpliedVolatility(
    marketPrice: number,
    underlyingPrice: number,
    strikePrice: number,
    timeToExpiration: number,
    riskFreeRate: number,
    optionType: 'call' | 'put',
    dividendYield: number = 0,
    tolerance: number = 0.0001,
    maxIterations: number = 100
  ): number {
    // Initial guess
    let volatility = 0.20; // 20% initial guess
    
    for (let i = 0; i < maxIterations; i++) {
      const inputs: OptionPricingInputs = {
        underlyingPrice,
        strikePrice,
        timeToExpiration,
        riskFreeRate,
        volatility,
        optionType,
        dividendYield
      };

      const result = this.calculateOptionPrice(inputs);
      const priceDiff = result.theoreticalPrice - marketPrice;

      // Check convergence
      if (Math.abs(priceDiff) < tolerance) {
        return volatility;
      }

      // Newton-Raphson update: vol_new = vol_old - f(vol) / f'(vol)
      // f'(vol) is vega
      if (result.vega > 0.0001) { // Avoid division by zero
        volatility = volatility - priceDiff / (result.vega * 100); // vega is already scaled
      } else {
        break;
      }

      // Keep volatility within reasonable bounds
      volatility = Math.max(0.001, Math.min(5.0, volatility));
    }

    return volatility;
  }

  /**
   * Convert time to expiration from minutes to years
   */
  static minutesToYears(minutes: number): number {
    return minutes / (this.TRADING_DAYS_PER_YEAR * this.MINUTES_PER_TRADING_DAY);
  }

  /**
   * Convert time to expiration from hours to years
   */
  static hoursToYears(hours: number): number {
    return hours / (this.TRADING_DAYS_PER_YEAR * this.HOURS_PER_TRADING_DAY);
  }

  /**
   * Convert time to expiration from days to years
   */
  static daysToYears(days: number): number {
    return days / this.TRADING_DAYS_PER_YEAR;
  }

  /**
   * Calculate time to expiration in years from expiration date
   */
  static timeToExpiration(expirationDate: Date, currentDate: Date = new Date()): number {
    const msToExpiration = expirationDate.getTime() - currentDate.getTime();
    const minutesToExpiration = msToExpiration / (1000 * 60);
    return this.minutesToYears(Math.max(0, minutesToExpiration));
  }

  /**
   * Determine if option is ITM, ATM, or OTM
   */
  private static getMoneyness(underlyingPrice: number, strikePrice: number, optionType: 'call' | 'put'): 'ITM' | 'ATM' | 'OTM' {
    const priceDiff = Math.abs(underlyingPrice - strikePrice);
    const atmThreshold = underlyingPrice * 0.005; // 0.5% threshold for ATM

    if (priceDiff <= atmThreshold) {
      return 'ATM';
    }

    if (optionType === 'call') {
      return underlyingPrice > strikePrice ? 'ITM' : 'OTM';
    } else {
      return underlyingPrice < strikePrice ? 'ITM' : 'OTM';
    }
  }

  /**
   * Calculate 0DTE specific metrics
   */
  static calculate0DTEMetrics(inputs: OptionPricingInputs): {
    timeDecayRate: number; // Theta per minute
    gammaRisk: number; // Gamma risk score (0-100)
    breakeven: number; // Breakeven price for the option
    probabilityITM: number; // Probability of finishing ITM
  } {
    const result = this.calculateOptionPrice(inputs);
    const { underlyingPrice, strikePrice, timeToExpiration, volatility, optionType } = inputs;

    // Time decay per minute (theta is already daily)
    const timeDecayRate = result.theta / this.MINUTES_PER_TRADING_DAY;

    // Gamma risk score (higher gamma = higher risk/reward)
    const gammaRisk = Math.min(100, result.gamma * underlyingPrice * underlyingPrice * 100);

    // Breakeven calculation
    let breakeven: number;
    if (optionType === 'call') {
      breakeven = strikePrice + result.theoreticalPrice;
    } else {
      breakeven = strikePrice - result.theoreticalPrice;
    }

    // Probability of finishing ITM (simplified Black-Scholes probability)
    const d2 = (Math.log(underlyingPrice / strikePrice) + (inputs.riskFreeRate - 0.5 * volatility * volatility) * timeToExpiration) / (volatility * Math.sqrt(timeToExpiration));
    const N = (x: number) => 0.5 * (1 + math.erf(x / Math.sqrt(2)));
    
    let probabilityITM: number;
    if (optionType === 'call') {
      probabilityITM = N(d2);
    } else {
      probabilityITM = N(-d2);
    }

    return {
      timeDecayRate,
      gammaRisk,
      breakeven,
      probabilityITM
    };
  }

  /**
   * Simulate option price changes over time (for backtesting)
   */
  static simulatePriceEvolution(
    inputs: OptionPricingInputs,
    priceChanges: number[], // Array of underlying price changes
    timeSteps: number[] // Array of time steps (in minutes)
  ): OptionPriceResult[] {
    const results: OptionPriceResult[] = [];
    let currentPrice = inputs.underlyingPrice;
    let currentTime = inputs.timeToExpiration;

    for (let i = 0; i < priceChanges.length && i < timeSteps.length; i++) {
      currentPrice += priceChanges[i];
      currentTime -= this.minutesToYears(timeSteps[i]);
      currentTime = Math.max(0, currentTime); // Don't go negative

      const newInputs: OptionPricingInputs = {
        ...inputs,
        underlyingPrice: currentPrice,
        timeToExpiration: currentTime
      };

      results.push(this.calculateOptionPrice(newInputs));
    }

    return results;
  }

  /**
   * Calculate portfolio Greeks for multiple positions
   */
  static calculatePortfolioGreeks(positions: Array<{
    inputs: OptionPricingInputs;
    quantity: number;
    multiplier?: number; // Contract multiplier (default 100)
  }>): GreeksResult {
    let totalDelta = 0;
    let totalGamma = 0;
    let totalTheta = 0;
    let totalVega = 0;
    let totalRho = 0;

    positions.forEach(position => {
      const result = this.calculateOptionPrice(position.inputs);
      const multiplier = position.multiplier || 100;
      const positionSize = position.quantity * multiplier;

      totalDelta += result.delta * positionSize;
      totalGamma += result.gamma * positionSize;
      totalTheta += result.theta * positionSize;
      totalVega += result.vega * positionSize;
      totalRho += result.rho * positionSize;
    });

    return {
      delta: totalDelta,
      gamma: totalGamma,
      theta: totalTheta,
      vega: totalVega,
      rho: totalRho
    };
  }
}
