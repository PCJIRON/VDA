import pathlib
import re

def fix():
    fa_path = pathlib.Path('qwen_desktop/ui/floating_assistant.py')
    fa_code = fa_path.read_text('utf-8')
    
    # 1. Stop floating block from triggering login directly
    old_float_login = """                    if not getattr(self, "oauth", None) or not self.oauth.is_authenticated():
                        self.trigger_login()
                    else:
                        self.toggle_expand()"""
    new_float_login = """                    self.toggle_expand()"""
    
    if old_float_login in fa_code:
        fa_code = fa_code.replace(old_float_login, new_float_login)
        print("Patched floating trigger.")

    # 2. Remove other forced login calls on startup/boot (if any)
    old_auth = """    def toggle_auth(self):
        if not self.oauth:
            self.trigger_login()
            return"""
    new_auth = """    def toggle_auth(self):
        if not self.oauth:
            # self.trigger_login() -> Removed to prevent random popup
            return"""
    if old_auth in fa_code:
        fa_code = fa_code.replace(old_auth, new_auth)
        print("Patched toggle_auth.")

    # Also check if it randomly launches QwenAuthDialog on start
    old_check = """        self._check_auth()"""
    new_check = """        self._check_auth()  # Auth checked but don't force popup if empty"""
    fa_code = fa_code.replace(old_check, new_check)

    fa_path.write_text(fa_code, 'utf-8')

    # 3. Completely rewrite settings_dialog.py
    sd_path = pathlib.Path('qwen_desktop/ui/settings_dialog.py')
    new_settings = '''import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QWidget, QListWidget, QListWidgetItem, QStackedWidget, 
                             QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor, QPainterPath

class RoundedAvatar(QWidget):
    def __init__(self, size=80, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Circle background
        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.fillPath(path, QColor("#e0e7ff"))
        
        # Draw user icon simple representation or use unicode
        painter.setPen(QColor("#9333ea"))
        font = self.font()
        font.setFamily("Segoe Fluent Icons")
        font.setPointSize(36)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "\\uE77B")  # Person icon

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(650, 480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._dragging = False
        self._drag_pos = QPoint()

        # Custom styling
        self.setStyleSheet("""
            QWidget#MainContainer {
                background-color: transparent;
            }
            QFrame#Sidebar {
                background-color: #f9fafb;
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
            }
            QFrame#Content {
                background-color: #ffffff;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
            }
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 15px;
                border-radius: 8px;
                margin-left: 10px;
                margin-right: 10px;
                margin-bottom: 2px;
                color: #4b5563;
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
            }
            QListWidget::item:selected {
                background-color: #f3e8ff;
                color: #9333ea;
            }
            QListWidget::item:hover:!selected {
                background-color: #f3f4f6;
            }
            QLabel#SidebarTitle {
                font-size: 16px;
                font-weight: bold;
                color: #1f2937;
                padding-left: 15px;
                padding-top: 15px;
                padding-bottom: 15px;
                font-family: 'Segoe UI';
            }
            QLabel#ContentTitle {
                font-size: 16px;
                font-weight: bold;
                color: #1f2937;
                padding: 15px;
                font-family: 'Segoe UI';
            }
            QPushButton#CloseBtn {
                background-color: transparent;
                color: #6b7280;
                font-size: 14px;
                font-family: 'Segoe UI';
                border: none;
            }
            QPushButton#CloseBtn:hover {
                color: #1f2937;
            }
            QLabel#UserEmail {
                font-size: 18px;
                font-weight: bold;
                color: #1f2937;
                font-family: 'Segoe UI';
            }
            QLabel#PlanText {
                font-size: 13px;
                color: #6b7280;
                font-family: 'Segoe UI';
            }
            QPushButton#LogOutBtn {
                background-color: #f3f4f6;
                color: #ef4444;
                border-radius: 16px;
                padding: 8px 30px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }
            QPushButton#LogOutBtn:hover {
                background-color: #fee2e2;
            }
        """)

        # Main Layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Frame
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Sidebar Title
        title_lbl = QLabel("\\uE713  Settings")
        title_lbl.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title_lbl)

        # Menu List
        self.menu_list = QListWidget()
        
        item_acc = QListWidgetItem("\\uE77B  Account")
        self.menu_list.addItem(item_acc)
        item_mcp = QListWidgetItem("\\uE734  MCP Servers")
        self.menu_list.addItem(item_mcp)
        item_plug = QListWidgetItem("\\uE718  Plugins")
        self.menu_list.addItem(item_plug)
        
        self.menu_list.setCurrentRow(0)
        sidebar_layout.addWidget(self.menu_list)
        
        # 2. Content Frame
        self.content = QFrame()
        self.content.setObjectName("Content")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Content Header
        header_widget = QWidget()
        header_widget.setFixedHeight(50)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 15, 0)
        
        self.content_title = QLabel("Account")
        self.content_title.setObjectName("ContentTitle")
        
        self.close_btn = QPushButton("\\uE711")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(self.content_title)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        
        content_layout.addWidget(header_widget)

        # Divider line
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #f3f4f6;")
        content_layout.addWidget(div)

        # Stacked Widget
        self.stack = QStackedWidget()

        #  Page: Account
        acc_page = QWidget()
        acc_layout = QVBoxLayout(acc_page)
        acc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Avatar
        self.avatar = RoundedAvatar(80)
        acc_layout.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignHCenter)
        acc_layout.addSpacing(20)

        # Status text
        self.email_lbl = QLabel("Not logged in")
        self.email_lbl.setObjectName("UserEmail")
        acc_layout.addWidget(self.email_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.plan_lbl = QLabel("Please login via Settings > Account")
        self.plan_lbl.setObjectName("PlanText")
        acc_layout.addWidget(self.plan_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        
        acc_layout.addSpacing(20)

        # Log out/in Button
        self.login_btn = QPushButton("[$] Login")
        self.login_btn.setObjectName("LogOutBtn")
        self.login_btn.hide() # Hidden by default
        
        self.logout_btn = QPushButton("[-> Log out")
        self.logout_btn.setObjectName("LogOutBtn")
        
        # In QwenDesktop FloatingAssistant hooks these exact buttons
        acc_layout.addWidget(self.login_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        acc_layout.addWidget(self.logout_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self.stack.addWidget(acc_page)

        #  Page: MCP
        mcp_page = QWidget()
        mcp_layout = QVBoxLayout(mcp_page)
        mcp_layout.addWidget(QLabel("MCP Servers Settings"), 0, Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(mcp_page)

        #  Page: Plugins
        plug_page = QWidget()
        plug_layout = QVBoxLayout(plug_page)
        plug_layout.addWidget(QLabel("Plugins Settings"), 0, Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(plug_page)

        content_layout.addWidget(self.stack)

        # Add to main
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content)

        # Hooks
        self.menu_list.currentRowChanged.connect(self._change_page)

        # Wait until showEvent to properly display login status
        
    def _change_page(self, i):
        self.stack.setCurrentIndex(i)
        if i == 0: self.content_title.setText("Account")
        elif i == 1: self.content_title.setText("MCP Servers")
        elif i == 2: self.content_title.setText("Plugins")

    def showEvent(self, event):
        parent_has_oauth = hasattr(self.parent(), "oauth") and self.parent().oauth is not None
        is_auth = False
        if parent_has_oauth:
            is_auth = self.parent().oauth.is_authenticated()
        
        if is_auth:
            self.email_lbl.setText("user@example.com") # Placeholder for demo
            if hasattr(self.parent().oauth, 'credentials') and isinstance(self.parent().oauth.credentials, dict):
                email = self.parent().oauth.credentials.get("email", "user@example.com")
                self.email_lbl.setText(email)

            self.plan_lbl.setText("Pro Plan Member")
            self.login_btn.hide()
            self.logout_btn.show()
        else:
            self.email_lbl.setText("Not logged in")
            self.plan_lbl.setText("Please sign in to continue")
            self.logout_btn.hide()
            self.login_btn.show()
            self.login_btn.setStyleSheet("background-color: #f3f4f6; color: #4b5563; border-radius: 16px; padding: 8px 30px; font-weight: bold;")
            self.login_btn.setText("Login")

        super().showEvent(event)

    # Window dragging logic for Frameless
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        event.accept()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dl = SettingsDialog()
    dl.show()
    sys.exit(app.exec())
'''
    sd_path.write_text(new_settings, 'utf-8')
    print("SettingsDialog rewritten.")

if __name__ == "__main__":
    fix()
