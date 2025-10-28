
{new number pair} | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>] | 1.1. assigning

        <= $.({remainder}) 
        
        <- {digit sum} | 1.1.2. imperative
            <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
            <- {sum}?<:{3}>
            <- {carry-over number}*1<:{2}> 
            <- [all {unit place value} of numbers]<:{1}> | 1.1.2.4. grouping
                <= &across({unit place value}:{number pair}*1)
                <- {unit place value} | 1.1.2.4.2. quantifying
                    <= *every({number pair}*1)%:[{number}]@(2) | 1.1.2.4.2.1. assigning
                        <= $.({single unit place value})
                        <- {single unit place value} | 1.1.2.4.2.1.2. imperative
                            <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)
                            <- {unit place digit}?<:{2}>
                            <- {number pair}*1*2
                    <- {number pair}*1

        <- {number pair}<$={1}> | 1.1.3. assigning
            <= $+({number pair to append}:{number pair})%:[{number pair}] | 1.1.3.1. timing
                <= @if!(<all number is 0>) | 1.1.3.1.1. timing
                    <= @if(<carry-over number is 0>)

            <- {number pair to append}<$={1}> | 1.1.3.2. quantifying
                <= *every({number pair}*1)%:[{number}]@(3) | 1.1.3.2.1. assigning
                    <= $.({number with last digit removed}) 
                    <- {number with last digit removed} | 1.1.3.2.1.2. imperative
                        <= ::(output 0 if {1}<$({number})%_> is less than 10, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>) 
                        <- {unit place digit}?<:{2}> 
                        <- {number pair}*1*3<:{1}>
                <- {number pair}*1

            <- <all number is 0> | 1.1.3.3. judgement
                <= :%(True):<{1}<$({number})%_> is 0> | 1.1.3.3.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {number pair to append}<$={1}><:{1}>

            <- <carry-over number is 0> | 1.1.3.4. judgement
                <= :%(True):<{1}<$({carry-over number})%_> is 0> | 1.1.3.4.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {carry-over number}*1 | 1.1.3.4.2. grouping
                    <= &across({carry-over number}*1:{carry-over number}*1<--<!_>>)
                    <- {carry-over number}*1 | 1.1.3.4.2.2. imperative
                        <= ::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10) | 1.1.3.4.2.2.1. timing
                            <= @after({digit sum})
                        <- {quotient}?<:{1}>
                        <- {digit sum}<:{2}>

        <- {remainder} | 1.1.4. imperative
            <= ::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10) | 1.1.4.1. timing
                <= @after({digit sum})
            <- {remainder}?<:{1}>
            <- {digit sum}<:{2}>

    <- {number pair}<$={1}> |ref. %(number pair)=[%(number)=[123, 98]]

