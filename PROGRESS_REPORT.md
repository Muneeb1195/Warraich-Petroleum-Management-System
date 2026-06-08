# Warraich Petroleum Management System — Progress Report

## Project Structure

```
petrol-pump/
├── main.py                          # Desktop entry (PySide6)
├── ui/                              # Desktop UI screens (PySide6)
│   ├── dashboard.py
│   ├── sales/pos.py, customer_list.py, invoice_pdf.py
│   ├── inventory/tank_list.py, pump_list.py, lube_list.py
│   ├── expenses/expense_list.py
│   ├── staff/employee_list.py, attendance_widget.py
│   ├── payroll/payroll_widget.py
│   ├── reports/report_widget.py, shift_reconciliation.py
│   ├── purchases/purchase_list.py
│   └── settings_dialog.py
├── models/                          # Desktop DB models (shared logic)
├── database/                        # Desktop DB connection + settings
├── utils/                           # Desktop utilities
├── .github/workflows/
│   ├── build-android.yml            # Android APK (tag: v*-android)
│   └── release-desktop.yml          # Desktop release (tag: v*)
│
android/                             # Android port (Kivy, self-contained)
├── main.py                          # Kivy entry point
├── buildozer.spec                   # Build config (API 34, min 21)
├── requirements_android.txt
├── libs/                            # Copied from desktop, zero mods except paths.py
│   ├── database/  (connection, schema, settings, backup, cloud_backup)
│   ├── models/    (all 10 models)
│   └── utils/     (formatting, paths with Android override)
└── ui/
    ├── main_screen.kv/py            # Sidebar nav + content area
    ├── dashboard_screen.kv/py       # 8 stat cards, Quick Sale, Close Day
    ├── pos_screen.kv/py             # Fuel/Lube tabs + cart + checkout
    ├── inventory_screen.kv/py       # Tanks, Pumps, Lubricants CRUD tabs
    ├── customers_screen.kv/py       # Customer CRUD + search
    ├── expenses_screen.kv/py        # Expense CRUD + inline category add
    ├── staff_screen.kv/py           # Employees, Attendance, Payroll tabs
    └── reports_screen.kv/py         # 6 report types + Excel export
```

## Desktop — Completed
- Full POS with fuel meter readings, lube sales, cart, GST calc, checkout
- Inventory CRUD (tanks, pumps, lubricants)
- Customer CRUD with balance tracking
- Expense recording with categories
- Staff management + daily attendance + payroll calc
- 6 report types (Daily Summary, P&L, Sales, Stock, Expense, Payroll)
- Dashboard with stat cards + 3 charts (trend, payment split, top products)
- Shift reconciliation (opening/closing readings vs sales)
- Google Drive cloud backup (embedded obfuscated secrets, OAuth local server)
- Auto backup timer
- Invoice PDF generation
- Purchase management

## Desktop — Pending
- Nothing significant (app is feature-complete at v1.5)

## Android — Completed
- Full project scaffold in `android/` folder (Kivy, self-contained)
- All base libs copied (models, database, utils)
- Kivy entry point with ScreenManager + init_db + auto_backup
- Main screen with dark sidebar navigation
- Dashboard: 8 stat cards (today sales, month, profit, expenses, tanks, lube, staff, pending payroll), Quick Sale + Close Day actions
- POS: Fuel sales with opening/closing meter readings, lube product selection, cart with remove, GST calc (taxable → CGST/SGST → round off → grand total), checkout writes to DB, customer + payment selectors
- Inventory: 3-tab CRUD (Tanks, Pumps, Lubricants) with search, edit/delete, popup forms
- Customers: CRUD list with search, inline form (name, phone, address, GSTIN, credit limit), balance coloring
- Expenses: CRUD with category spinner (+ inline add category), date, amount, description, search
- Staff: 3 tabs — Employees (CRUD, active/inactive toggle), Attendance (date+shift selector, per-employee Present/Absent/Half Day/Leave buttons, Mark All), Payroll (month/year selector, calculate button, mark paid per employee)
- Reports: 6 report types with date range selector, dynamic table rendering, summary label, Excel export via openpyxl
- Android-aware paths (env vars with pyjnius fallback)
- GitHub Actions CI for automated APK builds
- Separate tag conventions (`v*-android` for APK, `v*` for desktop)

## Android — Pending
- Build first working APK (CI fixes applied: single arch arm64-v8a, removed reportlab, JDK 17, Python 3.11, no retry loop)
- Shift reconciliation screen
- Purchase management screen
- Settings screen
- Cloud backup integration (pydrive2 — deferred until base APK works)
- PDF viewer for invoices
- Dashboard charts (kivy-garden.graph or matplotlib)
- Proper splash screen and app icon assets
- Play Store deployment

## Key Decisions
- `android/` folder is self-contained with copied (not symlinked) libs — manual sync needed if desktop models change
- Kivy over Flutter — business logic reuse (~50% of code) vs complete rewrite
- Embedded obfuscated client_secrets (same approach as desktop)
- `libs/` on sys.path so `from models.x import y` / `from database.x import y` works unchanged
