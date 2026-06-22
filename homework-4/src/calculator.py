def calculate_balance(transactions):
    """Calculate total balance. BUG-002: skips first transaction."""
    total = 0.0
    for t in transactions[1:]:  # BUG-002: off-by-one, skips transactions[0]
        total += t[1]
    return total


def average_spending(transactions):
    """Calculate average transaction amount. BUG-001: division by zero."""
    total = sum(t[1] for t in transactions)
    return total / len(transactions)  # BUG-001: ZeroDivisionError when empty


def total_by_category(transactions):
    """Sum amounts grouped by category."""
    result = {}
    for t in transactions:
        category = t[2]
        result[category] = result.get(category, 0) + t[1]
    return result
