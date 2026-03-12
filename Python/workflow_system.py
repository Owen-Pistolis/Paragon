# General Python Libraries
import os
import threading
from threading import Timer
from concurrent.futures import ThreadPoolExecutor
import json
from cryptography.fernet import Fernet
import shutil
import time
# PyAutoGUI for Mouse and Keyboard Automation
import pyautogui
from pywinauto.application import Application
import re
import logging
# Pyperclip for Clipboard Operations
import pyperclip
import subprocess
import requests
import smtplib
import pyotp
import shlex

# Selenium for Browser Automation
import selenium
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait

# IMAP for Email Handling (Optional if not used)
import imaplib
import email
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart

#Outlook
import win32com.client

#Google
from email.mime.text import MIMEText
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
# Test Google with a simple service build (e.g., Gmail API setup)
service = build("gmail", "v1", developerKey="your_api_key_here")
print("Google API Client successfully imported!")

import pygetwindow as gw
from screeninfo import get_monitors
#below is test for screeninfo get_monitors
# List all connected monitors and their details
monitors = get_monitors()
for monitor in monitors:
    print(f"Monitor: {monitor.name}, Width: {monitor.width}, Height: {monitor.height}")

# Use the same logging configuration as main.py
logging.getLogger().setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("workflow_execution.log"),
        logging.StreamHandler()
    ]
)

# --- Workflow Classes and Utilities ---

class Workflow:
    """
    Represents the state of a workflow, including:
    - Selenium WebDriver instance for browser automation.
    - Variables for sharing data between actions.
    - Current URL for browser tracking.
    """

    def __init__(self):
        self.driver = None  # Selenium WebDriver instance
        self.url = None  # Current URL
        self.variables = {}  # Shared variables


class WorkflowThread(threading.Thread):
    """
    A thread class for executing a single workflow.

    Args:
        workflow_name (str): The name of the workflow.
        workflow_actions (list): List of actions to execute in the workflow.
        workflow_state (Workflow): The state object associated with the workflow.
    """

    def __init__(self, workflow_name, workflow_actions, workflow_state):
        super().__init__()
        self.workflow_name = workflow_name
        self.workflow_actions = workflow_actions
        self.workflow_state = workflow_state
        self.start_time = None
        self.end_time = None

    def run(self):
        """
        Executes the workflow actions in this thread.
        Logs the start time, each action, and the duration.
        """
        try:
            self.start_time = time.time()
            logging.info(f"Starting workflow '{self.workflow_name}' in thread {self.name}")

            # Execute actions using typeSwitch
            typeSwitch(self.workflow_actions, self.workflow_state)

            self.end_time = time.time()
            duration = self.end_time - self.start_time
            logging.info(f"Completed workflow '{self.workflow_name}' in thread {self.name} (Duration: {duration:.2f}s)")
        except Exception as e:
            logging.error(f"Error in workflow '{self.workflow_name}' in thread {self.name}: {e}")


# --- Workflow Execution Utilities ---

def load_workflows(file_path="workflows.json"):
    """
    Load workflows from a JSON file.

    Args:
        file_path (str): Path to the workflows JSON file.

    Returns:
        dict: Dictionary of workflows.
    """
    try:
        with open(file_path, "r") as file:
            workflows = json.load(file)
            logging.info(f"Successfully loaded workflows from {file_path}")
            return workflows
    except FileNotFoundError:
        logging.error(f"Workflows file not found at {file_path}")
        return {}
    except Exception as e:
        logging.error(f"Error loading workflows: {e}")
        return {}


def runWorkflow(workflowName):
    """
    Loads the specified workflow by name from the workflows.json file.

    Args:
        workflowName (str): The name of the workflow to execute.

    Returns:
        list: List of actions for the workflow, or -1 if not found.
    """
    try:
        with open("workflows.json", "r") as file:
            workflows = json.load(file)
    except FileNotFoundError:
        logging.error("The workflows.json file was not found.")
        return -1
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from workflows.json.")
        return -1

    workflow = workflows.get(workflowName)
    if workflow is None:
        logging.error(f"Workflow '{workflowName}' was not found.")
        return -1

    logging.info(f"Workflow '{workflowName}' loaded successfully.")
    return workflow


def run_workflow_thread(workflow_name, workflow_actions):
    """
    Executes a single workflow and logs execution details.
    """
    start_time = time.time()
    logging.info(f"Starting workflow '{workflow_name}'")

    workflow_state = Workflow()  # Create a fresh state for the workflow
    try:
        typeSwitch(workflow_actions, workflow_state)
    except Exception as e:
        logging.error(f"Error in workflow '{workflow_name}': {e}")
    finally:
        duration = time.time() - start_time
        logging.info(f"Completed workflow '{workflow_name}' (Duration: {duration:.2f}s)")


def run_workflows_multithreaded_with_futures(workflows, max_threads=5):
    """
    Executes multiple workflows in parallel using a thread pool.

    Args:
        workflows (dict): A dictionary of workflow names and their action lists.
        max_threads (int): Maximum number of threads to use.
    """
    with ThreadPoolExecutor(max_threads) as executor:
        futures = []
        for workflow_name, workflow_actions in workflows.items():
            futures.append(executor.submit(run_workflow_thread, workflow_name, workflow_actions))

        # Wait for all threads to complete
        for future in futures:
            try:
                future.result()  # Retrieve result or raise exception
            except Exception as e:
                logging.error(f"Error in thread execution: {e}")
    logging.info("All workflows completed successfully.")


def close_workflow_resources(workflow_state):
    """
    Cleans up resources for a workflow, such as browser drivers.
    """
    if workflow_state.driver:
        workflow_state.driver.quit()
        logging.info("Browser driver closed.")


def run_workflows_with_interrupt_handling(workflows):
    """
    Executes workflows with handling for interruptions (e.g., Ctrl+C) and cleanup.

    Args:
        workflows (dict): A dictionary of workflow names and their action lists.
    """
    try:
        run_workflows_multithreaded_with_futures(workflows)
    except KeyboardInterrupt:
        logging.warning("Execution interrupted by user. Shutting down workflows...")
    finally:
        logging.info("Workflow execution terminated.")


# --- Main Execution Block ---

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        # Load workflows from JSON
        with open("workflows.json", "r") as file:
            workflows = json.load(file)

        # Execute workflows with proper handling
        run_workflows_with_interrupt_handling(workflows)

    except FileNotFoundError:
        logging.error("Workflows file not found.")
    except json.JSONDecodeError:
        logging.error("Error parsing workflows.json.")


def substituteVariables(value, variables):
    """
    Substitute variables in strings using the format ${variable_name}.
    Useful for dynamic workflows where data is passed between actions.

    Args:
        value (str): The string that may contain variables to substitute.
        variables (dict): A dictionary of variables to use for substitution.

    Returns:
        str: The string with variables substituted.
    """
    if isinstance(value, str):
        pattern = re.compile(r'\${(.*?)}')
        matches = pattern.findall(value)
        for match in matches:
            variable_value = variables.get(match, '')
            value = value.replace(f"${{{match}}}", str(variable_value))
    return value


# At the appropriate place in your workflow_system.py

def execute_workflow(workflow_data):
    """
    Executes the given workflow data.

    Args:
        workflow_data (dict): The workflow data containing 'name' and 'actions'.
    """
    workflow_name = workflow_data.get('name', 'Unnamed Workflow')
    actions = workflow_data.get('actions', [])
    logging.info(f"Executing workflow: {workflow_name}")

    # Create a new Workflow state instance
    workflow_state = Workflow()

    try:
        # Execute the actions using typeSwitch
        typeSwitch(actions, workflow_state)
        logging.info(f"Workflow '{workflow_name}' executed successfully.")
    except Exception as e:
        logging.error(f"Error executing workflow '{workflow_name}': {e}")
    finally:
        # Clean up resources if necessary
        close_workflow_resources(workflow_state)


def processAction(action, variables):
    """
    Recursively process an action's parameters, substituting variables
    where necessary.
    """
    try:
        processed_action = {}
        for key, value in action.items():
            if isinstance(value, dict):
                processed_action[key] = processAction(value, variables)
            elif isinstance(value, list):
                processed_action[key] = [
                    processAction(item, variables) if isinstance(item, dict) else substituteVariables(item, variables) for
                    item in value]
            else:
                processed_action[key] = substituteVariables(value, variables)
        return processed_action
    except Exception as e:
        logging.error(f"Error processing action: {e}")
        raise

def execute_action(self, action):
    """
    Executes a normalized action with proper error handling and retries.
    """
    try:
        normalized_action = normalize_action(action)
        action_type = normalized_action['type']
        logging.info(f"Executing action: {action_type}")

        # Initialize browser if needed
        if action_type == 'open_selenium':
            self.cleanup_browser()
            self.driver = open_selenium(
                browser=normalized_action.get('browser', 'chrome'),
                headless=normalized_action.get('headless', False)
            )
            self.browser_active = True
            return

        # Check browser state before each action that requires it
        if action_type in {'url_navigation', 'element_interact'}:
            if not self.ensure_browser_active():
                # Reinitialize browser if needed
                self.driver = open_selenium(
                    browser=normalized_action.get('browser', 'chrome'),
                    headless=normalized_action.get('headless', False)
                )
                self.browser_active = True
                
                # If this was a navigation action, we need to revisit the last URL
                if self.last_url and action_type == 'element_interact':
                    self.driver.get(self.last_url)
                    try:
                        WebDriverWait(self.driver, 30).until(
                            lambda driver: driver.execute_script('return document.readyState') == 'complete'
                        )
                    except Exception as e:
                        logging.warning(f"Page load wait failed: {e}")

            if action_type == 'url_navigation':
                url = normalized_action.get('url')
                self.driver.get(url)
                try:
                    WebDriverWait(self.driver, 30).until(
                        lambda driver: driver.execute_script('return document.readyState') == 'complete'
                    )
                    self.last_url = url
                except Exception as e:
                    logging.warning(f"Page load wait failed: {e}")
                
            elif action_type == 'element_interact':
                try:
                    self.element_interact(
                        selector=normalized_action.get('selector'),
                        by=normalized_action.get('by', 'css'),
                        action=normalized_action.get('action', 'click'),
                        value=normalized_action.get('value', '')
                    )
                except Exception as e:
                    logging.error(f"Element interaction failed: {e}")
                    self.take_debug_screenshot()
                    raise

        # Handle retries with progressive delays
        max_retries = normalized_action.get('retries', 3)
        base_wait_time = normalized_action.get('wait_time', 2)
        retry_action(lambda: None, max_retries=max_retries, wait_time=base_wait_time)

    except Exception as e:
        self._handle_action_error(normalized_action, e)
        if action_type in {'url_navigation', 'element_interact'}:
            self.cleanup_browser()
        raise

def generate_report(action_results, workflow_name):
    """
    Generates a summary report for a workflow execution.

    Args:
        action_results (list): List of results for each action.
        workflow_name (str): Name of the workflow.

    Returns:
        str: Summary report as a string.
    """
    report_lines = [f"Workflow Execution Report: {workflow_name}"]
    report_lines.append("=" * 50)
    for index, result in enumerate(action_results):
        status = "Success" if result["success"] else "Failed"
        report_lines.append(f"Step {index + 1}: {result['action_type']} - {status}")
        if not result["success"]:
            report_lines.append(f"    Error: {result['error']}")

    report_lines.append("=" * 50)
    return "\n".join(report_lines)


def typeSwitch(actions, myWorkflow=None, recipient_email=None):
    """
    Processes a list of actions, executes them, collects results for reporting,
    and sends the report via email if needed.

    Args:
        actions (list): A list of action dictionaries to execute.
        myWorkflow (Workflow, optional): The current workflow state. Defaults to None.
        recipient_email (str, optional): Email address to send the execution report.

    Returns:
        Workflow: The updated workflow state after executing the actions.
    """
    if myWorkflow is None:
        myWorkflow = Workflow()

    action_results = []

    try:
        for action in actions:
            action_type = action.get('type')
            logging.info(f"Executing action: {action_type}")
            
            action_result = {"action_type": action_type, "success": True, "error": None}
            try:
                if action_type == 'open_selenium':
                    myWorkflow.driver = open_selenium(
                        action.get('browser', 'chrome'),
                        action.get('headless', False)
                    )
                
                elif action_type == 'url_navigation':
                    url_navigation(myWorkflow.driver, action.get('url'))
                
                elif action_type == 'wait':
                    wait(action.get('duration', 1))
                
                elif action_type == 'typing_sequence':
                    # Find and click the search box
                    search_box = myWorkflow.driver.find_element(By.XPATH, "//input[@id='search']")
                    search_box.click()
                    search_box.clear()
                    # Type the text
                    for char in action.get('text', ''):
                        search_box.send_keys(char)
                        time.sleep(action.get('typing_speed', 0.1))
                
                elif action_type == 'element_interact':
                    element_interact(
                        myWorkflow.driver,
                        action.get('selector'),
                        getattr(By, action.get('by', 'XPATH').upper()),
                        action.get('action'),
                        action.get('value', '')
                    )
                
                elif action_type == 'close_selenium':
                    close_selenium(myWorkflow.driver)
                    myWorkflow.driver = None
                
                else:
                    logging.warning(f"Unknown action type: {action_type}")
                    
            except Exception as e:
                action_result["success"] = False
                action_result["error"] = str(e)
            action_results.append(action_result)

    except Exception as e:
        logging.error(f"An error occurred while processing actions: {e}")
        if myWorkflow.driver:
            myWorkflow.driver.quit()
            logging.info("Browser closed in error block.")

    # Generate report
    report = generate_report(action_results, "Current Workflow")
    logging.info(report)

    # Send the report via email if recipient_email is provided
    if recipient_email:
        send_execution_report(report, "Current Workflow", recipient_email)
    else:
        logging.info("No recipient email provided. Skipping email notification.")
    return myWorkflow


def send_execution_report(report, workflow_name, recipient_email):
    """
    Sends the workflow execution report via email.

    Args:
        report (str): The workflow execution report.
        workflow_name (str): Name of the workflow.
        recipient_email (str): Recipient's email address.
    """
    try:
        # SMTP server configuration
        smtp_server = "smtp.example.com"  # Replace with your SMTP server
        smtp_port = 587                  # Replace with your SMTP port
        smtp_username = "your_email@example.com"
        smtp_password = "your_password"

        # Create the email
        message = MIMEMultipart()
        message["From"] = smtp_username
        message["To"] = recipient_email
        message["Subject"] = f"Workflow Execution Report: {workflow_name}"

        # Attach the report
        message.attach(MIMEText(report, "plain"))

        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, recipient_email, message.as_string())
        logging.info(f"Execution report sent to {recipient_email}.")
    except Exception as e:
        logging.error(f"Failed to send execution report: {e}")


#mouse_actions
def left_click(x, y):
    """
    Performs a left mouse click at the specified (x, y) coordinates.

    Args:
        x (int): X-coordinate for the click.
        y (int): Y-coordinate for the click.
    """
    logging.info(f"Left-clicking at ({x}, {y})")
    pyautogui.click(x, y, button='left')
    logging.info("Click action completed")

def right_click(x, y):
    """
    Performs a right mouse click at the specified (x, y) coordinates.

    Args:
        x (int): X-coordinate for the click.
        y (int): Y-coordinate for the click.
    """
    logging.info(f"Right-clicking at ({x}, {y})")
    pyautogui.click(x, y, button='right')
    logging.info("Right-click action completed")

def middle_click(x, y):
    """
    Performs a middle mouse click at the specified (x, y) coordinates.

    Args:
        x (int): X-coordinate for the click.
        y (int): Y-coordinate for the click.
    """
    logging.info(f"Middle-clicking at ({x}, {y})")
    pyautogui.click(x, y, button='middle')
    logging.info("Middle-click action completed")

def double_left_click(x, y):
    """
    Performs a double left mouse click at the specified (x, y) coordinates.

    Args:
        x (int): X-coordinate for the click.
        y (int): Y-coordinate for the click.
    """
    logging.info(f"Double left-clicking at ({x}, {y})")
    pyautogui.doubleClick(x, y, button='left')
    logging.info("Double left-click action completed")

def mouse_drag(start_x, start_y, end_x, end_y, duration=0.5):
    """
    Drags the mouse cursor from the specified start coordinates to the end coordinates.

    Args:
        start_x (int): Starting X-coordinate.
        start_y (int): Starting Y-coordinate.
        end_x (int): Ending X-coordinate.
        end_y (int): Ending Y-coordinate.
        duration (float): Time taken to perform the drag in seconds (default is 0.5 seconds).
    """
    logging.info(f"Dragging mouse from ({start_x}, {start_y}) to ({end_x}, {end_y}) over {duration} seconds.")
    pyautogui.moveTo(start_x, start_y)
    pyautogui.dragTo(end_x, end_y, duration=duration)
    logging.info("Mouse drag action completed.")


def mouse_hover(x, y, duration=1.5):
    """
    Moves the mouse cursor to the specified (x, y) coordinates and hovers for the specified duration.

    Args:
        x (int): X-coordinate for the hover.
        y (int): Y-coordinate for the hover.
        duration (float): Time taken to move the mouse in seconds (default is 0.5 seconds).
    """
    logging.info(f"Hovering mouse at ({x}, {y}) over {duration} seconds.")
    pyautogui.moveTo(x, y, duration=duration)
    logging.info("Mouse hover action completed.")


def mouse_scroll(direction, amount):
    """
    Scrolls the mouse wheel up or down by a specified amount.

    Args:
        direction (str): Direction of the scroll ('up' or 'down').
        amount (int): Amount of scroll units.
    """
    logging.info(f"Scrolling {direction} by {amount} units.")
    pyautogui.scroll(amount if direction == 'up' else -amount)
    logging.info("Mouse scroll action completed.")


def mouse_move(x, y, duration=0.5):
    """
    Moves the mouse cursor to the specified (x, y) coordinates.

    Args:
        x (int): X-coordinate for the movement.
        y (int): Y-coordinate for the movement.
        duration (float): Time taken to move the mouse in seconds (default is 0.5 seconds).
    """
    logging.info(f"Moving mouse to ({x}, {y}) over {duration} seconds.")
    pyautogui.moveTo(x, y, duration=duration)
    logging.info("Mouse move action completed.")

def context_menu_open(x, y):
    """
    Opens the context menu at the specified screen coordinates.

    Args:
        x (int): The x-coordinate.
        y (int): The y-coordinate.
    """
    try:
        # Perform a right-click to open the context menu
        right_click(x, y)
        logging.info(f"Context menu opened at ({x}, {y}).")
    except Exception as e:
        logging.error(f"Failed to open context menu at ({x}, {y}): {e}")

def context_menu_select(x, y, option=None):
    """
    Opens the context menu at the specified (x, y) coordinates and selects a specific option.

    Args:
        x (int): X-coordinate for the context menu.
        y (int): Y-coordinate for the context menu.
        option (str or int): The option to select. Can be a number (e.g., 1 for the first option)
                             or a string (e.g., "Rename").
    """
    logging.info(f"Opening context menu at ({x}, {y}) and selecting option '{option}'")

    # Step 1: Open the context menu
    context_menu_open(x, y)
    time.sleep(0.5)  # Small pause to ensure the menu opens

    if isinstance(option, int):
        # Navigate using the keyboard for numbered options
        for _ in range(option):
            pyautogui.press("down")
        pyautogui.press("enter")
    elif isinstance(option, str):
        # Use image recognition to locate the option
        logging.warning("Selecting by text requires OCR or additional libraries.")
        # Placeholder for future enhancement
    else:
        logging.error("Invalid option type. Provide an integer (1-based index) or a string.")

    logging.info("Option selected from the context menu.")

#keyboard_actions
def keystroke(key):
    """
    Simulates pressing a single key.

    Args:
        key (str): The key to press.
    """
    logging.info(f"Pressing key: {key}")
    pyautogui.press(key)
    logging.info(f"Key press '{key}' completed.")


def key_combination(keys):
    """
    Simulates pressing a combination of keys simultaneously.

    Args:
        keys (list): A list of keys to press together (e.g., ['ctrl', 's']).
    """
    logging.info(f"Pressing key combination: {keys}")
    pyautogui.hotkey(*keys)
    logging.info(f"Key combination '{'+'.join(keys)}' completed.")



def typing_sequence(text, typing_speed=0.1):
    """
    Types a sequence of characters with a specified delay between each.
    
    Args:
        text (str): The text to type.
        typing_speed (float): Delay between keystrokes in seconds.
    """
    logging.info(f"Typing sequence: {text}")
    try:
        # Use pyautogui instead of direct driver access
        pyautogui.write(text, interval=typing_speed)
        logging.info("Typing sequence completed successfully")
    except Exception as e:
        logging.error(f"Failed to execute typing sequence: {e}")
        raise


def special_key_press(key):
    """
    Simulates pressing a special key (e.g., 'enter', 'esc').

    Args:
        key (str): The special key to press.
    """
    logging.info(f"Pressing special key: {key}")
    pyautogui.press(key)
    logging.info(f"Special key '{key}' press completed.")


def shortcut_use(shortcut):
    """
    Simulates a shortcut key combination.

    Args:
        shortcut (str): Shortcut as a string (e.g., 'ctrl+s').
    """
    keys = shortcut.split('+')
    logging.info(f"Using shortcut: {shortcut}")
    pyautogui.hotkey(*keys)
    logging.info(f"Shortcut '{shortcut}' executed.")






# File and Folder Actions
def file_open(file_path):
    """
    Opens a file using the default application.

    Args:
        file_path (str): Path to the file to open.
    """
    logging.info(f"Opening file: {file_path}")
    try:
        os.startfile(file_path)
        logging.info(f"File '{file_path}' opened successfully.")
    except Exception as e:
        logging.error(f"Failed to open file '{file_path}': {e}")







def file_save(file_path, content):
    """
    Saves content to a file.

    Args:
        file_path (str): Path to the file.
        content (str): Content to write to the file.
    """
    logging.info(f"Saving content to file: {file_path}")
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        logging.info(f"File '{file_path}' saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save file '{file_path}': {e}")
















def file_delete(file_path):
    """
    Deletes a file.

    Args:
        file_path (str): Path to the file to delete.
    """
    logging.info(f"Deleting file: {file_path}")
    try:
        os.remove(file_path)
        logging.info(f"File '{file_path}' deleted successfully.")
    except Exception as e:
        logging.error(f"Failed to delete file '{file_path}': {e}")



def file_rename(file_path, new_name):
    """
    Renames a file.

    Args:
        file_path (str): Path to the file to rename.
        new_name (str): New name for the file.
    """
    logging.info(f"Renaming file: {file_path} to {new_name}")
    try:
        directory = os.path.dirname(file_path)
        new_path = os.path.join(directory, new_name)
        os.rename(file_path, new_path)
        logging.info(f"File renamed to '{new_path}' successfully.")
    except Exception as e:
        logging.error(f"Failed to rename file '{file_path}': {e}")




















def file_move(source_path, destination_path):
    """
    Moves a file to a new location.

    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    logging.info(f"Moving file from {source_path} to {destination_path}")
    try:
        shutil.move(source_path, destination_path)
        logging.info("File moved successfully.")
    except Exception as e:
        logging.error(f"Failed to move file: {e}")

def file_copy(source_path, destination_path):
    """
    Copies a file to a new location.

    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    logging.info(f"Copying file from {source_path} to {destination_path}")
    try:
        shutil.copy(source_path, destination_path)
        logging.info("File copied successfully.")
    except Exception as e:
        logging.error(f"Failed to copy file: {e}")

def file_upload(file_path):
    """
    Uploads a file by typing its path and pressing Enter.

    Args:
        file_path (str): Path to the file to upload.
    """
    logging.info(f"Uploading file: {file_path}")
    pyautogui.write(file_path)
    pyautogui.press('enter')
    logging.info("File upload completed.")

