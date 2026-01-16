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
Book a flight from London to NYC for next Tuesday, 
but only if there is a hotel room available for under £200 that night.
"""

"""Normcode-version-0
::(Book a flight from London to NYC for next Tuesday)
    <= @if(<condition>)
    <- <condition>
        <= ::<there is a hotel room available in NYC for under £200 that night>
"""


"""Normcode-version-1
:<:({1}?<$={something booked}>)
    <= :App_book:(Book {1}?<$({something booked})%_> from {2}<$({source})%_> to {3}<$({destination})%_> for {4}<$({date})%_>)
        <= @if(<condition>)
        <- <condition>
            <= :%(True):<there is [{something}]>
            <- [{something}]
                <= &across({something}:{something})
                <- {something}
                    <= :App_search:({1}?<$({something})%_> in {2}<$({destination})%_> available for under {3}<$({price})%_> for {4}<$({date})%_>)
                    <- {hotel room}?<:{1}>
                    <- {NYC}?<:{2}>
                    <- {£200}?<:{3}>
                    <- {next Tuesday}?<:{4}>
    <- {ticket}?<:{1}>
    <- {London}?<:{2}>
    <- {NYC}?<:{3}>
    <- {next Tuesday}?<:{4}>
"""

"""Normcode-version-2

:<:({1}?<$={something booked}>)
    <= ::(Book a flight from London to NYC for next Tuesday)
        <= @by(1):({book result})^({1}<:{1}>, {2}<:{2}>, {3}<:{3}>, {4}<:{4}>)
            <= @if(<condition>)
            <- <condition>
                <= ::<there is a hotel room available in NYC for under £200 that night>
        <- {ticket}?<:{1}>
        <- {London}?<:{2}>
        <- {NYC}?<:{3}>
        <- {next Tuesday}?<:{4}>        

    <- {book result}<$={1}>
        <= $::
        <- :App_book:(Book {1}?<$({something booked})%_> from {2}<$({source})%_> to {3}<$({destination})%_> for {4}<$({date})%_>)<$={1}>
            <= :>:({1}?<$=:App_book:<$={1}>?>)
        <- [{1}<:{1}>, {2}<:{2}>, {3}<:{3}>, {4}<:{4}>]@1
"""




"""Normcode-version-3
:<:({1}?<$={something booked}>)
    <= ::(Book a flight from London to NYC for next Tuesday)
        <= @by(1):({book result})^[{1}<:{1}>, {2}<:{2}>, {3}<:{3}>, {4}<:{4}>]
            <= @if(<condition>)
            <- <condition>
                <= :%(True):<there is [{something}]>
                <- [{something}]
                    <= &across({something}:{something})
                    <- {something}
                        <= ::(hotel room available for under £200 that night)
                            <= @by(2):({search result})^({1}<:{1}>, {2}<:{2}>, {3}<:{3}>, {4}<:{4}>)
                            <- {something}<$={2}><:{1}>
                            <- {destination}<$={1}>
                            <- {price}<$={1}><:{3}>
                            <- {date}<$={1}><:{4}>
        <- {something}?<$={1}><:{1}>
        <- {source}<$={1}><:{2}>
        <- {destination}<$={1}><:{3}>
        <- {date}<$={1}><:{4}>


    <- {something}?<$={1}>
        <= :>:({1}?<$={ticket}?>)
    <- {source}<$={1}>
        <= $%
        <- {_}
            <= :>:({1}?<$={London}>)
    <- {destination}<$={1}>
        <= $%
        <- {_}
            <= :>:({1}?<$={NYC}>)
    <- {date}<$={1}>
        <= $%
        <- {_}
            <= :>:({1}?<$={next Tuesday}>)

    <- {book result}<$={1}>
        <= $::
        <- :App_book:(Book {1}?<$({something booked})%_> from {2}<$({source})%_> to {3}<$({destination})%_> for {4}<$({date})%_>)<$={1}>
            <= :>:({1}?<$=:App_book:<$={1}>?>)
        <- [{1}<:{1}>, {2}<:{2}>, {3}<:{3}>, {4}<:{4}>]@1

    <- {something}?<$={2}>
        <= :>:({1}?<$={hotel room}?>)

    <- {price}<$={1}>
        <= $%
        <- {_}
            <= :>:({1}?<$={£200}>)

    <- {search result}<$={1}>
        <= $::
        <- :App_search:({1}?<$({something})%_> in {2}<$({destination})%_> available for under {3}<$({price})%_> for {4}<$({date})%_>)
            <= :>:({1}?<$=:App_search:<$={1}>?>)
        <- [{1}<:{1}>, {2}<:{2}>, {3}<:{3}>, {4}<:{4}>]@2
    
"""


"""
Do something about some inputs x by method a and output something.
The input x 1 is flight, the input x 2 is London, the input x 3 is NYC, the input x 4 is next Tuesday.
The method a is to book something booked (being the input x 1) from source (being the input x 2) to destination (being the input x 3) for date (being the input x 4).
The method a is done only if condition is met.
The condition is met only if there is some non-empty z across all results of doing something about some inputs y by method b.
The input y 1 is hotel room, the input y 2 is input x 2, the input y 3 is £200, the input y 4 is input x 4.
The method b is to search for something (being the input y 1) in destination (being the input y 2) available for under price (being the input y 3) for date (being the input y 4).
"""

"""Normcode-version-4
:<:({1}?<$={_}>)
    <= ::()
        <= @by(1):({a})^+[{#}<:{#}>]
        <-+[{x}<$={#}><:{#}>]

    <- {x}<$={1}>
        <= :>:({1}?<$={flight}?>)
    <- {x}<$={2}>
        <= $%
        <- {_}
            <= :>:({1}?<$={London}>)
    <- {x}<$={3}>
        <= $%
        <- {_}
            <= :>:({1}?<$={NYC}>)
    <- {x}<$={4}>
        <= $%
        <- {_}
            <= :>:({1}?<$={next Tuesday}>)

    <- {a}<$={1}>
        <= $::
            <= @if(<condition>)
        <- :App_book:(Book {1}?<$({something booked})%_> from {2}<$({source})%_> to {3}<$({destination})%_> for {4}<$({date})%_>)<$={1}>
            <= :>:({1}?<$=:App_book:<$={1}>?>)
        <- +[{#}<:{#}>]@1

        <- <condition>
            <= :%(True):<there is [{z}]>
            <- [{z}]
                <= &across({z}:{z})
                <- {z}
                    <= ::()
                        <= @by(2):({b})^+[{#}<:{#}>]
                        <- +[{y}<$={#}><:{#}>]

        <- {y}<$={1}>
            <= :>:({1}?<$={hotel room}?>)
        <- {y}<$={2}>
            <= $=
            <- {x}<$={3}>
        <- {y}<$={3}>
            <= $%
            <- {_}
                <= :>:({1}?<$={£200}>)
        <- {y}<$={4}>
            <= $=
            <- {x}<$={4}>

        <- {b}<$={1}>
            <= $::
            <- :App_search:({1}?<$({something})%_> in {2}<$({destination})%_> available for under {3}<$({price})%_> for {4}<$({date})%_>)
                <= :>:({1}?<$=:App_search:<$={1}>?>)
            <- +[{#}<:{#}>]@2
    
"""
