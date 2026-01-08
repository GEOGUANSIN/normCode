# Parse Step Summary Script

## Overview

This script parses orchestrator log files to extract:
- **MFP Step Names**: Model Function Perception concept names (from Concept Name field in Function section of "States after MFP")
- **MVP Values**: Memory Value Perception values (from Reference Tensor in Values section)
- **OR Outputs**: Output Reference outputs (from Reference Tensor in Inference section)

Only processes sequences that are **judgement** or **imperative** related.

## Usage

```bash
python parse_step_summary.py <log_file> [options]
```

### Options

- `-o, --output PATH`: Output file path (default: `<log_file>_summary.md`)
- `-f, --format FORMAT`: Output format - `markdown` or `json` (default: `markdown`)
- `--no-stats`: Skip statistics section in output

### Examples

```bash
# Generate markdown summary (default)
python parse_step_summary.py orchestrator_log_20251105_211435.txt

# Generate JSON summary
python parse_step_summary.py orchestrator_log_20251105_211435.txt -f json

# Specify output file
python parse_step_summary.py orchestrator_log_20251105_211435.txt -o my_summary.md
```

## Output Format

### Markdown Format

The markdown output includes:
- Summary header with total sequences found
- **Statistics section** (unless `--no-stats` is used):
  - Total sequences and breakdown by type
  - Data coverage percentages (MFP, MVP, OR, Complete)
  - Timeline information (first/last timestamps, total duration)
- For each sequence:
  - Sequence type and number
  - Timestamp
  - MFP Step Name (if found)
  - MVP Values (if found)
  - OR Output (if found)

### JSON Format

The JSON output (when statistics are included) is an object containing:
```json
{
  "statistics": {
    "total_sequences": 9,
    "by_type": {"IMPERATIVE INPUT": 1, "IMPERATIVE DIRECT": 7, ...},
    "mfp_coverage": 100.0,
    "mvp_coverage": 44.4,
    "or_coverage": 100.0,
    ...
  },
  "sequences": [
    {
      "sequence_type": "IMPERATIVE INPUT",
      "sequence_number": 1,
      "timestamp": "2025-11-05 21:14:35,461",
      "mfp_name": ":>:({prompt}<:{normtext}>)",
      "mvp_values": "[{'prompt_text': '...'}]",
      "or_output": "['%7e5(...)']"
    },
    ...
  ]
}
```

If `--no-stats` is used, the JSON output is a simple array of sequence objects (without the statistics wrapper).

## Sequence Detection

The script identifies sequences as judgement/imperative related if the sequence name contains:
- `judgement` or `judgment`
- `imperative`

## Extraction Details

### MFP Step Names
- **Primary Source**: Extracted from the `Concept Name` field in the `Function` section of "States after MFP" logs
- **Format**: Concept names like `::{%(direct)}({prompt}<$({initialization prompt})%>: initialize normcode draft)`
- **Fallback**: If no Concept Name is found in MFP's Function section, the script uses the Function concept name from the preceding IR (Input References) step
- **Example**: For imperative_input sequences, it may use `:>:({prompt}<:{normtext}>)` from the IR step

### MVP Values
- Extracted from the `Reference Tensor` line in the `Values` section of "States after MVP" logs
- Typically contains prompt templates or input data as dictionaries or lists

### OR Outputs
- Extracted from the `Reference Tensor` line in the `Inference` section of "States after OR" logs
- Contains the final output references, often in wrapped format (e.g., `%7e5(...)` or `%f11(...)`)

## Notes

- Long values are truncated in markdown output (2000 characters) for readability
- Empty sections (missing MFP, MVP, or OR data) are omitted from the output
- The script processes sequences in order and maintains sequence numbers for each sequence type
- Statistics are included by default but can be disabled with `--no-stats` flag
- Console output includes a summary of statistics when processing completes

