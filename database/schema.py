SCHEMA_SQL = """

CREATE TABLE IF NOT EXISTS fuel_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL DEFAULT 'Litre',
    hsn_code TEXT,
    gst_rate REAL DEFAULT 18
);

CREATE TABLE IF NOT EXISTS tanks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    fuel_type_id INTEGER NOT NULL REFERENCES fuel_types(id),
    capacity REAL NOT NULL,
    current_level REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pumps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pump_no TEXT NOT NULL UNIQUE,
    tank_id INTEGER NOT NULL REFERENCES tanks(id),
    description TEXT
);

CREATE TABLE IF NOT EXISTS lube_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    product_name TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT 'Bottle',
    purchase_rate REAL NOT NULL DEFAULT 0,
    selling_price REAL NOT NULL DEFAULT 0,
    stock_qty REAL NOT NULL DEFAULT 0,
    hsn_code TEXT,
    gst_rate REAL DEFAULT 18
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    gstin TEXT
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    purchase_date TEXT NOT NULL DEFAULT (date('now')),
    invoice_no TEXT,
    total_amount REAL NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL CHECK(item_type IN ('fuel','lube')),
    fuel_type_id INTEGER REFERENCES fuel_types(id),
    lube_product_id INTEGER REFERENCES lube_products(id),
    qty REAL NOT NULL,
    rate REAL NOT NULL,
    amount REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    gstin TEXT,
    credit_limit REAL DEFAULT 0,
    balance REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT NOT NULL UNIQUE,
    customer_id INTEGER REFERENCES customers(id),
    sale_date TEXT NOT NULL DEFAULT (date('now')),
    payment_mode TEXT NOT NULL DEFAULT 'Cash',
    taxable_amount REAL NOT NULL DEFAULT 0,
    gst_rate REAL DEFAULT 18,
    cgst_amount REAL DEFAULT 0,
    sgst_amount REAL DEFAULT 0,
    total_amount REAL NOT NULL DEFAULT 0,
    round_off REAL DEFAULT 0,
    grand_total REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL CHECK(item_type IN ('fuel','lube')),
    pump_id INTEGER REFERENCES pumps(id),
    lube_product_id INTEGER REFERENCES lube_products(id),
    opening_reading REAL,
    closing_reading REAL,
    qty REAL NOT NULL,
    rate REAL NOT NULL,
    amount REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS expense_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES expense_categories(id),
    amount REAL NOT NULL,
    description TEXT,
    expense_date TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    bank_name TEXT,
    bank_account TEXT,
    ifsc_code TEXT,
    salary_type TEXT NOT NULL DEFAULT 'Fixed' CHECK(salary_type IN ('Fixed','Daily')),
    salary_amount REAL NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    date TEXT NOT NULL,
    shift TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Present' CHECK(status IN ('Present','Absent','Half Day','Leave')),
    UNIQUE(employee_id, date, shift)
);

CREATE TABLE IF NOT EXISTS payroll (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    working_days INTEGER DEFAULT 0,
    gross_salary REAL NOT NULL DEFAULT 0,
    deductions REAL NOT NULL DEFAULT 0,
    net_salary REAL NOT NULL DEFAULT 0,
    paid INTEGER NOT NULL DEFAULT 0,
    paid_date TEXT,
    notes TEXT,
    UNIQUE(employee_id, month, year)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    details TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS shift_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    shift TEXT NOT NULL,
    pump_id INTEGER NOT NULL REFERENCES pumps(id),
    opening_reading REAL NOT NULL DEFAULT 0,
    closing_reading REAL NOT NULL DEFAULT 0,
    is_closed INTEGER NOT NULL DEFAULT 0,
    reconciled_at TEXT,
    UNIQUE(date, shift, pump_id)
);

INSERT OR IGNORE INTO fuel_types (name, unit, hsn_code, gst_rate) VALUES
    ('Petrol', 'Litre', '271012', 18),
    ('Diesel', 'Litre', '271019', 18);

INSERT OR IGNORE INTO expense_categories (name) VALUES
    ('Electricity'), ('Rent'), ('Wages'), ('Maintenance'),
    ('Transport'), ('Utilities'), ('Miscellaneous');

"""
