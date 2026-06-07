from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Warraich Petroleum")
        self.setMinimumSize(550, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 28, 32, 24)

        title = QLabel("Welcome to Warraich Petroleum")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #f0f6fc;")
        layout.addWidget(title)

        subtitle = QLabel("Your complete petrol pump management system")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #8b949e; font-size: 13px; padding-bottom: 8px;")
        layout.addWidget(subtitle)

        steps = [
            ("1", "⛽", "Set Up Inventory",
             "Add your fuel tanks, dispensing pumps, and lubricant products.\n"
             "Navigate to Inventory to configure what you sell."),
            ("2", "🧾", "Record Sales",
             "Go to POS / Sales to ring up customer purchases.\n"
             "Enter meter readings for fuel, or select products for lubricants."),
            ("3", "📈", "Track & Report",
             "View your dashboard for real-time KPIs.\n"
             "Generate reports, manage payroll, and back up your data securely."),
        ]

        for num, icon, step_title, desc in steps:
            card = QLabel()
            card.setStyleSheet(
                "background-color: #161b22; border: 1px solid #21262d; "
                "border-radius: 8px; padding: 16px;"
            )
            card.setWordWrap(True)
            card.setText(
                f'<table><tr>'
                f'<td valign="top" width="40"><span style="font-size: 24px;">{icon}</span></td>'
                f'<td valign="top">'
                f'<b style="color: #f0f6fc; font-size: 14px;">{step_title}</b><br>'
                f'<span style="color: #8b949e; font-size: 12px;">{desc}</span>'
                f'</td>'
                f'</tr></table>'
            )
            layout.addWidget(card)

        layout.addSpacing(8)

        self.skip_check = QCheckBox("Don't show this again")
        self.skip_check.setStyleSheet("color: #8b949e; font-size: 12px;")
        layout.addWidget(self.skip_check)

        start_btn = QPushButton("Get Started")
        start_btn.setObjectName("successBtn")
        start_btn.setMinimumHeight(44)
        start_btn.setStyleSheet("font-size: 15px; font-weight: bold; border-radius: 8px;")
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn)

    def dont_show_again(self):
        return self.skip_check.isChecked()
