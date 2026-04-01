import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QWidget, QListWidget, QStackedWidget,
                             QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #f3f4f6;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #e0e7ff;
                color: #4338ca;
                font-weight: bold;
            }
            QFrame#MainContent {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
            QLabel#Header {
                font-size: 18px;
                font-weight: bold;
                color: #1f2937;
            }
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Left Menu
        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(160)
        self.menu_list.addItem("Account")
        self.menu_list.addItem("General")
        self.menu_list.addItem("Plugins")
        
        # Right Stacked Widget
        self.stack = QStackedWidget()
        self.stack.setObjectName("MainContent")
        
        # Account Page
        account_page = QFrame()
        account_layout = QVBoxLayout(account_page)
        
        header = QLabel("Account Settings")
        header.setObjectName("Header")
        account_layout.addWidget(header)
        
        info_label = QLabel("You can manage your Qwen account authentication here.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #4b5563; margin-top: 10px; margin-bottom: 20px;")
        account_layout.addWidget(info_label)
        
        self.login_btn = QPushButton("Login / Re-authenticate")
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setStyleSheet("background-color: #ef4444;")
        
        account_layout.addWidget(self.login_btn)
        account_layout.addWidget(self.logout_btn)
        account_layout.addStretch()

        # Connect signals (will be configured by parent)
        
        # Other Pages
        general_page = QFrame()
        general_layout = QVBoxLayout(general_page)
        general_layout.addWidget(QLabel("General Settings"))
        general_layout.addStretch()

        plugins_page = QFrame()
        plugins_layout = QVBoxLayout(plugins_page)
        plugins_layout.addWidget(QLabel("Plugins Management"))
        plugins_layout.addStretch()

        self.stack.addWidget(account_page)
        self.stack.addWidget(general_page)
        self.stack.addWidget(plugins_page)

        self.menu_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.menu_list.setCurrentRow(0)

        layout.addWidget(self.menu_list)
        layout.addWidget(self.stack)

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dl = SettingsDialog()
    dl.show()
    sys.exit(app.exec())
