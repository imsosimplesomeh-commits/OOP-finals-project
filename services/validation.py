from math import isfinite


def required(value, name):
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"{name} is required.")
    return value


def positive_integer(value, name):
    try:
        result = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a positive whole number.") from None
    if result <= 0:
        raise ValueError(f"{name} must be a positive whole number.")
    return result


def number(value, name):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Enter a number for {name.lower()}.") from None
    if not isfinite(result):
        raise ValueError(f"Enter a finite number for {name.lower()}.")
    return result
