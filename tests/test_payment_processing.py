
import sqlite3
import pytest

import services.payment_processing as payment_processing


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    # Create a separate temporary database
    db_path = tmp_path / "test_payments.db"
    monkeypatch.setattr(payment_processing, "DB_PATH", db_path)

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.executescript("""
        CREATE TABLE Invoice (
            invoice_id TEXT PRIMARY KEY,
            lifecycle_status TEXT,
            grand_total REAL
        );

        CREATE TABLE Approval (
            approval_id TEXT PRIMARY KEY,
            invoice_id TEXT,
            decision TEXT
        );

        CREATE TABLE InvoiceMatch (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT,
            result TEXT
        );

        CREATE TABLE Payment (
            payment_id TEXT PRIMARY KEY,
            invoice_id TEXT,
            payment_amount REAL,
            payment_date TEXT,
            payment_status TEXT
        );

        CREATE TABLE InvoiceEvent (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT,
            old_status TEXT,
            new_status TEXT,
            event_description TEXT
        );
    """)

    connection.commit()
    connection.close()

    return db_path


def add_invoice(db_path, invoice_id="TEST001",
                status="RECEIVED", amount=1500.00):
    connection = sqlite3.connect(db_path)
    connection.execute("""
        INSERT INTO Invoice
        VALUES (?, ?, ?)
    """, (invoice_id, status, amount))
    connection.commit()
    connection.close()


def test_payment_readiness(test_db):
    add_invoice(test_db)

    connection = sqlite3.connect(test_db)
    result = payment_processing.check_payment_readiness(
        connection.cursor(), "TEST001"
    )
    connection.close()

    assert result[0] is True


def test_invoice_not_found(test_db):
    connection = sqlite3.connect(test_db)

    result = payment_processing.check_payment_readiness(
        connection.cursor(), "INVALID"
    )
    connection.close()

    assert result[0] is False
    assert result[1] == "Invoice not found."


def test_unresolved_exception_blocked(test_db):
    add_invoice(test_db)

    connection = sqlite3.connect(test_db)
    connection.execute("""
        INSERT INTO InvoiceMatch (invoice_id, result)
        VALUES (?, ?)
    """, ("TEST001", "FAIL"))
    connection.commit()

    result = payment_processing.check_payment_readiness(
        connection.cursor(), "TEST001"
    )
    connection.close()

    assert result[0] is False
    assert "unresolved matching exceptions" in result[1]


def test_pending_approval_blocked(test_db):
    add_invoice(test_db)

    connection = sqlite3.connect(test_db)
    connection.execute("""
        INSERT INTO Approval
        VALUES (?, ?, ?)
    """, ("APP001", "TEST001", "PENDING"))
    connection.commit()

    result = payment_processing.check_payment_readiness(
        connection.cursor(), "TEST001"
    )
    connection.close()

    assert result[0] is False
    assert result[1] == "All approvals are not completed."


def test_duplicate_payment_blocked(test_db):
    add_invoice(test_db)

    connection = sqlite3.connect(test_db)
    connection.execute("""
        INSERT INTO Payment
        VALUES (?, ?, ?, ?, ?)
    """, ("PAY001", "TEST001", 1500.00,
          "2026-11-06", "PENDING"))
    connection.commit()

    result = payment_processing.check_payment_readiness(
        connection.cursor(), "TEST001"
    )
    connection.close()

    assert result[0] is False
    assert result[1] == "Payment already exists."


def test_payment_creation(test_db, monkeypatch):
    add_invoice(test_db)

    answers = iter(["TEST001", "YES"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    payment_processing.process_payment()

    connection = sqlite3.connect(test_db)
    payment = connection.execute("""
        SELECT invoice_id, payment_amount, payment_status
        FROM Payment
    """).fetchone()
    connection.close()

    assert payment == ("TEST001", 1500.00, "PENDING")


@pytest.mark.parametrize(
    "status, expected_invoice_status",
    [
        ("COMPLETED", "PAID"),
        ("FAILED", "PAYMENT_FAILED")
    ]
)
def test_payment_status_update(
    test_db, monkeypatch, status, expected_invoice_status
):
    add_invoice(test_db)

    connection = sqlite3.connect(test_db)
    connection.execute("""
        INSERT INTO Payment
        VALUES (?, ?, ?, ?, ?)
    """, ("PAY001", "TEST001", 1500.00,
          "2026-11-06", "PENDING"))
    connection.commit()
    connection.close()

    answers = iter(["PAY001", status])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    payment_processing.update_payment_status()

    connection = sqlite3.connect(test_db)

    payment_status = connection.execute("""
        SELECT payment_status FROM Payment
        WHERE payment_id = 'PAY001'
    """).fetchone()[0]

    invoice_status = connection.execute("""
        SELECT lifecycle_status FROM Invoice
        WHERE invoice_id = 'TEST001'
    """).fetchone()[0]

    event_count = connection.execute("""
        SELECT COUNT(*) FROM InvoiceEvent
        WHERE invoice_id = 'TEST001'
    """).fetchone()[0]

    connection.close()

    assert payment_status == status
    assert invoice_status == expected_invoice_status
    assert event_count == 1
