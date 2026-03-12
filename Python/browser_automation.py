from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
import time
import logging
from typing import Dict, Any
import os
from pathlib import Path
import requests
import base64
from PIL import Image
import io
from bs4 import BeautifulSoup
import re
import pyautogui
import vision

# Common key combinations for reference
KEY_COMBINATIONS = {
    'SELECT_ALL': (Keys.CONTROL, 'a'),
    'COPY': (Keys.CONTROL, 'c'),
    'PASTE': (Keys.CONTROL, 'v'),
    'CUT': (Keys.CONTROL, 'x'),
    'UNDO': (Keys.CONTROL, 'z'),
    'REDO': (Keys.CONTROL, 'y'),
    'SAVE': (Keys.CONTROL, 's'),
    'FIND': (Keys.CONTROL, 'f'),
    'NEW_TAB': (Keys.CONTROL, 't'),
    'CLOSE_TAB': (Keys.CONTROL, 'w'),
    'REFRESH': (Keys.CONTROL, 'r'),
    'ZOOM_IN': (Keys.CONTROL, '+'),
    'ZOOM_OUT': (Keys.CONTROL, '-'),
    'ZOOM_RESET': (Keys.CONTROL, '0'),
    'PAGE_DOWN': Keys.PAGE_DOWN,
    'PAGE_UP': Keys.PAGE_UP,
    'HOME': Keys.HOME,
    'END': Keys.END,
    'ARROW_UP': Keys.ARROW_UP,
    'ARROW_DOWN': Keys.ARROW_DOWN,
    'ARROW_LEFT': Keys.ARROW_LEFT,
    'ARROW_RIGHT': Keys.ARROW_RIGHT,
    'TAB': Keys.TAB,
    'SHIFT_TAB': (Keys.SHIFT, Keys.TAB),
    'ENTER': Keys.ENTER,
    'ESCAPE': Keys.ESCAPE,
    'DELETE': Keys.DELETE,
    'BACKSPACE': Keys.BACKSPACE,
    'SPACE': Keys.SPACE,
    'SELECT_TO_END': (Keys.SHIFT, Keys.END),
    'SELECT_TO_HOME': (Keys.SHIFT, Keys.HOME),
    'SELECT_NEXT_CHAR': (Keys.SHIFT, Keys.ARROW_RIGHT),
    'SELECT_PREV_CHAR': (Keys.SHIFT, Keys.ARROW_LEFT),
    'SELECT_NEXT_LINE': (Keys.SHIFT, Keys.ARROW_DOWN),
    'SELECT_PREV_LINE': (Keys.SHIFT, Keys.ARROW_UP),
    'SELECT_NEXT_WORD': (Keys.CONTROL, Keys.SHIFT, Keys.ARROW_RIGHT),
    'SELECT_PREV_WORD': (Keys.CONTROL, Keys.SHIFT, Keys.ARROW_LEFT),
    'MOVE_NEXT_WORD': (Keys.CONTROL, Keys.ARROW_RIGHT),
    'MOVE_PREV_WORD': (Keys.CONTROL, Keys.ARROW_LEFT),
    'SWITCH_WINDOW': (Keys.ALT, Keys.TAB),
    'PRINT': (Keys.CONTROL, 'p'),
    'NEW_WINDOW': (Keys.CONTROL, 'n'),
    'CLOSE_WINDOW': (Keys.ALT, Keys.F4),
    'SCREENSHOT': (Keys.CONTROL, Keys.SHIFT, 's'),
    'INSPECT_ELEMENT': (Keys.CONTROL, Keys.SHIFT, 'i'),
    'DEV_TOOLS': (Keys.F12,),
    'BOOKMARK': (Keys.CONTROL, 'd'),
    'HISTORY': (Keys.CONTROL, 'h'),
    'DOWNLOADS': (Keys.CONTROL, 'j'),
    'ADDRESS_BAR': (Keys.CONTROL, 'l'),
    'MUTE_TAB': (Keys.ALT, 'm'),
    'FULLSCREEN': (Keys.F11,),
    'PRINT_PREVIEW': (Keys.CONTROL, Keys.SHIFT, 'p'),
    'SAVE_AS': (Keys.CONTROL, Keys.SHIFT, 's'),
    'SELECT_ALL_TABS': (Keys.CONTROL, Keys.SHIFT, 'a')
}

