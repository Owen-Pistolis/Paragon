import json
import logging
from typing import Dict, Any, List, Union
import time
from windows_automation import WindowsAutomation
from browser_automation import BrowserAutomation
import win32gui
import win32con
import win32api
import win32ui
import tkinter as tk
from tkinter import ttk
import threading
from queue import Queue
import datetime
import os
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import ctypes
from ctypes import wintypes
import comtypes
from comtypes import CLSCTX_ALL
from comtypes.client import CreateObject

# Define GUID for Virtual Desktop interfaces
CLSID_ImmersiveShell = "{C2F03A33-21F5-47FA-B4BB-156362A2F239}"
CLSID_VirtualDesktopManagerInternal = "{C5E0CDCA-7B6E-41B2-9FC4-D93975CC467B}"

class IVirtualDesktop(comtypes.IUnknown):
    _case_insensitive_ = True
    _iid_ = comtypes.GUID('{FF72FFDD-BE7E-43FC-9C03-AD81681E88E4}')
    _methods_ = [
        comtypes.STDMETHOD(ctypes.HRESULT, 'IsViewVisible', []),
        comtypes.STDMETHOD(ctypes.HRESULT, 'GetID', [])
    ]

class IVirtualDesktopManager(comtypes.IUnknown):
    _case_insensitive_ = True
    _iid_ = comtypes.GUID('{A5CD92FF-29BE-454C-8D04-D82879FB3F1B}')
    _methods_ = [
        comtypes.STDMETHOD(ctypes.HRESULT, 'GetCount', []),
        comtypes.STDMETHOD(ctypes.HRESULT, 'GetDesktops', []),
        comtypes.STDMETHOD(ctypes.HRESULT, 'CreateDesktop', []),
        comtypes.STDMETHOD(ctypes.HRESULT, 'RemoveDesktop', [])
    ]

