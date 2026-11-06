
PRAGMA foreign_keys = ON;

-- 1. Vendor table
CREATE TABLE IF NOT EXISTS Vendor (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'CLOSED')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. Purchase Order table
CREATE TABLE IF NOT EXISTS PurchaseOrder (
    po_id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL,
    po_date TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    FOREIGN KEY (vendor_id) REFERENCES Vendor(vendor_id)
);

-- 3. Purchase Order Lines
CREATE TABLE IF NOT EXISTS PurchaseOrderLine (
    po_line_id TEXT PRIMARY KEY,
    po_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    quantity REAL NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    tax_code TEXT NOT NULL,
    FOREIGN KEY (po_id) REFERENCES PurchaseOrder(po_id)
);

-- 4. Goods Receipt
CREATE TABLE IF NOT EXISTS GoodsReceipt (
    receipt_id TEXT PRIMARY KEY,
    po_id TEXT NOT NULL,
    receipt_date TEXT NOT NULL,
    status TEXT DEFAULT 'RECEIVED',
    FOREIGN KEY (po_id) REFERENCES PurchaseOrder(po_id)
);

-- 5. Goods Receipt Lines
CREATE TABLE IF NOT EXISTS GoodsReceiptLine (
    receipt_line_id TEXT PRIMARY KEY,
    receipt_id TEXT NOT NULL,
    po_line_id TEXT NOT NULL,
    received_quantity REAL NOT NULL CHECK(received_quantity >= 0),
    FOREIGN KEY (receipt_id) REFERENCES GoodsReceipt(receipt_id),
    FOREIGN KEY (po_line_id) REFERENCES PurchaseOrderLine(po_line_id)
);

-- 6. Invoice
CREATE TABLE IF NOT EXISTS Invoice (
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

-- 7. Invoice Lines
CREATE TABLE IF NOT EXISTS InvoiceLine (
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

-- 8. Approval
CREATE TABLE IF NOT EXISTS Approval (
    approval_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    approver_name TEXT,
    decision TEXT NOT NULL DEFAULT 'PENDING',
    decision_date TEXT,
    comments TEXT,
    FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
);

-- 9. Payment
CREATE TABLE IF NOT EXISTS Payment (
    payment_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    payment_amount REAL NOT NULL,
    payment_date TEXT,
    payment_status TEXT DEFAULT 'PENDING',
    FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
);

-- 10. Invoice matching results
CREATE TABLE IF NOT EXISTS InvoiceMatch (
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

-- 11. Invoice event history
CREATE TABLE IF NOT EXISTS InvoiceEvent (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    event_description TEXT,
    event_time TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
);

-- Indexes for faster searching
CREATE INDEX IF NOT EXISTS idx_invoice_vendor
ON Invoice(vendor_id);

CREATE INDEX IF NOT EXISTS idx_invoice_number
ON Invoice(vendor_id, invoice_number);

CREATE INDEX IF NOT EXISTS idx_po_vendor
ON PurchaseOrder(vendor_id);

CREATE INDEX IF NOT EXISTS idx_invoice_event
ON InvoiceEvent(invoice_id);