# Comprehensive list of Selenium Keys
SELENIUM_KEYS = {
    # Basic Keys
    'NULL': Keys.NULL,
    'CANCEL': Keys.CANCEL,
    'HELP': Keys.HELP,
    'BACKSPACE': Keys.BACKSPACE,
    'BACK_SPACE': Keys.BACK_SPACE,
    'TAB': Keys.TAB,
    'CLEAR': Keys.CLEAR,
    'RETURN': Keys.RETURN,
    'ENTER': Keys.ENTER,
    'SHIFT': Keys.SHIFT,
    'CONTROL': Keys.CONTROL,
    'ALT': Keys.ALT,
    'PAUSE': Keys.PAUSE,
    'ESCAPE': Keys.ESCAPE,
    'SPACE': Keys.SPACE,
    
    # Navigation Keys
    'PAGE_UP': Keys.PAGE_UP,
    'PAGE_DOWN': Keys.PAGE_DOWN,
    'END': Keys.END,
    'HOME': Keys.HOME,
    'LEFT': Keys.LEFT,
    'UP': Keys.UP,
    'RIGHT': Keys.RIGHT,
    'DOWN': Keys.DOWN,
    'INSERT': Keys.INSERT,
    'DELETE': Keys.DELETE,
    
    # Function Keys
    'F1': Keys.F1,
    'F2': Keys.F2,
    'F3': Keys.F3,
    'F4': Keys.F4,
    'F5': Keys.F5,
    'F6': Keys.F6,
    'F7': Keys.F7,
    'F8': Keys.F8,
    'F9': Keys.F9,
    'F10': Keys.F10,
    'F11': Keys.F11,
    'F12': Keys.F12,
    
    # Special Characters
    'SEMICOLON': Keys.SEMICOLON,
    'EQUALS': Keys.EQUALS,
    'NUMPAD0': Keys.NUMPAD0,
    'NUMPAD1': Keys.NUMPAD1,
    'NUMPAD2': Keys.NUMPAD2,
    'NUMPAD3': Keys.NUMPAD3,
    'NUMPAD4': Keys.NUMPAD4,
    'NUMPAD5': Keys.NUMPAD5,
    'NUMPAD6': Keys.NUMPAD6,
    'NUMPAD7': Keys.NUMPAD7,
    'NUMPAD8': Keys.NUMPAD8,
    'NUMPAD9': Keys.NUMPAD9,
    'MULTIPLY': Keys.MULTIPLY,
    'ADD': Keys.ADD,
    'SEPARATOR': Keys.SEPARATOR,
    'SUBTRACT': Keys.SUBTRACT,
    'DECIMAL': Keys.DECIMAL,
    'DIVIDE': Keys.DIVIDE,
    
    # Meta Keys
    'META': Keys.META,
    'COMMAND': Keys.COMMAND,
    
    # Common Key Combinations
    'SELECT_ALL': (Keys.CONTROL, 'a'),
    'COPY': (Keys.CONTROL, 'c'),
    'PASTE': (Keys.CONTROL, 'v'),
    'CUT': (Keys.CONTROL, 'x'),
    'UNDO': (Keys.CONTROL, 'z'),
    'REDO': (Keys.CONTROL, 'y'),
    'NEW_TAB': (Keys.CONTROL, 't'),
    'CLOSE_TAB': (Keys.CONTROL, 'w'),
    'NEW_WINDOW': (Keys.CONTROL, 'n'),
    'CLOSE_WINDOW': (Keys.ALT, Keys.F4),
    'SWITCH_WINDOW': (Keys.ALT, Keys.TAB),
    'PRINT': (Keys.CONTROL, 'p'),
    'SAVE': (Keys.CONTROL, 's'),
    'FIND': (Keys.CONTROL, 'f'),
    'ZOOM_IN': (Keys.CONTROL, '+'),
    'ZOOM_OUT': (Keys.CONTROL, '-'),
    'ZOOM_RESET': (Keys.CONTROL, '0'),
    
    # Text Navigation
    'LINE_START': (Keys.HOME,),
    'LINE_END': (Keys.END,),
    'TEXT_START': (Keys.CONTROL, Keys.HOME),
    'TEXT_END': (Keys.CONTROL, Keys.END),
    'WORD_PREV': (Keys.CONTROL, Keys.LEFT),
    'WORD_NEXT': (Keys.CONTROL, Keys.RIGHT),
    
    # Text Selection
    'SELECT_LINE_START': (Keys.SHIFT, Keys.HOME),
    'SELECT_LINE_END': (Keys.SHIFT, Keys.END),
    'SELECT_WORD_PREV': (Keys.CONTROL, Keys.SHIFT, Keys.LEFT),
    'SELECT_WORD_NEXT': (Keys.CONTROL, Keys.SHIFT, Keys.RIGHT),
    'SELECT_TO_START': (Keys.CONTROL, Keys.SHIFT, Keys.HOME),
    'SELECT_TO_END': (Keys.CONTROL, Keys.SHIFT, Keys.END)
}

