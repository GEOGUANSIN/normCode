"""
Position Sizing Script

Calculates appropriate position size based on signals and risk profile.
This script is invoked by paradigms that need position sizing computation.
"""

def calculate_position_size(
    signal_bundle: dict,
    risk_profile: dict,
    current_price: float = None
) -> dict:
    """
    Calculate position size based on signals and risk constraints.
    
    Args:
        signal_bundle: Dict containing quantitative and narrative signals
        risk_profile: Investor's risk profile with constraints
        current_price: Current asset price (optional, extracted from signals if not provided)
        
    Returns:
        Dict with position sizing details
    """
    # Extract risk parameters
    max_position = risk_profile.get("max_position_size", {})
    stop_loss = risk_profile.get("stop_loss_rules", {})
    risk_tolerance = risk_profile.get("risk_tolerance", {})
    
    absolute_max = max_position.get("absolute_max_usd", 50000)
    portfolio_pct = max_position.get("portfolio_percentage", 0.10)
    per_trade_limit = max_position.get("per_trade_limit_usd", 10000)
    
    default_stop_pct = stop_loss.get("default_stop_loss_pct", 0.05)
    trailing_enabled = stop_loss.get("trailing_stop_enabled", False)
    trailing_pct = stop_loss.get("trailing_stop_pct", 0.03)
    
    # Extract signal confidence
    quant_signals = signal_bundle.get("quantitative_signals", {})
    narrative_signals = signal_bundle.get("narrative_signals", {})
    
    quant_confidence = quant_signals.get("summary", {}).get("confidence", 0.5)
    narrative_confidence = narrative_signals.get("confidence", 0.5)
    
    # Combined confidence (weighted average)
    combined_confidence = 0.6 * quant_confidence + 0.4 * narrative_confidence
    
    # Get current price from signals if not provided
    if current_price is None:
        current_price = quant_signals.get("current_price", 2100)  # fallback
    
    # Base position size (start with per-trade limit)
    base_position = per_trade_limit
    
    # Adjust for confidence (scale between 50% and 100% of base)
    confidence_multiplier = 0.5 + (0.5 * combined_confidence)
    adjusted_position = base_position * confidence_multiplier
    
    # Apply absolute maximum
    final_position = min(adjusted_position, absolute_max)
    
    # Calculate units
    units = final_position / current_price
    
    # Calculate stop loss price
    stop_loss_price = current_price * (1 - default_stop_pct)
    
    # Calculate risk amount
    risk_per_unit = current_price - stop_loss_price
    total_risk = risk_per_unit * units
    
    # Calculate target (using 2:1 reward-to-risk ratio)
    target_price = current_price + (2 * risk_per_unit)
    
    return {
        "position_size_usd": round(final_position, 2),
        "units": round(units, 4),
        "current_price": current_price,
        "stop_loss_price": round(stop_loss_price, 2),
        "target_price": round(target_price, 2),
        "risk_amount_usd": round(total_risk, 2),
        "reward_risk_ratio": 2.0,
        "confidence_used": round(combined_confidence, 2),
        "trailing_stop": {
            "enabled": trailing_enabled,
            "percentage": trailing_pct
        },
        "sizing_rationale": f"Position sized at {confidence_multiplier:.0%} of ${per_trade_limit} limit based on {combined_confidence:.0%} signal confidence"
    }


# Entry point for paradigm execution (paradigm calls main())
def main(input_1: dict, input_2: dict = None) -> dict:
    """
    Main entry point called by the paradigm.
    
    Args:
        input_1: Signal bundle (quantitative + narrative signals)
        input_2: Investor risk profile (optional, extracted from input_1 if bundled)
    
    Returns:
        Position sizing details
    """
    # Handle case where inputs are bundled together
    if input_2 is None:
        # Assume input_1 contains both signal_bundle and risk_profile
        if isinstance(input_1, dict):
            signal_bundle = input_1.get("signal_bundle", input_1.get("validated_signal", input_1))
            risk_profile = input_1.get("risk_profile", input_1.get("investor_risk_profile", {}))
        else:
            signal_bundle = input_1
            risk_profile = {}
    else:
        signal_bundle = input_1
        risk_profile = input_2
    
    return calculate_position_size(signal_bundle, risk_profile)


if __name__ == "__main__":
    import json
    import sys
    
    # Read from stdin or use test data
    if not sys.stdin.isatty():
        input_data = json.load(sys.stdin)
        signal_bundle = input_data.get("signal_bundle", {})
        risk_profile = input_data.get("risk_profile", {})
    else:
        # Test with sample data
        signal_bundle = {
            "quantitative_signals": {
                "current_price": 2130,
                "summary": {"confidence": 0.7}
            },
            "narrative_signals": {
                "confidence": 0.8
            }
        }
        risk_profile = {
            "max_position_size": {"per_trade_limit_usd": 10000},
            "stop_loss_rules": {"default_stop_loss_pct": 0.05}
        }
    
    result = calculate_position_size(signal_bundle, risk_profile)
    print(json.dumps(result, indent=2))

