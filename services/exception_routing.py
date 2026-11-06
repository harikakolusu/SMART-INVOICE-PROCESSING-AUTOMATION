
import sqlite3
from pathlib import Path
import uuid

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "invoice_automation_v2.db"


# Exception categories and responsible review teams
ROUTING_RULES = {
    "DUPLICATE_CHECK": "Duplicate Verification Team",
    "PO_CHECK": "Purchase Order Review Team",
    "VENDOR_CHECK": "Vendor Verification Team",
    "GR_CHECK": "Goods Receipt Review Team",
    "PO_LINE_CHECK": "Purchase Order Review Team",
    "PRICE_CHECK": "Price Review Team",
    "TAX_CHECK": "Tax Review Team",
    "ORDERED_QUANTITY_CHECK": "Quantity Review Team",
    "RECEIVED_QUANTITY_CHECK": "Goods Receipt Review Team"
}


def route_exceptions():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        # Find invoices with failed matching checks
        cursor.execute("""
            SELECT DISTINCT invoice_id
            FROM InvoiceMatch
            WHERE result = 'FAIL'
        """)

        exception_invoices = cursor.fetchall()

        routed_count = 0
        approval_count = 0

        for row in exception_invoices:

            invoice_id = row[0]

            # Get failed checks for this invoice
            cursor.execute("""
                SELECT DISTINCT check_type, message
                FROM InvoiceMatch
                WHERE invoice_id = ?
                AND result = 'FAIL'
            """, (invoice_id,))

            failures = cursor.fetchall()

            if not failures:
                continue

            # Remove previous automatically created pending approvals
            cursor.execute("""
                DELETE FROM Approval
                WHERE invoice_id = ?
                AND decision = 'PENDING'
                AND approver_name LIKE 'AUTO:%'
            """, (invoice_id,))

            # Get current lifecycle status
            cursor.execute("""
                SELECT lifecycle_status
                FROM Invoice
                WHERE invoice_id = ?
            """, (invoice_id,))

            result = cursor.fetchone()

            if result is None:
                continue

            old_status = result[0]

            # Route each failed check
            for check_type, message in failures:

                team = ROUTING_RULES.get(
                    check_type,
                    "General Exception Review Team"
                )

                approver = "AUTO:" + team

                comments = (
                    "Exception Type: " + check_type +
                    " | Reason: " + str(message)
                )

                approval_id = str(uuid.uuid4())

                cursor.execute("""
                    INSERT INTO Approval (
                        approval_id,
                        invoice_id,
                        approver_name,
                        decision,
                        comments
                    )
                    VALUES (?, ?, ?, 'PENDING', ?)
                """, (
                    approval_id,
                    invoice_id,
                    approver,
                    comments
                ))

                approval_count += 1

            # Update invoice lifecycle status
            new_status = "EXCEPTION_REVIEW"

            cursor.execute("""
                UPDATE Invoice
                SET lifecycle_status = ?
                WHERE invoice_id = ?
            """, (new_status, invoice_id))

            # Record event history only when status changes
            if old_status != new_status:

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
                    new_status,
                    "Invoice automatically routed for exception review"
                ))

            routed_count += 1

        connection.commit()

        print("\n========== EXCEPTION ROUTING RESULTS ==========")
        print("Total Exception Invoices:", len(exception_invoices))
        print("Invoices Routed:", routed_count)
        print("Approval Records Created:", approval_count)
        print("Exception routing completed!")

    except Exception as error:
        connection.rollback()
        print("Error:", error)
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    route_exceptions()
