import logging
import json
import time
from datetime import datetime
import os
import threading
from pynput import keyboard, mouse
import win32gui
import win32process
import psutil
import pyautogui
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt
import sys
import getpass
import socket
import shutil
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import win32com.client
import win32con
import win32api
import win32gui
import win32process
import win32ui
from ctypes import windll
import re
from datetime import datetime
import pywinauto
from pywinauto import Application, Desktop
import pythoncom
import cv2
import numpy as np
from mss import mss as mss_lib
import random
from PIL import Image
import win32clipboard
from screeninfo import get_monitors

# Add after other global variables
SCREEN_RECORDINGS_DIR = 'screen_recordings'
RECORDING_LOGS_DIR = 'recording_logs'
SCREENSHOTS_DIR = 'screenshots'
RAW_RECORDINGS_DIR = 'raw_recordings'

# Get screen dimensions
try:
    monitors = get_monitors()
    primary_monitor = monitors[0]  # Get primary monitor
    screen_width = primary_monitor.width
    screen_height = primary_monitor.height
except Exception as e:
    # Fallback to using win32api if screeninfo fails
    screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    logging.warning(f"Using fallback method for screen dimensions: {e}")

# Log screen dimensions
logging.info(f"Screen dimensions: {screen_width}x{screen_height}")

def get_disk_usage():
    """
    Get disk usage percentage (used space) for all drives.
    Returns the highest usage percentage among all drives.
    """
    try:
        max_usage = 0
        # Get all physical disk partitions (exclude network drives and CD-ROMs)
        partitions = [p for p in psutil.disk_partitions() 
                     if p.fstype != '' and 'cdrom' not in p.opts.lower()]
        
        for partition in partitions:
            try:
                # Get disk I/O counters for this partition
                disk_io = psutil.disk_io_counters(perdisk=True)
                disk_name = partition.device.strip(':\\')  # Get disk name without colon
                if disk_name in disk_io:
                    disk_stats = disk_io[disk_name]
                    
                    # Calculate disk activity percentage
                    read_bytes = disk_stats.read_bytes
                    write_bytes = disk_stats.write_bytes
                    total_bytes = read_bytes + write_bytes
                    
                    # Get current disk activity percentage
                    disk_busy = (disk_stats.read_time + disk_stats.write_time) / 10  # Convert to percentage
                    
                    if disk_busy > max_usage:
                        max_usage = disk_busy
                    
                    logging.debug(f"Disk {partition.mountpoint}: {disk_busy:.1f}% busy "
                                f"(Read: {read_bytes//(1024*1024)}MB, "
                                f"Write: {write_bytes//(1024*1024)}MB)")
                
            except PermissionError:
                continue
            except Exception as e:
                logging.error(f"Error checking partition {partition.mountpoint}: {e}")
                continue
                
        return max_usage
        
    except Exception as e:
        logging.error(f"Error getting disk usage: {e}")
        return 0

class ConsentDialog(QDialog):
    """Dialog to get user consent for system recording."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Recording Consent")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Add warning icon or header
        header = QLabel("⚠️ System Recording Consent Required")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF6B6B;")
        layout.addWidget(header)

        # Add keyboard shortcut information
        shortcut_info = QLabel("Keyboard Shortcuts:\nF9 - Start/Pause/Resume Recording\nF10 - Stop Recording")
        shortcut_info.setStyleSheet("font-size: 12px; color: #4A90E2;")
        layout.addWidget(shortcut_info)

        # Add detailed information
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
            <p>By clicking 'Start Recording', you agree to allow this application to record:</p>
            <ul>
                <li><b>Mouse Actions:</b> Clicks, movements, scrolling</li>
                <li><b>Keyboard Actions:</b> Key presses, combinations</li>
                <li><b>Window Information:</b> Active windows, focus changes</li>
                <li><b>System Events:</b> Application starts/stops</li>
                <li><b>Screenshots:</b> For context of actions</li>
                <li><b>File Operations:</b> File system changes</li>
            </ul>
            <p>This data will be used to:</p>
            <ul>
                <li>Create automated workflows</li>
                <li>Analyze user interactions</li>
                <li>Improve system automation</li>
            </ul>
            <p style="color: #FF6B6B;"><b>Note:</b> Do not record actions involving sensitive information.</p>
        """)
        layout.addWidget(info_text)

        # Add buttons
        button_layout = QVBoxLayout()
        self.accept_button = QPushButton("Start Recording")
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

def setup_detailed_logging():
    """Set up detailed error logging configuration."""
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Configure the root logger with both file and console handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture all levels
        
        # File handler for detailed logging
        detailed_handler = logging.FileHandler("logs/detailed_system_recording.log")
        detailed_handler.setLevel(logging.DEBUG)
        detailed_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        )
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        
        root_logger.addHandler(detailed_handler)
        root_logger.addHandler(console_handler)
        
        logging.info("Detailed logging system initialized")
    except Exception as e:
        print(f"Failed to set up detailed logging: {e}")

# Call setup_detailed_logging at module level
setup_detailed_logging()

