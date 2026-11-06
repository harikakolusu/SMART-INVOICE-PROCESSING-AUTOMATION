
import sqlite3
import random
import csv
from pathlib import Path
from datetime import date, timedelta
from faker import Faker

# -------------------------------------------------
# Configuration
# -------------------------------------------------

SEED = 20261022
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "invoice_automation_v2.db"
OUTPUT_DIR = BASE_DIR / "output"
GROUND_TRUTH_PATH = OUTPUT_DIR / "ground_truth.csv"

TODAY = date(2026, 11, 5)

# -------------------------------------------------
# Database connection
# -------------------------------------------------

def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# -------------------------------------------------
# Generate ground truth file
# -------------------------------------------------

def save_ground_truth(records):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(GROUND_TRUTH_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["invoice_id", "issue_type", "expected_status"]
        )
        writer.writeheader()
        writer.writerows(records)


# -------------------------------------------------
# Main generator
# -------------------------------------------------

def generate_data():
    conn = connect_db()
    cursor = conn.cursor()

    # Start with a fresh database only for this V2 generator.
    cursor.executescript("""
    DROP TABLE IF EXISTS InvoiceEvent;
    DROP TABLE IF EXISTS InvoiceMatch;
    DROP TABLE IF EXISTS Payment;
    DROP TABLE IF EXISTS Approval;
    DROP TABLE IF EXISTS InvoiceLine;
    DROP TABLE IF EXISTS Invoice;
    DROP TABLE IF EXISTS GoodsReceiptLine;
    DROP TABLE IF EXISTS GoodsReceipt;
    DROP TABLE IF EXISTS PurchaseOrderLine;
    DROP TABLE IF EXISTS PurchaseOrder;
    DROP TABLE IF EXISTS Vendor;

    CREATE TABLE Vendor (
        vendor_id TEXT PRIMARY KEY,
        vendor_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        status TEXT NOT NULL
    );

    CREATE TABLE PurchaseOrder (
        po_id TEXT PRIMARY KEY,
        vendor_id TEXT NOT NULL,
        po_date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (vendor_id) REFERENCES Vendor(vendor_id)
    );

    CREATE TABLE PurchaseOrderLine (
        po_line_id TEXT PRIMARY KEY,
        po_id TEXT NOT NULL,
        sku TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        tax_code TEXT NOT NULL,
        FOREIGN KEY (po_id) REFERENCES PurchaseOrder(po_id)
    );

    CREATE TABLE GoodsReceipt (
        receipt_id TEXT PRIMARY KEY,
        po_id TEXT NOT NULL,
        receipt_date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (po_id) REFERENCES PurchaseOrder(po_id)
    );

    CREATE TABLE GoodsReceiptLine (
        receipt_line_id TEXT PRIMARY KEY,
        receipt_id TEXT NOT NULL,
        po_line_id TEXT NOT NULL,
        received_quantity REAL NOT NULL,
        FOREIGN KEY (receipt_id) REFERENCES GoodsReceipt(receipt_id),
        FOREIGN KEY (po_line_id) REFERENCES PurchaseOrderLine(po_line_id)
    );

    CREATE TABLE Invoice (
        invoice_id TEXT PRIMARY KEY,
        vendor_id TEXT NOT NULL,
        po_id TEXT,
        invoice_number TEXT NOT NULL,
        invoice_date TEXT NOT NULL,
        subtotal REAL NOT NULL,
        tax_amount REAL NOT NULL,
        grand_total REAL NOT NULL,
        match_status TEXT DEFAULT 'PENDING',
        lifecycle_status TEXT DEFAULT 'RECEIVED',
        FOREIGN KEY (vendor_id) REFERENCES Vendor(vendor_id),
        FOREIGN KEY (po_id) REFERENCES PurchaseOrder(po_id)
    );

    CREATE TABLE InvoiceLine (
        invoice_line_id TEXT PRIMARY KEY,
        invoice_id TEXT NOT NULL,
        po_line_id TEXT,
        sku TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        tax_code TEXT NOT NULL,
        line_total REAL NOT NULL,
        tax_amount REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id),
        FOREIGN KEY (po_line_id) REFERENCES PurchaseOrderLine(po_line_id)
    );

    CREATE TABLE Approval (
        approval_id TEXT PRIMARY KEY,
        invoice_id TEXT NOT NULL,
        approver_name TEXT,
        decision TEXT DEFAULT 'PENDING',
        decision_date TEXT,
        comments TEXT,
        FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
    );

    CREATE TABLE Payment (
        payment_id TEXT PRIMARY KEY,
        invoice_id TEXT NOT NULL,
        payment_amount REAL NOT NULL,
        payment_date TEXT,
        payment_status TEXT DEFAULT 'PENDING',
        FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
    );

    CREATE TABLE InvoiceMatch (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT NOT NULL,
        check_type TEXT NOT NULL,
        result TEXT NOT NULL,
        expected_value TEXT,
        actual_value TEXT,
        message TEXT,
        checked_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
    );

    CREATE TABLE InvoiceEvent (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        event_description TEXT,
        event_time TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
    );
    """)

    # Vendors
    for i in range(1, 301):
        vendor_id = f"VND-{i:05d}"
        cursor.execute(
            "INSERT INTO Vendor VALUES (?, ?, ?, ?, ?)",
            (
                vendor_id,
                fake.company(),
                fake.company_email(),
                fake.phone_number(),
                "CLOSED" if i % 20 == 0 else "ACTIVE"
            )
        )

    # Purchase orders and lines
    po_lines = []
    po_vendors = {}

    for i in range(1, 1501):
        po_id = f"PO-2026-{i:06d}"
        vendor_id = f"VND-{random.randint(1, 300):05d}"
        po_date = TODAY - timedelta(days=random.randint(1, 300))

        cursor.execute(
            "INSERT INTO PurchaseOrder VALUES (?, ?, ?, ?)",
            (po_id, vendor_id, po_date.isoformat(), "APPROVED")
        )

        po_vendors[po_id] = vendor_id

        line_count = 2 if i <= 700 else 1

        for j in range(1, line_count + 1):
            po_line_id = f"POL-{i:06d}-{j:02d}"
            sku = f"SKU-{random.randint(1000, 9999)}"
            quantity = random.randint(5, 100)
            unit_price = round(random.uniform(50, 2000), 2)
            tax_code = random.choice(["GST_5", "GST_12", "GST_18"])

            cursor.execute(
                "INSERT INTO PurchaseOrderLine VALUES (?, ?, ?, ?, ?, ?)",
                (po_line_id, po_id, sku, quantity, unit_price, tax_code)
            )

            po_lines.append({
                "po_id": po_id,
                "po_line_id": po_line_id,
                "vendor_id": vendor_id,
                "sku": sku,
                "quantity": quantity,
                "unit_price": unit_price,
                "tax_code": tax_code,
                "po_date": po_date
            })

    # Goods receipts
    receipts = {}

    for i in range(1, 1801):
        po_line = random.choice(po_lines)
        receipt_id = f"GRN-2026-{i:06d}"
        receipt_date = po_line["po_date"] + timedelta(days=random.randint(1, 30))

        cursor.execute(
            "INSERT INTO GoodsReceipt VALUES (?, ?, ?, ?)",
            (receipt_id, po_line["po_id"], receipt_date.isoformat(), "RECEIVED")
        )

        received_qty = random.randint(1, int(po_line["quantity"]))
        receipt_line_id = f"GRL-{i:06d}"

        cursor.execute(
            "INSERT INTO GoodsReceiptLine VALUES (?, ?, ?, ?)",
            (receipt_line_id, receipt_id, po_line["po_line_id"], received_qty)
        )

        receipts.setdefault(po_line["po_line_id"], []).append(received_qty)

    
    # Invoices and ground truth
    ground_truth = []
    invoice_counter = {}

    issue_types = (
        ["CLEAN"] * 1400
        + ["PRICE_VARIANCE"] * 200
        + ["QUANTITY_MISMATCH"] * 160
        + ["DUPLICATE_INVOICE"] * 100
        + ["MISSING_RECEIPT"] * 80
        + ["TAX_MISMATCH"] * 60
    )

    random.shuffle(issue_types)

    lines_with_receipts = [
        line for line in po_lines
        if line["po_line_id"] in receipts
    ]

    lines_without_receipts = [
        line for line in po_lines
        if line["po_line_id"] not in receipts
    ]

    duplicate_vendor = "VND-00001"

    duplicate_lines = [
        line for line in lines_with_receipts
        if line["vendor_id"] == duplicate_vendor
    ]

    if not duplicate_lines:
        raise ValueError("No purchase order lines found for duplicate vendor")

    for i in range(1, 2001):
        issue = issue_types[i - 1]

        if issue == "MISSING_RECEIPT":
            po_line = random.choice(lines_without_receipts)
        elif issue == "DUPLICATE_INVOICE":
            po_line = random.choice(duplicate_lines)
        else:
            po_line = random.choice(lines_with_receipts)

        vendor_id = po_line["vendor_id"]
        po_id = po_line["po_id"]

        invoice_counter[vendor_id] = invoice_counter.get(vendor_id, 0) + 1

        invoice_id = f"INV-{vendor_id}-2026-{invoice_counter[vendor_id]:06d}"
        invoice_number = f"INVNUM-{vendor_id}-{invoice_counter[vendor_id]:06d}"

        if issue == "DUPLICATE_INVOICE":
            invoice_number = "DUP-INV-VND-00001"

        received_quantity = sum(
            receipts.get(po_line["po_line_id"], [])
        )

        if issue == "MISSING_RECEIPT":
            quantity = random.randint(1, int(po_line["quantity"]))
        else:
            max_invoice_quantity = min(
                int(po_line["quantity"]),
                int(received_quantity)
            )
            quantity = random.randint(1, max_invoice_quantity)

        price = po_line["unit_price"]
        tax_code = po_line["tax_code"]

        if issue == "PRICE_VARIANCE":
            price = round(price * 1.10, 2)
        elif issue == "QUANTITY_MISMATCH":
            quantity = int(po_line["quantity"]) + 5
        elif issue == "TAX_MISMATCH":
            tax_code = "GST_18" if tax_code != "GST_18" else "GST_5"

        line_total = round(quantity * price, 2)

        tax_rates = {
            "GST_5": 0.05,
            "GST_12": 0.12,
            "GST_18": 0.18
        }

        tax_amount = round(line_total * tax_rates[tax_code], 2)
        grand_total = round(line_total + tax_amount, 2)

        invoice_date = po_line["po_date"] + timedelta(days=random.randint(1, 45))

        cursor.execute(
            "INSERT INTO Invoice VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                invoice_id, vendor_id, po_id, invoice_number,
                invoice_date.isoformat(), line_total, tax_amount,
                grand_total, "PENDING", "RECEIVED"
            )
        )

        invoice_line_id = f"INVL-{invoice_id}-01"

        cursor.execute(
            "INSERT INTO InvoiceLine VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                invoice_line_id, invoice_id, po_line["po_line_id"],
                po_line["sku"], quantity, price, tax_code,
                line_total, tax_amount
            )
        )

        ground_truth.append({
            "invoice_id": invoice_id,
            "issue_type": issue,
            "expected_status": "MATCHED" if issue == "CLEAN" else "EXCEPTION"
        })

    conn.commit()
    conn.close()

    save_ground_truth(ground_truth)


print("V2 data generation completed!")
print("Database:", DB_PATH)
print("Ground truth:", GROUND_TRUTH_PATH)


if __name__ == "__main__":
    generate_data()
