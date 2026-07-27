# Import Core Libraries
# from typing import cast

# Check if string is float
def isfloat(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False

# Check if string is int
def isint(text: str) -> bool:
    try:
        int(text)
        return True
    except ValueError:
        return False

# Convert to Float if valid Number, otherwise return None
def float_or_none(text: str | None) -> float | None:
    if text is None:
        return None
    else:
        try:
            return float(text)
        except ValueError:
            return None

# Convert to Int if valid Number, otherwise return None
def int_or_none(text: str | None) -> float | None:
    if text is None:
        return None
    else:
        try:
            return int(text)
        except ValueError:
            return None
