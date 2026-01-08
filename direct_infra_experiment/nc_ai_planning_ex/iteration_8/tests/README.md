# Derivation Algorithm Test Suite

This directory contains test cases for the NormCode Derivation Algorithm.

## Test Cases

| Test | Pattern | Description | Tests Phase |
|------|---------|-------------|-------------|
| `test_01_linear_chain` | Linear | Filter + Average calculation | Basic extraction |
| `test_02_multi_input` | Multi-Input | Combine two data sources | Multiple inputs |
| `test_03_iteration` | Iteration | Process each image in folder | Loop patterns (`<*`) |
| `test_04_conditional` | Conditional | Email validation with if/else | Conditional branching |
| `test_05_branching` | Parallel | Multiple analyses in parallel | Sibling operations |
| `test_06_grouping` | Grouping | Bundle metrics into report | Collection patterns |
| `test_07_vague_instruction` | Vague | Minimal instruction | Phase 1 refinement |
| `test_08_nested_iteration` | Nested Loop | Language pair matrix | Nested `<*` patterns |

## Running a Test

1. **Copy the test's `inputs.json`** to `repos/inputs.json`:
   ```powershell
   Copy-Item tests/inputs_test_01.json repos/inputs.json
   ```

2. **Clear previous checkpoints**:
   ```powershell
   Remove-Item progress.txt, 1_*.txt, 2_*.json, 3_*.json, 4_*.json, ncds_output.ncds -ErrorAction SilentlyContinue
   ```

3. **Run the canvas app** and execute the derivation plan

4. **Check output** in `ncds_output.ncds`

## Expected Patterns in Output

### Linear Chain (test_01)
```ncds
<- {average}
    <= calculate the average
    <- {filtered numbers}
        <= filter out negative numbers
        <- {list of numbers}
```

### Multi-Input (test_02)
```ncds
<- {comprehensive report}
    <= generate report
    <- {merged data}
        <= merge data
        <- {sales data}
        <- {customer feedback}
```

### Iteration (test_03)
```ncds
<- {extracted text files}
    <= for each image
    <- {extracted text}
        <= apply OCR
        <- {image}
    <* {images}
```

### Conditional (test_04)
```ncds
<- {result}
    <= select valid option
    <- {success result}
        <= create account and send email
        <* <email is valid>
    <- {error result}
        <= return error
        <* <email is valid>
```

### Branching/Parallel (test_05)
```ncds
<- {document profile}
    <= combine analyses
    <- {topics}
        <= extract topics
        <- {document}
    <- {sentiment}
        <= analyze sentiment
        <- {document}
    <- {entities}
        <= identify entities
        <- {document}
```

### Grouping (test_06)
```ncds
<- {system health report}
    <= bundle metrics
    <- {cpu usage}
    <- {memory usage}
    <- {disk space}
    <- {network status}
```

## Test Validation

For each test, verify:
1. ✅ All concepts from instruction appear in output
2. ✅ All operations are represented
3. ✅ Dependency order is correct (bottom-up reading)
4. ✅ Ground concepts are properly marked
5. ✅ Control patterns (`<*`) are used appropriately

