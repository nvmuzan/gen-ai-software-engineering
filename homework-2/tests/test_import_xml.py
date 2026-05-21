"""Tests for XML import — 5 tests."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from importers import import_xml

VALID_XML = b"""<?xml version="1.0" ?>
<tickets>
  <ticket>
    <customer_id>CUST-1</customer_id>
    <customer_email>alice@example.com</customer_email>
    <customer_name>Alice</customer_name>
    <subject>Login issue</subject>
    <description>Cannot login for the past two days no matter what I try with my credentials.</description>
    <category>account_access</category>
    <priority>high</priority>
    <status>new</status>
    <assigned_to></assigned_to>
    <tags><tag>urgent</tag></tags>
    <metadata><source>web_form</source><device_type>desktop</device_type></metadata>
  </ticket>
</tickets>
"""

INVALID_XML = b"<unclosed>"

MISSING_FIELDS_XML = b"""<tickets><ticket><customer_id>X</customer_id></ticket></tickets>"""


def test_xml_valid_import():
    tickets, errors = import_xml(VALID_XML)
    assert len(tickets) == 1
    assert tickets[0].customer_email == "alice@example.com"


def test_xml_malformed():
    tickets, errors = import_xml(INVALID_XML)
    assert len(tickets) == 0
    assert len(errors) == 1
    assert "Invalid XML" in errors[0]["error"]


def test_xml_missing_fields():
    tickets, errors = import_xml(MISSING_FIELDS_XML)
    assert len(errors) == 1
    assert len(tickets) == 0


def test_xml_tags_parsed():
    tickets, errors = import_xml(VALID_XML)
    assert len(tickets) == 1
    assert "urgent" in tickets[0].tags


def test_xml_fixture_file():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "sample_tickets.xml")
    if not os.path.exists(fixture_path):
        return
    with open(fixture_path, "rb") as f:
        content = f.read()
    tickets, errors = import_xml(content)
    assert len(tickets) > 0
