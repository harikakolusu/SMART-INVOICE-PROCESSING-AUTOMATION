
import sqlite3
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "invoice_automation.db"


@pytest.fixture
def connection():
    assert DB_PATH.exists(), "Database file does not exist"

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    yield conn

    conn.close()


def test_database_tables(connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table'
    """)

    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "Vendor",
        "PurchaseOrder",
        "PurchaseOrderLine",
        "GoodsReceipt",
        "GoodsReceiptLine",
        "Invoice",
        "InvoiceLine",
        "Approval",
        "Payment",
        "InvoiceMatch",
        "InvoiceEvent"
    }

    assert expected_tables.issubset(tables)


def test_vendor_data(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Vendor")

    assert cursor.fetchone()[0] > 0


def test_purchase_order_data(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM PurchaseOrder")

    assert cursor.fetchone()[0] > 0


def test_invoice_data(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Invoice")

    assert cursor.fetchone()[0] > 0


def test_invoice_matching_results(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM InvoiceMatch")

    assert cursor.fetchone()[0] > 0


def test_exception_approval_records(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Approval")

    assert cursor.fetchone()[0] > 0
