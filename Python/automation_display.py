from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from workflow_executor import WorkflowExecutor
import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
import numpy as np
import time
import threading
import logging
import ctypes
from ctypes import wintypes
import comtypes
from comtypes import CLSCTX_ALL
from comtypes.client import CreateObject

# Virtual Desktop COM interface GUIDs
CLSID_ImmersiveShell = "{C2F03A33-21F5-47FA-B4BB-156362A2F239}"
CLSID_VirtualDesktopManagerInternal = "{C5E0CDCA-7B6E-41B2-9FC4-D93975CC467B}"
IID_IVirtualDesktopManagerInternal = "{F31574D6-B682-4CDC-BD56-1827860ABEC6}"

class IServiceProvider(comtypes.IUnknown):
    _iid_ = comtypes.GUID("{6D5140C1-7436-11CE-8034-00AA006009FA}")
    _methods_ = [
        comtypes.STDMETHOD(ctypes.HRESULT, "QueryService",
            [comtypes.GUID, comtypes.GUID, ctypes.POINTER(ctypes.c_void_p)]
        ),
    ]

class AutomationDisplay(QWidget):
    automation_completed = pyqtSignal(bool, str)
    step_started = pyqtSignal(int)
    log_message = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.update_display)
        self.capture_interval = 100  # 10 FPS
        self.is_running = False
        self.is_paused = False
        self.current_desktop = None
        self.automation_start_time = None
        self.workflow_path = None
        self.current_step = 0
        
        # Initialize virtual desktop manager with robust error handling
        self.virtual_desktop_manager = None
        try:
            self.shell = CreateObject("Shell.Application", interface=IServiceProvider)
            if self.shell:
                try:
                    self.virtual_desktop_manager = self.shell.QueryService( # type: ignore
                        comtypes.GUID(CLSID_VirtualDesktopManagerInternal),
                        comtypes.GUID(IID_IVirtualDesktopManagerInternal)
                    )
                except Exception as e:
                    self.log_message.emit(f"Virtual desktop manager initialization failed: {e}", logging.WARNING)
                    logging.warning(f"Virtual desktop manager initialization failed: {e}")
        except Exception as e:
            self.log_message.emit(f"Shell initialization failed: {e}", logging.WARNING)
            logging.warning(f"Shell initialization failed: {e}")
        
        # Create workflow executor with error handling
        try:
            self.workflow_executor = WorkflowExecutor()
            self.workflow_executor.progress_updated.connect(self.update_progress)
            self.workflow_executor.step_started.connect(self.on_step_started)
            self.workflow_executor.execution_completed.connect(self.on_workflow_completed)
            self.workflow_executor.log_message.connect(lambda msg, level: self.log_message.emit(msg, level))
        except Exception as e:
            self.log_message.emit(f"Failed to initialize workflow executor: {e}", logging.ERROR)
            logging.error(f"Failed to initialize workflow executor: {e}")

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Display area
        self.display_frame = QFrame()
        self.display_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.display_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 4px;
            }
        """)
        
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        display_layout = QVBoxLayout(self.display_frame)
        display_layout.addWidget(self.display_label)
        layout.addWidget(self.display_frame)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Time display
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-family: 'Consolas', monospace;
                font-size: 14px;
                padding: 5px;
            }
        """)
        
        # Control buttons
        self.play_button = QPushButton("▶")
        self.pause_button = QPushButton("⏸")
        self.stop_button = QPushButton("⏹")
        
        for button in [self.play_button, self.pause_button, self.stop_button]:
            button.setFixedSize(40, 40)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
                QPushButton:pressed {
                    background-color: #505050;
                }
            """)
            
        self.play_button.clicked.connect(self.start_automation)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.stop_button.clicked.connect(self.stop_automation)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 2px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #007acc;
            }
        """)
        self.progress_bar.setTextVisible(False)
        
        # Add widgets to controls layout
        controls_layout.addWidget(self.time_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        
        # Add controls to main layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.progress_bar)
        
    def start_automation(self):
        """Start workflow automation"""
        if not self.is_running:
            try:
                self.is_running = True
                self.is_paused = False
                self.automation_start_time = time.time()
                self.current_step = 0
                
                # Start display update timer
                self.capture_timer.start(self.capture_interval)
                
                # Start workflow execution
                if self.workflow_executor:
                    self.workflow_executor.execute_workflow()
                    self.log_message.emit("Started workflow execution", logging.INFO)
                else:
                    raise Exception("Workflow executor not initialized")
                    
            except Exception as e:
                self.is_running = False
                self.capture_timer.stop()
                error_msg = f"Failed to start automation: {str(e)}"
                self.log_message.emit(error_msg, logging.ERROR)
                self.automation_completed.emit(False, error_msg)
                
    def toggle_pause(self):
        """Toggle pause state"""
        if self.is_running:
            try:
                if self.is_paused:
                    self.workflow_executor.resume()
                    self.is_paused = False
                    self.capture_timer.start(self.capture_interval)
                    self.log_message.emit("Resumed workflow execution", logging.INFO)
                else:
                    self.workflow_executor.pause()
                    self.is_paused = True
                    self.capture_timer.stop()
                    self.log_message.emit("Paused workflow execution", logging.INFO)
            except Exception as e:
                error_msg = f"Failed to toggle pause state: {str(e)}"
                self.log_message.emit(error_msg, logging.ERROR)
                
    def stop_automation(self):
        """Stop workflow automation"""
        if self.is_running:
            try:
                self.workflow_executor.stop()
                self.is_running = False
                self.is_paused = False
                self.capture_timer.stop()
                self.log_message.emit("Stopped workflow execution", logging.INFO)
            except Exception as e:
                error_msg = f"Failed to stop automation: {str(e)}"
                self.log_message.emit(error_msg, logging.ERROR)
                
    def update_progress(self, progress: int):
        self.progress_bar.setValue(progress)
        
    def on_step_started(self, step_description):
        """Handle step started signal"""
        self.current_step += 1
        self.step_started.emit(self.current_step)
        self.log_message.emit(f"Step {self.current_step}: {step_description}", logging.INFO)
        
    def on_workflow_completed(self, success, message):
        """Handle workflow completion"""
        self.is_running = False
        self.capture_timer.stop()
        self.automation_completed.emit(success, message)
        
        if success:
            self.log_message.emit("Workflow completed successfully", logging.INFO)
        else:
            self.log_message.emit(f"Workflow failed: {message}", logging.ERROR)

    def create_virtual_desktop(self):
        """Create a new virtual desktop using Windows API"""
        try:
            # Use Windows key + Ctrl + D to create new desktop
            keyboard = ctypes.windll.user32
            
            # Press Windows + Ctrl + D
            keyboard.keybd_event(0x5B, 0, 0, 0)  # Windows key down
            keyboard.keybd_event(0x11, 0, 0, 0)  # Ctrl key down
            keyboard.keybd_event(0x44, 0, 0, 0)  # D key down
            
            # Release all keys
            keyboard.keybd_event(0x44, 0, 2, 0)  # D key up
            keyboard.keybd_event(0x11, 0, 2, 0)  # Ctrl key up
            keyboard.keybd_event(0x5B, 0, 2, 0)  # Windows key up
            
            # Give Windows time to create the desktop
            time.sleep(1)
            
            self.log_message.emit("Created new virtual desktop", logging.INFO)
            return True
            
        except Exception as e:
            error_msg = f"Failed to create virtual desktop: {e}"
            self.log_message.emit(error_msg, logging.ERROR)
            self.automation_completed.emit(False, error_msg)
            return False

    def update_display(self):
        """Update the display with current desktop screenshot"""
        if not self.is_running or self.is_paused:
            return
            
        hwin = None
        hwindc = None
        srcdc = None
        memdc = None
        bmp = None
            
        try:
            # Get the primary monitor
            monitor = {"left": 0, "top": 0, "width": win32api.GetSystemMetrics(0), "height": win32api.GetSystemMetrics(1)}
            
            # Create device context
            hwin = win32gui.GetDesktopWindow()
            hwindc = win32gui.GetWindowDC(hwin)
            srcdc = win32ui.CreateDCFromHandle(hwindc)
            memdc = srcdc.CreateCompatibleDC()
            
            # Create bitmap
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(srcdc, monitor["width"], monitor["height"])
            memdc.SelectObject(bmp)
            
            # Copy screen into bitmap
            memdc.BitBlt((0, 0), (monitor["width"], monitor["height"]), srcdc, (monitor["left"], monitor["top"]), win32con.SRCCOPY)
            
            # Convert to QPixmap and display
            bmpinfo = bmp.GetInfo()
            bmpstr = bmp.GetBitmapBits(True)
            image = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
            
            # Convert PIL image to QPixmap
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale pixmap to fit display while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.display_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.display_label.setPixmap(scaled_pixmap)
            
            # Update elapsed time
            if self.automation_start_time:
                elapsed = int(time.time() - self.automation_start_time)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                seconds = elapsed % 60
                self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                
        except Exception as e:
            self.log_message.emit(f"Failed to update display: {str(e)}", logging.ERROR)
            self.capture_timer.stop()
            
        finally:
            # Clean up in reverse order of creation
            try:
                if memdc:
                    memdc.DeleteDC()
                if bmp:
                    win32gui.DeleteObject(bmp.GetHandle())
                if srcdc:
                    srcdc.DeleteDC()
                if hwin and hwindc:
                    win32gui.ReleaseDC(hwin, hwindc)
            except Exception as e:
                self.log_message.emit(f"Warning: Cleanup failed: {str(e)}", logging.WARNING)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_running:
            self.update_display()  # Update display when widget is resized