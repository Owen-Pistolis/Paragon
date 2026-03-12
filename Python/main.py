import sys
import logging
import os
from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QObject
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QToolBar, QMenu, QToolButton
from main_gui import MainGUI, MainToolBar, load_workflows
from login_gui import LoginGUI, LoginToolBar
import threading
from auth import Auth

class Paragon(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Paragon AI: A Model of Excellence")
        self.setGeometry(100, 100, 800, 600)

        self.current_theme = "dark"
        self.apply_theme()

        self.auth = Auth(self)

        self.communicator = Communicator()
        self.communicator.login.connect(self.login)
        self.communicator.logout.connect(self.logout)

        try:
            workflows = load_workflows()
            logging.info(f"Loaded workflows: {list(workflows.keys())}")
        except FileNotFoundError:
            logging.warning("Workflows file not found. Starting with no workflows.")
            workflows = {}
        except Exception as e:
            logging.error(f"Error loading workflows: {e}")
            workflows = {}

        # Initialize Main GUI
        try:
            self.main_gui = MainGUI(workflows, self)
            logging.info("Main GUI initialized successfully.")
        except Exception as e:
            logging.critical(f"Failed to initialize GUI: {e}")
            sys.exit(1)

        try:
            self.login_gui = LoginGUI(self)
            logging.info("Login GUI initialized successfully")
        except Exception as e:
            logging.critical(f"Failed to initialize GUI: {e}")
            sys.exit(1)

        # Toolbars should be referenced directly to prevent garbage collection
        main_toolbar = MainToolBar(self)
        login_toolbar = LoginToolBar(self)

        self.toolbars = {
            "main": main_toolbar,
            "login": login_toolbar
        }

        # Set window icon with correct path
        icon_path = os.path.join(os.path.dirname(__file__), 'content', 'favicon.ico')
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.setWindowIcon(app_icon)
            # Set the taskbar icon
            if QApplication.instance():
                QApplication.instance().setWindowIcon(app_icon)
            logging.info(f"Application icon set from: {icon_path}")
        else:
            logging.warning(f"favicon.ico not found at: {icon_path}")

        # Stack widget setup
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.stack.addWidget(self.main_gui)
        self.stack.addWidget(self.login_gui)

        # Authentication state
        self.isAuthenticated = self.auth.auth_server.is_authenticated()

        # Set initial view and toolbar based on authentication state
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbars["login"])
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbars["main"])
        if(not self.isAuthenticated):
            
            self.stack.setCurrentWidget(self.login_gui)
            self.toolbars["main"].hide()
            print("You are not authenticated")
        else:
            self.stack.setCurrentWidget(self.main_gui)
            self.toolbars["login"].hide()
            print("You are authenticated")

    def switch_gui(self, index):
        self.stack.setCurrentIndex(index)
    
    def login(self, message):

        self.switch_gui(0)
        self.toolbars["login"].hide()
        self.toolbars["main"].show()
        logging.info(message)
    
    def logout(self, message):
        self.switch_gui(1)
        self.toolbars["main"].hide()
        self.toolbars["login"].show()
        logging.info(message)
    
    def apply_theme(self):
        """
        Applies the current theme to the application with consistent toolbar colors.
        Uses Qt-compatible style properties.
        """
        common_styles = """
            * { font-family: 'Roboto', sans-serif; font-size: 14px; }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
            QLineEdit, QTextEdit {
                border: 1px solid #fd7014;
                border-radius: 5px;
                padding: 6px;
            }
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                font-weight: bold;
            }
            QMenuBar {
                padding: 4px;
                border-bottom: 1px solid #fd7014;
            }
            QMenuBar::item {
                padding: 4px 10px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #fd7014;
            }
        """
        if self.current_theme == "light":
            self.setStyleSheet(f"""
                {common_styles}
                QMainWindow {{ background-color: #FCFAFF; color: #222831; }}
                QLabel {{ color: #222831; font-size: 16px; font-weight: bold; }}
                QPushButton {{ 
                    background-color: #fd7014; 
                    color: #FCFAFF;
                    border: 2px solid transparent;
                }}
                QPushButton:hover {{ 
                    background-color: #fd8f47; 
                    color: #222831;
                    border: 2px solid #fd7014;
                }}
                QLineEdit, QTextEdit {{ background-color: #FFFFFF; color: #222831; }}
                QTabBar::tab {{ background: #FFFFFF; color: #222831; }}
                QTabBar::tab:selected {{ background: #fd7014; color: #FCFAFF; }}
                QMenuBar {{ background-color: #FCFAFF; color: #222831; }}
                QMenuBar::item {{ color: #222831; }}
                QMenuBar::item:selected {{ background-color: #fd7014; color: #FCFAFF; }}
            """)
        else:
            self.setStyleSheet(f"""
                {common_styles}
                QMainWindow {{ background-color: #0d0f13; color: #FCFAFF; }}
                QLabel {{ color: #FCFAFF; font-size: 16px; font-weight: bold; }}
                QPushButton {{ 
                    background-color: #fd7014; 
                    color: #222831;
                    border: 2px solid transparent;
                }}
                QPushButton:hover {{ 
                    background-color: #fd8f47; 
                    color: #0d0f13;
                    border: 2px solid #fd7014;
                }}
                QLineEdit, QTextEdit {{ background-color: #222831; color: #FCFAFF; }}
                QTabBar::tab {{ background: #222831; color: #FCFAFF; }}
                QTabBar::tab:selected {{ background: #fd7014; color: #222831; }}
                QMenuBar {{ background-color: #222831; color: #FCFAFF; }}
                QMenuBar::item {{ color: #FCFAFF; }}
                QMenuBar::item:selected {{ background-color: #fd7014; color: #222831; }}
            """)

    def toggle_theme(self):
        """
        Toggles between light and dark themes.
        """
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

class Communicator(QObject):

    login = pyqtSignal(str)
    logout = pyqtSignal(str)

def setup_logging():
    """Sets up logging configuration."""
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/workflow_execution.log", mode="a"),
                logging.StreamHandler()
            ]
        )
        logging.info("Logging is set up successfully.")
    except Exception as e:
        print(f"Failed to set up logging: {e}")
        sys.exit(1)

setup_logging()
app = QApplication(sys.argv)
app.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance
window = Paragon()
window.show()
# Start the Qt event loop
try:
    sys.exit(app.exec())
except Exception as e:
    logging.error(f"An error occurred during the Qt event loop: {e}")
