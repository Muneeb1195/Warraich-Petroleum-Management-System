import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, Qt
from database.connection import init_db
from database.settings import settings
from database.backup import start_auto_backup
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Petrol Pump Management")
    app.setOrganizationName("Warraich Petroleum")

    style_path = Path(__file__).resolve().parent / "resources" / "style.qss"
    if style_path.exists():
        with open(style_path) as f:
            app.setStyleSheet(f.read())

    init_db()
    start_auto_backup()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
