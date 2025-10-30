:<:(::(Create a verifiable multi-agent system from normtext)) | 1. methodology
    <= @by(:_:)
    <- :_:{NormCode Methodology}({input normtext})
    <- {NormCode Methodology} | 1.1. grouping
        <= &across
        <- {Phase 1: Blueprinting} | 1.1.1. nominalization
            <= $::
            <- ::(Translate normtext to NormCode plan) | 1.1.1.1. imperative
                <= ::(Decompose concepts until no un-parsed text remains)
                <- {normtext}
                <- {normcode plan}?
        <- {Phase 2: Compilation} | 1.1.2. nominalization
            <= $::
            <- ::(Generate source code from NormCode plan) | 1.1.2.1. grouping
                <= &across
                <- {agent and tool specification} | 1.1.2.1.1. imperative
                    <= ::(Scan plan for functional concepts to define agent roles and tools)
                    <- {normcode plan}
                    <- {agent and tool specification}?
                <- {state specification} | 1.1.2.1.2. imperative
                    <= ::(Scan plan for object concepts to define state variables)
                    <- {normcode plan}
                    <- {state specification}?
                <- {system source code} | 1.1.2.1.3. imperative
                    <= ::(Generate agent scaffolds and controller logic)
                    <- {agent and tool specification}
                    <- {state specification}
                    <- {normcode plan}
                    <- {system source code}?
        <- {Phase 3: Execution & Verification} | 1.1.3. nominalization
            <= $::
            <- ::(Execute system and capture trace) | 1.1.3.1. imperative
                <= ::(Run the generated system with input data and capture the ExecutionState output)
                <- {system source code}
                <- {input data}
                <- {execution trace}?
    <- {input normtext} | 1.2. io
        <= :>:{input normtext}?()
```