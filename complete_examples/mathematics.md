
### Matehamtics Example




{model}
    <= $.({model})
    <- :S_model:(make {mathematical model with question} from the {scenarios})
    <- scenarios


{model} %= "the number we want = 7 + 9"


{model normcode}
    <= $.({model normcode})
    <- :S_NC:(make {model normcode}? from {model} model by {agent})
    <- {model}
    <- :S_model:


{model normcode} %= """
{the number we want}
    <= $.({the number we want})
    <- :S_model:({1}?<$={number}> = {2}<$={number}> + {3}<$={number}>)
    <- 7
    <- 9
"""


{calculation}
    <= :S_cal:(make {calculation} by observing {model normcode})
    <- {model normcode}

calculation %= "Calculate  ```NormCode :S_model:({1}?<$({number})%_> = {2}<$({number})%_ + {3}<$({number})%_>)``` by checking the table of addition with number {1} and number {2}." 

{calculation normCode}
    <= :S_NC:({calculation normCode} integrate {calculation} with {model normcode} by {agent})
    <- {model}
    <- :S_cal:


{calculation normCode} %= """
```NormCode
{the number we want}
    <= $.({the number we want})
    <- :S_model:({1}?<$({number})%_> = {2}<$({number})%_> + {3}<$({number})%_>)
        <= @by(:S_cal:^({1}<1:>), {2}<:2>, {3}<:3>)
        <- :S_cal:(check summation table {1}?<${result number}%_> for {2}<${number}%_> and {3}<${number}%_>)
    <- {7}<:2>
    <- {9}<:3>
```
"""

S_NC(:_:)
    <= S_NC(:_:)
    <- $({calculation NormCode}:)%
    <- {execution NormCode} 

#### Meta-mathematics Norm

```NormCode
S_NC(:_:)
    <= S_NC(:_:)
    <- $({calculation normCode}:)%
    <- {calculation normCode}
        <= :S_NC:({calculation normCode} integrate {calculation} with {model normcode} by {agent})
        <- {model normcode}
        <- :S_cal:
        <- {calculation}
            <= :S_cal:(make {calculation} by observing {model normcode})
            <- {model normcode}
                <= $.({model normcode}?)
                <- :S_NC:(make {model normcode}? from {model} model by {agent})
                <- {model}
                    <= $.({model}?)
                    <- :S_model:(make {mathematical model with question} from the {scenarios})
                    <- scenarios
                <- :S_model:
```

####One Possible After Session:

```NormCode
{the number we want}
    <= $.({the number we want})
    <- :S_model:({1}?<$({number})%_> = {2}<$({number})%_> + {3}<$({number})%_>)
        <= @by(:S_cal:^({1}<1:>), {2}<:2>, {3}<:3>)
        <- :S_cal:(check summation table {1}?<${result number}%_> for {2}<${number}%_> and {3}<${number}%_>)
    <- {7}<:2>
    <- {9}<:3>
```