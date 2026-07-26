# Check if string is float
def isfloat(text):
    try:
        float(text)
        return True
    except ValueError:
        return False

# Check if string is int
def isint(text):
    try:
        int(text)
        return True
    except ValueError:
        return False
