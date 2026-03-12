import ctypes
import json
import threading
import time
from datetime import datetime
import win32gui
import win32process
import win32clipboard
import psutil
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import locale
import getpass
import win32api
import win32con
import win32ui  # Added missing import
from pywinauto import Desktop, Application
import cv2
import numpy as np
from PIL import Image
import mss
from PIL import ImageGrab
from pynput import keyboard, mouse
from watchdog.watchmedo import observe_with
import logging
import random

#from gui import start_recording

# Global variables for screen dimensions and control flags
screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
screen_recording = False  # Flag to control screen recording
recording = False         # Flag to control overall recording
pause_event = threading.Event()  # Event to manage pause/resume functionality

# Define maximum resolution for recordings to save resources
max_width = 1024
max_height = 768

# Global variables
recording_data = []  # Store recorded actions
start_time = None
recording = False
pause_event = threading.Event()

SCREEN_RECORDINGS_DIR = 'screen_recordings'
RECORDING_LOGS_DIR = 'recording_logs'
SCREENSHOTS_DIR = 'screenshots'

# Create necessary directories
os.makedirs(SCREEN_RECORDINGS_DIR, exist_ok=True)
os.makedirs(RECORDING_LOGS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Global sequence counter
sequence_counter = 0

def setup_recording_logging(timestamp):
    """
    Set up logging for the current recording session.
    """
    # Create log filename with timestamp
    log_filename = os.path.join(RECORDING_LOGS_DIR, f'recording_log_{timestamp}.txt')
    
    # Create a specific logger for this recording
    recording_logger = logging.getLogger(f'recording_{timestamp}')
    recording_logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    recording_logger.addHandler(file_handler)
    
    return recording_logger

def log_action(logger, action_data):
    """
    Log an action with all its details in a structured format.
    """
    try:
        # Log basic action information
        logger.info("=" * 80)
        logger.info(f"Action Recorded at {datetime.now().isoformat()}")
        logger.info("-" * 40)
        
        # Log sequence and type information
        sequence_order = action_data.get('meta_information', {}).get('sequence_order', 'Unknown')
        logger.info(f"Sequence Number: {sequence_order}")
        logger.info(f"Action Type: {action_data.get('type', 'Unknown')}")
        
        # Log window and application context
        if 'window' in action_data:
            window = action_data['window']
            logger.info("\nWindow Context:")
            logger.info(f"  - Title: {window.get('window_title', 'Unknown')}")
            logger.info(f"  - Application: {window.get('executable', 'Unknown')}")
            logger.info(f"  - Process ID: {window.get('pid', 'Unknown')}")
        
        # Log element information for web interactions
        if 'element_info' in action_data:
            element = action_data['element_info']
            logger.info("\nElement Information:")
            logger.info(f"  - Tag: {element.get('tag_name', 'Unknown')}")
            logger.info(f"  - ID: {element.get('id', 'None')}")
            logger.info(f"  - Class: {element.get('class_name', 'None')}")
            logger.info(f"  - Text: {element.get('text', 'None')}")
            if 'xpath' in element:
                logger.info(f"  - XPath: {element['xpath']}")
        
        # Log mouse actions
        if 'position' in action_data:
            pos = action_data['position']
            logger.info("\nMouse Information:")
            logger.info(f"  - Position: x={pos.get('x')}, y={pos.get('y')}")
            if 'button' in action_data:
                logger.info(f"  - Button: {action_data['button']}")
            if 'pressed' in action_data:
                logger.info(f"  - State: {'Pressed' if action_data['pressed'] else 'Released'}")
        
        # Log keyboard actions
        if 'key' in action_data:
            logger.info("\nKeyboard Information:")
            logger.info(f"  - Key: {action_data['key']}")
            if 'current_string' in action_data.get('meta_information', {}):
                logger.info(f"  - Current Input: {action_data['meta_information']['current_string']}")
        
        # Log file operations
        if action_data.get('action_type') in ['file_created', 'file_deleted', 'file_modified']:
            logger.info("\nFile Operation:")
            logger.info(f"  - Path: {action_data.get('src_path', 'Unknown')}")
            logger.info(f"  - Type: {action_data.get('action_type', 'Unknown')}")
            logger.info(f"  - Is Directory: {action_data.get('is_directory', False)}")
        
        # Log system resources
        if action_data.get('action_type') == 'system_resource_usage':
            logger.info("\nSystem Resources:")
            logger.info(f"  - CPU Usage: {action_data.get('cpu_usage_percent')}%")
            logger.info(f"  - Memory Usage: {action_data.get('memory_usage_percent')}%")
            logger.info(f"  - Disk Usage: {action_data.get('disk_usage_percent')}%")
        
        # Log screenshots
        if 'screenshot' in action_data:
            logger.info("\nScreenshot Information:")
            logger.info(f"  - Path: {action_data['screenshot']}")
        
        # Log additional metadata
        if 'meta_information' in action_data:
            meta = action_data['meta_information']
            logger.info("\nMetadata:")
            logger.info(f"  - Timestamp: {meta.get('timestamp', 'Unknown')}")
            logger.info(f"  - Duration: {meta.get('interaction_duration', 'Unknown')} seconds")
            if 'user_intent_inferred' in meta:
                logger.info(f"  - Inferred Intent: {meta['user_intent_inferred'].get('intent', 'Unknown')}")
        
        logger.info("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"Error logging action: {e}")
        logger.error(f"Problematic action data: {json.dumps(action_data, indent=2)}")

def generate_unique_id():
    """Generate a unique ID for the recording session."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = ''.join(random.choices('0123456789ABCDEF', k=6))
    return f"REC_{timestamp}_{random_suffix}"

def start_recording(parent=None):
    """Initialize and start the recording process."""
    global recording, start_time, recording_data, current_recording_id
    
    try:
        # Reset recording state and sequence counter
        recording_data = []
        sequence_counter = 0  # Reset counter when starting new recording
        recording = True
        pause_event.clear()
        start_time = time.time()
        
        # Generate unique ID for this recording session
        current_recording_id = generate_unique_id()
        
        # Set up logging for this session
        session_logger = setup_recording_logging(current_recording_id)
        
        # Record initial system info
        user_info = {
            'recording_id': current_recording_id,
            'user_name': getpass.getuser(),
            'locale': locale.getdefaultlocale(),
            'start_time': datetime.now().isoformat()
        }
        
        # Log session start with sequence 0
        session_logger.info(f"=== Recording Session Started: {current_recording_id} ===")
        session_logger.info(f"Sequence Order: 0 (Session Start)")
        session_logger.info(f"User: {user_info['user_name']}")
        session_logger.info(f"Locale: {user_info['locale']}")
        session_logger.info(f"Start Time: {user_info['start_time']}")
        session_logger.info("=" * 50)

        # Start monitoring threads
        start_monitoring_threads()
        
        return True, session_logger
        
    except Exception as e:
        logging.error(f"Failed to start recording: {e}")
        recording = False
        return False, None

def start_monitoring_threads():
    """Start all monitoring threads."""
    try:
        # Start clipboard monitoring
        clipboard_thread = threading.Thread(target=monitor_clipboard, daemon=True)
        clipboard_thread.start()

        # Start process monitoring
        process_thread = threading.Thread(target=monitor_processes_and_services, daemon=True)
        process_thread.start()

        # Start file system monitoring
        fs_thread = threading.Thread(target=monitor_file_system, daemon=True)
        fs_thread.start()

        # Start window monitoring
        window_thread = threading.Thread(target=monitor_window_focus_and_input, daemon=True)
        window_thread.start()

        # Start resource monitoring
        resource_thread = threading.Thread(target=monitor_system_resources, daemon=True)
        resource_thread.start()

        logging.info("All monitoring threads started successfully")
        
    except Exception as e:
        logging.error(f"Failed to start monitoring threads: {e}")
        raise

def stop_recording(session_logger=None):
    """Stop the recording process."""
    global recording
    try:
        recording = False
        pause_event.set()
        
        if session_logger:
            session_logger.info("=== Recording Session Ended ===")
            session_logger.info(f"Total Actions Recorded: {len(recording_data)}")
            session_logger.info(f"End Time: {datetime.now().isoformat()}")
            session_logger.info("=" * 50)
        
        # Save raw recording data
        raw_data_file = save_raw_recording_data()
        
        if raw_data_file and session_logger:
            session_logger.info(f"Raw recording data saved to: {raw_data_file}")
        
        return recording_data
        
    except Exception as e:
        if session_logger:
            session_logger.error(f"Error stopping recording: {e}")
        return []

def pause_recording():
    """Pause the recording."""
    try:
        pause_event.set()
        logging.info("Recording paused")
        return True
    except Exception as e:
        logging.error(f"Error pausing recording: {e}")
        return False

def resume_recording():
    """Resume the recording."""
    try:
        pause_event.clear()
        logging.info("Recording resumed")
        return True
    except Exception as e:
        logging.error(f"Error resuming recording: {e}")
        return False

def get_recording_data():
    """Get the current recording data."""
    return recording_data

# Function to calculate target resolution while maintaining aspect ratio
def get_target_resolution(original_width, original_height, max_width, max_height):
    aspect_ratio = original_width / original_height
    if original_width > original_height:
        width = min(original_width, max_width)
        height = int(width / aspect_ratio)
    else:
        height = min(original_height, max_height)
        width = int(height * aspect_ratio)
    return (width, height)

# Calculate target resolution based on the screen size and max dimensions
target_resolution = get_target_resolution(screen_width, screen_height, max_width, max_height)

# Ensure the screenshots directory exists
if not os.path.exists('screenshots'):
    os.makedirs('screenshots')

# Check for administrative privileges
def is_admin():
    """
    Check if the script is running with administrative privileges.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Request administrative privileges
def request_admin():
    """
    Request administrative privileges if not already granted.
    """
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

# Prompt user for consent
def user_consent():
    """
    Prompt the user for consent, informing them about all data being captured.
    """
    consent = input(
        "This script will record your actions, including:\n"
        "- Keyboard inputs\n"
        "- Mouse clicks\n"
        "- Screenshots\n"
        "- Screen recordings\n"
        "- Clipboard changes\n"
        "- Window focus\n"
        "- Process and service activity\n"
        "- File system changes\n"
        "- Registry changes\n"
        "- System resource usage\n"
        "- Monitor information\n"
        "Do you consent to proceed? (yes/no): "
    )
    if consent.lower() != 'yes':
        print("User did not consent. Exiting.")
        sys.exit()

# Initialize global variables
recording_data = []                 # List to store all recorded events
start_time = None #added                  # Start time of the recording session
process_info_cache = {}             # Cache for process information

# Helper function to get active window details
def get_active_window():
    """
    Get details of the currently active window.
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        process = psutil.Process(pid)
        window_title = win32gui.GetWindowText(hwnd)
        executable = process.name()
        return {
            'window_title': window_title,
            'executable': executable,
            'pid': pid
        }
    except Exception as e:
        return {
            'window_title': None,
            'executable': None,
            'pid': None
        }

# Function to get monitor information for multi-monitor setups
def get_monitor_info(x, y):
    """
    Get monitor information based on cursor position.
    """
    monitors = win32api.EnumDisplayMonitors()
    for monitor in monitors:
        monitor_area = monitor[2]
        if monitor_area[0] <= x <= monitor_area[2] and monitor_area[1] <= y <= monitor_area[3]:
            return {
                'monitor_left': monitor_area[0],
                'monitor_top': monitor_area[1],
                'monitor_right': monitor_area[2],
                'monitor_bottom': monitor_area[3]
            }
    return None

# Capture screenshot at lower resolution
def capture_screenshot(action_type, timestamp):
    """Capture a screenshot with the recording ID in the filename."""
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            img = img.resize(target_resolution, Image.LANCZOS)
            
            # Create filename with recording ID
            filename = os.path.join(
                SCREENSHOTS_DIR, 
                f"{current_recording_id}_{action_type}_screenshot_{int(timestamp)}.png"
            )
            img.save(filename)
            
            logging.info(f"Screenshot saved: {filename}")
            return filename
            
    except Exception as e:
        logging.error(f"Failed to capture screenshot: {e}")
        return None

def create_meta_information(action_type, window_info=None, duration=None, additional_context=None):
    """
    Creates standardized meta information for recorded actions based on schema.
    """
    global sequence_counter  # Add this at the top of the file as: sequence_counter = 0
    
    # Increment sequence counter for each new action
    sequence_counter += 1
    
    timestamp = datetime.now().isoformat()
    
    meta_information = {
        "timestamp": timestamp,
        "sequence_order": sequence_counter,  # Use the global counter
        "screen_context": {
            "visible_ui_elements": []
        },
        "url_path_context": {
            "url": None,
            "file_path": None
        },
        "element_context": None,
        "application_context": {
            "application_name": window_info.get('executable') if window_info else None,
            "application_version": None
        },
        "interaction_duration": duration or 0.0,
        "user_intent_inferred": {
            "intent": f"Perform {action_type} action"
        },
        "previous_action_context": {
            "previous_action": recording_data[-1].get('type') if recording_data else None,
            "previous_sequence": sequence_counter - 1 if sequence_counter > 1 else None
        },
        "follow_up_action_context": {
            "predicted_next_action": None
        }
    }

    # Add visible UI elements
    if window_info:
        meta_information["screen_context"]["visible_ui_elements"].append(
            f"Window: {window_info.get('window_title')}"
        )

    # Add additional context if provided
    if additional_context:
        meta_information.update(additional_context)

    return meta_information

def on_click(x, y, button, pressed):
    """Enhanced mouse click recording with full schema metadata."""
    if not recording or pause_event.is_set():
        return
    
    try:
        action_type = 'left_click' if button == mouse.Button.left else 'right_click'
        
        details = {
            'position': {'x': x, 'y': y},
            'button': str(button),
            'pressed': pressed,
            'element_info': get_element_at_position(x, y),
            'context': {
                'monitor_info': get_monitor_info(x, y),
                'click_type': 'single'
            }
        }
        
        record_action(action_type, details)
        
    except Exception as e:
        logging.error(f"Error recording mouse click: {e}")

def on_scroll(x, y, dx, dy):
    """
    Callback function for mouse scroll events.
    """
    if not recording or pause_event.is_set():
        return
    monitor_info = get_monitor_info(x, y)
    event = {
        'timestamp': time.time() - start_time,
        'action_type': 'mouse_scroll',
        'dx': dx,
        'dy': dy,
        'position': {'x': x, 'y': y},
        'monitor': monitor_info,
        'window': get_active_window()
    }
    recording_data.append(event)

def on_move(x, y):
    """
    Callback function for mouse move events.
    """
    pass

# Record keyboard events
def on_press(key):
    """Enhanced keyboard event recording with full schema metadata."""
    if not recording or pause_event.is_set():
        return
    
    try:
        if isinstance(key, keyboard.Key):
            details = {
                'key': str(key),
                'key_type': 'special',
                'modifiers': get_active_modifiers(),
                'context': {
                    'input_field': get_active_input_field()
                }
            }
            record_action('special_key_press', details)
        else:
            if not hasattr(recording, 'current_string'):
                recording.current_string = ""
            recording.current_string += key.char
            
            details = {
                'key': key.char,
                'key_type': 'character',
                'current_string': recording.current_string,
                'context': {
                    'input_field': get_active_input_field()
                }
            }
            record_action('keystroke', details)
            
    except Exception as e:
        logging.error(f"Error recording keystroke: {e}")

def on_release(key):
    """Enhanced key release recording with metadata."""
    if not recording or pause_event.is_set():
        return
        
    try:
        timestamp = time.time() - start_time
        window_info = get_active_window()
        
        # Record key release event
        release_data = {
            'type': 'key_release',
            'key': key.char if hasattr(key, 'char') else str(key),
            'timestamp': timestamp,
            'window': window_info,
            'meta_information': create_meta_information(
                'key_release',
                window_info,
                0.1,
                {"key_type": "character" if hasattr(key, 'char') else "special"}
            )
        }
        recording_data.append(release_data)
        
    except Exception as e:
        logging.error(f"Error recording key release: {e}")

# Monitor clipboard events
def monitor_clipboard():
    """Enhanced clipboard monitoring with full metadata."""
    recent_value = ""
    while recording:
        if pause_event.is_set():
            time.sleep(0.5)
            continue
            
        try:
            win32clipboard.OpenClipboard()
            current_value = win32clipboard.GetClipboardData()
            
            if current_value != recent_value:
                window_info = get_active_window()
                
                details = {
                    'content_type': 'text',
                    'content_length': len(current_value),
                    'content': current_value[:100] + "..." if len(current_value) > 100 else current_value,
                    'previous_content': recent_value[:100] + "..." if len(recent_value) > 100 else recent_value,
                    'duration': 0.0
                }
                
                record_action('clipboard_operation', details, window_info)
                recent_value = current_value
                
        except Exception:
            pass
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

# Monitor process and service events
def monitor_processes_and_services():
    """
    Monitor process and service start/stop events.
    """
    existing_pids = set(psutil.pids())
    existing_services = {service.name(): service.status() for service in psutil.win_service_iter()}
    while recording:
        if pause_event.is_set():
            time.sleep(1)
            continue
        time.sleep(1)
        current_pids = set(psutil.pids())
        new_pids = current_pids - existing_pids
        terminated_pids = existing_pids - current_pids

        # Process start events
        for pid in new_pids:
            try:
                process = psutil.Process(pid)
                timestamp = time.time() - start_time
                screenshot_path = capture_screenshot('process_start', timestamp)
                event = {
                    'timestamp': timestamp,
                    'action_type': 'process_start',
                    'pid': pid,
                    'name': process.name(),
                    'exe': process.exe(),
                    'screenshot': screenshot_path
                }
                recording_data.append(event)
            except Exception:
                pass

        # Process termination events
        for pid in terminated_pids:
            timestamp = time.time() - start_time
            screenshot_path = capture_screenshot('process_terminate', timestamp)
            event = {
                'timestamp': timestamp,
                'action_type': 'process_terminate',
                'pid': pid,
                'screenshot': screenshot_path
            }
            recording_data.append(event)

        existing_pids = current_pids

# Monitor window focus changes and input boxes
def monitor_window_focus_and_input():
    """Enhanced window focus monitoring with full metadata."""
    last_window = None
    while recording:
        if pause_event.is_set():
            time.sleep(0.5)
            continue
            
        try:
            current_window = get_active_window()
            if current_window['window_title'] != last_window:
                details = {
                    'window_transition': {
                        'from': last_window,
                        'to': current_window['window_title']
                    },
                    'window_state': {
                        'maximized': is_window_maximized(current_window['window_title']),
                        'foreground': True
                    },
                    'duration': 0.0
                }
                
                record_action('window_focus', details, current_window)
                last_window = current_window['window_title']
                
        except Exception as e:
            logging.error(f"Error in window monitoring: {e}")

# Monitor file system changes
class FileSystemMonitorHandler(FileSystemEventHandler):
    """
    Handler for file system events.
    """
    def on_created(self, event):
        if pause_event.is_set():
            return
        timestamp = time.time() - start_time
        screenshot_path = capture_screenshot('file_created', timestamp)
        event_data = {
            'timestamp': timestamp,
            'action_type': 'file_created',
            'src_path': event.src_path,
            'is_directory': event.is_directory,
            'screenshot': screenshot_path
        }
        recording_data.append(event_data)

    def on_deleted(self, event):
        if pause_event.is_set():
            return
        timestamp = time.time() - start_time
        screenshot_path = capture_screenshot('file_deleted', timestamp)
        event_data = {
            'timestamp': timestamp,
            'action_type': 'file_deleted',
            'src_path': event.src_path,
            'is_directory': event.is_directory,
            'screenshot': screenshot_path
        }
        recording_data.append(event_data)

    def on_modified(self, event):
        if pause_event.is_set():
            return
        timestamp = time.time() - start_time
        screenshot_path = capture_screenshot('file_modified', timestamp)
        event_data = {
            'timestamp': timestamp,
            'action_type': 'file_modified',
            'src_path': event.src_path,
            'is_directory': event.is_directory,
            'screenshot': screenshot_path
        }
        recording_data.append(event_data)

def monitor_file_system():
    """
    Monitor file system changes in specified directories.
    """
    paths = [os.path.expanduser('~\Downloads')]  # Add more paths if needed
    event_handler = FileSystemMonitorHandler()
    observer = Observer()
    for path in paths:
        observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while recording:
            if pause_event.is_set():
                time.sleep(1)
                continue
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.stop()
    observer.join()

# Monitor registry changes (placeholder)
def monitor_registry_changes(): #monitors windows system registry changes
    """
    Monitor registry changes (implementation needed).
    """
    pass  # Implement as needed

# Monitor system resource usage
def monitor_system_resources():
    """
    Monitor CPU, memory, and disk usage.
    """
    while recording:
        if pause_event.is_set():
            time.sleep(1)
            continue
        time.sleep(1)
        cpu_usage = psutil.cpu_percent(interval=None)
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')
        event = {
            'timestamp': time.time() - start_time,
            'action_type': 'system_resource_usage',
            'cpu_usage_percent': cpu_usage,
            'memory_usage_percent': memory_info.percent,
            'disk_usage_percent': disk_usage.percent
        }
        recording_data.append(event)

# Start screen recording
def start_screen_recording():
    """Initialize screen recording with the recording ID in the filename."""
    if cv2 is None:
        logging.error("Screen recording disabled - OpenCV not available")
        return None, None

    try:
        video_filename = os.path.join(
            SCREEN_RECORDINGS_DIR, 
            f"{current_recording_id}_screencapture.avi"
        )
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(video_filename, fourcc, 8.0, target_resolution)
        
        # Set up recording-specific logging
        log_filename = os.path.join(
            RECORDING_LOGS_DIR, 
            f"{current_recording_id}_recording_log.txt"
        )
        recording_logger = logging.getLogger(f'recording_{current_recording_id}')
        recording_logger.setLevel(logging.INFO)
        fh = logging.FileHandler(log_filename)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        recording_logger.addHandler(fh)
        
        recording_logger.info(f"Started screen recording: {video_filename}")
        return out, video_filename
        
    except Exception as e:
        logging.error(f"Failed to start screen recording: {e}")
        return None, None

# Capture screen frames at lower resolution
def capture_screen(out):
    """
    Capture screen frames and write them to the video file.
    """
    if cv2 is None or out is None:
        return

    while screen_recording:
        if pause_event.is_set():
            time.sleep(0.125)
            continue
        img = grab_screen()
        if img is not None:
            out.write(img)
        time.sleep(0.125)  # Capture at ~8 frames per second

# Grab the screen and resize
def grab_screen():
    """
    Grab the current screen and resize the image to the target resolution.
    """
    if cv2 is None:
        return None

    try:
        hwin = win32gui.GetDesktopWindow()
        width = screen_width
        height = screen_height
        hwindc = win32gui.GetWindowDC(hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (width, height), srcdc, (0, 0), win32con.SRCCOPY)
        signedIntsArray = bmp.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype='uint8')
        img.shape = (height, width, 4)
        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        # Resize the image while maintaining aspect ratio
        img = cv2.resize(img, target_resolution, interpolation=cv2.INTER_AREA)
        return img
    except Exception as e:
        logging.error(f"Error capturing screen: {e}")
        return None

# Main function
def main():
    """
    Main function to initialize and start all monitoring threads and listeners.
    """
    global recording, screen_recording, start_time
    request_admin()
    user_consent()

    # Record user and system info
    user_info = {
        'user_name': getpass.getuser(),
        'locale': locale.getdefaultlocale(),
        'start_time': datetime.now().isoformat()
    }
    recording_data.append({'action_type': 'session_start', 'user_info': user_info})

    # Start keyboard listener for control keys
    control_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    control_listener.start()

    # Wait for the user to start recording
    print("Press F9 to start/pause/resume recording, F10 to stop.")
    while True:
        if recording:
            break
        time.sleep(0.1)

    # Initialize recording parameters
    start_time = time.time()
    screen_recording = True

    # Start screen recording
    out, video_filename = start_screen_recording()
    screen_thread = threading.Thread(target=capture_screen, args=(out,), daemon=True)
    screen_thread.start()

    # Start clipboard monitoring
    clipboard_thread = threading.Thread(target=monitor_clipboard, daemon=True)
    clipboard_thread.start()

    # Start process and service monitoring
    process_thread = threading.Thread(target=monitor_processes_and_services, daemon=True)
    process_thread.start()

    # Start file system monitoring
    fs_thread = threading.Thread(target=monitor_file_system, daemon=True)
    fs_thread.start()

    # Start window focus and input monitoring
    window_thread = threading.Thread(target=monitor_window_focus_and_input, daemon=True)
    window_thread.start()

    # Start system resource monitoring
    resource_thread = threading.Thread(target=monitor_system_resources, daemon=True)
    resource_thread.start()

    # Start registry monitoring (implement as needed)
    # registry_thread = threading.Thread(target=monitor_registry_changes, daemon=True)
    # registry_thread.start()

    # Start mouse listener
    mouse_listener = mouse.Listener(
        on_click=on_click,
        on_scroll=on_scroll,
        on_move=on_move)
    mouse_listener.start()

    # Keep the main thread alive while recording
    try:
        while recording:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    # Stop all monitoring threads
    screen_recording = False
    screen_thread.join()
    out.release()
    print(f'Screen recording saved to {video_filename}')

    # Wait for other threads to finish
    clipboard_thread.join()
    process_thread.join()
    fs_thread.join()
    window_thread.join()
    resource_thread.join()
    mouse_listener.stop()
    control_listener.stop()

    # Save recording data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'recording_{timestamp}.json'

    # Wrap the recording data in a top-level dictionary if required by the schema
    output_data = {
        'workflow_name': 'Recorded Workflow',
        'actions': recording_data
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print(f'Recording saved to {filename}')

def save_raw_recording_data():
    """Save raw recording data with the recording ID."""
    try:
        # Create raw data directory if it doesn't exist
        raw_data_dir = 'raw_recordings'
        os.makedirs(raw_data_dir, exist_ok=True)
        
        # Save raw recording data
        raw_data_file = os.path.join(
            raw_data_dir, 
            f"{current_recording_id}_raw_recording.json"
        )
        
        with open(raw_data_file, 'w') as f:
            json.dump({
                'recording_id': current_recording_id,
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'user_info': {
                    'user_name': getpass.getuser(),
                    'locale': locale.getdefaultlocale(),
                    'start_time': datetime.now().isoformat()
                },
                'recording_data': recording_data,
                'screen_recording': os.path.join(
                    SCREEN_RECORDINGS_DIR, 
                    f"{current_recording_id}_screencapture.avi"
                ),
                'screenshots': [
                    f for f in os.listdir(SCREENSHOTS_DIR) 
                    if f.startswith(current_recording_id)
                ],
                'log_file': os.path.join(
                    RECORDING_LOGS_DIR, 
                    f"{current_recording_id}_recording_log.txt"
                )
            }, f, indent=4)
            
        logging.info(f"Raw recording data saved to: {raw_data_file}")
        return raw_data_file
        
    except Exception as e:
        logging.error(f"Failed to save raw recording data: {e}")
        return None

class SmartScreenshotManager:
    def __init__(self):
        self.last_screenshot = None
        self.last_screenshot_hash = None
        self.min_interval = 0.5  # Minimum time between screenshots
        self.last_capture_time = 0
        
    def should_capture(self, current_screen):
        current_time = time.time()
        
        # Check time interval
        if current_time - self.last_capture_time < self.min_interval:
            return False
            
        # Calculate image hash
        current_hash = self.calculate_image_hash(current_screen)
        
        # Compare with last screenshot
        if self.last_screenshot_hash and self.last_screenshot_hash == current_hash:
            return False
            
        self.last_screenshot_hash = current_hash
        self.last_capture_time = current_time
        return True
    
    @staticmethod
    def calculate_image_hash(image):
        # Simple perceptual hash
        img = cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return hash(gray.tobytes())

screenshot_manager = SmartScreenshotManager()

class MemoryManager:
    def __init__(self, max_memory_percent=75):
        self.max_memory_percent = max_memory_percent
        self.cleanup_threshold = 70
        
    def check_memory(self):
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.max_memory_percent:
            self.cleanup_old_data()
    
    def cleanup_old_data(self):
        global recording_data
        if len(recording_data) > 1000:
            # Keep only the last 1000 events
            recording_data = recording_data[-1000:]
            # Force garbage collection
            import gc
            gc.collect()

memory_manager = MemoryManager()

class EventFilter:
    def __init__(self):
        self.last_mouse_pos = None
        self.mouse_threshold = 10  # pixels
        self.last_window_title = None
        self.last_keyboard_time = 0
        self.key_threshold = 0.05  # seconds

    def should_record_mouse_move(self, x, y):
        if not self.last_mouse_pos:
            self.last_mouse_pos = (x, y)
            return True
        
        distance = ((x - self.last_mouse_pos[0])**2 + (y - self.last_mouse_pos[1])**2)**0.5
        if distance > self.mouse_threshold:
            self.last_mouse_pos = (x, y)
            return True
        return False

    def should_record_keyboard(self, timestamp):
        if timestamp - self.last_keyboard_time > self.key_threshold:
            self.last_keyboard_time = timestamp
            return True
        return False

event_filter = EventFilter()

def create_action_metadata(action_type, details, window_info=None):
    """
    Creates comprehensive metadata for any action type following the schema.
    """
    global sequence_counter
    sequence_counter += 1
    
    timestamp = datetime.now().isoformat()
    window_info = window_info or get_active_window()
    
    metadata = {
        "timestamp": timestamp,
        "sequence_order": sequence_counter,
        "screen_context": {
            "visible_ui_elements": get_visible_elements(),
            "active_window": window_info.get('window_title'),
            "screen_resolution": (screen_width, screen_height)
        },
        "url_path_context": {
            "url": get_current_url() if is_browser_window(window_info) else None,
            "file_path": get_active_file_path()
        },
        "element_context": details.get('element_info', None),
        "application_context": {
            "application_name": window_info.get('executable'),
            "application_version": get_app_version(window_info.get('executable')),
            "process_id": window_info.get('pid')
        },
        "interaction_duration": details.get('duration', 0.1),
        "user_intent_inferred": {
            "intent": infer_user_intent(action_type, details),
            "context": details.get('context', {})
        },
        "previous_action_context": {
            "previous_action": get_previous_action(),
            "previous_sequence": sequence_counter - 1 if sequence_counter > 1 else None
        },
        "follow_up_action_context": {
            "predicted_next_action": predict_next_action(action_type, details)
        }
    }
    
    return metadata

def get_visible_elements():
    """Get all visible UI elements in the current window."""
    elements = []
    try:
        if is_browser_window(get_active_window()):
            # Get web elements if in browser
            elements.extend(get_web_elements())
        else:
            # Get desktop UI elements
            elements.extend(get_desktop_elements())
    except Exception as e:
        logging.error(f"Error getting visible elements: {e}")
    return elements

def get_web_elements():
    """Get visible elements from web browser."""
    elements = []
    try:
        import selenium.webdriver as webdriver
        driver = webdriver.Chrome()  # Or get existing driver
        visible_elements = driver.find_elements_by_css_selector('*:not([style*="display:none"])')
        for element in visible_elements:
            elements.append({
                'type': element.tag_name,
                'id': element.get_attribute('id'),
                'class': element.get_attribute('class'),
                'text': element.text
            })
    except Exception as e:
        logging.error(f"Error getting web elements: {e}")
    return elements

def get_desktop_elements():
    """Get visible elements from desktop application."""
    elements = []
    try:
        import pywinauto
        app = pywinauto.Desktop(backend="uia")
        window = app.window(title=get_active_window()['window_title'])
        for element in window.descendants():
            elements.append({
                'type': element.element_info.control_type,
                'name': element.element_info.name,
                'automation_id': element.element_info.automation_id
            })
    except Exception as e:
        logging.error(f"Error getting desktop elements: {e}")
    return elements

def record_action(action_type, details, window_info=None):
    """
    Records an action with full metadata according to the schema.
    """
    try:
        timestamp = time.time() - start_time
        window_info = window_info or get_active_window()
        
        # Create comprehensive metadata
        metadata = create_action_metadata(action_type, details, window_info)
        
        # Take screenshot if needed
        screenshot_path = None
        if action_type not in ['mouse_move', 'wait']:  # Skip for minor actions
            screenshot_path = capture_screenshot(action_type, timestamp)
        
        # Create action record
        action_record = {
            'type': action_type,
            'timestamp': timestamp,
            'window_info': window_info,
            'details': details,
            'screenshot': screenshot_path,
            'meta_information': metadata
        }
        
        # Add to recording data
        recording_data.append(action_record)
        
        # Log the action
        if hasattr(recording, 'session_logger'):
            log_action(recording.session_logger, action_record)
            
        logging.info(f"Recorded action: {action_type}")
        
    except Exception as e:
        logging.error(f"Error recording action {action_type}: {e}")

def is_window_maximized(window_title):
    """
    Check if a window is maximized.
    
    Args:
        window_title (str): Title of the window to check
        
    Returns:
        bool: True if window is maximized, False otherwise
    """
    try:
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            placement = win32gui.GetWindowPlacement(hwnd)
            return placement[1] == win32con.SW_SHOWMAXIMIZED
        return False
    except Exception as e:
        logging.error(f"Error checking window state: {e}")
        return False

def get_active_modifiers():
    """
    Get currently pressed modifier keys.
    
    Returns:
        list: List of active modifier keys
    """
    modifiers = []
    try:
        if win32api.GetKeyState(win32con.VK_SHIFT) < 0:
            modifiers.append('shift')
        if win32api.GetKeyState(win32con.VK_CONTROL) < 0:
            modifiers.append('ctrl')
        if win32api.GetKeyState(win32con.VK_MENU) < 0:  # Alt key
            modifiers.append('alt')
        return modifiers
    except Exception as e:
        logging.error(f"Error getting modifier keys: {e}")
        return []

def get_active_input_field():
    """
    Get information about the currently active input field.
    
    Returns:
        dict: Information about the active input field
    """
    try:
        window = get_active_window()
        if window['window_title']:
            app = Application(backend="uia").connect(title=window['window_title'])
            focused = app.top_window().get_focus()
            if focused:
                return {
                    'type': focused.element_info.control_type,
                    'name': focused.element_info.name,
                    'automation_id': focused.element_info.automation_id
                }
    except Exception as e:
        logging.error(f"Error getting active input field: {e}")
    return None

def get_element_at_position(x, y):
    """Get UI element at the specified coordinates."""
    try:
        window_info = get_active_window()
        if is_browser_window(window_info):
            return get_web_element_at_position(x, y)
        else:
            return get_desktop_element_at_position(x, y)
    except Exception as e:
        logging.error(f"Error getting element at position: {e}")
        return None

def get_web_element_at_position(x, y):
    """Get web element at coordinates using Selenium."""
    try:
        if hasattr(recording, 'driver'):
            element = recording.driver.execute_script(
                'return document.elementFromPoint(arguments[0], arguments[1]);',
                x, y
            )
            if element:
                return {
                    'tag_name': element.tag_name,
                    'id': element.get_attribute('id'),
                    'class': element.get_attribute('class'),
                    'text': element.text
                }
    except:
        pass
    return None

def get_desktop_element_at_position(x, y):
    """Get desktop UI element at coordinates."""
    try:
        hwnd = win32gui.WindowFromPoint((x, y))
        if hwnd:
            class_name = win32gui.GetClassName(hwnd)
            window_text = win32gui.GetWindowText(hwnd)
            return {
                'type': 'desktop_element',
                'class_name': class_name,
                'text': window_text,
                'handle': hwnd
            }
    except:
        pass
    return None

def get_current_url():
    """Get current URL if in a browser window."""
    try:
        if hasattr(recording, 'driver'):
            return recording.driver.current_url
    except:
        pass
    return None

def is_browser_window(window_info):
    """Check if window is a web browser."""
    if not window_info:
        return False
    browser_processes = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'iexplore.exe']
    return window_info.get('executable', '').lower() in browser_processes

def get_active_file_path():
    """Get path of currently active file."""
    try:
        window_info = get_active_window()
        if window_info and window_info['window_title']:
            # Try to extract file path from window title
            title = window_info['window_title']
            # Common patterns for file paths in window titles
            if ' - ' in title:
                potential_path = title.split(' - ')[0]
                if os.path.exists(potential_path):
                    return potential_path
    except:
        pass
    return None

def get_app_version(executable_name):
    """Get application version information."""
    try:
        if executable_name:
            process = psutil.Process(get_pid_by_name(executable_name))
            return process.exe()  # Could be enhanced to extract version info
    except:
        pass
    return "Unknown"

def infer_user_intent(action_type, details):
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

def get_previous_action():
    """Get the previous action's details."""
    if len(recording_data) > 0:
        last_action = recording_data[-1]
        return {
            "type": last_action.get('type'),
            "timestamp": last_action.get('timestamp'),
            "sequence_order": last_action.get('meta_information', {}).get('sequence_order')
        }
    return None

def predict_next_action(action_type, details):
    """Predict the next likely action based on current context."""
    # This could be enhanced with ML-based prediction
    common_sequences = {
        'left_click': ['keystroke', 'typing_sequence'],
        'keystroke': ['keystroke', 'typing_sequence'],
        'typing_sequence': ['left_click', 'key_combination'],
        'file_operation': ['window_focus', 'left_click']
    }
    return common_sequences.get(action_type, ['unknown'])[0]

def get_pid_by_name(process_name):
    """
    Get process ID by process name.
    
    Args:
        process_name (str): Name of the process to find
        
    Returns:
        int: Process ID if found, None otherwise
    """
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                return proc.info['pid']
        return None
    except Exception as e:
        logging.error(f"Error getting PID for process {process_name}: {e}")
        return None

if __name__ == '__main__':
    # Set up initial recording state
    recording = False
    pause_event.set()  # Start in paused state
    monitor_file_system()
    monitor_clipboard()
    monitor_window_focus_and_input()
    monitor_system_resources()
    monitor_processes_and_services()

    # Start the main function
    main()