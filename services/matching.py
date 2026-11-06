
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "invoice_automation_v2.db"

TOLERANCE = 0.01


def add_result(cursor, invoice_id, check_type, passed,
               expected=None, actual=None, message=""):

    cursor.execute("""
        INSERT INTO InvoiceMatch
        (invoice_id, check_type, result, expected_value,
         actual_value, message)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        invoice_id,
        check_type,
        "PASS" if passed else "FAIL",
        str(expected) if expected is not None else None,
        str(actual) if actual is not None else None,
        message
    ))

    return passed


def match_invoices():

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        invoices = cursor.execute("""
            SELECT * FROM Invoice
            ORDER BY invoice_id
        """).fetchall()

        matched_count = 0
        exception_count = 0

        for invoice in invoices:

            invoice_id = invoice["invoice_id"]
            po_id = invoice["po_id"]

            # Remove previous results when rerunning
            cursor.execute(
                "DELETE FROM InvoiceMatch WHERE invoice_id = ?",
                (invoice_id,)
            )

            results = []

            def record(check_type, passed, **kwargs):
                results.append(add_result(
                    cursor, invoice_id, check_type,
                    passed, **kwargs
                ))

            # 1. Duplicate invoice check
            duplicate_count = cursor.execute("""
                SELECT COUNT(*)
                FROM Invoice
                WHERE vendor_id = ?
                AND invoice_number = ?
            """, (
                invoice["vendor_id"],
                invoice["invoice_number"]
            )).fetchone()[0]

            record(
                "DUPLICATE_CHECK",
                duplicate_count == 1,
                expected="1 invoice",
                actual=duplicate_count,
                message="Unique invoice number"
                if duplicate_count == 1
                else "Duplicate invoice detected"
            )

            # 2. Purchase Order check
            po = None

            if po_id:
                po = cursor.execute("""
                    SELECT * FROM PurchaseOrder
                    WHERE po_id = ?
                """, (po_id,)).fetchone()

            record(
                "PO_CHECK",
                po is not None,
                expected="Valid Purchase Order",
                actual=po_id,
                message="Purchase Order found"
                if po else "Missing or invalid Purchase Order"
            )

            # 3. Continue with PO-related checks
            if po is not None:

                # 4. Vendor check
                record(
                    "VENDOR_CHECK",
                    invoice["vendor_id"] == po["vendor_id"],
                    expected=po["vendor_id"],
                    actual=invoice["vendor_id"],
                    message="Vendor matches"
                    if invoice["vendor_id"] == po["vendor_id"]
                    else "Vendor mismatch"
                )

                # 5. Goods Receipt check
                receipts = cursor.execute("""
                    SELECT receipt_id
                    FROM GoodsReceipt
                    WHERE po_id = ?
                """, (po_id,)).fetchall()

                record(
                    "GR_CHECK",
                    len(receipts) > 0,
                    expected="At least one Goods Receipt",
                    actual=len(receipts),
                    message="Goods Receipt found"
                    if receipts else "Missing Goods Receipt"
                )

                # 6. Invoice line checks
                invoice_lines = cursor.execute("""
                    SELECT * FROM InvoiceLine
                    WHERE invoice_id = ?
                """, (invoice_id,)).fetchall()

                for line in invoice_lines:

                    po_line = None
                    po_line_id = line["po_line_id"]

                    if po_line_id:
                        po_line = cursor.execute("""
                            SELECT * FROM PurchaseOrderLine
                            WHERE po_line_id = ?
                            AND po_id = ?
                        """, (po_line_id, po_id)).fetchone()

                    else:
                        candidates = cursor.execute("""
                            SELECT * FROM PurchaseOrderLine
                            WHERE po_id = ? AND sku = ?
                        """, (po_id, line["sku"])).fetchall()

                        if len(candidates) == 1:
                            po_line = candidates[0]

                    if po_line is None:

                        record(
                            "PO_LINE_CHECK",
                            False,
                            expected="Valid PO line",
                            actual=line["sku"],
                            message="Invoice line could not be linked to a PO line"
                        )
                        continue

                    # 7. Price check
                    price_ok = abs(
                        line["unit_price"] - po_line["unit_price"]
                    ) <= TOLERANCE

                    record(
                        "PRICE_CHECK",
                        price_ok,
                        expected=po_line["unit_price"],
                        actual=line["unit_price"],
                        message="Price matches"
                        if price_ok else "Price mismatch"
                    )

                    # 8. Tax code check

                    tax_ok = line["tax_code"] == po_line["tax_code"]

                    record(
                        "TAX_CHECK",
                        tax_ok,
                        expected=po_line["tax_code"],
                        actual=line["tax_code"],
                        message="Tax code matches"
                        if tax_ok else "Tax code mismatch"
                    )

                    # 9. Ordered quantity check
                    ordered_qty = po_line["quantity"]
                    invoice_qty = line["quantity"]

                    ordered_ok = invoice_qty <= ordered_qty + TOLERANCE

                    record(
                        "ORDERED_QUANTITY_CHECK",
                        ordered_ok,
                        expected=ordered_qty,
                        actual=invoice_qty,
                        message="Invoice quantity is within ordered quantity"
                        if ordered_ok else "Invoice quantity exceeds ordered quantity"
                    )

                    # 10. Received quantity check
                    received_qty = cursor.execute("""
                        SELECT COALESCE(SUM(grl.received_quantity), 0)
                        FROM GoodsReceiptLine grl
                        JOIN GoodsReceipt gr
                        ON gr.receipt_id = grl.receipt_id
                        WHERE gr.po_id = ?
                        AND grl.po_line_id = ?
                    """, (po_id, po_line["po_line_id"])).fetchone()[0]

                    received_ok = invoice_qty <= received_qty + TOLERANCE

                    record(
                        "RECEIVED_QUANTITY_CHECK",
                        received_ok,
                        expected=received_qty,
                        actual=invoice_qty,
                        message="Invoice quantity is within received quantity"
                        if received_ok else "Invoice quantity exceeds received quantity"
                    )

            # 11. Update overall invoice status
            if all(results):
                status = "MATCHED"
                matched_count += 1
            else:
                status = "EXCEPTION"
                exception_count += 1

            cursor.execute("""
                UPDATE Invoice
                SET match_status = ?
                WHERE invoice_id = ?
            """, (status, invoice_id))

        connection.commit()

        print("\n========== INVOICE MATCHING RESULTS ==========")
        print("Total Invoices:", len(invoices))
        print("Matched Invoices:", matched_count)
        print("Exception Invoices:", exception_count)
        print("Invoice matching completed!")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    match_invoices()
