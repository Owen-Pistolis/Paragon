from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QMessageBox,
    QTextEdit, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor
from automation_display import AutomationDisplay
import json
import os
import logging

class ActionPanel(QWidget):
    """Panel for displaying action information and logs"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Action info section
        action_info_group = QFrame()
        action_info_group.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        action_info_layout = QVBoxLayout(action_info_group)
        
        # Previous action
        self.prev_action_label = QLabel("Previous Action:")
        self.prev_action_text = QLabel()
        self.prev_action_text.setWordWrap(True)
        self.prev_action_text.setStyleSheet("color: #808080;")
        
        # Current action
        self.curr_action_label = QLabel("Current Action:")
        self.curr_action_text = QLabel()
        self.curr_action_text.setWordWrap(True)
        self.curr_action_text.setStyleSheet("color: #ffffff; font-weight: bold;")
        
        # Next action
        self.next_action_label = QLabel("Next Action:")
        self.next_action_text = QLabel()
        self.next_action_text.setWordWrap(True)
        self.next_action_text.setStyleSheet("color: #808080;")
        
        # Add action info widgets
        action_info_layout.addWidget(self.prev_action_label)
        action_info_layout.addWidget(self.prev_action_text)
        action_info_layout.addWidget(self.curr_action_label)
        action_info_layout.addWidget(self.curr_action_text)
        action_info_layout.addWidget(self.next_action_label)
        action_info_layout.addWidget(self.next_action_text)
        
        # Log section
        log_group = QFrame()
        log_group.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        log_layout = QVBoxLayout(log_group)
        
        log_label = QLabel("Execution Log:")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', monospace;
            }
        """)
        
        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_text)
        
        # Add sections to main layout
        layout.addWidget(action_info_group)
        layout.addWidget(log_group)
        
    def update_actions(self, prev=None, curr=None, next=None):
        """Update the displayed actions"""
        if prev:
            self.prev_action_text.setText(self._format_action(prev))
        else:
            self.prev_action_text.setText("None")
            
        if curr:
            self.curr_action_text.setText(self._format_action(curr))
        else:
            self.curr_action_text.setText("None")
            
        if next:
            self.next_action_text.setText(self._format_action(next))
        else:
            self.next_action_text.setText("None")
            
    def _format_action(self, action):
        """Format an action for display"""
        action_type = action.get('action_type', 'Unknown')
        context = action.get('context', '')
        meta = action.get('meta_information', {})
        
        if action_type == 'application_open':
            path = meta.get('url_path_context', {}).get('file_path', '')
            return f"Open application: {path}"
            
        elif action_type == 'typing_sequence':
            text = meta.get('text_entered', '')
            return f"Type text: {text[:30]}..."
            
        elif action_type == 'open_selenium':
            browser = meta.get('application_context', {}).get('application_name', '')
            url = meta.get('url_path_context', {}).get('url', '')
            return f"Open {browser}: {url}"
            
        elif action_type == 'parse_content':
            selector = meta.get('selector', '')
            return f"Parse content: {selector}"
            
        elif action_type == 'shortcut_use':
            shortcut = meta.get('shortcut', '')
            return f"Use shortcut: {shortcut}"
            
        elif action_type == 'special_key_press':
            key = meta.get('key', '')
            return f"Press key: {key}"
            
        elif action_type == 'handle_dialog':
            dialog_type = meta.get('dialog_type', '')
            response = meta.get('response', '')
            return f"Handle {dialog_type} dialog: {response}"
            
        elif action_type == 'wait':
            duration = meta.get('duration', 0)
            return f"Wait for {duration} seconds"
            
        elif action_type == 'application_close':
            element = meta.get('element_context', {}).get('element_name', '')
            return f"Close application: {element}"
            
        return f"{action_type} ({context})"
        
    def add_log(self, message: str, level: int = logging.INFO):
        """Add a message to the log with appropriate formatting"""
        cursor = self.log_text.textCursor()
        format = QTextCharFormat()
        
        # Set color based on log level
        if level == logging.ERROR:
            format.setForeground(QColor("#ff6b6b"))
        elif level == logging.WARNING:
            format.setForeground(QColor("#ffd93d"))
        elif level == logging.INFO:
            format.setForeground(QColor("#6bff6b"))
        else:
            format.setForeground(QColor("#ffffff"))
            
        # Move cursor to end and insert formatted text
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"{message}\n", format)
        
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

class AutomationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Automation Display")
        self.setMinimumSize(1200, 800)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        try:
            self._init_ui()
            self.load_workflows()
        except Exception as e:
            self.logger.error(f"Failed to initialize window: {e}")
            QMessageBox.critical(self, "Initialization Error", 
                f"Failed to initialize application: {str(e)}\n\nPlease check the logs for details.")
            
    def _init_ui(self):
        """Initialize the UI components with error handling"""
        try:
            # Create central widget and layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QHBoxLayout(central_widget)
            
            # Create left panel for automation display
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            
            # Create header
            header_layout = QHBoxLayout()
            workflow_label = QLabel("Select Workflow:")
            workflow_label.setStyleSheet("color: #e0e0e0; font-size: 14px;")
            
            self.workflow_combo = QComboBox()
            self.workflow_combo.setStyleSheet("""
                QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    padding: 5px;
                    min-width: 200px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(down_arrow.png);
                    width: 12px;
                    height: 12px;
                }
            """)
            
            # Add workflow selection change handler
            self.workflow_combo.currentIndexChanged.connect(self.on_workflow_selected)
            header_layout.addWidget(workflow_label)
            header_layout.addWidget(self.workflow_combo)
            header_layout.addStretch()
            
            # Add header to left layout
            left_layout.addLayout(header_layout)
            
            # Create right panel for action display first
            try:
                self.action_panel = ActionPanel()
            except Exception as e:
                self.logger.error(f"Failed to create action panel: {e}")
                raise
            
            # Create automation display after action panel
            try:
                self.automation_display = AutomationDisplay()
                self.automation_display.automation_completed.connect(self.on_automation_completed)
                self.automation_display.log_message.connect(self.action_panel.add_log)
                left_layout.addWidget(self.automation_display)
            except Exception as e:
                self.logger.error(f"Failed to create automation display: {e}")
                raise
            
            # Add panels to main layout
            layout.addWidget(left_panel, stretch=2)
            layout.addWidget(self.action_panel, stretch=1)
            
            # Set dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                }
                QWidget {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
            """)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UI: {e}")
            raise
            
    def load_workflows(self):
        """Load available workflows with error handling"""
        try:
            # Create workflows directory if it doesn't exist
            workflows_dir = "workflows"
            if not os.path.exists(workflows_dir):
                os.makedirs(workflows_dir)
                self.logger.info("Created workflows directory")
                
            # Get all JSON files from workflows directory
            workflow_files = [f for f in os.listdir(workflows_dir) 
                            if f.endswith('.json')]
                            
            if not workflow_files:
                self.logger.warning("No workflow files found in workflows directory")
                self.workflow_combo.addItem("No workflows available")
                self.workflow_combo.setEnabled(False)
                return
                
            # Clear existing items
            self.workflow_combo.clear()
                
            # Load each workflow file
            for workflow_file in workflow_files:
                try:
                    file_path = os.path.join(workflows_dir, workflow_file)
                    with open(file_path, 'r') as f:
                        workflow_data = json.load(f)
                        
                    # Get workflow name and add to combo box
                    workflow_name = workflow_data.get('name', os.path.splitext(workflow_file)[0])
                    self.workflow_combo.addItem(workflow_name, file_path)
                    self.logger.info(f"Loaded workflow: {workflow_name} from {workflow_file}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to load workflow {workflow_file}: {e}")
                    
            self.workflow_combo.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Failed to load workflows: {e}")
            self.workflow_combo.addItem("Error loading workflows")
            self.workflow_combo.setEnabled(False)
            QMessageBox.warning(self, "Workflow Loading Error",
                f"Failed to load workflows: {str(e)}")
                
    def on_workflow_selected(self, index):
        """Handle workflow selection with error handling"""
        try:
            if index < 0:
                return
                
            workflow_path = self.workflow_combo.itemData(index)
            if not workflow_path:
                self.logger.warning(f"No workflow path for index {index}")
                return
                
            self.logger.info(f"Loading workflow from: {workflow_path}")
            success = self.automation_display.workflow_executor.load_workflow(workflow_path)
            
            if success:
                self.logger.info("Successfully loaded workflow")
                # Update action panel with initial workflow state
                try:
                    with open(workflow_path, 'r') as f:
                        workflow_data = json.load(f)
                    actions = workflow_data.get('actions', [])
                    if actions:
                        self.action_panel.update_actions(
                            prev=None,
                            curr=actions[0] if len(actions) > 0 else None,
                            next=actions[1] if len(actions) > 1 else None
                        )
                except Exception as e:
                    self.logger.error(f"Failed to update action panel: {e}")
            else:
                self.logger.error("Failed to load workflow")
                QMessageBox.warning(self, "Workflow Loading Error",
                    "Failed to load the selected workflow. Please check the logs for details.")
                    
        except Exception as e:
            self.logger.error(f"Error selecting workflow: {e}")
            QMessageBox.warning(self, "Workflow Selection Error",
                f"Failed to select workflow: {str(e)}")
                
    def on_automation_completed(self, success, message):
        """Handle automation completion with error handling"""
        try:
            if success:
                self.logger.info("Automation completed successfully")
                QMessageBox.information(self, "Automation Complete", 
                    "Workflow execution completed successfully.")
            else:
                self.logger.error(f"Automation failed: {message}")
                QMessageBox.warning(self, "Automation Failed",
                    f"Workflow execution failed:\n\n{message}")
                    
        except Exception as e:
            self.logger.error(f"Error handling automation completion: {e}")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Set application-wide style
    app.setStyle("Fusion")
    
    # Create and show window
    window = AutomationWindow()
    window.show()
    
    sys.exit(app.exec()) 