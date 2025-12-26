# Session Termination Judgement

Determine whether the user wants to end the current canvas session.

## Input

**Current Message**: {1}

**Conversation History**: {2}

## Termination Signals

Return **True** if the user's message indicates they want to end the session:

### Explicit Termination
- "quit", "exit", "bye", "goodbye"
- "I'm done", "that's all", "finished"
- "end session", "close", "stop"
- "thanks, bye", "thank you, goodbye"
- Commands classified as "quit" or "exit"

### Implicit Termination
- User says "see you later", "gotta go"
- User indicates they're leaving: "heading out", "signing off"
- Farewell expressions in any language

## Non-Termination Signals

Return **False** if:

- User is asking questions
- User is giving commands (even if frustrated)
- User says "stop" but means stop execution, not end session
- User is making conversation
- Message is ambiguous - default to continuing

## Examples

| Message | Result | Reasoning |
|---------|--------|-----------|
| "quit" | True | Explicit termination command |
| "I'm done for today, thanks!" | True | Clear session end intent |
| "bye!" | True | Farewell |
| "stop the execution" | False | Stopping execution, not session |
| "delete that node" | False | Active command |
| "this is frustrating" | False | Expressing emotion, not leaving |
| "what does this node do?" | False | Asking question |
| "ok thanks" | False | Acknowledgment, not farewell |
| "thanks, that's all I needed" | True | Indicates completion |

## Output

Return a single boolean value:
- `true` - User wants to end the session
- `false` - User wants to continue

Consider the conversation history for context - a "thanks" after completing a task might signal end, while "thanks" mid-conversation does not.

