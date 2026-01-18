# 看跌信号评估提示

评估整体信号是否为看跌（建议卖出操作）。

## 输入
**验证信号包**: $input_1

**理论框架**: $input_2

## 决策规则

只有在以下条件全部满足时，信号才被判定为看跌：
1. 量化分析中的`overall_signal`为"bearish"，且
2. `bearish_count`超过`bullish_count`，且
3. 叙事情绪`overall_score`为负值（< 0）

**重要提示**：
- RSI超买但伴随强劲上升动能不是看跌信号 - 而是需谨慎的看涨信号
- 一个信号不能同时是看涨和看跌的 - 它们互相排斥
- 如果`overall_signal`显示"bullish"，此评估必须返回`false`
- 只有当`overall_signal`明确显示"bearish"时才返回`true`

## 评估步骤

1. 检查量化信号：
   - 查看`summary.overall_signal` - 是否为"bearish"？
   - 比较`bearish_count`与`bullish_count`

2. 检查叙事信号（如存在）：
   - 查看`overall_score` - 是否为负值？
   - 查看主题 - 是否偏向看跌（鹰派政策、美元走强等）？

3. 做出最终判定：
   - 如果overall_signal为"bearish"且bearish_count > bullish_count → **真**
   - 否则 → **假**

## 输出
返回一个包含"answer"字段的JSON对象，该字段包含布尔值：
```json
{
  "answer": true
}
```

**关键提示**：
- 只有当信号明确表明卖出情况时才返回`true`
- 如果`overall_signal`为"bullish"或"neutral"，返回`false`
- 答案必须是布尔值（`true`或`false`），不是字符串

