from PyQt6.QtCore import QObject, pyqtSignal
from browser_automation import BrowserAutomation
from windows_automation import WindowsAutomation
import json
import time
import threading
import logging
import os

class WorkflowExecutor(QObject):
    progress_updated = pyqtSignal(int)  # Progress percentage
    step_started = pyqtSignal(str)  # Step description
    execution_completed = pyqtSignal(bool, str)  # Success status and message
    log_message = pyqtSignal(str, int)  # Log message and level
    
    def __init__(self):
        super().__init__()
        self.browser_automation = BrowserAutomation()
        self.windows_automation = WindowsAutomation()
        self.current_workflow = None
        self.is_running = False
        self.is_paused = False
        self.pause_event = threading.Event()
        self.last_result = None
        
    def load_workflow(self, workflow_path: str):
        """Load a workflow from a JSON file"""
        if not workflow_path:
            self.log_message.emit("No workflow path provided", logging.ERROR)
            return False
            
        if not os.path.exists(workflow_path):
            self.log_message.emit(f"Workflow file not found: {workflow_path}", logging.ERROR)
            return False
            
        try:
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
                
            # Validate workflow structure
            if not isinstance(workflow_data, dict):
                raise ValueError("Invalid workflow format: root must be an object")
                
            # Validate required fields
            if 'name' not in workflow_data:
                raise ValueError("Invalid workflow format: missing 'name' key")
                
            if 'actions' not in workflow_data:
                raise ValueError("Invalid workflow format: missing 'actions' key")
                
            if not isinstance(workflow_data['actions'], list):
                raise ValueError("Invalid workflow format: 'actions' must be an array")
                
            self.current_workflow = workflow_data
            self.log_message.emit(f"Successfully loaded workflow: {workflow_data['name']}", logging.INFO)
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in workflow file: {str(e)}"
            self.log_message.emit(error_msg, logging.ERROR)
            self.execution_completed.emit(False, error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Failed to load workflow: {str(e)}"
            self.log_message.emit(error_msg, logging.ERROR)
            self.execution_completed.emit(False, error_msg)
            return False
            
    def execute_workflow(self):
        """Execute the loaded workflow"""
        if not self.current_workflow:
            error_msg = "No workflow loaded"
            self.log_message.emit(error_msg, logging.ERROR)
            self.execution_completed.emit(False, error_msg)
            return
            
        self.is_running = True
        self.pause_event.clear()
        execution_thread = None
        
        try:
            # Get actions from workflow
            actions = self.current_workflow.get('actions', [])
            if not actions:
                error_msg = "No actions found in workflow"
                self.log_message.emit(error_msg, logging.ERROR)
                self.execution_completed.emit(False, error_msg)
                return
                
            # Create and start execution thread
            execution_thread = threading.Thread(target=self._execute_actions, args=(actions,))
            execution_thread.start()
            
        except Exception as e:
            error_msg = f"Failed to start workflow execution: {str(e)}"
            self.log_message.emit(error_msg, logging.ERROR)
            self.execution_completed.emit(False, error_msg)
            self.is_running = False
            
    def _execute_actions(self, actions):
        """Execute workflow actions in a separate thread"""
        try:
            total_actions = len(actions)
            
            for i, action in enumerate(actions):
                if not self.is_running:
                    break
                    
                # Handle pause
                while self.is_paused and self.is_running:
                    self.pause_event.wait()
                    
                # Validate action structure
                if not isinstance(action, dict):
                    raise ValueError(f"Invalid action format at index {i}: must be an object")
                    
                action_type = action.get('action_type')
                context = action.get('context')
                meta = action.get('meta_information', {})
                
                if not action_type:
                    raise ValueError(f"Invalid action at index {i}: missing 'action_type'")
                if not context:
                    raise ValueError(f"Invalid action at index {i}: missing 'context'")
                    
                # Emit step description
                description = self._get_action_description(action)
                self.step_started.emit(description)
                self.log_message.emit(f"Executing: {description}", logging.INFO)
                
                try:
                    # Execute action based on type and context
                    if context == 'browser':
                        result = self._execute_browser_action(action_type, meta)
                    elif context == 'windows':
                        result = self._execute_windows_action(action_type, meta)
                    else:
                        raise ValueError(f"Unknown context: {context}")
                        
                    if not result or result.get("status") != "success":
                        raise Exception(result.get("message", f"Action failed: {action_type}"))
                        
                except Exception as e:
                    self.log_message.emit(f"Action failed: {str(e)}", logging.ERROR)
                    raise
                    
                # Update progress
                progress = int((i + 1) / total_actions * 100)
                self.progress_updated.emit(progress)
                
                # Add delay between actions if specified
                delay = action.get('delay_after', 0)
                if delay:
                    time.sleep(delay)
                    
            if self.is_running:
                self.log_message.emit("Workflow completed successfully", logging.INFO)
                self.execution_completed.emit(True, "Workflow completed successfully")
                
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            self.log_message.emit(error_msg, logging.ERROR)
            self.execution_completed.emit(False, error_msg)
            
        finally:
            self.is_running = False
            self.pause_event.clear()
            
    def _get_action_description(self, action):
        """Generate a human-readable description of the action"""
        action_type = action.get('action_type', '')
        context = action.get('context', '')
        meta = action.get('meta_information', {})
        
        if action_type == 'application_open':
            path = meta.get('url_path_context', {}).get('file_path', '')
            return f"Opening application: {path}"
        
        elif action_type == 'typing_sequence':
            text = meta.get('text_entered', '')
            speed = meta.get('typing_speed_wpm', '')
            return f"Typing text at {speed} WPM: {text[:30]}..."
        
        elif action_type == 'open_selenium':
            browser = meta.get('application_context', {}).get('application_name', '')
            url = meta.get('url_path_context', {}).get('url', '')
            return f"Opening {browser} browser: {url}"
        
        elif action_type == 'parse_content':
            selector = meta.get('selector', '')
            return f"Parsing content with selector: {selector}"
        
        elif action_type == 'shortcut_use':
            shortcut = meta.get('shortcut', '')
            return f"Using shortcut: {shortcut}"
        
        elif action_type == 'special_key_press':
            key = meta.get('key', '')
            return f"Pressing key: {key}"
        
        elif action_type == 'handle_dialog':
            dialog_type = meta.get('dialog_type', '')
            response = meta.get('response', '')
            return f"Handling {dialog_type} dialog with response: {response}"
        
        elif action_type == 'wait':
            duration = meta.get('duration', 0)
            return f"Waiting for {duration} seconds"
        
        elif action_type == 'application_close':
            element = meta.get('element_context', {}).get('element_name', '')
            return f"Closing application: {element}"
        
        return f"{action_type} ({context})"
        
    def _execute_browser_action(self, action_type, meta):
        """Execute a browser automation action"""
        try:
            # Get the corresponding method from BrowserAutomation
            method = getattr(self.browser_automation, action_type, None)
            if not method:
                error_msg = f"Unknown browser action: {action_type}"
                self.log_message.emit(error_msg, logging.ERROR)
                return {"status": "error", "message": error_msg}
                
            # Execute the method
            result = method(meta)
            
            # Check if result is valid
            if not result:
                error_msg = f"Browser action returned no result: {action_type}"
                self.log_message.emit(error_msg, logging.ERROR)
                return {"status": "error", "message": error_msg}
                
            # Log the result for debugging
            self.log_message.emit(f"Browser action result: {result}", logging.DEBUG)
            
            # Store result for potential use in subsequent actions
            if result.get("status") == "success":
                if "text" in result:
                    self.last_result = type('Result', (), {'text': result["text"]})()
                if "data" in result:
                    self.last_result = type('Result', (), {'data': result["data"]})()
            else:
                # If the action failed, log the error message
                error_msg = result.get("message", f"Browser action failed: {action_type}")
                self.log_message.emit(error_msg, logging.ERROR)
                
            return result
            
        except Exception as e:
            error_msg = f"Browser action failed: {str(e)}"
            self.log_message.emit(error_msg, logging.ERROR)
            return {"status": "error", "message": error_msg}

    def _execute_windows_action(self, action_type, meta):
        """Execute a windows automation action"""
        try:
            # Handle variable substitution in meta information
            if isinstance(meta, dict):
                for key, value in meta.items():
                    if isinstance(value, str) and '{last_result.text}' in value and hasattr(self, 'last_result'):
                        meta[key] = value.replace('{last_result.text}', getattr(self.last_result, 'text', ''))
            
            # Get the corresponding method from WindowsAutomation
            method = getattr(self.windows_automation, action_type, None)
            if not method:
                raise Exception(f"Unknown windows action: {action_type}")
                
            # Execute the method
            result = method(meta)
            
            # Store result for potential use in subsequent actions
            if result and result.get("status") == "success":
                if "text" in result:
                    self.last_result = type('Result', (), {'text': result["text"]})()
                if "data" in result:
                    self.last_result = type('Result', (), {'data': result["data"]})()
                    
            return result
            
        except Exception as e:
            self.log_message.emit(f"Windows action failed: {str(e)}", logging.ERROR)
            raise
        
    def pause(self):
        """Pause workflow execution"""
        self.is_paused = True
        self.pause_event.clear()
        self.log_message.emit("Workflow execution paused", logging.INFO)
        
    def resume(self):
        """Resume workflow execution"""
        self.is_paused = False
        self.pause_event.set()
        self.log_message.emit("Workflow execution resumed", logging.INFO)
        
    def stop(self):
        """Stop workflow execution"""
        self.is_running = False
        self.is_paused = False
        self.pause_event.set()  # Wake up paused thread
        self.log_message.emit("Workflow execution stopped", logging.INFO)