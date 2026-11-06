
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "invoice_automation_v2.db"


def view_pending_approvals(cursor):

    approvals = cursor.execute("""
        SELECT
            approval_id,
            invoice_id,
            approver_name,
            comments
        FROM Approval
        WHERE decision = 'PENDING'
        ORDER BY invoice_id
    """).fetchall()

    print("\n========== PENDING APPROVALS ==========")

    if not approvals:
        print("No pending approvals found.")
        return

    for approval in approvals:
        print("\nApproval ID:", approval[0])
        print("Invoice ID:", approval[1])
        print("Approver:", approval[2])
        print("Reason:", approval[3])

    print("\nTotal Pending Approvals:", len(approvals))


def update_invoice_status(cursor, invoice_id):

    decisions = cursor.execute("""
        SELECT decision
        FROM Approval
        WHERE invoice_id = ?
    """, (invoice_id,)).fetchall()

    decision_values = [row[0] for row in decisions]

    if "REJECTED" in decision_values:
        new_status = "REJECTED"

    elif decision_values and all(
        decision == "APPROVED"
        for decision in decision_values
    ):
        new_status = "APPROVED"

    else:
        new_status = "EXCEPTION_REVIEW"

    result = cursor.execute("""
        SELECT lifecycle_status
        FROM Invoice
        WHERE invoice_id = ?
    """, (invoice_id,)).fetchone()

    if result is None:
        raise ValueError("Invoice not found")

    old_status = result[0]

    cursor.execute("""
        UPDATE Invoice
        SET lifecycle_status = ?
        WHERE invoice_id = ?
    """, (new_status, invoice_id))

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
            "Approval workflow updated invoice status"
        ))

    return new_status


def process_approval():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:

        view_pending_approvals(cursor)

        approval_id = input(
            "\nEnter Approval ID to process (or type EXIT): "
        ).strip()

        if approval_id.upper() == "EXIT":
            print("Approval workflow closed.")
            return

        approval = cursor.execute("""
            SELECT invoice_id, decision
            FROM Approval
            WHERE approval_id = ?
        """, (approval_id,)).fetchone()

        if approval is None:
            print("Invalid Approval ID.")
            return

        if approval[1] != "PENDING":
            print("This approval has already been processed.")
            return

        decision = input(
            "Enter decision (APPROVED/REJECTED): "
        ).strip().upper()

        if decision not in ("APPROVED", "REJECTED"):
            print("Invalid decision.")
            return

        comments = input("Enter review comments: ").strip()

        cursor.execute("""
            UPDATE Approval
            SET decision = ?,
                decision_date = ?,
                comments = COALESCE(comments, '') ||
                        ' | Reviewer Comment: ' || ?
            WHERE approval_id = ?
            AND decision = 'PENDING'
        """, (
            decision,
            datetime.now().isoformat(timespec="seconds"),
            comments,
            approval_id
        ))

        invoice_id = approval[0]

        new_status = update_invoice_status(
            cursor, invoice_id
        )

        connection.commit()

        print("\n========== APPROVAL RESULT ==========")
        print("Invoice ID:", invoice_id)
        print("Decision:", decision)
        print("Updated Invoice Status:", new_status)
        print("Approval processed successfully!")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    process_approval()
