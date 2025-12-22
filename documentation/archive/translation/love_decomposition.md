

```normcode
:<:({Love})
    ...: "Love is a deep feeling of care and attachment toward someone or something. It shows through kind acts, sacrifice, and caring about another person's happiness. Love can be between partners, family, friends, or even spiritual connections. Love means accepting someone and wanting them to be happy, even when it's hard. Love is both an emotion and a decision to put someone else's wellbeing first."
    ?: What is Love?
    <= $.({deep feeling})
        ...: "Love is defined as a deep feeling with several aspects."
        ?: When is this deep feeling become love?
        <= @if(<definition satisfied>)
            /: "This deep feeling becomes love only when its defining conditions are satisfied."
        <- <definition satisfied>
            ...: "all the metioned conditions must be true: including shows through actions, can be between various entities, means acceptance and wanting happiness, and is a dual concept."
            ?: How to satisfy these conditions? (judgement request)
            <= ::{ALL(true)}<{individual conditions}>
                /: All the mentioned conditions must be true.
            <- {individual conditions}
                ...: "These conditions include showing through actions, can be between various entities, means acceptance and wanting happiness, and is a dual concept."
                ?: What are the individual conditions?
                <= &across
                    /: "The conditions are a sequence of the concepts defined in the initial decomposition."
                <- <shows through actions>
                <- <can be between various entities>
                <- <means acceptance and wanting happiness>
                <- <is a dual concept>
    <- {deep feeling}
        ...: "a deep feeling of care and attachment toward someone or something."
        ?: What is this feeling?
        <= $.({care or attachment})
            /: "It's specified as care and attachment."
        <- {care or attachment}
            ...: "care and attachment (as given by the user)."
            ?: What is this concept composed of?
            <= &across
                /: "This deep feeling is composed of care and attachment."
            <- {care}
                ...: "care (as given by the user)."
                ?: Is care a primitive input?
                <= :>:{care}?()
                    /: "Care is a primitive input from the user."
            <- {attachment}
                ...: "attachment (as given by the user)."
                ?: Is attachment a primitive input?
                <= :>:{attachment}?()
                    /: "Attachment is a primitive input from the user."
        <- <towards someone or something>
            ...: "towards someone or something (as given by the user)."
            ?: Towards what?
            <= ::<{deep feeling} is towards {target}>
                /: "The deep feeling is directed towards a target."
            <- {target}
                ...: "someone or something"
                ?: Is the target a primitive input?
                <= :>:{target}?()
                    /: "The target is a primitive input from the user."
    <- <shows through actions>
        ...: "This deep feeling shows through kind acts, sacrifice, and caring about another person's happiness."
        ?: How does it manifest? (Judgement Request)
        <= ::<{deep feeling} shows through {actions}>
        <- {actions}
            ...: "kind acts, sacrifice, and caring about another person's happiness (as given by the user)."
            ?: What are the actions?
            <= &across
                /: "The actions are a sequence of kind acts, sacrifice, and caring."
            <- {kind acts}
                ...: "kind acts (as given by the user)."
                ?: Are kind acts a primitive input?
                <= :>:{kind acts}?()
                    /: "Kind acts are a primitive input from the user."
            <- {sacrifice}
                ...: "sacrifice (as given by the user)."
                ?: Is sacrifice a primitive input?
                <= :>:{sacrifice}?()
                    /: "Sacrifice is a primitive input from the user."
            <- {caring about another person's happiness}
                ...: "caring about another person's happiness (as given by the user)."
                ?: Is caring a primitive input?
                <= :>:{caring about another person's happiness}?()
                    /: "Caring is a primitive input from the user."
    <- <can be between various entities>
        ...: "This deep feeling can be between partners, family, friends, or even spiritual connections."
        ?: How can this deep feeling exist between various entities? (Judgement Request)
        <= ::<{deep feeling} exists between {entities}>
        <- {entities}
            ...: "partners, family, friends, or even spiritual connections (as given by the user)."
            ?: What are the entities?
            <= &across
                /: "The entities are a sequence of partners, family, friends, and spiritual connections."
            <- {partners}
                ...: "partners (as given by the user)."
                ?: Are partners a primitive input?
                <= :>:{partners}?()
                    /: "Partners are a primitive input from the user."
            <- {family}
                ...: "family (as given by the user)."
                ?: Is family a primitive input?
                <= :>:{family}?()
                    /: "Family is a primitive input from the user."
            <- {friends}
                ...: "friends (as given by the user)."
                ?: Are friends a primitive input?
                <= :>:{friends}?()
                    /: "Friends are a primitive input from the user."
            <- {spiritual connections}
                ...: "spiritual connections (as given by the user)."
                ?: Are spiritual connections a primitive input?
                <= :>:{spiritual connections}?()
                    /: "Spiritual connections are a primitive input from the user."
    <- <means acceptance and wanting happiness>
        ...: "This deep feeling means accepting someone and wanting them to be happy, even when it's hard."
        ?: How does this deep feeling manifest its meaning? (Judgement Request)
        <= ::<{deep feeling} means meaning>
            ...: "accepting someone and wanting them to be happy, even when it's hard."
            ?: How is this meaning judged?
            <= @by(:_:)^({deep feeling})
                /: "The judgement is determined by a specific method."
            <- :_:{judgement breakdown}()
                /: "The method is a bounded process named 'judgement breakdown'."
            <- {judgement breakdown}
                ...: "The breakdown consists of a true scenario, a false scenario, and the condition that distinguishes them."
                ?: What is the composition of the judgement broken down?
                <= &across
                    /: "It is an ordered composition of the scenarios and the underlying condition."
                <- {true scenario action}
                    ...: "the true scenario is accepting someone and wanting them to be happy, even when it's hard"
                    ?: What is the action in the true scenario? (Nominalization)
                    <= $::
                        ...: "It is a nominalized action to output TRUE, conditional on the acceptance and wanting happiness."
                        ?: When is this action performed?
                        <= @if(<accepting someone and wanting them to be happy, even if it is hard>)
                            /: "This action executes only if the condition is met."
                        <- <accepting someone and wanting them to be happy, even if it is hard>
                    <- :<:(<%(TRUE)>)
                        /: The action is to output True in the true scenario.
                <- {false scenario action}
                    ...: "the false scenario is not accepting someone and wanting them to be happy, even when it's hard"
                    ?: What is the action in the false scenario? (Nominalization)
                    <= $::
                        ...: "It is a nominalized action to output FALSE, conditional on the lack of acceptance and wanting happiness."
                        ?: When is this action performed?
                        <= @if!(<accepting someone and wanting them to be happy, even if it is hard>)
                            /: "This action executes only if the condition is not met."
                        <- <accepting someone and wanting them to be happy, even if it is hard>
                    <- :<:(<%(FALSE)>)
                        /: The action is to output False in the false scenario.
                <- <accepting someone and wanting them to be happy, even if it is hard>
                    ...: "The condition is about accepting someone and wanting them to be happy, even when it's hard."
                    ?: How is this condition evaluated? (Judgement Request)
                    <= ::<accepting {someone} and wanting {them} to be happy, even if it is hard>
                        /: "It's a judgement that evaluates the act of accepting someone and wanting them to be happy."
                    <- {someone or something}
                    <- {deep feeling}
    <- <is a dual concept>
        ...: "This deep feeling is both an emotion and a decision to put someone else's wellbeing first."
        ?: How does this deep feeling manifest its nature? (Judgement Request)
        <= ::<{deep feeling} has a dual nature of {emotion} and {decision}>
            /: This deep feeling has a dual nature of being an emotion and a decision.
        <- {emotion}
            ...: "an emotion of wanting someone else's wellbeing first. (as given by the user)"
            ?: What is this emotion?
            <= $:.({emotion})
                ...: "it is emotion under the condition of wanting someone else's wellbeing first"
            ?: When is it this emotion?
            <= @if(<emotion is wanting someone else's wellbeing first>)
                /: "It is this emotion only if it is about wanting someone else's wellbeing first."
            <- {emotion}
                ...: "the raw emotion (given by the user)"
                ?: Is the raw emotion a primitive input?
                <= :>:{emotion}?()
                    /: "The raw emotion is a primitive input from the user."
            <- <emotion is wanting someone else's wellbeing first>
                ...: "the raw emotion is wanting someone else's wellbeing first"
                ?: Is the emotion about wanting wellbeing? (Judgement Request)
                <= ::<{emotion} is wanting {someone else}'s wellbeing>
                    /: "It's a judgement on whether the emotion is about the other's wellbeing."
                <- {someone or something}
                <- {emotion}
        <- {decision}
            ...: "a decision to put someone else's wellbeing first. (as given by the user)"
            ?: What is this decision?
            <= $:.({decision})
                ...: "it is decision under the condition of putting someone else's wellbeing first"
            ?: When is it this decision?
            <= @if(<decision is putting someone else's wellbeing first>)
                /: "It is this decision only if it is about wanting someone else's wellbeing first."
            <- {decision}
                ...: "the raw decision (given by the user)"
                ?: Is the raw decision a primitive input?
                <= :>:{decision}?()
                    /: "The raw decision is a primitive input from the user."
            <- <decision is putting someone else's wellbeing first>
                ...: "the raw decision is putting someone else's wellbeing first"
                ?: Is the decision about putting wellbeing first? (Judgement Request)
                <= ::<{decision} is putting {someone else}'s wellbeing first>
                    /: "It's a judgement on whether the decision is about the other's wellbeing."
                <- {someone or something}
                <- {decision}
```