class SystemRecorder:
    """Records system actions according to actions_schema.JSON5."""
    
    def __init__(self):
        self.recording = False
        self.paused = False
        self.sequence_counter = 0
        self.recording_data = []
        self.start_time = None
        self.recording_id = None
        self.screen_recorder = None
        self.screen_recording_thread = None
        self.screen_recording = False
        
        # Create all necessary directories
        self.setup_directories()
        
        # Initialize listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Threading lock for data access
        self.data_lock = threading.Lock()
        
        # Add to existing initialization
        self.resource_manager = ResourceManager()
        #self.gpu_recorder = GPUScreenRecorder()
        
    def setup_directories(self):
        """Create all necessary directories with proper structure."""
        directories = [
            SCREEN_RECORDINGS_DIR,
            RECORDING_LOGS_DIR,
            SCREENSHOTS_DIR,
            RAW_RECORDINGS_DIR
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Created directory: {directory}")

    def generate_recording_id(self):
        """Generate a unique recording ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = ''.join(random.choices('0123456789ABCDEF', k=6))
        return f"REC_{timestamp}_{random_suffix}"

    def start_screen_recording(self):
        """Initialize and start screen recording."""
        try:
            if not self.recording_id:
                self.recording_id = self.generate_recording_id()

            output_path = os.path.join(
                SCREEN_RECORDINGS_DIR,
                f"{self.recording_id}_screen_recording.avi"
            )

            # Initialize screen capture
            sct = mss_lib()
            monitor = sct.monitors[0]  # Capture primary monitor

            # Get screen dimensions
            width = monitor["width"]
            height = monitor["height"]

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.screen_recorder = cv2.VideoWriter(
                output_path,
                fourcc,
                30.0,  # FPS
                (width, height)
            )

            # Start recording thread
            self.screen_recording = True
            self.screen_recording_thread = threading.Thread(
                target=self._record_screen,
                args=(sct, monitor),
                daemon=True
            )
            self.screen_recording_thread.start()
            
            logging.info(f"Started screen recording: {output_path}")
            
        except Exception as e:
            logging.error(f"Failed to start screen recording: {e}")
            self.screen_recording = False
            if self.screen_recorder:
                self.screen_recorder.release()

    def _record_screen(self, sct, monitor):
        """Screen recording thread function."""
        try:
            while self.screen_recording and not self.paused:
                # Capture screen
                screenshot = sct.grab(monitor)
                
                # Convert to numpy array
                frame = np.array(screenshot)
                
                # Convert from BGRA to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Write frame
                self.screen_recorder.write(frame)
                
                # Control frame rate
                time.sleep(1/30)  # Approximately 30 FPS
                
        except Exception as e:
            logging.error(f"Error in screen recording: {e}")
        finally:
            if self.screen_recorder:
                self.screen_recorder.release()

    def stop_screen_recording(self):
        """Stop screen recording."""
        self.screen_recording = False
        if self.screen_recording_thread:
            self.screen_recording_thread.join()
        if self.screen_recorder:
            self.screen_recorder.release()
        logging.info("Screen recording stopped")

    def capture_screenshot(self, action_type, timestamp):
        """
        Capture a screenshot using mss and PIL.
        """
        try:
            if not self.recording_id:
                self.recording_id = self.generate_recording_id()

            # Create mss instance
            with mss_lib() as sct:  # Create new mss instance
                # Capture primary monitor
                monitor = sct.monitors[0]
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                
                # Resize to target resolution while maintaining aspect ratio
                target_resolution = (800, 600)
                img = img.resize(target_resolution, Image.LANCZOS)
                
                # Create filename with recording ID
                filename = os.path.join(
                    SCREENSHOTS_DIR,
                    f"{self.recording_id}_{action_type}_{int(timestamp)}.png"
                )
                
                # Save the image
                img.save(filename)
                logging.info(f"Screenshot saved: {filename}")
                return filename
                
        except Exception as e:
            logging.error(f"Failed to capture screenshot: {e}")
            return None

    def capture_window_screenshot(self, hwnd):
        """
        Capture a screenshot of a specific window.
        
        Args:
            hwnd: Window handle
        """
        try:
            # Get window dimensions
            window_rect = win32gui.GetWindowRect(hwnd)
            width = window_rect[2] - window_rect[0]
            height = window_rect[3] - window_rect[1]
            
            if width <= 0 or height <= 0:
                return None

            # Create device contexts and bitmap
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # Handle window styles (transparency, layered windows, etc.)
            win_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if win_style & win32con.WS_EX_LAYERED:
                # For layered windows (transparent/glass effects)
                saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY | win32con.CAPTUREBLT)
            else:
                # For standard windows
                saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

            # Convert to PIL Image
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)

            # Clean up
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            return img

        except Exception as e:
            logging.error(f"Error capturing window screenshot: {e}")
            return None

    def capture_monitor_screenshot(self, monitor_info):
        """
        Capture a screenshot of a specific monitor.
        
        Args:
            monitor_info: Monitor information dictionary
        """
        try:
            with mss_lib() as sct:
                monitor = {
                    "left": monitor_info["left"],
                    "top": monitor_info["top"],
                    "width": monitor_info["width"],
                    "height": monitor_info["height"]
                }
                screenshot = sct.grab(monitor)
                return Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        except Exception as e:
            logging.error(f"Error capturing monitor screenshot: {e}")
            return None

    def get_window_monitor(self, window_rect):
        """
        Get the monitor that contains most of the window.
        
        Args:
            window_rect: Tuple of (left, top, right, bottom)
        """
        try:
            monitors = get_monitors()
            window_center_x = (window_rect[0] + window_rect[2]) // 2
            window_center_y = (window_rect[1] + window_rect[3]) // 2
            
            for monitor in monitors:
                if (monitor.x <= window_center_x <= monitor.x + monitor.width and
                    monitor.y <= window_center_y <= monitor.y + monitor.height):
                    return {
                        "left": monitor.x,
                        "top": monitor.y,
                        "width": monitor.width,
                        "height": monitor.height
                    }
            
            # Fallback to primary monitor
            return {
                "left": 0,
                "top": 0,
                "width": win32api.GetSystemMetrics(win32con.SM_CXSCREEN),
                "height": win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            }
        except Exception as e:
            logging.error(f"Error getting window monitor: {e}")
            return None

    def get_cursor_monitor(self, x, y):
        """
        Get the monitor that contains the cursor.
        
        Args:
            x: Cursor X position
            y: Cursor Y position
        """
        try:
            monitors = get_monitors()
            for monitor in monitors:
                if (monitor.x <= x <= monitor.x + monitor.width and
                    monitor.y <= y <= monitor.y + monitor.height):
                    return {
                        "left": monitor.x,
                        "top": monitor.y,
                        "width": monitor.width,
                        "height": monitor.height
                    }
            
            # Fallback to primary monitor
            return {
                "left": 0,
                "top": 0,
                "width": win32api.GetSystemMetrics(win32con.SM_CXSCREEN),
                "height": win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            }
        except Exception as e:
            logging.error(f"Error getting cursor monitor: {e}")
            return None

    def start(self):
        """Start recording with proper initialization."""
        try:
            # Initialize recording state
            self.recording = True
            self.paused = False
            self.start_time = time.time()
            self.sequence_counter = 0
            self.recording_data = []

            # Generate new recording ID
            self.recording_id = self.generate_recording_id()
            logging.info(f"Generated recording ID: {self.recording_id}")

            # Initialize keyboard and mouse listeners
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.mouse_listener = mouse.Listener(
                on_click=self.on_click,
                on_scroll=self.on_scroll,
                on_move=self.on_move
            )

            # Start the listeners
            self.keyboard_listener.start()
            self.mouse_listener.start()
            logging.info("Input listeners started")

            # Initialize resource manager (simplified)
            self.resource_manager = ResourceManager()
            self.resource_manager.start_monitoring()
            logging.info("Resource manager started")

            # No need for enhanced monitoring setup anymore
            logging.info("Recording started successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self.cleanup_on_error()
            return False

    def cleanup_on_error(self):
        """Clean up resources if initialization fails."""
        try:
            # Stop all monitoring
            self._stop_monitoring_threads()
            
            # Stop resource monitoring
            if hasattr(self, 'resource_manager'):
                self.resource_manager.stop_monitoring()
            
            # Reset state
            self.recording = False
            self.paused = False
            
            # Close any open files or resources
            if hasattr(self, 'screen_recorder') and self.screen_recorder:
                self.screen_recorder.release()
            
            logging.info("Cleanup completed after error")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def stop(self):
        """Stop recording and cleanup resources."""
        try:
            logging.info("Stopping recording...")
            self.recording = False
            
            # Stop resource monitoring
            if hasattr(self, 'resource_manager'):
                self.resource_manager.stop_monitoring()
                logging.debug("Resource monitoring stopped")
            
            # Stop other monitoring
            self._stop_monitoring_threads()
            logging.debug("Monitoring threads stopped")
            
            # Save recording data
            recording_dir = self.save_recording_data()
            if recording_dir:
                logging.info(f"Recording saved to: {recording_dir}")
            
            return recording_dir
            
        except Exception as e:
            logging.error(f"Failed to stop recording: {e}")
            return None

    def pause(self):
        """Pause recording."""
        self.paused = True
        logging.info("Recording paused")

    def resume(self):
        """Resume recording without logging."""
        self.paused = False

    def get_user_consent(self):
        """Show consent dialog and get user permission."""
        dialog = ConsentDialog()
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted

    def record_action(self, action_type, details):
        """Record an action with enhanced URL context."""
        if not self.recording or self.paused:
            return

        try:
            timestamp = time.time() - self.start_time
            window_info = self.get_active_window_info()
            
            # Get URL context
            url_context = {
                "url": None,
                "domain": None,
                "path": None,
                "query_params": None
            }
            
            if self.is_browser_window(window_info):
                url = self.get_current_url()
                if url:
                    from urllib.parse import urlparse, parse_qs
                    parsed_url = urlparse(url)
                    url_context = {
                        "url": url,
                        "domain": parsed_url.netloc,
                        "path": parsed_url.path,
                        "query_params": parse_qs(parsed_url.query)
                    }
            
            # Create action record with enhanced URL context
            action = {
                "type": action_type,
                "timestamp": timestamp,
                "details": details,
                "window_info": window_info,
                "url_context": url_context,
                "meta_information": self.create_meta_information(action_type, details)
            }

            # Take screenshot for significant actions
            if action_type in ['left_click', 'right_click', 'keystroke', 'special_key_press']:
                screenshot_path = self.capture_screenshot(action_type, timestamp)
                if screenshot_path:
                    action['screenshot'] = screenshot_path

            # Add to recording data in a thread-safe way
            with self.data_lock:
                self.recording_data.append(action)
                self.sequence_counter += 1
            
            # Only log significant actions
            if action_type in ['left_click', 'right_click', 'keystroke', 'special_key_press']:
                logging.info(f"Recorded action: {action_type} (Sequence: {self.sequence_counter})")
                
        except Exception as e:
            logging.error(f"Error recording action {action_type}: {e}")

    def on_key_press(self, key):
        """Handle key press events with simplified logging."""
        try:
            # Check for control keys first
            if key == keyboard.Key.f9:
                if not self.recording:
                    logging.info("Starting recording (F9)")
                    self.recording = True
                    self.paused = False
                    return
                elif self.paused:
                    logging.info("Resuming recording (F9)")
                    self.paused = False
                    return
                else:
                    logging.info("Pausing recording (F9)")
                    self.paused = True
                    return
            elif key == keyboard.Key.f10:
                if self.recording:
                    logging.info("Stopping recording (F10)")
                    self.stop()
                    return
                return

            # Only record keypresses if recording and not paused
            if not self.recording or self.paused:
                return

            # Record the actual keypress with minimal context
            try:
                key_char = key.char  # For regular characters
                details = {
                    'key': key_char,
                    'key_type': 'character'
                }
                self.record_action('keystroke', details)
            except AttributeError:
                # Special keys
                details = {
                    'key': str(key),
                    'key_type': 'special'
                }
                self.record_action('special_key_press', details)

        except Exception as e:
            logging.error(f"Error handling key press: {e}")

    def on_key_release(self, key):
        """Handle key release events - now only used for control purposes."""
        pass  # We no longer track key releases

    def on_click(self, x, y, button, pressed):
        """Handle mouse click events with simplified logging."""
        if not self.recording or self.paused:
            return

        try:
            # Only process press events (ignore releases)
            if not pressed:
                return
            
            action_type = 'left_click'
            if button == mouse.Button.right:
                action_type = 'right_click'
            elif button == mouse.Button.middle:
                action_type = 'middle_click'
            
            details = {
                'position': {'x': x, 'y': y},
                'button': str(button)
            }
            
            # Always take screenshot for mouse clicks
            timestamp = time.time() - self.start_time
            screenshot_path = self.capture_screenshot(action_type, timestamp)
            if screenshot_path:
                details['screenshot'] = screenshot_path
            
            self.record_action(action_type, details)
            
        except Exception as e:
            logging.error(f"Error handling mouse click: {e}")

    def on_scroll(self, x, y, dx, dy):
        """Handle mouse scrolling."""
        details = {
            "x": x,
            "y": y,
            "delta_x": dx,
            "delta_y": dy
        }
        self.record_action('mouse_scroll', details)

    def on_move(self, x, y):
        """Handle mouse movement."""
        # Only record movements periodically to avoid excessive data
        pass

    def get_active_window_info(self):
        """Get information about the currently active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            
            return {
                "title": win32gui.GetWindowText(hwnd),
                "process_name": process.name(),
                "pid": pid
            }
        except Exception:
            return None

    def get_active_modifiers(self):
        """Get currently pressed modifier keys."""
        modifiers = []
        if pyautogui.keyDown('shift'):
            modifiers.append('shift')
        if pyautogui.keyDown('ctrl'):
            modifiers.append('ctrl')
        if pyautogui.keyDown('alt'):
            modifiers.append('alt')
        return modifiers

    def create_meta_information(self, action_type, details, window_info=None):
        """Create comprehensive metadata following actions_schema.JSON5."""
        timestamp = datetime.now().isoformat()
        
        # Get window info if not provided
        if window_info is None:
            window_info = self.get_active_window_info()
        
        meta_information = {
            "timestamp": timestamp,
            "sequence_order": self.sequence_counter,
            "screen_context": {
                "visible_ui_elements": self.get_visible_elements(),
                "active_window": window_info.get("title") if window_info else None,
                "screen_resolution": pyautogui.size(),
                "cursor_position": pyautogui.position()
            },
            "url_path_context": {
                "url": self.get_current_url() if self.is_browser_window(window_info) else None,
                "file_path": details.get('file_path'),
                "domain": self.extract_domain() if self.is_browser_window(window_info) else None
            },
            "element_context": {
                "element_type": details.get('element_type'),
                "element_name": details.get('element_name'),
                "element_id": details.get('element_id'),
                "element_class": details.get('element_class'),
                "element_attributes": details.get('element_attributes', {}),
                "element_state": {
                    "is_visible": details.get('is_visible', True),
                    "is_enabled": details.get('is_enabled', True),
                    "is_selected": details.get('is_selected', False)
                }
            },
            "application_context": {
                "application_name": window_info.get("process_name") if window_info else None,
                "application_version": self.get_app_version(window_info.get("process_name")) if window_info else None,
                "window_title": window_info.get("title") if window_info else None,
                "process_id": window_info.get("pid") if window_info else None
            }
        }
        return meta_information

    def get_time_since_previous_action(self):
        """Calculate time since previous action."""
        if len(self.recording_data) > 0:
            last_action = self.recording_data[-1]
            return time.time() - last_action.get('timestamp', time.time())
        return 0.0

    def get_previous_action(self):
        """Get the previous action's details."""
        if len(self.recording_data) > 0:
            last_action = self.recording_data[-1]
            return {
                "type": last_action.get('type'),
                "timestamp": last_action.get('timestamp'),
                "sequence_order": last_action.get('meta_information', {}).get('sequence_order')
            }
        return None

    def predict_next_action(self, current_action_type, details):
        """Predict the next likely action based on current context."""
        # This could be enhanced with ML-based prediction
        common_sequences = {
            'left_click': ['keystroke', 'typing_sequence'],
            'keystroke': ['keystroke', 'typing_sequence'],
            'typing_sequence': ['left_click', 'key_combination'],
            'file_operation': ['window_focus', 'left_click']
        }
        return common_sequences.get(current_action_type, ['unknown'])[0]

    def get_app_version(self, process_name):
        """Get application version information."""
        try:
            if process_name:
                process = psutil.Process(self.get_pid_by_name(process_name))
                return process.exe()  # Could be enhanced to extract version info
        except:
            pass
        return "Unknown"

    def get_pid_by_name(self, process_name):
        """Get process ID by name."""
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                return proc.info['pid']
        return None

    def extract_domain(self):
        """Extract domain from current URL."""
        try:
            if hasattr(self, 'driver'):
                url = self.driver.current_url
                from urllib.parse import urlparse
                return urlparse(url).netloc
        except:
            pass
        return None

    def get_visible_elements(self):
        """Get visible UI elements in the current window."""
        # Implement based on your needs
        return []

    def save_recording_data(self):
        """Save recorded data with enhanced organization."""
        if not self.recording_data:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        recording_dir = f'recordings/REC_{timestamp}'
        os.makedirs(recording_dir, exist_ok=True)

        try:
            # Save main recording data
            data_file = os.path.join(recording_dir, 'recording_data.json')
            with open(data_file, 'w') as f:
                json.dump({
                    "metadata": self.create_recording_metadata(),
                    "actions": self.recording_data,
                    "statistics": {
                        "total_actions": len(self.recording_data),
                        "duration": time.time() - self.start_time,
                        "action_types": self.get_action_statistics()
                    }
                }, f, indent=2)

            # Save log file
            log_file = os.path.join(recording_dir, 'recording.log')
            if hasattr(self, 'log_handler'):
                self.log_handler.flush()
                shutil.copy2(self.log_handler.baseFilename, log_file)

            logging.info(f"Recording saved to: {recording_dir}")
            return recording_dir
        except Exception as e:
            logging.error(f"Failed to save recording: {e}")
            return None

    def get_action_statistics(self):
        """Generate statistics about recorded actions."""
        stats = {}
        for action in self.recording_data:
            action_type = action.get('type')
            if action_type:
                stats[action_type] = stats.get(action_type, 0) + 1
        return stats

    def is_browser_window(self, window_info):
        """Check if the current window is a web browser."""
        if not window_info:
            return False
        
        browsers = {
            'chrome.exe': 'Chrome',
            'firefox.exe': 'Firefox',
            'msedge.exe': 'Edge',
            'iexplore.exe': 'Internet Explorer'
        }
        
        return window_info.get('process_name', '').lower() in browsers

    def get_current_url(self):
        """Get current URL if in a browser window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            
            # Expanded browser list
            browsers = {
                'chrome.exe': 'Chrome',
                'firefox.exe': 'Firefox',
                'msedge.exe': 'Edge',
                'iexplore.exe': 'Internet Explorer',
                'brave.exe': 'Brave',
                'opera.exe': 'Opera',
                'vivaldi.exe': 'Vivaldi'
            }
            
            if process.name().lower() in browsers:
                # Get window title
                title = win32gui.GetWindowText(hwnd)
                
                # Common URL patterns
                url_patterns = [
                    r'https?://[^\s<>"]+|www\.[^\s<>"]+',
                    r'(?:https?://)?(?:[\w-]+\.)+[\w-]+(?:/[\w-./?%&=]*)?'
                ]
                
                # Try to extract URL from title
                for pattern in url_patterns:
                    matches = re.findall(pattern, title)
                    if matches:
                        return matches[0]
                    
                # Try to get URL from clipboard if it's a URL
                try:
                    win32clipboard.OpenClipboard()
                    clipboard_data = win32clipboard.GetClipboardData()
                    win32clipboard.CloseClipboard()
                    
                    for pattern in url_patterns:
                        matches = re.findall(pattern, clipboard_data)
                        if matches:
                            return matches[0]
                except:
                    pass
                    
            return None
            
        except Exception as e:
            logging.debug(f"Error getting current URL: {e}")
            return None

    def get_active_file_path(self, window_info):
        """Get path of currently active file from window title."""
        try:
            if window_info and window_info.get('window_title'):
                title = window_info['window_title']
                
                # Common patterns for file paths
                if ' - ' in title:
                    potential_path = title.split(' - ')[0]
                    if os.path.exists(potential_path):
                        return os.path.abspath(potential_path)
                    
                # Look for file extensions
                words = title.split()
                for word in words:
                    if '.' in word and os.path.exists(word):
                        return os.path.abspath(word)
                    
        except Exception as e:
            logging.debug(f"Error getting active file path: {e}")
        return None

    def infer_user_intent(self, action_type, details):
        """Infer user intent based on action type and context."""
        intents = {
            'left_click': 'Select or activate element',
            'right_click': 'Open context menu',
            'double_left_click': 'Open or edit item',
            'mouse_drag': 'Move or reorder element',
            'keystroke': 'Input text or command',
            'key_combination': 'Execute shortcut command',
            'typing_sequence': 'Enter text content',
            'window_focus': 'Switch active window',
            'file_operation': 'Manage file system',
            'clipboard_operation': 'Transfer content'
        }
        return intents.get(action_type, 'Perform system action')

    def calculate_drag_distance(self, details):
        """Calculate the distance of a drag operation."""
        try:
            start_x = details.get('start_x', 0)
            start_y = details.get('start_y', 0)
            end_x = details.get('end_x', 0)
            end_y = details.get('end_y', 0)
            return ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
        except:
            return 0

    def create_recording_metadata(self):
        """Create metadata for the entire recording session."""
        return {
            "recording_id": f"REC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "system_info": {
                "platform": sys.platform,
                "screen_resolution": pyautogui.size(),
                "user": getpass.getuser(),
                "hostname": socket.gethostname()
            },
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "recording_settings": {
                "include_screenshots": True,
                "monitor_clipboard": True,
                "monitor_files": True,
                "monitor_processes": True
            }
        }

    def is_window_maximized(self, window_title):
        """Check if window is maximized."""
        try:
            if window_title:
                hwnd = win32gui.FindWindow(None, window_title)
                placement = win32gui.GetWindowPlacement(hwnd)
                return placement[1] == win32con.SW_SHOWMAXIMIZED
        except:
            pass
        return False

    def is_window_minimized(self, window_title):
        """Check if window is minimized."""
        try:
            if window_title:
                hwnd = win32gui.FindWindow(None, window_title)
                placement = win32gui.GetWindowPlacement(hwnd)
                return placement[1] == win32con.SW_SHOWMINIMIZED
        except:
            pass
        return False

    def _stop_monitoring_threads(self):
        """Stop all monitoring threads safely."""
        try:
            # Stop file system observers
            if hasattr(self, 'downloads_observer'):
                self.downloads_observer.stop()
                self.downloads_observer.join()
            if hasattr(self, 'documents_observer'):
                self.documents_observer.stop()
                self.documents_observer.join()
            
            # Stop input listeners
            if hasattr(self, 'mouse_listener'):
                self.mouse_listener.stop()
            if hasattr(self, 'keyboard_listener'):
                self.keyboard_listener.stop()
            
            # Stop screen recording
            if hasattr(self, 'screen_recording') and self.screen_recording:
                self.screen_recording = False
                if hasattr(self, 'screen_recording_thread'):
                    self.screen_recording_thread.join()
                
            logging.info("All monitoring threads stopped successfully")
            
        except Exception as e:
            logging.error(f"Error stopping monitoring threads: {e}")

    def get_monitor_info(self, x, y):
        """Get monitor information based on cursor position."""
        try:
            monitors = get_monitors()
            for monitor in monitors:
                if (monitor.x <= x <= monitor.x + monitor.width and
                    monitor.y <= y <= monitor.y + monitor.height):
                    return {
                        'monitor_left': monitor.x,
                        'monitor_top': monitor.y,
                        'monitor_width': monitor.width,
                        'monitor_height': monitor.height
                    }
            # Fallback to primary monitor
            return {
                'monitor_left': 0,
                'monitor_top': 0,
                'monitor_width': screen_width,
                'monitor_height': screen_height
            }
        except Exception as e:
            logging.debug(f"Error getting monitor info: {e}")
            return None

class ResourceManager:
    """Placeholder for resource management (throttling disabled)."""
    
    def __init__(self, max_cpu_percent=70, max_memory_percent=75):
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        self.throttle_level = 0
        self.is_monitoring = False

    def start_monitoring(self):
        """Start resource monitoring (currently disabled)."""
        self.is_monitoring = True
        logging.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop resource monitoring (currently disabled)."""
        self.is_monitoring = False
        logging.info("Resource monitoring stopped")

    def should_capture(self, data_type, last_capture_time):
        """Always return True since throttling is disabled."""
        return True

    def get_resource_stats(self):
        """Get basic resource statistics."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'throttle_level': 0
            }
        except Exception as e:
            logging.error(f"Error getting resource stats: {e}")
            return None

class EnhancedSystemRecorder(SystemRecorder):
    """Enhanced version of SystemRecorder with more comprehensive tracking."""
    
    def __init__(self):
        try:
            logging.debug("Initializing EnhancedSystemRecorder")
            super().__init__()
            
            if not logging.getLogger().handlers:
                setup_detailed_logging()
            
            # Create necessary directories with absolute paths
            self.base_dir = os.path.abspath(os.path.dirname(__file__))
            self.screenshots_dir = os.path.join(self.base_dir, 'screenshots')
            self.recordings_dir = os.path.join(self.base_dir, 'screen_recordings')
            self.logs_dir = os.path.join(self.base_dir, 'logs')
            
            # Create directories
            os.makedirs(self.screenshots_dir, exist_ok=True)
            os.makedirs(self.recordings_dir, exist_ok=True)
            os.makedirs(self.logs_dir, exist_ok=True)
            
            # Initialize data structures with appropriate sizes
            self.active_applications = {}
            self.document_states = {}
            self.input_history = []
            self.file_operations = []
            self.keystroke_buffer = []
            self.last_active_window = None
            self.last_resume_log = 0
            
            # Performance optimizations
            self.action_buffer_size = 1000  # Limit buffer size
            self.screenshot_interval = 0.5   # Minimum time between screenshots
            self.last_screenshot_time = 0
            self.last_action_time = 0
            self.action_throttle = 0.01      # Minimum time between actions
            
            # Thread-local storage for MSS
            self.mss_instances = threading.local()
            
            # Cache frequently accessed data
            self.cached_window_info = None
            self.window_info_cache_time = 0
            self.window_cache_ttl = 0.1  # Cache window info for 100ms
            
            logging.debug("EnhancedSystemRecorder initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize EnhancedSystemRecorder: {e}", exc_info=True)
            raise

    def should_capture_screenshot(self, action_type):
        """Determine if screenshot should be captured based on timing and action type."""
        current_time = time.time()
        if current_time - self.last_screenshot_time < self.screenshot_interval:
            return False
            
        # Only capture screenshots for significant actions
        significant_actions = {
            'left_click', 'right_click', 'keystroke', 
            'special_key_press', 'window_focus'
        }
        
        if action_type not in significant_actions:
            return False
            
        self.last_screenshot_time = current_time
        return True

    def get_active_window_info(self):
        """Get cached window info or update if expired."""
        current_time = time.time()
        if (self.cached_window_info and 
            current_time - self.window_info_cache_time < self.window_cache_ttl):
            return self.cached_window_info
            
        self.cached_window_info = super().get_active_window_info()
        self.window_info_cache_time = current_time
        return self.cached_window_info

    def record_action(self, action_type, details):
        """Record an action with throttling and buffer management."""
        if not self.recording or self.paused:
            return

        current_time = time.time()
        if current_time - self.last_action_time < self.action_throttle:
            return

        try:
            self.last_action_time = current_time
            timestamp = current_time - self.start_time
            
            # Get window info (cached)
            window_info = self.get_active_window_info()
            
            # Create action record
            action = {
                "type": action_type,
                "timestamp": timestamp,
                "details": details,
                "window_info": window_info,
                "meta_information": self.create_meta_information(action_type, details)
            }

            # Capture screenshot if needed
            if self.should_capture_screenshot(action_type):
                screenshot_path = self.capture_screenshot(action_type, timestamp)
                if screenshot_path:
                    action['screenshot'] = screenshot_path

            # Manage buffer size
            with self.data_lock:
                self.recording_data.append(action)
                if len(self.recording_data) > self.action_buffer_size:
                    self.recording_data = self.recording_data[-self.action_buffer_size:]
                self.sequence_counter += 1
            
            # Only log significant actions
            if action_type in ['left_click', 'right_click', 'keystroke', 'special_key_press']:
                logging.info(f"Recorded action: {action_type} (Sequence: {self.sequence_counter})")
                
        except Exception as e:
            logging.error(f"Error recording action {action_type}: {e}")

    def cleanup_old_data(self):
        """Periodically cleanup old data to manage memory."""
        try:
            with self.data_lock:
                if len(self.input_history) > 1000:
                    self.input_history = self.input_history[-1000:]
                if len(self.file_operations) > 1000:
                    self.file_operations = self.file_operations[-1000:]
                if len(self.keystroke_buffer) > 100:
                    self.keystroke_buffer = self.keystroke_buffer[-100:]
        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")

class EnhancedFileHandler(FileSystemEventHandler):
    """Enhanced file system event handler."""
    
    def __init__(self, recorder):
        self.recorder = recorder

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_info = {
            'path': event.src_path,
            'timestamp': datetime.now().isoformat(),
            'size': os.path.getsize(event.src_path) if os.path.exists(event.src_path) else None,
            'extension': os.path.splitext(event.src_path)[1],
            'in_downloads': self.recorder.downloads_path in event.src_path
        }
        
        self.recorder.record_action('file_created', file_info)

    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_info = {
            'path': event.src_path,
            'timestamp': datetime.now().isoformat(),
            'size': os.path.getsize(event.src_path) if os.path.exists(event.src_path) else None,
            'modification_type': 'modified'
        }
        
        self.recorder.record_action('file_modified', file_info)

    def on_deleted(self, event):
        file_info = {
            'path': event.src_path,
            'timestamp': datetime.now().isoformat(),
            'is_directory': event.is_directory
        }
        
        self.recorder.record_action('file_deleted', file_info)

class ErrorHandler:
    """Handles errors and recovery during recording."""
    
    def __init__(self, recorder):
        self.recorder = recorder
        self.error_log = []
        self.recovery_attempts = {}
        self.max_retries = 3
        
    def handle_error(self, error_type, error, context=None):
        """Handle errors with recovery attempts."""
        error_info = {
            'type': error_type,
            'message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'recording_id': self.recorder.recording_id
        }
        
        self.error_log.append(error_info)
        
        # Attempt recovery based on error type
        if error_type not in self.recovery_attempts:
            self.recovery_attempts[error_type] = 0
            
        if self.recovery_attempts[error_type] < self.max_retries:
            self.recovery_attempts[error_type] += 1
            return self.attempt_recovery(error_type, error_info)
        
        return False
    
    def attempt_recovery(self, error_type, error_info):
        """Attempt to recover from different types of errors."""
        try:
            if error_type == 'web_element_not_found':
                return self.recover_web_element()
            elif error_type == 'screenshot_failed':
                return self.recover_screenshot()
            elif error_type == 'recording_stalled':
                return self.recover_recording()
            elif error_type == 'memory_error':
                return self.recover_memory()
            
            return False
        except Exception as e:
            logging.error(f"Recovery attempt failed: {e}")
            return False
    
    def recover_web_element(self):
        """Attempt to recover lost web element."""
        try:
            # Try alternative element location strategies
            # Refresh page if needed
            # Wait and retry
            return True
        except:
            return False
            
    def recover_screenshot(self):
        """Attempt to recover screenshot functionality."""
        try:
            # Reinitialize screenshot capture
            # Try alternative screenshot method
            return True
        except:
            return False
            
    def recover_recording(self):
        """Attempt to recover stalled recording."""
        try:
            # Stop current recording threads
            # Reinitialize recording components
            # Restart recording
            return True
        except:
            return False
            
    def recover_memory(self):
        """Attempt to recover from memory issues."""
        try:
            # Clear unnecessary data
            # Force garbage collection
            import gc
            gc.collect()
            return True
        except:
            return False

class WebElementDetector:
    """Enhanced web element detection and tracking."""
    
    def __init__(self, recorder):
        self.recorder = recorder
        self.last_elements = {}
        self.element_history = []
        
    def detect_element(self, x, y, window_info):
        """Detect web element at coordinates with multiple strategies."""
        if not self.is_browser_window(window_info):
            return None
            
        element_info = {
            'coordinates': {'x': x, 'y': y},
            'timestamp': datetime.now().isoformat(),
            'window_info': window_info
        }
        
        try:
            # Try multiple detection strategies
            element = self.try_selenium_detection(x, y)
            if not element:
                element = self.try_accessibility_detection(x, y)
            if not element:
                element = self.try_image_recognition(x, y)
                
            if element:
                element_info.update(self.get_element_details(element))
                self.update_element_history(element_info)
                
            return element_info
        except Exception as e:
            self.recorder.error_handler.handle_error('web_element_detection', e, {
                'coordinates': {'x': x, 'y': y},
                'window_info': window_info
            })
            return None
    
    def get_element_details(self, element):
        """Get comprehensive element details."""
        return {
            'tag_name': element.tag_name,
            'attributes': self.get_all_attributes(element),
            'location': element.location,
            'size': element.size,
            'css_selector': self.generate_css_selector(element),
            'xpath': self.generate_xpath(element),
            'accessibility_id': self.get_accessibility_id(element),
            'parent_chain': self.get_parent_chain(element),
            'siblings': self.get_sibling_info(element),
            'state': {
                'is_displayed': element.is_displayed(),
                'is_enabled': element.is_enabled(),
                'is_selected': element.is_selected() if hasattr(element, 'is_selected') else None
            }
        }
    
    def get_all_attributes(self, element):
        """Get all element attributes."""
        try:
            return self.recorder.driver.execute_script(
                'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;',
                element
            )
        except:
            return {}
            
    def get_parent_chain(self, element, max_depth=3):
        """Get chain of parent elements."""
        chain = []
        current = element
        depth = 0
        
        while current and depth < max_depth:
            try:
                parent = current.find_element_by_xpath('..')
                chain.append({
                    'tag': parent.tag_name,
                    'id': parent.get_attribute('id'),
                    'class': parent.get_attribute('class')
                })
                current = parent
                depth += 1
            except:
                break
                
        return chain

class WorkflowDataCollector:
    """Collects and organizes data for workflow creation."""
    
    def __init__(self, recorder):
        self.recorder = recorder
        self.action_patterns = []
        self.context_data = {}
        self.workflow_metadata = {}
        
    def collect_action_data(self, action_type, details):
        """Collect comprehensive data for workflow creation."""
        action_data = {
            'basic_info': {
                'type': action_type,
                'timestamp': datetime.now().isoformat(),
                'sequence': self.recorder.sequence_counter
            },
            'context': self.get_action_context(),
            'patterns': self.detect_patterns(action_type, details),
            'relationships': self.get_action_relationships(action_type),
            'automation_hints': self.generate_automation_hints(action_type, details)
        }
        
        self.action_patterns.append(action_data)
        return action_data
    
    def get_action_context(self):
        """Get comprehensive context for the action."""
        return {
            'window_context': self.get_window_context(),
            'application_context': self.get_application_context(),
            'system_context': self.get_system_context(),
            'user_context': self.get_user_context()
        }
    
    def detect_patterns(self, action_type, details):
        """Detect patterns in user actions."""
        patterns = {
            'repeated_actions': self.find_repeated_actions(),
            'action_sequences': self.find_action_sequences(),
            'conditional_actions': self.find_conditional_actions(),
            'data_patterns': self.find_data_patterns(details)
        }
        return patterns
    
    def generate_automation_hints(self, action_type, details):
        """Generate hints for workflow automation."""
        return {
            'suggested_waits': self.suggest_wait_conditions(action_type),
            'error_handling': self.suggest_error_handling(action_type),
            'optimization_hints': self.suggest_optimizations(action_type),
            'validation_rules': self.suggest_validation_rules(details)
        }
    
    def find_repeated_actions(self):
        """Find repeated patterns in user actions."""
        # Implement pattern detection logic
        pass
    
    def find_action_sequences(self):
        """Find common sequences of actions."""
        # Implement sequence detection logic
        pass
    
    def suggest_wait_conditions(self, action_type):
        """Suggest appropriate wait conditions."""
        # Implement wait condition suggestions
        pass

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create and start recorder
    recorder = EnhancedSystemRecorder()
    if recorder.start():
        try:
            # Keep main thread alive
            while recorder.recording:
                time.sleep(0.1)
        except KeyboardInterrupt:
            recorder.stop() 