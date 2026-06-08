# Android Version — Progress Report

## File Structure

```
android/
├── main.py                              # Kivy entry point (ScreenManager + init_db)
├── buildozer.spec                       # Build config (API 34, min SDK 21, NDK 27)
├── requirements_android.txt
│
├── libs/                                # Copied from desktop, zero code changes except paths.py
│   ├── database/
│   │   ├── connection.py                # DB engine + session factory
│   │   ├── schema.py                    # 10 tables created on first run
│   │   ├── settings.py                  # Key-value app settings
│   │   ├── backup.py                    # Local JSON backup
│   │   └── cloud_backup.py              # Google Drive backup (embedded secrets)
│   │
│   ├── models/                          # Identical to desktop models
│   │   ├── base.py, customer.py, employee.py, expense.py
│   │   ├── fuel.py, lube.py, payroll.py, purchase.py
│   │   ├── sale.py, supplier.py
│   │
│   └── utils/
│       ├── paths.py                     # Android-aware (env vars + pyjnius fallback)
│       └── formatting.py                # Identical to desktop
│
└── ui/
    ├── __init__.py
    ├── main_screen.kv                   # Sidebar nav layout
    ├── main_screen.py                   # Sidebar button wiring
    │
    ├── dashboard_screen.kv              # 8 stat cards, Quick Sale, Close Day popup
    ├── dashboard_screen.py
    ├── pos_screen.kv                    # Fuel meters + Lube products + Cart + Checkout
    ├── pos_screen.py
    ├── inventory_screen.kv              # Tabs: Tanks, Pumps, Lubricants
    ├── inventory_screen.py
    ├── customers_screen.kv              # Customer list + add/edit form
    ├── customers_screen.py
    ├── expenses_screen.kv               # Expense list + inline category add
    ├── expenses_screen.py
    ├── staff_screen.kv                  # Tabs: Employees, Attendance, Payroll
    ├── staff_screen.py
    ├── reports_screen.kv                # 6 report types + Excel export
    └── reports_screen.py
```

## Completed
- Full Kivy project scaffold in `android/` (self-contained, no desktop file changes)
- All models, database, and utils copied from desktop (identical code)
- Android-aware path resolution (env vars `ANDROID_PRIVATE`, fallback to pyjnius)
- 7 screens fully implemented:
  - **Dashboard**: 8 stat cards (today sales, month sales, profit, expenses, tank count, lube, staff, pending payroll) + Quick Sale + Close Day summary popup
  - **POS**: Fuel sales with opening/closing meter readings per pump, lube product tab, cart with quantity + remove, GST calc (taxable → CGST/SGST → round off → grand total), customer+payment selectors, checkout writes DB
  - **Inventory**: 3-tab CRUD for Tanks, Pumps, Lubricants with search, popup add/edit/delete forms
  - **Customers**: List with search, add/edit form (name, phone, address, GSTIN, credit limit), balance color coding
  - **Expenses**: List with search, date+amount+description fields, category spinner with inline create-new-category
  - **Staff**: 3 tabs — Employees CRUD with active/inactive toggle, Attendance (date + shift, per-employee status buttons + Mark All), Payroll (month/year, calculate, mark paid)
  - **Reports**: 6 report types with date range, dynamic table, total summary, Excel export via openpyxl
- All screens wired in `main.py` ScreenManager + sidebar navigation
- GitHub Actions CI (`build-android.yml`) for automated APK builds
- Separated tag conventions: `v*-android` = APK, `v*` = desktop release

## Remaining — Blocked
- **APK build fails** — CI builds keep failing (currently on attempt #5). Last attempt removed `pyjnius` dep (likely JDK header issue). Awaiting build result.
- Shift reconciliation screen
- Purchase management screen
- Settings screen
- Cloud backup re-integration (pydrive2 deferred until base APK builds)
- Dashboard charts (kivy-garden.graph or matplotlib)
- Splash screen + app icon
- PDF invoice viewer
- Play Store deployment

## Key Notes
- `libs/` added to sys.path so `from models.x import Y` works identical to desktop
- Desktop and Android use the same DB schema — backups are compatible between both
- `buildozer.spec` has `log_level = 2` for detailed CI logs
- Removed `pydrive2`, `google-auth-oauthlib`, `pyjnius` from requirements to minimize build deps
- Current requirements: `python3, kivy==2.2.0, openpyxl, requests` (reportlab removed — unused on Android; Kivy pinned to 2.2.0 for stability)
- Build configured for single arch (`arm64-v8a`) — 2x faster than dual-arch
- CI: Python 3.11, JDK 17, 2-hour timeout, no retry loop, cache restore-keys fallback
- Placeholder splash/icon assets created in `assets/`
- All `pydrive2`/`jnius` imports made fully lazy (inside functions) — p4a won't try to resolve them at build time
- `threading` import removed from module level in `cloud_backup.py`
