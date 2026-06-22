def calculate_balance(transactions):
    """Calculate total balance."""
    total = 0.0
    for t in transactions:
        total += t[1]
    return total


def average_spending(transactions):
    """Calculate average transaction amount."""
    if not transactions:
        return 0.0
    total = sum(t[1] for t in transactions)
    return total / len(transactions)


def total_by_category(transactions):
    """Sum amounts grouped by category."""
    result = {}
    for t in transactions:
        category = t[2]
        result[category] = result.get(category, 0) + t[1]
    return result
