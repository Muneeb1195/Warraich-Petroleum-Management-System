# Desktop Version — Progress Report

## File Structure

```
petrol-pump/
├── main.py                          # Entry point (PySide6)
├── WarraichPetroleum.spec           # PyInstaller spec
├── requirements.txt
├── settings.ini
├── client_secrets.json              # Obfuscated Drive backup config
│
├── ui/
│   ├── main_window.py               # App window + tab nav
│   ├── dashboard.py                 # Dashboard with 3 charts
│   ├── settings_dialog.py
│   ├── welcome_dialog.py
│   │
│   ├── sales/
│   │   ├── pos.py                   # POS screen
│   │   ├── customer_list.py         # Customer CRUD
│   │   ├── invoice_pdf.py           # PDF invoice generator
│   │   └── quick_sale.py            # Quick sale popup
│   │
│   ├── inventory/
│   │   ├── tank_list.py
│   │   ├── pump_list.py
│   │   └── lube_list.py
│   │
│   ├── expenses/
│   │   └── expense_list.py
│   │
│   ├── staff/
│   │   ├── employee_list.py
│   │   └── attendance_widget.py
│   │
│   ├── payroll/
│   │   └── payroll_widget.py
│   │
│   ├── purchases/
│   │   └── purchase_list.py
│   │
│   └── reports/
│       ├── report_widget.py         # 6 report types
│       └── shift_reconciliation.py
│
├── models/                          # SQLAlchemy ORM models
│   ├── base.py, customer.py, employee.py, expense.py
│   ├── fuel.py, lube.py, payroll.py, purchase.py
│   ├── sale.py, supplier.py
│
├── database/
│   ├── connection.py                # DB engine + session
│   ├── schema.py                    # Create tables
│   ├── settings.py                  # App settings table
│   ├── backup.py                    # Local JSON backup
│   └── cloud_backup.py              # Google Drive backup
│
├── utils/
│   ├── paths.py                     # Path resolution
│   └── formatting.py                # Number/date formatting
│
└── .github/workflows/
    ├── release-desktop.yml          # Builds via PyInstaller (tag: v*)
    └── build.yml                    # Legacy CI
```

## Completed
- POS with fuel meter readings (opening/closing), lube sales, cart, GST calc, checkout
- Inventory CRUD (tanks, pumps, lubricants)
- Customer CRUD with balance tracking, credit limit
- Expense recording with categories
- Employee management + daily attendance (Present/Absent/Half/Leave) + payroll calc
- 6 report types (Daily Summary, P&L, Sales, Stock, Expense, Payroll)
- Dashboard: stats cards + 3 charts (trend, payment split, top products)
- Shift reconciliation (opening vs closing readings, vs actual sales)
- Google Drive cloud backup (embedded obfuscated secrets, local OAuth server)
- Auto backup timer
- Invoice PDF generation
- Purchase management
- PyInstaller build via GitHub Actions (v1.5 tagged and released)

## Remaining
- Nothing significant — app is feature-complete at v1.5
