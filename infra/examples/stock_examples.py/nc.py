nc_raw = """
:<: 
	<= $::
	<- ::(sell)
        <= @if(<price will fall>)
	<- ::(buy)
        <= @if!(<price will fall>)
    <- <price will fall>
        <= :%(True):<most {indicators} are {negative}>
        <- {negative}?
        <- [{indicators} and {their levels}]
            <= *every[{indicator}?]@(1)
                <= $.
                <- [{indicators} and {their levels}]*1
                    <= ::(check the {level}? of {indicator}?)
                        <= 
                    <- {level}?
                    <- {indicators}?*1
            <- {indicators}?
                <= &across[{indicator_1}?, {indicator_2}?:{indicators}?]
                <- {indicator_1}?
                <- {indicator_2}?


"""

"""
Place a DAY limit buy for 100 shares of AAPL at $180, 
only if an indicator scan for AAPL right now returns a majority of bullish signals among 
{RSI(14), MACD crossover, SMA(20) > SMA(50), Price > VWAP}.
"""

"""
::(Place a DAY limit buy for 100 shares of AAPL at $180)
    <= @if(<condition>)
    <- <condition>
        <= ::<an indicator scan for AAPL right now returns a majority of bullish signals among 
            {RSI(14), MACD crossover, SMA(20) > SMA(50), Price > VWAP}>       


        <- [{indicators} and {their levels}]
            <= *every[{indicator}?]@(1)
                <= $.
                <- [{indicator}? and {bulllish status}]*1
                    <= &in[{indicator}?:_, {bulllish status}:_]
                    <- {indicator}?
                    <- {bulllish status}
                        <= ::(check the {bulllish status}? of {indicator})
                        <- {bulllish status}?
                        <- {indicator}?*1

        <- {indicator}?
            <= &across+[{#}:{#}]
            <- {RSI(14)}?<:{1}>
            <- {MACD crossover}?<:{2}>
            <- {SMA(20) > SMA(50)}?<:{3}>
            <- {Price > VWAP}?<:{4}>
"""

"""
::(Place a DAY limit buy for 100 shares of AAPL at $180, 
only if an indicator scan for AAPL right now returns a majority of bullish signals among 
{RSI(14), MACD crossover, SMA(20) > SMA(50), Price > VWAP}.)
"""

"""
:<:
    <=::()
        <= @by(1):({a})^+[{#}<:{#}>]
        <- +[{x}<$={#}><:{#}>]


    <- {x}<$={1}>
        <= :>:({1}?<$={DAY limit buy for 100 shares}?>)
    <- {x}<$={2}>
        <= $%
        <- {_}
            <= :>:({2}?<$={AAPL}?>)
    <- {x}<$={3}>
        <= $%
        <- {_}
            <= :>:({3}?<$={180 dollars}?>)

    <- {a}
        <= $::
            <= @if(<condition>)
            <- <condition>
        <- :Trader:(Place a {1}<$({DAY limit buy for 100 shares})%_> of {2}<$({AAPL})%_> at {3}<$({180 dollars})%_>)
            <= :>:({1}?<$=:Trader:?>)
        <- +[{x}<:$={#}><:{#}>]@1

    <- <condition>    
        <= :%(True):<an {1}<$({indicator scan})%_> for {2}<$({stock})%_> has a majority of bullish signals among 
            {3}<$({indicators with their bullish status})%_>>

        <- {indicator scan}?<:{1}>
        <- {stock}?<:{2}>
        <- [[{z} and {w}<$={2}>]]<:{3}>


    <- [[{z} and {w}<$={2}>]]
        <= across[[{z} and {w}<$={2}>]:_]
            <- [{z} and {w}<$={2}>]
                <= *every[{z}]@(1)^[{w}<$={2}><*0>]
                    <= $.
                    <- [{z}*1 and {w}<$={2}>]
                        <= &in+[{#}:{#}]
                        <- {z}*1<:{1}>
                        <- {w}<$={2}><:{2}>
                            <= ::()
                                <= @by(2):({b})^+[{#}<:{#}>]
                            <- +[{w}<$={#}><:{#}>]

                    <- {w}<$={2}>
                        <= $.
                        <- {z}*1

    <- {w}<$={1}>
        <= :>:({1}?<$={bulllish status}?>)
    <- {b}
        <= $::
        <- :Monitor:(check the {1}?<$({bulllish status})%_> of {2}<$({indicator})%_>)
            <= :>:({1}?<$=:Monitor:?>)
        <- +[{w}<:$={#}><:{#}>]@2


    <- {z}
        <= &across+[{#}:{#}]
        <- +[{y}<$={#}><:{#}>]


    <- {y}<$={1}>
        <= :>:({1}?<$={RSI(14)}?>)
    <- {y}<$={2}>
        <= :>:({1}?<$={MACD crossover}?>)
    <- {y}<$={3}>
        <= :>:({1}?<$={SMA(20) > SMA(50)}?>)
    <- {y}<$={4}>
        <= :>:({1}?<$={Price > VWAP}?>)



    <- {b}
        <= $::
        <- :Monitor:(check the {1}?<$({bulllish status})%_> of {2}<$({indicator})%_>)
            <= @by(3):({c})^+[{#}<:{#}>]
            <- +[{v}<:$={#}><:{#}>]
        <- +[{w}<:$={#}><:{#}>]@2


    <= if indicator is 

"""