# Custom exception for element not found
class ElementNotFoundError(Exception):
    """Custom exception for when an element cannot be found"""
    pass

# Handle anticaptcha imports
#try:
#    import anticaptchaofficial.recaptchav2proxyless as recaptchav2proxyless
#    import anticaptchaofficial.recaptchav3proxyless as recaptchav3proxyless
#    import anticaptchaofficial.imagecaptcha as imagecaptcha
#    ANTICAPTCHA_AVAILABLE = True
#except ImportError:
#    ANTICAPTCHA_AVAILABLE = False
#    recaptchav2proxyless = None
#    recaptchav3proxyless = None
#    imagecaptcha = None

class BrowserAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.actions = None
        self.logger = logging.getLogger(__name__)

        # Add key mappings
        self.special_keys = {
            "enter": Keys.ENTER,
            "tab": Keys.TAB,
            "space": Keys.SPACE,
            "backspace": Keys.BACKSPACE,
            "delete": Keys.DELETE,
            "escape": Keys.ESCAPE,
            "up": Keys.UP,
            "down": Keys.DOWN,
            "left": Keys.LEFT,
            "right": Keys.RIGHT,
            "home": Keys.HOME,
            "end": Keys.END,
            "pageup": Keys.PAGE_UP,
            "pagedown": Keys.PAGE_DOWN,
            "insert": Keys.INSERT,
            "f1": Keys.F1,
            # ... add more special keys as needed
        }
        
        self.modifier_keys = {
            "ctrl": Keys.CONTROL,
            "alt": Keys.ALT,
            "shift": Keys.SHIFT,
            "meta": Keys.META,
            "command": Keys.COMMAND
        }

        # Add default download directory configuration
        self.default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Add common file input types
        self.file_input_types = [
            'file', 'upload', 'attachment', 'fileUpload', 'fileInput'
        ]

        # Add CAPTCHA service configuration
        self.anticaptcha_key = None  # Set your Anti-Captcha API key
        self.captcha_timeout = 120  # Timeout for CAPTCHA solving

        # Add vision fallback configuration
        self.use_vision_fallback = True
        self.vision_confidence = 0.8
        self.vision_timeout = 10

    def _try_vision_fallback(self, meta_information: Dict[str, Any], action_type: str = "find") -> Dict[str, str]:
        """Try to find or interact with elements using computer vision"""
        try:
            if not self.use_vision_fallback or "vision_fallback" not in meta_information:
                return {"status": "error", "message": "Vision fallback not available"}

            fallback_info = meta_information["vision_fallback"]
            text_to_find = fallback_info.get("text_to_find")
            region = fallback_info.get("region")
            timeout = fallback_info.get("timeout", self.vision_timeout)

            if action_type == "find":
                # Try to find text on screen
                found = vision.find_text_on_screen(text_to_find, region=region, timeout=timeout)
                if found:
                    return {"status": "success", "message": f"Found text: {text_to_find}"}
            
            elif action_type == "click":
                # Try to click text on screen
                clicked = vision.click_text_on_screen(text_to_find, region=region, timeout=timeout)
                if clicked:
                    return {"status": "success", "message": f"Clicked text: {text_to_find}"}

            return {"status": "error", "message": f"Vision fallback failed for: {text_to_find}"}
            
        except Exception as e:
            self.logger.error(f"Vision fallback failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def wait_for_element(self, meta_information):
        """Wait for an element to be present on the page with vision fallback"""
        try:
            self.logger.debug(f"wait_for_element called with meta_information: {meta_information}")
            selector = meta_information.get('selector')
            timeout = meta_information.get('timeout', 10)
            
            if not selector:
                error_msg = "No selector provided in meta_information"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            
            self.logger.debug(f"Waiting for element with selector: {selector}, timeout: {timeout}")    
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                self.logger.debug(f"Element found successfully: {selector}")
                return {"status": "success", "element": element}
            except TimeoutException:
                # Try vision fallback
                self.logger.warning(f"Selenium timeout, attempting vision fallback for: {selector}")
                vision_result = self._try_vision_fallback(meta_information, "find")
                if vision_result["status"] == "success":
                    return vision_result
                
                error_msg = f"Both Selenium and vision fallback failed for selector: {selector}"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            except Exception as e:
                error_msg = f"Error waiting for element: {str(e)}"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}
        except Exception as e:
            error_msg = f"Failed to execute wait_for_element: {str(e)}"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def click_element(self, meta_information):
        """Click an element on the page with vision fallback"""
        try:
            self.logger.debug(f"click_element called with meta_information: {meta_information}")
            selector = meta_information.get('selector')
            if not selector:
                error_msg = "No selector provided in meta_information"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}

            self.logger.debug(f"Attempting to click element with selector: {selector}")
            
            # First try Selenium click
            try:
                wait_result = self.wait_for_element({"selector": selector, "timeout": 10})
                if wait_result["status"] == "success":
                    element = wait_result["element"]
                    
                    # Check for special click types
                    if meta_information.get("double_click", False):
                        try:
                            self.logger.debug("Attempting double click")
                            ActionChains(self.driver).double_click(element).perform()
                            return {"status": "success", "message": f"Double clicked element: {selector}"}
                        except Exception as e:
                            self.logger.error(f"Double click failed: {str(e)}")
                    elif meta_information.get("right_click", False):
                        try:
                            self.logger.debug("Attempting right click")
                            ActionChains(self.driver).context_click(element).perform()
                            return {"status": "success", "message": f"Right clicked element: {selector}"}
                        except Exception as e:
                            self.logger.error(f"Right click failed: {str(e)}")
                    else:
                        try:
                            self.logger.debug("Attempting regular click")
                            element.click()
                            return {"status": "success", "message": f"Element clicked: {selector}"}
                        except Exception as click_error:
                            try:
                                self.logger.warning(f"Regular click failed, trying JavaScript click: {str(click_error)}")
                                self.driver.execute_script("arguments[0].click();", element)
                                return {"status": "success", "message": f"Element clicked via JavaScript: {selector}"}
                            except Exception as js_error:
                                self.logger.error(f"JavaScript click failed: {str(js_error)}")

            except Exception as selenium_error:
                self.logger.warning(f"Selenium click failed: {str(selenium_error)}")

            # If Selenium clicks fail, try vision fallback
            self.logger.warning(f"Selenium clicks failed, attempting vision fallback for: {selector}")
            vision_result = self._try_vision_fallback(meta_information, "click")
            if vision_result["status"] == "success":
                return vision_result

            error_msg = f"Both Selenium and vision fallback clicks failed for: {selector}"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}
            
        except Exception as e:
            error_msg = f"Failed to execute click_element: {str(e)}"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def open_selenium(self, meta_information):
        """Initialize and start a Selenium WebDriver instance"""
        try:
            # Check if there's already an active session
            if self.driver:
                self.logger.info("Selenium session already exists, reusing existing session")
                # Navigate to new URL if provided
                if "url_path_context" in meta_information and "url" in meta_information["url_path_context"]:
                    self.driver.get(meta_information["url_path_context"]["url"])
                return {"status": "success", "message": "Using existing Selenium session"}
            
            # Initialize new session if none exists
            if meta_information["application_context"]["application_name"] == "Chrome":
                self.driver = webdriver.Chrome()
            elif meta_information["application_context"]["application_name"] == "Firefox":
                self.driver = webdriver.Firefox()
            else:
                raise ValueError(f"Unsupported browser: {meta_information['application_context']['application_name']}")
            
            self.wait = WebDriverWait(self.driver, 30)
            self.actions = ActionChains(self.driver)
            
            # Navigate to URL if provided
            if "url_path_context" in meta_information and "url" in meta_information["url_path_context"]:
                self.driver.get(meta_information["url_path_context"]["url"])
            
            return {"status": "success", "message": "New Selenium session started successfully"}
        except Exception as e:
            self.logger.error(f"Failed to start Selenium: {str(e)}")
            # Cleanup if initialization failed
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                self.wait = None
                self.actions = None
            return {"status": "error", "message": str(e)}

    def close_selenium(self, meta_information):
        """Close the Selenium WebDriver instance"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.actions = None
            return {"status": "success", "message": "Selenium session closed successfully"}
        except Exception as e:
            self.logger.error(f"Failed to close Selenium: {str(e)}")
            return {"status": "error", "message": str(e)}

    def send_keys(self, meta_information):
        """Send keyboard input to an element"""
        try:
            selector = meta_information.get('selector')
            keys = meta_information.get('keys')
            
            if not selector or not keys:
                error_msg = "Missing selector or keys in meta_information"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            
            try:
                # Wait for element and send keys
                wait_result = self.wait_for_element({"selector": selector, "timeout": 10})
                if wait_result["status"] == "success":
                    element = wait_result["element"]
                    element.clear()  # Clear existing text
                    element.send_keys(keys)
                    return {"status": "success", "message": f"Keys sent to element: {selector}"}
                else:
                    return wait_result
                    
            except Exception as e:
                error_msg = f"Failed to send keys to element: {str(e)}"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}
                
        except Exception as e:
            error_msg = f"Failed to execute send_keys: {str(e)}"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def __del__(self):
        """Destructor to ensure Selenium session is closed"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass