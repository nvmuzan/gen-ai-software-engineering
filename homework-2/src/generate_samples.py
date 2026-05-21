"""Script to generate sample data files for testing."""
import csv
import json
import random
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

CATEGORIES = ["account_access", "technical_issue", "billing_question", "feature_request", "bug_report", "other"]
PRIORITIES = ["urgent", "high", "medium", "low"]
STATUSES = ["new", "in_progress", "waiting_customer", "resolved", "closed"]
SOURCES = ["web_form", "email", "api", "chat", "phone"]
DEVICES = ["desktop", "mobile", "tablet"]
BROWSERS = ["Chrome", "Firefox", "Safari", "Edge", None]

SUBJECTS_MAP = {
    "account_access": ["Can't login to my account", "Password reset not working", "2FA issue", "Account locked"],
    "technical_issue": ["App crashes on startup", "Getting 500 error", "Page not loading", "Slow performance"],
    "billing_question": ["Invoice not received", "Incorrect charge on my account", "Refund request", "Subscription price question"],
    "feature_request": ["Please add dark mode", "Would be nice to have export feature", "Suggestion: add API access"],
    "bug_report": ["Button not clickable — steps to reproduce", "Regression in v2.3", "Stack trace attached"],
    "other": ["General feedback", "Question about terms", "Partnership inquiry"],
}

DESCRIPTIONS_MAP = {
    "account_access": [
        "I cannot log into my account. I've tried resetting the password but the reset email never arrives.",
        "My account seems to be locked. I get 'access denied' every time I try to sign in.",
        "Two-factor authentication stopped working after I got a new phone.",
    ],
    "technical_issue": [
        "The application crashes every time I open the dashboard. This is a critical issue affecting my workflow.",
        "I'm getting a 500 Internal Server Error when submitting the contact form.",
        "The page loads very slowly — it takes over 30 seconds which is completely unusable.",
    ],
    "billing_question": [
        "I was charged twice this month for my subscription. Please refund the duplicate charge.",
        "I haven't received my invoice for last month. I need it for accounting purposes.",
        "Could you explain why my plan price increased without any notification?",
    ],
    "feature_request": [
        "It would be really nice to have a dark mode option. Many users have requested this.",
        "Please add the ability to export data to CSV. This would greatly improve our workflow.",
        "Suggestion: add keyboard shortcuts for common actions.",
    ],
    "bug_report": [
        "Steps to reproduce: 1) Open settings 2) Click Save 3) Error appears. Expected: settings saved. Actual: error 400.",
        "After the v2.3 update the search functionality stopped working. This is a clear regression.",
    ],
    "other": [
        "I have a general question about your terms of service regarding data retention.",
        "I'm interested in exploring a partnership opportunity with your team.",
    ],
}


def random_date(days_back=90):
    return (datetime.utcnow() - timedelta(days=random.randint(0, days_back))).isoformat()


def make_ticket(idx: int) -> dict:
    cat = random.choice(CATEGORIES)
    subjects = SUBJECTS_MAP[cat]
    descriptions = DESCRIPTIONS_MAP[cat]
    return {
        "id": str(uuid.uuid4()),
        "customer_id": f"CUST-{1000 + idx}",
        "customer_email": f"user{idx}@example.com",
        "customer_name": f"User {idx}",
        "subject": random.choice(subjects),
        "description": random.choice(descriptions),
        "category": cat,
        "priority": random.choice(PRIORITIES),
        "status": random.choice(STATUSES),
        "created_at": random_date(),
        "updated_at": random_date(30),
        "resolved_at": None,
        "assigned_to": random.choice([None, "agent1", "agent2", "agent3"]),
        "tags": random.sample(["billing", "urgent", "vip", "bug", "ux", "api"], k=random.randint(0, 3)),
        "metadata": {
            "source": random.choice(SOURCES),
            "browser": random.choice(BROWSERS),
            "device_type": random.choice(DEVICES),
        },
    }


def generate_json(n=20, path="sample_tickets.json"):
    tickets = [make_ticket(i) for i in range(1, n + 1)]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2, default=str)
    print(f"Generated {path} ({n} tickets)")


def generate_csv(n=50, path="sample_tickets.csv"):
    tickets = [make_ticket(i) for i in range(1, n + 1)]
    fieldnames = [
        "customer_id", "customer_email", "customer_name", "subject", "description",
        "category", "priority", "status", "assigned_to", "tags", "metadata",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in tickets:
            row = {k: t.get(k, "") for k in fieldnames}
            row["tags"] = json.dumps(t["tags"])
            row["metadata"] = json.dumps(t["metadata"])
            writer.writerow(row)
    print(f"Generated {path} ({n} tickets)")


def generate_xml(n=30, path="sample_tickets.xml"):
    root = ET.Element("tickets")
    for i in range(1, n + 1):
        t = make_ticket(i)
        elem = ET.SubElement(root, "ticket")
        simple_fields = ["customer_id", "customer_email", "customer_name", "subject",
                         "description", "category", "priority", "status", "assigned_to"]
        for field in simple_fields:
            child = ET.SubElement(elem, field)
            child.text = str(t[field]) if t[field] is not None else ""
        tags_elem = ET.SubElement(elem, "tags")
        for tag in t["tags"]:
            tag_elem = ET.SubElement(tags_elem, "tag")
            tag_elem.text = tag
        meta_elem = ET.SubElement(elem, "metadata")
        for k, v in t["metadata"].items():
            c = ET.SubElement(meta_elem, k)
            c.text = str(v) if v else ""
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="unicode", xml_declaration=True)
    print(f"Generated {path} ({n} tickets)")


def generate_invalid_files():
    with open("invalid_tickets.json", "w") as f:
        f.write('[{"customer_id": "X", "customer_email": "not-an-email", "subject": "hi", "description": "short"}]')
    with open("invalid_tickets.csv", "w") as f:
        f.write("customer_id,customer_email,subject\nBAD,not-email,too short\n")
    with open("invalid_tickets.xml", "w") as f:
        f.write("<tickets><ticket><customer_id>X</customer_id></ticket></tickets>")
    with open("malformed.json", "w") as f:
        f.write("{not valid json")
    with open("malformed.xml", "w") as f:
        f.write("<unclosed>")
    print("Generated invalid/malformed files")


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/../")
    generate_json(20, "sample_tickets.json")
    generate_csv(50, "sample_tickets.csv")
    generate_xml(30, "sample_tickets.xml")
    generate_invalid_files()
