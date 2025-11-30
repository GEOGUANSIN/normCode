
import re

def clean_val(val):
    """Extract value from formatted strings like '%5d3(9)' -> '9'"""
    if isinstance(val, str):
        # Match (content) at the end of string
        match = re.search(r'\((.*?)\)$', val)
        if match:
            return match.group(1)
    return val

# The runner injects variables based on the concept mapping. 
# {1} maps to input_1.
# The runner also expects 'result' variable to be set.

try:
    val = input_1
except NameError:
    val = None
    
print(f"DEBUG: Script running with input_1={val} (type: {type(val)})")

if val is None:
    result = ""
else:
    # The MVP step converts the reference to a human-readable string like "9, 9, and 2"
    # We need to parse this back into individual digits
    digits = []
    if isinstance(val, str):
        # Handle formatted strings like "9, 9, and 2" or "9, 9, 2"
        # Split by comma and clean up each part
        parts = re.split(r',\s*(?:and\s+)?', val)
        for part in parts:
            part = part.strip()
            if part:
                # If part is a formatted string like '%5d3(9)', extract the digit
                cleaned = clean_val(part)
                if cleaned:
                    digits.append(str(cleaned))
    elif isinstance(val, list):
        # If it's already a list, clean each element
        cleaned = [clean_val(d) for d in val if d]
        digits = [str(d) for d in cleaned]
    else:
        # Single value
        digits = [str(clean_val(val))]
    
    # IMPORTANT: Reverse the digits before combining
    # Digits come in reverse order (units first, tens, hundreds, etc.)
    # but to form the final number we need them in correct positional order
    digits.reverse()
    result = "".join(digits)
