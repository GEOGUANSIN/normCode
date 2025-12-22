"""
Technical Analysis Script for Gold Price Data

Computes price-based indicators from historical price data.
This script is invoked by the v_Script-h_Data-c_Execute-o_Struct paradigm.
"""

def compute_indicators(price_data: dict) -> dict:
    """
    Compute technical indicators from price data.
    
    Args:
        price_data: Dict containing 'data' list with OHLCV entries
        
    Returns:
        Dict with computed indicators
    """
    data = price_data.get("data", [])
    
    if not data:
        return {"error": "No price data provided"}
    
    # Extract closing prices
    closes = [d["close"] for d in data]
    volumes = [d["volume"] for d in data]
    
    # Simple Moving Averages
    def sma(values, period):
        if len(values) < period:
            return None
        return sum(values[-period:]) / period
    
    ma_5 = sma(closes, 5)
    ma_10 = sma(closes, 10)
    ma_20 = sma(closes, min(20, len(closes)))
    
    # RSI (simplified 14-period)
    def compute_rsi(prices, period=14):
        if len(prices) < period + 1:
            period = len(prices) - 1
        if period < 2:
            return 50  # neutral default
            
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    rsi = compute_rsi(closes)
    
    # MACD (12, 26, 9) - simplified
    def ema(values, period):
        if len(values) < period:
            return sma(values, len(values))
        multiplier = 2 / (period + 1)
        ema_val = sma(values[:period], period)
        for price in values[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
        return ema_val
    
    ema_12 = ema(closes, min(12, len(closes)))
    ema_26 = ema(closes, min(26, len(closes)))
    macd_line = ema_12 - ema_26 if ema_12 and ema_26 else 0
    
    # Price position relative to MAs
    current_price = closes[-1]
    above_ma_5 = current_price > ma_5 if ma_5 else None
    above_ma_10 = current_price > ma_10 if ma_10 else None
    
    # Volume trend (comparing recent to average)
    avg_volume = sum(volumes) / len(volumes)
    recent_volume = sum(volumes[-3:]) / 3 if len(volumes) >= 3 else volumes[-1]
    volume_trend = "increasing" if recent_volume > avg_volume * 1.1 else "decreasing" if recent_volume < avg_volume * 0.9 else "stable"
    
    # Price momentum (% change over last 5 days)
    if len(closes) >= 5:
        momentum_5d = (closes[-1] - closes[-5]) / closes[-5] * 100
    else:
        momentum_5d = (closes[-1] - closes[0]) / closes[0] * 100
    
    # Overall signal
    bullish_signals = 0
    bearish_signals = 0
    
    if above_ma_5: bullish_signals += 1
    elif above_ma_5 is False: bearish_signals += 1
    
    if above_ma_10: bullish_signals += 1
    elif above_ma_10 is False: bearish_signals += 1
    
    if rsi > 50 and rsi < 70: bullish_signals += 1
    elif rsi < 50 and rsi > 30: bearish_signals += 1
    
    if macd_line > 0: bullish_signals += 1
    elif macd_line < 0: bearish_signals += 1
    
    if momentum_5d > 1: bullish_signals += 1
    elif momentum_5d < -1: bearish_signals += 1
    
    overall_signal = "bullish" if bullish_signals > bearish_signals + 1 else "bearish" if bearish_signals > bullish_signals + 1 else "neutral"
    
    return {
        "symbol": price_data.get("symbol", "UNKNOWN"),
        "current_price": current_price,
        "indicators": {
            "ma_5": round(ma_5, 2) if ma_5 else None,
            "ma_10": round(ma_10, 2) if ma_10 else None,
            "ma_20": round(ma_20, 2) if ma_20 else None,
            "rsi": round(rsi, 2),
            "macd_line": round(macd_line, 4),
            "momentum_5d_pct": round(momentum_5d, 2),
            "volume_trend": volume_trend
        },
        "signals": {
            "above_ma_5": above_ma_5,
            "above_ma_10": above_ma_10,
            "rsi_zone": "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
            "macd_direction": "bullish" if macd_line > 0 else "bearish"
        },
        "summary": {
            "bullish_count": bullish_signals,
            "bearish_count": bearish_signals,
            "overall_signal": overall_signal,
            "confidence": abs(bullish_signals - bearish_signals) / 5.0
        }
    }


# Entry point for paradigm execution (paradigm calls main())
def main(input_1: dict) -> dict:
    """
    Main entry point called by the paradigm.
    Delegates to compute_indicators.
    """
    return compute_indicators(input_1)
if __name__ == "__main__":
    # When executed by paradigm, input comes from horizontal values
    import json
    import sys
    
    # Read from stdin or use test data
    if not sys.stdin.isatty():
        input_data = json.load(sys.stdin)
    else:
        # Test with sample data
        input_data = {
            "data": [
                {"close": 2050, "volume": 100000},
                {"close": 2060, "volume": 110000},
                {"close": 2055, "volume": 105000},
                {"close": 2070, "volume": 120000},
                {"close": 2080, "volume": 130000},
            ]
        }
    
    result = compute_indicators(input_data)
    print(json.dumps(result, indent=2))

