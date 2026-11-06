import sqlite3
from pathlib import Path
from datetime import datetime
import uuid

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "invoice_automation_v2.db"


def check_payment_readiness(cursor, invoice_id):

    invoice = cursor.execute("""
        SELECT lifecycle_status
        FROM Invoice
        WHERE invoice_id = ?
    """, (invoice_id,)).fetchone()

    if invoice is None:
        return False, "Invoice not found."

    if invoice[0] == "REJECTED":
        return False, "Rejected invoices cannot be paid."

    if invoice[0] not in ("RECEIVED", "APPROVED"):
        return False, "Invoice is not ready for payment."

    approvals = cursor.execute("""
        SELECT decision
        FROM Approval
        WHERE invoice_id = ?
    """, (invoice_id,)).fetchall()

    if approvals and not all(
        row[0] == "APPROVED" for row in approvals
    ):
        return False, "All approvals are not completed."

    failed_checks = cursor.execute("""
        SELECT COUNT(*)
        FROM InvoiceMatch
        WHERE invoice_id = ?
        AND result = 'FAIL'
    """, (invoice_id,)).fetchone()[0]

    if failed_checks > 0 and invoice[0] != "APPROVED":
        return False, "Invoice has unresolved matching exceptions."

    payment = cursor.execute("""
        SELECT COUNT(*)
        FROM Payment
        WHERE invoice_id = ?
    """, (invoice_id,)).fetchone()[0]

    if payment > 0:
        return False, "Payment already exists."

    return True, "Invoice is ready for payment."


def process_payment():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        invoice_id = input("Enter Invoice ID: ").strip()

        ready, message = check_payment_readiness(
            cursor, invoice_id
        )

        print("\nPayment Readiness:", message)

        if not ready:
            return

        confirm = input(
            "Proceed with payment creation? (YES/NO): "
        ).strip().upper()

        if confirm != "YES":
            print("Payment creation cancelled.")
            return

        payment_id = str(uuid.uuid4())

        invoice_amount = cursor.execute("""
            SELECT grand_total
            FROM Invoice
            WHERE invoice_id = ?
        """, (invoice_id,)).fetchone()[0]

        cursor.execute("""
            INSERT INTO Payment (
                payment_id,
                invoice_id,
                payment_amount,
                payment_date,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            payment_id,
            invoice_id,
            invoice_amount,
            datetime.now().isoformat(timespec="seconds"),
            "PENDING"
        ))

        connection.commit()

        print("\n========== PAYMENT RESULT ==========")
        print("Payment ID:", payment_id)
        print("Invoice ID:", invoice_id)
        print("Payment Status: PENDING")
        print("Payment record created successfully!")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def update_payment_status():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        payment_id = input("Enter Payment ID: ").strip()

        payment = cursor.execute("""
            SELECT invoice_id, payment_status
            FROM Payment
            WHERE payment_id = ?
        """, (payment_id,)).fetchone()

        if payment is None:
            print("Invalid Payment ID.")
            return

        if payment[1] != "PENDING":
            print("Payment has already been processed.")
            return

        status = input(
            "Enter payment status (COMPLETED/FAILED): "
        ).strip().upper()

        if status not in ("COMPLETED", "FAILED"):
            print("Invalid payment status.")
            return

        cursor.execute("""
            UPDATE Payment
            SET payment_status = ?
            WHERE payment_id = ?
        """, (status, payment_id))

        invoice_id = payment[0]

        old_status = cursor.execute("""
            SELECT lifecycle_status
            FROM Invoice
            WHERE invoice_id = ?
        """, (invoice_id,)).fetchone()[0]

        new_invoice_status = (
            "PAID" if status == "COMPLETED"
            else "PAYMENT_FAILED"
        )

        cursor.execute("""
            UPDATE Invoice
            SET lifecycle_status = ?
            WHERE invoice_id = ?
        """, (new_invoice_status, invoice_id))

        if old_status != new_invoice_status:
            cursor.execute("""
                INSERT INTO InvoiceEvent (
                    invoice_id,
                    old_status,
                    new_status,
                    event_description
                )
                VALUES (?, ?, ?, ?)
            """, (
                invoice_id,
                old_status,
                new_invoice_status,
                "Payment status updated to " + status
            ))

        connection.commit()

        print("\n========== PAYMENT STATUS RESULT ==========")
        print("Payment ID:", payment_id)
        print("Invoice ID:", payment[0])
        print("Payment Status:", status)
        print("Payment status updated successfully!")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    process_payment()