def file_download(file_url, destination_path):
    """
    Downloads a file from a URL to a specified destination.

    Args:
        file_url (str): URL of the file to download.
        destination_path (str): Path to save the downloaded file.
    """
    logging.info(f"Downloading file from {file_url} to {destination_path}")
    try:
        response = requests.get(file_url, stream=True)
        with open(destination_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info("File downloaded successfully.")
    except Exception as e:
        logging.error(f"Failed to download file: {e}")

# Browser Actions
def detect_default_browser():
    """
    Detects the default system browser.
    
    Returns:
        str: Browser identifier ('chrome', 'firefox', 'ie', or 'edge')
    """
    import winreg
    try:
        # Check Windows registry for default browser
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
            browser_reg = winreg.QueryValueEx(key, "ProgId")[0]
            
        browser_map = {
            'ChromeHTML': 'chrome',
            'FirefoxURL': 'firefox',
            'IE.HTTP': 'ie',
            'MSEdgeHTM': 'edge'
        }
        
        # Extract browser name from registry value
        for key, value in browser_map.items():
            if key.lower() in browser_reg.lower():
                return value
                
        return 'chrome'  # Default to Chrome if detection fails
    except Exception as e:
        logging.warning(f"Failed to detect default browser: {e}. Defaulting to Chrome.")
        return 'chrome'

def open_selenium(browser=None, headless=False):
    """
    Opens a Selenium WebDriver instance using the system's default browser or specified browser.
    
    Args:
        browser (str, optional): Specific browser to use ('chrome', 'firefox', 'ie', 'edge').
                               If None, uses system default.
        headless (bool): Whether to run the browser in headless mode.
        
    Returns:
        WebDriver: Selenium WebDriver instance
    """
    if browser is None:
        browser = detect_default_browser()
        
    logging.info(f"Initializing {browser} browser (headless: {headless})")
    
    try:
        if browser == 'chrome':
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-gpu')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Chrome driver: {e}")
                raise
                
        elif browser == 'firefox':
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            
            try:
                driver = webdriver.Firefox(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Firefox driver: {e}")
                raise
                
        elif browser == 'ie':
            options = webdriver.IeOptions()
            options.ignore_protected_mode_settings = True
            options.ignore_zoom_level = True
            options.require_window_focus = False
            
            try:
                driver = webdriver.Ie(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize IE driver: {e}")
                raise
                
        elif browser == 'edge':
            options = webdriver.EdgeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--start-maximized')
            
            try:
                driver = webdriver.Edge(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Edge driver: {e}")
                raise
                
        else:
            raise ValueError(f"Unsupported browser type: {browser}")
        
        # Set common configurations
        driver.set_page_load_timeout(30)
        if not headless:
            driver.maximize_window()
            
        logging.info(f"Successfully initialized {browser} browser")
        return driver
        
    except Exception as e:
        error_msg = f"Failed to initialize browser {browser}: {str(e)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

def close_selenium(driver):
    """
    Closes the Selenium WebDriver instance.

    Args:
        driver (WebDriver): Selenium WebDriver instance to close.
    """
    logging.info("Closing Selenium browser.")
    try:
        driver.quit()
        logging.info("Browser closed successfully.")
    except Exception as e:
        logging.error(f"Failed to close browser: {e}")

def url_navigation(driver, url):
    """
    Navigates the browser to the specified URL.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        url (str): URL to navigate to.
    """
    logging.info(f"Navigating to URL: {url}")
    try:
        driver.get(url)
        logging.info(f"Navigation to {url} completed successfully.")
    except Exception as e:
        logging.error(f"Failed to navigate to {url}: {e}")




def element_interact(driver, selector, by='xpath', action='click', value=''):
    """
    Unified element interaction function.
    """
    logging.info(f"Interacting with element: {selector} ({action})")
    try:
        by = getattr(By, by.upper())
        wait = WebDriverWait(driver, 20)
        
        # Element location logic
        element = wait.until(EC.presence_of_element_located((by, selector)))
        
        # Scroll and wait
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        
        # Action execution
        if action == 'click':
            try:
                element.click()
            except Exception:
                driver.execute_script("arguments[0].click();", element)
        elif action == 'input':
            element.clear()
            for char in value:
                element.send_keys(char)
                time.sleep(0.1)
        
        return True
    except Exception as e:
        logging.error(f"Element interaction failed: {str(e)}")
        take_error_screenshot(driver, "element_interaction")
        raise


def search_query(driver, search_box_selector, query, by=By.CSS_SELECTOR):
    """
    Performs a search query by typing in a search box and submitting.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        search_box_selector (str): Selector for the search box element.
        query (str): Search query to perform.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Performing search query: '{query}' in element: {search_box_selector} (by {by}")
    try:
        search_box = driver.find_element(by, search_box_selector)
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        logging.info("Search query executed successfully.")
    except Exception as e:
        logging.error(f"Failed to perform search query '{query}': {e}")

#new from GPT?? SELENIUM CONTINUED
def dynamic_interact(driver, actions, wait_time=5):
    """
    Executes a sequence of dynamic actions on the browser.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        actions (list of dict): List of actions with selectors and commands.
        wait_time (int): Wait time in seconds between actions.
    """
    logging.info("Executing dynamic interactions.")
    try:
        for action in actions:
            action_type = action.get("action_type")
            selector = action.get("selector")
            by = action.get("by", By.CSS_SELECTOR)

            if action_type == "click":
                logging.info(f"Clicking element: {selector}")
                driver.find_element(by, selector).click()
            elif action_type == "input":
                value = action.get("value", "")
                logging.info(f"Inputting '{value}' into element: {selector}")
                element = driver.find_element(by, selector)
                element.clear()
                element.send_keys(value)
            else:  # Fixed indentation
                logging.warning(f"Unsupported action type: {action_type}")

            time.sleep(wait_time)
        logging.info("Dynamic interactions completed successfully.")
    except Exception as e:
        logging.error(f"Failed during dynamic interactions: {e}")
def scroll_to_element(driver, selector, by=By.CSS_SELECTOR):
    """
    Scrolls the browser window until the specified element is in view.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the element to scroll to.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Scrolling to element: {selector} (by {by})")
    try:
        element = driver.find_element(by, selector)
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)
        logging.info(f"Scrolled to element: {selector}")
    except Exception as e:
        logging.error(f"Failed to scroll to element {selector}: {e}")

def select_dropdown_option(driver, selector, option_text, by=By.CSS_SELECTOR):
    """
    Selects an option from a dropdown by visible text.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the dropdown element.
        option_text (str): The visible text of the option to select.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Selecting '{option_text}' from dropdown: {selector} (by {by}")
    try:
        #from selenium.webdriver.support.ui import Select
        dropdown = Select(driver.find_element(by, selector))
        dropdown.select_by_visible_text(option_text)
        logging.info(f"Option '{option_text}' selected successfully.")
    except Exception as e:
        logging.error(f"Failed to select option '{option_text}' from dropdown {selector}: {e}")

def switch_to_iframe(driver, selector, by=By.CSS_SELECTOR):
    """
    Switches the context to an iframe.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the iframe element.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Switching to iframe: {selector} (by {by})")
    try:
        iframe = driver.find_element(by, selector)
        driver.switch_to.frame(iframe)
        logging.info("Switched to iframe successfully.")
    except Exception as e:
        logging.error(f"Failed to switch to iframe {selector}: {e}")

def switch_to_default_content(driver):
    """
    Switches the context back to the main document from an iframe.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Switching to default content.")
    try:
        driver.switch_to.default_content()
        logging.info("Switched to default content successfully.")
    except Exception as e:
        logging.error(f"Failed to switch to default content: {e}")


def retry_action(action_func, max_retries=3, wait_time=2):
    """
    Retries an action with exponential backoff and proper error handling.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return action_func()
        except Exception as e:
            last_error = e
            if attempt == max_retries - 1:
                logging.error(f"Action failed after {max_retries} attempts: {str(e)}")
                raise last_error
            
            wait_duration = wait_time * (2 ** attempt)  # Exponential backoff
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_duration} seconds...")
            time.sleep(wait_duration)
            
            # If this is a browser-related error, we should force cleanup
            if isinstance(e, (selenium.common.exceptions.NoSuchWindowException, 
                selenium.common.exceptions.WebDriverException)):
                logging.info("Browser session lost. Will reinitialize on next attempt.")


def wait_for_element(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    """
    Waits for an element to be present on the page.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the element.
        by (str): Selenium By strategy (e.g., CSS_SELECTOR, XPATH).
        timeout (int): Maximum wait time in seconds.

    Returns:
        WebElement: The located element.

    Raises:
        TimeoutException: If the element is not found within the timeout.
    """
    logging.info(f"Waiting for element: {selector} (by {by}) for up to {timeout} seconds.")
    try:
        element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
        logging.info(f"Element located: {selector}")
        return element
    except Exception as e:
        logging.error(f"Failed to locate element {selector} within {timeout} seconds: {e}")
        raise


def restart_driver(driver, browser='chrome', headless=False):
    """
    Restarts the Selenium WebDriver in case of failure.

    Args:
        driver (WebDriver): The current driver instance to close and restart.
        browser (str): Browser type ('chrome' or 'firefox').
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        WebDriver: A new driver instance.
    """
    logging.info("Restarting WebDriver due to failure.")
    try:
        close_selenium(driver)
    except Exception as e:
        logging.warning(f"Failed to gracefully close driver: {e}")

    return open_selenium(browser, headless)


# Communication and Actions
def email_read(platform='outlook', criteria=None):
    logging.info(f"Reading emails on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []

def email_write(platform='outlook', to=None, subject=None, body=None, cc=None, bcc=None):
    """
    Composes an email draft dynamically for Outlook or Gmail.

    Args:
        platform (str): Email platform ('outlook' or 'gmail').
        to (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.
    """
    try:
        if platform == 'gmail':
            email_write_gmail(to, subject, body, cc, bcc)
        elif platform == 'outlook':
            email_write_draft(to, subject, body, cc, bcc)
        else:
            logging.error(f"Unsupported platform: {platform}")
    except Exception as e:
        logging.error(f"Error composing email draft: {e}")



def email_send(to_address, subject, body, smtp_server=None, smtp_port=None, smtp_username=None, smtp_password=None, platform='outlook'):
    logging.info(f"Sending email to {to_address} via {platform}")
    try:
        if platform == 'outlook':
            send_email_outlook(to_address, subject, body)
        elif platform == 'gmail':
            if smtp_server and smtp_port and smtp_username and smtp_password:
                email_send_gmail(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password)
            else:
                raise ValueError("Gmail requires SMTP server, port, username, and password.")
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def scan_inbox(criteria, platform='outlook'):
    logging.info(f"Scanning inbox on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to scan inbox: {e}")
        return []

def email_search(criteria, platform='outlook'):
    logging.info(f"Searching emails on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to search emails: {e}")
        return []

#OUTLOOK IMPLEMENTATION
def email_read_outlook(criteria=None):
    logging.info(f"Reading emails with criteria: {criteria}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # Inbox
        messages = inbox.Items
        emails = []
        for message in messages:
            if criteria:
                if "subject" in criteria and criteria["subject"].lower() not in message.Subject.lower():
                    continue
                if "sender" in criteria and criteria["sender"].lower() not in message.SenderEmailAddress.lower():
                    continue
            emails.append({
                "subject": message.Subject,
                "body": message.Body,
                "sender": message.SenderName,
                "received_time": message.ReceivedTime
            })
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []

def email_write_draft(to, subject, body, cc=None, bcc=None):
    logging.info(f"Composing email draft to {to}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = to
        mail.Subject = subject
        mail.Body = body
        if cc:
            mail.CC = cc
        if bcc:
            mail.BCC = bcc
        mail.Display()
        logging.info("Draft created successfully.")
    except Exception as e:
        logging.error(f"Failed to compose email: {e}")



def send_email_outlook(to_address, subject, body):
    """
    Sends an email using Microsoft Outlook via COM.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
    """
    try:
        # Create an Outlook application instance
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0: Mail item

        # Set email properties
        mail.To = to_address
        mail.Subject = subject
        mail.Body = body

        # Send the email
        mail.Send()
        logging.info(f"Email sent successfully to {to_address} via Outlook.")
    except Exception as e:
        logging.error(f"Failed to send email via Outlook: {e}")



def scan_inbox_outlook(criteria):
    logging.info(f"Scanning inbox with criteria: {criteria}")
    return email_read_outlook(criteria)

#GMAIL IMPLEMENTATION

def email_read_gmail(criteria=None):
    """
    Reads emails from Gmail using the Gmail API.
    
    Args:
        criteria (dict, optional): Search criteria for filtering emails
        
    Returns:
        list: List of matching emails
    """
    logging.info(f"Reading emails from Gmail with criteria: {criteria}")
    try:
        creds = Credentials.from_authorized_user_file('token.json', 
            ['https://www.googleapis.com/auth/gmail.readonly'])
        service = build('gmail', 'v1', credentials=creds)
        query = ""
        if criteria:
            if "subject" in criteria:
                query += f"subject:{criteria['subject']} "
            if "sender" in criteria:
                query += f"from:{criteria['sender']} "
        
        results = service.users().messages().list(userId='me', q=query).execute()
        emails = []
        
        for msg in results.get('messages', []):
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            emails.append({
                "subject": next((h['value'] for h in headers if h['name'] == 'Subject'), ''),
                "snippet": msg_data.get('snippet', '')
            })
            
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
        
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []


def email_read_gmail_imap(username, password, criteria=None):
    logging.info(f"Reading emails via IMAP with criteria: {criteria}")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")
        search_query = "ALL"
        if criteria:
            if "subject" in criteria:
                search_query = f'SUBJECT "{criteria["subject"]}"'
            if "sender" in criteria:
                search_query = f'FROM "{criteria["sender"]}"'
        _, data = mail.search(None, search_query)
        emails = []
        for eid in data[0].split():
            _, msg_data = mail.fetch(eid, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    emails.append({
                        "subject": msg["subject"],
                        "sender": msg["from"],
                        "body": msg.get_payload(decode=True).decode()
                    })
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
    except Exception as e:
        logging.error(f"Failed to read emails via IMAP: {e}")
        return []


def create_gmail_message(to, subject, body, cc=None, bcc=None):
    """
    Creates a Gmail API-compatible message in base64 format.

    Args:
        to (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.

    Returns:
        dict: A dictionary containing the 'raw' message ready for Gmail API.
    """
    try:
        # Create the MIMEText email object
        message = MIMEText(body)
        message['To'] = to
        message['Subject'] = subject
        if cc:
            message['Cc'] = cc
        if bcc:
            message['Bcc'] = bcc

        # Encode the message in base64
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw}
    except Exception as e:
        logging.error(f"Failed to create Gmail message: {e}")
        raise


def email_write_gmail(to, subject, body, cc=None, bcc=None):
    """
    Composes and drafts an email in Gmail using the Gmail API.

    Args:
        to (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.
    """
    try:
        # Load credentials from token.json
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.compose'])
        service = build('gmail', 'v1', credentials=creds)

        # Create the email message
        message = create_gmail_message(to, subject, body, cc, bcc)

        # Create a draft in Gmail
        draft = service.users().drafts().create(userId='me', body=message).execute()
        logging.info(f"Draft created successfully with ID: {draft['id']}")
    except Exception as e:
        logging.error(f"Failed to compose Gmail draft: {e}")

def email_send_gmail(to_address, subject, body, smtp_server=None, smtp_port=None, smtp_username=None, smtp_password=None):
    """
    Sends an email using Gmail API.
    """
    logging.info(f"Sending email to {to_address} via Gmail API")
    try:
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.send'])
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(body)
        message['to'] = to_address
        message['subject'] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


#ADVANCED EMAIL CAPABILITIES

def email_send_with_attachments(to_address, subject, body, attachments, smtp_server, smtp_port, smtp_username, smtp_password):
    """
    Sends an email with multiple attachments using SMTP.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
        attachments (list): List of file paths to attach.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
    """
    logging.info(f"Sending email to {to_address} with {len(attachments)} attachments")
    try:
        message = MIMEMultipart()
        message["From"] = smtp_username
        message["To"] = to_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        for file_path in attachments:
            try:
                with open(file_path, "rb") as file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={file_path}")
                    message.attach(part)
            except FileNotFoundError:
                logging.error(f"Attachment not found: {file_path}")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_address, message.as_string())
        logging.info("Email with attachments sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email with attachments: {e}")

def read_attachments_outlook(criteria=None, download_folder="downloads"):
    """
    Reads emails and downloads attachments based on criteria.

    Args:
        criteria (dict, optional): Search criteria like sender or subject.
        download_folder (str): Folder to save downloaded attachments.
    """
    logging.info(f"Reading emails and downloading attachments to {download_folder}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # Inbox
        messages = inbox.Items
        for message in messages:
            if criteria:
                if "subject" in criteria and criteria["subject"].lower() not in message.Subject.lower():
                    continue
                if "sender" in criteria and criteria["sender"].lower() not in message.SenderEmailAddress.lower():
                    continue

            for attachment in message.Attachments:
                file_path = os.path.join(download_folder, str(attachment))
                attachment.SaveAsFile(file_path)
                logging.info(f"Downloaded attachment: {file_path}")
    except Exception as e:
        logging.error(f"Failed to download attachments: {e}")

def email_search_advanced(platform='outlook', criteria=None):
    """
    Searches emails with advanced criteria such as date range and keywords.

    Args:
        platform (str): Email platform ('outlook' or 'gmail').
        criteria (dict): Search criteria (e.g., subject, sender, date_range).

    Returns:
        list: List of matching emails.
    """
    logging.info(f"Performing advanced search on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)  # Add advanced filtering logic in email_read_outlook
        elif platform == 'gmail':
            return email_read_gmail(criteria)  # Update Gmail search logic to handle date ranges
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Advanced search failed: {e}")
        return []

def retry_email_send(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password, retries=3):
    """
    Retries sending an email if it fails.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        retries (int): Number of retry attempts.
    """
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Attempt {attempt} to send email to {to_address}")
            email_send_with_attachments(to_address, subject, body, [], smtp_server, smtp_port, smtp_username, smtp_password)
            logging.info("Email sent successfully.")
            break
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed: {e}")
            if attempt == retries:
                logging.error("All attempts to send email failed.")



def schedule_email(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password, delay):
    """
    Schedules an email to be sent after a delay.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        delay (int): Delay in seconds before sending the email.
    """
    logging.info(f"Scheduling email to {to_address} in {delay} seconds.")
    Timer(delay, email_send_with_attachments, args=(to_address, subject, body, [], smtp_server, smtp_port, smtp_username, smtp_password)).start()


# Interaction with Media


def media_play(file_path=None):
    """
    Plays media from a local file or resumes browser-based media.

    Args:
        file_path (str, optional): Path to the local media file. If None, resumes browser media.
    """
    if file_path:
        logging.info(f"Playing local media file: {file_path}")
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.call(('open' if os.name == 'darwin' else 'xdg-open', file_path))
            logging.info("Media playback started successfully.")
        except Exception as e:
            logging.error(f"Failed to play media: {e}")
    else:
        logging.info("Playing browser-based media.")
        pyautogui.press("playpause")  # Play/Pause media in browser or system


def media_pause():
    """
    Pauses browser-based media or system-level media.
    """
    logging.info("Pausing media...")
    try:
        pyautogui.press("playpause")  # Universal pause button
        logging.info("Media paused successfully.")
    except Exception as e:
        logging.error(f"Failed to pause media: {e}")






def media_seek(position):
    """
    Seeks media to a specific position in seconds.

    Args:
        position (int): Position in seconds to seek to.
    """
    logging.info(f"Seeking to position {position} seconds...")
    try:
        pyautogui.press("k")  # YouTube shortcut for pausing
        pyautogui.typewrite(str(position))  # Type the position
        pyautogui.press("enter")  # Confirm position change
        logging.info(f"Media seeked to {position} seconds.")
    except Exception as e:
        logging.error(f"Failed to seek media position: {e}")


def media_volume_change(volume):
    """
    Changes the system volume to a specified level.

    Args:
        volume (int): Volume level (0-100).
    """
    logging.info(f"Changing volume to {volume}...")
    try:
        if 0 <= volume <= 100:
            for _ in range(50):  # Reset to zero volume
                pyautogui.press("volumedown")
            for _ in range(volume // 2):  # Increase to the desired level (each press ~2%)
                pyautogui.press("volumeup")
            logging.info(f"Volume set to {volume}.")
        else:
            logging.error("Volume level must be between 0 and 100.")
    except Exception as e:
        logging.error(f"Failed to change volume: {e}")

#additional media control BROWSER and MUTE
def media_mute():
    """
    Toggles mute for the system or browser-based media.
    """
    logging.info("Toggling mute...")
    try:
        pyautogui.press("volumemute")
        logging.info("Mute toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle mute: {e}")

def browser_media_play_pause(driver):
    """
    Toggles play/pause for browser-based media (e.g., YouTube, Netflix).

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling play/pause for browser media...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("arguments[0].pause()" if video_element.is_playing else "arguments[0].play()", video_element)
        logging.info("Media play/pause toggled in browser.")
    except Exception as e:
        logging.error(f"Failed to control browser media: {e}")

def media_next_track():
    """
    Skips to the next media track for browser-based or system-level playback.
    """
    logging.info("Skipping to the next track...")
    try:
        pyautogui.press("nexttrack")  # Universal system shortcut
        logging.info("Skipped to the next track.")
    except Exception as e:
        logging.error(f"Failed to skip to the next track: {e}")

def media_previous_track():
    """
    Goes back to the previous media track for browser-based or system-level playback.
    """
    logging.info("Going back to the previous track...")
    try:
        pyautogui.press("prevtrack")  # Universal system shortcut
        logging.info("Went back to the previous track.")
    except Exception as e:
        logging.error(f"Failed to go back to the previous track: {e}")

def toggle_subtitles_browser(driver):
    """
    Toggles subtitles for media in a browser-based platform.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling subtitles in browser...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const player = document.querySelector('video');
            if (player.textTracks.length > 0) {
                const track = player.textTracks[0];
                track.mode = track.mode === 'showing' ? 'disabled' : 'showing';
            }
        """)
        logging.info("Subtitles toggled successfully in browser.")
    except Exception as e:
        logging.error(f"Failed to toggle subtitles: {e}")

def adjust_playback_speed(driver, speed):
    """
    Adjusts playback speed for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        speed (float): Desired playback speed (e.g., 1.5 for 1.5x speed).
    """
    logging.info(f"Setting playback speed to {speed}x...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script(f"arguments[0].playbackRate = {speed};", video_element)
        logging.info(f"Playback speed set to {speed}x.")
    except Exception as e:
        logging.error(f"Failed to adjust playback speed: {e}")

def toggle_media_loop(driver):
    """
    Toggles looping for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling media loop...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("arguments[0].loop = !arguments[0].loop;", video_element)
        logging.info("Media loop toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle media loop: {e}")

def toggle_fullscreen(driver):
    """
    Toggles fullscreen mode for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling fullscreen mode...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const player = arguments[0];
            if (!document.fullscreenElement) {
                player.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        """, video_element)
        logging.info("Fullscreen mode toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle fullscreen mode: {e}")


def media_volume_fade(volume, fade_time=5):
    """
    Fades volume in or out over a specified duration.

    Args:
        volume (int): Target volume level (0-100).
        fade_time (int): Duration of fade in seconds.
    """
    logging.info(f"Fading volume to {volume} over {fade_time} seconds...")
    try:
        current_volume = 0  # Assuming starting at 0
        step = volume // (fade_time * 2)  # Adjust step size based on fade time

        for level in range(0, volume + 1, step):
            media_volume_change(level)
            time.sleep(0.5)  # Smooth transition
        logging.info(f"Volume faded to {volume}.")
    except Exception as e:
        logging.error(f"Failed to fade volume: {e}")

def media_restart():
    """
    Restarts media playback from the beginning.
    """
    logging.info("Restarting media playback...")
    try:
        pyautogui.press("0")  # YouTube shortcut to go to the beginning
        logging.info("Media playback restarted.")
    except Exception as e:
        logging.error(f"Failed to restart media playback: {e}")


#Monitor Support & Multi-Monitor Setup Info (For media but reuseable)

def get_monitor_info():
    """
    Retrieves information about all connected monitors.

    Returns:
        list: A list of dictionaries with monitor details (width, height, x, y).
    """
    monitors = []
    for monitor in get_monitors():
        monitors.append({
            "width": monitor.width,
            "height": monitor.height,
            "x": monitor.x,
            "y": monitor.y
        })
    logging.info(f"Detected monitors: {monitors}")
    return monitors



def move_window_to_monitor(window_title, monitor_index):
    """
    Moves a window to a specified monitor.

    Args:
        window_title (str): Title of the window to move.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Moving '{window_title}' to monitor {monitor_index}")
    try:
        monitors = get_monitor_info()
        if monitor_index >= len(monitors):
            logging.error(f"Monitor index {monitor_index} is out of range.")
            return

        target_monitor = monitors[monitor_index]
        windows = gw.getWindowsWithTitle(window_title)

        if windows:
            window = windows[0]
            window.moveTo(target_monitor['x'], target_monitor['y'])
            logging.info(f"Window '{window_title}' moved to monitor {monitor_index}.")
        else:
            logging.error(f"Window '{window_title}' not found.")
    except Exception as e:
        logging.error(f"Failed to move window: {e}")

def fullscreen_on_monitor(window_title, monitor_index):
    """
    Toggles fullscreen for a window on a specific monitor.

    Args:
        window_title (str): Title of the window to fullscreen.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Toggling fullscreen for '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        pyautogui.hotkey("alt", "enter")  # Simulates fullscreen shortcut
        logging.info(f"Fullscreen toggled for '{window_title}' on monitor {monitor_index}.")
    except Exception as e:
        logging.error(f"Failed to toggle fullscreen: {e}")

def maximize_window_on_monitor(window_title, monitor_index):
    """
    Maximizes a window on a specific monitor.

    Args:
        window_title (str): Title of the window to maximize.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Maximizing '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        windows = gw.getWindowsWithTitle(window_title)
        if windows:
            window = windows[0]
            window.maximize()
            logging.info(f"Window '{window_title}' maximized on monitor {monitor_index}.")
        else:
            logging.error(f"Window '{window_title}' not found.")
    except Exception as e:
        logging.error(f"Failed to maximize window: {e}")

def control_media_on_monitor(window_title, monitor_index, action):
    """
    Controls media playback on a specific monitor.

    Args:
        window_title (str): Title of the media window.
        monitor_index (int): Index of the target monitor.
        action (str): Media control action ('play', 'pause', 'next', 'prev').
    """
    logging.info(f"Performing '{action}' on '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        if action == "play":
            pyautogui.press("playpause")
        elif action == "pause":
            pyautogui.press("playpause")
        elif action == "next":
            pyautogui.press("nexttrack")
        elif action == "prev":
            pyautogui.press("prevtrack")
        else:
            logging.error(f"Unsupported action: {action}")
        logging.info(f"Action '{action}' completed on '{window_title}' on monitor {monitor_index}.")
    except Exception as e:
        logging.error(f"Failed to perform action: {e}")






# Security and Authentication Actions

# Load encryption key (generate and save this once; reuse for decryption)
def load_encryption_key():
    """
    Loads the encryption key from a file.
    Returns:
        str: Encryption key.
    """
    try:
        with open("encryption.key", "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        logging.error("Encryption key file not found. Generate it using Fernet.")
        raise

def decrypt_password(encrypted_password):
    """
    Decrypts an encrypted password.

    Args:
        encrypted_password (str): Encrypted password in bytes.

    Returns:
        str: Decrypted password.
    """
    try:
        key = load_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode()).decode()
        logging.info("Password decrypted successfully.")
        return decrypted
    except Exception as e:
        logging.error(f"Failed to decrypt password: {e}")
        raise


def load_credentials(name):
    """
    Loads credentials from a JSON file based on the provided name.

    Args:
        name (str): The name of the credential to retrieve.

    Returns:
        dict: A dictionary containing 'username' and 'password'.

    Raises:
        KeyError: If the credential is not found in the file.
    """
    try:
        with open("credentials.json", "r") as file:
            all_credentials = json.load(file)

        if name not in all_credentials:
            raise KeyError(f"Credential '{name}' not found in credentials.json.")

        return all_credentials[name]
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in credentials.json.")
    except FileNotFoundError:
        raise FileNotFoundError("credentials.json file not found.")


def login_attempt(name):
    """
    Attempts to log in using stored credentials.

    Args:
        name (str): Name of the credential in the JSON file.
    """
    logging.info(f"Attempting login for credential: {name}")
    try:
        # Load the credentials by name
        credentials = load_credentials(name)

        username = credentials["username"]
        password = credentials["password"]

        # Placeholder for login logic
        logging.info(f"Logging in with username: {username}")
        # Implement your actual login logic here
    except KeyError as ke:
        logging.error(f"Missing key in credentials for '{name}': {ke}")
    except FileNotFoundError:
        logging.error("credentials.json file not found.")
    except Exception as e:
        logging.error(f"Login attempt failed for '{name}': {e}")





def logout():
    """
    Logs the user out.
    """
    logging.info("Logging out...")
    try:
        # Example: Send logout request to an API or invalidate session
        logging.info("Logout successful.")
    except Exception as e:
        logging.error(f"Logout failed: {e}")


def permission_request(permission):
    """
    Requests a specific system or application permission.

    Args:
        permission (str): Name of the permission to request.
    """
    logging.info(f"Requesting permission: {permission}")
    try:
        # Replace with actual permission logic
        logging.info(f"Permission '{permission}' granted.")
    except Exception as e:
        logging.error(f"Permission request failed: {e}")


def run_as_administrator(command):
    """
    Runs a command as Administrator.

    Args:
        command (str): The command to execute.
    """
    logging.info(f"Running command as Administrator: {command}")
    try:
        subprocess.run(["runas", "/user:Administrator", command], check=True)
        logging.info("Command executed successfully as Administrator.")
    except Exception as e:
        logging.error(f"Failed to execute command as Administrator: {e}")



def generate_otp(secret_key):
    """
    Generates a One-Time Password (OTP) using a secret key.

    Args:
        secret_key (str): Secret key for OTP generation.

    Returns:
        str: OTP.
    """
    totp = pyotp.TOTP(secret_key)
    otp = totp.now()
    logging.info(f"Generated OTP: {otp}")
    return otp

def verify_otp(secret_key, otp):
    """
    Verifies a One-Time Password (OTP) against a secret key.

    Args:
        secret_key (str): Secret key for OTP generation.
        otp (str): OTP to verify.

    Returns:
        bool: True if OTP is valid, False otherwise.
    """
    totp = pyotp.TOTP(secret_key)
    is_valid = totp.verify(otp)
    logging.info(f"OTP verification result: {is_valid}")
    return is_valid


logging.basicConfig(
    filename="security.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)



# Specialized Actions
def dropdown_select(driver=None, selector=None, value=None, by=By.CSS_SELECTOR, is_local=False, window_title=None):
    """
    Selects a value in a dropdown (web-based or local application).

    Args:
        driver (WebDriver, optional): Selenium WebDriver instance for web dropdowns.
        selector (str, optional): Selector for the web dropdown element.
        value (str or int): Value to select (visible text or index).
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        is_local (bool): Whether the dropdown is in a local application.
        window_title (str, optional): Title of the local application window.
    """
    try:
        if is_local and window_title:
            logging.info(f"Selecting '{value}' in dropdown in local application: {window_title}")
            #import pygetwindow as gw
            #import pywinauto
            #from pywinauto.application import Application
            # Locate window and dropdown control
            app = Application(backend="uia").connect(title=window_title)
            window = app.window(title=window_title)
            dropdown = window.child_window(title=selector, control_type="ComboBox")

            # Select dropdown value
            dropdown.select(value)
            logging.info(f"Successfully selected '{value}' in dropdown: {selector} (local).")

        elif driver and selector and value:
            logging.info(f"Selecting '{value}' in web dropdown: {selector}")
            element = driver.find_element(by, selector)
            dropdown = Select(element)

            if isinstance(value, int):
                dropdown.select_by_index(value)
            else:
                dropdown.select_by_visible_text(value)

            logging.info(f"Successfully selected '{value}' in web dropdown: {selector}.")
        else:
            raise ValueError("Invalid arguments. Provide either a web driver and selector or local application details.")
    except Exception as e:
        logging.error(f"Failed to select '{value}' in dropdown: {e}")

def checkbox_toggle(driver, selector, value, by=By.CSS_SELECTOR, max_retries=3):
    """
    Toggles a checkbox on or off with retries.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the checkbox element.
        value (bool): Desired state of the checkbox (True for checked, False for unchecked).
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        max_retries (int): Number of retry attempts.
    """
    def toggle_checkbox():
        checkbox = driver.find_element(by, selector)
        if checkbox.is_selected() != value:
            checkbox.click()

    retry_action(toggle_checkbox, max_retries=max_retries)


def slider_adjustment(driver, selector, value, by=By.CSS_SELECTOR):
    """
    Adjusts a slider to a specific value.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the slider element.
        value (int): Target value for the slider.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
    """
    logging.info(f"Adjusting slider {selector} to value {value}")
    try:
        slider = driver.find_element(by, selector)
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", slider, value)
        logging.info(f"Slider {selector} adjusted to {value}")
    except Exception as e:
        logging.error(f"Failed to adjust slider {selector}: {e}")


def calendar_interaction(driver, selector, date, by=By.CSS_SELECTOR, max_retries=3):
    """
    Interacts with a calendar to set a specific date with retries.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the calendar element.
        date (str): Date to set in the format 'YYYY-MM-DD'.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        max_retries (int): Number of retry attempts.
    """
    def set_date():
        calendar = driver.find_element(by, selector)
        calendar.clear()
        calendar.send_keys(date)

    retry_action(set_date, max_retries=max_retries)


def loop(actions, iterations, driver):
    """
    Loops through a series of actions with error recovery.

    Args:
        actions (list of callables): List of actions to execute.
        iterations (int): Number of times to repeat the loop.
        driver (WebDriver): Selenium WebDriver instance.
    """
    for i in range(iterations):
        logging.info(f"Executing loop iteration {i + 1}")
        for action in actions:
            try:
                action(driver)
            except Exception as e:
                logging.error(f"Error during loop iteration {i + 1}, action {action.__name__}: {e}")
                continue


def wait(duration):
    """
    Waits for a specified duration.

    Args:
        duration (int): Time to wait in seconds.
    """
    logging.info(f"Waiting for {duration} seconds...")
    try:
        time.sleep(duration)
        logging.info("Wait completed.")
    except Exception as e:
        logging.error(f"Error during wait: {e}")






def wait_for(driver, condition, selector, timeout=30, by=By.CSS_SELECTOR):
    """
    Waits for a specific condition to be met with logging.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        condition (callable): Condition to wait for (e.g., element_to_be_clickable).
        selector (str): Selector for the target element.
        timeout (int): Maximum wait time in seconds.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
    """
    logging.info(f"Waiting for condition '{condition.__name__}' on {selector}")
    try:
        WebDriverWait(driver, timeout).until(condition((by, selector)))
        logging.info(f"Condition '{condition.__name__}' met for {selector}")
    except Exception as e:
        logging.error(f"Condition '{condition.__name__}' not met for {selector} within {timeout} seconds: {e}")
        raise



#ERROR HANDLING & REALTIME ERORR HANDLING



def send_error_notification(error_message):
    """
    Sends an email notification with the error details.

    Args:
        error_message (str): The error message to include in the email.
    """
    try:
        smtp_server = "smtp.example.com"
        smtp_port = 587
        smtp_username = "your_email@example.com"
        smtp_password = "your_password"
        recipient_email = "admin@example.com"

        message = MIMEText(f"An error occurred:\n\n{error_message}")
        message["Subject"] = "Critical Error Notification"
        message["From"] = smtp_username
        message["To"] = recipient_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        logging.info("Error notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")

def retry_action_with_error_reporting(action, max_retries=3, wait_time=2, *args, **kwargs):
    """
    Retries an action if it fails and logs detailed error information.

    Args:
        action (callable): The function to execute.
        max_retries (int): Number of retry attempts.
        wait_time (int): Delay between retries in seconds.
        *args: Positional arguments for the action.
        **kwargs: Keyword arguments for the action.

    Returns:
        Any: The return value of the action if successful.
    """
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries} for action '{action.__name__}'")
            result = action(*args, **kwargs)
            logging.info(f"Action '{action.__name__}' succeeded on attempt {attempt + 1}")
            return result
        except Exception as e:
            error_message = f"Attempt {attempt + 1} failed for action '{action.__name__}': {e}"
            logging.error(error_message)
            if attempt == max_retries - 1:
                send_error_notification(error_message)
            time.sleep(wait_time)
    raise Exception(f"Action '{action.__name__}' failed after {max_retries} attempts.")

def loop_with_error_reporting(actions, iterations, driver):
    """
    Executes actions in a loop and generates a detailed error report.

    Args:
        actions (list of callables): List of actions to execute.
        iterations (int): Number of times to repeat the loop.
        driver (WebDriver): Selenium WebDriver instance.
    """
    error_summary = []

    for i in range(iterations):
        logging.info(f"Executing loop iteration {i + 1}")
        for action in actions:
            try:
                action(driver)
            except Exception as e:
                error_message = f"Error in loop iteration {i + 1}, action '{action.__name__}': {e}"
                logging.error(error_message)
                error_summary.append(error_message)

    # Log error summary
    if error_summary:
        logging.error("Error Summary:\n" + "\n".join(error_summary))
        send_error_notification("\n".join(error_summary))

def write_error_summary_to_file(error_summary, filename="error_summary.txt"):
    """
    Writes the error summary to a file.

    Args:
        error_summary (list): List of error messages.
        filename (str): Name of the file to write the summary to.
    """
    logging.info(f"Writing error summary to file: {filename}")
    try:
        with open(filename, "w") as file:
            file.write("Error Summary:\n")
            file.write("\n".join(error_summary))
        logging.info(f"Error summary written to {filename}.")
    except Exception as e:
        logging.error(f"Failed to write error summary to file: {e}")


class WorkflowExecutor:
    def __init__(self):
        self.driver = None
        self.app = None
        self.variables = {}
        self.status = "initialized"
        self.cipher = None
        self.browser_active = False
        self.last_url = None

    def execute_action(self, action):
        """
        Executes a normalized action with proper error handling and retries.
        """
        try:
            normalized_action = normalize_action(action)
            action_type = normalized_action['type']
            logging.info(f"Executing action: {action_type}")

            # Initialize browser if needed
            if action_type == 'open_selenium':
                self.cleanup_browser()
                self.driver = open_selenium(
                    browser=normalized_action.get('browser', 'chrome'),
                    headless=normalized_action.get('headless', False)
                )
                self.browser_active = True
                return

            # Check browser state before each action that requires it
            if action_type in {'url_navigation', 'element_interact'}:
                if not self.ensure_browser_active():
                    # Reinitialize browser if needed
                    self.driver = open_selenium(
                        browser=normalized_action.get('browser', 'chrome'),
                        headless=normalized_action.get('headless', False)
                    )
                    self.browser_active = True
                    
                    # If this was a navigation action, we need to revisit the last URL
                    if self.last_url and action_type == 'element_interact':
                        self.driver.get(self.last_url)
                        try:
                            WebDriverWait(self.driver, 30).until(
                                lambda driver: driver.execute_script('return document.readyState') == 'complete'
                            )
                        except Exception as e:
                            logging.warning(f"Page load wait failed: {e}")

                if action_type == 'url_navigation':
                    url = normalized_action.get('url')
                    self.driver.get(url)
                    try:
                        WebDriverWait(self.driver, 30).until(
                            lambda driver: driver.execute_script('return document.readyState') == 'complete'
                        )
                        self.last_url = url
                    except Exception as e:
                        logging.warning(f"Page load wait failed: {e}")
                    
                elif action_type == 'element_interact':
                    try:
                        self.element_interact(
                            selector=normalized_action.get('selector'),
                            by=normalized_action.get('by', 'css'),
                            action=normalized_action.get('action', 'click'),
                            value=normalized_action.get('value', '')
                        )
                    except Exception as e:
                        logging.error(f"Element interaction failed: {e}")
                        self.take_debug_screenshot()
                        raise

            # Don't cleanup browser after each action anymore
            # Only cleanup on explicit close or error

        except Exception as e:
            self._handle_action_error(normalized_action, e)
            if isinstance(e, (selenium.common.exceptions.NoSuchWindowException, 
                            selenium.common.exceptions.WebDriverException)):
                self.cleanup_browser()
            raise

    def ensure_browser_active(self):
        """
        Ensures browser is active and reinitializes if needed.
        Returns True if browser is active, False if it needs to be reinitialized.
        """
        if not self.driver:
            logging.info("No browser session exists")
            return False
        
        try:
            # More robust check for browser state
            self.driver.current_window_handle  # This will throw an exception if browser is closed
            return True
        except Exception as e:
            logging.warning(f"Browser check failed: {e}. Reinitializing...")
            self.cleanup_browser()
            return False

    def cleanup_browser(self):
        """Safely cleanup browser resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.warning(f"Error during browser cleanup: {e}")
            finally:
                self.driver = None
                self.browser_active = False
                self.last_url = None

    def element_interact(self, selector, by='css', action='click', value=''):
        """Interacts with a web element with smart selector fallback."""
        if not self.ensure_browser_active():
            raise ValueError("Browser not initialized or not active")
        
        logging.info(f"Interacting with element: {selector} ({action})")
        try:
            # Progressive selector strategy
            selectors_to_try = [
                # Try ID first (most specific)
                (By.ID, selector if not selector.startswith('#') else selector[1:]),
                # Then CSS selector
                (By.CSS_SELECTOR, selector),
                # Then class name
                (By.CLASS_NAME, selector if not selector.startswith('.') else selector[1:]),
                # Then name attribute
                (By.NAME, selector),
                # Finally, try XPath as fallback
                (By.XPATH, f"//*[@id='{selector}']"),  # ID as XPath
                (By.XPATH, f"//*[contains(@class, '{selector}')]"),  # Class as XPath
                (By.XPATH, f"//*[@name='{selector}']"),  # Name as XPath
                (By.XPATH, selector if selector.startswith('//') else f"//*[contains(text(), '{selector}')]")  # Text content or custom XPath
            ]

            wait = WebDriverWait(self.driver, 20)
            element = None
            last_error = None

            for by_type, sel in selectors_to_try:
                try:
                    element = wait.until(lambda d: (
                        d.find_element(by_type, sel) and
                        d.find_element(by_type, sel).is_displayed() and
                        d.find_element(by_type, sel).is_enabled()
                    ) and d.find_element(by_type, sel))
                    logging.info(f"Element found using {by_type}: {sel}")
                    break
                except Exception as e:
                    last_error = e
                    continue

            if not element:
                raise last_error or Exception("Element not found with any selector strategy")

            # Scroll element into view
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.scrollIntoView({block: 'center', behavior: 'instant'});
            """, element)
            
            time.sleep(0.5)

            if action == 'click':
                try:
                    element.click()
                except:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                    except:
                        ActionChains(self.driver).move_to_element(element).click().perform()
            elif action == 'input':
                for _ in range(3):
                    try:
                        element.clear()
                        element.send_keys(Keys.CONTROL + "a")
                        element.send_keys(Keys.DELETE)
                        for char in value:
                            element.send_keys(char)
                            time.sleep(0.1)
                        
                        if element.get_attribute('value') == value:
                            break
                    except Exception as e:
                        logging.warning(f"Input attempt failed: {e}, retrying...")
                        time.sleep(1)

            return True

        except Exception as e:
            logging.error(f"Element interaction failed: {str(e)}")
            self.take_debug_screenshot()
            raise

    def take_debug_screenshot(self):
        """Takes a debug screenshot if possible."""
        if self.driver:
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshots/debug_{timestamp}.png"
                os.makedirs("error_screenshots", exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Debug screenshot saved: {screenshot_path}")
            except Exception as e:
                logging.error(f"Failed to save debug screenshot: {e}")

    def cleanup(self):
        """Cleanup all resources."""
        self.cleanup_browser()
        if self.app:
            try:
                self.app = None
            except Exception as e:
                logging.error(f"Error cleaning up application: {e}")
        logging.info("Workflow cleanup completed successfully")

    def _init_cipher(self):
        """Initialize the cipher for encryption/decryption."""
        try:
            with open('secret.key', 'rb') as key_file:
                key = key_file.read()
            self.cipher = Fernet(key)
        except Exception as e:
            logging.error(f"Failed to initialize cipher: {e}")
            raise

    def _decrypt_password(self, encrypted_password):
        """
        Decrypt password using the initialized cipher.
        """
        try:
            if not self.cipher:
                self._init_cipher()
            return self.cipher.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logging.error(f"Error decrypting password: {e}")
            raise

    def _load_encryption_key(self):
        """
        Load encryption key from file.
        """
        try:
            with open('secret.key', 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading encryption key: {e}")
            raise

    def open_selenium(self, browser=None, headless=False):
        """Opens a Selenium WebDriver instance using system default or specified browser."""
        logging.info(f"Opening browser (headless: {headless})")
        try:
            self.driver = open_selenium(browser, headless)
            logging.info("Browser opened successfully")
            return self.driver
        except Exception as e:
            logging.error(f"Failed to open browser: {str(e)}")
            raise

    def close_selenium(self):
        """Closes the Selenium WebDriver instance."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("Browser closed successfully")
            except Exception as e:
                logging.error(f"Failed to close browser: {e}")
            finally:
                self.driver = None

    def url_navigation(self, url):
        """Navigates to a URL."""
        logging.info(f"Navigating to: {url}")
        try:
            self.driver.get(url)
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            logging.info(f"Navigation successful: {url}")
        except Exception as e:
            logging.error(f"Navigation failed: {e}")
            raise

    def _get_credentials(self, credential_name):
        """
        Get credentials from credentials.json file.
        """
        try:
            with open('credentials.json', 'r') as f:
                credentials_list = json.load(f)
                for cred in credentials_list:
                    if cred['name'].lower() == credential_name.lower():
                        return cred
            return None
        except Exception as e:
            logging.error(f"Error loading credentials: {e}")
            return None

    def _handle_action_error(self, action, error):
        """
        Handles errors that occur during action execution.
        """
        logging.error(f"Error executing action: {action.get('type')}")
        logging.error(f"Error details: {str(error)}")
        if self.driver:
            try:
                # Take screenshot on error
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshots/error_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Error screenshot saved: {screenshot_path}")
            except Exception as screenshot_error:
                logging.error(f"Failed to save error screenshot: {screenshot_error}")

    def __del__(self):
        """
        Destructor to ensure resources are freed even if cleanup wasn't called.
        """
        try:
            if self.driver:
                self.close_selenium()
        except:
            pass  # Suppress errors in destructor

    def wait_for_page_load(self, timeout=30):
        """Waits for page load to complete with multiple conditions."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: driver.execute_script('''
                return document.readyState === "complete" && 
                       !document.querySelector(".loading") &&
                       (typeof jQuery === "undefined" || jQuery.active === 0) &&
                       (!window.angular || !angular.element(document).injector() || 
                        !angular.element(document).injector().get('$http').pendingRequests.length)
            '''))
            time.sleep(1)  # Additional small wait for any final rendering
        except Exception as e:
            logging.error(f"Page load wait timeout: {e}")
            self.take_debug_screenshot()
            raise

    def handle_desktop_application(self, action):
        """Enhanced desktop application handling with retries and checks."""
        try:
            app_path = action.get('application_path')
            arguments = action.get('arguments', '')
            working_dir = action.get('working_dir')
            
            # Ensure any existing instance is closed
            try:
                app = Application().connect(path=app_path)
                app.kill()
                time.sleep(1)
            except:
                pass  # No existing instance
            
            # Launch application with retry
            for attempt in range(3):
                try:
                    if working_dir:
                        process = subprocess.Popen(
                            [app_path] + shlex.split(arguments),
                            cwd=working_dir,
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    else:
                        process = subprocess.Popen(
                            [app_path] + shlex.split(arguments),
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    
                    # Wait for window to appear
                    start_time = time.time()
                    while time.time() - start_time < 30:
                        try:
                            app = Application().connect(process=process.pid)
                            window = app.top_window()
                            window.wait('ready', timeout=10)
                            logging.info(f"Application launched successfully: {app_path}")
                            return app
                        except Exception:
                            time.sleep(1)
                    
                    raise TimeoutError("Application window did not appear")
                    
                except Exception as e:
                    logging.warning(f"Launch attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            logging.error(f"Failed to launch application {app_path}: {e}")
            raise

    def desktop_input(self, window, control_id, text, retries=3):
        """More reliable desktop input with retries."""
        for attempt in range(retries):
            try:
                # Find control and ensure it's ready
                control = window[control_id]
                control.wait('ready', timeout=10)
                
                # Clear existing text
                control.set_text('')
                time.sleep(0.5)
                
                # Type text with delay
                for char in text:
                    control.type_keys(char, pause=0.1)
                
                # Verify input
                actual_text = control.get_value()
                if actual_text == text:
                    return True
                    
                logging.warning(f"Input verification failed. Expected: {text}, Got: {actual_text}")
                
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Desktop input failed after {retries} attempts: {e}")
                    raise
                time.sleep(1)
                
        return False

    def desktop_click(self, window, control_id, retries=3):
        """More reliable desktop clicking with retries."""
        for attempt in range(retries):
            try:
                control = window[control_id]
                control.wait('ready', timeout=10)
                control.click_input()
                time.sleep(0.5)  # Wait for click to register
                return True
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Desktop click failed after {retries} attempts: {e}")
                    raise
                time.sleep(1)

# Function to execute a workflow
def execute_workflow(workflow_data):
    """
    Main entry point for workflow execution.
    
    Args:
        workflow_data (dict): The workflow to execute
    """
    executor = WorkflowExecutor()
    try:
        executor.execute_workflow(workflow_data)
    except Exception as e:
        logging.error(f"Workflow execution failed: {str(e)}")
        raise


# Action Type Mappings
ACTION_TYPE_MAPPINGS = {
    # Browser Actions
    'open_browser': 'open_selenium',
    'launch_browser': 'open_selenium',
    'start_browser': 'open_selenium',
    
    'close_browser': 'close_selenium',
    'quit_browser': 'close_selenium',
    'exit_browser': 'close_selenium',
    
    'navigate': 'url_navigation',
    'go_to': 'url_navigation',
    'go_to_url': 'url_navigation',
    'browse_to': 'url_navigation',
    
    'type': 'typing_sequence',
    'input': 'typing_sequence',
    'input_text': 'typing_sequence',
    'enter_text': 'typing_sequence',
    
    'click': 'element_interact',
    'click_element': 'element_interact',
    'click_button': 'element_interact',
    
    # Mouse Actions
    'mouse_click': 'left_click',
    'click_at': 'left_click',
    
    'right_click_at': 'right_click',
    'context_click': 'right_click',
    
    'double_click': 'double_left_click',
    'dbl_click': 'double_left_click',
    
    'drag': 'mouse_drag',
    'drag_and_drop': 'mouse_drag',
    
    'hover': 'mouse_hover',
    'mouse_over': 'mouse_hover',
    
    'scroll': 'mouse_scroll',
    'scroll_page': 'mouse_scroll',
    
    'move_mouse': 'mouse_move',
    'move_cursor': 'mouse_move',
    
    # Keyboard Actions
    'press_key': 'keystroke',
    'key_press': 'keystroke',
    
    'press_keys': 'key_combination',
    'key_combo': 'key_combination',
    
    'type_text': 'typing_sequence',
    'send_keys': 'typing_sequence',
    
    'special_key': 'special_key_press',
    'system_key': 'special_key_press',
    
    'shortcut': 'shortcut_use',
    'keyboard_shortcut': 'shortcut_use',
    
    # File Operations
    'open_file': 'file_open',
    'load_file': 'file_open',
    
    'save_file': 'file_save',
    'write_file': 'file_save',
    
    'delete_file': 'file_delete',
    'remove_file': 'file_delete',
    
    'rename_file': 'file_rename',
    'move_file': 'file_move',
    'copy_file': 'file_copy',
    'upload': 'file_upload',
    'download': 'file_download',
    
    # Wait Actions
    'sleep': 'wait',
    'pause': 'wait',
    'delay': 'wait',
    
    'wait_until': 'wait_for',
    'wait_for_element': 'wait_for',
    
    # Email Actions
    'read_email': 'email_read',
    'check_email': 'email_read',
    
    'write_email': 'email_write',
    'compose_email': 'email_write',
    
    'send_email': 'email_send',
    'email': 'email_send',
    
    # Application Actions
    'open_app': 'open_application',
    'launch_app': 'open_application',
    'start_app': 'open_application',
    'run_app': 'open_application'
}  # Remove the extra closing brace

def normalize_action(action):
    """
    Normalizes action type and parameters for consistent handling.
    """
    if not isinstance(action, dict):
        raise ValueError("Action must be a dictionary")
        
    # Make a copy to avoid modifying the original
    normalized = action.copy()
    
    # Normalize action type
    action_type = normalized.get('type', '').lower()
    normalized['type'] = ACTION_TYPE_MAPPINGS.get(action_type, action_type)
    
    return normalized

def wait(duration):
    """
    Waits for a specified duration.

    Args:
        duration (int): Time to wait in seconds.
    """
    logging.info(f"Waiting for {duration} seconds...")
    try:
        time.sleep(duration)
        logging.info("Wait completed.")
    except Exception as e:
        logging.error(f"Error during wait: {e}")

def take_error_screenshot(driver, error_type="error"):
    """
    Takes a screenshot when an error occurs.
    
    Args:
        driver: WebDriver instance
        error_type (str): Type of error for filename
    
    Returns:
        str: Path to screenshot or None if failed
    """
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_path = f"error_screenshots/{error_type}_{timestamp}.png"
        os.makedirs("error_screenshots", exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logging.info(f"Error screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"Failed to save error screenshot: {e}")
        return None

def email_write_gmail(to, subject, body, cc=None, bcc=None):
    """
    Composes and drafts an email in Gmail using the Gmail API.

    Args:
        to (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.
    """
    try:
        # Load credentials from token.json
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.compose'])
        service = build('gmail', 'v1', credentials=creds)

        # Create the email message
        message = create_gmail_message(to, subject, body, cc, bcc)

        # Create a draft in Gmail
        draft = service.users().drafts().create(userId='me', body=message).execute()
        logging.info(f"Draft created successfully with ID: {draft['id']}")
    except Exception as e:
        logging.error(f"Failed to compose Gmail draft: {e}")

def email_send_gmail(to_address, subject, body, smtp_server=None, smtp_port=None, smtp_username=None, smtp_password=None):
    """
    Sends an email using Gmail API.
    """
    logging.info(f"Sending email to {to_address} via Gmail API")
    try:
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.send'])
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(body)
        message['to'] = to_address
        message['subject'] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")




















def file_move(source_path, destination_path):
    """
    Moves a file to a new location.

    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    logging.info(f"Moving file from {source_path} to {destination_path}")
    try:
        shutil.move(source_path, destination_path)
        logging.info("File moved successfully.")
    except Exception as e:
        logging.error(f"Failed to move file: {e}")

def file_copy(source_path, destination_path):
    """
    Copies a file to a new location.

    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    logging.info(f"Copying file from {source_path} to {destination_path}")
    try:
        shutil.copy(source_path, destination_path)
        logging.info("File copied successfully.")
    except Exception as e:
        logging.error(f"Failed to copy file: {e}")

def file_upload(file_path):
    """
    Uploads a file by typing its path and pressing Enter.

    Args:
        file_path (str): Path to the file to upload.
    """
    logging.info(f"Uploading file: {file_path}")
    pyautogui.write(file_path)
    pyautogui.press('enter')
    logging.info("File upload completed.")

def file_download(file_url, destination_path):
    """
    Downloads a file from a URL to a specified destination.

    Args:
        file_url (str): URL of the file to download.
        destination_path (str): Path to save the downloaded file.
    """
    logging.info(f"Downloading file from {file_url} to {destination_path}")
    try:
        response = requests.get(file_url, stream=True)
        with open(destination_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info("File downloaded successfully.")
    except Exception as e:
        logging.error(f"Failed to download file: {e}")

# Browser Actions
def detect_default_browser():
    """
    Detects the default system browser.
    
    Returns:
        str: Browser identifier ('chrome', 'firefox', 'ie', or 'edge')
    """
    import winreg
    try:
        # Check Windows registry for default browser
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
            browser_reg = winreg.QueryValueEx(key, "ProgId")[0]
            
        browser_map = {
            'ChromeHTML': 'chrome',
            'FirefoxURL': 'firefox',
            'IE.HTTP': 'ie',
            'MSEdgeHTM': 'edge'
        }
        
        # Extract browser name from registry value
        for key, value in browser_map.items():
            if key.lower() in browser_reg.lower():
                return value
                
        return 'chrome'  # Default to Chrome if detection fails
    except Exception as e:
        logging.warning(f"Failed to detect default browser: {e}. Defaulting to Chrome.")
        return 'chrome'

def open_selenium(browser=None, headless=False):
    """
    Opens a Selenium WebDriver instance using the system's default browser or specified browser.
    
    Args:
        browser (str, optional): Specific browser to use ('chrome', 'firefox', 'ie', 'edge').
                               If None, uses system default.
        headless (bool): Whether to run the browser in headless mode.
        
    Returns:
        WebDriver: Selenium WebDriver instance
    """
    if browser is None:
        browser = detect_default_browser()
        
    logging.info(f"Initializing {browser} browser (headless: {headless})")
    
    try:
        if browser == 'chrome':
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-gpu')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Chrome driver: {e}")
                raise
                
        elif browser == 'firefox':
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            
            try:
                driver = webdriver.Firefox(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Firefox driver: {e}")
                raise
                
        elif browser == 'ie':
            options = webdriver.IeOptions()
            options.ignore_protected_mode_settings = True
            options.ignore_zoom_level = True
            options.require_window_focus = False
            
            try:
                driver = webdriver.Ie(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize IE driver: {e}")
                raise
                
        elif browser == 'edge':
            options = webdriver.EdgeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--start-maximized')
            
            try:
                driver = webdriver.Edge(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Edge driver: {e}")
                raise
                
        else:
            raise ValueError(f"Unsupported browser type: {browser}")
        
        # Set common configurations
        driver.set_page_load_timeout(30)
        if not headless:
            driver.maximize_window()
            
        logging.info(f"Successfully initialized {browser} browser")
        return driver
        
    except Exception as e:
        error_msg = f"Failed to initialize browser {browser}: {str(e)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

def close_selenium(driver):
    """
    Closes the Selenium WebDriver instance.

    Args:
        driver (WebDriver): Selenium WebDriver instance to close.
    """
    logging.info("Closing Selenium browser.")
    try:
        driver.quit()
        logging.info("Browser closed successfully.")
    except Exception as e:
        logging.error(f"Failed to close browser: {e}")

def url_navigation(driver, url):
    """
    Navigates the browser to the specified URL.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        url (str): URL to navigate to.
    """
    logging.info(f"Navigating to URL: {url}")
    try:
        driver.get(url)
        logging.info(f"Navigation to {url} completed successfully.")
    except Exception as e:
        logging.error(f"Failed to navigate to {url}: {e}")




def element_interact(driver, selector, by='xpath', action='click', value=''):
    """
    Unified element interaction function.
    """
    logging.info(f"Interacting with element: {selector} ({action})")
    try:
        by = getattr(By, by.upper())
        wait = WebDriverWait(driver, 20)
        
        # Element location logic
        element = wait.until(EC.presence_of_element_located((by, selector)))
        
        # Scroll and wait
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        
        # Action execution
        if action == 'click':
            try:
                element.click()
            except Exception:
                driver.execute_script("arguments[0].click();", element)
        elif action == 'input':
            element.clear()
            for char in value:
                element.send_keys(char)
                time.sleep(0.1)
        
        return True
    except Exception as e:
        logging.error(f"Element interaction failed: {str(e)}")
        take_error_screenshot(driver, "element_interaction")
        raise


def search_query(driver, search_box_selector, query, by=By.CSS_SELECTOR):
    """
    Performs a search query by typing in a search box and submitting.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        search_box_selector (str): Selector for the search box element.
        query (str): Search query to perform.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Performing search query: '{query}' in element: {search_box_selector} (by {by}")
    try:
        search_box = driver.find_element(by, search_box_selector)
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        logging.info("Search query executed successfully.")
    except Exception as e:
        logging.error(f"Failed to perform search query '{query}': {e}")

#new from GPT?? SELENIUM CONTINUED
def dynamic_interact(driver, actions, wait_time=5):
    """
    Executes a sequence of dynamic actions on the browser.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        actions (list of dict): List of actions with selectors and commands.
        wait_time (int): Wait time in seconds between actions.
    """
    logging.info("Executing dynamic interactions.")
    try:
        for action in actions:
            action_type = action.get("action_type")
            selector = action.get("selector")
            by = action.get("by", By.CSS_SELECTOR)

            if action_type == "click":
                logging.info(f"Clicking element: {selector}")
                driver.find_element(by, selector).click()
            elif action_type == "input":
                value = action.get("value", "")
                logging.info(f"Inputting '{value}' into element: {selector}")
                element = driver.find_element(by, selector)
                element.clear()
                element.send_keys(value)
            else:  # Fixed indentation
                logging.warning(f"Unsupported action type: {action_type}")

            time.sleep(wait_time)
        logging.info("Dynamic interactions completed successfully.")
    except Exception as e:
        logging.error(f"Failed during dynamic interactions: {e}")
def scroll_to_element(driver, selector, by=By.CSS_SELECTOR):
    """
    Scrolls the browser window until the specified element is in view.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the element to scroll to.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Scrolling to element: {selector} (by {by})")
    try:
        element = driver.find_element(by, selector)
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)
        logging.info(f"Scrolled to element: {selector}")
    except Exception as e:
        logging.error(f"Failed to scroll to element {selector}: {e}")

def select_dropdown_option(driver, selector, option_text, by=By.CSS_SELECTOR):
    """
    Selects an option from a dropdown by visible text.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the dropdown element.
        option_text (str): The visible text of the option to select.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Selecting '{option_text}' from dropdown: {selector} (by {by}")
    try:
        #from selenium.webdriver.support.ui import Select
        dropdown = Select(driver.find_element(by, selector))
        dropdown.select_by_visible_text(option_text)
        logging.info(f"Option '{option_text}' selected successfully.")
    except Exception as e:
        logging.error(f"Failed to select option '{option_text}' from dropdown {selector}: {e}")

def switch_to_iframe(driver, selector, by=By.CSS_SELECTOR):
    """
    Switches the context to an iframe.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the iframe element.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Switching to iframe: {selector} (by {by})")
    try:
        iframe = driver.find_element(by, selector)
        driver.switch_to.frame(iframe)
        logging.info("Switched to iframe successfully.")
    except Exception as e:
        logging.error(f"Failed to switch to iframe {selector}: {e}")

def switch_to_default_content(driver):
    """
    Switches the context back to the main document from an iframe.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Switching to default content.")
    try:
        driver.switch_to.default_content()
        logging.info("Switched to default content successfully.")
    except Exception as e:
        logging.error(f"Failed to switch to default content: {e}")


def retry_action(action_func, max_retries=3, wait_time=2):
    """
    Retries an action with exponential backoff and proper error handling.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return action_func()
        except Exception as e:
            last_error = e
            if attempt == max_retries - 1:
                logging.error(f"Action failed after {max_retries} attempts: {str(e)}")
                raise last_error
            
            wait_duration = wait_time * (2 ** attempt)  # Exponential backoff
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_duration} seconds...")
            time.sleep(wait_duration)
            
            # If this is a browser-related error, we should force cleanup
            if isinstance(e, (selenium.common.exceptions.NoSuchWindowException, 
                selenium.common.exceptions.WebDriverException)):
                logging.info("Browser session lost. Will reinitialize on next attempt.")


def wait_for_element(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    """
    Waits for an element to be present on the page.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the element.
        by (str): Selenium By strategy (e.g., CSS_SELECTOR, XPATH).
        timeout (int): Maximum wait time in seconds.

    Returns:
        WebElement: The located element.

    Raises:
        TimeoutException: If the element is not found within the timeout.
    """
    logging.info(f"Waiting for element: {selector} (by {by}) for up to {timeout} seconds.")
    try:
        element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
        logging.info(f"Element located: {selector}")
        return element
    except Exception as e:
        logging.error(f"Failed to locate element {selector} within {timeout} seconds: {e}")
        raise


def restart_driver(driver, browser='chrome', headless=False):
    """
    Restarts the Selenium WebDriver in case of failure.

    Args:
        driver (WebDriver): The current driver instance to close and restart.
        browser (str): Browser type ('chrome' or 'firefox').
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        WebDriver: A new driver instance.
    """
    logging.info("Restarting WebDriver due to failure.")
    try:
        close_selenium(driver)
    except Exception as e:
        logging.warning(f"Failed to gracefully close driver: {e}")

    return open_selenium(browser, headless)


# Communication and Actions
def email_read(platform='outlook', criteria=None):
    logging.info(f"Reading emails on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []

def email_write(platform='outlook', to=None, subject=None, body=None, cc=None, bcc=None):
    """
    Composes an email draft dynamically for Outlook or Gmail.

    Args:
        platform (str): Email platform ('outlook' or 'gmail').
        to (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.
    """
    try:
        if platform == 'gmail':
            email_write_gmail(to, subject, body, cc, bcc)
        elif platform == 'outlook':
            email_write_draft(to, subject, body, cc, bcc)
        else:
            logging.error(f"Unsupported platform: {platform}")
    except Exception as e:
        logging.error(f"Error composing email draft: {e}")



def email_send(to_address, subject, body, smtp_server=None, smtp_port=None, smtp_username=None, smtp_password=None, platform='outlook'):
    logging.info(f"Sending email to {to_address} via {platform}")
    try:
        if platform == 'outlook':
            send_email_outlook(to_address, subject, body)
        elif platform == 'gmail':
            if smtp_server and smtp_port and smtp_username and smtp_password:
                email_send_gmail(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password)
            else:
                raise ValueError("Gmail requires SMTP server, port, username, and password.")
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def scan_inbox(criteria, platform='outlook'):
    logging.info(f"Scanning inbox on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to scan inbox: {e}")
        return []

def email_search(criteria, platform='outlook'):
    logging.info(f"Searching emails on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to search emails: {e}")
        return []

#OUTLOOK IMPLEMENTATION
def email_read_outlook(criteria=None):
    logging.info(f"Reading emails with criteria: {criteria}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # Inbox
        messages = inbox.Items
        emails = []
        for message in messages:
            if criteria:
                if "subject" in criteria and criteria["subject"].lower() not in message.Subject.lower():
                    continue
                if "sender" in criteria and criteria["sender"].lower() not in message.SenderEmailAddress.lower():
                    continue
            emails.append({
                "subject": message.Subject,
                "body": message.Body,
                "sender": message.SenderName,
                "received_time": message.ReceivedTime
            })
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []

def email_write_draft(to, subject, body, cc=None, bcc=None):
    logging.info(f"Composing email draft to {to}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = to
        mail.Subject = subject
        mail.Body = body
        if cc:
            mail.CC = cc
        if bcc:
            mail.BCC = bcc
        mail.Display()
        logging.info("Draft created successfully.")
    except Exception as e:
        logging.error(f"Failed to compose email: {e}")



def send_email_outlook(to_address, subject, body):
    """
    Sends an email using Microsoft Outlook via COM.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
    """
    try:
        # Create an Outlook application instance
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0: Mail item

        # Set email properties
        mail.To = to_address
        mail.Subject = subject
        mail.Body = body

        # Send the email
        mail.Send()
        logging.info(f"Email sent successfully to {to_address} via Outlook.")
    except Exception as e:
        logging.error(f"Failed to send email via Outlook: {e}")



def scan_inbox_outlook(criteria):
    logging.info(f"Scanning inbox with criteria: {criteria}")
    return email_read_outlook(criteria)

#GMAIL IMPLEMENTATION

def email_read_gmail(criteria=None):
    """
    Reads emails from Gmail using the Gmail API.
    
    Args:
        criteria (dict, optional): Search criteria for filtering emails
        
    Returns:
        list: List of matching emails
    """
    logging.info(f"Reading emails from Gmail with criteria: {criteria}")
    try:
        creds = Credentials.from_authorized_user_file('token.json', 
            ['https://www.googleapis.com/auth/gmail.readonly'])
        service = build('gmail', 'v1', credentials=creds)
        query = ""
        if criteria:
            if "subject" in criteria:
                query += f"subject:{criteria['subject']} "
            if "sender" in criteria:
                query += f"from:{criteria['sender']} "
        
        results = service.users().messages().list(userId='me', q=query).execute()
        emails = []
        
        for msg in results.get('messages', []):
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            emails.append({
                "subject": next((h['value'] for h in headers if h['name'] == 'Subject'), ''),
                "snippet": msg_data.get('snippet', '')
            })
            
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
        
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []


def email_read_gmail_imap(username, password, criteria=None):
    logging.info(f"Reading emails via IMAP with criteria: {criteria}")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")
        search_query = "ALL"
        if criteria:
            if "subject" in criteria:
                search_query = f'SUBJECT "{criteria["subject"]}"'
            if "sender" in criteria:
                search_query = f'FROM "{criteria["sender"]}"'
        _, data = mail.search(None, search_query)
        emails = []
        for eid in data[0].split():
            _, msg_data = mail.fetch(eid, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    emails.append({
                        "subject": msg["subject"],
                        "sender": msg["from"],
                        "body": msg.get_payload(decode=True).decode()
                    })
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
    except Exception as e:
        logging.error(f"Failed to read emails via IMAP: {e}")
        return []


def create_gmail_message(to, subject, body, cc=None, bcc=None):
    """
    Creates a Gmail API-compatible message in base64 format.

    Args:
        to (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.

    Returns:
        dict: A dictionary containing the 'raw' message ready for Gmail API.
    """
    try:
        # Create the MIMEText email object
        message = MIMEText(body)
        message['To'] = to
        message['Subject'] = subject
        if cc:
            message['Cc'] = cc
        if bcc:
            message['Bcc'] = bcc

        # Encode the message in base64
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw}
    except Exception as e:
        logging.error(f"Failed to create Gmail message: {e}")
        raise


def email_send_with_attachments(to_address, subject, body, attachments, smtp_server, smtp_port, smtp_username, smtp_password):
    """
    Sends an email with multiple attachments using SMTP.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
        attachments (list): List of file paths to attach.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
    """
    logging.info(f"Sending email to {to_address} with {len(attachments)} attachments")
    try:
        message = MIMEMultipart()
        message["From"] = smtp_username
        message["To"] = to_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        for file_path in attachments:
            try:
                with open(file_path, "rb") as file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={file_path}")
                    message.attach(part)
            except FileNotFoundError:
                logging.error(f"Attachment not found: {file_path}")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_address, message.as_string())
        logging.info("Email with attachments sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email with attachments: {e}")

def read_attachments_outlook(criteria=None, download_folder="downloads"):
    """
    Reads emails and downloads attachments based on criteria.

    Args:
        criteria (dict, optional): Search criteria like sender or subject.
        download_folder (str): Folder to save downloaded attachments.
    """
    logging.info(f"Reading emails and downloading attachments to {download_folder}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # Inbox
        messages = inbox.Items
        for message in messages:
            if criteria:
                if "subject" in criteria and criteria["subject"].lower() not in message.Subject.lower():
                    continue
                if "sender" in criteria and criteria["sender"].lower() not in message.SenderEmailAddress.lower():
                    continue

            for attachment in message.Attachments:
                file_path = os.path.join(download_folder, str(attachment))
                attachment.SaveAsFile(file_path)
                logging.info(f"Downloaded attachment: {file_path}")
    except Exception as e:
        logging.error(f"Failed to download attachments: {e}")

def email_search_advanced(platform='outlook', criteria=None):
    """
    Searches emails with advanced criteria such as date range and keywords.

    Args:
        platform (str): Email platform ('outlook' or 'gmail').
        criteria (dict): Search criteria (e.g., subject, sender, date_range).

    Returns:
        list: List of matching emails.
    """
    logging.info(f"Performing advanced search on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)  # Add advanced filtering logic in email_read_outlook
        elif platform == 'gmail':
            return email_read_gmail(criteria)  # Update Gmail search logic to handle date ranges
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Advanced search failed: {e}")
        return []

def retry_email_send(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password, retries=3):
    """
    Retries sending an email if it fails.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        retries (int): Number of retry attempts.
    """
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Attempt {attempt} to send email to {to_address}")
            email_send_with_attachments(to_address, subject, body, [], smtp_server, smtp_port, smtp_username, smtp_password)
            logging.info("Email sent successfully.")
            break
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed: {e}")
            if attempt == retries:
                logging.error("All attempts to send email failed.")



def schedule_email(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password, delay):
    """
    Schedules an email to be sent after a delay.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        delay (int): Delay in seconds before sending the email.
    """
    logging.info(f"Scheduling email to {to_address} in {delay} seconds.")
    Timer(delay, email_send_with_attachments, args=(to_address, subject, body, [], smtp_server, smtp_port, smtp_username, smtp_password)).start()


# Interaction with Media


def media_play(file_path=None):
    """
    Plays media from a local file or resumes browser-based media.

    Args:
        file_path (str, optional): Path to the local media file. If None, resumes browser media.
    """
    if file_path:
        logging.info(f"Playing local media file: {file_path}")
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.call(('open' if os.name == 'darwin' else 'xdg-open', file_path))
            logging.info("Media playback started successfully.")
        except Exception as e:
            logging.error(f"Failed to play media: {e}")
    else:
        logging.info("Playing browser-based media.")
        pyautogui.press("playpause")  # Play/Pause media in browser or system


def media_pause():
    """
    Pauses browser-based media or system-level media.
    """
    logging.info("Pausing media...")
    try:
        pyautogui.press("playpause")  # Universal pause button
        logging.info("Media paused successfully.")
    except Exception as e:
        logging.error(f"Failed to pause media: {e}")





def media_seek(position):
    """
    Seeks media to a specific position in seconds.

    Args:
        position (int): Position in seconds to seek to.
    """
    logging.info(f"Seeking to position {position} seconds...")
    try:
        pyautogui.press("k")  # YouTube shortcut for pausing
        pyautogui.typewrite(str(position))  # Type the position
        pyautogui.press("enter")  # Confirm position change
        logging.info(f"Media seeked to {position} seconds.")
    except Exception as e:
        logging.error(f"Failed to seek media position: {e}")


def media_volume_change(volume):
    """
    Changes the system volume to a specified level.

    Args:
        volume (int): Volume level (0-100).
    """
    logging.info(f"Changing volume to {volume}...")
    try:
        if 0 <= volume <= 100:
            for _ in range(50):  # Reset to zero volume
                pyautogui.press("volumedown")
            for _ in range(volume // 2):  # Increase to the desired level (each press ~2%)
                pyautogui.press("volumeup")
            logging.info(f"Volume set to {volume}.")
        else:
            logging.error("Volume level must be between 0 and 100.")
    except Exception as e:
        logging.error(f"Failed to change volume: {e}")

#additional media control BROWSER and MUTE
def media_mute():
    """
    Toggles mute for the system or browser-based media.
    """
    logging.info("Toggling mute...")
    try:
        pyautogui.press("volumemute")
        logging.info("Mute toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle mute: {e}")

def browser_media_play_pause(driver):
    """
    Toggles play/pause for browser-based media (e.g., YouTube, Netflix).

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling play/pause for browser media...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("arguments[0].pause()" if video_element.is_playing else "arguments[0].play()", video_element)
        logging.info("Media play/pause toggled in browser.")
    except Exception as e:
        logging.error(f"Failed to control browser media: {e}")

def media_next_track():
    """
    Skips to the next media track for browser-based or system-level playback.
    """
    logging.info("Skipping to the next track...")
    try:
        pyautogui.press("nexttrack")  # Universal system shortcut
        logging.info("Skipped to the next track.")
    except Exception as e:
        logging.error(f"Failed to skip to the next track: {e}")

def media_previous_track():
    """
    Goes back to the previous media track for browser-based or system-level playback.
    """
    logging.info("Going back to the previous track...")
    try:
        pyautogui.press("prevtrack")  # Universal system shortcut
        logging.info("Went back to the previous track.")
    except Exception as e:
        logging.error(f"Failed to go back to the previous track: {e}")

def toggle_subtitles_browser(driver):
    """
    Toggles subtitles for media in a browser-based platform.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling subtitles in browser...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const player = document.querySelector('video');
            if (player.textTracks.length > 0) {
                const track = player.textTracks[0];
                track.mode = track.mode === 'showing' ? 'disabled' : 'showing';
            }
        """)
        logging.info("Subtitles toggled successfully in browser.")
    except Exception as e:
        logging.error(f"Failed to toggle subtitles: {e}")

def adjust_playback_speed(driver, speed):
    """
    Adjusts playback speed for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        speed (float): Desired playback speed (e.g., 1.5 for 1.5x speed).
    """
    logging.info(f"Setting playback speed to {speed}x...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script(f"arguments[0].playbackRate = {speed};", video_element)
        logging.info(f"Playback speed set to {speed}x.")
    except Exception as e:
        logging.error(f"Failed to adjust playback speed: {e}")

def toggle_media_loop(driver):
    """
    Toggles looping for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling media loop...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("arguments[0].loop = !arguments[0].loop;", video_element)
        logging.info("Media loop toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle media loop: {e}")

def toggle_fullscreen(driver):
    """
    Toggles fullscreen mode for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling fullscreen mode...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const player = arguments[0];
            if (!document.fullscreenElement) {
                player.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        """, video_element)
        logging.info("Fullscreen mode toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle fullscreen mode: {e}")


def media_volume_fade(volume, fade_time=5):
    """
    Fades volume in or out over a specified duration.

    Args:
        volume (int): Target volume level (0-100).
        fade_time (int): Duration of fade in seconds.
    """
    logging.info(f"Fading volume to {volume} over {fade_time} seconds...")
    try:
        current_volume = 0  # Assuming starting at 0
        step = volume // (fade_time * 2)  # Adjust step size based on fade time

        for level in range(0, volume + 1, step):
            media_volume_change(level)
            time.sleep(0.5)  # Smooth transition
        logging.info(f"Volume faded to {volume}.")
    except Exception as e:
        logging.error(f"Failed to fade volume: {e}")

def media_restart():
    """
    Restarts media playback from the beginning.
    """
    logging.info("Restarting media playback...")
    try:
        pyautogui.press("0")  # YouTube shortcut to go to the beginning
        logging.info("Media playback restarted.")
    except Exception as e:
        logging.error(f"Failed to restart media playback: {e}")


#Monitor Support & Multi-Monitor Setup Info (For media but reuseable)

def get_monitor_info():
    """
    Retrieves information about all connected monitors.

    Returns:
        list: A list of dictionaries with monitor details (width, height, x, y).
    """
    monitors = []
    for monitor in get_monitors():
        monitors.append({
            "width": monitor.width,
            "height": monitor.height,
            "x": monitor.x,
            "y": monitor.y
        })
    logging.info(f"Detected monitors: {monitors}")
    return monitors



def move_window_to_monitor(window_title, monitor_index):
    """
    Moves a window to a specified monitor.

    Args:
        window_title (str): Title of the window to move.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Moving '{window_title}' to monitor {monitor_index}")
    try:
        monitors = get_monitor_info()
        if monitor_index >= len(monitors):
            logging.error(f"Monitor index {monitor_index} is out of range.")
            return

        target_monitor = monitors[monitor_index]
        windows = gw.getWindowsWithTitle(window_title)

        if windows:
            window = windows[0]
            window.moveTo(target_monitor['x'], target_monitor['y'])
            logging.info(f"Window '{window_title}' moved to monitor {monitor_index}.")
        else:
            logging.error(f"Window '{window_title}' not found.")
    except Exception as e:
        logging.error(f"Failed to move window: {e}")

def fullscreen_on_monitor(window_title, monitor_index):
    """
    Toggles fullscreen for a window on a specific monitor.

    Args:
        window_title (str): Title of the window to fullscreen.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Toggling fullscreen for '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        pyautogui.hotkey("alt", "enter")  # Simulates fullscreen shortcut
        logging.info(f"Fullscreen toggled for '{window_title}' on monitor {monitor_index}.")
    except Exception as e:
        logging.error(f"Failed to toggle fullscreen: {e}")

def maximize_window_on_monitor(window_title, monitor_index):
    """
    Maximizes a window on a specific monitor.

    Args:
        window_title (str): Title of the window to maximize.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Maximizing '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        windows = gw.getWindowsWithTitle(window_title)
        if windows:
            window = windows[0]
            window.maximize()
            logging.info(f"Window '{window_title}' maximized on monitor {monitor_index}.")
        else:
            logging.error(f"Window '{window_title}' not found.")
    except Exception as e:
        logging.error(f"Failed to maximize window: {e}")

def control_media_on_monitor(window_title, monitor_index, action):
    """
    Controls media playback on a specific monitor.

    Args:
        window_title (str): Title of the media window.
        monitor_index (int): Index of the target monitor.
        action (str): Media control action ('play', 'pause', 'next', 'prev').
    """
    logging.info(f"Performing '{action}' on '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        if action == "play":
            pyautogui.press("playpause")
        elif action == "pause":
            pyautogui.press("playpause")
        elif action == "next":
            pyautogui.press("nexttrack")
        elif action == "prev":
            pyautogui.press("prevtrack")
        else:
            logging.error(f"Unsupported action: {action}")
        logging.info(f"Action '{action}' completed on '{window_title}' on monitor {monitor_index}.")
    except Exception as e:
        logging.error(f"Failed to perform action: {e}")






# Security and Authentication Actions

# Load encryption key (generate and save this once; reuse for decryption)
def load_encryption_key():
    """
    Loads the encryption key from a file.
    Returns:
        str: Encryption key.
    """
    try:
        with open("encryption.key", "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        logging.error("Encryption key file not found. Generate it using Fernet.")
        raise

def decrypt_password(encrypted_password):
    """
    Decrypts an encrypted password.

    Args:
        encrypted_password (str): Encrypted password in bytes.

    Returns:
        str: Decrypted password.
    """
    try:
        key = load_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode()).decode()
        logging.info("Password decrypted successfully.")
        return decrypted
    except Exception as e:
        logging.error(f"Failed to decrypt password: {e}")
        raise


def load_credentials(name):
    """
    Loads credentials from a JSON file based on the provided name.

    Args:
        name (str): The name of the credential to retrieve.

    Returns:
        dict: A dictionary containing 'username' and 'password'.

    Raises:
        KeyError: If the credential is not found in the file.
    """
    try:
        with open("credentials.json", "r") as file:
            all_credentials = json.load(file)

        if name not in all_credentials:
            raise KeyError(f"Credential '{name}' not found in credentials.json.")

        return all_credentials[name]
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in credentials.json.")
    except FileNotFoundError:
        raise FileNotFoundError("credentials.json file not found.")


def login_attempt(name):
    """
    Attempts to log in using stored credentials.

    Args:
        name (str): Name of the credential in the JSON file.
    """
    logging.info(f"Attempting login for credential: {name}")
    try:
        # Load the credentials by name
        credentials = load_credentials(name)

        username = credentials["username"]
        password = credentials["password"]

        # Placeholder for login logic
        logging.info(f"Logging in with username: {username}")
        # Implement your actual login logic here
    except KeyError as ke:
        logging.error(f"Missing key in credentials for '{name}': {ke}")
    except FileNotFoundError:
        logging.error("credentials.json file not found.")
    except Exception as e:
        logging.error(f"Login attempt failed for '{name}': {e}")





def logout():
    """
    Logs the user out.
    """
    logging.info("Logging out...")
    try:
        # Example: Send logout request to an API or invalidate session
        logging.info("Logout successful.")
    except Exception as e:
        logging.error(f"Logout failed: {e}")


def permission_request(permission):
    """
    Requests a specific system or application permission.

    Args:
        permission (str): Name of the permission to request.
    """
    logging.info(f"Requesting permission: {permission}")
    try:
        # Replace with actual permission logic
        logging.info(f"Permission '{permission}' granted.")
    except Exception as e:
        logging.error(f"Permission request failed: {e}")


def run_as_administrator(command):
    """
    Runs a command as Administrator.

    Args:
        command (str): The command to execute.
    """
    logging.info(f"Running command as Administrator: {command}")
    try:
        subprocess.run(["runas", "/user:Administrator", command], check=True)
        logging.info("Command executed successfully as Administrator.")
    except Exception as e:
        logging.error(f"Failed to execute command as Administrator: {e}")



def generate_otp(secret_key):
    """
    Generates a One-Time Password (OTP) using a secret key.

    Args:
        secret_key (str): Secret key for OTP generation.

    Returns:
        str: OTP.
    """
    totp = pyotp.TOTP(secret_key)
    otp = totp.now()
    logging.info(f"Generated OTP: {otp}")
    return otp

def verify_otp(secret_key, otp):
    """
    Verifies a One-Time Password (OTP) against a secret key.

    Args:
        secret_key (str): Secret key for OTP generation.
        otp (str): OTP to verify.

    Returns:
        bool: True if OTP is valid, False otherwise.
    """
    totp = pyotp.TOTP(secret_key)
    is_valid = totp.verify(otp)
    logging.info(f"OTP verification result: {is_valid}")
    return is_valid


logging.basicConfig(
    filename="security.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)



# Specialized Actions
def dropdown_select(driver=None, selector=None, value=None, by=By.CSS_SELECTOR, is_local=False, window_title=None):
    """
    Selects a value in a dropdown (web-based or local application).

    Args:
        driver (WebDriver, optional): Selenium WebDriver instance for web dropdowns.
        selector (str, optional): Selector for the web dropdown element.
        value (str or int): Value to select (visible text or index).
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        is_local (bool): Whether the dropdown is in a local application.
        window_title (str, optional): Title of the local application window.
    """
    try:
        if is_local and window_title:
            logging.info(f"Selecting '{value}' in dropdown in local application: {window_title}")
            #import pygetwindow as gw
            #import pywinauto
            #from pywinauto.application import Application
            # Locate window and dropdown control
            app = Application(backend="uia").connect(title=window_title)
            window = app.window(title=window_title)
            dropdown = window.child_window(title=selector, control_type="ComboBox")

            # Select dropdown value
            dropdown.select(value)
            logging.info(f"Successfully selected '{value}' in dropdown: {selector} (local).")

        elif driver and selector and value:
            logging.info(f"Selecting '{value}' in web dropdown: {selector}")
            element = driver.find_element(by, selector)
            dropdown = Select(element)

            if isinstance(value, int):
                dropdown.select_by_index(value)
            else:
                dropdown.select_by_visible_text(value)

            logging.info(f"Successfully selected '{value}' in web dropdown: {selector}.")
        else:
            raise ValueError("Invalid arguments. Provide either a web driver and selector or local application details.")
    except Exception as e:
        logging.error(f"Failed to select '{value}' in dropdown: {e}")

def checkbox_toggle(driver, selector, value, by=By.CSS_SELECTOR, max_retries=3):
    """
    Toggles a checkbox on or off with retries.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the checkbox element.
        value (bool): Desired state of the checkbox (True for checked, False for unchecked).
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        max_retries (int): Number of retry attempts.
    """
    def toggle_checkbox():
        checkbox = driver.find_element(by, selector)
        if checkbox.is_selected() != value:
            checkbox.click()

    retry_action(toggle_checkbox, max_retries=max_retries)


def slider_adjustment(driver, selector, value, by=By.CSS_SELECTOR):
    """
    Adjusts a slider to a specific value.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the slider element.
        value (int): Target value for the slider.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
    """
    logging.info(f"Adjusting slider {selector} to value {value}")
    try:
        slider = driver.find_element(by, selector)
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", slider, value)
        logging.info(f"Slider {selector} adjusted to {value}")
    except Exception as e:
        logging.error(f"Failed to adjust slider {selector}: {e}")


def calendar_interaction(driver, selector, date, by=By.CSS_SELECTOR, max_retries=3):
    """
    Interacts with a calendar to set a specific date with retries.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the calendar element.
        
        date (str): Date to set in the format 'YYYY-MM-DD'.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        max_retries (int): Number of retry attempts.
    """
    def set_date():
        calendar = driver.find_element(by, selector)
        calendar.clear()
        calendar.send_keys(date)

    retry_action(set_date, max_retries=max_retries)


def loop(actions, iterations, driver):
    """
    Loops through a series of actions with error recovery.

    Args:
        actions (list of callables): List of actions to execute.
        iterations (int): Number of times to repeat the loop.
        driver (WebDriver): Selenium WebDriver instance.
    """
    for i in range(iterations):
        logging.info(f"Executing loop iteration {i + 1}")
        for action in actions:
            try:
                action(driver)
            except Exception as e:
                logging.error(f"Error during loop iteration {i + 1}, action {action.__name__}: {e}")
                continue


def wait(duration):
    """
    Waits for a specified duration.

    Args:
        duration (int): Time to wait in seconds.
    """
    logging.info(f"Waiting for {duration} seconds...")
    try:
        time.sleep(duration)
        logging.info("Wait completed.")
    except Exception as e:
        logging.error(f"Error during wait: {e}")






def wait_for(driver, condition, selector, timeout=30, by=By.CSS_SELECTOR):
    """
    Waits for a specific condition to be met with logging.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        condition (callable): Condition to wait for (e.g., element_to_be_clickable).
        selector (str): Selector for the target element.
        timeout (int): Maximum wait time in seconds.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
    """
    logging.info(f"Waiting for condition '{condition.__name__}' on {selector}")
    try:
        WebDriverWait(driver, timeout).until(condition((by, selector)))
        logging.info(f"Condition '{condition.__name__}' met for {selector}")
    except Exception as e:
        logging.error(f"Condition '{condition.__name__}' not met for {selector} within {timeout} seconds: {e}")
        raise



#ERROR HANDLING & REALTIME ERORR HANDLING



def send_error_notification(error_message):
    """
    Sends an email notification with the error details.

    Args:
        error_message (str): The error message to include in the email.
    """
    try:
        smtp_server = "smtp.example.com"
        smtp_port = 587
        smtp_username = "your_email@example.com"
        smtp_password = "your_password"
        recipient_email = "admin@example.com"

        message = MIMEText(f"An error occurred:\n\n{error_message}")
        message["Subject"] = "Critical Error Notification"
        message["From"] = smtp_username
        message["To"] = recipient_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        logging.info("Error notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")

def retry_action_with_error_reporting(action, max_retries=3, wait_time=2, *args, **kwargs):
    """
    Retries an action if it fails and logs detailed error information.

    Args:
        action (callable): The function to execute.
        max_retries (int): Number of retry attempts.
        wait_time (int): Delay between retries in seconds.
        *args: Positional arguments for the action.
        **kwargs: Keyword arguments for the action.

    Returns:
        Any: The return value of the action if successful.
    """
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries} for action '{action.__name__}'")
            result = action(*args, **kwargs)
            logging.info(f"Action '{action.__name__}' succeeded on attempt {attempt + 1}")
            return result
        except Exception as e:
            error_message = f"Attempt {attempt + 1} failed for action '{action.__name__}': {e}"
            logging.error(error_message)
            if attempt == max_retries - 1:
                send_error_notification(error_message)
            time.sleep(wait_time)
    raise Exception(f"Action '{action.__name__}' failed after {max_retries} attempts.")

def loop_with_error_reporting(actions, iterations, driver):
    """
    Executes actions in a loop and generates a detailed error report.

    Args:
        actions (list of callables): List of actions to execute.
        iterations (int): Number of times to repeat the loop.
        driver (WebDriver): Selenium WebDriver instance.
    """
    error_summary = []

    for i in range(iterations):
        logging.info(f"Executing loop iteration {i + 1}")
        for action in actions:
            try:
                action(driver)
            except Exception as e:
                error_message = f"Error in loop iteration {i + 1}, action '{action.__name__}': {e}"
                logging.error(error_message)
                error_summary.append(error_message)

    # Log error summary
    if error_summary:
        logging.error("Error Summary:\n" + "\n".join(error_summary))
        send_error_notification("\n".join(error_summary))

def write_error_summary_to_file(error_summary, filename="error_summary.txt"):
    """
    Writes the error summary to a file.

    Args:
        error_summary (list): List of error messages.
        filename (str): Name of the file to write the summary to.
    """
    logging.info(f"Writing error summary to file: {filename}")
    try:
        with open(filename, "w") as file:
            file.write("Error Summary:\n")
            file.write("\n".join(error_summary))
        logging.info(f"Error summary written to {filename}.")
    except Exception as e:
        logging.error(f"Failed to write error summary to file: {e}")


class WorkflowExecutor:
    def __init__(self):
        self.driver = None
        self.app = None
        self.variables = {}
        self.status = "initialized"
        self.cipher = None
        self.browser_active = False
        self.last_url = None

    def execute_action(self, action):
        """
        Executes a normalized action with proper error handling and retries.
        """
        try:
            normalized_action = normalize_action(action)
            action_type = normalized_action['type']
            logging.info(f"Executing action: {action_type}")

            # Initialize browser if needed
            if action_type == 'open_selenium':
                self.cleanup_browser()
                self.driver = open_selenium(
                    browser=normalized_action.get('browser'),
                    headless=normalized_action.get('headless', False)
                )
                self.browser_active = True
                return

            # Check browser state before each action that requires it
            if action_type in ['url_navigation', 'element_interact']:
                if not self.ensure_browser_active():
                    # Reinitialize browser if needed
                    self.driver = open_selenium(
                        browser=normalized_action.get('browser', 'chrome'),
                        headless=normalized_action.get('headless', False)
                    )
                    self.browser_active = True
                    
                    # If this was a navigation action, we need to revisit the last URL
                    if self.last_url and action_type == 'element_interact':
                        self.driver.get(self.last_url)
                        try:
                            WebDriverWait(self.driver, 30).until(
                                lambda driver: driver.execute_script('return document.readyState') == 'complete'
                            )
                        except Exception as e:
                            logging.warning(f"Page load wait failed: {e}")

                if action_type == 'url_navigation':
                    url = normalized_action.get('url')
                    self.driver.get(url)
                    try:
                        WebDriverWait(self.driver, 30).until(
                            lambda driver: driver.execute_script('return document.readyState') == 'complete'
                        )
                        self.last_url = url
                    except Exception as e:
                        logging.warning(f"Page load wait failed: {e}")
                    
                elif action_type == 'element_interact':
                    try:
                        self.element_interact(
                            selector=normalized_action.get('selector'),
                            by=normalized_action.get('by', 'css'),
                            action=normalized_action.get('action', 'click'),
                            value=normalized_action.get('value', '')
                        )
                    except Exception as e:
                        logging.error(f"Element interaction failed: {e}")
                        self.take_debug_screenshot()
                        raise

            # Don't cleanup browser after each action anymore
            # Only cleanup on explicit close or error

        except Exception as e:
            self._handle_action_error(normalized_action, e)
            if isinstance(e, (selenium.common.exceptions.NoSuchWindowException, 
                            selenium.common.exceptions.WebDriverException)):
                self.cleanup_browser()
            raise

    def ensure_browser_active(self):
        """
        Ensures browser is active and reinitializes if needed.
        Returns True if browser is active, False if it needs to be reinitialized.
        """
        if not self.driver:
            logging.info("No browser session exists")
            return False
        
        try:
            # More robust check for browser state
            self.driver.current_window_handle  # This will throw an exception if browser is closed
            return True
        except Exception as e:
            logging.warning(f"Browser check failed: {e}. Reinitializing...")
            self.cleanup_browser()
            return False

    def cleanup_browser(self):
        """Safely cleanup browser resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.warning(f"Error during browser cleanup: {e}")
            finally:
                self.driver = None
                self.browser_active = False
                self.last_url = None

    def element_interact(self, selector, by='css', action='click', value=''):
        """Interacts with a web element with smart selector fallback."""
        if not self.ensure_browser_active():
            raise ValueError("Browser not initialized or not active")
        
        logging.info(f"Interacting with element: {selector} ({action})")
        try:
            # Progressive selector strategy
            selectors_to_try = [
                # Try ID first (most specific)
                (By.ID, selector if not selector.startswith('#') else selector[1:]),
                # Then CSS selector
                (By.CSS_SELECTOR, selector),
                # Then class name
                (By.CLASS_NAME, selector if not selector.startswith('.') else selector[1:]),
                # Then name attribute
                (By.NAME, selector),
                # Finally, try XPath as fallback
                (By.XPATH, f"//*[@id='{selector}']"),  # ID as XPath
                (By.XPATH, f"//*[contains(@class, '{selector}')]"),  # Class as XPath
                (By.XPATH, f"//*[@name='{selector}']"),  # Name as XPath
                (By.XPATH, selector if selector.startswith('//') else f"//*[contains(text(), '{selector}')]")  # Text content or custom XPath
            ]

            wait = WebDriverWait(self.driver, 20)
            element = None
            last_error = None

            for by_type, sel in selectors_to_try:
                try:
                    element = wait.until(lambda d: (
                        d.find_element(by_type, sel) and
                        d.find_element(by_type, sel).is_displayed() and
                        d.find_element(by_type, sel).is_enabled()
                    ) and d.find_element(by_type, sel))
                    logging.info(f"Element found using {by_type}: {sel}")
                    break
                except Exception as e:
                    last_error = e
                    continue

            if not element:
                raise last_error or Exception("Element not found with any selector strategy")

            # Scroll element into view
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.scrollIntoView({block: 'center', behavior: 'instant'});
            """, element)
            
            time.sleep(0.5)

            if action == 'click':
                try:
                    element.click()
                except:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                    except:
                        ActionChains(self.driver).move_to_element(element).click().perform()
            elif action == 'input':
                for _ in range(3):
                    try:
                        element.clear()
                        element.send_keys(Keys.CONTROL + "a")
                        element.send_keys(Keys.DELETE)
                        for char in value:
                            element.send_keys(char)
                            time.sleep(0.1)
                        
                        if element.get_attribute('value') == value:
                            break
                    except Exception as e:
                        logging.warning(f"Input attempt failed: {e}, retrying...")
                        time.sleep(1)

            return True

        except Exception as e:
            logging.error(f"Element interaction failed: {str(e)}")
            self.take_debug_screenshot()
            raise

    def take_debug_screenshot(self):
        """Takes a debug screenshot if possible."""
        if self.driver:
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshots/debug_{timestamp}.png"
                os.makedirs("error_screenshots", exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Debug screenshot saved: {screenshot_path}")
            except Exception as e:
                logging.error(f"Failed to save debug screenshot: {e}")

    def cleanup(self):
        """Cleanup all resources."""
        self.cleanup_browser()
        if self.app:
            try:
                self.app = None
            except Exception as e:
                logging.error(f"Error cleaning up application: {e}")
        logging.info("Workflow cleanup completed successfully")

    def _init_cipher(self):
        """Initialize the cipher for encryption/decryption."""
        try:
            with open('secret.key', 'rb') as key_file:
                key = key_file.read()
            self.cipher = Fernet(key)
        except Exception as e:
            logging.error(f"Failed to initialize cipher: {e}")
            raise

    def _decrypt_password(self, encrypted_password):
        """
        Decrypt password using the initialized cipher.
        """
        try:
            if not self.cipher:
                self._init_cipher()
            return self.cipher.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logging.error(f"Error decrypting password: {e}")
            raise

    def _load_encryption_key(self):
        """
        Load encryption key from file.
        """
        try:
            with open('secret.key', 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading encryption key: {e}")
            raise

    def open_selenium(self, browser=None, headless=False):
        """Opens a Selenium WebDriver instance using system default or specified browser."""
        logging.info(f"Opening browser (headless: {headless})")
        try:
            self.driver = open_selenium(browser, headless)
            logging.info("Browser opened successfully")
            return self.driver
        except Exception as e:
            logging.error(f"Failed to open browser: {str(e)}")
            raise

    def close_selenium(self):
        """Closes the Selenium WebDriver instance."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("Browser closed successfully")
            except Exception as e:
                logging.error(f"Failed to close browser: {e}")
            finally:
                self.driver = None

    def url_navigation(self, url):
        """Navigates to a URL."""
        logging.info(f"Navigating to: {url}")
        try:
            self.driver.get(url)
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            logging.info(f"Navigation successful: {url}")
        except Exception as e:
            logging.error(f"Navigation failed: {e}")
            raise

    def _get_credentials(self, credential_name):
        """
        Get credentials from credentials.json file.
        """
        try:
            with open('credentials.json', 'r') as f:
                credentials_list = json.load(f)
                for cred in credentials_list:
                    if cred['name'].lower() == credential_name.lower():
                        return cred
            return None
        except Exception as e:
            logging.error(f"Error loading credentials: {e}")
            return None

    def _handle_action_error(self, action, error):
        """
        Handles errors that occur during action execution.
        """
        logging.error(f"Error executing action: {action.get('type')}")
        logging.error(f"Error details: {str(error)}")
        if self.driver:
            try:
                # Take screenshot on error
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshots/error_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Error screenshot saved: {screenshot_path}")
            except Exception as screenshot_error:
                logging.error(f"Failed to save error screenshot: {screenshot_error}")

    def __del__(self):
        """
        Destructor to ensure resources are freed even if cleanup wasn't called.
        """
        try:
            if self.driver:
                self.close_selenium()
        except:
            pass  # Suppress errors in destructor

    def wait_for_page_load(self, timeout=30):
        """Waits for page load to complete with multiple conditions."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: driver.execute_script('''
                return document.readyState === "complete" && 
                       !document.querySelector(".loading") &&
                       (typeof jQuery === "undefined" || jQuery.active === 0) &&
                       (!window.angular || !angular.element(document).injector() || 
                        !angular.element(document).injector().get('$http').pendingRequests.length)
            '''))
            time.sleep(1)  # Additional small wait for any final rendering
        except Exception as e:
            logging.error(f"Page load wait timeout: {e}")
            self.take_debug_screenshot()
            raise

    def handle_desktop_application(self, action):
        """Enhanced desktop application handling with retries and checks."""
        try:
            app_path = action.get('application_path')
            arguments = action.get('arguments', '')
            working_dir = action.get('working_dir')
            
            # Ensure any existing instance is closed
            try:
                app = Application().connect(path=app_path)
                app.kill()
                time.sleep(1)
            except:
                pass  # No existing instance
            
            # Launch application with retry
            for attempt in range(3):
                try:
                    if working_dir:
                        process = subprocess.Popen(
                            [app_path] + shlex.split(arguments),
                            cwd=working_dir,
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    else:
                        process = subprocess.Popen(
                            [app_path] + shlex.split(arguments),
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    
                    # Wait for window to appear
                    start_time = time.time()
                    while time.time() - start_time < 30:
                        try:
                            app = Application().connect(process=process.pid)
                            window = app.top_window()
                            window.wait('ready', timeout=10)
                            logging.info(f"Application launched successfully: {app_path}")
                            return app
                        except Exception:
                            time.sleep(1)
                    
                    raise TimeoutError("Application window did not appear")
                    
                except Exception as e:
                    logging.warning(f"Launch attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            logging.error(f"Failed to launch application {app_path}: {e}")
            raise

    def desktop_input(self, window, control_id, text, retries=3):
        """More reliable desktop input with retries."""
        for attempt in range(retries):
            try:
                # Find control and ensure it's ready
                control = window[control_id]
                control.wait('ready', timeout=10)
                
                # Clear existing text
                control.set_text('')
                time.sleep(0.5)
                
                # Type text with delay
                for char in text:
                    control.type_keys(char, pause=0.1)
                
                # Verify input
                actual_text = control.get_value()
                if actual_text == text:
                    return True
                    
                logging.warning(f"Input verification failed. Expected: {text}, Got: {actual_text}")
                
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Desktop input failed after {retries} attempts: {e}")
                    raise
                time.sleep(1)
                
        return False

    def desktop_click(self, window, control_id, retries=3):
        """More reliable desktop clicking with retries."""
        for attempt in range(retries):
            try:
                control = window[control_id]
                control.wait('ready', timeout=10)
                control.click_input()
                time.sleep(0.5)  # Wait for click to register
                return True
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Desktop click failed after {retries} attempts: {e}")
                    raise
                time.sleep(1)

# Function to execute a workflow
def execute_workflow(workflow_data):
    """
    Main entry point for workflow execution.
    
    Args:
        workflow_data (dict): The workflow to execute
    """
    executor = WorkflowExecutor()
    try:
        executor.execute_workflow(workflow_data)
    except Exception as e:
        logging.error(f"Workflow execution failed: {str(e)}")
        raise


# Action Type Mappings
ACTION_TYPE_MAPPINGS = {
    # Browser Actions
    'open_browser': 'open_selenium',
    'launch_browser': 'open_selenium',
    'start_browser': 'open_selenium',
    
    'close_browser': 'close_selenium',
    'quit_browser': 'close_selenium',
    'exit_browser': 'close_selenium',
    
    'navigate': 'url_navigation',
    'go_to': 'url_navigation',
    'go_to_url': 'url_navigation',
    'browse_to': 'url_navigation',
    
    'type': 'typing_sequence',
    'input': 'typing_sequence',
    'input_text': 'typing_sequence',
    'enter_text': 'typing_sequence',
    
    'click': 'element_interact',
    'click_element': 'element_interact',
    'click_button': 'element_interact',
    
    # Mouse Actions
    'mouse_click': 'left_click',
    'click_at': 'left_click',
    
    'right_click_at': 'right_click',
    'context_click': 'right_click',
    
    'double_click': 'double_left_click',
    'dbl_click': 'double_left_click',
    
    'drag': 'mouse_drag',
    'drag_and_drop': 'mouse_drag',
    
    'hover': 'mouse_hover',
    'mouse_over': 'mouse_hover',
    
    'scroll': 'mouse_scroll',
    'scroll_page': 'mouse_scroll',
    
    'move_mouse': 'mouse_move',
    'move_cursor': 'mouse_move',
    
    # Keyboard Actions
    'press_key': 'keystroke',
    'key_press': 'keystroke',
    
    'press_keys': 'key_combination',
    'key_combo': 'key_combination',
    
    'type_text': 'typing_sequence',
    'send_keys': 'typing_sequence',
    
    'special_key': 'special_key_press',
    'system_key': 'special_key_press',
    
    'shortcut': 'shortcut_use',
    'keyboard_shortcut': 'shortcut_use',
    
    # File Operations
    'open_file': 'file_open',
    'load_file': 'file_open',
    
    'save_file': 'file_save',
    'write_file': 'file_save',
    
    'delete_file': 'file_delete',
    'remove_file': 'file_delete',
    
    'rename_file': 'file_rename',
    'move_file': 'file_move',
    'copy_file': 'file_copy',
    'upload': 'file_upload',
    'download': 'file_download',
    
    # Wait Actions
    'sleep': 'wait',
    'pause': 'wait',
    'delay': 'wait',
    
    'wait_until': 'wait_for',
    'wait_for_element': 'wait_for',
    
    # Email Actions
    'read_email': 'email_read',
    'check_email': 'email_read',
    
    'write_email': 'email_write',
    'compose_email': 'email_write',
    
    'send_email': 'email_send',
    'email': 'email_send',
    
    # Application Actions
    'open_app': 'open_application',
    'launch_app': 'open_application',
    'start_app': 'open_application',
    'run_app': 'open_application'
}  # Remove the extra closing brace

def normalize_action(action):
    """
    Normalizes action type and parameters for consistent handling.
    """
    if not isinstance(action, dict):
        raise ValueError("Action must be a dictionary")
        
    # Make a copy to avoid modifying the original
    normalized = action.copy()
    
    # Normalize action type
    action_type = normalized.get('type', '').lower()
    normalized['type'] = ACTION_TYPE_MAPPINGS.get(action_type, action_type)
    
    return normalized

def wait(duration):
    """
    Waits for a specified duration.

    Args:
        duration (int): Time to wait in seconds.
    """
    logging.info(f"Waiting for {duration} seconds...")
    try:
        time.sleep(duration)
        logging.info("Wait completed.")
    except Exception as e:
        logging.error(f"Error during wait: {e}")

def take_error_screenshot(driver, error_type="error"):
    """
    Takes a screenshot when an error occurs.
    
    Args:
        driver: WebDriver instance
        error_type (str): Type of error for filename
    
    Returns:
        str: Path to screenshot or None if failed
    """
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_path = f"error_screenshots/{error_type}_{timestamp}.png"
        os.makedirs("error_screenshots", exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logging.info(f"Error screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"Failed to save error screenshot: {e}")
        return None

def email_write_gmail(to, subject, body, cc=None, bcc=None):
    """
    Composes and drafts an email in Gmail using the Gmail API.

    Args:
        to (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.
    """
    try:
        # Load credentials from token.json
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.compose'])
        service = build('gmail', 'v1', credentials=creds)

        # Create the email message
        message = create_gmail_message(to, subject, body, cc, bcc)

        # Create a draft in Gmail
        draft = service.users().drafts().create(userId='me', body=message).execute()
        logging.info(f"Draft created successfully with ID: {draft['id']}")
    except Exception as e:
        logging.error(f"Failed to compose Gmail draft: {e}")

def email_send_gmail(to_address, subject, body, smtp_server=None, smtp_port=None, smtp_username=None, smtp_password=None):
    """
    Sends an email using Gmail API.
    """
    logging.info(f"Sending email to {to_address} via Gmail API")
    try:
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.send'])
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(body)
        message['to'] = to_address
        message['subject'] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def email_search_advanced(platform='outlook', criteria=None):
    """
    Searches emails with advanced criteria such as date range and keywords.

    Args:
        platform (str): Email platform ('outlook' or 'gmail').
        criteria (dict): Search criteria (e.g., subject, sender, date_range).

    Returns:
        list: List of matching emails.
    """
    logging.info(f"Performing advanced search on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)  # Add advanced filtering logic in email_read_outlook
        elif platform == 'gmail':
            return email_read_gmail(criteria)  # Update Gmail search logic to handle date ranges
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Advanced search failed: {e}")
        return []

def retry_email_send(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password, retries=3):
    """
    Retries sending an email if it fails.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        retries (int): Number of retry attempts.
    """
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Attempt {attempt} to send email to {to_address}")
            email_send_with_attachments(to_address, subject, body, [], smtp_server, smtp_port, smtp_username, smtp_password)
            logging.info("Email sent successfully.")
            break
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed: {e}")
            if attempt == retries:
                logging.error("All attempts to send email failed.")



def schedule_email(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password, delay):
    """
    Schedules an email to be sent after a delay.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        delay (int): Delay in seconds before sending the email.
    """
    logging.info(f"Scheduling email to {to_address} in {delay} seconds.")
    Timer(delay, email_send_with_attachments, args=(to_address, subject, body, [], smtp_server, smtp_port, smtp_username, smtp_password)).start()


# Interaction with Media


def media_play(file_path=None):
    """
    Plays media from a local file or resumes browser-based media.

    Args:
        file_path (str, optional): Path to the local media file. If None, resumes browser media.
    """
    if file_path:
        logging.info(f"Playing local media file: {file_path}")
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.call(('open' if os.name == 'darwin' else 'xdg-open', file_path))
            logging.info("Media playback started successfully.")
        except Exception as e:
            logging.error(f"Failed to play media: {e}")
    else:
        logging.info("Playing browser-based media.")
        pyautogui.press("playpause")  # Play/Pause media in browser or system


def media_pause():
    """
    Pauses browser-based media or system-level media.
    """
    logging.info("Pausing media...")
    try:
        pyautogui.press("playpause")  # Universal pause button
        logging.info("Media paused successfully.")
    except Exception as e:
        logging.error(f"Failed to pause media: {e}")





def media_seek(position):
    """
    Seeks media to a specific position in seconds.

    Args:
        position (int): Position in seconds to seek to.
    """
    logging.info(f"Seeking to position {position} seconds...")
    try:
        pyautogui.press("k")  # YouTube shortcut for pausing
        pyautogui.typewrite(str(position))  # Type the position
        pyautogui.press("enter")  # Confirm position change
        logging.info(f"Media seeked to {position} seconds.")
    except Exception as e:
        logging.error(f"Failed to seek media position: {e}")


def media_volume_change(volume):
    """
    Changes the system volume to a specified level.

    Args:
        volume (int): Volume level (0-100).
    """
    logging.info(f"Changing volume to {volume}...")
    try:
        if 0 <= volume <= 100:
            for _ in range(50):  # Reset to zero volume
                pyautogui.press("volumedown")
            for _ in range(volume // 2):  # Increase to the desired level (each press ~2%)
                pyautogui.press("volumeup")
            logging.info(f"Volume set to {volume}.")
        else:
            logging.error("Volume level must be between 0 and 100.")
    except Exception as e:
        logging.error(f"Failed to change volume: {e}")

#additional media control BROWSER and MUTE
def media_mute():
    """
    Toggles mute for the system or browser-based media.
    """
    logging.info("Toggling mute...")
    try:
        pyautogui.press("volumemute")
        logging.info("Mute toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle mute: {e}")

def browser_media_play_pause(driver):
    """
    Toggles play/pause for browser-based media (e.g., YouTube, Netflix).

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling play/pause for browser media...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("arguments[0].pause()" if video_element.is_playing else "arguments[0].play()", video_element)
        logging.info("Media play/pause toggled in browser.")
    except Exception as e:
        logging.error(f"Failed to control browser media: {e}")

def media_next_track():
    """
    Skips to the next media track for browser-based or system-level playback.
    """
    logging.info("Skipping to the next track...")
    try:
        pyautogui.press("nexttrack")  # Universal system shortcut
        logging.info("Skipped to the next track.")
    except Exception as e:
        logging.error(f"Failed to skip to the next track: {e}")

def media_previous_track():
    """
    Goes back to the previous media track for browser-based or system-level playback.
    """
    logging.info("Going back to the previous track...")
    try:
        pyautogui.press("prevtrack")  # Universal system shortcut
        logging.info("Went back to the previous track.")
    except Exception as e:
        logging.error(f"Failed to go back to the previous track: {e}")

def toggle_subtitles_browser(driver):
    """
    Toggles subtitles for media in a browser-based platform.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling subtitles in browser...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const player = document.querySelector('video');
            if (player.textTracks.length > 0) {
                const track = player.textTracks[0];
                track.mode = track.mode === 'showing' ? 'disabled' : 'showing';
            }
        """)
        logging.info("Subtitles toggled successfully in browser.")
    except Exception as e:
        logging.error(f"Failed to toggle subtitles: {e}")

def adjust_playback_speed(driver, speed):
    """
    Adjusts playback speed for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        speed (float): Desired playback speed (e.g., 1.5 for 1.5x speed).
    """
    logging.info(f"Setting playback speed to {speed}x...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script(f"arguments[0].playbackRate = {speed};", video_element)
        logging.info(f"Playback speed set to {speed}x.")
    except Exception as e:
        logging.error(f"Failed to adjust playback speed: {e}")

def toggle_media_loop(driver):
    """
    Toggles looping for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling media loop...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("arguments[0].loop = !arguments[0].loop;", video_element)
        logging.info("Media loop toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle media loop: {e}")

def toggle_fullscreen(driver):
    """
    Toggles fullscreen mode for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling fullscreen mode...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const player = arguments[0];
            if (!document.fullscreenElement) {
                player.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        """, video_element)
        logging.info("Fullscreen mode toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle fullscreen mode: {e}")


def media_volume_fade(volume, fade_time=5):
    """
    Fades volume in or out over a specified duration.

    Args:
        volume (int): Target volume level (0-100).
        fade_time (int): Duration of fade in seconds.
    """
    logging.info(f"Fading volume to {volume} over {fade_time} seconds...")
    try:
        current_volume = 0  # Assuming starting at 0
        step = volume // (fade_time * 2)  # Adjust step size based on fade time

        for level in range(0, volume + 1, step):
            media_volume_change(level)
            time.sleep(0.5)  # Smooth transition
        logging.info(f"Volume faded to {volume}.")
    except Exception as e:
        logging.error(f"Failed to fade volume: {e}")

def media_restart():
    """
    Restarts media playback from the beginning.
    """
    logging.info("Restarting media playback...")
    try:
        pyautogui.press("0")  # YouTube shortcut to go to the beginning
        logging.info("Media playback restarted.")
    except Exception as e:
        logging.error(f"Failed to restart media playback: {e}")


#Monitor Support & Multi-Monitor Setup Info (For media but reuseable)

def get_monitor_info():
    """
    Retrieves information about all connected monitors.

    Returns:
        list: A list of dictionaries with monitor details (width, height, x, y).
    """
    monitors = []
    for monitor in get_monitors():
        monitors.append({
            "width": monitor.width,
            "height": monitor.height,
            "x": monitor.x,
            "y": monitor.y
        })
    logging.info(f"Detected monitors: {monitors}")
    return monitors



def move_window_to_monitor(window_title, monitor_index):
    """
    Moves a window to a specified monitor.

    Args:
        window_title (str): Title of the window to move.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Moving '{window_title}' to monitor {monitor_index}")
    try:
        monitors = get_monitor_info()
        if monitor_index >= len(monitors):
            logging.error(f"Monitor index {monitor_index} is out of range.")
            return

        target_monitor = monitors[monitor_index]
        windows = gw.getWindowsWithTitle(window_title)

        if windows:
            window = windows[0]
            window.moveTo(target_monitor['x'], target_monitor['y'])
            logging.info(f"Window '{window_title}' moved to monitor {monitor_index}.")
        else:
            logging.error(f"Window '{window_title}' not found.")
    except Exception as e:
        logging.error(f"Failed to move window: {e}")

def fullscreen_on_monitor(window_title, monitor_index):
    """
    Toggles fullscreen for a window on a specific monitor.

    Args:
        window_title (str): Title of the window to fullscreen.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Toggling fullscreen for '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        pyautogui.hotkey("alt", "enter")  # Simulates fullscreen shortcut
        logging.info(f"Fullscreen toggled for '{window_title}' on monitor {monitor_index}.")
    except Exception as e:
        logging.error(f"Failed to toggle fullscreen: {e}")

def maximize_window_on_monitor(window_title, monitor_index):
    """
    Maximizes a window on a specific monitor.

    Args:
        window_title (str): Title of the window to maximize.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Maximizing '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        windows = gw.getWindowsWithTitle(window_title)
        if windows:
            window = windows[0]
            window.maximize()
            logging.info(f"Window '{window_title}' maximized on monitor {monitor_index}.")
        else:
            logging.error(f"Window '{window_title}' not found.")
    except Exception as e:
        logging.error(f"Failed to maximize window: {e}")

def control_media_on_monitor(window_title, monitor_index, action):
    """
    Controls media playback on a specific monitor.

    Args:
        window_title (str): Title of the media window.
        monitor_index (int): Index of the target monitor.
        action (str): Media control action ('play', 'pause', 'next', 'prev').
    """
    logging.info(f"Performing '{action}' on '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        if action == "play":
            pyautogui.press("playpause")
        elif action == "pause":
            pyautogui.press("playpause")
        elif action == "next":
            pyautogui.press("nexttrack")
        elif action == "prev":
            pyautogui.press("prevtrack")
        else:
            logging.error(f"Unsupported action: {action}")
        logging.info(f"Action '{action}' completed on '{window_title}' on monitor {monitor_index}.")
    except Exception as e:
        logging.error(f"Failed to perform action: {e}")






# Security and Authentication Actions

# Load encryption key (generate and save this once; reuse for decryption)
def load_encryption_key():
    """
    Loads the encryption key from a file.
    Returns:
        str: Encryption key.
    """
    try:
        with open("encryption.key", "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        logging.error("Encryption key file not found. Generate it using Fernet.")
        raise

def decrypt_password(encrypted_password):
    """
    Decrypts an encrypted password.

    Args:
        encrypted_password (str): Encrypted password in bytes.

    Returns:
        str: Decrypted password.
    """
    try:
        key = load_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode()).decode()
        logging.info("Password decrypted successfully.")
        return decrypted
    except Exception as e:
        logging.error(f"Failed to decrypt password: {e}")
        raise


def load_credentials(name):
    """
    Loads credentials from a JSON file based on the provided name.

    Args:
        name (str): The name of the credential to retrieve.

    Returns:
        dict: A dictionary containing 'username' and 'password'.

    Raises:
        KeyError: If the credential is not found in the file.
    """
    try:
        with open("credentials.json", "r") as file:
            all_credentials = json.load(file)

        if name not in all_credentials:
            raise KeyError(f"Credential '{name}' not found in credentials.json.")

        return all_credentials[name]
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in credentials.json.")
    except FileNotFoundError:
        raise FileNotFoundError("credentials.json file not found.")


def login_attempt(name):
    """
    Attempts to log in using stored credentials.

    Args:
        name (str): Name of the credential in the JSON file.
    """
    logging.info(f"Attempting login for credential: {name}")
    try:
        # Load the credentials by name
        credentials = load_credentials(name)

        username = credentials["username"]
        password = credentials["password"]

        # Placeholder for login logic
        logging.info(f"Logging in with username: {username}")
        # Implement your actual login logic here
    except KeyError as ke:
        logging.error(f"Missing key in credentials for '{name}': {ke}")
    except FileNotFoundError:
        logging.error("credentials.json file not found.")
    except Exception as e:
        logging.error(f"Login attempt failed for '{name}': {e}")





def logout():
    """
    Logs the user out.
    """
    logging.info("Logging out...")
    try:
        # Example: Send logout request to an API or invalidate session
        logging.info("Logout successful.")
    except Exception as e:
        logging.error(f"Logout failed: {e}")


def permission_request(permission):
    """
    Requests a specific system or application permission.

    Args:
        permission (str): Name of the permission to request.
    """
    logging.info(f"Requesting permission: {permission}")
    try:
        # Replace with actual permission logic
        logging.info(f"Permission '{permission}' granted.")
    except Exception as e:
        logging.error(f"Permission request failed: {e}")


def run_as_administrator(command):
    """
    Runs a command as Administrator.

    Args:
        command (str): The command to execute.
    """
    logging.info(f"Running command as Administrator: {command}")
    try:
        subprocess.run(["runas", "/user:Administrator", command], check=True)
        logging.info("Command executed successfully as Administrator.")
    except Exception as e:
        logging.error(f"Failed to execute command as Administrator: {e}")



def generate_otp(secret_key):
    """
    Generates a One-Time Password (OTP) using a secret key.

    Args:
        secret_key (str): Secret key for OTP generation.

    Returns:
        str: OTP.
    """
    totp = pyotp.TOTP(secret_key)
    otp = totp.now()
    logging.info(f"Generated OTP: {otp}")
    return otp

def verify_otp(secret_key, otp):
    """
    Verifies a One-Time Password (OTP) against a secret key.

    Args:
        secret_key (str): Secret key for OTP generation.
        otp (str): OTP to verify.

    Returns:
        bool: True if OTP is valid, False otherwise.
    """
    totp = pyotp.TOTP(secret_key)
    is_valid = totp.verify(otp)
    logging.info(f"OTP verification result: {is_valid}")
    return is_valid


logging.basicConfig(
    filename="security.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)



# Specialized Actions
def dropdown_select(driver=None, selector=None, value=None, by=By.CSS_SELECTOR, is_local=False, window_title=None):
    """
    Selects a value in a dropdown (web-based or local application).

    Args:
        driver (WebDriver, optional): Selenium WebDriver instance for web dropdowns.
        selector (str, optional): Selector for the web dropdown element.
        value (str or int): Value to select (visible text or index).
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        is_local (bool): Whether the dropdown is in a local application.
        window_title (str, optional): Title of the local application window.
    """
    try:
        if is_local and window_title:
            logging.info(f"Selecting '{value}' in dropdown in local application: {window_title}")
            #import pygetwindow as gw
            #import pywinauto
            #from pywinauto.application import Application
            # Locate window and dropdown control
            app = Application(backend="uia").connect(title=window_title)
            window = app.window(title=window_title)
            dropdown = window.child_window(title=selector, control_type="ComboBox")

            # Select dropdown value
            dropdown.select(value)
            logging.info(f"Successfully selected '{value}' in dropdown: {selector} (local).")

        elif driver and selector and value:
            logging.info(f"Selecting '{value}' in web dropdown: {selector}")
            element = driver.find_element(by, selector)
            dropdown = Select(element)

            if isinstance(value, int):
                dropdown.select_by_index(value)
            else:
                dropdown.select_by_visible_text(value)

            logging.info(f"Successfully selected '{value}' in web dropdown: {selector}.")
        else:
            raise ValueError("Invalid arguments. Provide either a web driver and selector or local application details.")
    except Exception as e:
        logging.error(f"Failed to select '{value}' in dropdown: {e}")

def checkbox_toggle(driver, selector, value, by=By.CSS_SELECTOR, max_retries=3):
    """
    Toggles a checkbox on or off with retries.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the checkbox element.
        value (bool): Desired state of the checkbox (True for checked, False for unchecked).
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        max_retries (int): Number of retry attempts.
    """
    def toggle_checkbox():
        checkbox = driver.find_element(by, selector)
        if checkbox.is_selected() != value:
            checkbox.click()

    retry_action(toggle_checkbox, max_retries=max_retries)


def slider_adjustment(driver, selector, value, by=By.CSS_SELECTOR):
    """
    Adjusts a slider to a specific value.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the slider element.
        value (int): Target value for the slider.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
    """
    logging.info(f"Adjusting slider {selector} to value {value}")
    try:
        slider = driver.find_element(by, selector)
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", slider, value)
        logging.info(f"Slider {selector} adjusted to {value}")
    except Exception as e:
        logging.error(f"Failed to adjust slider {selector}: {e}")


def calendar_interaction(driver, selector, date, by=By.CSS_SELECTOR, max_retries=3):
    """
    Interacts with a calendar to set a specific date with retries.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the calendar element.
        date (str): Date to set in the format 'YYYY-MM-DD'.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        max_retries (int): Number of retry attempts.
    """
    def set_date():
        calendar = driver.find_element(by, selector)
        calendar.clear()
        calendar.send_keys(date)

    retry_action(set_date, max_retries=max_retries)


def loop(actions, iterations, driver):
    """
    Loops through a series of actions with error recovery.

    Args:
        actions (list of callables): List of actions to execute.
        iterations (int): Number of times to repeat the loop.
        driver (WebDriver): Selenium WebDriver instance.
    """
    for i in range(iterations):
        logging.info(f"Executing loop iteration {i + 1}")
        for action in actions:
            try:
                action(driver)
            except Exception as e:
                logging.error(f"Error during loop iteration {i + 1}, action {action.__name__}: {e}")
                continue


def wait(duration):
    """
    Waits for a specified duration.

    Args:
        duration (int): Time to wait in seconds.
    """
    logging.info(f"Waiting for {duration} seconds...")
    try:
        time.sleep(duration)
        logging.info("Wait completed.")
    except Exception as e:
        logging.error(f"Error during wait: {e}")






def wait_for(driver, condition, selector, timeout=30, by=By.CSS_SELECTOR):
    """
    Waits for a specific condition to be met with logging.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        condition (callable): Condition to wait for (e.g., element_to_be_clickable).
        selector (str): Selector for the target element.
        timeout (int): Maximum wait time in seconds.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
    """
    logging.info(f"Waiting for condition '{condition.__name__}' on {selector}")
    try:
        WebDriverWait(driver, timeout).until(condition((by, selector)))
        logging.info(f"Condition '{condition.__name__}' met for {selector}")
    except Exception as e:
        logging.error(f"Condition '{condition.__name__}' not met for {selector} within {timeout} seconds: {e}")
        raise



#ERROR HANDLING & REALTIME ERORR HANDLING



def send_error_notification(error_message):
    """
    Sends an email notification with the error details.

    Args:
        error_message (str): The error message to include in the email.
    """
    try:
        smtp_server = "smtp.example.com"
        smtp_port = 587
        smtp_username = "your_email@example.com"
        smtp_password = "your_password"
        recipient_email = "admin@example.com"

        message = MIMEText(f"An error occurred:\n\n{error_message}")
        message["Subject"] = "Critical Error Notification"
        message["From"] = smtp_username
        message["To"] = recipient_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        logging.info("Error notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")


def retry_action_with_error_reporting(action, max_retries=3, wait_time=2, *args, **kwargs):
    """
    Retries an action if it fails and logs detailed error information.

    Args:
        action (callable): The function to execute.
        max_retries (int): Number of retry attempts.
        wait_time (int): Delay between retries in seconds.
        *args: Positional arguments for the action.
        **kwargs: Keyword arguments for the action.

    Returns:
        Any: The return value of the action if successful.
    """
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries} for action '{action.__name__}'")
            result = action(*args, **kwargs)
            logging.info(f"Action '{action.__name__}' succeeded on attempt {attempt + 1}")
            return result
        except Exception as e:
            error_message = f"Attempt {attempt + 1} failed for action '{action.__name__}': {e}"
            logging.error(error_message)
            if attempt == max_retries - 1:
                send_error_notification(error_message)
            time.sleep(wait_time)
    raise Exception(f"Action '{action.__name__}' failed after {max_retries} attempts.")

def loop_with_error_reporting(actions, iterations, driver):
    """
    Executes actions in a loop and generates a detailed error report.

    Args:
        actions (list of callables): List of actions to execute.
        iterations (int): Number of times to repeat the loop.
        driver (WebDriver): Selenium WebDriver instance.
    """
    error_summary = []

    for i in range(iterations):
        logging.info(f"Executing loop iteration {i + 1}")
        for action in actions:
            try:
                action(driver)
            except Exception as e:
                error_message = f"Error in loop iteration {i + 1}, action '{action.__name__}': {e}"
                logging.error(error_message)
                error_summary.append(error_message)

    # Log error summary
    if error_summary:
        logging.error("Error Summary:\n" + "\n".join(error_summary))
        send_error_notification("\n".join(error_summary))

def write_error_summary_to_file(error_summary, filename="error_summary.txt"):
    """
    Writes the error summary to a file.

    Args:
        error_summary (list): List of error messages.
        filename (str): Name of the file to write the summary to.
    """
    logging.info(f"Writing error summary to file: {filename}")
    try:
        with open(filename, "w") as file:
            file.write("Error Summary:\n")
            file.write("\n".join(error_summary))
        logging.info(f"Error summary written to {filename}.")
    except Exception as e:
        logging.error(f"Failed to write error summary to file: {e}")


class WorkflowExecutor:
    def __init__(self):
        self.driver = None
        self.app = None
        self.variables = {}
        self.status = "initialized"
        self.cipher = None
        self.browser_active = False
        self.last_url = None

    def execute_action(self, action):
        """
        Executes a normalized action with proper error handling and retries.
        """
        try:
            normalized_action = normalize_action(action)
            action_type = normalized_action['type']
            logging.info(f"Executing action: {action_type}")

            # Initialize browser if needed
            if action_type == 'open_selenium':
                self.cleanup_browser()
                self.driver = open_selenium(
                    browser=normalized_action.get('browser'),
                    headless=normalized_action.get('headless', False)
                )
                self.browser_active = True
                return

            # Check browser state before each action that requires it
            if action_type in ['url_navigation', 'element_interact']:
                if not self.ensure_browser_active():
                    # Reinitialize browser if needed
                    self.driver = open_selenium(
                        browser=normalized_action.get('browser', 'chrome'),
                        headless=normalized_action.get('headless', False)
                    )
                    self.browser_active = True
                    
                    # If this was a navigation action, we need to revisit the last URL
                    if self.last_url and action_type == 'element_interact':
                        self.driver.get(self.last_url)
                        try:
                            WebDriverWait(self.driver, 30).until(
                                lambda driver: driver.execute_script('return document.readyState') == 'complete'
                            )
                        except Exception as e:
                            logging.warning(f"Page load wait failed: {e}")

                if action_type == 'url_navigation':
                    url = normalized_action.get('url')
                    self.driver.get(url)
                    try:
                        WebDriverWait(self.driver, 30).until(
                            lambda driver: driver.execute_script('return document.readyState') == 'complete'
                        )
                        self.last_url = url
                    except Exception as e:
                        logging.warning(f"Page load wait failed: {e}")
                    
                elif action_type == 'element_interact':
                    try:
                        self.element_interact(
                            selector=normalized_action.get('selector'),
                            by=normalized_action.get('by', 'css'),
                            action=normalized_action.get('action', 'click'),
                            value=normalized_action.get('value', '')
                        )
                    except Exception as e:
                        logging.error(f"Element interaction failed: {e}")
                        self.take_debug_screenshot()
                        raise

            # Don't cleanup browser after each action anymore
            # Only cleanup on explicit close or error

        except Exception as e:
            self._handle_action_error(normalized_action, e)
            if isinstance(e, (selenium.common.exceptions.NoSuchWindowException, 
                            selenium.common.exceptions.WebDriverException)):
                self.cleanup_browser()
            raise

    def ensure_browser_active(self):
        """
        Ensures browser is active and reinitializes if needed.
        Returns True if browser is active, False if it needs to be reinitialized.
        """
        if not self.driver:
            logging.info("No browser session exists")
            return False
        
        try:
            # More robust check for browser state
            self.driver.current_window_handle  # This will throw an exception if browser is closed
            return True
        except Exception as e:
            logging.warning(f"Browser check failed: {e}. Reinitializing...")
            self.cleanup_browser()
            return False

    def cleanup_browser(self):
        """Safely cleanup browser resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.warning(f"Error during browser cleanup: {e}")
            finally:
                self.driver = None
                self.browser_active = False
                self.last_url = None

    def element_interact(self, selector, by='css', action='click', value=''):
        """Interacts with a web element with smart selector fallback."""
        if not self.ensure_browser_active():
            raise ValueError("Browser not initialized or not active")
        
        logging.info(f"Interacting with element: {selector} ({action})")
        try:
            # Progressive selector strategy
            selectors_to_try = [
                # Try ID first (most specific)
                (By.ID, selector if not selector.startswith('#') else selector[1:]),
                # Then CSS selector
                (By.CSS_SELECTOR, selector),
                # Then class name
                (By.CLASS_NAME, selector if not selector.startswith('.') else selector[1:]),
                # Then name attribute
                (By.NAME, selector),
                # Finally, try XPath as fallback
                (By.XPATH, f"//*[@id='{selector}']"),  # ID as XPath
                (By.XPATH, f"//*[contains(@class, '{selector}')]"),  # Class as XPath
                (By.XPATH, f"//*[@name='{selector}']"),  # Name as XPath
                (By.XPATH, selector if selector.startswith('//') else f"//*[contains(text(), '{selector}')]")  # Text content or custom XPath
            ]

            wait = WebDriverWait(self.driver, 20)
            element = None
            last_error = None

            for by_type, sel in selectors_to_try:
                try:
                    element = wait.until(lambda d: (
                        d.find_element(by_type, sel) and
                        d.find_element(by_type, sel).is_displayed() and
                        d.find_element(by_type, sel).is_enabled()
                    ) and d.find_element(by_type, sel))
                    logging.info(f"Element found using {by_type}: {sel}")
                    break
                except Exception as e:
                    last_error = e
                    continue

            if not element:
                raise last_error or Exception("Element not found with any selector strategy")

            # Scroll element into view
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.scrollIntoView({block: 'center', behavior: 'instant'});
            """, element)
            
            time.sleep(0.5)

            if action == 'click':
                try:
                    element.click()
                except:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                    except:
                        ActionChains(self.driver).move_to_element(element).click().perform()
            elif action == 'input':
                for _ in range(3):
                    try:
                        element.clear()
                        element.send_keys(Keys.CONTROL + "a")
                        element.send_keys(Keys.DELETE)
                        for char in value:
                            element.send_keys(char)
                            time.sleep(0.1)
                        
                        if element.get_attribute('value') == value:
                            break
                    except Exception as e:
                        logging.warning(f"Input attempt failed: {e}, retrying...")
                        time.sleep(1)

            return True

        except Exception as e:
            logging.error(f"Element interaction failed: {str(e)}")
            self.take_debug_screenshot()
            raise

    def take_debug_screenshot(self):
        """Takes a debug screenshot if possible."""
        if self.driver:
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshots/debug_{timestamp}.png"
                os.makedirs("error_screenshots", exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Debug screenshot saved: {screenshot_path}")
            except Exception as e:
                logging.error(f"Failed to save debug screenshot: {e}")

    def cleanup(self):
        """Cleanup all resources."""
        self.cleanup_browser()
        if self.app:
            try:
                self.app = None
            except Exception as e:
                logging.error(f"Error cleaning up application: {e}")
        logging.info("Workflow cleanup completed successfully")

    def _init_cipher(self):
        """Initialize the cipher for encryption/decryption."""
        try:
            with open('secret.key', 'rb') as key_file:
                key = key_file.read()
            self.cipher = Fernet(key)
        except Exception as e:
            logging.error(f"Failed to initialize cipher: {e}")
            raise

    def _decrypt_password(self, encrypted_password):
        """
        Decrypt password using the initialized cipher.
        """
        try:
            if not self.cipher:
                self._init_cipher()
            return self.cipher.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logging.error(f"Error decrypting password: {e}")
            raise

    def _load_encryption_key(self):
        """
        Load encryption key from file.
        """
        try:
            with open('secret.key', 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading encryption key: {e}")
            raise

    def open_selenium(self, browser=None, headless=False):
        """Opens a Selenium WebDriver instance using system default or specified browser."""
        logging.info(f"Opening browser (headless: {headless})")
        try:
            self.driver = open_selenium(browser, headless)
            logging.info("Browser opened successfully")
            return self.driver
        except Exception as e:
            logging.error(f"Failed to open browser: {str(e)}")
            raise

    def close_selenium(self):
        """Closes the Selenium WebDriver instance."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("Browser closed successfully")
            except Exception as e:
                logging.error(f"Failed to close browser: {e}")
            finally:
                self.driver = None

    def url_navigation(self, url):
        """Navigates to a URL."""
        logging.info(f"Navigating to: {url}")
        try:
            self.driver.get(url)
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            logging.info(f"Navigation successful: {url}")
        except Exception as e:
            logging.error(f"Navigation failed: {e}")
            raise

    def _get_credentials(self, credential_name):
        """
        Get credentials from credentials.json file.
        """
        try:
            with open('credentials.json', 'r') as f:
                credentials_list = json.load(f)
                for cred in credentials_list:
                    if cred['name'].lower() == credential_name.lower():
                        return cred
            return None
        except Exception as e:
            logging.error(f"Error loading credentials: {e}")
            return None

    def _handle_action_error(self, action, error):
        """
        Handles errors that occur during action execution.
        """
        logging.error(f"Error executing action: {action.get('type')}")
        logging.error(f"Error details: {str(error)}")
        if self.driver:
            try:
                # Take screenshot on error
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshots/error_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Error screenshot saved: {screenshot_path}")
            except Exception as screenshot_error:
                logging.error(f"Failed to save error screenshot: {screenshot_error}")

    def __del__(self):
        """
        Destructor to ensure resources are freed even if cleanup wasn't called.
        """
        try:
            if self.driver:
                self.close_selenium()
        except:
            pass  # Suppress errors in destructor

    def wait_for_page_load(self, timeout=30):
        """Waits for page load to complete with multiple conditions."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: driver.execute_script('''
                return document.readyState === "complete" && 
                       !document.querySelector(".loading") &&
                       (typeof jQuery === "undefined" || jQuery.active === 0) &&
                       (!window.angular || !angular.element(document).injector() || 
                        !angular.element(document).injector().get('$http').pendingRequests.length)
            '''))
            time.sleep(1)  # Additional small wait for any final rendering
        except Exception as e:
            logging.error(f"Page load wait timeout: {e}")
            self.take_debug_screenshot()
            raise

    def handle_desktop_application(self, action):
        """Enhanced desktop application handling with retries and checks."""
        try:
            app_path = action.get('application_path')
            arguments = action.get('arguments', '')
            working_dir = action.get('working_dir')
            
            # Ensure any existing instance is closed
            try:
                app = Application().connect(path=app_path)
                app.kill()
                time.sleep(1)
            except:
                pass  # No existing instance
            
            # Launch application with retry
            for attempt in range(3):
                try:
                    if working_dir:
                        process = subprocess.Popen(
                            [app_path] + shlex.split(arguments),
                            cwd=working_dir,
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    else:
                        process = subprocess.Popen(
                            [app_path] + shlex.split(arguments),
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    
                    # Wait for window to appear
                    start_time = time.time()
                    while time.time() - start_time < 30:
                        try:
                            app = Application().connect(process=process.pid)
                            window = app.top_window()
                            window.wait('ready', timeout=10)
                            logging.info(f"Application launched successfully: {app_path}")
                            return app
                        except Exception:
                            time.sleep(1)
                    
                    raise TimeoutError("Application window did not appear")
                    
                except Exception as e:
                    logging.warning(f"Launch attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            logging.error(f"Failed to launch application {app_path}: {e}")
            raise

    def desktop_input(self, window, control_id, text, retries=3):
        """More reliable desktop input with retries."""
        for attempt in range(retries):
            try:
                # Find control and ensure it's ready
                control = window[control_id]
                control.wait('ready', timeout=10)
                
                # Clear existing text
                control.set_text('')
                time.sleep(0.5)
                
                # Type text with delay
                for char in text:
                    control.type_keys(char, pause=0.1)
                
                # Verify input
                actual_text = control.get_value()
                if actual_text == text:
                    return True
                    
                logging.warning(f"Input verification failed. Expected: {text}, Got: {actual_text}")
                
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Desktop input failed after {retries} attempts: {e}")
                    raise
                time.sleep(1)
                
        return False

    def desktop_click(self, window, control_id, retries=3):
        """More reliable desktop clicking with retries."""
        for attempt in range(retries):
            try:
                control = window[control_id]
                control.wait('ready', timeout=10)
                control.click_input()
                time.sleep(0.5)  # Wait for click to register
                return True
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Desktop click failed after {retries} attempts: {e}")
                    raise
                time.sleep(1)

# Function to execute a workflow
def execute_workflow(workflow_data):
    """
    Main entry point for workflow execution.
    
    Args:
        workflow_data (dict): The workflow to execute
    """
    executor = WorkflowExecutor()
    try:
        executor.execute_workflow(workflow_data)
    except Exception as e:
        logging.error(f"Workflow execution failed: {str(e)}")
        raise


# Action Type Mappings
ACTION_TYPE_MAPPINGS = {
    # Browser Actions
    'open_browser': 'open_selenium',
    'launch_browser': 'open_selenium',
    'start_browser': 'open_selenium',
    
    'close_browser': 'close_selenium',
    'quit_browser': 'close_selenium',
    'exit_browser': 'close_selenium',
    
    'navigate': 'url_navigation',
    'go_to': 'url_navigation',
    'go_to_url': 'url_navigation',
    'browse_to': 'url_navigation',
    
    'type': 'typing_sequence',
    'input': 'typing_sequence',
    'input_text': 'typing_sequence',
    'enter_text': 'typing_sequence',
    
    'click': 'element_interact',
    'click_element': 'element_interact',
    'click_button': 'element_interact',
    
    # Mouse Actions
    'mouse_click': 'left_click',
    'click_at': 'left_click',
    
    'right_click_at': 'right_click',
    'context_click': 'right_click',
    
    'double_click': 'double_left_click',
    'dbl_click': 'double_left_click',
    
    'drag': 'mouse_drag',
    'drag_and_drop': 'mouse_drag',
    
    'hover': 'mouse_hover',
    'mouse_over': 'mouse_hover',
    
    'scroll': 'mouse_scroll',
    'scroll_page': 'mouse_scroll',
    
    'move_mouse': 'mouse_move',
    'move_cursor': 'mouse_move',
    
    # Keyboard Actions
    'press_key': 'keystroke',
    'key_press': 'keystroke',
    
    'press_keys': 'key_combination',
    'key_combo': 'key_combination',
    
    'type_text': 'typing_sequence',
    'send_keys': 'typing_sequence',
    
    'special_key': 'special_key_press',
    'system_key': 'special_key_press',
    
    'shortcut': 'shortcut_use',
    'keyboard_shortcut': 'shortcut_use',
    
    # File Operations
    'open_file': 'file_open',
    'load_file': 'file_open',
    
    'save_file': 'file_save',
    'write_file': 'file_save',
    
    'delete_file': 'file_delete',
    'remove_file': 'file_delete',
    
    'rename_file': 'file_rename',
    'move_file': 'file_move',
    'copy_file': 'file_copy',
    'upload': 'file_upload',
    'download': 'file_download',
    
    # Wait Actions
    'sleep': 'wait',
    'pause': 'wait',
    'delay': 'wait',
    
    'wait_until': 'wait_for',
    'wait_for_element': 'wait_for',
    
    # Email Actions
    'read_email': 'email_read',
    'check_email': 'email_read',
    
    'write_email': 'email_write',
    'compose_email': 'email_write',
    
    'send_email': 'email_send',
    'email': 'email_send',
    
    # Application Actions
    'open_app': 'open_application',
    'launch_app': 'open_application',
    'start_app': 'open_application',
    'run_app': 'open_application'
}  # Remove the extra closing brace

def normalize_action(action):
    """
    Normalizes action type and parameters for consistent handling.
    """
    if not isinstance(action, dict):
        raise ValueError("Action must be a dictionary")
        
    # Make a copy to avoid modifying the original
    normalized = action.copy()
    
    # Normalize action type
    action_type = normalized.get('type', '').lower()
    normalized['type'] = ACTION_TYPE_MAPPINGS.get(action_type, action_type)
    
    return normalized

def wait(duration):
    """
    Waits for a specified duration.

    Args:
        duration (int): Time to wait in seconds.
    """
    logging.info(f"Waiting for {duration} seconds...")
    try:
        time.sleep(duration)
        logging.info("Wait completed.")
    except Exception as e:
        logging.error(f"Error during wait: {e}")

def take_error_screenshot(driver, error_type="error"):
    """
    Takes a screenshot when an error occurs.
    
    Args:
        driver: WebDriver instance
        error_type (str): Type of error for filename
    
    Returns:
        str: Path to screenshot or None if failed
    """
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_path = f"error_screenshots/{error_type}_{timestamp}.png"
        os.makedirs("error_screenshots", exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logging.info(f"Error screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"Failed to save error screenshot: {e}")
        return None

def email_write_gmail(to, subject, body, cc=None, bcc=None):
    """
    Composes and drafts an email in Gmail using the Gmail API.

    Args:
        to (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.
    """
    try:
        # Load credentials from token.json
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.compose'])
        service = build('gmail', 'v1', credentials=creds)

        # Create the email message
        message = create_gmail_message(to, subject, body, cc, bcc)

        # Create a draft in Gmail
        draft = service.users().drafts().create(userId='me', body=message).execute()
        logging.info(f"Draft created successfully with ID: {draft['id']}")
    except Exception as e:
        logging.error(f"Failed to compose Gmail draft: {e}")

def email_send_gmail(to_address, subject, body, smtp_server=None, smtp_port=None, smtp_username=None, smtp_password=None):
    """
    Sends an email using Gmail API.
    """
    logging.info(f"Sending email to {to_address} via Gmail API")
    try:
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.send'])
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(body)
        message['to'] = to_address
        message['subject'] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")




















def file_move(source_path, destination_path):
    """
    Moves a file to a new location.

    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    logging.info(f"Moving file from {source_path} to {destination_path}")
    try:
        shutil.move(source_path, destination_path)
        logging.info("File moved successfully.")
    except Exception as e:
        logging.error(f"Failed to move file: {e}")

def file_copy(source_path, destination_path):
    """
    Copies a file to a new location.

    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    logging.info(f"Copying file from {source_path} to {destination_path}")
    try:
        shutil.copy(source_path, destination_path)
        logging.info("File copied successfully.")
    except Exception as e:
        logging.error(f"Failed to copy file: {e}")

def file_upload(file_path):
    """
    Uploads a file by typing its path and pressing Enter.

    Args:
        file_path (str): Path to the file to upload.
    """
    logging.info(f"Uploading file: {file_path}")
    pyautogui.write(file_path)
    pyautogui.press('enter')
    logging.info("File upload completed.")

def file_download(file_url, destination_path):
    """
    Downloads a file from a URL to a specified destination.

    Args:
        file_url (str): URL of the file to download.
        destination_path (str): Path to save the downloaded file.
    """
    logging.info(f"Downloading file from {file_url} to {destination_path}")
    try:
        response = requests.get(file_url, stream=True)
        with open(destination_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info("File downloaded successfully.")
    except Exception as e:
        logging.error(f"Failed to download file: {e}")




# Browser Actions
def detect_default_browser():
    """
    Detects the default system browser.
    
    Returns:
        str: Browser identifier ('chrome', 'firefox', 'ie', or 'edge')
    """
    import winreg
    try:
        # Check Windows registry for default browser
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
            browser_reg = winreg.QueryValueEx(key, "ProgId")[0]
            
        browser_map = {
            'ChromeHTML': 'chrome',
            'FirefoxURL': 'firefox',
            'IE.HTTP': 'ie',
            'MSEdgeHTM': 'edge'
        }
        
        # Extract browser name from registry value
        for key, value in browser_map.items():
            if key.lower() in browser_reg.lower():
                return value
                
        return 'chrome'  # Default to Chrome if detection fails
    except Exception as e:
        logging.warning(f"Failed to detect default browser: {e}. Defaulting to Chrome.")
        return 'chrome'

def open_selenium(browser=None, headless=False):
    """
    Opens a Selenium WebDriver instance using the system's default browser or specified browser.
    
    Args:
        browser (str, optional): Specific browser to use ('chrome', 'firefox', 'ie', 'edge').
                               If None, uses system default.
        headless (bool): Whether to run the browser in headless mode.
        
    Returns:
        WebDriver: Selenium WebDriver instance
    """
    if browser is None:
        browser = detect_default_browser()
        
    logging.info(f"Initializing {browser} browser (headless: {headless})")
    
    try:
        if browser == 'chrome':
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-gpu')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Chrome driver: {e}")
                raise
                
        elif browser == 'firefox':
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            
            try:
                driver = webdriver.Firefox(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Firefox driver: {e}")
                raise
                
        elif browser == 'ie':
            options = webdriver.IeOptions()
            options.ignore_protected_mode_settings = True
            options.ignore_zoom_level = True
            options.require_window_focus = False
            
            try:
                driver = webdriver.Ie(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize IE driver: {e}")
                raise
                
        elif browser == 'edge':
            options = webdriver.EdgeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--start-maximized')
            
            try:
                driver = webdriver.Edge(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize Edge driver: {e}")
                raise
                
        else:
            raise ValueError(f"Unsupported browser type: {browser}")
        
        # Set common configurations
        driver.set_page_load_timeout(30)
        if not headless:
            driver.maximize_window()
            
        logging.info(f"Successfully initialized {browser} browser")
        return driver
        
    except Exception as e:
        error_msg = f"Failed to initialize browser {browser}: {str(e)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

def close_selenium(driver):
    """
    Closes the Selenium WebDriver instance.

    Args:
        driver (WebDriver): Selenium WebDriver instance to close.
    """
    logging.info("Closing Selenium browser.")
    try:
        driver.quit()
        logging.info("Browser closed successfully.")
    except Exception as e:
        logging.error(f"Failed to close browser: {e}")

def url_navigation(driver, url):
    """
    Navigates the browser to the specified URL.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        url (str): URL to navigate to.
    """
    logging.info(f"Navigating to URL: {url}")
    try:
        driver.get(url)
        logging.info(f"Navigation to {url} completed successfully.")
    except Exception as e:
        logging.error(f"Failed to navigate to {url}: {e}")




def element_interact(driver, selector, by='xpath', action='click', value=''):
    """
    Unified element interaction function.
    """
    logging.info(f"Interacting with element: {selector} ({action})")
    try:
        by = getattr(By, by.upper())
        wait = WebDriverWait(driver, 20)
        
        # Element location logic
        element = wait.until(EC.presence_of_element_located((by, selector)))
        
        # Scroll and wait
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        
        # Action execution
        if action == 'click':
            try:
                element.click()
            except Exception:
                driver.execute_script("arguments[0].click();", element)
        elif action == 'input':
            element.clear()
            for char in value:
                element.send_keys(char)
                time.sleep(0.1)
        
        return True
    except Exception as e:
        logging.error(f"Element interaction failed: {str(e)}")
        take_error_screenshot(driver, "element_interaction")
        raise


def search_query(driver, search_box_selector, query, by=By.CSS_SELECTOR):
    """
    Performs a search query by typing in a search box and submitting.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        search_box_selector (str): Selector for the search box element.
        query (str): Search query to perform.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Performing search query: '{query}' in element: {search_box_selector} (by {by}")
    try:
        search_box = driver.find_element(by, search_box_selector)
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        logging.info("Search query executed successfully.")
    except Exception as e:
        logging.error(f"Failed to perform search query '{query}': {e}")

#new from GPT?? SELENIUM CONTINUED
def dynamic_interact(driver, actions, wait_time=5):
    """
    Executes a sequence of dynamic actions on the browser.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        actions (list of dict): List of actions with selectors and commands.
        wait_time (int): Wait time in seconds between actions.
    """
    logging.info("Executing dynamic interactions.")
    try:
        for action in actions:
            action_type = action.get("action_type")
            selector = action.get("selector")
            by = action.get("by", By.CSS_SELECTOR)

            if action_type == "click":
                logging.info(f"Clicking element: {selector}")
                driver.find_element(by, selector).click()
            elif action_type == "input":
                value = action.get("value", "")
                logging.info(f"Inputting '{value}' into element: {selector}")
                element = driver.find_element(by, selector)
                element.clear()
                element.send_keys(value)
            else:  # Fixed indentation
                logging.warning(f"Unsupported action type: {action_type}")

            time.sleep(wait_time)
        logging.info("Dynamic interactions completed successfully.")
    except Exception as e:
        logging.error(f"Failed during dynamic interactions: {e}")
def scroll_to_element(driver, selector, by=By.CSS_SELECTOR):
    """
    Scrolls the browser window until the specified element is in view.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the element to scroll to.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Scrolling to element: {selector} (by {by})")
    try:
        element = driver.find_element(by, selector)
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)
        logging.info(f"Scrolled to element: {selector}")
    except Exception as e:
        logging.error(f"Failed to scroll to element {selector}: {e}")

def select_dropdown_option(driver, selector, option_text, by=By.CSS_SELECTOR):
    """
    Selects an option from a dropdown by visible text.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the dropdown element.
        option_text (str): The visible text of the option to select.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Selecting '{option_text}' from dropdown: {selector} (by {by}")
    try:
        #from selenium.webdriver.support.ui import Select
        dropdown = Select(driver.find_element(by, selector))
        dropdown.select_by_visible_text(option_text)
        logging.info(f"Option '{option_text}' selected successfully.")
    except Exception as e:
        logging.error(f"Failed to select option '{option_text}' from dropdown {selector}: {e}")

def switch_to_iframe(driver, selector, by=By.CSS_SELECTOR):
    """
    Switches the context to an iframe.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the iframe element.
        by (str): Selenium By strategy (e.g., By.CSS_SELECTOR, By.XPATH).
    """
    logging.info(f"Switching to iframe: {selector} (by {by})")
    try:
        iframe = driver.find_element(by, selector)
        driver.switch_to.frame(iframe)
        logging.info("Switched to iframe successfully.")
    except Exception as e:
        logging.error(f"Failed to switch to iframe {selector}: {e}")

def switch_to_default_content(driver):
    """
    Switches the context back to the main document from an iframe.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Switching to default content.")
    try:
        driver.switch_to.default_content()
        logging.info("Switched to default content successfully.")
    except Exception as e:
        logging.error(f"Failed to switch to default content: {e}")


def retry_action(action_func, max_retries=3, wait_time=2):
    """
    Retries an action with exponential backoff and proper error handling.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return action_func()
        except Exception as e:
            last_error = e
            if attempt == max_retries - 1:
                logging.error(f"Action failed after {max_retries} attempts: {str(e)}")
                raise last_error
            
            wait_duration = wait_time * (2 ** attempt)  # Exponential backoff
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_duration} seconds...")
            time.sleep(wait_duration)
            
            # If this is a browser-related error, we should force cleanup
            if isinstance(e, (selenium.common.exceptions.NoSuchWindowException, 
                selenium.common.exceptions.WebDriverException)):
                logging.info("Browser session lost. Will reinitialize on next attempt.")


def wait_for_element(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    """
    Waits for an element to be present on the page.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the element.
        by (str): Selenium By strategy (e.g., CSS_SELECTOR, XPATH).
        timeout (int): Maximum wait time in seconds.

    Returns:
        WebElement: The located element.

    Raises:
        TimeoutException: If the element is not found within the timeout.
    """
    logging.info(f"Waiting for element: {selector} (by {by}) for up to {timeout} seconds.")
    try:
        element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
        logging.info(f"Element located: {selector}")
        return element
    except Exception as e:
        logging.error(f"Failed to locate element {selector} within {timeout} seconds: {e}")
        raise


def restart_driver(driver, browser='chrome', headless=False):
    """
    Restarts the Selenium WebDriver in case of failure.

    Args:
        driver (WebDriver): The current driver instance to close and restart.
        browser (str): Browser type ('chrome' or 'firefox').
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        WebDriver: A new driver instance.
    """
    logging.info("Restarting WebDriver due to failure.")
    try:
        close_selenium(driver)
    except Exception as e:
        logging.warning(f"Failed to gracefully close driver: {e}")

    return open_selenium(browser, headless)


# Communication and Actions
def email_read(platform='outlook', criteria=None):
    logging.info(f"Reading emails on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []

def email_write(platform='outlook', to=None, subject=None, body=None, cc=None, bcc=None):
    """
    Composes an email draft dynamically for Outlook or Gmail.

    Args:
        platform (str): Email platform ('outlook' or 'gmail').
        to (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.
    """
    try:
        if platform == 'gmail':
            email_write_gmail(to, subject, body, cc, bcc)
        elif platform == 'outlook':
            email_write_draft(to, subject, body, cc, bcc)
        else:
            logging.error(f"Unsupported platform: {platform}")
    except Exception as e:
        logging.error(f"Error composing email draft: {e}")



def email_send(to_address, subject, body, smtp_server=None, smtp_port=None, smtp_username=None, smtp_password=None, platform='outlook'):
    logging.info(f"Sending email to {to_address} via {platform}")
    try:
        if platform == 'outlook':
            send_email_outlook(to_address, subject, body)
        elif platform == 'gmail':
            if smtp_server and smtp_port and smtp_username and smtp_password:
                email_send_gmail(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password)
            else:
                raise ValueError("Gmail requires SMTP server, port, username, and password.")
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def scan_inbox(criteria, platform='outlook'):
    logging.info(f"Scanning inbox on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to scan inbox: {e}")
        return []

def email_search(criteria, platform='outlook'):
    logging.info(f"Searching emails on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)
        elif platform == 'gmail':
            return email_read_gmail(criteria)
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Failed to search emails: {e}")
        return []

#OUTLOOK IMPLEMENTATION
def email_read_outlook(criteria=None):
    logging.info(f"Reading emails with criteria: {criteria}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # Inbox
        messages = inbox.Items
        emails = []
        for message in messages:
            if criteria:
                if "subject" in criteria and criteria["subject"].lower() not in message.Subject.lower():
                    continue
                if "sender" in criteria and criteria["sender"].lower() not in message.SenderEmailAddress.lower():
                    continue
            emails.append({
                "subject": message.Subject,
                "body": message.Body,
                "sender": message.SenderName,
                "received_time": message.ReceivedTime
            })
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []

def email_write_draft(to, subject, body, cc=None, bcc=None):
    logging.info(f"Composing email draft to {to}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = to
        mail.Subject = subject
        mail.Body = body
        if cc:
            mail.CC = cc
        if bcc:
            mail.BCC = bcc
        mail.Display()
        logging.info("Draft created successfully.")
    except Exception as e:
        logging.error(f"Failed to compose email: {e}")



def send_email_outlook(to_address, subject, body):
    """
    Sends an email using Microsoft Outlook via COM.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
    """
    try:
        # Create an Outlook application instance
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0: Mail item

        # Set email properties
        mail.To = to_address
        mail.Subject = subject
        mail.Body = body

        # Send the email
        mail.Send()
        logging.info(f"Email sent successfully to {to_address} via Outlook.")
    except Exception as e:
        logging.error(f"Failed to send email via Outlook: {e}")



def scan_inbox_outlook(criteria):
    logging.info(f"Scanning inbox with criteria: {criteria}")
    return email_read_outlook(criteria)

#GMAIL IMPLEMENTATION

def email_read_gmail(criteria=None):
    """
    Reads emails from Gmail using the Gmail API.
    
    Args:
        criteria (dict, optional): Search criteria for filtering emails
        
    Returns:
        list: List of matching emails
    """
    logging.info(f"Reading emails from Gmail with criteria: {criteria}")
    try:
        creds = Credentials.from_authorized_user_file('token.json', 
            ['https://www.googleapis.com/auth/gmail.readonly'])
        service = build('gmail', 'v1', credentials=creds)
        query = ""
        if criteria:
            if "subject" in criteria:
                query += f"subject:{criteria['subject']} "
            if "sender" in criteria:
                query += f"from:{criteria['sender']} "
        
        results = service.users().messages().list(userId='me', q=query).execute()
        emails = []
        
        for msg in results.get('messages', []):
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_data.get('payload', {}).get('headers', [])
            emails.append({
                "subject": next((h['value'] for h in headers if h['name'] == 'Subject'), ''),
                "snippet": msg_data.get('snippet', '')
            })
            
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
        
    except Exception as e:
        logging.error(f"Failed to read emails: {e}")
        return []


def email_read_gmail_imap(username, password, criteria=None):
    logging.info(f"Reading emails via IMAP with criteria: {criteria}")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")
        search_query = "ALL"
        if criteria:
            if "subject" in criteria:
                search_query = f'SUBJECT "{criteria["subject"]}"'
            if "sender" in criteria:
                search_query = f'FROM "{criteria["sender"]}"'
        _, data = mail.search(None, search_query)
        emails = []
        for eid in data[0].split():
            _, msg_data = mail.fetch(eid, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    emails.append({
                        "subject": msg["subject"],
                        "sender": msg["from"],
                        "body": msg.get_payload(decode=True).decode()
                    })
        logging.info(f"Retrieved {len(emails)} emails.")
        return emails
    except Exception as e:
        logging.error(f"Failed to read emails via IMAP: {e}")
        return []


def create_gmail_message(to, subject, body, cc=None, bcc=None):
    """
    Creates a Gmail API-compatible message in base64 format.

    Args:
        to (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.

    Returns:
        dict: A dictionary containing the 'raw' message ready for Gmail API.
    """
    try:
        # Create the MIMEText email object
        message = MIMEText(body)
        message['To'] = to
        message['Subject'] = subject
        if cc:
            message['Cc'] = cc
        if bcc:
            message['Bcc'] = bcc

        # Encode the message in base64
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw}
    except Exception as e:
        logging.error(f"Failed to create Gmail message: {e}")
        raise


def email_send_with_attachments(to_address, subject, body, attachments, smtp_server, smtp_port, smtp_username, smtp_password):
    """
    Sends an email with multiple attachments using SMTP.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
        attachments (list): List of file paths to attach.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
    """
    logging.info(f"Sending email to {to_address} with {len(attachments)} attachments")
    try:
        message = MIMEMultipart()
        message["From"] = smtp_username
        message["To"] = to_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        for file_path in attachments:
            try:
                with open(file_path, "rb") as file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={file_path}")
                    message.attach(part)
            except FileNotFoundError:
                logging.error(f"Attachment not found: {file_path}")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_address, message.as_string())
        logging.info("Email with attachments sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email with attachments: {e}")

def read_attachments_outlook(criteria=None, download_folder="downloads"):
    """
    Reads emails and downloads attachments based on criteria.

    Args:
        criteria (dict, optional): Search criteria like sender or subject.
        download_folder (str): Folder to save downloaded attachments.
    """
    logging.info(f"Reading emails and downloading attachments to {download_folder}")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # Inbox
        messages = inbox.Items
        for message in messages:
            if criteria:
                if "subject" in criteria and criteria["subject"].lower() not in message.Subject.lower():
                    continue
                if "sender" in criteria and criteria["sender"].lower() not in message.SenderEmailAddress.lower():
                    continue

            for attachment in message.Attachments:
                file_path = os.path.join(download_folder, str(attachment))
                attachment.SaveAsFile(file_path)
                logging.info(f"Downloaded attachment: {file_path}")
    except Exception as e:
        logging.error(f"Failed to download attachments: {e}")

def email_search_advanced(platform='outlook', criteria=None):
    """
    Searches emails with advanced criteria such as date range and keywords.

    Args:
        platform (str): Email platform ('outlook' or 'gmail').
        criteria (dict): Search criteria (e.g., subject, sender, date_range).

    Returns:
        list: List of matching emails.
    """
    logging.info(f"Performing advanced search on {platform} with criteria: {criteria}")
    try:
        if platform == 'outlook':
            return email_read_outlook(criteria)  # Add advanced filtering logic in email_read_outlook
        elif platform == 'gmail':
            return email_read_gmail(criteria)  # Update Gmail search logic to handle date ranges
        else:
            raise ValueError("Unsupported platform. Use 'outlook' or 'gmail'.")
    except Exception as e:
        logging.error(f"Advanced search failed: {e}")
        return []

def retry_email_send(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password, retries=3):
    """
    Retries sending an email if it fails.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        retries (int): Number of retry attempts.
    """
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Attempt {attempt} to send email to {to_address}")
            email_send_with_attachments(to_address, subject, body, [], smtp_server, smtp_port, smtp_username, smtp_password)
            logging.info("Email sent successfully.")
            break
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed: {e}")
            if attempt == retries:
                logging.error("All attempts to send email failed.")



def schedule_email(to_address, subject, body, smtp_server, smtp_port, smtp_username, smtp_password, delay):
    """
    Schedules an email to be sent after a delay.

    Args:
        to_address (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        delay (int): Delay in seconds before sending the email.
    """
    logging.info(f"Scheduling email to {to_address} in {delay} seconds.")
    Timer(delay, email_send_with_attachments, args=(to_address, subject, body, [], smtp_server, smtp_port, smtp_username, smtp_password)).start()


# Interaction with Media


def media_play(file_path=None):
    """
    Plays media from a local file or resumes browser-based media.

    Args:
        file_path (str, optional): Path to the local media file. If None, resumes browser media.
    """
    if file_path:
        logging.info(f"Playing local media file: {file_path}")
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.call(('open' if os.name == 'darwin' else 'xdg-open', file_path))
            logging.info("Media playback started successfully.")
        except Exception as e:
            logging.error(f"Failed to play media: {e}")
    else:
        logging.info("Playing browser-based media.")
        pyautogui.press("playpause")  # Play/Pause media in browser or system


def media_pause():
    """
    Pauses browser-based media or system-level media.
    """
    logging.info("Pausing media...")
    try:
        pyautogui.press("playpause")  # Universal pause button
        logging.info("Media paused successfully.")
    except Exception as e:
        logging.error(f"Failed to pause media: {e}")





def media_seek(position):
    """
    Seeks media to a specific position in seconds.

    Args:
        position (int): Position in seconds to seek to.
    """
    logging.info(f"Seeking to position {position} seconds...")
    try:
        pyautogui.press("k")  # YouTube shortcut for pausing
        pyautogui.typewrite(str(position))  # Type the position
        pyautogui.press("enter")  # Confirm position change
        logging.info(f"Media seeked to {position} seconds.")
    except Exception as e:
        logging.error(f"Failed to seek media position: {e}")


def media_volume_change(volume):
    """
    Changes the system volume to a specified level.

    Args:
        volume (int): Volume level (0-100).
    """
    logging.info(f"Changing volume to {volume}...")
    try:
        if 0 <= volume <= 100:
            for _ in range(50):  # Reset to zero volume
                pyautogui.press("volumedown")
            for _ in range(volume // 2):  # Increase to the desired level (each press ~2%)
                pyautogui.press("volumeup")
            logging.info(f"Volume set to {volume}.")
        else:
            logging.error("Volume level must be between 0 and 100.")
    except Exception as e:
        logging.error(f"Failed to change volume: {e}")

#additional media control BROWSER and MUTE
def media_mute():
    """
    Toggles mute for the system or browser-based media.
    """
    logging.info("Toggling mute...")
    try:
        pyautogui.press("volumemute")
        logging.info("Mute toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle mute: {e}")

def browser_media_play_pause(driver):
    """
    Toggles play/pause for browser-based media (e.g., YouTube, Netflix).

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling play/pause for browser media...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("arguments[0].pause()" if video_element.is_playing else "arguments[0].play()", video_element)
        logging.info("Media play/pause toggled in browser.")
    except Exception as e:
        logging.error(f"Failed to control browser media: {e}")

def media_next_track():
    """
    Skips to the next media track for browser-based or system-level playback.
    """
    logging.info("Skipping to the next track...")
    try:
        pyautogui.press("nexttrack")  # Universal system shortcut
        logging.info("Skipped to the next track.")
    except Exception as e:
        logging.error(f"Failed to skip to the next track: {e}")

def media_previous_track():
    """
    Goes back to the previous media track for browser-based or system-level playback.
    """
    logging.info("Going back to the previous track...")
    try:
        pyautogui.press("prevtrack")  # Universal system shortcut
        logging.info("Went back to the previous track.")
    except Exception as e:
        logging.error(f"Failed to go back to the previous track: {e}")

def toggle_subtitles_browser(driver):
    """
    Toggles subtitles for media in a browser-based platform.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling subtitles in browser...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const player = document.querySelector('video');
            if (player.textTracks.length > 0) {
                const track = player.textTracks[0];
                track.mode = track.mode === 'showing' ? 'disabled' : 'showing';
            }
        """)
        logging.info("Subtitles toggled successfully in browser.")
    except Exception as e:
        logging.error(f"Failed to toggle subtitles: {e}")

def adjust_playback_speed(driver, speed):
    """
    Adjusts playback speed for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        speed (float): Desired playback speed (e.g., 1.5 for 1.5x speed).
    """
    logging.info(f"Setting playback speed to {speed}x...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script(f"arguments[0].playbackRate = {speed};", video_element)
        logging.info(f"Playback speed set to {speed}x.")
    except Exception as e:
        logging.error(f"Failed to adjust playback speed: {e}")

def toggle_media_loop(driver):
    """
    Toggles looping for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling media loop...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("arguments[0].loop = !arguments[0].loop;", video_element)
        logging.info("Media loop toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle media loop: {e}")

def toggle_fullscreen(driver):
    """
    Toggles fullscreen mode for browser-based media.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    logging.info("Toggling fullscreen mode...")
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const player = arguments[0];
            if (!document.fullscreenElement) {
                player.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        """, video_element)
        logging.info("Fullscreen mode toggled successfully.")
    except Exception as e:
        logging.error(f"Failed to toggle fullscreen mode: {e}")


def media_volume_fade(volume, fade_time=5):
    """
    Fades volume in or out over a specified duration.

    Args:
        volume (int): Target volume level (0-100).
        fade_time (int): Duration of fade in seconds.
    """
    logging.info(f"Fading volume to {volume} over {fade_time} seconds...")
    try:
        current_volume = 0  # Assuming starting at 0
        step = volume // (fade_time * 2)  # Adjust step size based on fade time

        for level in range(0, volume + 1, step):
            media_volume_change(level)
            time.sleep(0.5)  # Smooth transition
        logging.info(f"Volume faded to {volume}.")
    except Exception as e:
        logging.error(f"Failed to fade volume: {e}")

def media_restart():
    """
    Restarts media playback from the beginning.
    """
    logging.info("Restarting media playback...")
    try:
        pyautogui.press("0")  # YouTube shortcut to go to the beginning
        logging.info("Media playback restarted.")
    except Exception as e:
        logging.error(f"Failed to restart media playback: {e}")


#Monitor Support & Multi-Monitor Setup Info (For media but reuseable)

def get_monitor_info():
    """
    Retrieves information about all connected monitors.

    Returns:
        list: A list of dictionaries with monitor details (width, height, x, y).
    """
    monitors = []
    for monitor in get_monitors():
        monitors.append({
            "width": monitor.width,
            "height": monitor.height,
            "x": monitor.x,
            "y": monitor.y
        })
    logging.info(f"Detected monitors: {monitors}")
    return monitors



def move_window_to_monitor(window_title, monitor_index):
    """
    Moves a window to a specified monitor.

    Args:
        window_title (str): Title of the window to move.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Moving '{window_title}' to monitor {monitor_index}")
    try:
        monitors = get_monitor_info()
        if monitor_index >= len(monitors):
            logging.error(f"Monitor index {monitor_index} is out of range.")
            return

        target_monitor = monitors[monitor_index]
        windows = gw.getWindowsWithTitle(window_title)

        if windows:
            window = windows[0]
            window.moveTo(target_monitor['x'], target_monitor['y'])
            logging.info(f"Window '{window_title}' moved to monitor {monitor_index}.")
        else:
            logging.error(f"Window '{window_title}' not found.")
    except Exception as e:
        logging.error(f"Failed to move window: {e}")

def fullscreen_on_monitor(window_title, monitor_index):
    """
    Toggles fullscreen for a window on a specific monitor.

    Args:
        window_title (str): Title of the window to fullscreen.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Toggling fullscreen for '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        pyautogui.hotkey("alt", "enter")  # Simulates fullscreen shortcut
        logging.info(f"Fullscreen toggled for '{window_title}' on monitor {monitor_index}.")
    except Exception as e:
        logging.error(f"Failed to toggle fullscreen: {e}")

def maximize_window_on_monitor(window_title, monitor_index):
    """
    Maximizes a window on a specific monitor.

    Args:
        window_title (str): Title of the window to maximize.
        monitor_index (int): Index of the target monitor (0-based).
    """
    logging.info(f"Maximizing '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        windows = gw.getWindowsWithTitle(window_title)
        if windows:
            window = windows[0]
            window.maximize()
            logging.info(f"Window '{window_title}' maximized on monitor {monitor_index}.")
        else:
            logging.error(f"Window '{window_title}' not found.")
    except Exception as e:
        logging.error(f"Failed to maximize window: {e}")

def control_media_on_monitor(window_title, monitor_index, action):
    """
    Controls media playback on a specific monitor.

    Args:
        window_title (str): Title of the media window.
        monitor_index (int): Index of the target monitor.
        action (str): Media control action ('play', 'pause', 'next', 'prev').
    """
    logging.info(f"Performing '{action}' on '{window_title}' on monitor {monitor_index}")
    try:
        move_window_to_monitor(window_title, monitor_index)
        if action == "play":
            pyautogui.press("playpause")
        elif action == "pause":
            pyautogui.press("playpause")
        elif action == "next":
            pyautogui.press("nexttrack")
        elif action == "prev":
            pyautogui.press("prevtrack")
        else:
            logging.error(f"Unsupported action: {action}")
        logging.info(f"Action '{action}' completed on '{window_title}' on monitor {monitor_index}.")
    except Exception as e:
        logging.error(f"Failed to perform action: {e}")






# Security and Authentication Actions

# Load encryption key (generate and save this once; reuse for decryption)
def load_encryption_key():
    """
    Loads the encryption key from a file.
    Returns:
        str: Encryption key.
    """
    try:
        with open("encryption.key", "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        logging.error("Encryption key file not found. Generate it using Fernet.")
        raise

def decrypt_password(encrypted_password):
    """
    Decrypts an encrypted password.

    Args:
        encrypted_password (str): Encrypted password in bytes.

    Returns:
        str: Decrypted password.
    """
    try:
        key = load_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode()).decode()
        logging.info("Password decrypted successfully.")
        return decrypted
    except Exception as e:
        logging.error(f"Failed to decrypt password: {e}")
        raise


def load_credentials(name):
    """
    Loads credentials from a JSON file based on the provided name.

    Args:
        name (str): The name of the credential to retrieve.

    Returns:
        dict: A dictionary containing 'username' and 'password'.

    Raises:
        KeyError: If the credential is not found in the file.
    """
    try:
        with open("credentials.json", "r") as file:
            all_credentials = json.load(file)

        if name not in all_credentials:
            raise KeyError(f"Credential '{name}' not found in credentials.json.")

        return all_credentials[name]
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in credentials.json.")
    except FileNotFoundError:
        raise FileNotFoundError("credentials.json file not found.")


def login_attempt(name):
    """
    Attempts to log in using stored credentials.

    Args:
        name (str): Name of the credential in the JSON file.
    """
    logging.info(f"Attempting login for credential: {name}")
    try:
        # Load the credentials by name
        credentials = load_credentials(name)

        username = credentials["username"]
        password = credentials["password"]

        # Placeholder for login logic
        logging.info(f"Logging in with username: {username}")
        # Implement your actual login logic here
    except KeyError as ke:
        logging.error(f"Missing key in credentials for '{name}': {ke}")
    except FileNotFoundError:
        logging.error("credentials.json file not found.")
    except Exception as e:
        logging.error(f"Login attempt failed for '{name}': {e}")





def logout():
    """
    Logs the user out.
    """
    logging.info("Logging out...")
    try:
        # Example: Send logout request to an API or invalidate session
        logging.info("Logout successful.")
    except Exception as e:
        logging.error(f"Logout failed: {e}")


def permission_request(permission):
    """
    Requests a specific system or application permission.

    Args:
        permission (str): Name of the permission to request.
    """
    logging.info(f"Requesting permission: {permission}")
    try:
        # Replace with actual permission logic
        logging.info(f"Permission '{permission}' granted.")
    except Exception as e:
        logging.error(f"Permission request failed: {e}")


def run_as_administrator(command):
    """
    Runs a command as Administrator.

    Args:
        command (str): The command to execute.
    """
    logging.info(f"Running command as Administrator: {command}")
    try:
        subprocess.run(["runas", "/user:Administrator", command], check=True)
        logging.info("Command executed successfully as Administrator.")
    except Exception as e:
        logging.error(f"Failed to execute command as Administrator: {e}")



def generate_otp(secret_key):
    """
    Generates a One-Time Password (OTP) using a secret key.

    Args:
        secret_key (str): Secret key for OTP generation.

    Returns:
        str: OTP.
    """
    totp = pyotp.TOTP(secret_key)
    otp = totp.now()
    logging.info(f"Generated OTP: {otp}")
    return otp

def verify_otp(secret_key, otp):
    """
    Verifies a One-Time Password (OTP) against a secret key.

    Args:
        secret_key (str): Secret key for OTP generation.
        otp (str): OTP to verify.

    Returns:
        bool: True if OTP is valid, False otherwise.
    """
    totp = pyotp.TOTP(secret_key)
    is_valid = totp.verify(otp)
    logging.info(f"OTP verification result: {is_valid}")
    return is_valid


logging.basicConfig(
    filename="security.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)



# Specialized Actions
def dropdown_select(driver=None, selector=None, value=None, by=By.CSS_SELECTOR, is_local=False, window_title=None):
    """
    Selects a value in a dropdown (web-based or local application).

    Args:
        driver (WebDriver, optional): Selenium WebDriver instance for web dropdowns.
        selector (str, optional): Selector for the web dropdown element.
        value (str or int): Value to select (visible text or index).
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        is_local (bool): Whether the dropdown is in a local application.
        window_title (str, optional): Title of the local application window.
    """
    try:
        if is_local and window_title:
            logging.info(f"Selecting '{value}' in dropdown in local application: {window_title}")
            #import pygetwindow as gw
            #import pywinauto
            #from pywinauto.application import Application
            # Locate window and dropdown control
            app = Application(backend="uia").connect(title=window_title)
            window = app.window(title=window_title)
            dropdown = window.child_window(title=selector, control_type="ComboBox")

            # Select dropdown value
            dropdown.select(value)
            logging.info(f"Successfully selected '{value}' in dropdown: {selector} (local).")

        elif driver and selector and value:
            logging.info(f"Selecting '{value}' in web dropdown: {selector}")
            element = driver.find_element(by, selector)
            dropdown = Select(element)

            if isinstance(value, int):
                dropdown.select_by_index(value)
            else:
                dropdown.select_by_visible_text(value)

            logging.info(f"Successfully selected '{value}' in web dropdown: {selector}.")
        else:
            raise ValueError("Invalid arguments. Provide either a web driver and selector or local application details.")
    except Exception as e:
        logging.error(f"Failed to select '{value}' in dropdown: {e}")

def checkbox_toggle(driver, selector, value, by=By.CSS_SELECTOR, max_retries=3):
    """
    Toggles a checkbox on or off with retries.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the checkbox element.
        value (bool): Desired state of the checkbox (True for checked, False for unchecked).
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        max_retries (int): Number of retry attempts.
    """
    def toggle_checkbox():
        checkbox = driver.find_element(by, selector)
        if checkbox.is_selected() != value:
            checkbox.click()

    retry_action(toggle_checkbox, max_retries=max_retries)


def slider_adjustment(driver, selector, value, by=By.CSS_SELECTOR):
    """
    Adjusts a slider to a specific value.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the slider element.
        value (int): Target value for the slider.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
    """
    logging.info(f"Adjusting slider {selector} to value {value}")
    try:
        slider = driver.find_element(by, selector)
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", slider, value)
        logging.info(f"Slider {selector} adjusted to {value}")
    except Exception as e:
        logging.error(f"Failed to adjust slider {selector}: {e}")


def calendar_interaction(driver, selector, date, by=By.CSS_SELECTOR, max_retries=3):
    """
    Interacts with a calendar to set a specific date with retries.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        selector (str): Selector for the calendar element.
        date (str): Date to set in the format 'YYYY-MM-DD'.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
        max_retries (int): Number of retry attempts.
    """
    def set_date():
        calendar = driver.find_element(by, selector)
        calendar.clear()
        calendar.send_keys(date)

    retry_action(set_date, max_retries=max_retries)


def loop(actions, iterations, driver):
    """
    Loops through a series of actions with error recovery.

    Args:
        actions (list of callables): List of actions to execute.
        iterations (int): Number of times to repeat the loop.
        driver (WebDriver): Selenium WebDriver instance.
    """
    for i in range(iterations):
        logging.info(f"Executing loop iteration {i + 1}")
        for action in actions:
            try:
                action(driver)
            except Exception as e:
                logging.error(f"Error during loop iteration {i + 1}, action {action.__name__}: {e}")
                continue


def wait(duration):
    """
    Waits for a specified duration.

    Args:
        duration (int): Time to wait in seconds.
    """
    logging.info(f"Waiting for {duration} seconds...")
    try:
        time.sleep(duration)
        logging.info("Wait completed.")
    except Exception as e:
        logging.error(f"Error during wait: {e}")






def wait_for(driver, condition, selector, timeout=30, by=By.CSS_SELECTOR):
    """
    Waits for a specific condition to be met with logging.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        condition (callable): Condition to wait for (e.g., element_to_be_clickable).
        selector (str): Selector for the target element.
        timeout (int): Maximum wait time in seconds.
        by (str): Selector strategy (e.g., CSS_SELECTOR, XPATH).
    """
    logging.info(f"Waiting for condition '{condition.__name__}' on {selector}")
    try:
        WebDriverWait(driver, timeout).until(condition((by, selector)))
        logging.info(f"Condition '{condition.__name__}' met for {selector}")
    except Exception as e:
        logging.error(f"Condition '{condition.__name__}' not met for {selector} within {timeout} seconds: {e}")
        raise



#ERROR HANDLING & REALTIME ERORR HANDLING



def send_error_notification(error_message):
    """
    Sends an email notification with the error details.

    Args:
        error_message (str): The error message to include in the email.
    """
    try:
        smtp_server = "smtp.example.com"
        smtp_port = 587
        smtp_username = "your_email@example.com"
        smtp_password = "your_password"
        recipient_email = "admin@example.com"

        message = MIMEText(f"An error occurred:\n\n{error_message}")
        message["Subject"] = "Critical Error Notification"
        message["From"] = smtp_username
        message["To"] = recipient_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        logging.info("Error notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")

def retry_action_with_error_reporting(action, max_retries=3, wait_time=2, *args, **kwargs):
    """
    Retries an action if it fails and logs detailed error information.

    Args:
        action (callable): The function to execute.
        max_retries (int): Number of retry attempts.
        wait_time (int): Delay between retries in seconds.
        *args: Positional arguments for the action.
        **kwargs: Keyword arguments for the action.

    Returns:
        Any: The return value of the action if successful.
    """
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries} for action '{action.__name__}'")
            result = action(*args, **kwargs)
            logging.info(f"Action '{action.__name__}' succeeded on attempt {attempt + 1}")
            return result
        except Exception as e:
            error_message = f"Attempt {attempt + 1} failed for action '{action.__name__}': {e}"
            logging.error(error_message)
            if attempt == max_retries - 1:
                send_error_notification(error_message)
            time.sleep(wait_time)
    raise Exception(f"Action '{action.__name__}' failed after {max_retries} attempts.")

def loop_with_error_reporting(actions, iterations, driver):
    """
    Executes actions in a loop and generates a detailed error report.

    Args:
        actions (list of callables): List of actions to execute.
        iterations (int): Number of times to repeat the loop.
        driver (WebDriver): Selenium WebDriver instance.
    """
    error_summary = []

    for i in range(iterations):
        logging.info(f"Executing loop iteration {i + 1}")
        for action in actions:
            try:
                action(driver)
            except Exception as e:
                error_message = f"Error in loop iteration {i + 1}, action '{action.__name__}': {e}"
                logging.error(error_message)
                error_summary.append(error_message)

    # Log error summary
    if error_summary:
        logging.error("Error Summary:\n" + "\n".join(error_summary))
        send_error_notification("\n".join(error_summary))

def write_error_summary_to_file(error_summary, filename="error_summary.txt"):
    """
    Writes the error summary to a file.

    Args:
        error_summary (list): List of error messages.
        filename (str): Name of the file to write the summary to.
    """
    logging.info(f"Writing error summary to file: {filename}")
    try:
        with open(filename, "w") as file:
            file.write("Error Summary:\n")
            file.write("\n".join(error_summary))
        logging.info(f"Error summary written to {filename}.")
    except Exception as e:
        logging.error(f"Failed to write error summary to file: {e}")


class WorkflowExecutor:
    def __init__(self):
        self.driver = None
        self.app = None
        self.variables = {}
        self.status = "initialized"
        self.cipher = None
        self.browser_active = False
        self.last_url = None

    def execute_action(self, action):
        """
        Executes a normalized action with proper error handling and retries.
        """
        try:
            normalized_action = normalize_action(action)
            action_type = normalized_action['type']
            logging.info(f"Executing action: {action_type}")

            # Initialize browser if needed
            if action_type == 'open_selenium':
                self.cleanup_browser()
                self.driver = open_selenium(
                    browser=normalized_action.get('browser'),
                    headless=normalized_action.get('headless', False)
                )
                self.browser_active = True
                return

            # Check browser state before each action that requires it
            if action_type in ['url_navigation', 'element_interact']:
                if not self.ensure_browser_active():
                    # Reinitialize browser if needed
                    self.driver = open_selenium(
                        browser=normalized_action.get('browser', 'chrome'),
                        headless=normalized_action.get('headless', False)
                    )
                    self.browser_active = True
                    
                    # If this was a navigation action, we need to revisit the last URL
                    if self.last_url and action_type == 'element_interact':
                        self.driver.get(self.last_url)
                        try:
                            WebDriverWait(self.driver, 30).until(
                                lambda driver: driver.execute_script('return document.readyState') == 'complete'
                            )
                        except Exception as e:
                            logging.warning(f"Page load wait failed: {e}")

                if action_type == 'url_navigation':
                    url = normalized_action.get('url')
                    self.driver.get(url)
                    try:
                        WebDriverWait(self.driver, 30).until(
                            lambda driver: driver.execute_script('return document.readyState') == 'complete'
                        )
                        self.last_url = url
                    except Exception as e:
                        logging.warning(f"Page load wait failed: {e}")
                    
                elif action_type == 'element_interact':
                    try:
                        self.element_interact(
                            selector=normalized_action.get('selector'),
                            by=normalized_action.get('by', 'css'),
                            action=normalized_action.get('action', 'click'),
                            value=normalized_action.get('value', '')
                        )
                    except Exception as e:
                        logging.error(f"Element interaction failed: {e}")
                        self.take_debug_screenshot()
                        raise

            # Don't cleanup browser after each action anymore
            # Only cleanup on explicit close or error

        except Exception as e:
            self._handle_action_error(normalized_action, e)
            if isinstance(e, (selenium.common.exceptions.NoSuchWindowException, 
                            selenium.common.exceptions.WebDriverException)):
                self.cleanup_browser()
            raise

    def ensure_browser_active(self):
        """
        Ensures browser is active and reinitializes if needed.
        Returns True if browser is active, False if it needs to be reinitialized.
        """
        if not self.driver:
            logging.info("No browser session exists")
            return False
        
        try:
            # More robust check for browser state
            self.driver.current_window_handle  # This will throw an exception if browser is closed
            return True
        except Exception as e:
            logging.warning(f"Browser check failed: {e}. Reinitializing...")
            self.cleanup_browser()
            return False

    def cleanup_browser(self):
        """Safely cleanup browser resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.warning(f"Error during browser cleanup: {e}")
            finally:
                self.driver = None
                self.browser_active = False
                self.last_url = None

    def element_interact(self, selector, by='css', action='click', value=''):
        """Interacts with a web element with smart selector fallback."""
        if not self.ensure_browser_active():
            raise ValueError("Browser not initialized or not active")
        
        logging.info(f"Interacting with element: {selector} ({action})")
        try:
            # Progressive selector strategy
            selectors_to_try = [
                # Try ID first (most specific)
                (By.ID, selector if not selector.startswith('#') else selector[1:]),
                # Then CSS selector
                (By.CSS_SELECTOR, selector),
                # Then class name
                (By.CLASS_NAME, selector if not selector.startswith('.') else selector[1:]),
                # Then name attribute
                (By.NAME, selector),
                # Finally, try XPath as fallback
                (By.XPATH, f"//*[@id='{selector}']"),  # ID as XPath
                (By.XPATH, f"//*[contains(@class, '{selector}')]"),  # Class as XPath
                (By.XPATH, f"//*[@name='{selector}']"),  # Name as XPath
                (By.XPATH, selector if selector.startswith('//') else f"//*[contains(text(), '{selector}')]")  # Text content or custom XPath
            ]

            wait = WebDriverWait(self.driver, 20)
            element = None
            last_error = None

            for by_type, sel in selectors_to_try:
                try:
                    element = wait.until(lambda d: (
                        d.find_element(by_type, sel) and
                        d.find_element(by_type, sel).is_displayed() and
                        d.find_element(by_type, sel).is_enabled()
                    ) and d.find_element(by_type, sel))
                    logging.info(f"Element found using {by_type}: {sel}")
                    break
                except Exception as e:
                    last_error = e
                    continue

            if not element:
                raise last_error or Exception("Element not found with any selector strategy")

            # Scroll element into view
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.scrollIntoView({block: 'center', behavior: 'instant'});
            """, element)
            
            time.sleep(0.5)

            if action == 'click':
                try:
                    element.click()
                except:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                    except:
                        ActionChains(self.driver).move_to_element(element).click().perform()
            elif action == 'input':
                for _ in range(3):
                    try:
                        element.clear()
                        element.send_keys(Keys.CONTROL + "a")
                        element.send_keys(Keys.DELETE)
                        for char in value:
                            element.send_keys(char)
                            time.sleep(0.1)
                        
                        if element.get_attribute('value') == value:
                            break
                    except Exception as e:
                        logging.warning(f"Input attempt failed: {e}, retrying...")
                        time.sleep(1)

            return True

        except Exception as e:
            logging.error(f"Element interaction failed: {str(e)}")
            self.take_debug_screenshot()
            raise

    def take_debug_screenshot(self):
        """Takes a debug screenshot if possible."""
        if self.driver:
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshots/debug_{timestamp}.png"
                os.makedirs("error_screenshots", exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Debug screenshot saved: {screenshot_path}")
            except Exception as e:
                logging.error(f"Failed to save debug screenshot: {e}")

    def cleanup(self):
        """Cleanup all resources."""
        self.cleanup_browser()
        if self.app:
            try:
                self.app = None
            except Exception as e:
                logging.error(f"Error cleaning up application: {e}")
        logging.info("Workflow cleanup completed successfully")

    def _init_cipher(self):
        """Initialize the cipher for encryption/decryption."""
        try:
            with open('secret.key', 'rb') as key_file:
                key = key_file.read()
            self.cipher = Fernet(key)
        except Exception as e:
            logging.error(f"Failed to initialize cipher: {e}")
            raise

    def _decrypt_password(self, encrypted_password):
        """
        Decrypt password using the initialized cipher.
        """
        try:
            if not self.cipher:
                self._init_cipher()
            return self.cipher.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logging.error(f"Error decrypting password: {e}")
            raise

    def _load_encryption_key(self):
        """
        Load encryption key from file.
        """
        try:
            with open('secret.key', 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading encryption key: {e}")
            raise

    def open_selenium(self, browser=None, headless=False):
        """Opens a Selenium WebDriver instance using system default or specified browser."""
        logging.info(f"Opening browser (headless: {headless})")
        try:
            self.driver = open_selenium(browser, headless)
            logging.info("Browser opened successfully")
            return self.driver
        except Exception as e:
            logging.error(f"Failed to open browser: {str(e)}")
            raise

    def close_selenium(self):
        """Closes the Selenium WebDriver instance."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("Browser closed successfully")
            except Exception as e:
                logging.error(f"Failed to close browser: {e}")
            finally:
                self.driver = None

    def url_navigation(self, url):
        """Navigates to a URL."""
        logging.info(f"Navigating to: {url}")
        try:
            self.driver.get(url)
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            logging.info(f"Navigation successful: {url}")
        except Exception as e:
            logging.error(f"Navigation failed: {e}")
            raise

    def _get_credentials(self, credential_name):
        """
        Get credentials from credentials.json file.
        """
        try:
            with open('credentials.json', 'r') as f:
                credentials_list = json.load(f)
                for cred in credentials_list:
                    if cred['name'].lower() == credential_name.lower():
                        return cred
            return None
        except Exception as e:
            logging.error(f"Error loading credentials: {e}")
            return None

    def _handle_action_error(self, action, error):
        """
        Handles errors that occur during action execution.
        """
        logging.error(f"Error executing action: {action.get('type')}")
        logging.error(f"Error details: {str(error)}")
        if self.driver:
            try:
                # Take screenshot on error
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"error_screenshots/error_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Error screenshot saved: {screenshot_path}")
            except Exception as screenshot_error:
                logging.error(f"Failed to save error screenshot: {screenshot_error}")

    def __del__(self):
        """
        Destructor to ensure resources are freed even if cleanup wasn't called.
        """
        try:
            if self.driver:
                self.close_selenium()
        except:
            pass  # Suppress errors in destructor

    def wait_for_page_load(self, timeout=30):
        """Waits for page load to complete with multiple conditions."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: driver.execute_script('''
                return document.readyState === "complete" && 
                       !document.querySelector(".loading") &&
                       (typeof jQuery === "undefined" || jQuery.active === 0) &&
                       (!window.angular || !angular.element(document).injector() || 
                        !angular.element(document).injector().get('$http').pendingRequests.length)
            '''))
            time.sleep(1)  # Additional small wait for any final rendering
        except Exception as e:
            logging.error(f"Page load wait timeout: {e}")
            self.take_debug_screenshot()
            raise

    def handle_desktop_application(self, action):
        """Enhanced desktop application handling with retries and checks."""
        try:
            app_path = action.get('application_path')
            arguments = action.get('arguments', '')
            working_dir = action.get('working_dir')
            
            # Ensure any existing instance is closed
            try:
                app = Application().connect(path=app_path)
                app.kill()
                time.sleep(1)
            except:
                pass  # No existing instance
            
            # Launch application with retry
            for attempt in range(3):
                try:
                    if working_dir:
                        process = subprocess.Popen(
                            [app_path] + shlex.split(arguments),
                            cwd=working_dir,
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    else:
                        process = subprocess.Popen(
                            [app_path] + shlex.split(arguments),
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    
                    # Wait for window to appear
                    start_time = time.time()
                    while time.time() - start_time < 30:
                        try:
                            app = Application().connect(process=process.pid)
                            window = app.top_window()
                            window.wait('ready', timeout=10)
                            logging.info(f"Application launched successfully: {app_path}")
                            return app
                        except Exception:
                            time.sleep(1)
                    
                    raise TimeoutError("Application window did not appear")
                    
                except Exception as e:
                    logging.warning(f"Launch attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            logging.error(f"Failed to launch application {app_path}: {e}")
            raise

    def desktop_input(self, window, control_id, text, retries=3):
        """More reliable desktop input with retries."""
        for attempt in range(retries):
            try:
                # Find control and ensure it's ready
                control = window[control_id]
                control.wait('ready', timeout=10)
                
                # Clear existing text
                control.set_text('')
                time.sleep(0.5)
                
                # Type text with delay
                for char in text:
                    control.type_keys(char, pause=0.1)
                
                # Verify input
                actual_text = control.get_value()
                if actual_text == text:
                    return True
                    
                logging.warning(f"Input verification failed. Expected: {text}, Got: {actual_text}")
                
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Desktop input failed after {retries} attempts: {e}")
                    raise
                time.sleep(1)
                
        return False

    def desktop_click(self, window, control_id, retries=3):
        """More reliable desktop clicking with retries."""
        for attempt in range(retries):
            try:
                control = window[control_id]
                control.wait('ready', timeout=10)
                control.click_input()
                time.sleep(0.5)  # Wait for click to register
                return True
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Desktop click failed after {retries} attempts: {e}")
                    raise
                time.sleep(1)

# Function to execute a workflow
def execute_workflow(workflow_data):
    """
    Main entry point for workflow execution.
    
    Args:
        workflow_data (dict): The workflow to execute
    """
    executor = WorkflowExecutor()
    try:
        executor.execute_workflow(workflow_data)
    except Exception as e:
        logging.error(f"Workflow execution failed: {str(e)}")
        raise


# Action Type Mappings
ACTION_TYPE_MAPPINGS = {
    # Browser Actions
    'open_browser': 'open_selenium',
    'launch_browser': 'open_selenium',
    'start_browser': 'open_selenium',
    
    'close_browser': 'close_selenium',
    'quit_browser': 'close_selenium',
    'exit_browser': 'close_selenium',
    
    'navigate': 'url_navigation',
    'go_to': 'url_navigation',
    'go_to_url': 'url_navigation',
    'browse_to': 'url_navigation',
    
    'type': 'typing_sequence',
    'input': 'typing_sequence',
    'input_text': 'typing_sequence',
    'enter_text': 'typing_sequence',
    
    'click': 'element_interact',
    'click_element': 'element_interact',
    'click_button': 'element_interact',
    
    # Mouse Actions
    'mouse_click': 'left_click',
    'click_at': 'left_click',
    
    'right_click_at': 'right_click',
    'context_click': 'right_click',
    
    'double_click': 'double_left_click',
    'dbl_click': 'double_left_click',
    
    'drag': 'mouse_drag',
    'drag_and_drop': 'mouse_drag',
    
    'hover': 'mouse_hover',
    'mouse_over': 'mouse_hover',
    
    'scroll': 'mouse_scroll',
    'scroll_page': 'mouse_scroll',
    
    'move_mouse': 'mouse_move',
    'move_cursor': 'mouse_move',
    
    # Keyboard Actions
    'press_key': 'keystroke',
    'key_press': 'keystroke',
    
    'press_keys': 'key_combination',
    'key_combo': 'key_combination',
    
    'type_text': 'typing_sequence',
    'send_keys': 'typing_sequence',
    
    'special_key': 'special_key_press',
    'system_key': 'special_key_press',
    
    'shortcut': 'shortcut_use',
    'keyboard_shortcut': 'shortcut_use',
    
    # File Operations
    'open_file': 'file_open',
    'load_file': 'file_open',
    
    'save_file': 'file_save',
    'write_file': 'file_save',
    
    'delete_file': 'file_delete',
    'remove_file': 'file_delete',
    
    'rename_file': 'file_rename',
    'move_file': 'file_move',
    'copy_file': 'file_copy',
    'upload': 'file_upload',
    'download': 'file_download',
    
    # Wait Actions
    'sleep': 'wait',
    'pause': 'wait',
    'delay': 'wait',
    
    'wait_until': 'wait_for',
    'wait_for_element': 'wait_for',
    
    # Email Actions
    'read_email': 'email_read',
    'check_email': 'email_read',
    
    'write_email': 'email_write',
    'compose_email': 'email_write',
    
    'send_email': 'email_send',
    'email': 'email_send',
    
    # Application Actions
    'open_app': 'open_application',
    'launch_app': 'open_application',
    'start_app': 'open_application',
    'run_app': 'open_application'
}  # Remove the extra closing brace

def normalize_action(action):
    """
    Normalizes action type and parameters for consistent handling.
    """
    if not isinstance(action, dict):
        raise ValueError("Action must be a dictionary")
        
    # Make a copy to avoid modifying the original
    normalized = action.copy()
    
    # Normalize action type
    action_type = normalized.get('type', '').lower()
    normalized['type'] = ACTION_TYPE_MAPPINGS.get(action_type, action_type)
    
    return normalized

def wait(duration):
    """
    Waits for a specified duration.

    Args:
        duration (int): Time to wait in seconds.
    """
    logging.info(f"Waiting for {duration} seconds...")
    try:
        time.sleep(duration)
        logging.info("Wait completed.")
    except Exception as e:
        logging.error(f"Error during wait: {e}")

def take_error_screenshot(driver, error_type="error"):
    """
    Takes a screenshot when an error occurs.
    
    Args:
        driver: WebDriver instance
        error_type (str): Type of error for filename
    
    Returns:
        str: Path to screenshot or None if failed
    """
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_path = f"error_screenshots/{error_type}_{timestamp}.png"
        os.makedirs("error_screenshots", exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logging.info(f"Error screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"Failed to save error screenshot: {e}")
        return None

def email_write_gmail(to, subject, body, cc=None, bcc=None):
    """
    Composes and drafts an email in Gmail using the Gmail API.

    Args:
        to (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        cc (str, optional): CC recipients.
        bcc (str, optional): BCC recipients.
    """
    try:
        # Load credentials from token.json
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.compose'])
        service = build('gmail', 'v1', credentials=creds)

        # Create the email message
        message = create_gmail_message(to, subject, body, cc, bcc)

        # Create a draft in Gmail
        draft = service.users().drafts().create(userId='me', body=message).execute()
        logging.info(f"Draft created successfully with ID: {draft['id']}")
    except Exception as e:
        logging.error(f"Failed to compose Gmail draft: {e}")

def email_send_gmail(to_address, subject, body, smtp_server=None, smtp_port=None, smtp_username=None, smtp_password=None):
    """
    Sends an email using Gmail API.
    """
    logging.info(f"Sending email to {to_address} via Gmail API")
    try:
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.send'])
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(body)
        message['to'] = to_address
        message['subject'] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")




















def file_move(source_path, destination_path):
    """
    Moves a file to a new location.

    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    logging.info(f"Moving file from {source_path} to {destination_path}")
    try:
        shutil.move(source_path, destination_path)
        logging.info("File moved successfully.")
    except Exception as e:
        logging.error(f"Failed to move file: {e}")
