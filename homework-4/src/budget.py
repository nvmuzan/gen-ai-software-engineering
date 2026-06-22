import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import init_db, add_transaction, get_all_transactions, search_transactions
from calculator import calculate_balance, average_spending, total_by_category


def cmd_add(args):
    if len(args) < 3:
        print("Usage: budget.py add <amount> <category> <description>")
        sys.exit(1)
    amount = float(args[0])
    category = args[1]
    description = " ".join(args[2:])
    add_transaction(amount, category, description)
    print(f"Added: {amount:.2f} | {category} | {description}")


def cmd_list(args):
    transactions = get_all_transactions()
    if not transactions:
        print("No transactions found.")
        return
    print(f"{'ID':<5} {'Amount':>10} {'Category':<15} {'Description':<30} Date")
    print("-" * 75)
    for t in transactions:
        print(f"{t[0]:<5} {t[1]:>10.2f} {t[2]:<15} {t[3]:<30} {t[4]}")


def cmd_search(args):
    if not args:
        print("Usage: budget.py search <keyword>")
        sys.exit(1)
    keyword = " ".join(args)
    results = search_transactions(keyword)
    if not results:
        print(f"No transactions matching '{keyword}'.")
        return
    for t in results:
        print(f"{t[0]}: {t[1]:.2f} | {t[2]} | {t[3]}")


def cmd_summary(args):
    transactions = get_all_transactions()
    balance = calculate_balance(transactions)
    avg = average_spending(transactions)
    by_cat = total_by_category(transactions)
    print(f"Balance:  {balance:.2f}")
    print(f"Average:  {avg:.2f}")
    print("By category:")
    for cat, total in by_cat.items():
        print(f"  {cat}: {total:.2f}")


COMMANDS = {"add": cmd_add, "list": cmd_list, "search": cmd_search, "summary": cmd_summary}


def main():
    init_db()
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: budget.py <command> [args]")
        print("Commands:", ", ".join(COMMANDS))
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
