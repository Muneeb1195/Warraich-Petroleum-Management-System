from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QFormLayout, QGroupBox,
                               QDoubleSpinBox, QMessageBox, QTabWidget, QWidget,
                               QComboBox, QCheckBox)
from PySide6.QtCore import Qt
from database.settings import settings
from database.cloud_backup import is_connected, disconnect, has_secrets
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px 0 4px 0;")
        layout.addWidget(title)

        subtitle = QLabel("Configure business info, fuel rates, tax, and cloud backup")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px; padding: 0 0 12px 0;")
        layout.addWidget(subtitle)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Business info tab
        biz_tab = QWidget()
        biz_layout = QFormLayout(biz_tab)
        self.biz_name = QLineEdit(settings.business_name())
        self.biz_name.setToolTip("Name of your petrol pump business (appears on invoices)")
        self.biz_address = QLineEdit(settings.business_address())
        self.biz_address.setToolTip("Business address for invoices and receipts")
        self.biz_phone = QLineEdit(settings.business_phone())
        self.biz_phone.setToolTip("Contact phone number for your business")
        self.biz_gstin = QLineEdit(settings.gstin())
        self.biz_gstin.setToolTip("GST registration number (leave blank if not registered)")
        biz_layout.addRow("Business Name:", self.biz_name)
        biz_layout.addRow("Address:", self.biz_address)
        biz_layout.addRow("Phone:", self.biz_phone)
        biz_layout.addRow("GSTIN:", self.biz_gstin)
        tabs.addTab(biz_tab, "Business")

        # Fuel rates tab
        fuel_tab = QWidget()
        fuel_layout = QFormLayout(fuel_tab)
        self.petrol_rate = QDoubleSpinBox()
        self.petrol_rate.setRange(0, 9999)
        self.petrol_rate.setDecimals(2)
        self.petrol_rate.setValue(settings.fuel_rate("petrol"))
        self.petrol_rate.setToolTip("Selling price per litre of petrol (used in POS)")
        self.diesel_rate = QDoubleSpinBox()
        self.diesel_rate.setRange(0, 9999)
        self.diesel_rate.setDecimals(2)
        self.diesel_rate.setValue(settings.fuel_rate("diesel"))
        self.diesel_rate.setToolTip("Selling price per litre of diesel (used in POS)")
        fuel_layout.addRow(f"Petrol Rate ({CURRENCY_SYMBOL_RAW}/L):", self.petrol_rate)
        fuel_layout.addRow(f"Diesel Rate ({CURRENCY_SYMBOL_RAW}/L):", self.diesel_rate)
        tabs.addTab(fuel_tab, "Fuel Rates")

        # GST tab
        gst_tab = QWidget()
        gst_layout = QFormLayout(gst_tab)
        self.default_gst = QDoubleSpinBox()
        self.default_gst.setRange(0, 100)
        self.default_gst.setDecimals(2)
        self.default_gst.setValue(settings.default_gst_rate())
        self.default_gst.setToolTip("Default GST rate applied to new sales")
        self.hsn_petrol = QLineEdit(settings.hsn_code("petrol"))
        self.hsn_petrol.setToolTip("HSN code for petrol (used on GST invoices)")
        self.hsn_diesel = QLineEdit(settings.hsn_code("diesel"))
        self.hsn_diesel.setToolTip("HSN code for diesel (used on GST invoices)")
        self.hsn_lube = QLineEdit(settings.hsn_code("lube"))
        self.hsn_lube.setToolTip("HSN code for lubricants (used on GST invoices)")
        gst_layout.addRow("Default GST Rate (%):", self.default_gst)
        gst_layout.addRow("HSN Code - Petrol:", self.hsn_petrol)
        gst_layout.addRow("HSN Code - Diesel:", self.hsn_diesel)
        gst_layout.addRow("HSN Code - Lubricants:", self.hsn_lube)
        tabs.addTab(gst_tab, "GST")

        # Regional tab
        reg_tab = QWidget()
        reg_layout = QFormLayout(reg_tab)
        self.currency_symbol = QLineEdit(settings.currency_symbol())
        self.currency_symbol.setToolTip("Currency symbol shown on invoices and reports")
        self.date_format_combo = QComboBox()
        self.date_format_combo.setToolTip("How dates are displayed throughout the app")
        self.date_format_combo.addItems(["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
        idx = self.date_format_combo.findText(settings.date_format())
        if idx >= 0:
            self.date_format_combo.setCurrentIndex(idx)
        reg_layout.addRow("Currency Symbol:", self.currency_symbol)
        reg_layout.addRow("Date Format:", self.date_format_combo)
        tabs.addTab(reg_tab, "Regional")

        # Cloud Backup tab
        cloud_tab = QWidget()
        cloud_layout = QVBoxLayout(cloud_tab)
        cloud_layout.setSpacing(16)

        self.cloud_status = QLabel()
        self.cloud_status.setStyleSheet("font-size: 14px; padding: 8px;")
        cloud_layout.addWidget(self.cloud_status)

        self.cloud_connect_btn = QPushButton()
        self.cloud_connect_btn.setToolTip("Connect or disconnect Google Drive for automatic backups")
        self.cloud_connect_btn.clicked.connect(self._toggle_cloud)
        cloud_layout.addWidget(self.cloud_connect_btn)

        self.cloud_enabled_cb = QCheckBox("Enable automatic cloud backup")
        self.cloud_enabled_cb.setToolTip("When checked, new backups are automatically uploaded to Google Drive")
        self.cloud_enabled_cb.setChecked(settings.cloud_backup_enabled())
        cloud_layout.addWidget(self.cloud_enabled_cb)

        cloud_layout.addWidget(QLabel(f"Last backup: {settings.last_cloud_backup()}"))
        cloud_layout.addStretch()
        self._update_cloud_ui()
        tabs.addTab(cloud_tab, "Cloud Backup")

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save all settings changes")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Discard all unsaved changes")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _update_cloud_ui(self):
        if is_connected():
            self.cloud_status.setText("✅ Connected to Google Drive")
            self.cloud_status.setStyleSheet("color: #3fb950; font-size: 14px; padding: 8px;")
            self.cloud_connect_btn.setText("Disconnect Google Drive")
            self.cloud_connect_btn.setObjectName("dangerBtn")
        else:
            self.cloud_status.setText("❌ Not connected to Google Drive")
            self.cloud_status.setStyleSheet("color: #f85149; font-size: 14px; padding: 8px;")
            self.cloud_connect_btn.setText("Connect Google Drive")
            self.cloud_connect_btn.setObjectName("successBtn")

    def _toggle_cloud(self):
        if is_connected():
            reply = QMessageBox.question(self, "Disconnect",
                                          "Disconnect Google Drive? Cloud backups will stop.",
                                          QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                disconnect()
                self._update_cloud_ui()
        else:
            if not has_secrets():
                from database.cloud_backup import CLIENT_SECRETS_PATH
                QMessageBox.critical(
                    self, "Not Set Up",
                    f"client_secrets.json not found.\n\n"
                    f"To set up cloud backup:\n"
                    f"1. Go to https://console.cloud.google.com/\n"
                    f"2. Enable Google Drive API\n"
                    f"3. Create OAuth credentials (Desktop app)\n"
                    f"4. Download JSON and save as:\n"
                    f"   {CLIENT_SECRETS_PATH}"
                )
                return
            try:
                from database.cloud_backup import _get_drive
                QMessageBox.information(
                    self, "Connecting",
                    "A browser window will open. Sign in to your Google account and grant access.")
                _get_drive()
                self._update_cloud_ui()
                QMessageBox.information(self, "Connected", "Google Drive connected successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Connection Failed",
                                     f"Could not connect to Google Drive.\n\n{str(e)}")

    def _save(self):
        settings.set_business_info(
            self.biz_name.text(),
            self.biz_address.text(),
            self.biz_phone.text(),
            self.biz_gstin.text(),
        )
        settings.set_fuel_rate("petrol", self.petrol_rate.value())
        settings.set_fuel_rate("diesel", self.diesel_rate.value())
        settings.set("GST", "default_rate", str(self.default_gst.value()))
        settings.set("GST", "hsn_petrol", self.hsn_petrol.text())
        settings.set("GST", "hsn_diesel", self.hsn_diesel.text())
        settings.set("GST", "hsn_lube", self.hsn_lube.text())
        settings.set("Regional", "currency_symbol", self.currency_symbol.text())
        settings.set("Regional", "date_format", self.date_format_combo.currentText())
        settings.set_cloud_backup_enabled(self.cloud_enabled_cb.isChecked())
        settings.save()
        QMessageBox.information(self, "Saved", "Settings saved successfully.\nRestart the app for some changes to take effect.")
        self.accept()

    def refresh(self):
        pass
