
import random
import sqlite3
from faker import Faker
from pathlib import Path
from datetime import date

fake = Faker()
SEED = 20261022

random.seed(SEED)
Faker.seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "invoice_automation_v2.db"


def generate_vendors():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    for i in range(1, 301):

        vendor_id = f"VND-{i:05d}"
        vendor_name = fake.company()
        email = fake.unique.company_email()
        phone = fake.numerify("9#########")

        status = random.choices(
            ["ACTIVE", "CLOSED"],
            weights=[95, 5]
        )[0]

        cursor.execute("""
            INSERT OR REPLACE INTO Vendor
            (vendor_id, vendor_name, email, phone, status)
            VALUES (?, ?, ?, ?, ?)
        """, (vendor_id, vendor_name, email, phone, status))

    connection.commit()

    cursor.execute("SELECT COUNT(*) FROM Vendor")
    count = cursor.fetchone()[0]

    print("Vendor generation completed!")
    print("Total vendors:", count)

    connection.close()



def generate_purchase_orders():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    # Get existing vendors
    cursor.execute("SELECT vendor_id FROM Vendor")
    vendors = [row[0] for row in cursor.fetchall()]

    if not vendors:
        print("Error: No vendors found. Generate vendors first.")
        connection.close()
        return

    # Generate 1500 Purchase Orders
    for i in range(1, 1501):
        po_id = f"PO-{i:05d}"

        cursor.execute("""
            INSERT OR IGNORE INTO PurchaseOrder
            (po_id, vendor_id, po_date, status)
            VALUES (?, ?, ?, ?)
        """, (
            po_id,
            random.choice(vendors),
            str(fake.date_between(start_date="-2y", end_date="today")),
            random.choice(["OPEN", "CLOSED", "APPROVED"])
        ))

    # Generate 2200 Purchase Order Lines
    po_ids = [f"PO-{i:05d}" for i in range(1, 1501)]

    for i in range(1, 2201):
        po_line_id = f"POL-{i:05d}"

        cursor.execute("""
            INSERT OR IGNORE INTO PurchaseOrderLine
            (po_line_id, po_id, sku, quantity, unit_price, tax_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            po_line_id,
            random.choice(po_ids),
            f"SKU-{random.randint(1000, 9999)}",
            random.randint(1, 100),
            round(random.uniform(50, 5000), 2),
            random.choice(["GST_5", "GST_12", "GST_18"])
        ))

    connection.commit()

    # Verify generated records
    cursor.execute("SELECT COUNT(*) FROM Vendor")
    print("Total Vendors:", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM PurchaseOrder")
    print("Total Purchase Orders:", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM PurchaseOrderLine")
    print("Total Purchase Order Lines:", cursor.fetchone()[0])

    connection.close()
    print("Purchase Order generation completed!")

def generate_goods_receipts():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    # Get existing Purchase Order Lines
    cursor.execute("""
        SELECT pol.po_line_id, pol.po_id, pol.quantity, po.po_date
        FROM PurchaseOrderLine pol
        JOIN PurchaseOrder po ON pol.po_id = po.po_id
    """)

    po_lines = cursor.fetchall()

    if not po_lines:
        print("Error: No Purchase Order Lines found.")
        connection.close()
        return

    # Generate 1800 Goods Receipts
    for i in range(1, 1801):

        receipt_id = f"GR-{i:05d}"

        po_line = random.choice(po_lines)

        po_line_id = po_line[0]
        po_id = po_line[1]
        ordered_quantity = po_line[2]
        receipt_date = po_line[3]

        received_quantity = round(
            random.uniform(1, ordered_quantity), 2
        )

        cursor.execute("""
            INSERT OR IGNORE INTO GoodsReceipt
            (receipt_id, po_id, receipt_date, status)
            VALUES (?, ?, ?, ?)
        """, (
            receipt_id,
            po_id,
            receipt_date,
            "RECEIVED"
        ))

        cursor.execute("""
            INSERT OR IGNORE INTO GoodsReceiptLine
            (receipt_line_id, receipt_id, po_line_id, received_quantity)
            VALUES (?, ?, ?, ?)
        """, (
            f"GRL-{i:05d}",
            receipt_id,
            po_line_id,
            received_quantity
        ))

    connection.commit()

    # Verify records
    cursor.execute("SELECT COUNT(*) FROM GoodsReceipt")
    print("Total Goods Receipts:", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM GoodsReceiptLine")
    print("Total Goods Receipt Lines:", cursor.fetchone()[0])

    connection.close()

    print("Goods Receipt generation completed!")


def generate_invoices():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    # Get valid Purchase Order Lines with Vendor details
    cursor.execute("""
        SELECT
            pol.po_line_id,
            pol.po_id,
            po.vendor_id,
            pol.sku,
            pol.quantity,
            pol.unit_price,
            pol.tax_code,
            po.po_date
        FROM PurchaseOrderLine pol
        JOIN PurchaseOrder po ON pol.po_id = po.po_id
    """)

    po_lines = cursor.fetchall()

    if not po_lines:
        print("Error: No Purchase Order Lines found.")
        connection.close()
        return

    tax_rates = {
        "GST_5": 0.05,
        "GST_12": 0.12,
        "GST_18": 0.18
    }

    # Generate 2000 Invoices
    for i in range(1, 2001):

        invoice_id = f"INV-{i:05d}"
        invoice_number = f"INV-NUM-{i:05d}"

        po_line = random.choice(po_lines)

        po_line_id = po_line[0]
        po_id = po_line[1]
        vendor_id = po_line[2]
        sku = po_line[3]
        ordered_quantity = po_line[4]
        unit_price = po_line[5]
        tax_code = po_line[6]
        po_date = po_line[7]

        quantity = round(
            random.uniform(1, ordered_quantity), 2
        )

        subtotal = round(quantity * unit_price, 2)

        tax_amount = round(
            subtotal * tax_rates[tax_code], 2
        )

        grand_total = round(subtotal + tax_amount, 2)

        invoice_date = str(
            fake.date_between(
                start_date=date.fromisoformat(po_date),
                end_date=date.today()
        )
        )

        cursor.execute("""
            INSERT OR IGNORE INTO Invoice
            (invoice_id, vendor_id, po_id, invoice_number,
             invoice_date, subtotal, tax_amount, grand_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            vendor_id,
            po_id,
            invoice_number,
            invoice_date,
            subtotal,
            tax_amount,
            grand_total
        ))

        cursor.execute("""
            INSERT OR IGNORE INTO InvoiceLine
            (invoice_line_id, invoice_id, po_line_id, sku,
             quantity, unit_price, tax_code, line_total, tax_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"INVL-{i:05d}",
            invoice_id,
            po_line_id,
            sku,
            quantity,
            unit_price,
            tax_code,
            subtotal,
            tax_amount
        ))

    connection.commit()

    # Verify generated records
    cursor.execute("SELECT COUNT(*) FROM Invoice")
    print("Total Invoices:", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM InvoiceLine")
    print("Total Invoice Lines:", cursor.fetchone()[0])

    connection.close()

    print("Invoice generation completed!")

if __name__ == "__main__":
    generate_purchase_orders()
    generate_goods_receipts()
    generate_invoices()
