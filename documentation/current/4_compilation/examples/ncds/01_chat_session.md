# Example 01: Chat Session Controller

**Status**: ✅ Working (verified against `canvas_app/compiler/repos/`)

---

## Natural Language Instruction

```
Build a chat session controller that:

1. Waits for the user to send a message
2. Parses the message to understand what canvas command they want
3. Executes the canvas command and gets the result status
4. Generates a helpful response based on the message and command result
5. Sends the response back to the user
6. Checks if the user wants to end the session
7. If not ending, adds the message to history and waits for the next message
8. Repeats until the user wants to end
9. Returns the collection of all interaction statuses
```

---

## Derived `.ncds`

```ncds
/: Chat Session Controller
/: A self-seeding loop that handles user messages until termination

<- session result
    <= select all canvas statuses as final result
    
    <- on-going messages
        <= initialize to empty list
    
    <- all canvas statuses
        <= for every on-going message
        
            <= return the canvas status per iteration
            
            <- canvas status
                <= bundle the message, command status, and response sent together
                
                <- current message
                    <= read user input (blocks until received)
                
                <- command status
                    <= execute the canvas command based on parsed intent
                    <- parsed command
                        <= understand the user message as a canvas command
                        <- current message
                        <- canvas command schema
                
                <- response sent
                    <= send the response message to the user
                    <- response
                        <= generate a helpful response for the user
                        <- current message
                        <- command status
            
            <- session should end?
                <= judge if the user wants to end the session
                <- current message
                <- command status
                <- on-going messages
            
            <- on-going messages
                <= append current message to collection
                    <= if session should NOT end
                    <* session should end?
                <- current message
                <- on-going messages
        
        <- on-going messages
        <* message in on-going messages
```

---

## Key Patterns Demonstrated

### 1. Self-Seeding Loop
The loop starts with an empty `[on-going messages]` but runs once anyway due to `start_without_value_only_once=True`. The first iteration creates the first item to append.

### 2. Blocking I/O Within Loop
`<= read user input` blocks the entire iteration until the user sends a message. This creates natural "wait for user" behavior.

### 3. Conditional Append for Termination
Instead of an explicit "break", the append is gated by a timing condition:
```ncds
<= append current message to collection
    <= if session should NOT end    /: @:! timing gate
    <* session should end?          /: condition context
```
When append is blocked → no new work → loop ends naturally.

### 4. Grouped Result Per Iteration
Each iteration bundles its components together:
```ncds
<- canvas status
    <= bundle the message, command status, and response sent together
    <- current message
    <- command status
    <- response sent
```

### 5. Judgement for Control Flow
```ncds
<- session should end?
    <= judge if the user wants to end the session
```
Returns a boolean proposition used to control the append timing.

---

## Corresponding Formal Structure

After formalization, this becomes (abbreviated):

| Flow Index | Concept | Sequence |
|------------|---------|----------|
| `1` | `{session result}` | assigning (`$.`) |
| `1.2` | `[on-going messages]` | assigning (`$%`) |
| `1.3` | `[all canvas statuses]` | looping (`*.`) |
| `1.3.1` | loop body | assigning (`$.`) |
| `1.3.1.2` | `{canvas status}` | grouping (`&[{}]`) |
| `1.3.1.2.3` | `{command status}` | imperative |
| `1.3.1.2.3.2` | `{parsed command}` | imperative |
| `1.3.1.2.3.2.2` | `{current message}` | imperative (`:>:`) |
| `1.3.1.2.4` | `{response sent}` | imperative |
| `1.3.1.2.4.2` | `{response}` | imperative |
| `1.3.1.3` | `<session should end>` | judgement |
| `1.3.1.4` | `[on-going messages]` | assigning (`$+`) |
| `1.3.1.4.1` | timing gate | timing (`@:!`) |

---

## Body Faculties Used

| Operation | Faculty | Paradigm |
|-----------|---------|----------|
| Read user input | `chat` | `c_ChatRead-o_Literal` |
| Understand command | `llm` | `h_Memo-v_Prompt-c_LLMGenerate-o_Command` |
| Execute command | `canvas` | `h_Command-c_CanvasExecute-o_Status` |
| Generate response | `llm` | `h_Message_Status-v_Prompt-c_LLMGenerate-o_Memo` |
| Send response | `chat` | `h_Response-c_ChatWrite-o_Status` |
| Judge termination | `llm` | `h_Memo-v_Prompt-c_LLMGenerate-o_Truth` |

---

## Files

- **Source repos**: `canvas_app/compiler/repos/chat.concept.json`, `chat.inference.json`
- **Paradigms**: `canvas_app/compiler/provisions/paradigms/`
- **Prompts**: `canvas_app/compiler/provisions/prompts/`

