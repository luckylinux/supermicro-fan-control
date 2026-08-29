# Import Core Libraries
from typing import Any

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

class NestDict(dict):
    # Override get Method
    def get(self,
        key: Any,
        default: Any = None
        ) -> Any:

        print(f"Get Nest Dictionary Element {key}", flush=True)

        key_parts = key.split("/")

        # Initialize Value
        value = self

        for id, item in enumerate(key_parts):
            if id == len(key_parts) - 1:
                value = value.get(item, default)
            else:
                value = value.get(item, {})

        # Return Value
        return value
