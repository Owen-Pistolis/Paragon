from PyQt6.QtCore import (
    Qt, QSize
)
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget,
    QToolBar, QMenu, QToolButton, QLabel, QPushButton, 
)

class LoginGUI(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main  = main
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.init_login_tab()


    
    def init_login_tab(self):

        login_tab = QWidget()
        layout = QVBoxLayout(login_tab)

        # Account Header
        login_header = QLabel("Login by clicking the button below")
        login_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(login_header)

        # Login Section
        login_button = QPushButton("Login to Auth0")
        login_button.clicked.connect(self.main.auth.auth_server.login)
        layout.addWidget(login_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.tabs.addTab(login_tab, "Login")


class LoginToolBar(QToolBar):
    def __init__(self, main):
        super().__init__()

        self.main = main

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setMovable(False)
        self.setIconSize(QSize(24, 24))

        # Add Toolbar Dropdowns
        self.add_about_dropdown()
        self.add_login_dropdown()
    
    
    def add_about_dropdown(self):
        """
        Adds the About dropdown menu to the toolbar.
        """
        about_dropdown_button = QToolButton(self)
        about_dropdown_button.setText("About")
        about_dropdown_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        about_menu = QMenu(self)
        about_menu.addAction(QAction("About Us", self))
        about_dropdown_button.setMenu(about_menu)
        self.addWidget(about_dropdown_button)

    def add_login_dropdown(self):
        """
        Adds the Account dropdown menu to the toolbar.
        """
        account_dropdown_button = QToolButton(self)
        account_dropdown_button.setText("Account")
        account_dropdown_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        account_menu = QMenu(self)
        account_menu.addAction(QAction("Login", self))
        account_dropdown_button.setMenu(account_menu)
        self.addWidget(account_dropdown_button)