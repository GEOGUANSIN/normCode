def get_unit_place_digit(number: int) -> int:
    """Extracts the unit place digit from a number."""
    return number % 10


def remove_last_digit_from_number(number: int) -> int:
    """Removes the last digit from a number. Returns 0 if the number is a single digit."""
    if number < 10:
        return 0
    return number // 10
