"""
The RSI measures the strength of recent price momentum 
by comparing average gains to average losses over a chosen lookback period (usually 14). 
Starting from a series of closing prices (C_t), you first compute the day-to-day changes (Δ_t = C_t - C_{t-1}), 
then separate them into **gains** (positive changes) and **losses** (absolute values of negative changes). 
The initial 14-period averages of these gains and losses give (\text{AvgGain}*{14}) and (\text{AvgLoss}*{14}). 
From that point onward, each is smoothed using Wilder’s formula—essentially an exponential moving average with smoothing factor (1/14):
[
\text{AvgGain}*t = \frac{(\text{AvgGain}*{t-1} \times 13) + \text{Gain}_t}{14}, \quad
\text{AvgLoss}*t = \frac{(\text{AvgLoss}*{t-1} \times 13) + \text{Loss}_t}{14}.
]
The **Relative Strength** is then (RS_t = \text{AvgGain}_t / \text{AvgLoss}_t), 
and the **RSI** converts this into a 0–100 scale via
[
RSI_t = 100 - \frac{100}{1 + RS_t}.
]
When RSI rises above 50, average gains dominate (bullish momentum);
when it falls below 50, losses dominate (bearish momentum);

"""

"""

:<:({RSI(14)'s momentum status} in the {period})
    <= *every({period})
        <= $.
        <- [{RSI(14)'s momentum status} in the {period}*]
            <= &in[{period}*1; {RSI(14)'s momentum status}]
                <- {period}*1

                <- {RSI(14)'s momentum status}
                    <= @by(5):({RSI(14)'s momentum status})

                <- <RSI above 50>
                    <= ::<RSI above 50>
                    <- {RSI}<$={2}>
                        <= @by(4):({RSI})
                        <- {period}*1
        <- {period}
            <= :>@time:()

    <- {iniital moving average of gains or losses}
        <= ::(compute the average of gains or losses in 14-days period)        
            <- [{gains or losses}]
                <= ::(seperate the {gains or losses} from the changes)
                    <- [{the day-to-day changes}]
                        <= ::(compute the day-to-day changes (Δ_t = C_t - C_{t-1}))
                        <- [{series of closing prices (C_t)}]
                            <= ::(get series of closing prices (C_t) at this period)
                            <- [{period}]
                                <= :<@1:([{period}])
                <- {gains or losses}

    <- {new moving average of gains or losses}
        <= ::(compute new moving average by Wilder's formula)
        <- {\text{AvgGain}*t = \frac{(\text{AvgGain}*{t-1} \times 13) + \text{Gain}_t}{14}}?
            <= @if<{gains or losses} is {gains}>
        <- {\text{AvgLoss}*t = \frac{(\text{AvgLoss}*{t-1} \times 13) + \text{Loss}_t}{14}}?
            <= @if<{gains or losses} is {losses}>
        <- {closing prices (C_{t+1})}
            <= ::(get the period closing prices of this period)
                <- [{period}]
                <= :<@2:([{period}])
        <- [{previous average of gains or losses}]
            <= :<@2:([{previous average of gains or losses}])

    <- {RSI computed}
        <= ::(compute the RSI with formula)
        <- {(RSI_t = 100 - \frac{100}{1 + RS_t})}
        <- {relative strength}
            <= ::(compute the relative strength with formula)
            <- {(RS_t = \text{AvgGain}_t / \text{AvgLoss}_t)}
            <- [{gain} and {loss}]
                <= :<@3:()

    <- {RSI}
        <= @by(3):({RSI computed})

        <- {average losses}
            <= @by(2):({new moving average of gains or losses})
                <= @if(<this period is initial period>)
            <- {next period}
            <- {losses}?
            <- {previous average of losses}

        <- {average gains}
            <= @by(2):({new moving average of gains or losses})
                <= @if!(<this period is initial period>)
            <- {next period}
            <- {gains}?
            <- {previous average of gains}

        <- {average losses}
            <= @by(1):({iniital moving average of gains or losses})
                <= @if!(<this period is initial period>)
            <- {losses}?
            <- {period}

        <- {average gains}
            <= @by(1):({iniital moving average of gains or losses})
                <= @if(<this period is initial period>)
            <- {gains}?
            <- {period}

        <- {period}
            <= $.
                <= @if(<next period is not the last period>)
            <- {next period}
                <= ::(period + 1)
                <- [{period}*1]
                    <= :<:{@4}([{period}*1])



    <- <this period is initial period>

        <= :%(True):<{this period} is the initial period in {all period}>

        <- {this period}
            <= :<@4:([{period}*1])

        <- [all {period}]
            <= &across({period})
            <- {period}



    <- {RSI(14)'s momentum status}
            <= $%
                <= @after(<RSI above 50>)
            <- {bullish}
                <= @if(<RSI above 50>)
            <- {bearish}
                <= @if!(<RSI above 50>)



"""