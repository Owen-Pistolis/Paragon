from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QScrollArea, QWidget, QLineEdit, QHBoxLayout,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
import openai
import json
import time
import re
import shared
import asyncio
import logging
from pydantic import BaseModel, Field, validator, ValidationError
from typing import List, Optional, Dict, Union
from datetime import datetime


class LLMWizardDialog(QDialog):
    response_received = pyqtSignal(str)

    def __init__(self, main):
        super().__init__()
        self.main = main
        if not self.main.api_key:
            QMessageBox.critical(self, "Error", "Please set your OpenAI API Key first.")
            return

        openai.api_key = self.main.api_key
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are an expert workflow automation assistant that creates precise, robust workflows. "
                "Your workflows must follow these exact patterns and use these specific action types:\n\n"

                "CORE ACTION PATTERNS:\n\n"
                
                "1. Browser Actions:\n"
                "- open_selenium:\n"
                "  * Required: browser='chrome', headless=false\n"
                "  * Always first action for web automation\n\n"
                
                "- url_navigation:\n"
                "  * Required: url=string\n"
                "  * Always follows open_selenium\n\n"
                
                "- element_interact:\n"
                "  * Required: selector, by, action\n"
                "  * by options: 'xpath', 'id', 'name', 'css selector'\n"
                "  * action options: 'click', 'input'\n"
                "  * For credentials: include credential_name and credential_field\n\n"
                
                "- close_selenium:\n"
                "  * Always last action in browser sequences\n\n"

                "2. Desktop Actions:\n"
                "- open_application:\n"
                "  * Required: application_path\n\n"
                
                "- typing_sequence:\n"
                "  * Required: text, typing_speed\n"
                "  * typing_speed typically 0.1\n\n"
                
                "- key_combination:\n"
                "  * Required: keys=[list of keys]\n"
                "  * Example: ['alt', 'tab']\n\n"

                "3. Control Actions:\n"
                "- wait:\n"
                "  * Required: duration (in seconds)\n"
                "  * Use between critical actions\n\n"

                "EXAMPLE WORKFLOW (Login Pattern):\n"
                "```json\n"
                "{\n"
                '    "name": "Web Login Example",\n'
                '    "actions": [\n'
                '        {\n'
                '            "type": "open_selenium",\n'
                '            "browser": "chrome",\n'
                '            "headless": false,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 1,\n'
                '                "description": "Open browser"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "url_navigation",\n'
                '            "url": "https://example.com/login",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 2,\n'
                '                "description": "Navigate to login page"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "element_interact",\n'
                '            "selector": "//input[@id=\'username\']",\n'
                '            "by": "xpath",\n'
                '            "action": "input",\n'
                '            "credential_name": "example_creds",\n'
                '            "credential_field": "username",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 3,\n'
                '                "description": "Enter username"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "wait",\n'
                '            "duration": 1,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 4,\n'
                '                "description": "Short pause"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "close_selenium",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 5,\n'
                '                "description": "Close browser"\n'
                '            }\n'
                '        }\n'
                '    ]\n'
                '}\n'
                "```\n\n"

                "CRITICAL RULES:\n"
                "1. Always include proper wait actions between critical steps\n"
                "2. Always use sequence_order starting from 1\n"
                "3. Always close browser sessions\n"
                "4. Use xpath selectors for maximum reliability\n"
                "5. Include clear, specific descriptions\n"
                "6. Follow exact action patterns shown above\n"
                "7. Include all required fields for each action type\n"
                "8. Use credential_name and credential_field for login forms\n"
                "9. Add waits after navigation and before clicks\n"
                "10. Validate all actions match the Pydantic models\n\n"

                "SELECTOR PATTERNS:\n"
                "- Login forms: //input[@id='username'], //input[@id='password']\n"
                "- Submit buttons: //button[@id='submit'], //button[@type='submit']\n"
                "- Search boxes: //input[@type='search'], //input[@name='q']\n"
                "- Navigation: //a[contains(@href, '/path')]\n"
                "- Forms: //form[@id='login-form']//input\n\n"

                "Always output complete, valid JSON workflows within ```json code blocks."
            )
        }

        self.setWindowTitle("Workflow Setup Wizard")
        self.resize(600, 500)

        self.wizard_conversation = [self.system_prompt]
        self.init_ui()

        initial_prompt = (
            "Hello, I am Paragon, a model of excellence and a workflow wizard! I'm here to help you automate your task through chat or system recording. "
            "To begin, please provide a name for your workflow."
        )
        self.wizard_conversation.append({"role": "assistant", "content": initial_prompt})
        self.add_message("Assistant", initial_prompt)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_area.setWidget(self.chat_container)
        main_layout.addWidget(self.chat_area)

        input_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        main_layout.addLayout(input_layout)

    def add_message(self, sender, message):
        """
        Adds a formatted message to the chat area.
        """
        formatted_message = (
            f"<div style='margin-bottom: 10px; padding: 5px; border-radius: 5px;'>"
            f"<b>{sender}:</b><br>{message.replace(chr(10), '<br>')}"
            "</div>"
        )
        message_label = QLabel(formatted_message)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)  # Enable rich text rendering
        self.chat_layout.addWidget(message_label)
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def send_message(self):
        user_message = self.user_input.text().strip()
        if not user_message:
            return

        self.wizard_conversation.append({"role": "user", "content": user_message})
        self.add_message("You", user_message)
        self.user_input.clear()

        # Start processing the response
        self.generate_assistant_reply(self.wizard_conversation)

    def generate_assistant_reply(self, conversation):
        """
        Function to generate assistant reply using OpenAI API in a background thread.
        """
        self.thread = QThread()
        self.worker = LLMWorker(self.main, conversation)
        self.worker.moveToThread(self.thread)

        # Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.response_received.connect(self.process_response)
        self.worker.response_received.connect(self.thread.quit)
        self.worker.response_received.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start the thread
        self.thread.start()

    def process_response(self, assistant_reply):
        """
        Processes the assistant's reply and validates workflow structure.
        """
        try:
            json_code_blocks = re.findall(r"```json(.*?)```", assistant_reply, re.DOTALL)
            
            if json_code_blocks:
                formatted_responses = []
                for block in json_code_blocks:
                    try:
                        # Parse JSON and validate with Pydantic
                        raw_workflow = json.loads(block.strip())
                        workflow = Workflow(**raw_workflow)
                        
                        # Format for display
                        formatted_json = json.dumps(workflow.dict(), indent=4)
                        formatted_responses.append(f"<pre>{formatted_json}</pre>")
                        
                        # Save validated workflow
                        self.main.workflows[workflow.name] = workflow.dict()
                        self.main.save_workflows_to_disk()
                        
                        # Add success message
                        formatted_responses.append(
                            f"<div style='color: green; margin: 10px 0;'>"
                            f"✓ Workflow '{workflow.name}' has been validated and saved!</div>"
                        )
                        
                    except json.JSONDecodeError as e:
                        formatted_responses.append(
                            f"<div style='color: red; margin: 10px 0;'>"
                            f"Error: Invalid JSON format - {str(e)}</div>"
                        )
                    except ValidationError as e:
                        formatted_responses.append(
                            f"<div style='color: red; margin: 10px 0;'>"
                            f"Error: Invalid workflow structure - {str(e)}</div>"
                        )
                        
                # Combine all responses
                assistant_reply = (
                    assistant_reply.split("```json")[0] + 
                    "\n".join(formatted_responses)
                )
                
            # Add the message to the chat
            self.add_message("Assistant", assistant_reply)
            self.wizard_conversation.append({"role": "assistant", "content": assistant_reply})
            
            # Update the workflow list in the main GUI
            self.main.update_workflow_listbox()
            
        except Exception as e:
            logging.error(f"Error processing response: {e}", exc_info=True)
            self.add_message(
                "System", 
                f"<div style='color: red;'>Error processing response: {str(e)}</div>"
            )

    def validate_workflow(self, workflow):
        """
        Validates the workflow structure and provides detailed error messages.
        Expected format:
        {
            "name": "Workflow Name",
            "actions": [
                {
                    "type": "action_type",
                    "meta_information": {
                        "sequence_order": integer,
                        "description": "string"
                    },
                    // action-specific parameters
                }
            ]
        }
        """
        try:
            # Check if workflow is a dictionary
            if not isinstance(workflow, dict):
                logging.error("Validation Error: Workflow is not a JSON object")
                return False

            # Check required top-level keys
            required_keys = ["name", "actions"]
            for key in required_keys:
                if key not in workflow:
                    logging.error(f"Validation Error: Missing required key '{key}'")
                    return False

            # Validate name
            if not isinstance(workflow["name"], str) or not workflow["name"].strip():
                logging.error("Validation Error: Name must be a non-empty string")
                return False

            # Validate actions array
            if not isinstance(workflow["actions"], list):
                logging.error("Validation Error: 'actions' must be an array")
                return False

            # Validate each action
            for i, action in enumerate(workflow["actions"]):
                if not isinstance(action, dict):
                    logging.error(f"Validation Error: Action {i} is not an object")
                    return False

                # Check required action keys
                if "type" not in action:
                    logging.error(f"Validation Error: Action {i} missing 'type'")
                    return False

                if "meta_information" not in action:
                    logging.error(f"Validation Error: Action {i} missing 'meta_information'")
                    return False

                # Validate meta_information
                meta = action["meta_information"]
                if not isinstance(meta, dict):
                    logging.error(f"Validation Error: Action {i} meta_information is not an object")
                    return False

                if "sequence_order" not in meta or not isinstance(meta["sequence_order"], int):
                    logging.error(f"Validation Error: Action {i} missing or invalid sequence_order")
                    return False

                if "description" not in meta or not isinstance(meta["description"], str):
                    logging.error(f"Validation Error: Action {i} missing or invalid description")
                    return False

            logging.info("Workflow validation successful")
            return True

        except Exception as e:
            logging.error(f"Validation Error: {str(e)}")
            return False

    def update_system_prompt(self):
        """Update system prompt with comprehensive examples and patterns."""
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are an expert workflow automation assistant that creates precise, robust workflows. "
                "Your workflows must follow these exact patterns and use these specific action types:\n\n"

                "CORE ACTION PATTERNS:\n\n"
                
                "1. Browser Actions:\n"
                "- open_selenium:\n"
                "  * Required: browser='chrome', headless=false\n"
                "  * Always first action for web automation\n\n"
                
                "- url_navigation:\n"
                "  * Required: url=string\n"
                "  * Always follows open_selenium\n\n"
                
                "- element_interact:\n"
                "  * Required: selector, by, action\n"
                "  * by options: 'xpath', 'id', 'name', 'css selector'\n"
                "  * action options: 'click', 'input'\n"
                "  * For credentials: include credential_name and credential_field\n\n"
                
                "- close_selenium:\n"
                "  * Always last action in browser sequences\n\n"

                "2. Desktop Actions:\n"
                "- open_application:\n"
                "  * Required: application_path\n\n"
                
                "- typing_sequence:\n"
                "  * Required: text, typing_speed\n"
                "  * typing_speed typically 0.1\n\n"
                
                "- key_combination:\n"
                "  * Required: keys=[list of keys]\n"
                "  * Example: ['alt', 'tab']\n\n"

                "3. Control Actions:\n"
                "- wait:\n"
                "  * Required: duration (in seconds)\n"
                "  * Use between critical actions\n\n"

                "EXAMPLE WORKFLOW (Login Pattern):\n"
                "```json\n"
                "{\n"
                '    "name": "Web Login Example",\n'
                '    "actions": [\n'
                '        {\n'
                '            "type": "open_selenium",\n'
                '            "browser": "chrome",\n'
                '            "headless": false,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 1,\n'
                '                "description": "Open browser"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "url_navigation",\n'
                '            "url": "https://example.com/login",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 2,\n'
                '                "description": "Navigate to login page"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "element_interact",\n'
                '            "selector": "//input[@id=\'username\']",\n'
                '            "by": "xpath",\n'
                '            "action": "input",\n'
                '            "credential_name": "example_creds",\n'
                '            "credential_field": "username",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 3,\n'
                '                "description": "Enter username"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "wait",\n'
                '            "duration": 1,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 4,\n'
                '                "description": "Short pause"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "close_selenium",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 5,\n'
                '                "description": "Close browser"\n'
                '            }\n'
                '        }\n'
                '    ]\n'
                '}\n'
                "```\n\n"

                "CRITICAL RULES:\n"
                "1. Always include proper wait actions between critical steps\n"
                "2. Always use sequence_order starting from 1\n"
                "3. Always close browser sessions\n"
                "4. Use xpath selectors for maximum reliability\n"
                "5. Include clear, specific descriptions\n"
                "6. Follow exact action patterns shown above\n"
                "7. Include all required fields for each action type\n"
                "8. Use credential_name and credential_field for login forms\n"
                "9. Add waits after navigation and before clicks\n"
                "10. Validate all actions match the Pydantic models\n\n"

                "SELECTOR PATTERNS:\n"
                "- Login forms: //input[@id='username'], //input[@id='password']\n"
                "- Submit buttons: //button[@id='submit'], //button[@type='submit']\n"
                "- Search boxes: //input[@type='search'], //input[@name='q']\n"
                "- Navigation: //a[contains(@href, '/path')]\n"
                "- Forms: //form[@id='login-form']//input\n\n"

                "Always output complete, valid JSON workflows within ```json code blocks."

                "COMPREHENSIVE EXAMPLE (All Action Types):\n"
                "```json\n"
                "{\n"
                '    "name": "Complete Workflow Example",\n'
                '    "actions": [\n'
                '        {\n'
                '            "type": "open_selenium",\n'
                '            "browser": "chrome",\n'
                '            "headless": false,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 1,\n'
                '                "description": "Open Chrome browser"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "url_navigation",\n'
                '            "url": "https://example.com/login",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 2,\n'
                '                "description": "Navigate to login page"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "wait",\n'
                '            "duration": 2,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 3,\n'
                '                "description": "Wait for page load"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "element_interact",\n'
                '            "selector": "//input[@id=\'username\']",\n'
                '            "by": "xpath",\n'
                '            "action": "input",\n'
                '            "credential_name": "example_creds",\n'
                '            "credential_field": "username",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 4,\n'
                '                "description": "Enter username"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "key_combination",\n'
                '            "keys": ["tab"],\n'
                '            "meta_information": {\n'
                '                "sequence_order": 5,\n'
                '                "description": "Move to password field"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "typing_sequence",\n'
                '            "text": "secure_password",\n'
                '            "typing_speed": 0.1,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 6,\n'
                '                "description": "Type password"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "element_interact",\n'
                '            "selector": "//button[@type=\'submit\']",\n'
                '            "by": "xpath",\n'
                '            "action": "click",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 7,\n'
                '                "description": "Click login button"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "wait",\n'
                '            "duration": 2,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 8,\n'
                '                "description": "Wait for login"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "open_application",\n'
                '            "application_path": "notepad.exe",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 9,\n'
                '                "description": "Open Notepad"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "typing_sequence",\n'
                '            "text": "Login successful",\n'
                '            "typing_speed": 0.1,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 10,\n'
                '                "description": "Record success"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "file_save",\n'
                '            "file_path": "C:/logs/login_log.txt",\n'
                '            "content": "Login completed successfully",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 11,\n'
                '                "description": "Save log file"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "mouse_click",\n'
                '            "x": 100,\n'
                '            "y": 100,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 12,\n'
                '                "description": "Click specific coordinates"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "search_query",\n'
                '            "query": "search term",\n'
                '            "wait_time": 2.0,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 13,\n'
                '                "description": "Perform search"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "wait_for",\n'
                '            "condition": "element_visible",\n'
                '            "selector": "//div[@class=\'results\']",\n'
                '            "by": "xpath",\n'
                '            "timeout": 10.0,\n'
                '            "meta_information": {\n'
                '                "sequence_order": 14,\n'
                '                "description": "Wait for results"\n'
                '            }\n'
                '        },\n'
                '        {\n'
                '            "type": "close_selenium",\n'
                '            "meta_information": {\n'
                '                "sequence_order": 15,\n'
                '                "description": "Close browser"\n'
                '            }\n'
                '        }\n'
                '    ]\n'
                '}\n'
                "```\n\n"
            )
        }


