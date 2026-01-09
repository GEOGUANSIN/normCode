# 看涨信号评估提示

评估整体信号是否为看涨（建议买入操作）。

## 输入
**验证信号包**: $input_1

**理论框架**: $input_2

## 决策规则

只有在以下条件全部满足时，信号才被判定为看涨：
1. 量化分析中的`overall_signal`为"bullish"，且
2. `bullish_count`超过`bearish_count`，且
3. 叙事情绪`overall_score`为正值（> 0）

**重要提示**：
- RSI超买（> 70）但伴随上升动能仍然是看涨信号（需谨慎）- 不是看跌信号
- 一个信号不能同时是看涨和看跌的 - 它们互相排斥
- 如果`overall_signal`显示"bullish"，此评估应返回`true`

## 评估步骤

1. 检查量化信号：
   - 查看`summary.overall_signal` - 是否为"bullish"？
   - 比较`bullish_count`与`bearish_count`
   
2. 检查叙事信号（如存在）：
   - 查看`overall_score` - 是否为正值？
   - 查看`confidence` - 是否合理（> 0.3）？

3. 做出最终判定：
   - 如果overall_signal为"bullish"且bullish_count > bearish_count → **真**
   - 否则 → **假**

## 输出
返回一个包含"answer"字段的JSON对象，该字段包含布尔值：
```json
{
  "answer": true
}
```

**关键提示**：
- 如果信号表明有买入机会，返回`true`
- 否则返回`false`
- 答案必须是布尔值（`true`或`false`），不是字符串

