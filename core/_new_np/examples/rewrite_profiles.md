
### Profiles


####Instruction Set for Profile 1: The Approachable Tech Evangelist
*Transform technical concepts into relatable ideas using everyday analogies. Maintain a conversational rhythm with contractions, encouraging phrases, and sentences under 25 words. Use strategic emphasis through exclamations and occasional emojis. Replace jargon with plain alternatives, frame benefits as personal wins, and end with an uplifting call-to-action.*

With examples: 
*"When rewriting content for this voice, transform technical details into relatable concepts using everyday analogies (e.g., 'like a digital safe'). Maintain a conversational rhythm with contractions ('you'll', 'we've'), sprinkle in encouraging phrases ('you've got this!'), and keep sentences under 25 words. Use strategic emphasis through exclamations ('Game-changer!') and occasional emojis (🚀) to amplify excitement. Replace jargon with friendly alternatives ('extra security steps' instead of 'MFA'), and always frame benefits as personal wins ('This saves YOU time'). End with an uplifting call-to-action that makes readers feel capable."*

NormCode for instruction:

```
{new_content}
    <= $.({content}?)
    <- {content}
    <- :S:(rewrite {1}<$({content})%_> for profile 1)
        <= @by^({content}:{content})
        <- {6 steps}
            <= &across[{step 1}:_,{step 2}:_,{step 3}:_,{step 4}:_,{step 5}:_,{step 6}:_]^({content}:{content})
            <- {step 1}
                <= $::^({content}:{content}) 
                <- :S:(transform {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_> using {3}?<$({everyday_analogies})%_>)
                <- {technical_concepts}<:{1}>
                    <= $.({technical_concepts}?)^({content}:{content})
                    <- :S:({1}?<$({technical_concepts})%_> from {2}<$({content})%_>)
                    <- {technical_concepts}?<:{1}> 
                    <- {content}<:{2}>
                <- {relatable_ideas}?<:{3}>
                <- {everyday_analogies}?<:{4}>
                <- {content}<:{2}>
            <- {step 2}
                <= $::^({content}:{content})  
                <- ::(maintain {1}<$({conversational_rhythm})%_> with {2}<$({contractions})%_>, {3}<$({encouraging_phrases})%_>, and {4}<$({short_sentences})%_>)
                <- {conversational_rhythm}<:{1}>
                <- {contractions}<:{2}>
                <- {encouraging_phrases}<:{3}>
                <- {short_sentences}<:{4}>
            <- {step 3}
                <= $::
                <- ::(use {1}<$({strategic_emphasis})%_> through {2}<$({exclamations})%_> and {3}<$({occasional_emojis})%_>)
                <- {strategic_emphasis}<:{1}>
                <- {exclamations}<:{2}>
                <- {occasional_emojis}<:{3}>
            <- {step 4}
                <= $::  
                <- ::(frame {1}<$({benefits})%_> as {2}<$({personal_wins})%_>)
                <- {benefits}<:{1}>
                <- {personal_wins}<:{2}>
            <- {step 5}
                <= $::
                <- ::(replace {1}<$({jargon})%_> with {2}<$({plain_alternatives})%_>)
                <- {jargon}<:{1}>
                <- {plain_alternatives}<:{2}>
            <- {step 6}
                <= $::
                <- ::(end with {1}<$({uplifting_call_to_action})%_>)
                <- {uplifting_call_to_action}<:{1}>
```


####Instruction Set for Profile 2: The Precision-Focused Engineer
*Preserve technical accuracy while optimizing clarity. Use industry-standard terms precisely, passive voice for system behaviors, and qualified statements where appropriate. Structure complex information logically with consistent sentence lengths. Employ subtle dry humor sparingly through understatement. Avoid exaggeration; replace subjective claims with measurable statements. Prioritize factual completeness and acknowledge limitations explicitly.*

With examples: 
*"For this rewrite, preserve all technical accuracy while optimizing for clarity. Use industry-standard terms precisely ('256-bit encryption'), passive voice for system behaviors ('data is encrypted'), and qualified statements where appropriate ('in 90% of use cases'). Structure complex information with logical connectors ('therefore', 'consequently') and maintain consistent sentence lengths (15-20 words). Employ subtle dry humor sparingly through understatement ('surprisingly painless'). Avoid exaggeration—replace marketing terms like 'revolutionary' with measurable claims ('3x faster processing'). Prioritize factual completeness over persuasion, explicitly noting limitations where relevant."*

NormCode for instruction:





### Example Focus 

```
:NormCode:({1}<$(:_:)%_> has {2}<${content}%_> in the awared workspace for {3}<$({control}%_)>)
    <- ({agent}<$(:S_read_content:)%_>)<:{1}>
    <- {content}<:{2}>
    <- {read}<:{3}>

:NormCode:({1}<$(:_:)%_> has {2}<${content}%_> in the awared workspace for {3}<$({control}%_)>)
    <- ({agent}<$(:S_write_content:)%_>)<:{1}>
    <- {content}<:{2}>
    <- {read and write}<:{3}>
```

```
{step 1}
    <= $::
    <- :S_write_content:(transform {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_>)
    <- [all {technical_concepts}<:{1}> and {relatable_ideas}<:{2}>]
        <= &in({technical_concepts}:{technical_concepts}; {relatable_ideas}:{technical_concepts})
        <- {technical_concepts}
        <- {relatable_ideas}
            <= ::(make {1}<$({technical_concepts})%_> into {2}?<$({relatable_ideas})%_> using everyday analogies)
            <- {technical_concepts}<:{1}>
                <= :S_read_content:({1}?<$({technical_concepts})%_>)
                <- {technical_concepts}?<:{1}>
            <- {relatable_ideas}?<:{2}>
```