from PyQt6.QtCore import (
    Qt, QSize, QThread, pyqtSignal, QTimer, QEvent, QMetaObject, Q_ARG
)
from PyQt6.QtGui import QIcon, QAction, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QToolBar, QMenu, QToolButton, QLabel, QTextEdit, QPushButton, 
    QHBoxLayout, QInputDialog, QMessageBox, QListWidget, QLineEdit, 
    QDialog, QGroupBox, QGridLayout, QSpinBox, QFileDialog, QTreeView
)
import logging
import json
import os
from cryptography.fernet import Fernet as fernet
from workflowWizard import LLMWizardDialog
import threading
import shared
import time
import sys
import workflow_system  # Import your workflow_system.py module
import psutil
from datetime import datetime
import requests
import math
import uuid
from dataFormat import JsonChunk
from datetime import datetime

class WorkflowCompletionEvent(QEvent):
    """
    Custom event for workflow completion.
    """
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, workflow_name, success, message):
        super().__init__(self.EVENT_TYPE)
        self.workflow_name = workflow_name
        self.success = success
        self.message = message


class MainGUI(QWidget):
    """
    Main GUI window for managing workflows with tabs, a toolbar, and theme support.
    """

    def __init__(self, workflows, main, execute_action_callback=None):
        """
        Initializes the GUI.

        Args:
            workflows (dict): The workflows loaded from the JSON file.
            execute_action_callback (callable): Function to execute a workflow action.
        """
        super().__init__()
        self.main = main
        # Load API key if available
        self.api_key = None
        self.load_api_key()

        self.workflows = workflows or {}
        self.workflows_path = "workflows.json"
        self.execute_action_callback = execute_action_callback

        # Initialize the cipher for encryption/decryption
        self.init_cipher()

        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Add tabs
        self.init_tabs()

        # Start processing queues
        self.start_queue_processors()


    def show_recording_info(self):
        """
        Shows information about what the recording system captures.
        """
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("System Recording Information")
        info_dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Add header
        header = QLabel("⚠️ System Recording Information")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF6B6B;")
        layout.addWidget(header)
        
        # Add information text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
            <p>The system recording functionality captures:</p>
            <ul>
                <li><b>Mouse Actions:</b> Clicks, movements, scrolling</li>
                <li><b>Keyboard Actions:</b> Key presses, combinations</li>
                <li><b>Window Information:</b> Active windows, focus changes</li>
                <li><b>System Events:</b> Application starts/stops</li>
                <li><b>Screenshots:</b> For context of actions</li>
                <li><b>File Operations:</b> File system changes</li>
            </ul>
            <p>This data is used to:</p>
            <ul>
                <li>Create automated workflows</li>
                <li>Analyze user interactions</li>
                <li>Improve system automation</li>
            </ul>
            <p style="color: #FF6B6B;"><b>Note:</b> Do not record actions involving sensitive information. By using this software, you agree to the collection and use of this data as described and our terms of service.</p>
            <p><b>Keyboard Shortcuts:</b></p>
            <ul>
                <li>F9 - Start/Pause/Resume Recording</li>
                <li>F10 - Stop Recording</li>
            </ul>
        """)
        layout.addWidget(info_text)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(info_dialog.accept)
        layout.addWidget(close_button)
        
        info_dialog.setLayout(layout)
        info_dialog.exec()

    def init_tabs(self):
        """
        Initializes the main tabbed layout with tabs in the specified order:
        Account, Credentials, Workflows, System Recording, Documents and Content, and Logging.
        """
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Add tabs in the desired order
        self.init_account_tab()        # 1. Account
        self.init_credentials_tab()    # 2. Credentials
        self.init_workflows_tab()      # 3. Workflows
        self.init_recording_tab()      # 4. System Recording
        self.init_documents_tab()      # 5. Documents and Content
        self.init_logging_tab()        # 6. Logging

    def init_account_tab(self):
        """
        Initializes the Account tab with Login, Billing/API Usage, and Subscription sections.
        """
        account_tab = QWidget()
        layout = QVBoxLayout(account_tab)

        # Account Header
        account_header = QLabel("Account Information")
        account_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(account_header)

        api_test = QPushButton("Send Test Data")
        api_test.clicked.connect(self.getWeather)
        layout.addWidget(api_test)

        self.tabs.addTab(account_tab, "Account")

    def getWeather(self):

        with open("large_json_63MB.json") as file:
            chunk_size = 1024 * 512
            json_string = file.read()
            total_size = len(json_string.encode("utf-8"))
            total_chunks = math.ceil(total_size/chunk_size)
            group_id = uuid.uuid4()
            timestamp = datetime.now()
            headers = {"Content-Type": "application/json"}
            print(total_chunks)
            for count in range(total_chunks):
                start = count * chunk_size
                current_chunk = JsonChunk(count + 1, total_chunks, json_string[start: start + chunk_size], uuid.uuid4(), group_id, timestamp)
                # response = self.main.auth.session.get("https://paragonai.io/api/weatherforecast")
                response = self.main.auth.session.post("https://paragonai.io/api/JsonChunks/uploadChunk", json=current_chunk.to_dict(), headers=headers)
                response_code = response.status_code
                print(response_code, response.text)

    def init_workflows_tab(self):
        """
        Initializes the Workflows tab with Workflow Wizard at the top.
        """
        workflows_tab = QWidget()
        layout = QVBoxLayout(workflows_tab)

        # Add Workflow Wizard button at the top with system orange color and proper text contrast
        wizard_button = QPushButton("Workflow Wizard")
        wizard_button.clicked.connect(self.open_workflow_wizard)
        wizard_button.setStyleSheet("""
            QPushButton {
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                background-color: #fd7014;
                color: #222831;
                border-radius: 4px;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #fd8f47;
                color: #222831;
            }
        """)
        layout.addWidget(wizard_button)

        # Add workflow list section
        layout.addWidget(QLabel("Available Workflows"))
        self.workflow_list = QListWidget()
        self.update_workflow_listbox()
        layout.addWidget(self.workflow_list)

        # Workflow action buttons in original layout
        button_layout = QHBoxLayout()
        start_button = QPushButton("Start Workflow")
        stop_button = QPushButton("Stop Workflow")
        edit_button = QPushButton("Edit Workflow")
        delete_button = QPushButton("Delete Workflow")

        start_button.clicked.connect(self.execute_selected_workflow)
        stop_button.clicked.connect(self.stop_workflow)
        edit_button.clicked.connect(self.edit_selected_workflow)
        delete_button.clicked.connect(self.delete_selected_workflow)

        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)

        self.tabs.addTab(workflows_tab, "Workflows")

        # Running workflows list
        layout.addWidget(QLabel("Running Workflows"))
        self.running_workflows_list = QListWidget()
        layout.addWidget(self.running_workflows_list)


#REVISIT FOR NEW WORKFLOW_SYSTEM.PY
    def validate_workflow(self, workflow):
        """
        Validates the workflow structure and provides detailed error messages.
        Expected format:
        {
            "name": "Workflow Name",
            "actions": [ ... ],  # List of action dictionaries
        }
        """
        if not isinstance(workflow, dict):
            logging.error("Validation Error: Workflow is not a JSON object.")
            return False

        # Check for 'name' key
        if "name" not in workflow:
            logging.error("Validation Error: 'name' key is missing in the workflow.")
            return False

        # Check for 'actions' key
        if "actions" not in workflow:
            logging.error("Validation Error: 'actions' key is missing in the workflow.")
            return False

        # Validate 'actions'
        if not isinstance(workflow["actions"], list):
            logging.error("Validation Error: 'actions' is not a list.")
            return False

        return True

    def init_cipher(self):
        """
        Initialize the cipher for encrypting/decrypting API keys and credentials.
        """
        try:
            key_file = 'secret.key'
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
                self.cipher = fernet(key)
                logging.info("Cipher initialized successfully.")
            else:
                logging.error("secret.key file not found. Please ensure it exists.")
                raise FileNotFoundError("secret.key not found")
            
        except Exception as e:
            logging.error(f"Failed to initialize cipher: {e}")
            raise

    def init_credentials_tab(self):
        """
        Initializes the Credentials tab for managing stored credentials.
        """
        credentials_tab = QWidget()
        layout = QVBoxLayout(credentials_tab)

        layout.addWidget(QLabel("Credentials Management"))

        # List widget to display credentials
        self.credentials_list = QListWidget()
        layout.addWidget(self.credentials_list)

        # Buttons for Add, Edit, Delete
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add")
        edit_button = QPushButton("Edit")
        delete_button = QPushButton("Delete")

        add_button.clicked.connect(self.add_credentials)
        edit_button.clicked.connect(self.edit_credentials)
        delete_button.clicked.connect(self.delete_credentials)

        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)

        self.tabs.addTab(credentials_tab, "Credentials")

        # Load credentials when initializing
        self.load_credentials()

    def load_credentials(self):
        """
        Load credentials from the JSON file and display them in the list widget.
        """
        self.credentials_list.clear()
        if os.path.exists('credentials.json'):
            with open('credentials.json', 'r') as f:
                self.existing_credentials = json.load(f)
            for cred in self.existing_credentials:
                self.credentials_list.addItem(cred["name"])
        else:
            self.existing_credentials = []

    def add_credentials(self):
        """
        Open a dialog to add new credentials.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Credential")
        dialog.setModal(True)
        dialog.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(dialog)

        name_label = QLabel("Credential Name:")
        name_entry = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(name_entry)

        username_label = QLabel("Username:")
        username_entry = QLineEdit()
        layout.addWidget(username_label)
        layout.addWidget(username_entry)

        password_label = QLabel("Password:")
        password_entry = QLineEdit()
        password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_label)
        layout.addWidget(password_entry)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        def save_credentials():
            name = name_entry.text().strip()
            username = username_entry.text().strip()
            password = password_entry.text().strip()
            if not name or not username or not password:
                QMessageBox.critical(dialog, "Error", "All fields are required.")
                return
            # Encrypt the password
            encrypted_password = self.cipher.encrypt(password.encode()).decode()
            credentials = {
                "name": name,
                "username": username,
                "password": encrypted_password
            }
            # Load existing credentials
            if os.path.exists('credentials.json'):
                with open('credentials.json', 'r') as f:
                    existing_credentials = json.load(f)
            else:
                existing_credentials = []
            existing_credentials.append(credentials)
            with open('credentials.json', 'w') as f:
                json.dump(existing_credentials, f, indent=4)
            self.load_credentials()
            logging.info(f"Credential '{name}' added successfully.")
            dialog.accept()

        save_button.clicked.connect(save_credentials)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()

    def edit_credentials(self):
        """
        Open a dialog to edit the selected credential.
        """
        selected_items = self.credentials_list.selectedItems()
        if not selected_items:
            QMessageBox.critical(self, "Error", "No credential selected.")
            return
        selected_index = self.credentials_list.row(selected_items[0])
        credential = self.existing_credentials[selected_index]

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Credential")
        dialog.setModal(True)
        dialog.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(dialog)

        name_label = QLabel("Credential Name:")
        name_entry = QLineEdit()
        name_entry.setText(credential["name"])
        layout.addWidget(name_label)
        layout.addWidget(name_entry)

        username_label = QLabel("Username:")
        username_entry = QLineEdit()
        username_entry.setText(credential["username"])
        layout.addWidget(username_label)
        layout.addWidget(username_entry)

        password_label = QLabel("Password:")
        password_entry = QLineEdit()
        password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        decrypted_password = self.cipher.decrypt(credential["password"].encode()).decode()
        password_entry.setText(decrypted_password)
        layout.addWidget(password_label)
        layout.addWidget(password_entry)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        def save_edited_credentials():
            name = name_entry.text().strip()
            username = username_entry.text().strip()
            password = password_entry.text().strip()
            if not name or not username or not password:
                QMessageBox.critical(dialog, "Error", "All fields are required.")
                return
            # Encrypt the password
            encrypted_password = self.cipher.encrypt(password.encode()).decode()
            updated_credential = {
                "name": name,
                "username": username,
                "password": encrypted_password
            }
            self.existing_credentials[selected_index] = updated_credential
            with open('credentials.json', 'w') as f:
                json.dump(self.existing_credentials, f, indent=4)
            self.load_credentials()
            logging.info(f"Credential '{name}' updated successfully.")
            dialog.accept()

        save_button.clicked.connect(save_edited_credentials)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()

    def delete_credentials(self):
        """
        Delete the selected credential.
        """
        selected_items = self.credentials_list.selectedItems()
        if not selected_items:
            QMessageBox.critical(self, "Error", "No credential selected.")
            return
        selected_index = self.credentials_list.row(selected_items[0])
        credential = self.existing_credentials[selected_index]
        confirm = QMessageBox.question(self, "Confirm Delete",
                                       f"Are you sure you want to delete '{credential['name']}'?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            del self.existing_credentials[selected_index]
            with open('credentials.json', 'w') as f:
                json.dump(self.existing_credentials, f, indent=4)
            self.load_credentials()
            logging.info(f"Credential '{credential['name']}' deleted successfully.")

    def init_logging_tab(self):
        """
        Initializes the Logging tab for viewing log output.
        """
        logging_tab = QWidget()
        layout = QVBoxLayout(logging_tab)

        # Add header
        layout.addWidget(QLabel("Log Viewer"))

        # Log viewer text edit with custom styling
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_viewer)

        # Add control buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self.clear_logs)
        
        save_button = QPushButton("Save Logs")
        save_button.clicked.connect(self.save_logs)
        
        button_layout.addWidget(clear_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)

        self.tabs.addTab(logging_tab, "Logging")

        # Set up custom log handler
        self.log_handler = QTextEditLogger(self.log_viewer)
        self.log_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

    def clear_logs(self):
        """Clears the log viewer."""
        self.log_viewer.clear()

    def save_logs(self):
        """Saves the current logs to a file using proper path handling."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        filename = os.path.join(log_dir, f"workflow_log_{timestamp}.txt")
        
        try:
            os.makedirs(log_dir, exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_viewer.toPlainText())
            QMessageBox.information(self, "Success", f"Logs saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save logs: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save logs: {str(e)}")

    def add_log_message(self, message):
        """
        Adds a formatted log message to the log viewer.
        
        Args:
            message (str): The log message
        """
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f'<span style="color: #ffffff">[{timestamp}] {message}</span><br>'
            
            def update_log():
                self.log_viewer.append(formatted_message)
                # Auto-scroll to bottom
                scrollbar = self.log_viewer.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
            # Use QTimer to safely update GUI from any thread
            QTimer.singleShot(0, update_log)
            
        except Exception as e:
            print(f"Error adding log message: {e}")


    def start_workflow(self):
        logging.info("Starting workflow...")

    def stop_workflow(self):
        logging.info("Stopping workflow...")

    def open_workflow_wizard(self):
        wizard = LLMWizardDialog(self)
        wizard.exec()
        # Update workflows after wizard is closed
        self.update_workflow_listbox()
    
    def add_api_key(self):
        """
        Opens a dialog to input and save an OpenAI API key.
        """
        api_key, ok = QInputDialog.getText(
            self, 
            "Set API Key", 
            "Enter your OpenAI API Key:\n\nGet your key from: https://platform.openai.com/api-keys",
            QLineEdit.EchoMode.Password
        )

        if ok and api_key.strip():
            # Validate API key format
            if not api_key.startswith('sk-'):
                QMessageBox.warning(
                    self, 
                    "Invalid Key Format", 
                    "OpenAI API keys should start with 'sk-'. Please check your key."
                )
                return

            try:
                # Save the API key
                self.api_key = api_key.strip()
                
                # Create api_keys directory if it doesn't exist
                os.makedirs('api_keys', exist_ok=True)
                
                # Encrypt and save the API key using the same cipher as credentials
                encrypted_key = self.cipher.encrypt(self.api_key.encode())
                with open('api_keys/openai_key.enc', 'wb') as f:
                    f.write(encrypted_key)
                
                QMessageBox.information(
                    self, 
                    "API Key Set", 
                    "Your API key has been saved successfully!\n\nYou can now use the Workflow Wizard."
                )
                logging.info("API key has been set and saved.")
                
            except Exception as e:
                logging.error(f"Failed to save API key: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to save API key. Please try again."
                )
                
        elif ok:
            QMessageBox.warning(
                self, 
                "Invalid Input", 
                "API key cannot be empty."
            )
            logging.warning("Empty API key input.")

    def load_api_key(self):
        """Load encrypted API key from file."""
        try:
            key_path = 'api_keys/openai_key.enc'
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    encrypted_key = f.read()
                    self.api_key = self.cipher.decrypt(encrypted_key).decode()
                    logging.info("API key loaded successfully.")
                    return True
        except Exception as e:
            logging.error(f"Failed to load API key: {e}")
        return False

    def update_workflow_listbox(self):
        """
        Update the workflow list with the current workflows.
        """
        self.workflow_list.clear()
        for workflow_name in self.workflows.keys():
            self.workflow_list.addItem(workflow_name)

    def execute_selected_workflow(self):
        """
        Execute the selected workflow.
        """
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            QMessageBox.critical(self, "Error", "No workflow selected.")
            return

        selected_workflow_name = selected_items[0].text()
        selected_workflow = self.workflows.get(selected_workflow_name)
        
        if not selected_workflow:
            QMessageBox.critical(self, "Error", f"Workflow '{selected_workflow_name}' not found.")
            return
        
        # Add to running workflows list
        self.running_workflows_list.addItem(selected_workflow_name)
        
        # Start workflow execution in a separate thread
        execution_thread = threading.Thread(
            target=self._execute_workflow_and_cleanup,
            args=(selected_workflow_name, selected_workflow),
            daemon=True
        )
        execution_thread.start()

    def _execute_workflow_and_cleanup(self, workflow_name, workflow_data):
        """
        Internal method to execute workflow and handle cleanup.
        """
        try:
            self.add_log_message(f"Starting workflow: {workflow_name}")
            
            # Execute workflow
            executor = workflow_system.WorkflowExecutor()
            for action in workflow_data.get('actions', []):
                action_type = action.get('type', 'unknown')
                self.add_log_message(f"Executing action: {action_type}")
                
                try:
                    executor.execute_action(action)
                    self.add_log_message(f"Action {action_type} completed successfully")
                except Exception as action_error:
                    self.add_log_message(f"Action {action_type} failed: {str(action_error)}")
                    raise
            
            executor.cleanup()
            self.add_log_message(f"Workflow '{workflow_name}' completed successfully!")
            
            # Handle successful completion
            QApplication.instance().postEvent(
                self,
                WorkflowCompletionEvent(
                    workflow_name,
                    success=True,
                    message=f"Workflow '{workflow_name}' completed successfully!"
                )
            )
        except Exception as e:
            error_msg = f"Error executing workflow '{workflow_name}': {str(e)}"
            self.add_log_message(error_msg)
            logging.exception("Full traceback:")
            
            # Handle failure
            QApplication.instance().postEvent(
                self,
                WorkflowCompletionEvent(
                    workflow_name,
                    success=False,
                    message=error_msg
                )
            )

    def event(self, event):
        """
        Handle custom events.
        """
        if event.type() == WorkflowCompletionEvent.EVENT_TYPE:
            self._handle_workflow_completion(event)
            return True
        return super().event(event)

    def _handle_workflow_completion(self, event):
        """
        Handle workflow completion event.
        """
        try:
            # Remove from running workflows list
            for i in range(self.running_workflows_list.count()):
                item = self.running_workflows_list.item(i)
                if item and item.text() == event.workflow_name:
                    self.running_workflows_list.takeItem(i)
                    break
            
            # Update UI
            self.running_workflows_list.update()
            
            # Show appropriate message
            if event.success:
                QMessageBox.information(self, "Workflow Complete", event.message)
            else:
                QMessageBox.critical(self, "Workflow Error", event.message)
                
            logging.info(f"Workflow '{event.workflow_name}' cleanup completed")
            
        except Exception as e:
            logging.error(f"Error handling workflow completion: {e}")

    def edit_selected_workflow(self):
        """
        Open the workflow editor for the selected workflow.
        """
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            QMessageBox.critical(self, "Error", "No workflow selected.")
            return
        selected_workflow = selected_items[0].text()
        self.open_workflow_editor(selected_workflow)

    def delete_selected_workflow(self):
        """
        Delete the selected workflow.
        """
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            QMessageBox.critical(self, "Error", "No workflow selected.")
            return
        selected_workflow = selected_items[0].text()
        confirm = QMessageBox.question(
            self, "Confirm Delete", f"Are you sure you want to delete '{selected_workflow}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            del self.workflows[selected_workflow]
            self.save_workflows_to_disk()
            self.update_workflow_listbox()
            self.add_log_message(f"Workflow '{selected_workflow}' deleted successfully.")



    def save_workflows_to_disk(self):
        """
        Save the workflows to a JSON file.
        """
        try:
            with open(self.workflows_path, 'w') as f:
                json.dump(self.workflows, f, indent=4)
            logging.info("Workflows saved successfully.")
        except Exception as e:
            logging.error(f"Failed to save workflows: {e}")

    def add_log_message(self, message):
        """
        Add a log message to the log viewer.
        """
        self.log_viewer.append(message)

    def open_workflow_editor(self, workflow_name):
        """
        Open a dialog to edit the workflow.
        """
        workflow = self.workflows[workflow_name]
        editor_dialog = WorkflowEditorDialog(self, workflow_name, workflow)
        editor_dialog.exec()
        # After editing, save workflows and update list
        self.save_workflows_to_disk()
        self.update_workflow_listbox()

    def start_queue_processors(self):
        """
        Start processing queues for log messages and workflow status updates.
        """
        self.process_log_queue()
        self.process_workflow_status_queue()
        self.process_update_workflows()

    def process_log_queue(self):
        """
        Process log messages from the shared log queue.
        """
        while not shared.log_queue.empty():
            message = shared.log_queue.get()
            self.add_log_message(message)
        QTimer.singleShot(100, self.process_log_queue)

    def process_workflow_status_queue(self):
        """
        Process workflow status updates.
        """
        while not shared.workflow_status_queue.empty():
            status_update = shared.workflow_status_queue.get()
            workflow_name = status_update['workflow_name']
            status = status_update['status']
            if status == 'completed':
                # Remove workflow_name from running_workflows_list
                self.remove_running_workflow(workflow_name)
        QTimer.singleShot(100, self.process_workflow_status_queue)

    def process_update_workflows(self):
        """
        Update workflows if there are any changes.
        """
        if shared.update_workflows.is_set():
            self.update_workflow_listbox()
            shared.update_workflows.clear()
        QTimer.singleShot(100, self.process_update_workflows)

    def init_recording_tab(self):
        """
        Initializes the System Recording tab with resource controls.
        """
        recording_tab = QWidget()
        layout = QVBoxLayout(recording_tab)

        # Add header
        layout.addWidget(QLabel("System Action Recording"))

        # Status indicator
        self.recording_status = QLabel("Status: Not Recording")
        self.recording_status.setStyleSheet("""
            QLabel {
                color: #ff0000;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #ff0000;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.recording_status)

        # Add keyboard shortcut information
        shortcut_info = QLabel("Keyboard Shortcuts:\nF9 - Start/Pause/Resume Recording\nF10 - Stop Recording")
        shortcut_info.setStyleSheet("font-size: 12px; color: #4A90E2;")
        layout.addWidget(shortcut_info)

        # Resource Limits Group
        resource_group = QGroupBox("System Resource Limits")
        resource_layout = QGridLayout()

        # CPU Limit
        resource_layout.addWidget(QLabel("CPU Usage Limit (%):"), 0, 0)
        self.cpu_limit = QSpinBox()
        self.cpu_limit.setRange(10, 100)
        self.cpu_limit.setValue(70)  # Default value
        self.cpu_limit.setToolTip("Maximum CPU usage before throttling")
        resource_layout.addWidget(self.cpu_limit, 0, 1)

        # Memory Limit
        resource_layout.addWidget(QLabel("Memory Usage Limit (%):"), 1, 0)
        self.memory_limit = QSpinBox()
        self.memory_limit.setRange(10, 100)
        self.memory_limit.setValue(75)  # Default value
        self.memory_limit.setToolTip("Maximum memory usage before throttling")
        resource_layout.addWidget(self.memory_limit, 1, 1)

        # Resource Monitor
        resource_layout.addWidget(QLabel("Current Usage:"), 2, 0, 1, 2)
        self.resource_monitor = QTextEdit()
        self.resource_monitor.setReadOnly(True)
        self.resource_monitor.setMaximumHeight(60)
        self.resource_monitor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 5px;
            }
        """)
        self.resource_monitor.viewport().setAutoFillBackground(False)
        resource_layout.addWidget(self.resource_monitor, 3, 0, 1, 2)

        resource_group.setLayout(resource_layout)
        layout.addWidget(resource_group)

        # Button container
        button_layout = QHBoxLayout()
        
        # Create recording control buttons
        self.start_button = QPushButton("Start Recording")
        self.pause_button = QPushButton("Pause Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.save_button = QPushButton("Save Recording")

        # Set initial button states
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(False)

        # Connect button signals and additional signals
        self.start_button.clicked.connect(self.start_recording)
        self.pause_button.clicked.connect(self.pause_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.save_button.clicked.connect(self.save_recording)

        # Add buttons to layout
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)

        # Add recording preview/log area
        self.recording_log = QTextEdit()
        self.recording_log.setReadOnly(True)
        self.recording_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.recording_log)

        # Start resource monitoring timer
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self.update_resource_monitor)
        self.resource_timer.start(1000)  # Update every second

        def handle_recording_error(error_msg):
            self.add_log_message(f"Error: {error_msg}")
            self.recording_status.setText("Status: Error")
            self.recording_status.setStyleSheet("""
                QLabel {
                    color: #ff0000;
                    font-weight: bold;
                    padding: 5px;
                    border: 1px solid #ff0000;
                    border-radius: 3px;
                }
            """)
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)

        def handle_recording_status(is_recording):
            if not is_recording:
                self.start_button.setEnabled(True)
                self.pause_button.setEnabled(False)
                self.stop_button.setEnabled(False)

        # Connect the error and status signals
        if hasattr(self, 'recording_thread'):
            self.recording_thread.error_signal.connect(handle_recording_error)
            self.recording_thread.status_signal.connect(handle_recording_status)

        self.tabs.addTab(recording_tab, "System Recording")

    def update_resource_monitor(self):
        """Update the resource monitor display safely."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Create simple text content (removed disk info)
            monitor_text = f"CPU: {cpu_percent:.1f}% | Memory: {memory_percent:.1f}%"
            
            # Use QMetaObject to safely update GUI from any thread
            def safe_update():
                if self.resource_monitor and not self.resource_monitor.isHidden():
                    # Simple text update without any formatting
                    self.resource_monitor.setPlainText(monitor_text)
            
            # Execute update in the main thread
            QTimer.singleShot(0, safe_update)
            
        except Exception as e:
            logging.error(f"Error updating resource monitor: {e}")

    def start_recording(self):
        """Start system recording with resource limits."""
        try:
            self.recording_status.setText("Status: Recording")
            self.recording_status.setStyleSheet("""
                QLabel {
                    color: #00ff00;
                    font-weight: bold;
                    padding: 5px;
                    border: 1px solid #00ff00;
                    border-radius: 3px;
                }
            """)
            
            # Update button states
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
            # Start recording thread
            self.recording_thread = RecordingThread(
                self,
                cpu_limit=self.cpu_limit.value(),
                memory_limit=self.memory_limit.value()
            )
            self.recording_thread.log_signal.connect(self.update_recording_log)
            self.recording_thread.start()
            
            self.add_log_message("Starting recording with resource limits:\n"
                                f"CPU: {self.cpu_limit.value()}% | "
                                f"Memory: {self.memory_limit.value()}%")
            
        except Exception as e:
            error_msg = f"Error starting recording: {str(e)}"
            self.add_log_message(error_msg)
            logging.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            
            # Reset button states
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)

    def pause_recording(self):
        """Pause/Resume system recording."""
        try:
            if self.pause_button.text() == "Pause Recording":
                self.recording_status.setText("Status: Paused")
                self.recording_status.setStyleSheet("""
                    QLabel {
                        color: #ffa500;
                        font-weight: bold;
                        padding: 5px;
                        border: 1px solid #ffa500;
                        border-radius: 3px;
                    }
                """)
                self.pause_button.setText("Resume Recording")
                self.recording_thread.pause()
            else:
                self.recording_status.setText("Status: Recording")
                self.recording_status.setStyleSheet("""
                    QLabel {
                        color: #00ff00;
                        font-weight: bold;
                        padding: 5px;
                        border: 1px solid #00ff00;
                        border-radius: 3px;
                    }
                """)
                self.pause_button.setText("Pause Recording")
                self.recording_thread.resume()
            
            self.add_log_message("Recording paused" if self.pause_button.text() == "Resume Recording" else "Recording resumed")
            
        except Exception as e:
            self.add_log_message(f"Error toggling pause: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to toggle pause: {str(e)}")

    def stop_recording(self):
        """Stop system recording."""
        try:
            self.recording_status.setText("Status: Stopped")
            self.recording_status.setStyleSheet("""
                QLabel {
                    color: #ff0000;
                    font-weight: bold;
                    padding: 5px;
                    border: 1px solid #ff0000;
                    border-radius: 3px;
                }
            """)
            
            # Update button states
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.save_button.setEnabled(True)
            
            # Stop the recording thread
            if hasattr(self, 'recording_thread'):
                self.recording_thread.stop()
                self.recording_thread.wait()
            
            self.add_log_message("Recording stopped")
            
        except Exception as e:
            self.add_log_message(f"Error stopping recording: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to stop recording: {str(e)}")

    def save_recording(self):
        """Save the recorded actions as a workflow."""
        try:
            # Convert recording to workflow format
            from recording_converter import convert_recording_to_workflow
            workflow = convert_recording_to_workflow(self.recording_thread.get_recording_data())
            
            # Get workflow name from user
            name, ok = QInputDialog.getText(self, "Save Workflow", "Enter workflow name:")
            if ok and name:
                # Add to workflows
                self.workflows[name] = workflow
                self.save_workflows_to_disk()
                self.update_workflow_listbox()
                
                # Reset recording state
                self.save_button.setEnabled(False)
                self.recording_log.clear()
                
                self.add_log_message(f"Recording saved as workflow: {name}")
                QMessageBox.information(self, "Success", f"Recording saved as workflow: {name}")
            
        except Exception as e:
            self.add_log_message(f"Error saving recording: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save recording: {str(e)}")

    def update_recording_log(self, message):
        """Update the recording log with new messages."""
        self.recording_log.append(message)
        # Auto-scroll to bottom
        scrollbar = self.recording_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def init_documents_tab(self):
        """
        Initializes the Documents tab with a standard item model.
        """
        documents_tab = QWidget()
        layout = QVBoxLayout(documents_tab)

        # Header
        header = QLabel("Documents Management")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Create standard item model for file display
        self.document_model = QStandardItemModel()
        self.document_model.setHorizontalHeaderLabels(['Name', 'Date Modified'])

        # Tree view to display the files
        self.file_tree_view = QTreeView()
        self.file_tree_view.setModel(self.document_model)
        self.file_tree_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.file_tree_view.setColumnWidth(0, 250)  # Name column
        self.file_tree_view.setColumnWidth(1, 200)  # Date column
        layout.addWidget(self.file_tree_view)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Document")
        delete_button = QPushButton("Delete Document")
        view_button = QPushButton("View Document")

        add_button.clicked.connect(self.add_document)
        delete_button.clicked.connect(self.delete_selected_document)
        view_button.clicked.connect(self.view_selected_document)

        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(view_button)
        layout.addLayout(button_layout)

        self.tabs.addTab(documents_tab, "Documents")

        # Load existing documents
        self.refresh_document_list()

    def refresh_document_list(self):
        """Refresh the document list in the tree view."""
        try:
            self.document_model.clear()
            self.document_model.setHorizontalHeaderLabels(['Name', 'Date Modified'])
            
            docs_dir = os.path.join(os.path.dirname(__file__), 'local_user_documents')
            if os.path.exists(docs_dir):
                for filename in os.listdir(docs_dir):
                    file_path = os.path.join(docs_dir, filename)
                    if os.path.isfile(file_path):
                        name_item = QStandardItem(filename)
                        date_item = QStandardItem(
                            datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                        )
                        self.document_model.appendRow([name_item, date_item])
                        
        except Exception as e:
            logging.error(f"Error refreshing document list: {e}")

    def add_document(self):
        """Handle document upload by copying to local_user_documents."""
        try:
            # Base directory for storing documents
            docs_dir = os.path.join(os.path.expanduser("~"), "Desktop", "local_user_documents")
            os.makedirs(docs_dir, exist_ok=True)  # Ensure the directory exists
            
            # Debug: Log the directory paths
            logging.debug(f"Documents directory: {docs_dir}")
            
            # Create and configure the QFileDialog
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Select Document")
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
            
            # Set default directory to user's home
            initial_directory = os.path.expanduser("~")
            file_dialog.setDirectory(initial_directory)
            
            # Debug: Log the starting directory
            logging.debug(f"Starting QFileDialog in directory: {initial_directory}")
            
            # Execute the dialog and process selected files
            if file_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_files = file_dialog.selectedFiles()
                
                if not selected_files:
                    QMessageBox.warning(self, "Warning", "No file selected.")
                    return
                
                file_path = selected_files[0]
                
                # Ensure the selected file exists
                if not os.path.exists(file_path):
                    QMessageBox.critical(self, "Error", f"Selected file does not exist: {file_path}")
                    return
                
                # Handle duplicate filenames
                original_filename = os.path.basename(file_path)
                new_file_path = os.path.join(docs_dir, original_filename)
                counter = 1
                while os.path.exists(new_file_path):
                    name, ext = os.path.splitext(original_filename)
                    new_file_path = os.path.join(docs_dir, f"{name}_{counter}{ext}")
                    counter += 1
                
                # Copy file to documents directory
                import shutil
                shutil.copy2(file_path, new_file_path)
                
                # Debug: Log the new file path
                logging.debug(f"File copied to: {new_file_path}")
                
                # Refresh the document list or update the UI
                self.refresh_document_list()
                
                QMessageBox.information(self, "Success", f"Document added: {new_file_path}")
            else:
                logging.info("File dialog canceled by the user.")

        except Exception as e:
            logging.error(f"Error in add_document: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to add document: {str(e)}")


    def delete_selected_document(self):
        """Delete the selected document."""
        try:
            selected_indexes = self.file_tree_view.selectedIndexes()
            if not selected_indexes:
                QMessageBox.warning(self, "Warning", "No document selected")
                return
            
            # Get the file name from the first column
            file_name = self.document_model.data(selected_indexes[0])
            docs_dir = os.path.join(os.path.dirname(__file__), 'local_user_documents')
            file_path = os.path.join(docs_dir, file_name)
            
            if os.path.exists(file_path):
                confirm = QMessageBox.question(
                    self,
                    "Confirm Delete",
                    f"Are you sure you want to delete '{file_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if confirm == QMessageBox.StandardButton.Yes:
                    os.remove(file_path)
                    self.refresh_document_list()
                    logging.info(f"Document deleted: {file_path}")
            
        except Exception as e:
            logging.error(f"Error deleting document: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete document: {str(e)}"
            )

    def view_selected_document(self):
        """View the selected document using system-specific methods."""
        try:
            selected_indexes = self.file_tree_view.selectedIndexes()
            if not selected_indexes:
                QMessageBox.warning(self, "Warning", "No document selected")
                return
            
            # Get the file name from the first column
            file_name = self.document_model.data(selected_indexes[0])
            docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'local_user_documents')
            file_path = os.path.join(docs_dir, file_name)
            
            if os.path.exists(file_path):
                # Use system-specific file opening methods
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':
                    import subprocess
                    subprocess.run(['open', file_path], check=True)
                else:  # Linux and other Unix-like
                    import subprocess
                    subprocess.run(['xdg-open', file_path], check=True)
            else:
                QMessageBox.warning(self, "Warning", "Document not found")
                
        except Exception as e:
            logging.error(f"Error viewing document: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to view document: {str(e)}"
            )

    def save_document_metadata(self, name, file_path):
        """Save document metadata to JSON file."""
        try:
            metadata_path = os.path.join(os.path.dirname(__file__), 'local_user_documents', 'metadata.json')
            
            # Load existing metadata
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            # Add new document metadata
            metadata[name] = {
                'file_path': file_path,
                'added_date': datetime.now().isoformat(),
                'file_type': os.path.splitext(file_path)[1]
            }
            
            # Save updated metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
                
        except Exception as e:
            logging.error(f"Error saving document metadata: {e}")

    def remove_document_metadata(self, name):
        """Remove document metadata from JSON file."""
        try:
            metadata_path = os.path.join(os.path.dirname(__file__), 'local_user_documents', 'metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                if name in metadata:
                    del metadata[name]
                    
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=4)
                        
        except Exception as e:
            logging.error(f"Error removing document metadata: {e}")

    def get_document_path(self, name):
        """Get the file path for a document by its name."""
        try:
            metadata_path = os.path.join(os.path.dirname(__file__), 'local_user_documents', 'metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                if name in metadata:
                    return metadata[name]['file_path']
                    
        except Exception as e:
            logging.error(f"Error getting document path: {e}")
        return None

    def load_documents(self):
        """Load existing documents into the list."""
        try:
            metadata_path = os.path.join(os.path.dirname(__file__), 'local_user_documents', 'metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                self.document_list.clear()
                for name in metadata:
                    self.document_list.addItem(name)
                    
        except Exception as e:
            logging.error(f"Error loading documents: {e}")

    def add_content(self):
        """Add new content."""
        try:
            # Get content name and text from user
            name, ok = QInputDialog.getText(
                self,
                "Add Content",
                "Enter a name for this content:"
            )
            
            if ok and name:
                text, ok = QInputDialog.getMultiLineText(
                    self,
                    "Add Content",
                    "Enter the content text:",
                    ""
                )
                
                if ok:
                    # Create content directory if it doesn't exist
                    content_dir = os.path.join(os.path.dirname(__file__), 'local_user_documents', 'content')
                    os.makedirs(content_dir, exist_ok=True)
                    
                    # Save content to file
                    content_path = os.path.join(content_dir, f"{name}.txt")
                    
                    # Check if content already exists
                    if os.path.exists(content_path):
                        response = QMessageBox.question(
                            self,
                            "Content Exists",
                            "Content with this name already exists. Do you want to replace it?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        if response == QMessageBox.StandardButton.No:
                            return
                    
                    # Save content
                    with open(content_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    # Add to content list
                    self.content_list.addItem(name)
                    
                    logging.info(f"Content '{name}' added successfully")
                    QMessageBox.information(self, "Success", f"Content '{name}' added successfully")
                    
        except Exception as e:
            logging.error(f"Error adding content: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add content: {str(e)}")

    def edit_content(self):
        """Edit selected content."""
        try:
            selected_items = self.content_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Warning", "Please select content to edit")
                return
            
            content_name = selected_items[0].text()
            content_path = os.path.join(
                os.path.dirname(__file__), 
                'local_user_documents', 
                'content', 
                f"{content_name}.txt"
            )
            
            if os.path.exists(content_path):
                # Read existing content
                with open(content_path, 'r', encoding='utf-8') as f:
                    current_text = f.read()
                
                # Get edited text from user
                new_text, ok = QInputDialog.getMultiLineText(
                    self,
                    "Edit Content",
                    f"Edit content for '{content_name}':",
                    current_text
                )
                
                if ok:
                    # Save edited content
                    with open(content_path, 'w', encoding='utf-8') as f:
                        f.write(new_text)
                    
                    logging.info(f"Content '{content_name}' updated successfully")
                    QMessageBox.information(self, "Success", f"Content '{content_name}' updated successfully")
            else:
                QMessageBox.warning(self, "Warning", f"Content '{content_name}' not found")
                
        except Exception as e:
            logging.error(f"Error editing content: {e}")
            QMessageBox.critical(self, "Error", f"Failed to edit content: {str(e)}")

    def delete_content(self):
        """Delete selected content."""
        try:
            selected_items = self.content_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Warning", "Please select content to delete")
                return
            
            content_name = selected_items[0].text()
            content_path = os.path.join(
                os.path.dirname(__file__), 
                'local_user_documents', 
                'content', 
                f"{content_name}.txt"
            )
            
            if os.path.exists(content_path):
                response = QMessageBox.question(
                    self,
                    "Confirm Delete",
                    f"Are you sure you want to delete '{content_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if response == QMessageBox.StandardButton.Yes:
                    os.remove(content_path)
                    self.content_list.takeItem(self.content_list.row(selected_items[0]))
                    logging.info(f"Content '{content_name}' deleted successfully")
            else:
                QMessageBox.warning(self, "Warning", f"Content '{content_name}' not found")
                
        except Exception as e:
            logging.error(f"Error deleting content: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete content: {str(e)}")

    def load_content(self):
        """Load existing content into the list."""
        try:
            content_dir = os.path.join(os.path.dirname(__file__), 'local_user_documents', 'content')
            if os.path.exists(content_dir):
                self.content_list.clear()
                for filename in os.listdir(content_dir):
                    if filename.endswith('.txt'):
                        name = os.path.splitext(filename)[0]
                        self.content_list.addItem(name)
                        
        except Exception as e:
            logging.error(f"Error loading content: {e}")


class MainToolBar(QToolBar):
    def __init__(self, main):
        super().__init__()
        self.main = main
        print(f"My Value is: {type(self.main.main_gui)}")

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setMovable(False)
        self.setIconSize(QSize(24, 24))

        # Add Toolbar Dropdowns
        self.add_about_dropdown()
        self.add_account_dropdown()
        self.add_options_dropdown()
        self.add_help_dropdown()

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

    def add_account_dropdown(self):
        """
        Adds the Account dropdown menu to the toolbar.
        """
        account_dropdown_button = QToolButton(self)
        account_dropdown_button.setText("Account")
        account_dropdown_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        account_menu = QMenu(self)
        account_menu.addAction(QAction("Account Info", self))
        account_menu.addAction(QAction("Billing Info", self))
        account_menu.addAction(QAction("API Usage", self))
        account_logout_action = QAction("Logout", self)
        account_logout_action.triggered.connect(
            lambda: self.main.auth.auth_server.logout(self.main.auth.access_token)
        )
        account_menu.addAction(account_logout_action)
        account_dropdown_button.setMenu(account_menu)
        self.addWidget(account_dropdown_button)

    def add_options_dropdown(self):
        """
        Adds the Options dropdown menu to the toolbar.
        """
        options_dropdown_button = QToolButton(self)
        options_dropdown_button.setText("Options")
        options_dropdown_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        options_menu = QMenu(self)
        set_api_key_action = QAction("Set API Key", self)
        set_api_key_action.triggered.connect(self.main.main_gui.add_api_key)
        change_theme_action = QAction("Change Theme", self)
        change_theme_action.triggered.connect(self.main.toggle_theme)

        options_menu.addAction(set_api_key_action)
        options_menu.addAction(change_theme_action)

        options_dropdown_button.setMenu(options_menu)
        self.addWidget(options_dropdown_button)

    def add_help_dropdown(self):
        """
        Adds the Help dropdown menu to the toolbar with recording information.
        """
        help_dropdown_button = QToolButton(self)
        help_dropdown_button.setText("Help")
        help_dropdown_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        help_menu = QMenu(self)
        
        # Add Recording Information action
        recording_info_action = QAction("Recording Information", self)
        recording_info_action.triggered.connect(self.main.main_gui.show_recording_info)
        
        help_menu.addAction(recording_info_action)
        help_menu.addAction(QAction("Report Bug", self))
        help_menu.addAction(QAction("Submit Feedback", self))
        help_menu.addAction(QAction("Feature Request", self))
        help_dropdown_button.setMenu(help_menu)
        self.addWidget(help_dropdown_button)

class WorkflowEditorDialog(QDialog):
    """
    Dialog for editing a workflow.
    """

    def __init__(self, parent, workflow_name, workflow):
        super().__init__(parent)
        self.workflow_name = workflow_name
        self.workflow = workflow
        self.main = parent
        self.setWindowTitle(f"Edit Workflow: {workflow_name}")
        self.setGeometry(100, 100, 600, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # List widget to display actions
        self.action_list = QListWidget()
        for index, action in enumerate(self.workflow):
            self.action_list.addItem(f"Action {index + 1}: {action}")
        layout.addWidget(self.action_list)

        # Buttons for editing actions
        button_layout = QHBoxLayout()
        edit_action_button = QPushButton("Edit Action")
        delete_action_button = QPushButton("Delete Action")

        edit_action_button.clicked.connect(self.edit_action)
        delete_action_button.clicked.connect(self.delete_action)

        button_layout.addWidget(edit_action_button)
        button_layout.addWidget(delete_action_button)
        layout.addLayout(button_layout)

        # Save button
        save_button = QPushButton("Save Workflow")
        save_button.clicked.connect(self.save_workflow)
        layout.addWidget(save_button)

    def edit_action(self):
        selected_items = self.action_list.selectedItems()
        if not selected_items:
            QMessageBox.critical(self, "Error", "No action selected.")
            return
        action_index = self.action_list.row(selected_items[0])
        # Implement action editing logic here
        # For now, we just display a message
        QMessageBox.information(self, "Edit Action", f"Editing action {action_index + 1}")

    def delete_action(self):
        selected_items = self.action_list.selectedItems()
        if not selected_items:
            QMessageBox.critical(self, "Error", "No action selected.")
            return
        action_index = self.action_list.row(selected_items[0])
        del self.workflow[action_index]
        self.action_list.takeItem(action_index)
        logging.info(f"Action {action_index + 1} deleted from workflow '{self.workflow_name}'.")

    def save_workflow(self):
        self.main.workflows[self.workflow_name] = self.workflow
        logging.info(f"Workflow '{self.workflow_name}' saved.")
        self.accept()



def load_workflows(file_path="workflows.json"):
    """
    Load workflows from a JSON file.
    """
    try:
        with open(file_path, "r") as file:
            workflows = json.load(file)
            logging.info(f"Successfully loaded workflows from {file_path}")
            # Validate each workflow
            for name, workflow in workflows.items():
                if not isinstance(workflow, dict):
                    logging.warning(f"Workflow '{name}' has invalid format")
                    continue
                if 'name' not in workflow:
                    workflow['name'] = name  # Add name if missing
                if 'actions' not in workflow:
                    logging.warning(f"Workflow '{name}' has no actions")
                    continue
                logging.info(f"Loaded workflow: {name} with {len(workflow['actions'])} actions")
            return workflows
    except FileNotFoundError:
        logging.error(f"Workflows file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding workflows JSON: {e}")
        return {}
    except Exception as e:
        logging.error(f"Unexpected error loading workflows: {e}")
        return {}

class QTextEditLogger(logging.Handler):
    """
    Custom logging handler that writes logs to a QTextEdit widget.
    """
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.widget.setReadOnly(True)

    def emit(self, record):
        """
        Emit a log record by formatting it and adding it to the QTextEdit.
        """
        try:
            msg = self.format(record)
            color = {
                'INFO': '#ffffff',
                'WARNING': '#ffa500',
                'ERROR': '#ff0000',
                'CRITICAL': '#ff0000',
                'DEBUG': '#808080'
            }.get(record.levelname, '#ffffff')
            
            formatted_msg = f'<span style="color: {color}">{msg}</span><br>'
            
            # Ensure GUI updates happen in the main thread
            def append_text():
                self.widget.append(formatted_msg)
                # Auto-scroll to bottom
                scrollbar = self.widget.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
            # Use QTimer to safely update GUI from any thread
            QTimer.singleShot(0, append_text)
            
        except Exception as e:
            print(f"Error in log handler: {e}")





class RecordingThread(QThread):
    """Thread for handling system recording."""
    log_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)  # Signal for error messages
    status_signal = pyqtSignal(bool)  # Signal for recording status

    def __init__(self, parent=None, cpu_limit=70, memory_limit=75):
        super().__init__(parent)
        self.recording_data = []
        self._is_running = True
        self._is_paused = False
        self.pause_condition = threading.Condition()
        self.recorder = None  # Initialize recorder as None
        
        # Resource limits
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit

        # Initialize directories
        try:
            os.makedirs('screenshots', exist_ok=True)
            os.makedirs('logs', exist_ok=True)
            os.makedirs('screen_recordings', exist_ok=True)
            os.makedirs('raw_recordings', exist_ok=True)
        except Exception as e:
            self.error_signal.emit(f"Failed to create directories: {str(e)}")

    def run(self):
        """Main recording loop."""
        try:
            self.log_signal.emit("Initializing recording system...")
            
            # Import and create recorder
            from system_recording import EnhancedSystemRecorder
            self.recorder = EnhancedSystemRecorder()
            
            # Configure resource limits
            self.log_signal.emit("Configuring resource limits...")
            if hasattr(self.recorder, 'resource_manager'):
                self.recorder.resource_manager.max_cpu_percent = self.cpu_limit
                self.recorder.resource_manager.max_memory_percent = self.memory_limit
            
            # Start recording
            self.log_signal.emit("Starting recording...")
            if not self.recorder.start():
                raise Exception("Failed to start recording - user cancelled or initialization failed")
            
            self.log_signal.emit("Recording started successfully")
            self.status_signal.emit(True)
            
            # Main recording loop
            while self._is_running:
                try:
                    with self.pause_condition:
                        while self._is_paused and self._is_running:
                            if self.recorder:
                                self.recorder.pause()
                            self.pause_condition.wait()
                        if self._is_running and self.recorder:
                            self.recorder.resume()
                    
                    time.sleep(0.1)
                except Exception as loop_error:
                    self.error_signal.emit(f"Error in recording loop: {str(loop_error)}")
                    break
            
            # Stop recording and get data
            self.log_signal.emit("Stopping recording...")
            if self.recorder:
                self.recorder.stop()
                self.recording_data = self.recorder.recording_data
                self.log_signal.emit("Recording stopped successfully")
            
        except Exception as e:
            error_msg = f"Recording error: {str(e)}"
            self.error_signal.emit(error_msg)
            logging.error(f"Detailed error: {e}", exc_info=True)
            if self.recorder:
                try:
                    self.recorder.cleanup_on_error()
                except:
                    pass
            self.status_signal.emit(False)

    def stop(self):
        """Stop recording."""
        self._is_running = False
        with self.pause_condition:
            self._is_paused = False
            self.pause_condition.notify()
        if self.recorder:
            try:
                self.recorder.stop()
            except Exception as e:
                self.error_signal.emit(f"Error stopping recording: {str(e)}")

    def pause(self):
        """Pause recording."""
        self._is_paused = True
        if self.recorder:
            try:
                self.recorder.pause()
            except Exception as e:
                self.error_signal.emit(f"Error pausing recording: {str(e)}")

    def resume(self):
        """Resume recording."""
        with self.pause_condition:
            self._is_paused = False
            self.pause_condition.notify()
        if self.recorder:
            try:
                self.recorder.resume()
            except Exception as e:
                self.error_signal.emit(f"Error resuming recording: {str(e)}")

    def get_recording_data(self):
        """Get the recorded data."""
        return self.recording_data


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    workflows = load_workflows()
    gui = MainGUI(workflows)
    gui.show()
    sys.exit(app.exec())
