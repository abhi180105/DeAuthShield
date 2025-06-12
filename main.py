# main.py
from PyQt6.QtWidgets import QApplication
from gui import DeAuthShieldGUI
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeAuthShieldGUI()
    window.show()
    sys.exit(app.exec())
