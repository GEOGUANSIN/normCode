"""
仓位计算脚本

根据信号和风险偏好计算适当的仓位规模。
此脚本由需要仓位计算的范式调用。
"""

def calculate_position_size(
    signal_bundle: dict,
    risk_profile: dict,
    current_price: float = None
) -> dict:
    """
    根据信号和风险约束计算仓位规模。
    
    参数:
        signal_bundle: 包含量化和叙事信号的字典
        risk_profile: 投资者风险偏好及约束条件
        current_price: 当前资产价格（可选，如未提供则从信号中提取）
        
    返回:
        包含仓位规模详情的字典
    """
    # 提取风险参数
    max_position = risk_profile.get("max_position_size", {})
    stop_loss = risk_profile.get("stop_loss_rules", {})
    risk_tolerance = risk_profile.get("risk_tolerance", {})
    
    absolute_max = max_position.get("absolute_max_usd", 50000)
    portfolio_pct = max_position.get("portfolio_percentage", 0.10)
    per_trade_limit = max_position.get("per_trade_limit_usd", 10000)
    
    default_stop_pct = stop_loss.get("default_stop_loss_pct", 0.05)
    trailing_enabled = stop_loss.get("trailing_stop_enabled", False)
    trailing_pct = stop_loss.get("trailing_stop_pct", 0.03)
    
    # 提取信号置信度
    quant_signals = signal_bundle.get("quantitative_signals", {})
    narrative_signals = signal_bundle.get("narrative_signals", {})
    
    quant_confidence = quant_signals.get("summary", {}).get("confidence", 0.5)
    narrative_confidence = narrative_signals.get("confidence", 0.5)
    
    # 综合置信度（加权平均）
    combined_confidence = 0.6 * quant_confidence + 0.4 * narrative_confidence
    
    # 如未提供，从信号中获取当前价格
    if current_price is None:
        current_price = quant_signals.get("current_price", 2100)  # 备用值
    
    # 基础仓位规模（从单笔交易限额开始）
    base_position = per_trade_limit
    
    # 根据置信度调整（在基础的50%到100%之间缩放）
    confidence_multiplier = 0.5 + (0.5 * combined_confidence)
    adjusted_position = base_position * confidence_multiplier
    
    # 应用绝对最大值
    final_position = min(adjusted_position, absolute_max)
    
    # 计算单位数量
    units = final_position / current_price
    
    # 计算止损价格
    stop_loss_price = current_price * (1 - default_stop_pct)
    
    # 计算风险金额
    risk_per_unit = current_price - stop_loss_price
    total_risk = risk_per_unit * units
    
    # 计算目标价（使用2:1的盈亏比）
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
        "sizing_rationale": f"根据{combined_confidence:.0%}信号置信度，仓位设为${per_trade_limit}限额的{confidence_multiplier:.0%}"
    }


# 范式执行入口点（范式调用 main()）
def main(input_1: dict, input_2: dict = None) -> dict:
    """
    范式调用的主入口点。
    
    参数:
        input_1: 信号包（量化+叙事信号）
        input_2: 投资者风险偏好（可选，如打包在一起则从input_1提取）
    
    返回:
        仓位规模详情
    """
    # 处理输入打包在一起的情况
    if input_2 is None:
        # 假设input_1同时包含signal_bundle和risk_profile
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
    
    # 从标准输入读取或使用测试数据
    if not sys.stdin.isatty():
        input_data = json.load(sys.stdin)
        signal_bundle = input_data.get("signal_bundle", {})
        risk_profile = input_data.get("risk_profile", {})
    else:
        # 使用样本数据测试
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
    print(json.dumps(result, indent=2, ensure_ascii=False))