class AutomationRunner:
    def __init__(self):
        self.windows_automation = WindowsAutomation()
        self.browser_automation = BrowserAutomation()
        self.logger = logging.getLogger(__name__)
        self.status_queue = Queue()
        self.current_workflow = None
        self.is_running = False
        self.pause_event = threading.Event()
        
        # Initialize UI
        self.root = None
        self.desktop_view = None
        self.init_ui()
        
        # Create virtual desktop
        self.create_virtual_desktop()
        
        # Start screen capture thread
        self.capture_thread = threading.Thread(target=self._screen_capture_loop, daemon=True)
        self.capture_thread.start()

    def init_ui(self):
        """Initialize the UI components"""
        try:
            # Create main window
            self.root = tk.Tk()
            self.root.title("Automation Runner")
            
            # Configure window size and position
            window_width = 1200
            window_height = 800
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Create main frame
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create desktop view (left panel)
            desktop_frame = ttk.LabelFrame(main_frame, text="Desktop View")
            desktop_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create canvas for desktop view
            self.desktop_view = tk.Canvas(
                desktop_frame,
                width=800,
                height=600,
                bg='black'
            )
            self.desktop_view.pack(fill=tk.BOTH, expand=True)
            
            # Create control panel (right panel)
            control_frame = ttk.LabelFrame(main_frame, text="Controls")
            control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
            
            # Add control buttons
            ttk.Button(control_frame, text="Start", command=self.start_automation).pack(pady=5)
            ttk.Button(control_frame, text="Stop", command=self.stop_automation).pack(pady=5)
            ttk.Button(control_frame, text="Pause", command=self.pause_automation).pack(pady=5)
            
            # Add status display
            status_frame = ttk.LabelFrame(control_frame, text="Status")
            status_frame.pack(fill=tk.X, pady=10, padx=5)
            self.status_label = ttk.Label(status_frame, text="Ready")
            self.status_label.pack(pady=5)
            
            self.logger.info("UI initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UI: {str(e)}")
            raise

    def start_automation(self):
        """Start the automation workflow"""
        self.is_running = True
        self.status_label.config(text="Running...")

    def stop_automation(self):
        """Stop the automation workflow"""
        self.is_running = False
        self.status_label.config(text="Stopped")

    def pause_automation(self):
        """Pause/Resume the automation workflow"""
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.status_label.config(text="Running...")
        else:
            self.pause_event.set()
            self.status_label.config(text="Paused")

    def run(self, workflow_path: str):
        """Main method to run the automation"""
        try:
            if not os.path.exists(workflow_path):
                self.logger.error(f"Workflow file not found: {workflow_path}")
                return
                
            with open(workflow_path, 'r') as f:
                self.current_workflow = json.load(f)
            
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Failed to run automation: {str(e)}")

    def create_virtual_desktop(self):
        """Create a new virtual desktop for automation"""
        try:
            # For now, just log that we're skipping virtual desktop creation
            self.logger.info("Virtual desktop creation skipped - using current desktop")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create virtual desktop: {str(e)}")
            return False

    def _screen_capture_loop(self):
        """Main loop for screen capture and visual feedback"""
        try:
            # Initialize screen capture
            hwnd = win32gui.GetDesktopWindow()
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

            while True:
                try:
                    # Create DC and bitmap
                    hwndDC = win32gui.GetWindowDC(hwnd)
                    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                    saveDC = mfcDC.CreateCompatibleDC()
                    
                    # Create bitmap object
                    saveBitMap = win32ui.CreateBitmap()
                    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                    saveDC.SelectObject(saveBitMap)
                    
                    # Copy screen to bitmap
                    saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
                    
                    # Convert to PIL Image
                    bmpinfo = saveBitMap.GetInfo()
                    bmpstr = saveBitMap.GetBitmapBits(True)
                    img = Image.frombuffer(
                        'RGB',
                        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                        bmpstr, 'raw', 'BGRX', 0, 1
                    )
                    
                    # Get current mouse position for trail
                    current_pos = win32gui.GetCursorPos()
                    self.last_mouse_positions.append(current_pos)
                    if len(self.last_mouse_positions) > self.max_mouse_positions:
                        self.last_mouse_positions.pop(0)
                    
                    # Draw mouse trail
                    draw = ImageDraw.Draw(img)
                    for i, pos in enumerate(self.last_mouse_positions):
                        alpha = int(255 * (i / len(self.last_mouse_positions)))
                        color = (64, 158, 255, alpha)  # Blue trail with fade
                        draw.ellipse([pos[0]-2, pos[1]-2, pos[0]+2, pos[1]+2], 
                                   fill=color)
                    
                    # Update and draw click animations
                    current_time = time.time()
                    new_animations = []
                    for anim in self.click_animations:
                        age = current_time - anim['start_time']
                        if age < self.click_animation_duration:
                            progress = age / self.click_animation_duration
                            radius = int(self.click_animation_max_radius * progress)
                            alpha = int(255 * (1 - progress))
                            color = (*anim['color'], alpha)
                            x, y = anim['position']
                            draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                                       outline=color, width=2)
                            new_animations.append(anim)
                    self.click_animations = new_animations
                    
                    # Convert to PhotoImage and update canvas
                    if self.desktop_view:  # Check if desktop_view exists
                        photo = ImageTk.PhotoImage(img)
                        self.desktop_view.create_image(0, 0, image=photo, anchor="nw")
                        self.desktop_view.image = photo  # Keep reference
                    
                    # Clean up
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                    saveDC.DeleteDC()
                    mfcDC.DeleteDC()
                    win32gui.ReleaseDC(hwnd, hwndDC)
                    
                    # Wait for next frame
                    time.sleep(self.capture_interval)
                    
                except Exception as e:
                    self.logger.error(f"Screen capture error: {str(e)}")
                    time.sleep(1)  # Prevent rapid error logging
                    
        except Exception as e:
            self.logger.error(f"Fatal screen capture error: {str(e)}")

    # ... (rest of the AutomationRunner class implementation)