import pyautogui
import win32gui
import win32con
import win32process
import win32api
import logging
import time
from typing import Dict, Any, List, Union
import keyboard
import shutil
import os
import pathlib
from datetime import datetime
import win32file
import win32con
import win32api
import win32security
import win32com.client
from typing import Optional

try:
    import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False

class WindowsAutomation:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Configure PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Map click types to PyAutoGUI button names
        self.button_map = {
            "left": "left",
            "right": "right",
            "middle": "middle"
        }

        # Add special key mapping
        self.special_keys = {
            "enter": "enter",
            "tab": "tab",
            "space": "space",
            "backspace": "backspace",
            "delete": "delete",
            "escape": "esc",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "home": "home",
            "end": "end",
            "pageup": "pageup",
            "pagedown": "pagedown",
            "insert": "insert",
            "f1": "f1",
            # ... add more special keys as needed
        }

        # Add modifier key mapping
        self.modifier_keys = {
            "ctrl": "ctrl",
            "alt": "alt",
            "shift": "shift",
            "win": "win"
        }

        # Add file operation constants
        self.FILE_OPERATIONS = {
            'copy': shutil.copy2,
            'move': shutil.move,
            'delete': os.remove,
            'rename': os.rename
        }

        # Add Word application instance
        self.word_app = None

    def _validate_coordinates(self, x: float, y: float) -> bool:
        """Validate if coordinates are within screen boundaries"""
        screen_width, screen_height = pyautogui.size()
        return 0 <= x <= screen_width and 0 <= y <= screen_height

    def _perform_click(self, x: float, y: float, button: str, clicks: int = 1, interval: float = 0.0) -> Dict[str, str]:
        """Helper method to perform mouse clicks"""
        try:
            if not self._validate_coordinates(x, y):
                return {"status": "error", "message": "Coordinates out of screen bounds"}
            
            # Move mouse to position first
            pyautogui.moveTo(x, y, duration=0.1)
            
            # Perform the click
            pyautogui.click(x=x, y=y, button=button, clicks=clicks, interval=interval)
            
            return {
                "status": "success", 
                "message": f"{button} click ({clicks} clicks) performed at ({x}, {y})"
            }
        except Exception as e:
            self.logger.error(f"Failed to perform mouse click: {str(e)}")
            return {"status": "error", "message": str(e)}

    # Single Clicks
    def left_click(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a left mouse click"""
        x = meta_information["mouse_coordinates"]["x"]
        y = meta_information["mouse_coordinates"]["y"]
        return self._perform_click(x, y, "left")

    def right_click(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a right mouse click"""
        x = meta_information["mouse_coordinates"]["x"]
        y = meta_information["mouse_coordinates"]["y"]
        return self._perform_click(x, y, "right")

    def middle_click(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a middle mouse click"""
        x = meta_information["mouse_coordinates"]["x"]
        y = meta_information["mouse_coordinates"]["y"]
        return self._perform_click(x, y, "middle")

    # Double Clicks
    def double_left_click(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a double left click"""
        x = meta_information["mouse_coordinates"]["x"]
        y = meta_information["mouse_coordinates"]["y"]
        return self._perform_click(x, y, "left", clicks=2, interval=0.1)

    def double_right_click(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a double right click"""
        x = meta_information["mouse_coordinates"]["x"]
        y = meta_information["mouse_coordinates"]["y"]
        return self._perform_click(x, y, "right", clicks=2, interval=0.1)

    def double_middle_click(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a double middle click"""
        x = meta_information["mouse_coordinates"]["x"]
        y = meta_information["mouse_coordinates"]["y"]
        return self._perform_click(x, y, "middle", clicks=2, interval=0.1)

    # Mouse Movements
    def mouse_drag(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a mouse drag operation with improved error handling"""
        try:
            start_x = meta_information["start_coordinates"]["x"]
            start_y = meta_information["start_coordinates"]["y"]
            end_x = meta_information["end_coordinates"]["x"]
            end_y = meta_information["end_coordinates"]["y"]
            
            if not (self._validate_coordinates(start_x, start_y) and 
                   self._validate_coordinates(end_x, end_y)):
                return {"status": "error", "message": "Coordinates out of screen bounds"}
            
            # Move to start position
            pyautogui.moveTo(start_x, start_y, duration=0.1)
            # Perform drag
            pyautogui.mouseDown()
            pyautogui.moveTo(end_x, end_y, duration=0.2)
            pyautogui.mouseUp()
            
            return {"status": "success", "message": "Mouse drag completed successfully"}
        except Exception as e:
            self.logger.error(f"Failed to perform mouse drag: {str(e)}")
            return {"status": "error", "message": str(e)}

    def mouse_hover(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Hover mouse over specified coordinates for a duration"""
        try:
            x = meta_information["mouse_coordinates"]["x"]
            y = meta_information["mouse_coordinates"]["y"]
            duration = meta_information.get("hover_duration", 1.0)
            
            if not self._validate_coordinates(x, y):
                return {"status": "error", "message": "Coordinates out of screen bounds"}
            
            # Move to position and wait
            pyautogui.moveTo(x, y, duration=0.1)
            time.sleep(duration)
            
            return {"status": "success", "message": f"Mouse hovered at ({x}, {y}) for {duration} seconds"}
        except Exception as e:
            self.logger.error(f"Failed to perform mouse hover: {str(e)}")
            return {"status": "error", "message": str(e)}

    def mouse_scroll(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform mouse scroll operation"""
        try:
            scroll_amount = meta_information["scroll_amount"]
            direction = meta_information["scroll_direction"].lower()
            
            # Convert scroll amount to positive or negative based on direction
            if direction == "down":
                scroll_amount = -abs(scroll_amount)
            else:  # up
                scroll_amount = abs(scroll_amount)
            
            pyautogui.scroll(scroll_amount)
            return {
                "status": "success", 
                "message": f"Scrolled {direction} by {abs(scroll_amount)} units"
            }
        except Exception as e:
            self.logger.error(f"Failed to perform mouse scroll: {str(e)}")
            return {"status": "error", "message": str(e)}

    def mouse_move(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Move mouse through a series of coordinates"""
        try:
            path_coordinates = meta_information["path_coordinates"]
            movement_duration = meta_information.get("movement_duration", 1.0)
            
            # Validate all coordinates
            for coord in path_coordinates:
                if not self._validate_coordinates(coord["x"], coord["y"]):
                    return {"status": "error", "message": "Path contains coordinates out of screen bounds"}
            
            # Calculate time per movement
            if len(path_coordinates) > 1:
                duration_per_move = movement_duration / (len(path_coordinates) - 1)
            else:
                duration_per_move = movement_duration
            
            # Move through each coordinate
            for coord in path_coordinates:
                pyautogui.moveTo(coord["x"], coord["y"], duration=duration_per_move)
            
            return {"status": "success", "message": "Mouse movement completed successfully"}
        except Exception as e:
            self.logger.error(f"Failed to perform mouse movement: {str(e)}")
            return {"status": "error", "message": str(e)}

    def context_menu_open(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Open context menu at specified coordinates"""
        try:
            x = meta_information["mouse_coordinates"]["x"]
            y = meta_information["mouse_coordinates"]["y"]
            
            if not self._validate_coordinates(x, y):
                return {"status": "error", "message": "Coordinates out of screen bounds"}
            
            # Move to position and perform right click
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.rightClick()
            
            # Wait for menu to appear
            time.sleep(0.2)
            
            return {
                "status": "success", 
                "message": f"Context menu opened at ({x}, {y})"
            }
        except Exception as e:
            self.logger.error(f"Failed to open context menu: {str(e)}")
            return {"status": "error", "message": str(e)}

    def application_open(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Open a Windows application"""
        try:
            app_path = meta_information["url_path_context"]["file_path"]
            win32api.ShellExecute(0, "open", app_path, None, None, 1)
            
            return {"status": "success", "message": f"Application opened: {app_path}"}
        except Exception as e:
            self.logger.error(f"Failed to open application: {str(e)}")
            return {"status": "error", "message": str(e)}

    def window_resize(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Resize a window to specified dimensions"""
        try:
            window_name = meta_information["element_context"]["element_name"]
            new_width = meta_information["new_size"]["width"]
            new_height = meta_information["new_size"]["height"]
            
            hwnd = win32gui.FindWindow(None, window_name)
            if hwnd:
                win32gui.SetWindowPos(
                    hwnd, 
                    win32con.HWND_TOP,
                    0, 0, 
                    new_width, 
                    new_height,
                    win32con.SWP_NOMOVE
                )
                return {"status": "success", "message": "Window resized successfully"}
            else:
                return {"status": "error", "message": "Window not found"}
        except Exception as e:
            self.logger.error(f"Failed to resize window: {str(e)}")
            return {"status": "error", "message": str(e)}

    def process_start(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Start a Windows process"""
        try:
            process_path = meta_information["url_path_context"]["file_path"]
            startup_info = win32process.STARTUPINFO()
            process_info = win32process.CreateProcess(
                process_path,
                None,
                None,
                None,
                0,
                0,
                None,
                None,
                startup_info
            )
            return {
                "status": "success", 
                "message": f"Process started with PID: {process_info[2]}"
            }
        except Exception as e:
            self.logger.error(f"Failed to start process: {str(e)}")
            return {"status": "error", "message": str(e)}

    def process_end(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """End a Windows process"""
        try:
            process_id = meta_information["process_id"]
            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, process_id)
            if handle:
                win32api.TerminateProcess(handle, 0)
                win32api.CloseHandle(handle)
                return {"status": "success", "message": f"Process {process_id} terminated"}
            return {"status": "error", "message": "Process not found"}
        except Exception as e:
            self.logger.error(f"Failed to end process: {str(e)}")
            return {"status": "error", "message": str(e)}

    def keystroke(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a single keystroke"""
        try:
            key = meta_information["key"]
            modifiers = meta_information.get("modifiers", [])
            
            # Hold down modifier keys if any
            for modifier in modifiers:
                pyautogui.keyDown(self.modifier_keys.get(modifier.lower()))
            
            # Press and release the main key
            pyautogui.press(key)
            
            # Release modifier keys
            for modifier in reversed(modifiers):
                pyautogui.keyUp(self.modifier_keys.get(modifier.lower()))
            
            return {
                "status": "success",
                "message": f"Keystroke performed: {'+'.join(modifiers + [key])}"
            }
        except Exception as e:
            self.logger.error(f"Failed to perform keystroke: {str(e)}")
            return {"status": "error", "message": str(e)}

    def key_combination(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform a combination of keystrokes"""
        try:
            keys = meta_information["keys"]
            
            # Convert keys to PyAutoGUI format
            key_combination = '+'.join(keys)
            
            # Use PyAutoGUI's hotkey function
            pyautogui.hotkey(*keys)
            
            return {
                "status": "success",
                "message": f"Key combination performed: {key_combination}"
            }
        except Exception as e:
            self.logger.error(f"Failed to perform key combination: {str(e)}")
            return {"status": "error", "message": str(e)}

    def typing_sequence(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Type a sequence of text"""
        try:
            text = meta_information["text_entered"]
            typing_speed = meta_information.get("typing_speed_wpm", 100)
            
            # Convert WPM to seconds per character
            # Average word length is 5 characters
            interval = 60 / (typing_speed * 5)
            
            # Type the text with the calculated interval
            pyautogui.write(text, interval=interval)
            
            return {
                "status": "success",
                "message": f"Typed text: {text} at {typing_speed} WPM"
            }
        except Exception as e:
            self.logger.error(f"Failed to type sequence: {str(e)}")
            return {"status": "error", "message": str(e)}

    def special_key_press(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Press a special key"""
        try:
            key = meta_information["key"]
            if key not in self.special_keys:
                return {"status": "error", "message": f"Unsupported special key: {key}"}
            
            pyautogui.press(self.special_keys[key.lower()])
            
            return {
                "status": "success",
                "message": f"Special key pressed: {key}"
            }
        except Exception as e:
            self.logger.error(f"Failed to press special key: {str(e)}")
            return {"status": "error", "message": str(e)}

    def shortcut_use(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Use a keyboard shortcut"""
        try:
            shortcut = meta_information["shortcut"]
            keys = shortcut.split('+')
            
            # Clean and validate keys
            keys = [k.strip().lower() for k in keys]
            
            # Use PyAutoGUI's hotkey function for the shortcut
            pyautogui.hotkey(*keys)
            
            return {
                "status": "success",
                "message": f"Shortcut used: {shortcut}"
            }
        except Exception as e:
            self.logger.error(f"Failed to use shortcut: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _send_win32_input(self, key_code: int, flags: int = 0) -> None:
        """Helper method to send input using win32api"""
        win32api.keybd_event(key_code, 0, flags, 0)

    def _handle_special_character(self, char: str) -> None:
        """Helper method to handle special characters using win32api"""
        # Get virtual key code and shift state
        vk_code = win32api.VkKeyScan(char)
        needs_shift = (vk_code >> 8) & 1
        
        # Press shift if needed
        if needs_shift:
            self._send_win32_input(win32con.VK_SHIFT, 0)
        
        # Press and release the key
        self._send_win32_input(vk_code & 0xFF, 0)
        self._send_win32_input(vk_code & 0xFF, win32con.KEYEVENTF_KEYUP)
        
        # Release shift if needed
        if needs_shift:
            self._send_win32_input(win32con.VK_SHIFT, win32con.KEYEVENTF_KEYUP)

    def type_with_win32(self, text: str, interval: float = 0.0) -> None:
        """Alternative typing method using win32api for special cases"""
        for char in text:
            try:
                if char.isprintable():
                    self._handle_special_character(char)
                else:
                    # Handle non-printable characters (e.g., newlines)
                    pyautogui.press(char)
                if interval > 0:
                    time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Failed to type character '{char}': {str(e)}")
                raise

    def _validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """Validate file path and return file information"""
        try:
            path = pathlib.Path(file_path)
            
            if not path.parent.exists():
                return {
                    "valid": False,
                    "message": f"Directory does not exist: {path.parent}"
                }
            
            file_info = {
                "valid": True,
                "path": str(path),
                "name": path.name,
                "extension": path.suffix,
                "parent": str(path.parent),
                "exists": path.exists(),
                "is_file": path.is_file() if path.exists() else None,
                "size": path.stat().st_size if path.exists() else None,
                "created": datetime.fromtimestamp(path.stat().st_ctime) if path.exists() else None,
                "modified": datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else None
            }
            
            return file_info
        except Exception as e:
            return {"valid": False, "message": str(e)}

    def file_open(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Open a file with its default application"""
        try:
            file_path = meta_information["url_path_context"]["file_path"]
            file_info = self._validate_file_path(file_path)
            
            if not file_info["valid"]:
                return {"status": "error", "message": file_info["message"]}
            
            if not file_info["exists"]:
                return {"status": "error", "message": f"File not found: {file_path}"}
            
            # Open file with default application
            os.startfile(file_path)
            
            return {
                "status": "success",
                "message": f"File opened: {file_path}",
                "file_info": file_info
            }
        except Exception as e:
            self.logger.error(f"Failed to open file: {str(e)}")
            return {"status": "error", "message": str(e)}

    def file_save(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Save file operation - typically handled by active application"""
        try:
            file_path = meta_information["url_path_context"]["file_path"]
            save_method = meta_information.get("save_method", "direct")
            
            if save_method == "shortcut":
                # Simulate Ctrl+S
                self.shortcut_use({"shortcut": "ctrl+s"})
                time.sleep(0.5)  # Wait for save dialog
                
                if file_path:
                    # Type the file path
                    self.typing_sequence({"text_entered": file_path})
                    time.sleep(0.2)
                    # Press Enter to confirm
                    self.special_key_press({"key": "enter"})
            
            return {
                "status": "success",
                "message": f"File save initiated: {file_path}"
            }
        except Exception as e:
            self.logger.error(f"Failed to save file: {str(e)}")
            return {"status": "error", "message": str(e)}

    def file_delete(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Delete a file with optional recycle bin use"""
        try:
            file_path = meta_information["url_path_context"]["file_path"]
            use_recycle_bin = meta_information.get("use_recycle_bin", True)
            file_info = self._validate_file_path(file_path)
            
            if not file_info["valid"]:
                return {"status": "error", "message": file_info["message"]}
            
            if not file_info["exists"]:
                return {"status": "error", "message": f"File not found: {file_path}"}
            
            if use_recycle_bin:
                if SEND2TRASH_AVAILABLE:
                    send2trash.send2trash(file_path)
                else:
                    # Fallback to permanent delete if send2trash is not available
                    os.remove(file_path)
                    return {
                        "status": "warning",
                        "message": "send2trash package not available, file permanently deleted"
                    }
            else:
                os.remove(file_path)
            
            return {
                "status": "success",
                "message": f"File {'moved to recycle bin' if use_recycle_bin and SEND2TRASH_AVAILABLE else 'deleted'}: {file_path}",
                "file_info": file_info
            }
        except Exception as e:
            self.logger.error(f"Failed to delete file: {str(e)}")
            return {"status": "error", "message": str(e)}

    def file_rename(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Rename a file"""
        try:
            old_path = meta_information["url_path_context"]["file_path"]
            new_name = meta_information["new_file_name"]
            file_info = self._validate_file_path(old_path)
            
            if not file_info["valid"]:
                return {"status": "error", "message": file_info["message"]}
            
            if not file_info["exists"]:
                return {"status": "error", "message": f"File not found: {old_path}"}
            
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            if os.path.exists(new_path):
                return {"status": "error", "message": f"Destination file already exists: {new_path}"}
            
            os.rename(old_path, new_path)
            
            return {
                "status": "success",
                "message": f"File renamed from {old_path} to {new_path}",
                "old_path": old_path,
                "new_path": new_path
            }
        except Exception as e:
            self.logger.error(f"Failed to rename file: {str(e)}")
            return {"status": "error", "message": str(e)}

    def file_move(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Move a file to a new location"""
        try:
            source_path = meta_information["source_path"]
            dest_path = meta_information["destination_path"]
            
            source_info = self._validate_file_path(source_path)
            dest_info = self._validate_file_path(dest_path)
            
            if not source_info["valid"]:
                return {"status": "error", "message": source_info["message"]}
            
            if not source_info["exists"]:
                return {"status": "error", "message": f"Source file not found: {source_path}"}
            
            if os.path.exists(dest_path):
                return {"status": "error", "message": f"Destination file already exists: {dest_path}"}
            
            shutil.move(source_path, dest_path)
            
            return {
                "status": "success",
                "message": f"File moved from {source_path} to {dest_path}",
                "source_info": source_info,
                "destination_path": dest_path
            }
        except Exception as e:
            self.logger.error(f"Failed to move file: {str(e)}")
            return {"status": "error", "message": str(e)}

    def file_copy(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Copy a file to a new location"""
        try:
            source_path = meta_information["source_path"]
            dest_path = meta_information["destination_path"]
            preserve_metadata = meta_information.get("preserve_metadata", True)
            
            source_info = self._validate_file_path(source_path)
            dest_info = self._validate_file_path(dest_path)
            
            if not source_info["valid"]:
                return {"status": "error", "message": source_info["message"]}
            
            if not source_info["exists"]:
                return {"status": "error", "message": f"Source file not found: {source_path}"}
            
            if os.path.exists(dest_path):
                return {"status": "error", "message": f"Destination file already exists: {dest_path}"}
            
            if preserve_metadata:
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copy(source_path, dest_path)
            
            return {
                "status": "success",
                "message": f"File copied from {source_path} to {dest_path}",
                "source_info": source_info,
                "destination_path": dest_path
            }
        except Exception as e:
            self.logger.error(f"Failed to copy file: {str(e)}")
            return {"status": "error", "message": str(e)}

    def file_upload(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Handle file upload through simulated keyboard/mouse actions"""
        try:
            file_path = meta_information["url_path_context"]["file_path"]
            upload_button = meta_information.get("upload_button_coordinates")
            
            file_info = self._validate_file_path(file_path)
            if not file_info["valid"]:
                return {"status": "error", "message": file_info["message"]}
            
            # Click upload button if coordinates provided
            if upload_button:
                self.left_click({"mouse_coordinates": upload_button})
                time.sleep(0.5)
            
            # Type the file path
            self.typing_sequence({"text_entered": file_path})
            time.sleep(0.2)
            
            # Press Enter to confirm
            self.special_key_press({"key": "enter"})
            
            return {
                "status": "success",
                "message": f"File upload initiated: {file_path}",
                "file_info": file_info
            }
        except Exception as e:
            self.logger.error(f"Failed to initiate file upload: {str(e)}")
            return {"status": "error", "message": str(e)}

    def file_download(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Handle file download through simulated keyboard/mouse actions"""
        try:
            save_path = meta_information["save_location"]
            download_link = meta_information.get("download_coordinates")
            
            # Validate save location
            save_info = self._validate_file_path(save_path)
            if not save_info["valid"]:
                return {"status": "error", "message": save_info["message"]}
            
            # Click download link if coordinates provided
            if download_link:
                self.left_click({"mouse_coordinates": download_link})
                time.sleep(0.5)
            
            # Wait for save dialog and handle it
            time.sleep(1)  # Wait for download dialog
            
            # Type the save path
            self.typing_sequence({"text_entered": save_path})
            time.sleep(0.2)
            
            # Press Enter to confirm
            self.special_key_press({"key": "enter"})
            
            return {
                "status": "success",
                "message": f"File download initiated to: {save_path}"
            }
        except Exception as e:
            self.logger.error(f"Failed to initiate file download: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_word_app(self) -> Optional[win32com.client.CDispatch]:
        """Get or create Word application instance"""
        try:
            if self.word_app is None:
                self.word_app = win32com.client.Dispatch("Word.Application")
                self.word_app.Visible = True
            return self.word_app
        except Exception as e:
            self.logger.error(f"Failed to get Word application: {str(e)}")
            return None

    def text_selection(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Select text in active Word document"""
        try:
            word = self._get_word_app()
            if not word:
                return {"status": "error", "message": "Could not access Word application"}

            selection_type = meta_information.get("selection_type", "manual")
            
            if selection_type == "manual":
                # Manual selection using keyboard shortcuts
                start_pos = meta_information.get("selection_start_position", 0)
                end_pos = meta_information.get("selection_end_position", 0)
                
                # Move to start position
                word.Selection.Start = start_pos
                word.Selection.End = end_pos
            
            elif selection_type == "word":
                # Select current word
                word.Selection.WordLeft(Unit=1, Extend=1)
            
            elif selection_type == "line":
                # Select current line
                word.Selection.HomeKey(Unit=5, Extend=1)  # 5 = Line
            
            elif selection_type == "paragraph":
                # Select current paragraph
                word.Selection.Paragraphs(1).Range.Select()
            
            elif selection_type == "all":
                # Select all text
                word.Selection.WholeStory()
            
            return {
                "status": "success",
                "message": f"Text selected using method: {selection_type}"
            }
        except Exception as e:
            self.logger.error(f"Failed to select text: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _select_text(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper function to select text using various methods"""
        try:
            selection_type = meta_information.get("selection_type", "keyboard")
            
            if selection_type == "keyboard":
                # Get selection range
                start_pos = meta_information.get("selection_start_position", 0)
                end_pos = meta_information.get("selection_end_position", 0)
                
                # Move to start position (if specified)
                if "start_coordinates" in meta_information:
                    start_x = meta_information["start_coordinates"]["x"]
                    start_y = meta_information["start_coordinates"]["y"]
                    pyautogui.moveTo(start_x, start_y, duration=0.1)
                    pyautogui.click()
                
                # Hold shift and move to end position
                pyautogui.keyDown('shift')
                
                if "end_coordinates" in meta_information:
                    # Mouse-based selection
                    end_x = meta_information["end_coordinates"]["x"]
                    end_y = meta_information["end_coordinates"]["y"]
                    pyautogui.moveTo(end_x, end_y, duration=0.1)
                    pyautogui.click()
                else:
                    # Keyboard-based selection
                    for _ in range(end_pos - start_pos):
                        pyautogui.press('right')
                
                pyautogui.keyUp('shift')
                
            elif selection_type == "mouse":
                # Mouse drag selection
                start_x = meta_information["start_coordinates"]["x"]
                start_y = meta_information["start_coordinates"]["y"]
                end_x = meta_information["end_coordinates"]["x"]
                end_y = meta_information["end_coordinates"]["y"]
                
                pyautogui.moveTo(start_x, start_y, duration=0.1)
                pyautogui.mouseDown()
                pyautogui.moveTo(end_x, end_y, duration=0.2)
                pyautogui.mouseUp()
                
            elif selection_type == "shortcut":
                # Common text selection shortcuts
                shortcut_type = meta_information.get("shortcut_type", "")
                
                if shortcut_type == "select_all":
                    pyautogui.hotkey('ctrl', 'a')
                elif shortcut_type == "select_word":
                    pyautogui.doubleClick()
                elif shortcut_type == "select_line":
                    pyautogui.tripleClick()
                elif shortcut_type == "select_paragraph":
                    pyautogui.click(clicks=4)
            
            return {
                "status": "success",
                "message": f"Text selected using {selection_type} method"
            }
        except Exception as e:
            self.logger.error(f"Failed to select text: {str(e)}")
            return {"status": "error", "message": str(e)}

    def select_text(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Public method to select text based on context"""
        try:
            # Check if we're in Word
            if meta_information.get("application_context", {}).get("application_name") == "Microsoft Word":
                return self.text_selection(meta_information)  # Use Word-specific selection
            
            # For other applications, use general text selection
            return self._select_text(meta_information)
            
        except Exception as e:
            self.logger.error(f"Failed to select text: {str(e)}")
            return {"status": "error", "message": str(e)}

    def copy(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Copy selected text"""
        try:
            # If no text is selected, try to select it first
            if meta_information.get("select_before_copy", False):
                selection_result = self.select_text(meta_information)
                if selection_result["status"] == "error":
                    return selection_result
            
            # Perform copy operation
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.1)  # Wait for clipboard to update
            
            return {
                "status": "success",
                "message": "Text copied to clipboard"
            }
        except Exception as e:
            self.logger.error(f"Failed to copy text: {str(e)}")
            return {"status": "error", "message": str(e)}

    def cut(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Cut selected text"""
        try:
            # If no text is selected, try to select it first
            if meta_information.get("select_before_cut", False):
                selection_result = self.select_text(meta_information)
                if selection_result["status"] == "error":
                    return selection_result
            
            # Perform cut operation
            pyautogui.hotkey('ctrl', 'x')
            time.sleep(0.1)  # Wait for clipboard to update
            
            return {
                "status": "success",
                "message": "Text cut to clipboard"
            }
        except Exception as e:
            self.logger.error(f"Failed to cut text: {str(e)}")
            return {"status": "error", "message": str(e)}

    def paste(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Paste text at current position"""
        try:
            paste_type = meta_information.get("paste_type", "normal")
            
            if paste_type == "plain_text":
                # Paste as plain text (Ctrl+Shift+V in many applications)
                pyautogui.hotkey('ctrl', 'shift', 'v')
            else:
                # Normal paste
                pyautogui.hotkey('ctrl', 'v')
            
            time.sleep(0.1)  # Wait for paste to complete
            
            return {
                "status": "success",
                "message": f"Text pasted using {paste_type} method"
            }
        except Exception as e:
            self.logger.error(f"Failed to paste text: {str(e)}")
            return {"status": "error", "message": str(e)}

    def undo(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Undo last action in Word"""
        try:
            word = self._get_word_app()
            if not word:
                return {"status": "error", "message": "Could not access Word application"}
            
            times = meta_information.get("undo_steps", 1)
            for _ in range(times):
                word.Application.Undo()
            
            return {
                "status": "success",
                "message": f"Undid {times} action(s)"
            }
        except Exception as e:
            self.logger.error(f"Failed to undo: {str(e)}")
            return {"status": "error", "message": str(e)}

    def redo(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Redo last undone action in Word"""
        try:
            word = self._get_word_app()
            if not word:
                return {"status": "error", "message": "Could not access Word application"}
            
            times = meta_information.get("redo_steps", 1)
            for _ in range(times):
                word.Application.Redo()
            
            return {
                "status": "success",
                "message": f"Redid {times} action(s)"
            }
        except Exception as e:
            self.logger.error(f"Failed to redo: {str(e)}")
            return {"status": "error", "message": str(e)}

    def formatting_text(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Apply formatting to selected text in Word"""
        try:
            word = self._get_word_app()
            if not word:
                return {"status": "error", "message": "Could not access Word application"}
            
            formatting = meta_information.get("formatting_changes", {})
            
            # Apply font formatting
            if "font" in formatting:
                word.Selection.Font.Name = formatting["font"]
            if "size" in formatting:
                word.Selection.Font.Size = formatting["size"]
            if "bold" in formatting:
                word.Selection.Font.Bold = formatting["bold"]
            if "italic" in formatting:
                word.Selection.Font.Italic = formatting["italic"]
            if "underline" in formatting:
                word.Selection.Font.Underline = formatting["underline"]
            if "color" in formatting:
                # Convert hex color to RGB
                color = formatting["color"].lstrip('#')
                rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                word.Selection.Font.Color = rgb[0] + (rgb[1] * 256) + (rgb[2] * 256 * 256)
            
            return {
                "status": "success",
                "message": "Formatting applied successfully",
                "formatting_applied": formatting
            }
        except Exception as e:
            self.logger.error(f"Failed to apply formatting: {str(e)}")
            return {"status": "error", "message": str(e)}

    def table_editing(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Edit table in Word document"""
        try:
            word = self._get_word_app()
            if not word:
                return {"status": "error", "message": "Could not access Word application"}
            
            table_action = meta_information.get("table_action", "")
            table_location = meta_information.get("table_location", {})
            table_changes = meta_information.get("table_changes", {})
            
            # Get the active table
            if word.Selection.Tables.Count > 0:
                table = word.Selection.Tables(1)
            else:
                return {"status": "error", "message": "No table selected"}
            
            if table_action == "add_row":
                row = table_location.get("row", 1)
                table.Rows.Add(table.Rows(row))
            
            elif table_action == "add_column":
                column = table_location.get("column", 1)
                table.Columns.Add(table.Columns(column))
            
            elif table_action == "delete_row":
                row = table_location.get("row", 1)
                table.Rows(row).Delete()
            
            elif table_action == "delete_column":
                column = table_location.get("column", 1)
                table.Columns(column).Delete()
            
            elif table_action == "modify_cells":
                for cell_change in table_changes.get("cells_modified", []):
                    row = cell_change.get("row", 1)
                    column = cell_change.get("column", 1)
                    new_value = cell_change.get("new_value", "")
                    table.Cell(row, column).Range.Text = new_value
            
            return {
                "status": "success",
                "message": f"Table {table_action} completed successfully"
            }
        except Exception as e:
            self.logger.error(f"Failed to edit table: {str(e)}")
            return {"status": "error", "message": str(e)}

    def application_close(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Close a Windows application"""
        try:
            # Get window handle by application name
            window_name = meta_information["element_context"]["element_name"]
            
            # Try to find window with exact name
            hwnd = win32gui.FindWindow(None, window_name)
            
            # If not found, try to find window containing the name
            if not hwnd:
                def callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if window_name in title:
                            windows.append(hwnd)
                    return True
                
                windows = []
                win32gui.EnumWindows(callback, windows)
                
                if windows:
                    hwnd = windows[0]  # Use the first matching window
            
            if not hwnd:
                return {"status": "error", "message": f"Application window not found: {window_name}"}
            
            # Get actual window title for logging
            actual_title = win32gui.GetWindowText(hwnd)
            
            # Try graceful close first
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
            # Wait for window to close
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 second timeout
                if not win32gui.IsWindow(hwnd):
                    return {"status": "success", "message": f"Application closed: {actual_title}"}
                time.sleep(0.1)
            
            # Force close if necessary
            if meta_information.get("force_close", False):
                # Get process ID from window handle
                _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, process_id)
                if handle:
                    win32api.TerminateProcess(handle, 0)
                    win32api.CloseHandle(handle)
                    return {"status": "success", "message": f"Application force closed: {actual_title}"}
            
            return {"status": "error", "message": f"Failed to close application: {actual_title}"}
        except Exception as e:
            self.logger.error(f"Failed to close application: {str(e)}")
            return {"status": "error", "message": str(e)}

    def window_move(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Move a window to specified coordinates"""
        try:
            window_name = meta_information["element_context"]["element_name"]
            new_x = meta_information["new_position"]["x"]
            new_y = meta_information["new_position"]["y"]
            
            # Try to find window with exact name
            hwnd = win32gui.FindWindow(None, window_name)
            
            # If not found, try to find window containing the name
            if not hwnd:
                def callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if window_name in title:
                            windows.append(hwnd)
                    return True
                
                windows = []
                win32gui.EnumWindows(callback, windows)
                
                if windows:
                    hwnd = windows[0]  # Use the first matching window
            
            if not hwnd:
                return {"status": "error", "message": f"Window not found: {window_name}"}
            
            # Get current window position and size
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            # Move window
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOP,
                new_x,
                new_y,
                width,
                height,
                win32con.SWP_NOSIZE
            )
            
            # Get actual window title for logging
            actual_title = win32gui.GetWindowText(hwnd)
            
            return {
                "status": "success",
                "message": f"Window '{actual_title}' moved to ({new_x}, {new_y})"
            }
        except Exception as e:
            self.logger.error(f"Failed to move window: {str(e)}")
            return {"status": "error", "message": str(e)}

    def system_login(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform Windows system login"""
        try:
            username = meta_information["username"]
            password = meta_information.get("password", "")
            
            # Simulate Ctrl+Alt+Delete if needed
            if meta_information.get("requires_ctrl_alt_del", False):
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt
                win32api.keybd_event(win32con.VK_DELETE, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_DELETE, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(1)
            
            # Type username
            pyautogui.write(username)
            pyautogui.press('tab')
            
            # Type password
            pyautogui.write(password)
            pyautogui.press('enter')
            
            return {
                "status": "success",
                "message": f"Login attempted for user: {username}"
            }
        except Exception as e:
            self.logger.error(f"Failed to perform system login: {str(e)}")
            return {"status": "error", "message": str(e)}

    def system_logout(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Perform Windows system logout"""
        try:
            # Open Start menu
            pyautogui.press('win')
            time.sleep(0.5)
            
            # Click user icon
            if "user_icon_coordinates" in meta_information:
                coords = meta_information["user_icon_coordinates"]
                self.left_click({"mouse_coordinates": coords})
            else:
                # Alternative: Use Windows + L
                pyautogui.hotkey('win', 'l')
            
            time.sleep(0.5)
            
            # Click Sign out
            if "sign_out_coordinates" in meta_information:
                coords = meta_information["sign_out_coordinates"]
                self.left_click({"mouse_coordinates": coords})
            
            return {
                "status": "success",
                "message": "System logout initiated"
            }
        except Exception as e:
            self.logger.error(f"Failed to perform system logout: {str(e)}")
            return {"status": "error", "message": str(e)}

    def system_shutdown(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Initiate system shutdown"""
        try:
            shutdown_type = meta_information.get("shutdown_type", "normal")
            force = meta_information.get("force", False)
            
            if shutdown_type == "restart":
                flags = win32con.EWX_REBOOT
            else:  # normal shutdown
                flags = win32con.EWX_POWEROFF
            
            if force:
                flags |= win32con.EWX_FORCE
            
            # Initiate shutdown
            win32api.ExitWindowsEx(flags, 0)
            
            return {
                "status": "success",
                "message": f"System {shutdown_type} initiated"
            }
        except Exception as e:
            self.logger.error(f"Failed to initiate system shutdown: {str(e)}")
            return {"status": "error", "message": str(e)}

    def system_settings_change(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Change Windows system settings"""
        try:
            setting_type = meta_information["setting_type"]
            setting_value = meta_information["setting_value"]
            
            if setting_type == "display_brightness":
                # Change display brightness
                import wmi
                wmi_obj = wmi.WMI(namespace='wmi')
                monitors = wmi_obj.WmiMonitorBrightnessMethods()
                for monitor in monitors:
                    monitor.WmiSetBrightness(setting_value, 0)
            
            elif setting_type == "volume":
                # Change system volume
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(setting_value / 100.0, None)
            
            elif setting_type == "power_plan":
                # Change power plan
                os.system(f"powercfg /setactive {setting_value}")
            
            return {
                "status": "success",
                "message": f"System setting '{setting_type}' changed to {setting_value}"
            }
        except Exception as e:
            self.logger.error(f"Failed to change system settings: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_outlook_app(self) -> Optional[win32com.client.CDispatch]:
        """Get or create Outlook application instance"""
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            return outlook, namespace
        except Exception as e:
            self.logger.error(f"Failed to get Outlook application: {str(e)}")
            return None, None

    def email_read(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Read email from Outlook"""
        try:
            outlook, namespace = self._get_outlook_app()
            if not outlook:
                return {"status": "error", "message": "Could not access Outlook"}

            # Get the folder (default is inbox)
            folder_name = meta_information.get("folder_name", "Inbox")
            folder = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
            
            # Get email by ID or search criteria
            if "email_id" in meta_information:
                email = folder.Items.Find(f'@EntryID="{meta_information["email_id"]}"')
            else:
                # Search by subject/sender
                search_criteria = []
                if "subject" in meta_information:
                    search_criteria.append(f'@Subject="{meta_information["subject"]}"')
                if "sender" in meta_information:
                    search_criteria.append(f'@SenderEmailAddress="{meta_information["sender"]}"')
                
                filter_string = " AND ".join(search_criteria)
                email = folder.Items.Find(filter_string) if filter_string else None

            if not email:
                return {"status": "error", "message": "Email not found"}

            # Mark as read if specified
            if meta_information.get("mark_as_read", True):
                email.UnRead = False

            return {
                "status": "success",
                "message": "Email read successfully",
                "email_data": {
                    "subject": email.Subject,
                    "sender": email.SenderEmailAddress,
                    "received_time": str(email.ReceivedTime),
                    "body": email.Body,
                    "has_attachments": email.Attachments.Count > 0
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to read email: {str(e)}")
            return {"status": "error", "message": str(e)}

    def email_write(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Create new email in Outlook"""
        try:
            outlook, _ = self._get_outlook_app()
            if not outlook:
                return {"status": "error", "message": "Could not access Outlook"}

            # Create new email
            mail = outlook.CreateItem(0)  # 0 = olMailItem
            
            # Set email properties
            mail.Subject = meta_information.get("subject", "")
            mail.To = meta_information.get("to", "")
            mail.CC = meta_information.get("cc", "")
            mail.BCC = meta_information.get("bcc", "")
            mail.Body = meta_information.get("body", "")
            
            # Handle attachments
            attachments = meta_information.get("attachments", [])
            for attachment in attachments:
                if os.path.exists(attachment):
                    mail.Attachments.Add(attachment)

            # Save draft if specified
            if meta_information.get("save_draft", True):
                mail.Save()

            return {
                "status": "success",
                "message": "Email created successfully",
                "email_id": mail.EntryID
            }
        except Exception as e:
            self.logger.error(f"Failed to create email: {str(e)}")
            return {"status": "error", "message": str(e)}

    def email_send(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Send email from Outlook"""
        try:
            outlook, _ = self._get_outlook_app()
            if not outlook:
                return {"status": "error", "message": "Could not access Outlook"}

            # Get existing draft or create new email
            if "email_id" in meta_information:
                namespace = outlook.GetNamespace("MAPI")
                drafts = namespace.GetDefaultFolder(16)  # 16 = olFolderDrafts
                mail = drafts.Items.Find(f'@EntryID="{meta_information["email_id"]}"')
            else:
                # Create and configure new email
                result = self.email_write(meta_information)
                if result["status"] == "error":
                    return result
                mail = outlook.GetItemFromID(result["email_id"])

            # Send the email
            mail.Send()

            return {
                "status": "success",
                "message": "Email sent successfully"
            }
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return {"status": "error", "message": str(e)}

    def scan_inbox(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Scan Outlook inbox with specified criteria"""
        try:
            outlook, namespace = self._get_outlook_app()
            if not outlook:
                return {"status": "error", "message": "Could not access Outlook"}

            # Get inbox folder
            inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
            
            # Build search criteria
            criteria = []
            if "subject_keywords" in meta_information:
                subject_terms = [f'@Subject LIKE "%{kw}%"' for kw in meta_information["subject_keywords"]]
                criteria.append(f"({' OR '.join(subject_terms)})")
            
            if "sender_emails" in meta_information:
                sender_terms = [f'@SenderEmailAddress="{email}"' for email in meta_information["sender_emails"]]
                criteria.append(f"({' OR '.join(sender_terms)})")
            
            if "date_range" in meta_information:
                start_date = meta_information["date_range"]["start_date"]
                end_date = meta_information["date_range"]["end_date"]
                criteria.append(f'@ReceivedTime >= "{start_date}" AND @ReceivedTime <= "{end_date}"')

            # Apply filter
            filter_string = " AND ".join(criteria)
            matching_emails = []
            
            if filter_string:
                items = inbox.Items.Restrict(filter_string)
            else:
                items = inbox.Items

            # Collect matching emails
            for item in items:
                matching_emails.append({
                    "subject": item.Subject,
                    "sender": item.SenderEmailAddress,
                    "received_time": str(item.ReceivedTime),
                    "has_attachments": item.Attachments.Count > 0,
                    "email_id": item.EntryID
                })

            return {
                "status": "success",
                "message": f"Found {len(matching_emails)} matching emails",
                "emails": matching_emails
            }
        except Exception as e:
            self.logger.error(f"Failed to scan inbox: {str(e)}")
            return {"status": "error", "message": str(e)}

    def email_search(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Search for specific emails in Outlook"""
        try:
            outlook, namespace = self._get_outlook_app()
            if not outlook:
                return {"status": "error", "message": "Could not access Outlook"}

            # Get folder to search in
            folder_name = meta_information.get("folder_name", "Inbox")
            folder = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
            
            # Build advanced search criteria
            search_criteria = []
            
            # Text content search
            if "search_text" in meta_information:
                search_criteria.append(f'@Body LIKE "%{meta_information["search_text"]}%" OR '
                                    f'@Subject LIKE "%{meta_information["search_text"]}%"')
            
            # Attachment search
            if meta_information.get("has_attachments"):
                search_criteria.append("@Attachments.Count > 0")
            
            # Date range
            if "date_range" in meta_information:
                start_date = meta_information["date_range"]["start_date"]
                end_date = meta_information["date_range"]["end_date"]
                search_criteria.append(f'@ReceivedTime >= "{start_date}" AND @ReceivedTime <= "{end_date}"')
            
            # Importance level
            if "importance" in meta_information:
                search_criteria.append(f'@Importance = {meta_information["importance"]}')

            # Apply search
            filter_string = " AND ".join(search_criteria)
            search_results = []
            
            if filter_string:
                items = folder.Items.Restrict(filter_string)
            else:
                items = folder.Items

            # Sort if specified
            if "sort_by" in meta_information:
                items.Sort(f"[{meta_information['sort_by']}]", meta_information.get("sort_descending", True))

            # Collect results
            for item in items:
                search_results.append({
                    "subject": item.Subject,
                    "sender": item.SenderEmailAddress,
                    "received_time": str(item.ReceivedTime),
                    "has_attachments": item.Attachments.Count > 0,
                    "importance": item.Importance,
                    "email_id": item.EntryID
                })

            return {
                "status": "success",
                "message": f"Found {len(search_results)} matching emails",
                "search_results": search_results
            }
        except Exception as e:
            self.logger.error(f"Failed to search emails: {str(e)}")
            return {"status": "error", "message": str(e)}

    def dropdown_select(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Handle dropdown selection using various methods"""
        try:
            selection_method = meta_information.get("selection_method", "click")
            
            if selection_method == "click":
                # Click dropdown to open
                if "dropdown_coordinates" in meta_information:
                    self.left_click({"mouse_coordinates": meta_information["dropdown_coordinates"]})
                    time.sleep(0.2)
                
                # Click option
                if "option_coordinates" in meta_information:
                    self.left_click({"mouse_coordinates": meta_information["option_coordinates"]})
            
            elif selection_method == "keyboard":
                # Focus dropdown if coordinates provided
                if "dropdown_coordinates" in meta_information:
                    self.left_click({"mouse_coordinates": meta_information["dropdown_coordinates"]})
                    time.sleep(0.2)
                
                # Navigate to option using keyboard
                option_index = meta_information.get("option_index", 0)
                # Open dropdown
                self.special_key_press({"key": "down"})
                time.sleep(0.1)
                
                # Navigate to desired option
                for _ in range(option_index):
                    self.special_key_press({"key": "down"})
                    time.sleep(0.05)
                
                # Select option
                self.special_key_press({"key": "enter"})
            
            return {
                "status": "success",
                "message": "Dropdown selection completed"
            }
        except Exception as e:
            self.logger.error(f"Failed to select from dropdown: {str(e)}")
            return {"status": "error", "message": str(e)}

    def checkbox_toggle(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Toggle checkbox state"""
        try:
            # Click checkbox
            if "checkbox_coordinates" in meta_information:
                self.left_click({"mouse_coordinates": meta_information["checkbox_coordinates"]})
            
            # Verify state if coordinates for checking are provided
            desired_state = meta_information.get("desired_state", True)
            if "state_check_coordinates" in meta_information:
                # Add verification logic here if needed
                pass
            
            return {
                "status": "success",
                "message": f"Checkbox toggled to {'checked' if desired_state else 'unchecked'}"
            }
        except Exception as e:
            self.logger.error(f"Failed to toggle checkbox: {str(e)}")
            return {"status": "error", "message": str(e)}

    def slider_adjustment(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Adjust slider control"""
        try:
            start_x = meta_information["slider_coordinates"]["x"]
            start_y = meta_information["slider_coordinates"]["y"]
            target_value = meta_information["target_value"]  # 0 to 100
            slider_width = meta_information.get("slider_width", 100)
            
            # Calculate target x coordinate based on desired value
            target_x = start_x + (slider_width * (target_value / 100))
            
            # Click and drag slider
            pyautogui.moveTo(start_x, start_y, duration=0.1)
            pyautogui.mouseDown()
            pyautogui.moveTo(target_x, start_y, duration=0.2)
            pyautogui.mouseUp()
            
            return {
                "status": "success",
                "message": f"Slider adjusted to {target_value}%"
            }
        except Exception as e:
            self.logger.error(f"Failed to adjust slider: {str(e)}")
            return {"status": "error", "message": str(e)}

    def calendar_interaction(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Interact with calendar control"""
        try:
            interaction_type = meta_information.get("interaction_type", "select_date")
            
            if interaction_type == "select_date":
                # Click calendar to open
                if "calendar_coordinates" in meta_information:
                    self.left_click({"mouse_coordinates": meta_information["calendar_coordinates"]})
                    time.sleep(0.2)
                
                # Navigate to desired date
                target_date = meta_information.get("target_date", {})
                current_date = datetime.now()
                
                # Navigate months if needed
                month_diff = (target_date.year - current_date.year) * 12 + target_date.month - current_date.month
                
                for _ in range(abs(month_diff)):
                    if month_diff > 0:
                        self.special_key_press({"key": "pagedown"})
                    else:
                        self.special_key_press({"key": "pageup"})
                    time.sleep(0.1)
                
                # Click date if coordinates provided
                if "date_coordinates" in meta_information:
                    self.left_click({"mouse_coordinates": meta_information["date_coordinates"]})
            
            return {
                "status": "success",
                "message": "Calendar interaction completed"
            }
        except Exception as e:
            self.logger.error(f"Failed to interact with calendar: {str(e)}")
            return {"status": "error", "message": str(e)}

    def loop(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Execute a sequence of actions in a loop"""
        try:
            iterations = meta_information.get("iterations", 1)
            actions = meta_information.get("actions", [])
            
            for iteration in range(iterations):
                for action in actions:
                    action_type = action.get("action_type")
                    action_meta = action.get("meta_information", {})
                    
                    # Get the corresponding method
                    method = getattr(self, action_type, None)
                    if method:
                        result = method(action_meta)
                        if result["status"] == "error":
                            return {
                                "status": "error",
                                "message": f"Loop failed at iteration {iteration + 1}: {result['message']}"
                            }
                    
                    # Wait between actions if specified
                    if "action_delay" in action:
                        time.sleep(action["action_delay"])
                
                # Wait between iterations if specified
                if "iteration_delay" in meta_information:
                    time.sleep(meta_information["iteration_delay"])
            
            return {
                "status": "success",
                "message": f"Loop completed {iterations} iterations"
            }
        except Exception as e:
            self.logger.error(f"Failed to execute loop: {str(e)}")
            return {"status": "error", "message": str(e)}

    def wait(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Wait for a specified duration"""
        try:
            duration = meta_information.get("duration", 1.0)
            time.sleep(duration)
            
            return {
                "status": "success",
                "message": f"Waited for {duration} seconds"
            }
        except Exception as e:
            self.logger.error(f"Failed to execute wait: {str(e)}")
            return {"status": "error", "message": str(e)}

    def wait_for(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Wait for a specific condition to be met"""
        try:
            condition_type = meta_information.get("condition_type", "")
            timeout = meta_information.get("timeout", 30)
            check_interval = meta_information.get("check_interval", 0.5)
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if condition_type == "pixel_color":
                    # Check pixel color at coordinates
                    x = meta_information["coordinates"]["x"]
                    y = meta_information["coordinates"]["y"]
                    expected_color = meta_information["expected_color"]
                    actual_color = pyautogui.pixel(x, y)
                    
                    if actual_color == expected_color:
                        return {
                            "status": "success",
                            "message": "Pixel color condition met"
                        }
                
                elif condition_type == "image_present":
                    # Check if image is present on screen
                    image_path = meta_information["image_path"]
                    try:
                        location = pyautogui.locateOnScreen(image_path, confidence=0.9)
                        if location:
                            return {
                                "status": "success",
                                "message": "Image found on screen",
                                "location": location
                            }
                    except:
                        pass
                
                elif condition_type == "window_exists":
                    # Check if window exists
                    window_name = meta_information["window_name"]
                    hwnd = win32gui.FindWindow(None, window_name)
                    if hwnd:
                        return {
                            "status": "success",
                            "message": f"Window '{window_name}' found"
                        }
                
                elif condition_type == "window_active":
                    # Check if window is active
                    window_name = meta_information["window_name"]
                    active_hwnd = win32gui.GetForegroundWindow()
                    active_window_name = win32gui.GetWindowText(active_hwnd)
                    
                    if active_window_name == window_name:
                        return {
                            "status": "success",
                            "message": f"Window '{window_name}' is active"
                        }
                
                # Wait before next check
                time.sleep(check_interval)
            
            return {
                "status": "error",
                "message": f"Condition not met within {timeout} seconds"
            }
        except Exception as e:
            self.logger.error(f"Failed to execute wait_for: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _handle_uac_dialog(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to handle User Account Control (UAC) dialog"""
        try:
            # Wait for UAC dialog
            time.sleep(1)  # Wait for dialog to appear
            
            # Look for UAC dialog
            uac_dialog = win32gui.FindWindow("#32770", "User Account Control")
            if uac_dialog:
                # Find and click "Yes" button
                yes_button = win32gui.FindWindowEx(uac_dialog, None, "Button", "&Yes")
                if yes_button:
                    win32gui.SendMessage(yes_button, win32con.BM_CLICK, 0, 0)
                    return {"status": "success", "message": "UAC dialog accepted"}
            
            return {"status": "error", "message": "UAC dialog not found"}
        except Exception as e:
            self.logger.error(f"Failed to handle UAC dialog: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_input(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to input 2FA code"""
        try:
            code = meta_information.get("verification_code", "")
            input_method = meta_information.get("input_method", "keyboard")
            
            if input_method == "keyboard":
                # Type the code
                self.typing_sequence({"text_entered": code})
                time.sleep(0.2)
                self.special_key_press({"key": "enter"})
            elif input_method == "clipboard":
                # Use clipboard for sensitive input
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(code)
                win32clipboard.CloseClipboard()
                
                # Paste the code
                self.shortcut_use({"shortcut": "ctrl+v"})
                time.sleep(0.2)
                self.special_key_press({"key": "enter"})
            
            return {"status": "success", "message": "2FA code entered"}
        except Exception as e:
            self.logger.error(f"Failed to input 2FA code: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_verify_success(self, meta_information: Dict[str, Any]) -> bool:
        """Helper method to verify 2FA success"""
        try:
            # Wait for success indicator
            success_timeout = meta_information.get("success_timeout", 10)
            check_interval = meta_information.get("check_interval", 0.5)
            start_time = time.time()
            
            while time.time() - start_time < success_timeout:
                if "success_image" in meta_information:
                    # Check for success image on screen
                    try:
                        if pyautogui.locateOnScreen(meta_information["success_image"], confidence=0.9):
                            return True
                    except:
                        pass
                
                if "success_pixel" in meta_information:
                    # Check for success pixel color
                    x = meta_information["success_pixel"]["x"]
                    y = meta_information["success_pixel"]["y"]
                    expected_color = meta_information["success_pixel"]["color"]
                    if pyautogui.pixel(x, y) == expected_color:
                        return True
                
                time.sleep(check_interval)
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to verify 2FA success: {str(e)}")
            return False

    def _2fa_handle_error(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to handle 2FA errors"""
        try:
            # Check for error indicators
            if "error_image" in meta_information:
                error_location = pyautogui.locateOnScreen(meta_information["error_image"], confidence=0.9)
                if error_location:
                    return {"status": "error", "message": "2FA error detected"}
            
            return {"status": "success", "message": "No 2FA errors detected"}
        except Exception as e:
            self.logger.error(f"Failed to handle 2FA error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_backup_code(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to handle backup code entry"""
        try:
            if "backup_code" in meta_information:
                # Click backup code option if coordinates provided
                if "backup_option_coordinates" in meta_information:
                    self.left_click({"mouse_coordinates": meta_information["backup_option_coordinates"]})
                    time.sleep(0.5)
                
                # Enter backup code
                return self._2fa_input({"verification_code": meta_information["backup_code"]})
            
            return {"status": "error", "message": "No backup code provided"}
        except Exception as e:
            self.logger.error(f"Failed to handle backup code: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_handle_method_selection(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to handle 2FA method selection"""
        try:
            method = meta_information.get("2fa_method", "")
            
            if "method_coordinates" in meta_information:
                # Click the specified 2FA method option
                self.left_click({"mouse_coordinates": meta_information["method_coordinates"]})
                time.sleep(0.5)
                return {"status": "success", "message": f"Selected 2FA method: {method}"}
            
            return {"status": "error", "message": "No method coordinates provided"}
        except Exception as e:
            self.logger.error(f"Failed to select 2FA method: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_wait_for_code(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to wait for 2FA code (e.g., SMS or email)"""
        try:
            timeout = meta_information.get("code_timeout", 60)
            check_interval = meta_information.get("check_interval", 5)
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check email if method is email
                if meta_information.get("2fa_method") == "email":
                    email_result = self.email_search({
                        "search_text": meta_information.get("email_search_text", "verification code"),
                        "folder_name": "Inbox",
                        "sort_by": "ReceivedTime",
                        "sort_descending": True
                    })
                    
                    if email_result["status"] == "success" and email_result["search_results"]:
                        return {"status": "success", "message": "2FA code email received"}
                
                time.sleep(check_interval)
            
            return {"status": "error", "message": "Timeout waiting for 2FA code"}
        except Exception as e:
            self.logger.error(f"Failed to wait for 2FA code: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_extract_code(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to extract 2FA code from email or SMS"""
        try:
            if meta_information.get("2fa_method") == "email":
                email_result = self.email_read({
                    "folder_name": "Inbox",
                    "search_text": meta_information.get("email_search_text", "verification code")
                })
                
                if email_result["status"] == "success":
                    # Extract code using regex pattern
                    import re
                    pattern = meta_information.get("code_pattern", r"\b\d{6}\b")
                    match = re.search(pattern, email_result["email_data"]["body"])
                    if match:
                        return {
                            "status": "success",
                            "message": "2FA code extracted",
                            "code": match.group(0)
                        }
            
            return {"status": "error", "message": "Failed to extract 2FA code"}
        except Exception as e:
            self.logger.error(f"Failed to extract 2FA code: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_cleanup(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to clean up after 2FA"""
        try:
            # Clear clipboard if used
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            
            return {"status": "success", "message": "2FA cleanup completed"}
        except Exception as e:
            self.logger.error(f"Failed to cleanup after 2FA: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_retry(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Helper method to handle 2FA retry"""
        try:
            max_retries = meta_information.get("max_retries", 3)
            current_retry = meta_information.get("current_retry", 0)
            
            if current_retry < max_retries:
                meta_information["current_retry"] = current_retry + 1
                return self._2fa_interaction(meta_information)
            
            return {"status": "error", "message": f"Max retries ({max_retries}) exceeded"}
        except Exception as e:
            self.logger.error(f"Failed to retry 2FA: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_interaction(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Internal method to handle complete 2FA flow"""
        try:
            # Select 2FA method if needed
            if "method_coordinates" in meta_information:
                method_result = self._2fa_handle_method_selection(meta_information)
                if method_result["status"] == "error":
                    return method_result
            
            # Wait for and extract code if needed
            if meta_information.get("wait_for_code", False):
                wait_result = self._2fa_wait_for_code(meta_information)
                if wait_result["status"] == "error":
                    return wait_result
                
                extract_result = self._2fa_extract_code(meta_information)
                if extract_result["status"] == "success":
                    meta_information["verification_code"] = extract_result["code"]
            
            # Input the code
            input_result = self._2fa_input(meta_information)
            if input_result["status"] == "error":
                return input_result
            
            # Verify success
            if not self._2fa_verify_success(meta_information):
                # Check for errors
                error_result = self._2fa_handle_error(meta_information)
                if error_result["status"] == "error":
                    # Try backup code if available
                    if "backup_code" in meta_information:
                        return self._2fa_backup_code(meta_information)
                    # Otherwise retry
                    return self._2fa_retry(meta_information)
            
            # Cleanup
            self._2fa_cleanup(meta_information)
            
            return {"status": "success", "message": "2FA completed successfully"}
        except Exception as e:
            self.logger.error(f"Failed to complete 2FA interaction: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _2fa_interaction(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Public method for 2FA interaction"""
        try:
            meta_information["current_retry"] = 0
            return self._2fa_interaction(meta_information)
        except Exception as e:
            self.logger.error(f"Failed to handle 2FA interaction: {str(e)}")
            return {"status": "error", "message": str(e)}

    def permission_request(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Handle Windows permission requests"""
        try:
            permission_type = meta_information.get("permission_type", "")
            
            if permission_type == "uac":
                return self._handle_uac_dialog(meta_information)
            
            elif permission_type == "firewall":
                # Handle Windows Firewall dialog
                firewall_dialog = win32gui.FindWindow(None, "Windows Security Alert")
                if firewall_dialog:
                    allow_button = win32gui.FindWindowEx(firewall_dialog, None, "Button", "Allow access")
                    if allow_button:
                        win32gui.SendMessage(allow_button, win32con.BM_CLICK, 0, 0)
                        return {"status": "success", "message": "Firewall access allowed"}
            
            elif permission_type == "app_permissions":
                # Handle modern Windows app permissions
                permission_dialog = win32gui.FindWindow(None, meta_information.get("dialog_title", ""))
                if permission_dialog:
                    allow_button = win32gui.FindWindowEx(permission_dialog, None, "Button", "Yes")
                    if allow_button:
                        win32gui.SendMessage(allow_button, win32con.BM_CLICK, 0, 0)
                        return {"status": "success", "message": "App permission granted"}
            
            return {"status": "error", "message": "Permission dialog not found"}
        except Exception as e:
            self.logger.error(f"Failed to handle permission request: {str(e)}")
            return {"status": "error", "message": str(e)}

    def run_as_administrator(self, meta_information: Dict[str, Any]) -> Dict[str, str]:
        """Run an application as administrator"""
        try:
            app_path = meta_information["url_path_context"]["file_path"]
            
            # Verify file exists
            if not os.path.exists(app_path):
                return {"status": "error", "message": f"Application not found: {app_path}"}
            
            # Run as administrator
            try:
                win32api.ShellExecute(
                    0,
                    "runas",  # This triggers the UAC prompt
                    app_path,
                    meta_information.get("arguments", None),
                    os.path.dirname(app_path),
                    1  # SW_SHOWNORMAL
                )
            except win32api.error as e:
                if e.winerror == 1223:  # User canceled UAC prompt
                    return {"status": "error", "message": "User canceled elevation request"}
                raise
            
            # Handle UAC dialog if needed
            if meta_information.get("handle_uac", True):
                uac_result = self._handle_uac_dialog(meta_information)
                if uac_result["status"] == "error":
                    return uac_result
            
            return {
                "status": "success",
                "message": f"Application launched as administrator: {app_path}"
            }
        except Exception as e:
            self.logger.error(f"Failed to run as administrator: {str(e)}")
            return {"status": "error", "message": str(e)}

    def handle_dialog(self, meta_information):
        """Handle various Windows dialogs"""
        try:
            dialog_type = meta_information.get('dialog_type')
            response = meta_information.get('response', '')
            timeout = meta_information.get('timeout', 10)  # Default 10 second timeout
            
            if not dialog_type:
                return {"status": "error", "message": "No dialog type specified"}
                
            start_time = time.time()
            dialog_found = False
            
            while time.time() - start_time < timeout:
                # Try to find the dialog window
                if dialog_type == 'file_overwrite':
                    # Look for common save/overwrite dialog titles
                    dialog_titles = [
                        'Save As',
                        'Confirm Save As',
                        'Replace or Skip Files',
                        'Confirm File Replace',
                        'File Exists'
                    ]
                    
                    for title in dialog_titles:
                        dialog = win32gui.FindWindow(None, title)
                        if dialog:
                            dialog_found = True
                            # Find and click the appropriate button based on response
                            if response.lower() == 'yes':
                                # Try different button texts
                                button_texts = ['&Yes', 'Replace', 'OK']
                                for text in button_texts:
                                    try:
                                        button = win32gui.FindWindowEx(dialog, None, 'Button', text)
                                        if button:
                                            win32gui.SendMessage(dialog, win32con.WM_COMMAND, win32gui.GetDlgCtrlID(button), 0)
                                            return {"status": "success", "message": f"Handled {dialog_type} dialog"}
                                    except Exception:
                                        continue
                            elif response.lower() == 'no':
                                button = win32gui.FindWindowEx(dialog, None, 'Button', '&No')
                                if button:
                                    win32gui.SendMessage(dialog, win32con.WM_COMMAND, win32gui.GetDlgCtrlID(button), 0)
                                    return {"status": "success", "message": f"Handled {dialog_type} dialog"}
                            break
                            
                elif dialog_type == 'file_save':
                    dialog = win32gui.FindWindow('#32770', 'Save As')
                    if dialog:
                        dialog_found = True
                        button = win32gui.FindWindowEx(dialog, None, 'Button', '&Save')
                        if button:
                            win32gui.SendMessage(dialog, win32con.WM_COMMAND, win32gui.GetDlgCtrlID(button), 0)
                            return {"status": "success", "message": f"Handled {dialog_type} dialog"}
                            
                # Add more dialog types as needed
                
                if not dialog_found:
                    time.sleep(0.1)  # Short sleep to prevent CPU overuse
                    
            if not dialog_found:
                return {
                    "status": "error",
                    "message": f"Dialog '{dialog_type}' not found within timeout"
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Failed to handle dialog: {str(e)}"}
            
        return {"status": "success", "message": f"Handled {dialog_type} dialog"}