class LLMWorker(QObject):
    response_received = pyqtSignal(str)

    def __init__(self, main, conversation):
        super().__init__()
        self.main = main
        self.conversation = conversation

    async def async_run(self):
        """
        Asynchronous method to communicate with OpenAI API.
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=self.conversation
            )
            assistant_reply = response.choices[0].message.content
        except Exception as e:
            assistant_reply = f"Error communicating with OpenAI API: {e}"

        self.response_received.emit(assistant_reply)

    def run(self):
        """
        Synchronous entry point for PyQt's QThread, calls async_run using asyncio.
        """
        asyncio.run(self.async_run())

# Pydantic models for workflow structure
class ActionMetaInfo(BaseModel):
    sequence_order: int = Field(..., description="Order of action in workflow")
    description: str = Field(..., description="Human-readable description of the action")

class BaseAction(BaseModel):
    type: str = Field(..., description="Type of action to perform")
    meta_information: ActionMetaInfo

class MouseAction(BaseAction):
    type: str = Field(..., pattern="^(left_click|right_click|middle_click|double_left_click|mouse_drag|mouse_hover|mouse_scroll|mouse_move|context_menu_open)$")
    x: Optional[int] = Field(None, description="X coordinate for mouse action")
    y: Optional[int] = Field(None, description="Y coordinate for mouse action")
    start_x: Optional[int] = Field(None, description="Starting X coordinate for drag")
    start_y: Optional[int] = Field(None, description="Starting Y coordinate for drag")
    end_x: Optional[int] = Field(None, description="Ending X coordinate for drag")
    end_y: Optional[int] = Field(None, description="Ending Y coordinate for drag")
    duration: Optional[float] = Field(default=1.0, ge=0.1, description="Duration for hover/drag/move")
    direction: Optional[str] = Field(default="up", pattern="^(up|down)$", description="Scroll direction")
    amount: Optional[int] = Field(default=1, description="Scroll amount")

class KeyboardAction(BaseAction):
    type: str = Field(..., pattern="^(keystroke|typing_sequence|key_combination|special_key_press|shortcut_use)$")
    key: Optional[str] = Field(None, description="Single key to press")
    keys: Optional[List[str]] = Field(None, description="Keys for combination")
    text: Optional[str] = Field(None, description="Text to type")
    typing_speed: Optional[float] = Field(0.1, ge=0.01, le=1.0, description="Speed of typing")
    shortcut: Optional[str] = Field(None, description="Predefined keyboard shortcut")

class FileAction(BaseAction):
    type: str = Field(..., pattern="^(file_open|file_save|file_delete|file_rename|file_move|file_copy|file_upload|file_download)$")
    file_path: str = Field(..., description="Path to file")
    content: Optional[str] = Field(None, description="Content for file save")
    new_name: Optional[str] = Field(None, description="New name for rename")
    destination_path: Optional[str] = Field(None, description="Destination path for move/copy")
    file_url: Optional[str] = Field(None, description="URL for file download")

class BrowserAction(BaseAction):
    type: str = Field(..., pattern="^(open_selenium|close_selenium|element_interact|url_navigation|search_query)$")
    browser: Optional[str] = Field("chrome", pattern="^(chrome|firefox)$")
    headless: Optional[bool] = Field(False)
    selector: Optional[str] = Field(None)
    by: Optional[str] = Field(
        "name",
        pattern="^(id|name|css selector|xpath|class name|tag name|link text|partial link text)$"
    )
    url: Optional[str] = Field(None)
    query: Optional[str] = Field(None)
    wait_time: Optional[float] = Field(2.0, ge=0.1)

class CommunicationAction(BaseAction):
    type: str = Field(..., pattern="^(email_read|email_write|email_send|scan_inbox|email_search)$")
    platform: Optional[str] = Field("outlook", pattern="^(outlook|gmail)$")
    to_address: Optional[str] = Field(None)
    subject: Optional[str] = Field(None)
    body: Optional[str] = Field(None)
    cc: Optional[List[str]] = Field(None)
    bcc: Optional[List[str]] = Field(None)
    criteria: Optional[dict] = Field(None)
    smtp_server: Optional[str] = Field(None)
    smtp_port: Optional[int] = Field(None)
    smtp_username: Optional[str] = Field(None)
    smtp_password: Optional[str] = Field(None)

class SecurityAction(BaseAction):
    type: str = Field(..., pattern="^(login_attempt|logout|permission_request|run_as_administrator)$")
    name: Optional[str] = Field(None)
    permission: Optional[str] = Field(None)
    command: Optional[str] = Field(None)

class SpecializedAction(BaseAction):
    type: str = Field(..., pattern="^(dropdown_select|wait|wait_for)$")
    selector: Optional[str] = Field(None)
    value: Optional[str] = Field(None)
    by: Optional[str] = Field("css selector")
    is_local: Optional[bool] = Field(False)
    window_title: Optional[str] = Field(None)
    duration: Optional[float] = Field(1.0, ge=0.1)
    condition: Optional[str] = Field(None)
    timeout: Optional[float] = Field(30.0, ge=0.1)

class Workflow(BaseModel):
    name: str = Field(..., description="Name of the workflow")
    actions: List[Union[
        MouseAction,
        KeyboardAction,
        FileAction,
        BrowserAction,
        CommunicationAction,
        SecurityAction,
        SpecializedAction
    ]] = Field(..., description="List of actions to perform")

    @validator('name')
    def name_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError("Workflow name cannot be empty")
        if len(v) > 100:
            raise ValueError("Workflow name too long (max 100 characters)")
        return v.strip()

    @validator('actions')
    def actions_must_be_valid(cls, v):
        if not v:
            raise ValueError("Workflow must contain at least one action")
        
        # Validate sequence order
        sequence_numbers = [action.meta_information.sequence_order for action in v]
        if sorted(sequence_numbers) != list(range(1, len(v) + 1)):
            raise ValueError("Action sequence_order must be sequential starting from 1")
        
        # Validate browser session logic
        browser_opened = False
        for action in v:
            if isinstance(action, BrowserAction):
                if action.type == 'open_selenium':
                    if browser_opened:
                        raise ValueError("Cannot open browser session when one is already open")
                    browser_opened = True
                elif action.type == 'close_selenium':
                    if not browser_opened:
                        raise ValueError("Cannot close browser session when none is open")
                    browser_opened = False
                elif action.type in ['url_navigation', 'element_interact', 'search_query']:
                    if not browser_opened:
                        raise ValueError(f"Cannot perform {action.type} without an open browser session")
        
        if browser_opened:
            raise ValueError("Browser session must be closed at end of workflow")
        
        return v

    class Config:
        extra = "forbid"  # Prevent additional fields not in the model
