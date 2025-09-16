export interface Trade {
    side: "BUY" | "SELL";
    price: number;
    size: number;
    timestamp: string; // YYYY-MM-DD
    reason: string;
  }
  
  export interface OHLC {
    time: string; // YYYY-MM-DD
    open: number;
    high: number;
    low: number;
    close: number;
  }
  